from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np, json, math
from build_dials import draw_dials
from pack_io import save_png
R=Path(__file__).resolve().parents[1]; P=R/'pack';P.mkdir(exist_ok=True)
S=4
# Original imagegen artwork; build script only sizes, masks and assembles pack assets.
assets={name: f'source/{name}_master.png' for name in ('title','carrier','cockpit')}
for k,v in assets.items():
 if k=='carrier':continue # clean animated launch plate is built once, below
 src=R/v
 im=Image.open(src).convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
 if k=='cockpit':
  # Align the painted monitor/frame edges with fixed native instrument rows.
  out=Image.new('RGBA',(1024,960))
  # Start below the sky-colored margin baked into the cockpit master. The
  # first coaming segment still ends at the original instrument boundary.
  srcys=[131,142,177,214,240];dstys=[128,144,176,208,240]
  for a,b,c,d in zip(srcys,srcys[1:],dstys,dstys[1:]):out.paste(im.crop((0,a*4,1024,b*4)).resize((1024,(d-c)*4),Image.Resampling.LANCZOS),(0,c*4))
  im=out
  # Decorative dial scales are vector UI; flight values and attitude remain native.
  draw_dials(im)
 save_png(im,P/f'{k}.png')
fontpath=str(R/'source/fonts/DejaVuSansMono-Bold.ttf')
font=ImageFont.truetype(fontpath,25)
title_ui=Image.new('RGBA',(1024,960));d=ImageDraw.Draw(title_ui)
d.text((512,866),'PRESS START',font=ImageFont.truetype(fontpath,25),anchor='mm',fill=(218,232,241,255),stroke_width=1,stroke_fill=(9,23,41,255))
save_png(title_ui,P/'title_prompt.png')
# Dynamic instrument glyphs remain tied to original CHR data.
trans=Image.new('RGBA',(32,32));save_png(trans,P/'transparent.png')
lines=['# Top Gun HD v0.3.2 - cockpit colors and map water fills','<ver>109','<scale>4','<overscan>0,0,0,0','<img>transparent.png','<img>instruments.png']
def capture(n,s):return (R/f'captures/baseline/{n:05d}.{s}').read_bytes()
def pat(n,i):return capture(n,'chr')[i*16:(i+1)*16].hex().upper()
def tile_cond(name,n,x,y,i):lines.append(f'<condition>{name},tileAtPosition,{x},{y},{pat(n,i)},00000000,Y')
tile_cond('title',180,88,56,0x53)
tile_cond('carrier',900,112,80,0x6d)
# Unique stable cockpit coaming from the second nametable, as displayed at y=128.
tile_cond('cockpit',3240,80,132,0x51)
lines+=['<condition>prompt,frameRange,64,20','<condition>panel,positionCheckY,>=,128',
 '[title]<background>title.png,1,0,0,30',
 '[title&prompt]<background>title_prompt.png,1,0,0,31',
 '[carrier]<background>carrier.png,1,0,0,30',
 '[cockpit]<background>cockpit.png,1,0,0,10']
# Transparency removes only original static cockpit housing. Live data is kept.
remove={0,0xf,*range(0x50,0x62),0x69,0x6a,0x6b,0x70,0x7b,0x8b,0x92}
# Analog dials: keep markings and use muted neutral tones instead of orange.
analog=set(range(0x5c,0x60))|set(range(0x6c,0x70))|set(range(0x7c,0x80))|set(range(0x8c,0x90))
remove|=analog
# Actual glyph shapes; all text uses exact original tile matching, excluding artwork reuse.
chars={i+1:str(i) for i in range(10)}|{0x10+i:chr(65+i) for i in range(26)}|{0x0b:"'",0x0c:'.',0x0d:'?',0x0e:'!'}
chrdata=capture(3240,'chr')
def decode(b):return np.array([[((b[y]>>(7-x))&1)+2*((b[y+8]>>(7-x))&1) for x in range(8)] for y in range(8)])
def glyph(char):
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 dr.text((16,14),char,font=font,anchor='mm',fill=(147,242,151,255))
 return im
