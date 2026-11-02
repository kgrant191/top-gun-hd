"""Precise flight-display graphics and native impact-shake registration."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import math, json
from pack_io import save_png

R=Path(__file__).resolve().parents[1]; P=R/'pack'
fontpath=R/'source/fonts/DejaVuSansMono-Bold.ttf'
if not fontpath.exists(): fontpath=Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf')
chrdata=(R/'captures/baseline/03240.chr').read_bytes()
def pat(i): return chrdata[i*16:(i+1)*16].hex().upper()
def decode(i,data=chrdata):
 b=data[i*16:(i+1)*16]
 return np.array([[((b[y]>>(7-x))&1)+2*((b[y+8]>>(7-x))&1) for x in range(8)] for y in range(8)])

# Artwork is registered to native screen coordinates; keep the surrounding painted metal.
base=Image.open(P/'cockpit.png').convert('RGBA'); d=ImageDraw.Draw(base)
def label(x,y,t,size=12,fill='#9fb9b7',anchor='lt'):
 d.text((x*4,y*4),t,font=ImageFont.truetype(str(fontpath),size),fill=fill,anchor=anchor)
# Dark, restrained phosphor surface. Native symbols supply all live information.
yy,xx=np.mgrid[0:256,0:368];glow=np.exp(-(((xx-184)/230)**2+((yy-105)/190)**2))
rgb=np.stack([3+3*glow,14+10*glow,15+8*glow],axis=-1).astype('uint8')
rgb[::4]=np.clip(rgb[::4].astype(int)-1,0,255)
base.paste(Image.fromarray(rgb),(80*4,144*4)); d=ImageDraw.Draw(base)
label(128,130.5,'FIRE CONTROL',12,'#b5c5bd','mt')
label(11.5,222.6,'FUEL',11,'#a9bbb7','mt')
label(44,222.6,'ATTITUDE',11,'#a9bbb7','mt')
# Subtle monitor trim remains outside the native 96x64 information area.
d.line((80*4,207.7*4,174*4,207.7*4),fill='#345a57',width=2)
save_png(base,P/'cockpit.png')

conditions=[
 f'<condition>cockpitBorder,tileAtPosition,180,148,{pat(0x5a)},00000000,Y',
 '<condition>impactLeft,memoryCheckConstant,007E,==,01',
 '<condition>impactRight,memoryCheckConstant,007E,==,FF',
 '<condition>flightX0,positionCheckX,>=,78','<condition>flightX1,positionCheckX,<,178',
 '<condition>flightY0,positionCheckY,>=,143','<condition>flightY1,positionCheckY,<,209',
 '<condition>messageY0,positionCheckY,>=,160','<condition>messageY1,positionCheckY,<,184',
 '<condition>landingNumberY,positionCheckY,>=,192',
 '<condition>landingNumberX,positionCheckX,>=,142',
 '<condition>guideLeft0,originPositionCheckX,>=,79','<condition>guideLeft1,originPositionCheckX,<,82',
 '<condition>guideRight0,originPositionCheckX,>=,167','<condition>guideRight1,originPositionCheckX,<,170',
]
flight='cockpit&flightX0&flightX1&flightY0&flightY1'
atlas=Image.new('RGBA',(512,512));rules=[];slot=0
def add(i,im,cond=flight,sprite=False,key=None,strict=False):
 global slot
 x=slot%16*32;y=slot//16*32;atlas.alpha_composite(im,(x,y));slot+=1
 rules.append(f'[{cond}]<tile>3,{key or pat(i)},{"FF2A100F" if sprite else "0F2A0A31"},{x},{y},1,{"N" if strict else "Y"}')
def glyph(t,color='#a7eac6',size=23):
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 dr.text((16,15),t,font=ImageFont.truetype(str(fontpath),size),fill=color,anchor='mm')
 return im

# The ROM's ten four-tile digit definitions (PRG file offset 0x1E0B8).
# Decode the displayed value from all four native tiles, then draw a complete HD digit.
large_digits=[(0x3f,0x40,0x49,0x4a),(0x2a,0x42,0x4b,0x4c),
 (0x45,0x46,0x49,0x4e),(0x41,0x46,0x4d,0x4a),(0x47,0x48,0x4b,0x4c),
 (0x43,0x44,0x4d,0x4a),(0x43,0x44,0x49,0x4a),(0x3f,0x40,0x4b,0x4c),
 (0x43,0x46,0x49,0x4a),(0x43,0x46,0x4d,0x4a)]
for side,x,addr in [('L',208,0x2a5a),('R',224,0x2a5c)]:
 for q in range(4):
  ox=x+(q%2)*8;oy=144+(q//2)*8
  for axis,v in [('X',ox),('Y',oy)]:
   conditions.extend([f'<condition>count{side}{q}{axis}0,originPositionCheck{axis},>=,{v-1}',f'<condition>count{side}{q}{axis}1,originPositionCheck{axis},<,{v+2}'])
 for value,tiles in enumerate(large_digits):
  names=[]
  for q,t in enumerate(tiles):
   name=f'count{side}{value}q{q}';names.append(name)
   conditions.append(f'<condition>{name},ppuMemoryCheckConstant,{addr+q%2+(q//2)*32:04X},==,{t:02X}')
  im=Image.new('RGBA',(64,64));dr=ImageDraw.Draw(im)
  dr.text((32,31),str(value),font=ImageFont.truetype(str(fontpath),52),fill='#b9efd0',anchor='mm')
  for q,t in enumerate(tiles):
   crop=im.crop(((q%2)*32,(q//2)*32,(q%2+1)*32,(q//2+1)*32))
   pos='&'.join(f'count{side}{q}{axis}{edge}' for axis in ['X','Y'] for edge in [0,1])
   add(t,crop,'cockpit&'+'&'.join(names)+'&'+pos)

# Native 0/I/5 glyphs double as O/I/S. Scope word forms to the instruction lines.
for i,t in [(1,'O'),(2,'I'),(6,'S')]: add(i,glyph(t),flight+'&messageY0&messageY1')
for i in range(1,11): add(i,glyph(str(i-1)),flight+'&landingNumberY&landingNumberX')
for i in range(0x10,0x2a):
 if i==0x1e: continue
 add(i,glyph(':' if i==0x18 else chr(65+i-0x10)))
for i in range(1,11): add(i,glyph(str(i-1)))
for i,t in [(0x0b,"'"),(0x0c,'.'),(0x0d,'?'),(0x0e,'!'),(0x3e,'-')]:add(i,glyph(t))

# Radar grid: thin, muted lines with a distinct bright own-aircraft symbol.
for i in [0x98,0x99]:
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 dr.line((16,0,16,31),fill='#285e4d',width=2)
 dr.line((0,16,31,16),fill='#285e4d',width=2)
 if i==0x99:
  dr.line((8,19,16,11,24,19),fill='#c1f8d2',width=3)
  dr.line((16,11,16,24),fill='#c1f8d2',width=2)
 add(i,im)
# The radar edge ticks share native CHR with attitude bezel tiles.
for i in [0x72,0x75]:
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 if i==0x72:dr.line((0,16,13,16),fill='#528b72',width=2)
 add(i,im)

# Landing guidance lines and native aircraft pitch/bank shapes.
for side,x0,x1 in [('Left',8,31),('Right',0,22)]:
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 dr.line((x0,17,x1,17),fill='#3d7565',width=2)
 add(0x9b,im,flight+f'&guide{side}0&guide{side}1')
for i in range(0x9b,0xab):
 a=decode(i);im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 if i==0x9b:dr.line((0,17,31,17),fill='#3d7565',width=2)
 else:
  mask=Image.fromarray(((a==1)*255).astype('uint8')).resize((32,32),Image.Resampling.LANCZOS)
  im=Image.new('RGBA',(32,32),'#b5f5cf');im.putalpha(mask)
 add(i,im)

# Fuel: the half-filled tile was absent from the previous mapping.
for i,levels in [(0x80,(True,True)),(0x81,(False,False)),(0x71,(False,True))]:
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 for y,filled in zip([4,20],levels):
  dr.rounded_rectangle((1,y,26,y+10),radius=2,fill='#83dabc' if filled else '#0a1d21',outline='#b6efca' if filled else '#2c4950',width=1)
 add(i,im,'cockpit&fuelX0&fuelX1&lowerY0&lowerY1')

# Flight HUD corner. Source mirroring preserves all four native positions.
im=Image.new('RGBA',(128,128));dr=ImageDraw.Draw(im)
dr.line((5,20,104,20,104,123),fill='#143e34',width=21)
dr.line((5,20,104,20,104,123),fill='#b0f7cd',width=10)
add(0x101,im.resize((32,32),Image.Resampling.LANCZOS),'cockpit',True)
# Remaining HUD and attitude symbols retain their exact masks with smooth edges.
for i in range(0x102,0x10a):
 a=decode(i)
 mask=Image.fromarray((((a>0) if i==0x103 else (a==1))*255).astype('uint8')).resize((32,32),Image.Resampling.LANCZOS)
 edge=mask.filter(ImageFilter.MaxFilter(3))
 im=Image.new('RGBA',(32,32),'#0c3029');im.putalpha(edge)
 fg=Image.new('RGBA',(32,32),'#b9f4d2' if i<0x104 else '#ecf3da');fg.putalpha(mask)
 im.alpha_composite(fg)
 if i in [0x102,0x103,0x104,0x105]:
  im=Image.new('RGBA',(128,128));dr=ImageDraw.Draw(im)
  if i==0x102:
   dr.ellipse((14,14,114,114),outline='#153e33',width=13)
   dr.ellipse((17,17,111,111),outline='#baf8d4',width=6)
  elif i==0x103:
   for a,b in [((40,64),(52,64)),((76,64),(88,64)),((64,40),(64,52)),((64,76),(64,88))]:
    dr.line((*a,*b),fill='#163e34',width=11);dr.line((*a,*b),fill='#d3f9db',width=5)
   dr.ellipse((59,59,69,69),fill='#e9ffe1')
  elif i==0x104:
   dr.line((4,68,28,44,127,44),fill='#10282c',width=20)
   dr.line((4,68,28,44,127,44),fill='#eaf3d9',width=10)
  else:
   dr.line((0,44,127,44),fill='#10282c',width=20)
   dr.line((0,44,127,44),fill='#eaf3d9',width=10)
   dr.polygon([(40,44),(88,44),(64,82)],fill='#eaf3d9')
  im=im.resize((32,32),Image.Resampling.LANCZOS)
 add(i,im,'cockpit',True)
# Preserve tiny contact location and color emphasis without a blocky NES square.
im=Image.new('RGBA',(128,128));dr=ImageDraw.Draw(im)
dr.ellipse((33,29,78,94),fill='#f2a35d80')
dr.ellipse((41,38,70,85),fill='#ffd39d');dr.ellipse((49,46,62,77),fill='#fff0cc')
add(0x10f,im.resize((32,32),Image.Resampling.LANCZOS),'cockpit',True)

# Landing pitch indicator: trace the five complete native aircraft outlines,
# simplify their pixel stair steps, and slice the vector glyphs back into native sprites.
landing_data=(R/'source/landing_chr.bin').read_bytes()
def simplify(points,eps=1.0):
 if len(points)<3:return points
 a=np.array(points[0],float);b=np.array(points[-1],float);v=b-a
 pts=np.array(points,float)
 if np.dot(v,v)==0:dist=np.linalg.norm(pts-a,axis=1)
 else:
  t=np.clip((pts-a)@v/np.dot(v,v),0,1)
  dist=np.linalg.norm(pts-(a+t[:,None]*v),axis=1)
 j=int(np.argmax(dist))
 if dist[j]<=eps:return [points[0],points[-1]]
 return simplify(points[:j+1],eps)[:-1]+simplify(points[j:],eps)
for pose in json.loads((R/'source/landing_pose_mappings.json').read_text()):
 W,H=pose['width'],pose['height'];mask=np.zeros((H,W),bool)
 for yy,t,attr,xx in pose['sprites']:
  a=decode(256+t,landing_data)==1
  if attr&64:a=a[:,::-1]
  if attr&128:a=a[::-1]
  x,y=xx-pose['x'],yy+1-pose['y'];mask[y:y+8,x:x+8]|=a
 edges={}
 def edge(a,b):edges.setdefault(a,[]).append(b)
 for y,x in zip(*np.where(mask)):
  if y==0 or not mask[y-1,x]:edge((x,y),(x+1,y))
  if x==W-1 or not mask[y,x+1]:edge((x+1,y),(x+1,y+1))
  if y==H-1 or not mask[y+1,x]:edge((x+1,y+1),(x,y+1))
  if x==0 or not mask[y,x-1]:edge((x,y+1),(x,y))
 artwork=Image.new('RGBA',(W*16,H*16));dr=ImageDraw.Draw(artwork)
 while edges:
  start=next(iter(edges));p=start;poly=[p]
  for _ in range(10000):
   q=edges[p].pop()
   if not edges[p]:del edges[p]
   poly.append(q);p=q
   if p==start:break
  poly=simplify(poly)
  if len(poly)>3:
   pts=[(int(x*16),int(y*16)) for x,y in poly]
   dr.polygon(pts,fill='#80bca2');dr.line(pts,fill='#d1f5da',width=6,joint='curve')
 artwork=artwork.resize((W*4,H*4),Image.Resampling.LANCZOS)
 for yy,t,attr,xx in pose['sprites']:
  x,y=xx-pose['x'],yy+1-pose['y'];im=artwork.crop((x*4,y*4,(x+8)*4,(y+8)*4))
  if attr&64:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if attr&128:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  add(256+t,im,flight,True,landing_data[(256+t)*16:(257+t)*16].hex().upper(),strict=True)
save_png(atlas,P/'flight_ui.png')

lines=(P/'hires.txt').read_text().splitlines()
# The old anchor sat on the edge of the cockpit. The center stays valid during ±1px shake.
for j,l in enumerate(lines):
 if l.startswith('<condition>cockpit,'):lines[j]=f'<condition>cockpit,tileAtPosition,120,132,{pat(0x51)},00000000,Y'
 # Include complete displaced native tiles instead of clipping their outer pixel.
 replacements={
  '<condition>numX0,positionCheckX,>=,8':'<condition>numX0,positionCheckX,>=,7',
  '<condition>numX1,positionCheckX,<,48':'<condition>numX1,positionCheckX,<,49',
  '<condition>fuelX0,positionCheckX,>=,8':'<condition>fuelX0,positionCheckX,>=,7',
  '<condition>fuelX1,positionCheckX,<,16':'<condition>fuelX1,positionCheckX,<,17',
  '<condition>attX0,positionCheckX,>=,24':'<condition>attX0,positionCheckX,>=,23',
  '<condition>attX1,positionCheckX,<,64':'<condition>attX1,positionCheckX,<,65',
 }
 lines[j]=replacements.get(lines[j],lines[j])
idx=lines.index('<img>panel_details.png')+1;lines.insert(idx,'<img>flight_ui.png')
idx=next(i for i,l in enumerate(lines) if l.startswith('<condition>'));lines[idx:idx]=conditions
idx=next(i for i,l in enumerate(lines) if '<tile>' in l);lines[idx:idx]=rules
# Shift the painted panel with the game's horizontal impact displacement.
# The NES world continues through scanlines 128-129, overlapping the HD
# coaming's top edge. A foreground cap covers only those two scanlines.
# Instrument tiles and sprites remain above the normal background layer.
def save_windshield_cap(image, name):
 cap=Image.new('RGBA',image.size)
 cap.paste(image.crop((0,128*4,1024,130*4)),(0,128*4))
 save_png(cap,P/name)
save_windshield_cap(base,'windshield_cap.png')
for name,dx in [('left',-4),('right',4)]:
 shifted=Image.new('RGBA',base.size);shifted.paste(base,(dx,0))
 # Extend edge pixels to avoid an exposed black sliver at the screen boundary.
 edge=base.crop((0,0,1,960) if dx>0 else (1023,0,1024,960)).resize((4,960))
 shifted.paste(edge,(0 if dx>0 else 1020,0));save_png(shifted,P/f'cockpit_{name}.png')
 save_windshield_cap(shifted,f'windshield_cap_{name}.png')
idx=lines.index('[cockpit]<background>cockpit.png,1,0,0,10')
lines[idx:idx+1]=[
 '[cockpit&impactLeft]<background>cockpit_left.png,1,0,0,10',
 '[cockpit&impactRight]<background>cockpit_right.png,1,0,0,10',
 '[cockpit&!impactLeft&!impactRight]<background>cockpit.png,1,0,0,10',
 '[cockpit&impactLeft]<background>windshield_cap_left.png,1,0,0,30',
 '[cockpit&impactRight]<background>windshield_cap_right.png,1,0,0,30',
 '[cockpit&!impactLeft&!impactRight]<background>windshield_cap.png,1,0,0,30',
]
lines=[l.replace('[cockpit', '[cockpit&cockpitBorder') for l in lines]
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
print('Flight UI:',slot,'native-driven symbols; impact-shake registration enabled')
