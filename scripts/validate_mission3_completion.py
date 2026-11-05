"""Validate the six private Mission 3 captures and a separate full rebuild."""
from pathlib import Path
import argparse, hashlib, json, subprocess
from collections import Counter, defaultdict
import numpy as np
from PIL import Image
from validate_mission2 import compare, digest
R=Path(__file__).resolve().parents[1]
BASE='dce71e720f4fb98dd39f030dabccb6590636db23'
CLIPS={'plane':389,'plane2':290,'wall':665,'radar':731,'radar2':329,'boss':2889}

def validate(q,rebuild):
 p=R/'pack';report={'version':'0.11.0','base_commit':BASE,'replays':{}}
 for clip,frames in CLIPS.items():
  a=q/(clip+'_native');b=q/(clip+'_release')
  entry=compare(a,b,q/(clip+'_native_replay.wav'),q/(clip+'_release_replay.wav'),frames)
  assert (a/'chr.bin').read_bytes()==(b/'chr.bin').read_bytes()
  assert (a/'chr.bin').stat().st_size==frames*8192
  assert (q/(clip+'_release_replay.end')).exists()
  log=(q/(clip+'_release.log')).read_text()
  assert not any(s in log for s in ['[HDPack','Script error','handshake timeout','finalization timeout'])
  video=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height,nb_frames','-of','json',str(q/(clip+'_release_replay.avi'))]))['streams'][0]
  assert (video['width'],video['height'])==(1024,960)
  assert frames-2<=int(video['nb_frames'])<=frames
  entry.update({'identical_chr_frames':frames,'hd_video':video})
  report['replays'][clip]=entry
 oldpaths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines()
 approved=[f for f in oldpaths if f.endswith('.png')];assert len(approved)==171
 for f in approved:assert subprocess.check_output(['git','show',BASE+':'+f],cwd=R)==(R/f).read_bytes(),f
 oldlines=subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines()
 lines=(p/'hires.txt').read_text().splitlines();remaining=iter(lines[1:])
 # All old rules and definitions retain their order and text.
 for old in oldlines[1:]:assert any(current==old for current in remaining),old
 imgs=[l[5:] for l in lines if l.startswith('<img>')];assert len(imgs)==len(set(imgs))
 definitions=defaultdict(list);olddefs=defaultdict(list)
 for collection,source in [(definitions,lines),(olddefs,oldlines)]:
  for l in source:
   if l.startswith('<condition>'):collection[l[11:].split(',')[0]].append(l)
 for name,values in definitions.items():
  if len(values)>1:assert values==olddefs[name],name
 names=set(definitions)|{'hmirror','vmirror','bgpriority'};sizes={}
 for f in p.glob('*.png'):
  with Image.open(f) as im:im.load();sizes[f.name]=im.size
 for l in lines:
  if l.startswith('['):assert all(n.lstrip('!') in names for n in l[1:l.index(']')].split('&')),l
  if '<tile>' in l:
   v=l.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[imgs[int(v[0])]];assert 0<=x<=w-32 and 0<=y<=h-32,l
  if '<background>' in l:assert l.split('<background>')[1].split(',')[0] in sizes,l
 assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
 assert {f.name for f in p.iterdir() if f.is_file()}=={f.name for f in rebuild.iterdir() if f.is_file()}
 for f in p.iterdir():
  if f.is_file():assert f.read_bytes()==(rebuild/f.name).read_bytes(),f.name
 colors=json.loads((q/'color_audit_release.json').read_text())
 for clip,cs in colors.items():
  for color,v in cs.items():assert v['pixels']==0,(clip,color,v)
 trace=np.fromfile(q/'boss_native/trace.bin',np.uint8).reshape(-1,4384);counts=Counter();visible=0
 for r in trace:
  cells={int(x):int(t) for y,t,a,x in r[4096:4352].reshape(64,4) if int(y)+1==29 and a==0 and 192<=x<=232 and x%8==0}
  if len(cells)==6:
   pattern=tuple(cells[x] for x in range(192,233,8));counts[pattern]+=1;visible+=1
 assert set(counts)=={(16,16,16,16,18,18)},counts
 # Check actual rendered meter samples, excluding the intentional impact wash.
 meter_samples=0
 for f in (q/'boss_release').glob('*.png'):
  n=int(f.stem);r=trace[n-1];previous=trace[max(0,n-2)]
  if r[4358]!=0x27 or previous[4358]!=0x27:continue
  cells=[t for y,t,a,x in r[4096:4352].reshape(64,4) if y==28 and a==0 and x in range(192,233,8)]
  if len(cells)!=6:continue
  if sum(y==28 and a==0 and x in range(192,233,8) for y,t,a,x in previous[4096:4352].reshape(64,4))!=6:continue
  # Native OAM priority lets a passing cloud or projectile obscure the bar.
  # Check its colors only when all six sample points are unobstructed.
  obstructed=False
  # The end-frame dump may already contain OAM prepared for the next render;
  # screen images can still show the preceding snapshot's occluding sprite.
  for sy,st,sa,sx in np.concatenate([previous[4096:4352],r[4096:4352]]).reshape(-1,4):
   sx,sy,st,sa=map(int,(sx,sy,st,sa))
   if sy==28 and sa==0 and sx in range(192,233,8):continue
   if any(sx<=192+cell*8+2<sx+8 and sy+1<=34<sy+9 for cell in range(6)):
    obstructed=True;break
  if obstructed:continue
  im=Image.open(f).convert('RGB')
  for cell in range(6):
   pixel=im.getpixel((192*4+cell*32+10,29*4+22))
   assert pixel==((239,187,98) if cell<4 else (19,45,50)),(f,cell,pixel)
  meter_samples+=1
 assert meter_samples>40
 report.update({'total_identical_input_frames':sum(CLIPS.values()),'preserved_pngs':approved,
  'decoded_pngs':len(sizes),'isolated_rebuild_identical':True,'old_rules_preserved_in_order':True,
  'native_color_audit':colors,'boss_meter':{'visible_frames':visible,'full_cells':4,'empty_cells':2,
  'verified_rendered_samples':meter_samples,'half_cell_mapping':True,'health_depletion_exercised':False},
  'rom_or_audio_replacements':False,'limitations':['Recorded base approach stages 0-6 only; later sizes, defeat and Mission 3 landing untested.','Boss HP does not decrease in the supplied recording; the native half-cell mapping is not replay-exercised.','CPU state comparison excludes audio-device metadata; PCM is checked separately.'],
  'pack_sha256':{f.name:digest(f) for f in sorted(p.iterdir()) if f.is_file()}})
 (R/'validation/mission3_completion_v0.11.0.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS:',sum(CLIPS.values()),'native/CHR frames, six PCM recordings, 171 preserved PNGs, clean native-color audit, meter rendering, deterministic rebuild.')

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path);ap.add_argument('--rebuild',type=Path,required=True);args=ap.parse_args();validate(args.qa,args.rebuild)
