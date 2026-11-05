"""Mission 3 desert, ground targets and reuse of approved flight/refueling art.
All predicates read native state; no ROM, gameplay, timing or audio edits.
"""
from pathlib import Path
from collections import defaultdict
import json,re
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from pack_io import save_png
R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
M=json.loads((S/'mission3_mappings.json').read_text());lines=(P/'hires.txt').read_text().splitlines()
assert '<condition>missionThree,memoryCheckConstant,0030,==,03' not in lines
index=sum(l.startswith('<img>') for l in lines);atlas=Image.new('RGBA',(1024,1024));slot=0
conditions=['<condition>missionThree,memoryCheckConstant,0030,==,03',
 '<condition>mission3Desert,ppuMemoryCheckConstant,3F06,==,27',
 f'<condition>menuMissionThree,tileAtPosition,80,32,{M["mission_three_pattern"]},00000000,Y',
 f'<condition>menuMapThree,tileAtPosition,80,112,{M["map_anchor"]},00000000,Y']
rules=[];backgrounds=[]
scene='cockpit&cockpitBorder&missionThree';flight=scene+'&mission2Flight&rearCombatPhase';world=flight+'&environmentWorld'
def dec(p):
 b=np.frombuffer(bytes.fromhex(p),np.uint8);return np.unpackbits(b[:8,None],axis=1)+2*np.unpackbits(b[8:,None],axis=1)
def trim(name):
 im=Image.open(S/name).convert('RGBA');return im.crop(im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())
def add(im,pattern,pal,cond):
 global slot
 x,y=slot%32*32,slot//32*32;slot+=1;assert slot<=1024
 atlas.alpha_composite(im,(x,y));rule=f'[{cond}]<tile>{index},{pattern},{pal},{x},{y},1,N';rules.append(rule);return rule
# Mission 3 shares the corrected Mission 2 cockpit, aircraft, effects and
# refueling palette. Retain the original rule order in its scoped copies.
# Carrier body and component geometry is deliberately excluded.
for l in lines:
 if not l.startswith('['):continue
 if 'missionTwo' in l and '!missionTwo' not in l:
  if any(x in l for x in ['bossBodyPresent','bossPart','bossSize','bossDistance','bossMeter','mission2BossRoute']):continue
  if '<tile>15,' in l:continue
  if '<tile>16,' in l and 'targetOrdinal' not in l and 'enemyWorld' not in l:continue
  q=l.replace('missionTwo','missionThree')
  (backgrounds if '<background>' in q else rules).append(q)
# Native ground palette also applies to existing projectile/impact families.
for l in list(rules):
 if ',FF10000F,' in l:rules.append(l.replace(',FF10000F,',',FF101B0F,'))
# Non-Mission-2 tanker fallback must not outrank the Mission 3 departure/exit.
# Its original behavior is retained for other missions.
lines=[l.replace('&!missionTwo]<background>mission2_tanker.png','&!missionTwo&!missionThree]<background>mission2_tanker.png') for l in lines]
# Reuse launch, weapon selection, typography and panel layout for numeral 3.
for l in lines:
 if l.startswith('[') and 'menuMissionTwo' in l and 'menuMapTwo' not in l:
  q=l.replace('menuMissionTwo','menuMissionThree')
  (backgrounds if '<background>' in q else rules).append(q)
