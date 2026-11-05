"""Scan actual HD gameplay video for native world colors and green HUD cells."""
from pathlib import Path
import argparse,json,subprocess
import numpy as np

ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path);ap.add_argument('run');args=ap.parse_args()
q=args.qa;name='m4boss_'+args.run
trace=np.fromfile(q/'m4boss_native/trace.bin',np.uint8).reshape(-1,4384)
def stream(path,scale=None):
 command=['ffmpeg','-v','error','-threads','1','-i',str(path)]
 if scale:command+=['-vf',scale]
 return subprocess.Popen(command+['-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
n=stream(q/'m4boss_native_replay.avi');h=stream(q/(name+'_replay.avi'),'scale=256:240:flags=neighbor')
size=256*240*3;count=0;bad=[];hudbad=[];active=0
while True:
 nb=n.stdout.read(size);hb=h.stdout.read(size)
 if len(nb)<size or len(hb)<size:break
 frame=count+2;count+=1
 if frame>len(trace) or trace[frame-1,0x18]!=7:continue
 nn=np.frombuffer(nb,np.uint8).reshape(240,256,3)[:128];full=np.frombuffer(hb,np.uint8).reshape(240,256,3);hh=full[:128]
 same=(nn==hh).all(axis=2)
 allowed=(nn.max(axis=2)-nn.min(axis=2)<3)&(nn.max(axis=2)<150)
 allowed|=(nn[:,:,1]>120)&(nn[:,:,0]<30)
 for color in [[228,229,148],[108,6,0],[0,64,77],[173,173,173],[181,49,32]]:allowed|=(nn==color).all(axis=2)
 yy,xx=np.where(same&allowed)
 if len(xx)>2:bad.append(dict(frame=frame,pixels=len(xx),bbox=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]))
 hud=full[144:208,80:176];green=((hud==[92,228,48]).all(axis=2)|(hud==[0,82,0]).all(axis=2))
 nt=trace[frame-1,2048:4096]
 if nt[1024+0x2ac]==0xad and nt[1024+0x2b3]==0xb0:active+=1
 if green.any():hudbad.append(dict(frame=frame,pixels=int(green.sum())))
n.stdout.close();h.stdout.close();assert n.wait()==h.wait()==0
(q/(name+'_video_audit.json')).write_text(json.dumps(dict(video_frames=count,unpainted_frames=len(bad),threshold_pixels=3,frames=bad),indent=2)+'\n')
(q/(name+'_hud_audit.json')).write_text(json.dumps(dict(video_frames=count,active_rear_display_frames=active,native_green_frames=len(hudbad),frames=hudbad),indent=2)+'\n')
print('Scanned',count,'video frames; world suspects',len(bad),bad[:10],'; native green HUD frames',len(hudbad),hudbad[:10])
