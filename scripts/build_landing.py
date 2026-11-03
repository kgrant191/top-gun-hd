"""Read-only carrier approach, touchdown, rollout and cannon-tracer artwork."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from pack_io import save_png

R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
M=json.loads((S/'landing_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines()
assert '<img>landing_details.png' not in lines
index=sum(l.startswith('<img>') for l in lines)
conditions=[
 '<condition>landingMode,memoryCheckConstant,0018,==,07',
 '<condition>carrierApproach,memoryCheckConstant,009F,==,01',
 '<condition>carrierSide,memoryCheckConstant,009F,==,03',
 '<condition>rolloutStart,memoryCheckConstant,009F,>=,05',
 '<condition>rolloutEnd,memoryCheckConstant,009F,<,08',
 f'<condition>sideVisible,tileAtPosition,32,168,{M["side_anchor"]},00000000,Y',
 '<condition>landingTransition2,memoryCheckConstant,009F,==,02',
 '<condition>landingTransition4,memoryCheckConstant,009F,==,04',
 '<condition>landingTransition8,memoryCheckConstant,009F,==,08',
]
backgrounds=[];rules=[];additions=[];atlas=Image.new('RGBA',(1024,1024));slot=0
scene='cockpit&cockpitBorder'
approach=scene+'&landingMode&carrierApproach'
side='landingMode&carrierSide&sideVisible'
rollout=scene+'&landingMode&rolloutStart&rolloutEnd'
font=str(S/'fonts/DejaVuSansMono-Bold.ttf')

def trimmed(name):
 im=Image.open(S/name).convert('RGBA')
 box=im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox()
 return im.crop(box)

def add(im,pattern,palette,cond):
 global slot
 x,y=slot%32*32,slot//32*32;slot+=1
 atlas.alpha_composite(im,(x,y))
 rules.append(f'[{cond}]<tile>{index},{pattern},{palette},{x},{y},1,N')

def decode(pattern):
 a=np.frombuffer(bytes.fromhex(pattern),np.uint8)
 return np.unpackbits(a[:8,None],axis=1)+2*np.unpackbits(a[8:,None],axis=1)

# Whole-ship layers follow the original nametable coordinates and PPU scroll.
# Native geometry signatures select distance; no movie-frame timing is used.
ship=trimmed('landing_approach_master.png')
patterns=set()
for e in M['approach']:
 stage=e['stage'];names=[]
 for k,(addr,value) in enumerate(e['signature']):
  name=f'carrierSize{stage}_{k}';names.append(name)
  conditions.append(f'<condition>{name},ppuMemoryCheckConstant,{addr:04X},==,{value:02X}')
 x0,y0,x1,y1=e['bbox'];art=ship.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS)
 plate=Image.new('RGBA',(2048,1536))
 for dx in [0,1024]:plate.alpha_composite(art,(x0*4+dx,y0*4))
 filename=f'landing_approach_{stage:02d}.png';save_png(plate,P/filename)
 backgrounds.append(f'[{approach}&'+ '&'.join(names)+f']<background>{filename},1,1,1,8')
 patterns.update(t['pattern'] for t in e['cells'])
for pattern in sorted(patterns):
 for pal in ['0F301131','0F001131']:
  rules.append(f'[{approach}&environmentWorld]<tile>0,{pattern},{pal},0,0,1,N')

# Side-on touchdown: an opaque carrier and distant sea, below the live jet.
sky=Image.open(S/'environment_sky_master.png').convert('RGBA').resize((1024,704),Image.Resampling.LANCZOS)
water=Image.open(S/'environment_water_master.png').convert('RGBA').resize((1088,300),Image.Resampling.LANCZOS)
carrier=trimmed('landing_broadside_master.png').resize((512,100),Image.Resampling.LANCZOS)
for phase,dx in enumerate([0,4,8,4]):
 name=f'landingWave{phase}';conditions.append(f'<condition>{name},memoryCheckConstant,001A,==,{phase*4:02X},0C')
 plate=Image.new('RGBA',(1024,960));plate.alpha_composite(sky,(0,0))
 sea=water.crop((32+dx,0,1056+dx,256));a=np.array(sea).astype(float)
 fade=np.exp(-np.arange(256)/18)[:,None,None]*.45
 a=a*(1-fade)+np.array([123,161,182,255])*fade
 plate.alpha_composite(Image.fromarray(np.uint8(a)),(0,704))
 # Match the native flight-deck surface where the aircraft's wheels touch.
 plate.alpha_composite(carrier,(128,606))
 # Distant escorts keep the native scene's scale and direction.
 for x in [676,844]:
  escort=carrier.resize((48,10),Image.Resampling.LANCZOS)
  plate.alpha_composite(escort,(x,697))
 filename=f'landing_side_{phase}.png';save_png(plate,P/filename)
 backgrounds.append(f'[{side}&{name}]<background>{filename},1,0,0,20')
jet=trimmed('landing_jet_master.png')
im=Image.new('RGBA',(64,32));small=ImageOps.contain(jet,(48,20),Image.Resampling.LANCZOS)
im.alpha_composite(small,((64-small.width)//2,24-small.height))
pattern=M['side_chr'][str(0xe7)]
rules.append(f'[{side}]<tile>0,{pattern},FF10000F,0,0,1,N')
for j in range(2):
 key=hashlib.sha256(f'TopGunLandingJetPiece{j}'.encode()).hexdigest()[:32].upper()
 additions.append(f'<addition>{pattern},FF10000F,{j*8-4},-1,{key},FF10000F,N')
 add(im.crop((j*32,0,j*32+32,32)),key,'FF10000F',side)
 rules.append(f'<tile>0,{key},FF10000F,0,0,1,N')
shadow=Image.new('RGBA',(32,32));d=ImageDraw.Draw(shadow)
d.ellipse((5,12,27,18),fill='#19374760')
add(shadow,M['side_chr'][str(0xe6)],'FF10000F',side)

# Honor native blank transitions; no cached cockpit layers over the side view.
black=Image.new('RGBA',(1024,960),(0,0,0,255));save_png(black,P/'landing_black.png')
backgrounds.append('[landingMode&carrierSide&!sideVisible]<background>landing_black.png,1,0,0,39')
for n in [2,4,8]:backgrounds.append(f'[landingMode&landingTransition{n}]<background>landing_black.png,1,0,0,39')
rewritten=[]
for l in lines:
 if '<background>' in l and l.startswith('[') and 'cockpit' in l.split(']')[0]:
  c,tail=l[1:].split(']',1)
  rewritten += [f'[{c}&!landingMode]'+tail,f'[{c}&landingMode&!carrierSide&!landingTransition2&!landingTransition4&!landingTransition8]'+tail]
 else:rewritten.append(l)
lines=rewritten

# Native background-priority mask sprites become an unwanted gray block after
# transparent scenery replacements. Hide them only during deck rollout.
rules.append(f'[{rollout}&enemyWorld]<tile>0,{M["rollout_chr"]["32"]},FF2A100F,0,0,1,N')
for pattern in M['rollout_marks']:
 a=decode(pattern)
 # Repaint the game's moving deck lights/dashes, preserving their positions.
 mask=Image.fromarray(np.uint8(a==1)*255).resize((32,32),Image.Resampling.LANCZOS)
 im=Image.new('RGBA',(32,32),'#f2eacb');im.putalpha(mask)
 add(im,pattern,'FF2A100F',rollout+'&enemyWorld')

# The rollout swaps in several shoreline/edge tiles absent from earlier
# scenery captures. Locate the first actual sea/deck pixels, including mixed
# rows, so no native blue band survives between the painted material planes.
for k,pattern in enumerate(M['rollout_backgrounds']):
 for pal in ['0F301131','0F001131']:
  rules.append(f'[{rollout}&environmentWorld]<tile>0,{pattern},{pal},0,0,1,N')
# Mesen selects the first matching background at a priority. Sort by the
# actual first painted row, across patterns, rather than by pattern key.
for value,material,priority in [(2,'ocean',7),(1,'runway',8)]:
 candidates=[]
 for k,pattern in enumerate(M['rollout_backgrounds']):
  rows=np.where(np.any(decode(pattern)==value,axis=1))[0]
  if len(rows):
   for y in range(128):candidates.append((y+int(rows[0]),y,k,pattern))
 for first,y,k,pattern in sorted(candidates):
   name=f'landing{material}{k}_{y}'
   conditions.append(f'<condition>{name},tileAtPosition,8,{y},{pattern},00000000,Y')
   backgrounds.append(f'[{rollout}&{name}]<background>environment_{material}_plane.png,1,0,0,{priority},0,{128-first}')

# Gunfire has no fins or missile body. Preserve native centers, growth and
# palettes; actual missiles use different keys and retain v0.6.0 artwork.
palettes=['FF10000F','FF152630','FF153630','FF162630','FF2A100F']
for t,pattern in M['combat_chr'].items():
 t=int(t);im=Image.new('RGBA',(128,128));d=ImageDraw.Draw(im)
 radius={0x0d:38,0x0e:29,0x0f:20,0x13:12}[t]
 cx,cy=(72,40) if t==0x13 else (64,64)
 d.ellipse((cx-radius*.6,cy-radius,cx+radius*.6,cy+radius),fill='#e65e2d65')
 d.ellipse((cx-radius*.38,cy-radius*.72,cx+radius*.38,cy+radius*.72),fill='#f5ab50')
 d.ellipse((cx-radius*.19,cy-radius*.45,cx+radius*.19,cy+radius*.45),fill='#fff8d8')
 im=im.resize((32,32),Image.Resampling.LANCZOS)
 # The farthest round shares a CHR key with one multi-tile effect. Its
 # existing nearby-layout rule retains priority for that different object.
 cond=scene+'&enemyWorld'+('&!combat19_0_1' if t==0x13 else '')
 for pal in palettes:add(im,pattern,pal,cond)

# The post-landing debrief retains the game's live score and remaining lives.
conditions += ['<condition>landingDebrief,memoryCheckConstant,0018,==,0A',
 f'<condition>debriefVisible,tileAtPosition,40,72,{M["debrief_chr"][0x1c]},0F300F0F,N']
debrief='landingDebrief&debriefVisible'
panel=Image.open(P/'menu_console.png').convert('RGBA');d=ImageDraw.Draw(panel)
d.rectangle((360,38,670,77),fill='#101b20')
d.text((512,56),'MISSION DEBRIEF',font=ImageFont.truetype(font,19),anchor='mm',fill='#b9cfcd')
d.rounded_rectangle((220,440,804,600),radius=12,fill='#07191d',outline='#47676a',width=2)
d.rounded_rectangle((220,624,804,686),radius=10,fill='#12272b',outline='#47676a',width=2)
d.line((160,353,864,353),fill='#a98a55',width=3)
badge=ImageOps.contain(ship,(180,160),Image.Resampling.LANCZOS)
panel.alpha_composite(badge,((1024-badge.width)//2,118))
save_png(panel,P/'landing_debrief.png')
backgrounds.append(f'[{debrief}]<background>landing_debrief.png,1,0,0,10')
rules.append(f'[{debrief}]<tile>0,{M["debrief_chr"][0]},0F300F0F,0,0,1,N')
chars={0x10+i:chr(65+i) for i in range(26)}|{0x30+i:str(i) for i in range(10)}|{1:'O',2:'I',0x0e:'!',0x0c:':',0x3e:'-'}
for t,ch in chars.items():
 im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
 d.text((16,16),ch,font=ImageFont.truetype(font,24),anchor='mm',fill='#c0e5d7')
 add(im,M['debrief_chr'][t],'0F300F0F',debrief)

save_png(atlas,P/'landing_details.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1
lines[i:i]=['<img>landing_details.png']+conditions+additions
i=next(i for i,l in enumerate(lines) if '<tile>' in l)
lines[i:i]=backgrounds+rules
lines[0]='# Top Gun HD v0.7.0 - carrier landing and cannon tracers'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
print('Landing:',len(M['approach']),'carrier sizes;',slot,'detail tiles')
