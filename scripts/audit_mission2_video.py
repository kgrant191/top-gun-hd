"""Audit decoded HD frames for native world/HUD pixels and alignment."""
from pathlib import Path
import argparse,hashlib,json,subprocess,numpy as np
ap=argparse.ArgumentParser();ap.add_argument('video',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--trace',type=Path,required=True);ap.add_argument('--first-input',type=int,choices=[2,3]);args=ap.parse_args()
tr=np.fromfile(args.trace,np.uint8).reshape(-1,4384)
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=nb_frames,width,height','-of','json',str(args.video)]))['streams'][0]
expected=int(meta['nb_frames']);first=args.first_input or len(tr)-expected+1
assert first in (2,3), (expected,first)
p=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-i',str(args.video),'-vf','scale=256:240:flags=neighbor','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
blue=[];green=[];green_world=[];meter=[];fighters=[];panel=[];i=first;size=256*240*3
while True:
 raw=p.stdout.read(size)
 if not raw:break
 a=np.frombuffer(raw,np.uint8).reshape(240,256,3)
 panel.append(hashlib.sha256(a[144:240,:76].tobytes()).hexdigest())
 if tr[i-1,0x18] in [6,7]:
  world=a[:128];hud=a[144:208,80:176]
  b=np.all(world==[21,95,217],axis=2)|np.all(world==[100,176,255],axis=2)
  g=np.all(hud==[92,228,48],axis=2)
  if b.sum()>=8:blue.append([i,int(b.sum())])
  if g.sum()>0:green.append([i,int(g.sum())])
  gw=np.all(world==[92,228,48],axis=2)
  if gw.sum()>1:green_world.append([i,int(gw.sum())])
  m=np.all(a[27:39,190:241]==[92,228,48],axis=2)
  if m.sum()>0:meter.append([i,int(m.sum())])
  f=np.all(world==[12,147,0],axis=2)|np.all(world==[228,229,148],axis=2)
  if f.sum()>1:fighters.append([i,int(f.sum())])
 i+=1
assert p.wait()==0
assert i-first==expected
r={'video_frames':i-first,'first_input_frame':first,'video_meta':meta,'native_blue_frames':blue,'native_green_hud_frames':green,'native_green_world_frames':green_world,'native_green_meter_frames':meter,'native_fighter_color_frames':fighters,'unchanged_panel_sha256':panel}
args.out.write_text(json.dumps(r));print('Video',args.video.name, 'frames',i-first,'first input',first,'blue',len(blue),'green HUD',len(green),'firstgreen',green[:8])