# Desert uses its own native-scrolled surface for all seven bank stages.
surface=trim('mission3_desert_master.png').resize((1280,1024),Image.Resampling.LANCZOS)
a=np.array(surface).astype(float);fog=np.array([177,179,166,255]);fade=np.exp(-np.arange(1024)/42)[:,None,None]*.7
surface=Image.fromarray(np.uint8(a*(1-fade)+fog*fade))
for bank,slope in [(0,0),(-1,1/32),(-2,1/16),(-3,1/8),(1,-1/32),(2,-1/16),(3,-1/8)]:
 tag='zero' if bank==0 else ('left' if bank<0 else 'right')+str(abs(bank));base=Image.new('RGBA',(1280,1856));base.paste(surface,(0,766));a=np.array(base);alpha=np.clip((np.arange(base.height)-766)/8,0,1);a[:,:,3]=np.uint8(a[:,:,3]*alpha[:,None]);base=Image.fromarray(a)
 turned=base.transform((1024,1536),Image.Transform.AFFINE,(1,0,128,-slope,1,slope*512),Image.Resampling.BICUBIC)
 name=f'mission3_desert_{tag}.png';save_png(turned,P/name)
 backgrounds.insert(0,f'[{scene}&mission3Desert&envBank_{tag}]<background>{name},1,0,1,7')
 skyname='environment_sky.png' if bank==0 else f'environment_sky_{tag}.png'
 edge=Image.open(P/skyname).crop((0,0,1024,12));edgename=f'mission3_sky_edge_{tag}.png';save_png(edge,P/edgename)
 backgrounds.insert(0,f'[{scene}&mission3Desert&envBank_{tag}]<background>{edgename},1,0,0,21')
# Exact desert horizon keys; repainting is confined to the flight window.
for p in M.get('terrain_keys',[]):rules.insert(0,f'[{world}&mission3Desert]<tile>0,{p},0F302721,0,0,1,N')
for p in M['takeoff_terrain_keys']:rules.insert(0,f'[{scene}&mission2Takeoff&environmentWorld&mission3Desert]<tile>0,{p},0F302721,0,0,1,N')
for l in list(rules):
 if ',0F301121,' in l and 'missionThree' in l:rules.append(l.replace(',0F301121,',',0F302721,'))
# Map retains its geography and moving native marker, using the console colors.
from map_geometry import contours,simplify,area
mapimage=Image.new('RGBA',(1024,960));d=ImageDraw.Draw(mapimage);d.rounded_rectangle((144,364,880,916),radius=12,fill='#04111b',outline='#608b91',width=2)
layer=Image.new('RGBA',(704,512),'#092332');d=ImageDraw.Draw(layer);polys=[simplify(p) for p in contours(np.array(M['map_pixels'])==0x17)]
for p in sorted(polys,key=lambda p:abs(area(p)),reverse=True):d.polygon([(int(x*4),int(y*4)) for x,y in p],fill='#706044' if area(p)>0 else '#092332')
for p in polys:d.line([(int(x*4),int(y*4)) for x,y in p],fill='#c9b78d',width=2,joint='curve')
for x in range(0,704,64):d.line((x,0,x,512),fill='#31505b70',width=1)
for y in range(0,512,64):d.line((0,y,704,y),fill='#31505b70',width=1)
mapimage.alpha_composite(layer,(160,384));save_png(mapimage,P/'mission3_map.png')
menu='menuMissionM&menuMissionN&menuMissionThree&menuHeaderPresent&menuMapThree';region=menu+'&menuMapX0&menuMapX1&menuMapY0&menuMapY1'
backgrounds.insert(0,f'[{menu}]<background>mission3_map.png,1,0,0,11')
for e in M['map_markers']:
 mask=Image.fromarray(np.uint8(e['mask'])*255).resize((32,32),Image.Resampling.LANCZOS);im=Image.new('RGBA',(32,32),'#edc78b');im.putalpha(mask)
 for pal in ['0F17212A','0F2A0F0F']:add(im,e['pattern'],pal,region)
for p in M['map_keys']:
 for pal in ['0F17212A','0F2A0F0F']:rules.append(f'[{region}]<tile>0,{p},{pal},0,0,1,N')
