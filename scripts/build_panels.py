from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np, math
R=Path(__file__).resolve().parents[1];P=R/'pack'
font_path=R/'source/fonts/DejaVuSansMono-Bold.ttf'
if not font_path.exists():font_path=Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf')
base=Image.open(P/'cockpit.png').convert('RGBA');d=ImageDraw.Draw(base)
def box(rect,fill,r=0,outline=None,width=1):
 coords=tuple(round(v*4) for v in rect)
 if r:d.rounded_rectangle(coords,radius=round(r*4),fill=fill,outline=outline,width=width)
 else:d.rectangle(coords,fill=fill,outline=outline,width=width)
def bezel(rect):
 x,y,x2,y2=rect;box(rect,'#111b24',1.2,'#81939b',2)
 box((x+.7,y+.7,x2-.7,y2-.7),'#273842',.8,'#050b10',2)
 box((x+1.6,y+1.6,x2-1.6,y2-1.6),'#030e10',.8,'#75908d',1)
 for xx in [x+.9,x2-.9]:
  for yy in [y+.9,y2-.9]:
   d.ellipse((xx*4-1,yy*4-1,xx*4+1,yy*4+1),fill='#c8c8b4')
def text(x,y,t,size,color='#b8dacc'):
 d.text((round(x*4),round(y*4)),t,font=ImageFont.truetype(str(font_path),size),fill=color,anchor='lt')
# Rebuild only the two instrument clusters to the exact native display bounds.
box((2,139,71,174),'#182832',1)
bezel((4,141,69,155.5));bezel((4,157,69,172.5))
text(51,144,'ALT',15);text(52,150,'FT',11,'#6b9191')
text(50,160,'SPEED',12);text(53,166.5,'M/H',10,'#6b9191')
box((180,139,254,173.5),'#182832',1)
bezel((181.5,140.5,252,172))
text(185,144,'MISSILE',14);text(185,151.5,'REMAIN',14);text(185,161.5,'TYPE',14)
# Fuel has its own track; the attitude window never overlaps it.
box((2,173.5,71,221),'#182832',1)
bezel((5.5,173.5,18,220));bezel((21,173.5,67,219.5))
text(10,173.8,'F',9);text(10,217.5,'E',9)
base.save(P/'cockpit.png')
# UI tile overrides precede the old atlas rules. Regions preserve shared CHR glyphs elsewhere.
conditions=[
 '<condition>leftHudX0,positionCheckX,>=,0','<condition>leftHudX1,positionCheckX,<,72',
 '<condition>leftHudY0,positionCheckY,>=,140','<condition>leftHudY1,positionCheckY,<,174',
 '<condition>numX0,positionCheckX,>=,8','<condition>numX1,positionCheckX,<,48',
 '<condition>rightHudX0,positionCheckX,>=,180','<condition>rightHudX1,positionCheckX,<,254',
 '<condition>countY0,positionCheckY,>=,144','<condition>countY1,positionCheckY,<,160',
 '<condition>typeY0,positionCheckY,>=,160','<condition>typeY1,positionCheckY,<,168',
 '<condition>fuelX0,positionCheckX,>=,8','<condition>fuelX1,positionCheckX,<,16',
 '<condition>lowerY0,positionCheckY,>=,176','<condition>lowerY1,positionCheckY,<,216',
 '<condition>attX0,positionCheckX,>=,24','<condition>attX1,positionCheckX,<,64',
]
chrdata=(R/'captures/baseline/03240.chr').read_bytes()
def pat(i):return chrdata[i*16:(i+1)*16].hex().upper()
def decode(i):
 b=chrdata[i*16:(i+1)*16]
 return np.array([[((b[y]>>(7-x))&1)+2*((b[y+8]>>(7-x))&1) for x in range(8)] for y in range(8)])
atlas=Image.new('RGBA',(512,512));rules=[];slot=0
left='cockpit&leftHudX0&leftHudX1&leftHudY0&leftHudY1'
right='cockpit&rightHudX0&rightHudX1&leftHudY0&leftHudY1'
num=left+'&numX0&numX1'
typ=right+'&typeY0&typeY1'
fuel='cockpit&fuelX0&fuelX1&lowerY0&lowerY1'
att='cockpit&attX0&attX1&lowerY0&lowerY1'
def add(i,im,cond,sprite=False):
 global slot
 x=slot%16*32;y=slot//16*32;atlas.alpha_composite(im,(x,y));slot+=1
 rules.append(f'[{cond}]<tile>2,{pat(i)},{"FF2A100F" if sprite else "0F2A0A31"},{x},{y},1,Y')
