"""Verify native replays, artwork preservation and deterministic ending build."""
from pathlib import Path
import argparse,json,subprocess
import numpy as np
from PIL import Image
from validate_mission2 import compare,digest
R=Path(__file__).resolve().parents[1]
BASE='cbeb2347ec1b6d0cdbb3c241bc414f393717744c'
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path);ap.add_argument('--rebuild',type=Path,required=True);args=ap.parse_args();q=args.qa;p=R/'pack'
report={'version':'0.15.0','base_commit':BASE,'replays':{}}
for clip,run,frames in [('m4end1','checked015',4755),('m4ending','final015',2205),('m4boss','checked015',8420)]:
 name=clip+'_'+run;a=q/(clip+'_native');b=q/name
 result=compare(a,b,q/(clip+'_native_replay.wav'),q/(name+'_replay.wav'),frames)
 assert (a/'chr.bin').read_bytes()==(b/'chr.bin').read_bytes();result['full_chr_trace_identical']=True
 assert (q/(name+'_replay.end')).exists()
 assert not any(s in (q/(name+'.log')).read_text() for s in ['[HDPack','Script error','handshake timeout','finalization timeout'])
 if clip!='m4ending':
  audit=json.loads((q/(name+'_video_audit.json')).read_text());assert audit['video_frames']>=frames-2
  assert not audit['unpainted_frames'],audit['frames'][:10];result['world_video_audit']=audit
  hud=json.loads((q/(name+'_hud_audit.json')).read_text());assert not hud['native_green_frames'];result['hud_video_audit']=hud
 else:
  # Confirm all five native poses, including the arm-up/down alternation.
  trace=np.fromfile(a/'trace.bin',np.uint8).reshape(-1,4384);chrtrace=np.memmap(a/'chr.bin',np.uint8,mode='r',shape=(frames,8192))
  m=json.loads((R/'source/ending_mappings.json').read_text());counts={};fallback=[]
  for f,row in enumerate(trace):
   if row[0x18]!=11 or row[2048+0x288]!=0x8a:continue
   oam=row[4096:4352].reshape(64,4);selected=-1
   for phase,e in enumerate(m['canopy_phases']):
    if all(any(int(x)==t['x'] and int(y)+1==t['y'] and (int(attr)&3)==1 and chrtrace[f,4096+int(tile)*16:4096+(int(tile)+1)*16].tobytes().hex().upper()==t['pattern'] for y,tile,attr,x in oam) for t in e['tiles']):selected=phase;break
   counts[selected]=counts.get(selected,0)+1
   if selected==-1:fallback.append(f+1)
  assert counts=={-1:3,0:311,1:16,2:48,3:256,4:1245},counts
  assert fallback==[108,109,110]
  result['native_canopy_pose_counts']=counts;result['native_setup_frames']=fallback
  # Confirm the actual emulator output includes the opening and both arm poses.
  poses={180:0,480:2,660:3,900:4}
  for frame,phase in poses.items():
   rendered=np.array(Image.open(b/f'{frame:05}.png').convert('RGB'))[316:484,600:880]
   expected=np.array(Image.open(p/f'ending_carrier_{phase}.png').convert('RGB'))[316:484,600:880]
   assert np.array_equal(rendered,expected),(frame,phase)
  result['rendered_animation_pose_checks']=poses

 if clip=='m4boss':
  video=json.loads((q/'m4boss_v015_comparison.json').read_text());assert video['current_sha256']==digest(q/(name+'_replay.avi'))
  assert video['baseline_sha256']==digest(q/'m4boss_complete_replay.avi')
  assert not video['unexpected_changed_frames'],video['unexpected_changed_frames'][:10];result['v014_regression']=video
 report['replays'][clip]=result
oldpaths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines();preserved=[f for f in oldpaths if f.endswith('.png')];assert len(preserved)==240
for f in preserved:assert subprocess.check_output(['git','show',BASE+':'+f],cwd=R)==(R/f).read_bytes(),f
old=subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines();lines=(p/'hires.txt').read_text().splitlines();remaining=iter(lines[1:])
for line in old[1:]:assert any(v==line for v in remaining),line
imgs=[l[5:] for l in lines if l.startswith('<img>')];assert len(imgs)==len(set(imgs));sizes={}
names={l[11:].split(',')[0] for l in lines if l.startswith('<condition>')}|{'hmirror','vmirror','bgpriority'}
for f in p.glob('*.png'):
 with Image.open(f) as im:im.load();sizes[f.name]=im.size
for line in lines:
 if line.startswith('['):assert all(n.lstrip('!') in names for n in line[1:line.index(']')].split('&')),line
 if '<tile>' in line:
  v=line.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[imgs[int(v[0])]];assert 0<=x<=w-32 and 0<=y<=h-32,line
 if '<background>' in line:
  v=line.split('<background>')[1].split(',');assert v[0] in sizes and 0<=int(v[4])<40,line
  if len(v)>6 and v[0].startswith('ending_'):assert int(v[5])>=0 and int(v[6])>=0,line
assert not any('<'+tag+'>' in '\n'.join(lines) for tag in ['patch','bgm','sfx'])
files=lambda root:{f.name:f for f in root.iterdir() if f.is_file() and not f.name.startswith('.')}
actual,rebuilt=files(p),files(args.rebuild);assert actual.keys()==rebuilt.keys()
for name,f in actual.items():assert f.read_bytes()==rebuilt[name].read_bytes(),name
report.update({'preserved_png_count':len(preserved),'old_rules_preserved_in_order':True,'isolated_rebuild_identical':True,'rom_or_audio_replacements':False,
 'limitations':['The supplied movies do not cover a continuous shuttle-defeat-to-success transition.','AVI may omit one or two edge frames; trace and PCM cover every input.','Other unrecorded outcomes, including Mission 3 boss defeat and landing, remain unverified.'],
 'pack_sha256':{name:digest(f) for name,f in sorted(actual.items())}})
(R/'validation/ending_v0.15.0.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 6,960 new inputs and 8,420 regression inputs; native state, CHR and PCM; 240 preserved PNGs; isolated rebuild.')