# Ground targets use complete captured metasprite signatures. Specific views
# precede one per-pattern fallback, so clipped targets retain HD coverage.
masters={n:trim(f'mission3_{n}_master.png') for n in ['radar','tank','barrier']};new=[];fallback={}
for li,e in enumerate(sorted(M['objects'],key=lambda e:-e['count'])):
 if e['kind']=='barrier':continue
 w,h=e['size'];x0,y0,x1,y1=e['bbox'];art=masters[e['kind']]
 # Oblique poses keep the native viewing side through OAM mirroring.
 if e['id'] in [47,62,79,90]:art=ImageOps.mirror(art)
 im=Image.new('RGBA',(w*4,h*4));im.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 for ti,t in enumerate(e['tiles']):
  piece=im.crop((t['x']*4,t['y']*4,t['x']*4+32,t['y']*4+32))
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  gates=[]
  for ai,anchor in enumerate([e['tiles'][0],e['tiles'][-1]]):
   tag=f'm3Object{li}_{ti}_{ai}';gates.append(tag)
   conditions.append(f'<condition>{tag},spriteNearby,{anchor["x"]-t["x"]},{anchor["y"]-t["y"]},{anchor["pattern"]},{e["palette"]},N')
  base=flight+'&enemyWorld'+('&hmirror' if t['attr']&64 else '&!hmirror')+('&vmirror' if t['attr']&128 else '&!vmirror')
  rule=add(piece,t['pattern'],e['palette'],base+'&'+'&'.join(gates));rules.pop();new.append(rule);fallback.setdefault((t['pattern'],e['palette'],t['attr']&192),rule.replace('&'+'&'.join(gates),''))
# Repeated barricade CHR cells are independent modules rather than samples of
# one large target. Give each module identical local geometry at each size.
seen=set()
for e in M['objects']:
 if e['kind']!='barrier':continue
 for t in e['tiles']:
  key=(t['pattern'],e['palette'])
  if key in seen:continue
  seen.add(key);a=dec(t['pattern']);ys,xs=np.where(a>0)
  if not len(xs):continue
  x0,y0,x1,y1=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1);im=Image.new('RGBA',(32,32));im.alpha_composite(masters['barrier'].resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
  rule=add(im,t['pattern'],e['palette'],flight+'&enemyWorld');rules.pop();new.append(rule)
# Use the same geometry when the game swaps the ground-target palette.
for l in list(new)+list(fallback.values()):
 if ',FF101B0F,' in l:new.append(l.replace(',FF101B0F,',',FF381A0F,'))
 elif ',FF381A0F,' in l:new.append(l.replace(',FF381A0F,',',FF101B0F,'))
rules=new+list(fallback.values())+rules
# Two newly observed banked fighter layouts reuse approved aircraft masters.
for e in M['missing_aircraft']:
 art=trim('mission2_reused_front.png' if e['id']==13 else 'mission2_reused_rear.png')
 art=art.rotate(-25 if e['id']==13 else -40,Image.Resampling.BICUBIC,expand=True)
 w,h=e['size'];x0,y0,x1,y1=e['bbox'];im=Image.new('RGBA',(w*4,h*4));im.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 for t in e['tiles']:
  piece=im.crop((t['x']*4,t['y']*4,t['x']*4+32,t['y']*4+32))
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  add(piece,t['pattern'],'FF381A0F',flight+'&enemyWorld')
# Fully connected refueling introduces a larger boom and two earlier tube
# keys absent from the previous recordings. Assemble it from the same master.
refuel=scene+'&mission2Flight&refuelRoute&refuelActive'
boom=trim('mission2_boom_master.png');extra=[]
for e in M['boom_extra']:
 ts=e['tiles'];main=ts[:34] if e['id']==81 else ts[:10]
 x0=min(t['x'] for t in main);y0=min(t['y'] for t in main);x1=max(t['x'] for t in main)+8;y1=max(t['y'] for t in main)+8
 art=boom.crop((0,int(boom.height*.15),boom.width,boom.height)) if e['id']==81 else boom
 im=Image.new('RGBA',((max(t['x'] for t in ts)+8)*4,(max(t['y'] for t in ts)+8)*4))
 im.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 # Fixed connecting tube uses one strip sampled from the approved metal.
 for ti,t in enumerate(ts):
  pattern=t['pattern']
  if e['id']==28 and t['tile'] not in [0xcc,0xdc]:continue
  if e['id']==81 and ti>=34:
   a=dec(pattern);ys,xs=np.where(a>0);piece=Image.new('RGBA',(32,32))
   if len(xs):
    bx0,by0,bx1,by1=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)
    row=int(boom.height*.10);opaque=np.where(np.array(boom.getchannel('A'))[row]>=128)[0];tube=boom.crop((int(opaque.min()),row,int(opaque.max()+1),row+1))
    piece.alpha_composite(tube.resize(((bx1-bx0)*4,(by1-by0)*4),Image.Resampling.LANCZOS),(bx0*4,by0*4))
  else:
   piece=im.crop((t['x']*4,t['y']*4,t['x']*4+32,t['y']*4+32))
   if t['attr']&64:piece=ImageOps.mirror(piece)
   if t['attr']&128:piece=ImageOps.flip(piece)
  cond=refuel+'&enemyWorld'+('&hmirror' if t['attr']&64 else '&!hmirror')+('&vmirror' if t['attr']&128 else '&!vmirror')
  if e['id']==81:
   tag=f'm3ConnectedBoomY{ti}';conditions.append(f'<condition>{tag},originPositionCheckY,==,{e["origin"][1]+t["y"]}');cond+='&'+tag
   # Stage 5 is the connected pose. Exact keys still preserve a fallback below.
   if 'm3BoomConnected' not in [c.split(',')[0][11:] for c in conditions]:conditions.append('<condition>m3BoomConnected,memoryCheckConstant,009F,==,05')
   cond+='&m3BoomConnected'
  rule=add(piece,pattern,'FF10000F',cond);rules.pop();extra.append(rule)
