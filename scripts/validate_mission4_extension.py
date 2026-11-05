"""Validate all five added replays, original Mission 4 regression, and rebuild."""
from pathlib import Path
import argparse, json, subprocess
from PIL import Image
from validate_mission2 import compare, digest, pcm
from validate_mission3_radar_edges import hashes

R=Path(__file__).resolve().parents[1]
BASE='235658ec0b1b7b32462a7f5a520edd01bae7686c'
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path);ap.add_argument('--rebuild',type=Path,required=True);args=ap.parse_args();q=args.qa;p=R/'pack'
 report={'version':'0.13.0','previous_review_commit':BASE,'replays':{}}
 for clip,frames in [('m4clip1',651),('m4clip2',978),('m4clip3',252),('m4clip4',256),('m4later',6535)]:
  run=clip+('_delivery3' if clip=='m4later' else '_complete')
  result=compare(q/(clip+'_native'),q/run,q/(clip+'_native_replay.wav'),q/(run+'_replay.wav'),frames)
  assert (q/(clip+'_native/chr.bin')).read_bytes()==(q/(run+'/chr.bin')).read_bytes()
  result['full_chr_trace_identical']=True
  audit=json.loads((q/(run+'_video_audit.json')).read_text());assert audit['unpainted_frames']==0,(clip,audit['frames'][:10]);assert audit['video_frames']>=frames-2
  result['original_sprite_color_audit']=audit
  import numpy as np
  trace=np.fromfile(q/(clip+'_native/trace.bin'),np.uint8).reshape(-1,4384)
  mismatched=np.flatnonzero(((trace[:,4358]==0x10)&(trace[:,0x37]!=3))|((trace[:,4358]==6)&(trace[:,0x37]!=2)))
  if clip=='m4later':
   assert (mismatched+1).tolist()==[5481]
   result['terrain_transition_guard_verified_in_final_capture']=[5481]
  else:
   assert len(mismatched)==0
   result['final_terrain_phase_guard_does_not_change_this_capture']=True
  if clip!='m4later':
   active=(trace[:,0x18]==7)&(trace[:,0x30]==4)
   assert not (active&np.isin(trace[:,0x37],[2,3])).any()
   assert not (active&(trace[:,0x2e]==4)&(trace[:,0x9f]>=1)).any()
   result['final_refuel_mask_and_flame_rules_inactive']=True
  report['replays'][clip]=result
  log=(q/(run+'.log')).read_text();assert not any(s in log for s in ['[HDPack','Script error','handshake timeout','finalization timeout']);assert (q/(run+'_replay.end')).exists()
 # The original long movie retains its native trace and audio. Its HD video
 # should also remain identical; new exact keys preserve old generic fallbacks.
 assert (q/'mission4_native/trace.bin').read_bytes()==(q/'mission4_regression/trace.bin').read_bytes()
 assert (q/'mission4_native/chr.bin').read_bytes()==(q/'mission4_regression/chr.bin').read_bytes()
 assert pcm(q/'mission4_native_replay.wav')==pcm(q/'mission4_regression_replay.wav')
 cache=q/'m4_final_regression_video.json'
 if cache.exists():
  cached=json.loads(cache.read_text())
  assert cached['baseline_sha256']==digest(q/'mission4_v012_replay.avi') and cached['current_sha256']==digest(q/'mission4_regression_replay.avi')
  common=cached['common_video_frames'];changed=cached['changed_hd_frames']
 else:
  a,b=hashes(q/'mission4_v012_replay.avi'),hashes(q/'mission4_regression_replay.avi');common=min(len(a),len(b));changed=[i+2 for i,(x,y) in enumerate(zip(a,b)) if x!=y]
 report['earlier_mission4_regression']={'native_inputs':10352,'full_trace_and_chr_identical':True,'pcm_identical':True,'common_video_frames':common,'changed_hd_frames':changed}
 assert common>=10350
 assert not changed,changed[:20]
 audit=json.loads((q/'mission4_regression_video_audit.json').read_text())
 report['earlier_mission4_regression']['native_color_candidates_identical_to_v012']=audit
 import numpy as np
 trace=np.fromfile(q/'mission4_native/trace.bin',np.uint8).reshape(-1,4384)
 active=(trace[:,0x18]==7)&(trace[:,0x30]==4)
 assert not (active&np.isin(trace[:,0x37],[2,3])).any()
 assert not (active&(trace[:,0x2e]==4)&(trace[:,0x9f]>=1)).any()
 report['earlier_mission4_regression']['final_refuel_mask_and_flame_rules_inactive']=True
 oldpaths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines();preserved=[f for f in oldpaths if f.endswith('.png')];assert len(preserved)==216
 for f in preserved:assert subprocess.check_output(['git','show',BASE+':'+f],cwd=R)==(R/f).read_bytes(),f
 old=subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines();lines=(p/'hires.txt').read_text().splitlines();remaining=iter(lines[1:])
 for l in old[1:]:
  l=l.replace('&!missionTwo&!missionThree]<background>mission2_tanker.png','&!missionTwo&!missionThree&!missionFour]<background>mission2_tanker.png')
  assert any(v==l for v in remaining),l
 imgs=[l[5:] for l in lines if l.startswith('<img>')];assert len(imgs)==len(set(imgs));names={l[11:].split(',')[0] for l in lines if l.startswith('<condition>')}|{'hmirror','vmirror','bgpriority'};sizes={}
 for f in p.glob('*.png'):
  with Image.open(f) as im:im.load();sizes[f.name]=im.size
 for l in lines:
  if l.startswith('['):assert all(n.lstrip('!') in names for n in l[1:l.index(']')].split('&')),l
  if '<tile>' in l:
   v=l.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[imgs[int(v[0])]];assert 0<=x<=w-32 and 0<=y<=h-32,l
  if '<background>' in l:assert l.split('<background>')[1].split(',')[0] in sizes,l
 assert not any('<'+tag+'>' in '\n'.join(lines) for tag in ['patch','bgm','sfx'])
 assert {f.name for f in p.iterdir()}=={f.name for f in args.rebuild.iterdir()}
 for f in p.iterdir():assert f.read_bytes()==(args.rebuild/f.name).read_bytes(),f.name
 report.update({'unchanged_previous_pngs':len(preserved),'old_rules_preserved_in_order_except_scoped_tanker_fallback':True,'full_rebuild_identical':True,
  'limitations':['Final target and ending are absent from these recordings.','AVI captures may omit up to two edge frames; trace and PCM cover every input.'],
  'pack_sha256':{f.name:digest(f) for f in sorted(p.iterdir())}})
 (R/'validation/mission4_extension_v0.13.0.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS: 8,672 new inputs, 10,352 regression inputs, identical native trace/CHR/audio, 216 preserved PNGs, deterministic rebuild.')
 print('Regression HD changes:',len(changed),changed[:20])
if __name__=='__main__':main()
