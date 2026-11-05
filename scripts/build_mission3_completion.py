"""Recorded Mission 3 missing poses, base approach and native boss meter."""
from pathlib import Path
from collections import defaultdict
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pack_io import save_png
R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
M=json.loads((S/'mission3_completion_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines()
assert '<img>mission3_completion.png' not in lines
index=sum(l.startswith('<img>') for l in lines)
scene='cockpit&cockpitBorder&missionThree&mission2Flight&rearCombatPhase'
world=scene+'&environmentWorld';sprite=scene+'&enemyWorld'
conditions=[];rules=[];backgrounds=[];atlas=Image.new('RGBA',(1024,256));slot=0

def trim(im):return im.crop(im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())
def master(name):return trim(Image.open(S/name).convert('RGBA'))
def dec(p):
 b=np.frombuffer(bytes.fromhex(p),np.uint8);return np.unpackbits(b[:8,None],axis=1)+2*np.unpackbits(b[8:,None],axis=1)
def add(im,p,pal,gate):
 global slot
 x,y=slot%32*32,slot//32*32;slot+=1;assert slot<=256
 atlas.alpha_composite(im,(x,y));rule=f'[{gate}]<tile>{index},{p},{pal},{x},{y},1,N';rules.append(rule);return rule

# A tile's canonical art is unchanged by OAM mirroring. The earlier aircraft
# additions only admitted unmirrored sprites, so the opposite bank reverted.
# Expand only their orientation gates; keep the existing atlas and ordering.
mirrors=[]
for l in lines:
 if l.startswith('['+sprite) and '<tile>16,' in l and '&!hmirror&!vmirror]' in l:
  mirrors.append(l.replace('&!hmirror&!vmirror]','&hmirror&!vmirror]'))
rules.extend(mirrors)
# Explosion sprites can clip the incoming missile's complete signature.
# Its surviving cells must retain their approved metal artwork independently.
missile_fallback=[]
for l in lines:
 if '<tile>' in l and '&incoming' in l and ',FF2A100F,' in l:
  head,tail=l.split(']<tile>');gates=[g for g in head[1:].split('&') if not g.startswith('incoming')]
  missile_fallback.append('['+'&'.join(gates)+'&missionThree&mission2Flight&rearCombatPhase]<tile>'+tail)
rules.extend(missile_fallback)

# New captured layouts get full relative signatures. Fallbacks cover clipped
# tiles, but never outrank a previously mapped family with the same key.
oldkeys={tuple(l.split('<tile>')[1].split(',')[1:3]) for l in lines if '<tile>' in l}
fallback=[]
parts=Image.open(S/'mission2_boss_components_master.png').convert('RGBA')
partbox=json.loads((S/'mission2_approach_mappings.json').read_text())['component_crops']['turret']
gun=trim(parts.crop(partbox))
for li,e in enumerate(M['new_layouts']):
 kind=e['kind'];art=gun if kind=='groundgun' else master('mission3_radar_master.png') if kind=='radar' else master('mission2_reused_front.png').rotate(55,Image.Resampling.BICUBIC,expand=True)
 if e['id']==71:art=ImageOps.mirror(art)
 w,h=e['size'];x0,y0,x1,y1=e['bbox'];im=Image.new('RGBA',(w*4,h*4));im.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 pals=[e['palette']] if kind=='aircraft' else ['FF101B0F','FF381A0F']
 for ti,t in enumerate(e['tiles']):
  piece=im.crop((t['x']*4,t['y']*4,t['x']*4+32,t['y']*4+32))
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  for pi,pal in enumerate(pals):
   gate=sprite+('&hmirror' if t['attr']&64 else '&!hmirror')+('&vmirror' if t['attr']&128 else '&!vmirror')
   anchors=[]
   for ai,a in enumerate([e['tiles'][0],e['tiles'][-1]]):
    name=f'm3Complete{li}_{ti}_{pi}_{ai}';anchors.append(name);conditions.append(f'<condition>{name},spriteNearby,{a["x"]-t["x"]},{a["y"]-t["y"]},{a["pattern"]},{pal},N')
   rule=add(piece,t['pattern'],pal,gate+'&'+'&'.join(anchors))
   if (t['pattern'],pal) not in oldkeys:fallback.append(rule.replace('&'+'&'.join(anchors),''))
rules.extend(fallback)

# The large barricade is a repeating column. Use one continuous approved
# brace module per repeated upper cell and its short foot at the bottom.
barrier=master('mission3_barrier_master.png');seen=set()
for t in M['barrier_cells']:
 if t['pattern'] in seen:continue
 seen.add(t['pattern']);a=dec(t['pattern']);ys,xs=np.where(a>0);x0,y0,x1,y1=map(int,(xs.min(),ys.min(),xs.max()+1,ys.max()+1));art=barrier
 if t['tile']==0xb1:art=barrier.crop((0,int(barrier.height*.75),barrier.width,barrier.height))
 piece=Image.new('RGBA',(32,32));piece.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 for pal in ['FF101B0F','FF381A0F']:add(piece,t['pattern'],pal,sprite)

# Every native base size has one scroll-following plate. Exact nametable
# layouts win; the native distance counter handles multi-frame transfers.
base=master('mission3_base_master.png');plates={}
for e in M['boss_stages']:
 st=e['stage'];ox,oy=e['origin'];x0,y0,x1,y1=e['bbox'];art=base.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS)
 plate=Image.new('RGBA',(2048,1536))
 for dx in [0,1024]:plate.alpha_composite(art,((ox+x0)*4+dx,(oy+y0)*4))
 name=f'mission3_base_{st:02d}.png';save_png(plate,P/name);plates[st]=name;gates=[]
 for ti,t in enumerate(e['tiles']):
  name=f'm3BaseSize{st}Tile{ti}';gates.append(name);address=0x2000+(oy+t['y'])//8*32+(ox+t['x'])//8
  conditions.append(f'<condition>{name},ppuMemoryCheckConstant,{address:04X},==,{t["tile"]:02X}')
 backgrounds.append(f'[{scene}&bossBodyPresent&'+ '&'.join(gates)+f']<background>{plates[st]},1,1,1,9')
for st,name in plates.items():backgrounds.append(f'[{scene}&bossBodyPresent&bossDistance{st}]<background>{name},1,1,1,9')
# These CHR keys are buildings, not explosions. Reveal the new base only in
# Mission 3 while native BG geometry is actually present.
for p in M['boss_background_keys']:rules.append(f'[{world}&bossBodyPresent]<tile>0,{p},0F302721,0,0,1,N')
# A lethal hit replaces the desert palette with the shared damage palette.
# Retain the desert and mask the transferred BG tiles through that palette's
# native lifetime, including the two frames after the hull flag resets.
conditions.append('<condition>m3DamageDesert,ppuMemoryCheckConstant,3F06,==,10')
for l in lines:
 if '<background>mission3_desert_' in l or '<background>mission3_sky_edge_' in l:
  if 'mission3Desert' in l and 'm3Refuel' not in l and 'mission3Refuel' not in l:
   backgrounds.append(l.replace('mission3Desert','m3DamageDesert&mission2Flight&rearCombatPhase'))
for p in M['damage_world_keys']:
 rules.append(f'[{world}&m3DamageDesert]<tile>0,{p},0F301016,0,0,1,N')
# Top raster scanline can still carry the previous vertical scroll.
backgrounds.insert(0,f'[{scene}&bossBodyPresent&envBank_zero]<background>mission3_sky_edge_zero.png,1,0,0,21')

# Exact native full / half / empty patterns drive six independent cells.
# No guessed HP counter, fixed fill, timing, or RAM modification.
title=Image.new('RGBA',(192,32),'#061b20df');d=ImageDraw.Draw(title);d.text((96,0),'BASE',font=ImageFont.truetype(str(S/'fonts/DejaVuSansMono-Bold.ttf'),13),anchor='mt',fill='#e3d8b3')
health=dict(M['health']);health['F0F1F0F1F0F1F1FF0000000000000000']={'tile':17}
for cell in range(6):
 for p,e in health.items():
  im=title.crop((cell*32,0,cell*32+32,32));d=ImageDraw.Draw(im);d.rounded_rectangle((2,16,29,29),radius=2,fill='#132d32',outline='#77908a',width=1)
  amount={16:24,17:12,18:0}[e['tile']]
  if amount:d.rectangle((4,18,3+amount,27),fill='#efbb62');d.line((4,18,3+amount,18),fill='#ffe1a1')
  add(im,p,'FF2A100F',scene+f'&bossMeterY0&bossMeterY1&bossMeterX{cell}')

# New exact-palette keys must preserve all old generic fallback alternatives.
defaults=defaultdict(list)
for l in lines:
 if '<tile>' not in l:continue
 v=l.split('<tile>')[1].split(',')
 if v[6]=='Y':defaults[v[1]].append(l)
newkeys={tuple(l.split('<tile>')[1].split(',')[1:3]) for l in rules}
for p,pal in sorted(newkeys-oldkeys):
 for l in defaults[p]:
  v=l.split('<tile>')[1].split(',');v[2]=pal;v[6]='N';rules.append(l.split('<tile>')[0]+'<tile>'+','.join(v))
save_png(atlas,P/'mission3_completion.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1;lines[i:i]=['<img>mission3_completion.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l);lines[i:i]=backgrounds+rules
lines[0]='# Top Gun HD v0.11.0 - Mission 3 missing poses, base approach and boss meter'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
report=dict(atlas_cells=slot,rules=len(rules),conditions=len(conditions),backgrounds=len(backgrounds),mirror_aliases=len(mirrors),base_sizes=len(plates),preserved_pngs=171)
(S/'mission3_completion_build.json').write_text(json.dumps(report,indent=2)+'\n');print('Mission 3 completion:',report)