# Keep inherited specific refueling glyphs ahead of generic panel defaults.
for l in lines:
 if l.startswith('[') and '<tile>' in l and 'refuel' in l and 'missionTwo' not in l:
  extra.append(l.replace(']<tile>','&missionThree]<tile>'))
# Mask the last sky tile origin, which crosses scanline 128 on this route.
conditions.append('<condition>m3RefuelWorld,positionCheckY,<,132')
for p in json.loads((S/'mission2_mappings.json').read_text())['tanker_mask_keys']:
 extra.append(f'[{refuel}&m3RefuelWorld]<tile>0,{p},0F300021,0,0,1,N')
rules=extra+rules
# The raster split leaves three native sky scanlines below the last tile
# origin. A narrow layer above NES BG and below sprites closes that seam.
edge=Image.new('RGBA',(1024,960));sky=Image.open(P/'environment_sky.png').convert('RGBA');edge.paste(sky.crop((0,500,1024,512)),(0,500));save_png(edge,P/'mission3_refuel_lower_edge.png')
backgrounds.insert(0,f'[{refuel}]<background>mission3_refuel_lower_edge.png,1,0,0,21')
# Preserve original defaults when adding an exact palette key: Mesen exact
# lookup otherwise suppresses the older generic alternative even out of scope.
oldkeys=set();defaults=defaultdict(list)
for l in lines:
 if '<tile>' not in l:continue
 p=l.split('<tile>')[1].split(',');oldkeys.add((p[1],p[2]))
 if p[6]=='Y':defaults[p[1]].append(l)
newkeys={(p[1],p[2]) for l in rules if '<tile>' in l for p in [l.split('<tile>')[1].split(',')]}
for p,pal in sorted(newkeys-oldkeys):
 for l in defaults[p]:
  v=l.split('<tile>')[1].split(',');v[2]=pal;v[6]='N';rules.append(l.split('<tile>')[0]+'<tile>'+','.join(v))
save_png(atlas,P/'mission3_sprites.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1;lines[i:i]=['<img>mission3_sprites.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l);lines[i:i]=backgrounds+rules
lines[0]='# Top Gun HD v0.10.0 - Mission 3 desert and ground targets'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
(S/'mission3_build.json').write_text(json.dumps(dict(atlas_cells=slot,rules=len(rules),conditions=len(conditions),backgrounds=len(backgrounds)),indent=2)+'\n')
print('Mission 3:',slot,'atlas cells;',len(rules),'rules;',len(backgrounds),'backgrounds')
