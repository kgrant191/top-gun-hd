"""Recorded Mission 4 helicopters, rear display and shuttle approach."""
from pathlib import Path
from collections import defaultdict
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pack_io import save_png

R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
M=json.loads((S/'mission4_final_target_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines()
assert '<img>mission4_final_target.png' not in lines
index=sum(l.startswith('<img>') for l in lines)
scene='cockpit&cockpitBorder&missionFour&mission2Flight'
flight=scene+'&rearCombatPhase';world=flight+'&environmentWorld'
rules=[];conditions=[];backgrounds=[];fallback=[]
atlas=Image.new('RGBA',(1024,512));slot=0

def trim(im):
 return im.crop(im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())
def dec(p):
 b=np.frombuffer(bytes.fromhex(p),np.uint8)
 return np.unpackbits(b[:8,None],axis=1)+2*np.unpackbits(b[8:,None],axis=1)
def add(im,pattern,palette,gate):
 global slot
 x,y=slot%32*32,slot//32*32;slot+=1;assert slot<=512
 atlas.alpha_composite(im,(x,y))
 line=f'[{gate}]<tile>{index},{pattern},{palette},{x},{y},1,N'
 rules.append(line);return line

# Native white rotor marks determine blade angle and animation phase.
# Connect their endpoints with a metallic blade and attach the fuselage
# mast to its hub; retain the native footprint and sprite lifetime.
sheet=Image.open(S/'mission4_helicopter_master.png').convert('RGBA')
front=trim(sheet.crop((0,0,575,sheet.height)))
for li,e in enumerate(M['helicopters']):
 w,h=e['size'];native=np.zeros((h,w),np.uint8)
 for t in e['tiles']:
  a=dec(t['pattern'])
  if t['attr']&64:a=np.fliplr(a)
  if t['attr']&128:a=np.flipud(a)
  native[t['y']:t['y']+8,t['x']:t['x']+8]=np.maximum(native[t['y']:t['y']+8,t['x']:t['x']+8],a)
 yy,xx=np.where(native==2)
 if not len(xx):yy,xx=np.where(native>0)
 bx,by,bw,bh=int(xx.min()),int(yy.min()),int(xx.max()-xx.min()+1),int(yy.max()-yy.min()+1)
 art=front
 codes={t['tile'] for t in e['tiles']}
 if codes&set(range(0x95,0xab)):
  angle=17 if e['tiles'][0]['attr']&64 else -17
  art=trim(art.rotate(angle,Image.Resampling.BICUBIC,expand=True))
 ry,rx=np.where((native==1)&(np.indices(native.shape)[0]<=by+2))
 if len(rx)>=2 and rx.max()>rx.min():
  slope,intercept=np.polyfit(rx,ry,1)
  cx=(float(rx.min())+float(rx.max()))/2;cy=float(slope*cx+intercept)
 else:
  cx=bx+bw/2;cy=max(0,by-1);slope=0;intercept=cy
  rx=np.array([max(0,bx-1),min(w-1,bx+bw)])
 bodytop=min(by,int(round(cy+1)))
 im=Image.new('RGBA',(w*4,h*4))
 body=art.resize((bw*4,(by+bh-bodytop)*4),Image.Resampling.LANCZOS)
 alpha=np.array(body)[:,:,3];ay,ax=np.where(alpha>128)
 if len(ax):
  mastx=bx*4+float(ax[ay<=ay.min()+2].mean());masty=bodytop*4+int(ay.min())+2
  mast=ImageDraw.Draw(im);mast.line((int(cx*4+2),int(cy*4+2),int(mastx),masty),fill='#718387',width=3)
 im.alpha_composite(body,(bx*4,bodytop*4))
 d=ImageDraw.Draw(im)
 points=[(int(x*4+2),int((slope*x+intercept)*4+2)) for x in [rx.min(),rx.max()]]
 d.line(points,fill='#33434a',width=4);d.line(points,fill='#a9bdc3',width=2)
 # Alternate the crossing blade using the captured CHR animation phase.
 spread=max(2,min(6,bw//3));tilt=1 if li%2 else -1
 d.line((int((cx-spread)*4),int((cy-tilt)*4),int((cx+spread)*4),int((cy+tilt)*4)),fill='#6e8992',width=2)
 d.ellipse((int(cx*4)-2,int(cy*4)-2,int(cx*4)+3,int(cy*4)+3),fill='#c4d0cd')
 for ti,t in enumerate(e['tiles']):
  piece=im.crop((t['x']*4,t['y']*4,t['x']*4+32,t['y']*4+32))
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  gates=[]
  for ai,anchor in enumerate([e['tiles'][0],e['tiles'][-1]]):
   name=f'm4Heli{li}_{ti}_{ai}';gates.append(name)
   dx=(anchor['x']-t['x'])*(-1 if t['attr']&64 else 1)
   dy=(anchor['y']-t['y'])*(-1 if t['attr']&128 else 1)
   conditions.append(f'<condition>{name},spriteNearby,{dx},{dy},{anchor["pattern"]},{e["palette"]},N')
  gate=flight+'&enemyWorld'+('&hmirror' if t['attr']&64 else '&!hmirror')+('&vmirror' if t['attr']&128 else '&!vmirror')
  line=add(piece,t['pattern'],e['palette'],gate+'&'+'&'.join(gates))
  fallback.append(line.replace('&'+'&'.join(gates),''))
rules+=list(dict.fromkeys(fallback))

# The shuttle's one- and two-pixel cannon rounds retain their exact native
# positions and size, using the existing painted hot-projectile artwork.
burst=trim(Image.open(S/'impact_burst_master.png').convert('RGBA'))
for bullet in M['boss_bullets']:
 x0,y0,x1,y1=bullet['bbox'];im=Image.new('RGBA',(32,32))
 im.alpha_composite(burst.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 add(im,bullet['pattern'],'FF162630',flight+'&m4RockyPhase&enemyWorld')

# Boss cannon rounds can occlude a top-row anchor in the lethal impact.
# The opposite outer corner still identifies the 32-pixel burst. Keep its
# approved atlas pieces when that one corner is present during the hit.
for line in lines:
 if '<tile>9,' not in line or '&impactBurst0_' not in line:continue
 head,tail=line[1:].split(']',1);tokens=head.split('&')
 checks=[n for n in tokens if n.startswith('impactBurst0_')]
 j=int(checks[0].split('_')[1]);corner=0 if j==3 else 3
 check=f'impactBurst0_{j}_{corner}'
 assert check in checks
 tokens=[n for n in tokens if not n.startswith('impactBurst0_')]
 tokens+=['missionFour','hullImpact','m4ShuttlePresent',check]
 rules.append('['+'&'.join(tokens)+']'+tail)

# Newly recorded curve cells otherwise expose native green pixels on the
# amber display. Mask only background cells inside the active rear display.
conditions.extend(['<condition>m4RearGraphY0,originPositionCheckY,>=,159',
 '<condition>m4RearGraphY1,originPositionCheckY,<,209'])
rear=scene+'&rearThreatL&rearThreatR&flightX0&flightX1&m4RearGraphY0&m4RearGraphY1'
for pattern in M['danger_background_keys']:
 for pal in ['0F2A0A0F','0F2A0A16']:
  rules.append(f'[{rear}]<tile>0,{pattern},{pal},0,0,1,N')
for line in lines:
 if not line.startswith('[') or '<tile>' not in line or ',0F2A0A31,' not in line:continue
 head=line[1:line.index(']')]
 if 'mission' in head.lower():continue
 if ('rearThreatL&rearThreatR' in head and 'rearTextY' in head) or 'rearRemainder' in head:
  rules.insert(0,line.replace(']<tile>','&missionFour]<tile>').replace(',0F2A0A31,',',0F2A0A0F,'))

# The target's native nametable changes through seven recorded sizes.
# Follow its exact geometry and scrolling; no RAM writes or guessed timers.
conditions.append('<condition>m4ShuttlePresent,ppuMemoryCheckConstant,22EF,>=,C0')
shuttle=trim(Image.open(S/'mission4_shuttle_master.png').convert('RGBA'))
for entry in M['boss_stages']:
 stage=entry['stage'];ox,oy=entry['origin'];w,h=entry['size']
 box=(3,1,6,7) if stage==0 else (0,5,w,h) if stage==4 else (0,0,w,h)
 x0,y0,x1,y1=box;art=shuttle.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS)
 plate=Image.new('RGBA',(2048,1536))
 for dx in [0,1024]:plate.alpha_composite(art,((ox+x0)*4+dx,(oy+y0)*4))
 filename=f'mission4_shuttle_{stage:02d}.png';save_png(plate,P/filename)
 gate=f'm4ShuttleSize{stage}';tile=entry['tiles'][0]
 conditions.append(f'<condition>{gate},ppuMemoryCheckConstant,{tile["address"]:04X},==,{tile["tile"]:02X}')
 backgrounds.append(f'[{flight}&{gate}]<background>{filename},1,1,1,9')
for pattern in M['boss_background_keys']:
 for pal in ['0F00100F','0F301016']:
  rules.append(f'[{world}&m4ShuttlePresent]<tile>0,{pattern},{pal},0,0,1,N')

# Preserve all six native full/half/empty health cells, labeled for this boss.
font=ImageFont.truetype(str(S/'fonts/DejaVuSansMono-Bold.ttf'),13)
title=Image.new('RGBA',(192,32),'#061b20df');ImageDraw.Draw(title).text((96,0),'SHUTTLE',font=font,anchor='mt',fill='#e3d8b3')
health=dict(json.loads((S/'mission3_completion_mappings.json').read_text())['health'])
health['F0F1F0F1F0F1F1FF0000000000000000']={'tile':17}
for cell in range(6):
 for pattern,e in health.items():
  im=title.crop((cell*32,0,cell*32+32,32));d=ImageDraw.Draw(im)
  d.rounded_rectangle((2,16,29,29),radius=2,fill='#132d32',outline='#77908a',width=1)
  amount={16:24,17:12,18:0}[e['tile']]
  if amount:d.rectangle((4,18,3+amount,27),fill='#efbb62');d.line((4,18,3+amount,18),fill='#ffe1a1')
  add(im,pattern,'FF2A100F',flight+f'&bossMeterY0&bossMeterY1&bossMeterX{cell}')

# Preserve every generic alternative when a new exact palette key is added.
oldkeys=set();defaults=defaultdict(list)
for line in lines:
 if '<tile>' not in line:continue
 v=line.split('<tile>')[1].split(',');oldkeys.add(tuple(v[1:3]))
 if v[6]=='Y':defaults[v[1]].append(line)
newkeys={tuple(line.split('<tile>')[1].split(',')[1:3]) for line in rules}
for pattern,pal in sorted(newkeys-oldkeys):
 for line in defaults[pattern]:
  v=line.split('<tile>')[1].split(',');v[2]=pal;v[6]='N'
  rules.append(line.split('<tile>')[0]+'<tile>'+','.join(v))
rules=list(dict.fromkeys(rules));save_png(atlas,P/'mission4_final_target.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1
lines[i:i]=['<img>mission4_final_target.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l)
lines[i:i]=backgrounds+rules
lines[0]='# Top Gun HD v0.14.0 - Mission 4 helicopters, rear display and shuttle'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
report=dict(atlas_cells=slot,rules=len(rules),conditions=len(conditions),backgrounds=len(backgrounds),helicopter_layouts=len(M['helicopters']),shuttle_sizes=len(M['boss_stages']))
(S/'mission4_final_target_build.json').write_text(json.dumps(report,indent=2)+'\n')
print('Mission 4 final target:',report)
