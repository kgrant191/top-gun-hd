"""Validate Mission 4 private captures and reproducible install pack."""
from pathlib import Path
import argparse,json,subprocess,hashlib,wave
from PIL import Image
from validate_mission2 import compare,digest,pcm,state
from validate_mission3_radar_edges import hashes
R=Path(__file__).resolve().parents[1];BASE='5b53b7b84529bd5a72e648b5a70964169e7d6fc1'
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path);ap.add_argument('--previous-qa',type=Path,required=True);ap.add_argument('--rebuild',type=Path,required=True);args=ap.parse_args();q=args.qa;p=R/'pack';prev=args.previous_qa
 report={'version':'0.12.0','approved_base':BASE}
 report['mission4']=compare(q/'mission4_native',q/'mission4_release',q/'mission4_native_replay.wav',q/'mission4_release_replay.wav',10352)
 assert (q/'mission4_native/chr.bin').read_bytes()==(q/'mission4_release/chr.bin').read_bytes()
 assert (q/'baseclose_regression/trace.bin').read_bytes()==(prev/'baseclose_native/trace.bin').read_bytes()
 assert (q/'baseclose_regression/chr.bin').read_bytes()==(prev/'baseclose_native/chr.bin').read_bytes()
 assert pcm(q/'baseclose_regression_replay.wav')==pcm(prev/'baseclose_native_replay.wav')
 a,b=hashes(prev/'baseclose_candidate_replay.avi'),hashes(q/'baseclose_regression_replay.avi');common=min(len(a),len(b));assert common>=2681 and a[:common]==b[:common]
 report['mission3_regression']={'identical_native_inputs':2683,'identical_hd_video_frames':common,'identical_pcm':True}
 for run in ['mission4_release','baseclose_regression']:
  log=(q/(run+'.log')).read_text();assert not any(s in log for s in ['[HDPack','Script error','handshake timeout','finalization timeout'])
  assert(q/(run+'_replay.end')).exists()
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines();preserved=[f for f in paths if f.endswith('.png')];assert len(preserved)==186
 for f in preserved:assert subprocess.check_output(['git','show',BASE+':'+f],cwd=R)==(R/f).read_bytes(),f
 old=subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines();lines=(p/'hires.txt').read_text().splitlines();remaining=iter(lines[1:])
 for l in old[1:]:assert any(v==l for v in remaining),l
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
 report.update({'unchanged_approved_pngs':len(preserved),'old_rules_preserved_in_order':True,'full_rebuild_identical':True,
 'full_video_original_sprite_audit':json.loads((q/'release_video_audit.json').read_text()),
 'limitations':['The recording ends at game over during ocean combat. Later Mission 4 terrain, refueling, space-shuttle target and ending are unrecorded.',
 'Native video capture may omit one final frame; trace and PCM cover all inputs.'],
 'pack_sha256':{f.name:digest(f) for f in sorted(p.iterdir())}})
 assert report['full_video_original_sprite_audit']['unpainted_frames']==0
 (R/'validation/mission4_v0.12.0.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS: 10,352 Mission 4 inputs and PCM; 2,683 Mission 3 regression inputs and unchanged video; 186 preserved PNGs; deterministic rebuild.')
if __name__=='__main__':main()
