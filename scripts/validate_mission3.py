"""Validate the private Mission 3 replay and deterministic installer build.
Usage: python3 scripts/validate_mission3.py QA_ROOT --rebuild PACK --zip ZIP
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile,collections
import numpy as np
from PIL import Image
from validate_mission2 import compare,video_hashes
R=Path(__file__).resolve().parents[1];BASE='74167a8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path);ap.add_argument('--rebuild',type=Path,required=True);ap.add_argument('--zip',type=Path,required=True);a=ap.parse_args();q=a.qa;p=R/'pack'
 report={'version':'0.10.0','base_commit':BASE,'main_merge':'e2af94b7e37740616eb3abfb881a801f5a914f45'}
 report['mission3_replay']=compare(q/'native',q/'release',q/'native_replay.wav',q/'release_replay.wav',21467)
 report['takeoff_final_patch']=compare(q/'takeoff_native',q/'takeoff_final',q/'takeoff_native_replay.wav',q/'takeoff_final_replay.wav',600)
 report['refuel_return_final_patch']=compare(q/'return_native',q/'return_final2',q/'return_native_replay.wav',q/'return_final2_replay.wav',600)
 replayed=(q/'release_replayed_hires.txt').read_text().splitlines();current=(p/'hires.txt').read_text().splitlines()
 added=list((collections.Counter(current)-collections.Counter(replayed)).elements())
 assert not collections.Counter(replayed)-collections.Counter(current)
 takeoff=[l for l in added if '[cockpit&cockpitBorder&missionThree&mission2Takeoff&environmentWorld&mission3Desert]<tile>0,' in l]
 returning=[l for l in added if '[cockpit&cockpitBorder&missionThree&mission2Flight&refuelRoute&mission3RefuelReturn&environmentWorld&mission3Desert]<tile>0,' in l]
 assert len(added)==22 and len(takeoff)==10 and len(returning)==10
 assert set(added)-set(takeoff)-set(returning)=={
  '<condition>mission3RefuelReturn,memoryCheckConstant,009F,==,08',
  '[cockpit&cockpitBorder&missionThree&mission2Flight&refuelRoute&mission3RefuelReturn&mission3Desert&envBank_zero]<background>mission3_sky_edge_zero.png,1,0,0,22'}
 oldkeys={tuple(l.split('<tile>')[1].split(',')[1:3]) for l in replayed if '<tile>' in l}
 assert all(tuple(l.split('<tile>')[1].split(',')[1:3]) in oldkeys for l in takeoff+returning)
 report['takeoff_final_patch'].update({'added_rules':10,'scope':'Mission 3 takeoff mode 6, desert palette, windshield only','new_exact_keys':False,'removed_rules':0,'range':[1801,2400]})
 report['refuel_return_final_patch'].update({'added_tile_rules':10,'added_background_rules':1,'added_conditions':1,'scope':'Mission 3 flight mode 7, route 4, phase 8, desert palette, windshield only','new_exact_keys':False,'removed_rules':0,'range':[16801,17400]})
 assert (q/'native/chr.bin').read_bytes()==(q/'release/chr.bin').read_bytes()
 report['mission3_replay']['identical_chr_frames']=21467
 for token in ['[HDPack','Script error','handshake timeout','finalization timeout']:
  assert token not in (q/'release.log').read_text(),token
 old=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines();old=[f for f in old if f.endswith('.png')];assert len(old)==154
 for f in old:assert (R/f).read_bytes()==subprocess.check_output(['git','show',BASE+':'+f],cwd=R),f
 report['unchanged_v091_pngs']=old
 lines=(p/'hires.txt').read_text().splitlines();imgs=[l[5:] for l in lines if l.startswith('<img>')];assert len(imgs)==len(set(imgs))
 cs={l.split(',')[0][11:] for l in lines if l.startswith('<condition>')}|{'hmirror','vmirror','bgpriority'}
 sizes={}
 for f in p.glob('*.png'):
  with Image.open(f) as im:im.load();sizes[f.name]=im.size
 for l in lines:
  if l.startswith('['):assert all(c.lstrip('!') in cs for c in l[1:l.index(']')].split('&')),l
  if '<tile>' in l:
   v=l.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[imgs[int(v[0])]];assert 0<=x<=w-32 and 0<=y<=h-32,l
  if '<background>' in l:assert l.split('<background>')[1].split(',')[0] in sizes,l
 assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
 names={f.name for f in p.iterdir() if f.is_file()};assert names=={f.name for f in a.rebuild.iterdir() if f.is_file()}
 for f in p.iterdir():
  if f.is_file():assert f.read_bytes()==(a.rebuild/f.name).read_bytes(),f.name
 with zipfile.ZipFile(a.zip) as z:
  assert set(z.namelist())==names
  for name in names:assert z.read(name)==(p/name).read_bytes(),name
 # Live HD captures sampled through all palette transitions and every 120 inputs.
 bad=[];samples=0
 trace=np.fromfile(q/'native/trace.bin',np.uint8).reshape(-1,4384)
 for f in sorted((q/'release').glob('*.png'))+sorted((q/'takeoff_final').glob('*.png'))+sorted((q/'return_final2').glob('*.png')):
  if f.stat().st_size<100:continue
  im=np.array(Image.open(f).convert('RGB'))
  if im.shape[:2]!=(960,1024):continue
  n=int(f.stem)
  if f.parent.name=='release' and trace[n-1,0x30]==3 and trace[n-1,0x18]==6 and trace[n-1,-26]==0x27:continue
  if f.parent.name=='release' and trace[n-1,0x30]==3 and trace[n-1,0x18]==7 and trace[n-1,0x2e]==4 and trace[n-1,0x9f]==8 and trace[n-1,-26]==0x27:continue
  samples+=1
  blue=int(np.all(im[:512]==[100,176,255],axis=2).sum())
  green_world=int(np.all(im[:512]==[92,228,48],axis=2).sum())
  green_hud=int(np.all(im[576:832,320:704]==[92,228,48],axis=2).sum())
  orange=int(np.all(im[:512]==[234,158,34],axis=2).sum())
  if max(blue,green_world,green_hud,orange)>4:bad.append([n,blue,green_world,green_hud,orange])
 assert not bad,bad
 # The movie's leading Mission 2 landing/debrief remains pixel-identical.
 before=video_hashes(q/'before_first246.md5');after=video_hashes(q/'release_first246.md5');assert before==after and len(before)==246
 report.update({'unchanged_preceding_mission2_video_frames':246,'decoded_pngs':len(sizes),
  'visual_samples':samples,'sampled_native_artifact_colors':bad,'isolated_rebuild_identical':True,
  'installer':{'file':a.zip.name,'sha256':sha(a.zip),'files':len(names),'exact_pack':True},
  'pack_sha256':{f.name:sha(f) for f in sorted(p.iterdir()) if f.is_file()},
  'rom_or_audio_replacements':False,
  'limitations':['Movie ends at game over; Mission 3 base boss and landing are not covered.',
   'Unrecorded target layouts, outcomes, Mission 4 and ending need further coverage.',
   'Visual inspection and exact native-color checks are sampled; full replay plus two final 600-frame transition checks cover gameplay and audio.',
   'Audio-device metadata excluded from state dictionaries; PCM checked separately.']})
 (R/'validation/mission3_v0.10.0.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS: 21,467 native/CHR frames, sampled CPU state, identical PCM; 154 preserved PNGs; exact rebuild and installer; visual samples',samples)
if __name__=='__main__':main()
