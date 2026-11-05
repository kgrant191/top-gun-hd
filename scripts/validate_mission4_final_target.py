"""Validate the new shuttle movie and two earlier Mission 4 regressions."""
from pathlib import Path
import argparse,json,subprocess
import numpy as np
from PIL import Image
from validate_mission2 import compare,digest,pcm,state

R=Path(__file__).resolve().parents[1]
BASE='26caa213315ecbbfb3227af57ae558459d418b14'

def compare_regression(a,b,aw,bw,frames):
 # The refueling capture lacks one checkpoint set. Full per-input traces,
 # CHR, audio and rendered video still cover that input without a gap.
 assert (a/'trace.bin').stat().st_size==frames*4384
 assert (a/'trace.bin').read_bytes()==(b/'trace.bin').read_bytes()
 counts={}
 for ext in ['ram','chr','nt','oam','pal','state']:
  files=sorted(a.glob('*.'+ext));assert files
  missing=[f.name for f in files if not (b/f.name).exists()]
  assert missing==['00180.'+ext],missing
  for f in files:
   if f.name in missing:continue
   g=b/f.name
   assert (state(f)==state(g) if ext=='state' else f.read_bytes()==g.read_bytes()),f
  counts[ext]=len(files)-len(missing)
 audio=pcm(aw);assert audio==pcm(bw)
 return {'identical_native_trace_frames':frames,'identical_checkpoints':counts,
  'unavailable_checkpoint_frames':[180],'identical_pcm':audio,'trace_sha256':digest(a/'trace.bin')}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path);ap.add_argument('--rebuild',type=Path,required=True);args=ap.parse_args();q=args.qa;p=R/'pack'
 report={'version':'0.14.0','previous_review_commit':BASE,'replays':{}}
 for clip,run,frames in [('m4boss','complete',8420),('m4later','v014',6535),('mission4','v014',10352)]:
  name=clip+'_'+run
  compare_capture=compare_regression if clip=='m4later' else compare
  result=compare_capture(q/(clip+'_native'),q/name,q/(clip+'_native_replay.wav'),q/(name+'_replay.wav'),frames)
  assert (q/(clip+'_native/chr.bin')).read_bytes()==(q/(name+'/chr.bin')).read_bytes()
  result['full_chr_trace_identical']=True
  assert (q/(name+'_replay.end')).exists()
  log=(q/(name+'.log')).read_text()
  assert not any(s in log for s in ['[HDPack','Script error','handshake timeout','finalization timeout'])
  if clip=='m4boss':
   audit=json.loads((q/(name+'_video_audit.json')).read_text());assert audit['unpainted_frames']==0,audit['frames'][:10]
   assert audit['video_frames']>=frames-2;result['native_color_video_audit']=audit
   hud=json.loads((q/(name+'_hud_audit.json')).read_text());assert hud['native_green_frames']==0,hud;result['rear_display_video_audit']=hud
  else:
   cached=json.loads((q/(clip+'_v014_comparison.json')).read_text())
   assert cached['current_sha256']==digest(q/(name+'_replay.avi'))
   baseline=q/('m4later_delivery3_replay.avi' if clip=='m4later' else 'mission4_regression_replay.avi')
   assert cached['baseline_sha256']==digest(baseline)
   assert cached['common_video_frames']>=frames-2
   assert not cached['changed_hd_frames'],cached['changed_hd_frames'][:20]
   result['hd_video_identical_to_v013']=cached
   # The final mast alignment changes only helicopter atlas cells; those
   # exact CHR/palette pairs are absent from these earlier recordings.
   mapping=json.loads((R/'source/mission4_final_target_mappings.json').read_text())
   keys={t['pattern'] for e in mapping['helicopters'] for t in e['tiles']}
   trace=np.fromfile(q/(clip+'_native/trace.bin'),np.uint8).reshape(-1,4384)
   impact=(trace[:,0x18]==7)&(trace[:,0x30]==4)&(trace[:,0x4e]==0)&(trace[:,2048+0x2ef]>=0xc0)
   assert not impact.any()
   chrtrace=np.memmap(q/(clip+'_native/chr.bin'),np.uint8,mode='r',shape=(len(trace),8192))
   for f,row in enumerate(trace):
    if row[0x18]!=7 or row[0x30]!=4:continue
    pal=row[4352:]
    for sy,tile,attr,sx in row[4096:4352].reshape(64,4).astype(int):
     if sy>=127:continue
     if ('FF'+pal[16+(attr&3)*4+1:16+(attr&3)*4+4].tobytes().hex().upper())!='FF20180F':continue
     assert chrtrace[f,4096+tile*16:4096+tile*16+16].tobytes().hex().upper() not in keys
   result['final_helicopter_polish_inactive_in_capture']=True
   result['final_boss_impact_rule_inactive_in_capture']=True
  report['replays'][clip]=result
 oldpaths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines()
 preserved=[f for f in oldpaths if f.endswith('.png')];assert len(preserved)==232
 for f in preserved:assert subprocess.check_output(['git','show',BASE+':'+f],cwd=R)==(R/f).read_bytes(),f
 old=subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines();lines=(p/'hires.txt').read_text().splitlines();remaining=iter(lines[1:])
 for line in old[1:]:assert any(v==line for v in remaining),line
 imgs=[l[5:] for l in lines if l.startswith('<img>')];assert len(imgs)==len(set(imgs))
 names={l[11:].split(',')[0] for l in lines if l.startswith('<condition>')}|{'hmirror','vmirror','bgpriority'};sizes={}
 for f in p.glob('*.png'):
  with Image.open(f) as im:im.load();sizes[f.name]=im.size
 for line in lines:
  if line.startswith('['):assert all(n.lstrip('!') in names for n in line[1:line.index(']')].split('&')),line
  if '<tile>' in line:
   v=line.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[imgs[int(v[0])]];assert 0<=x<=w-32 and 0<=y<=h-32,line
  if '<background>' in line:assert line.split('<background>')[1].split(',')[0] in sizes,line
 assert not any('<'+tag+'>' in '\n'.join(lines) for tag in ['patch','bgm','sfx'])
 files=lambda root:{f.name:f for f in root.iterdir() if f.is_file() and not f.name.startswith('.')}
 actual,rebuilt=files(p),files(args.rebuild);assert actual.keys()==rebuilt.keys()
 for name,f in actual.items():assert f.read_bytes()==rebuilt[name].read_bytes(),name
 report.update({'preserved_png_count':len(preserved),'old_rules_preserved_in_order':True,'isolated_rebuild_identical':True,
  'limitations':['Shuttle sizes after stage 6, target defeat, launch and ending are absent.','AVI may omit one or two edge frames; trace and PCM cover every supplied input.',
   'Refueling regression checkpoint 180 is unavailable; full native/CHR traces, audio and HD video cover it.'],
  'pack_sha256':{name:digest(f) for name,f in sorted(actual.items())}})
 (R/'validation/mission4_final_target_v0.14.0.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS: 8,420 new inputs; 16,887 regression inputs; native state, CHR and PCM unchanged; 232 preserved PNGs; clean rebuild.')

if __name__=='__main__':main()