atlas=Image.new('RGBA',(512,512));records=[];slot=0
# Render all live cockpit data, including grid, gauges, tiny labels, underlays and marks.
live=set(range(1,0x50))|set(range(0x62,0x99))|{0xb1,0xb2,0xb3,0xb4,0xb5}
live|=analog
live-=remove
for i in sorted(live):
 if False:im=glyph(chars[i])
 else:
  a=decode(chrdata[i*16:i*16+16]);im=Image.new('RGBA',(8,8));px=im.load()
  for y in range(8):
   for x in range(8):
    v=a[y,x]
    # Avoid painting source background fields over the cockpit master.
    if i in analog: col=[(0,0,0,0),(150,181,193,255),(0,0,0,0),(203,225,228,255)][v]
    else:col=[(0,0,0,0),(117,233,126,255),(6,29,23,160),(167,248,166,255)][v]
    px[x,y]=col
  im=im.resize((32,32),Image.Resampling.NEAREST)
 x=slot%16*32;y=slot//16*32;atlas.alpha_composite(im,(x,y));records.append((i,x,y));slot+=1
sprite_records=[]
for i in range(0x101,0x10a):
 a=decode(chrdata[i*16:i*16+16]);im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 for yy in range(8):
  for xx in range(8):
   v=a[yy,xx]
   if v:dr.rectangle((xx*4,yy*4,xx*4+3,yy*4+3),fill={1:(138,255,183,255),2:(18,46,41,255),3:(5,24,22,255)}[int(v)])
 x=slot%16*32;y=slot//16*32;atlas.alpha_composite(im,(x,y));sprite_records.append((i,x,y));slot+=1
save_png(atlas,P/'instruments.png')
# Ignore palette only through default fallback, scoped to cockpit and lower screen.
# Palette matched rules first, default mappings for legitimate flashing palettes follow.
for i in sorted(remove):lines.append(f'[cockpit&panel]<tile>0,{pat(3240,i)},0F2A0A31,0,0,1,Y')
for i,x,y in records:lines.append(f'[cockpit&panel]<tile>1,{pat(3240,i)},0F2A0A31,{x},{y},1,Y')
for i,x,y in sprite_records:lines.append(f'[cockpit]<tile>1,{pat(3240,i)},FF2A100F,{x},{y},1,Y')
# Briefing/menu font shares the CHR alphabet; explicitly scoped by its palette.
for i,x,y in records:
 if i in chars:lines.append(f'<tile>1,{pat(3240,i)},0F2A0F0F,{x},{y},1,N')
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
meta={'version': '0.2.0', 'emulator': 'MesenCE 2.2.1 (user supplied)', 'scale': 4, 'features': ['Approved title and native-timed animated launch', 'Impact-safe HD cockpit with native shake registration', 'Fine targeting reticle and radar display', 'Native-driven smooth missile digits and fuel segments', 'Updated landing instructions and pitch-aircraft indicator'], 'not_yet_redrawn': ['Enemy aircraft and projectiles', 'Clouds, ocean and terrain', 'Briefing map and weapon diagrams', 'Later missions, landing and refuelling'], 'assets': {'title': 'source/title_master.png', 'carrier': 'source/carrier_master.png', 'cockpit': 'source/cockpit_master.png'}, 'approved_intro_version': '0.1.1'}
(R/'source/build_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
import subprocess
subprocess.run(['python3',str(R/'scripts/build_launch.py')],check=True)
m=json.loads((R/'source/launch_mappings.json').read_text())
t=(P/'hires.txt').read_text();idx=t.index('<condition>');t=t[:idx]+'\n'.join(m['conditions'])+'\n'+t[idx:]
t=t.replace('[carrier]<background>carrier.png,1,0,0,30','[carrier]<background>carrier.png,1,0,0,30\n'+'\n'.join(m['backgrounds']))
(P/'hires.txt').write_text(t)
subprocess.run(['python3',str(R/'scripts/build_panels.py')],check=True)
subprocess.run(['python3',str(R/'scripts/build_flight_ui.py')],check=True)
subprocess.run(['python3',str(R/'scripts/build_menus.py')],check=True)
meta=json.loads((R/'source/build_manifest.json').read_text())
meta['version']='0.3.2'
meta['features'].append('Neutral windshield coaming and consistent attitude-display tick colors')
meta['features'].append('Correct inland-water fills within the original mission-one coastline')
(R/'source/build_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
# Install pack/ manually or through the emulator after reviewing the build.
print('Built',len(lines),'lines;',slot,'instrument tiles')
