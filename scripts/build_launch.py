from pathlib import Path
from PIL import Image
import numpy as np, shutil, json
R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
masters={'carrier_clean_master.png':'exec-e8d5f3dc-3f5b-4f00-9fae-069007e081b9.png','director_sheet.png':'exec-470b0db3-ed82-42c2-8f61-f8292da9084b.png','flames_sheet.png':'exec-98af10b0-ebbc-40cb-bf29-e9dc8e87fbc1.png'}
for dst,src in masters.items():
 if not (S/dst).exists():shutil.copy(R.parent/'generated_images'/src,S/dst)
plate=Image.open(S/'carrier_clean_master.png').convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS);plate.save(P/'carrier.pending.png');(P/'carrier.pending.png').replace(P/'carrier.png')
# Extract sprite cells and register them by their feet, not their changing arm bounds.
sheet=Image.open(S/'director_sheet.png').convert('RGBA');w,h=sheet.size
for pose in range(2):
 cell=sheet.crop((pose*w//2,0,(pose+1)*w//2,h));a=np.array(cell)[:,:,3]
 ys,xs=np.where(a>40);footy=int(ys.max());mask=a[max(0,footy-15):footy+1]>40
 footx=float(np.where(mask)[1].mean());scale=.092
 small=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
 layer=Image.new('RGBA',(1024,960));layer.alpha_composite(small,(round(950-footx*scale),round(692-footy*scale)))
 layer.save(P/f'director_{pose}.png')
# Four imagegen VFX phases, registered to the white-hot emitter root in each cell.
sheet=Image.open(S/'flames_sheet.png').convert('RGBA');w,h=sheet.size
phases=[]
for j in range(4):
 cell=sheet.crop(((j%2)*w//2,(j//2)*h//2,(j%2+1)*w//2,(j//2+1)*h//2));a=np.array(cell)
 bright=(a[:,:,0]>235)&(a[:,:,1]>230)&(a[:,:,2]>200)&(a[:,:,3]>120)
 yy,xx=np.where(bright);phases.append((cell,float(xx.mean()),float(yy.mean())))
# Use the ROM's actual sprite pattern states, including the ignition ramp.
# Captured native state keys are part of the source, so rebuilding needs no trace run.
mapping=S/'launch_mappings.json'
if mapping.exists():
 states={int(k):tuple(v) for k,v in json.loads(mapping.read_text())['original_states'].items()}
else:
 trace=R/'captures/launch_trace';states={}
 for p in sorted(trace.glob('*.oam')):
  n=int(p.stem)
  if n>1180:continue
  o=p.read_bytes()
  for i in range(0,256,4):
   if o[i+3]<=48<o[i+3]+8 and o[i]+1<=145<o[i]+9:
    t=o[i+1];states.setdefault(t,(n,p.with_suffix('.chr').read_bytes()[(256+t)*16:(257+t)*16].hex().upper()))
assert len(states)==8, 'Expected all eight native launch animation states'
conditions=['<condition>directorRaised,ppuMemoryCheckConstant,229C,==,94']
backgrounds=['[carrier&directorRaised]<background>director_1.png,1,0,0,32','[carrier&!directorRaised]<background>director_0.png,1,0,0,32']
settings={2:(0,.22),8:(1,.42),16:(0,.64),27:(1,.78),40:(0,.88),58:(1,1),80:(2,1),104:(3,1)}
for t,(n,key) in states.items():
 phase,mul=settings[t];cell,rx,ry=phases[phase];sx=.26*mul;sy=.38*mul
 small=cell.resize((max(1,round(cell.width*sx)),max(1,round(cell.height*sy))),Image.Resampling.LANCZOS)
 layer=Image.new('RGBA',(1024,960))
 for ex,ey in [(209,568),(452,576)]:layer.alpha_composite(small,(round(ex-rx*sx),round(ey-ry*sy)))
 fn=f'exhaust_{t:02X}.png';layer.save(P/fn)
 conditions.append(f'<condition>exhaust{t:02X},spriteAtPosition,48,145,{key},FF202615,Y')
 backgrounds.append(f'[carrier&exhaust{t:02X}]<background>{fn},1,0,0,31,0,0,Add')
(R/'source/launch_mappings.json').write_text(json.dumps({'conditions':conditions,'backgrounds':backgrounds,'original_states':states},indent=2)+'\n')
print('Launch:',len(states),'flame states, two director poses')