def blank(i,cond):rules.append(f'[{cond}]<tile>0,{pat(i)},0F2A0A31,0,0,1,Y')
for i in [0x96,0x97,0x79,0x86,0x87,0x88,0x94,0x95,0x91]:blank(i,left)
for i in [0x66,0x67,0x68,0x76,0x77,0x78,0x89,0x8a]:blank(i,right)
# Remove old fuel labels from the edge of the attitude window.
for i in [0x93,0x7a]:blank(i,'cockpit&panel')
def digit(t):
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 f=ImageFont.truetype(str(font_path),26)
 dr.text((16,15),t,font=f,anchor='mm',fill='#a7f3b2')
 return im
for i in range(1,11):add(i,digit(str(i-1)),num)
for i in range(1,11):add(i,digit(str(i-1)),typ)
add(0x23,digit('T'),typ);add(0x3e,digit('-'),typ)
# Smooth the original large missile counter while keeping each changing quadrant.
for i in range(0x3f,0x4f):
 a=decode(i);mask=Image.fromarray(((a==1)*255).astype('uint8'),'L').resize((32,32),Image.Resampling.LANCZOS)
 im=Image.new('RGBA',(32,32),'#a7f3b2');im.putalpha(mask)
 add(i,im,right+'&countY0&countY1')
# Native selection arrows keep their visibility timing and stay inside the bezel.
im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
dr.polygon([(8,16),(21,8),(21,24)],fill='#80bca1')
add(0x90,im,right)
# Filled and empty fuel states are distinct. Keep each native segment on its original row.
for i,filled in [(0x80,True),(0x81,False)]:
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 for y in [4,20]:
  dr.rounded_rectangle((1,y,26,y+10),radius=2,fill='#79d8bd' if filled else '#08191e',outline='#b6efca' if filled else '#33525b',width=1)
 add(i,im,fuel)
# Attitude background retains the original horizon/pitch geometry, with aviation colors.
for i in [0x62,0x63,0x64,0x65,0x72,0x73,0x74,0x75,0x82,0x83,0x84,0x85]:
 a=decode(i);im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 for y in range(8):
  for x in range(8):
   v=int(a[y,x]);col=None
   if v==2:col='#163e55'
   elif v==1:col='#68462e'
   if col:dr.rectangle((x*4,y*4,x*4+3,y*4+3),fill=col)
 # Tick marks in the upper field and central pitch scale must remain clear.
 if i in [0x64,0x72,0x74,0x73]:
  target=1
  for y in range(8):
   for x in range(8):
    if a[y,x]==target and (i!=0x73 or y==5):dr.rectangle((x*4,y*4,x*4+3,y*4+3),fill='#cedbd4')
 if i==0x84:
  for y in range(8):
   for x in range(8):
    if a[y,x]==2:dr.rectangle((x*4,y*4,x*4+3,y*4+3),fill='#d5d5bc')
 add(i,im,att)
# Bank/pitch marker sprites move under game control, with white symbols and dark outlines.
for i in range(0x104,0x10a):
 a=decode(i);im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 for y in range(8):
  for x in range(8):
   v=int(a[y,x])
   if v:dr.rectangle((x*4,y*4,x*4+3,y*4+3),fill={1:'#eaf7df',2:'#09202b',3:'#09202b'}[v])
 add(i,im,'cockpit',True)
atlas.save(P/'panel_details.png')
# Insert all definitions before consumers and put all overrides before generic matching rules.
lines=(P/'hires.txt').read_text().splitlines();idx=lines.index('<img>instruments.png')+1;lines.insert(idx,'<img>panel_details.png')
idx=next(i for i,l in enumerate(lines) if l.startswith('<condition>'));lines[idx:idx]=conditions
idx=next(i for i,l in enumerate(lines) if '<tile>' in l);lines[idx:idx]=rules
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
print('Panels:',slot,'precise UI tiles')
