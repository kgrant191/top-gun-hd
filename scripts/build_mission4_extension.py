"""Mission 4 recorded ground phases, single tanker, and missing target sizes."""
from pathlib import Path
from collections import defaultdict
import json
import numpy as np
from PIL import Image, ImageOps
from pack_io import save_png

R=Path(__file__).resolve().parents[1]; P=R/'pack'; S=R/'source'
lines=(P/'hires.txt').read_text().splitlines()
assert not any('m4DesertPhase,' in l for l in lines)
M=json.loads((S/'mission4_extension_mappings.json').read_text())
index=sum(l.startswith('<img>') for l in lines)
scene='cockpit&cockpitBorder&missionFour'
flight=scene+'&mission2Flight&rearCombatPhase'
refuel=scene+'&mission2Flight&refuelRoute&refuelActive'
conditions=['<condition>m4DesertPhase,memoryCheckConstant,0037,==,02',
 '<condition>m4RockyPhase,memoryCheckConstant,0037,==,03',
 '<condition>m4DesertPalette,ppuMemoryCheckConstant,3F06,==,06',
 '<condition>m4RockyPalette,ppuMemoryCheckConstant,3F06,==,10',
 '<condition>m4RefuelPalette,ppuMemoryCheckConstant,3F06,==,00']
rules=[]; backgrounds=[]

# Carry forward complete radar silhouettes, ground targets, projectile keys,
# and connected boom geometry. The base boss has separate native geometry.
ground=[]
def reusable_m3(l):
 head=l[1:l.index(']')]
 return any(f'<tile>{i},' in l for i in [17,18,19]) or 'refuel' in head.lower()
for l in lines:
 if not l.startswith('[') or '<tile>' not in l: continue
 head=l[1:l.index(']')].split('&')
 if 'missionThree' not in head or any('base' in n.lower() or 'menu' in n.lower() for n in head): continue
 if '<tile>20,' in l: continue
 if not reusable_m3(l):continue
 ground.append(l.replace('missionThree','missionFour'))
rules.extend(ground)
# Native refueling uses solid sprite columns to hide the wrapped tanker.
# Their Mission 4 palette differs from the earlier mission's mask palette.
rules.append(f'[{refuel}&enemyWorld]<tile>0,0000000000000000FFFFFFFFFFFFFFFF,FF380C0F,0,0,1,N')
# A missile can cover the small flame's neighboring top cell. Its unique
# unmirrored corner still identifies the approved 16-pixel burst artwork.
for phase in ['m4DesertPhase','m4RockyPhase']:
 rules.append(f'[{flight}&{phase}&enemyWorld&!hmirror&!vmirror]<tile>9,00C814C64A64277F00000000041F1F0F,FF162630,192,96,1,N')
# The first disconnect frame still contains the fully connected OAM pose.
# Keep that pose HD until native sprite transfer replaces it. Its exact CHR,
# mirroring and Y positions match only this frame in the recorded stage 6;
# subsequent stage-6 poses use their ordinary boom art.
conditions.append('<condition>m4BoomRelease,memoryCheckConstant,009F,==,06')
for l in ground:
 if '&m3BoomConnected]' not in l:continue
 rules.insert(0,l.replace('&m3BoomConnected]','&m4BoomRelease]'))

# Reuse palette-independent arrival/departure predicates. A two-page tanker
# is correct only after the native entrance scroll reset and before exit.
for l in lines:
 if l.startswith('[') and '&missionThree' in l and '<background>mission2_tanker' in l:
  backgrounds.append(l.replace('missionThree','missionFour'))
lines=[l.replace('&!missionTwo&!missionThree]<background>mission2_tanker.png',
 '&!missionTwo&!missionThree&!missionFour]<background>mission2_tanker.png') for l in lines]

# Palette families recorded in red ground, refueling, and the dark final
# terrain. Relative sprite predicates must receive the same palette alias.
phase_maps=[{'0F2A0A21':'0F2A0A0C','0F001121':'0F00110C','0F261621':'0F26160C',
             '0F301121':'0F37060C','0F302721':'0F37060C'},
            {'0F2A0A21':'0F2A0A0C','0F001121':'0F00110C','0F261621':'0F26160C',
             '0F300021':'0F30000C','FF381A0F':'FF380C0F'},
            {'0F2A0A21':'0F2A0A0F','0F001121':'0F00110F','0F261621':'0F26160F',
             '0F301121':'0F00100F','0F302721':'0F00100F',
             'FF381A0F':'FF20180F','FF101B0F':'FF10000F'}]
source=[]
for l in lines:
 if not l.startswith('['): continue
 ts=l[1:l.index(']')].split('&')
 if any(t in ts for t in ['missionFour','missionTwo','!missionTwo','!missionThree']): continue
 if any('base' in t.lower() or 'menu' in t.lower() for t in ts): continue
 if '<background>' in l: continue
 if 'missionThree' in ts and not reusable_m3(l):continue
 source.append(l.replace('missionThree','missionFour'))
# Newer Mission 4 aircraft geometry also needs the dark-ground sprite palette.
source.extend(l for l in lines if l.startswith('[') and '&missionFour' in l and '<tile>' in l)
for pi,pm in enumerate(phase_maps):
 aliases={}
 for l in lines:
  if not l.startswith('<condition>') or not any(p in l for p in pm): continue
  name=l.split(',')[0][11:];new=f'{name}M4Ext{pi}';aliases[name]=new
  q=l.replace('<condition>'+name+',','<condition>'+new+',')
  for a,b in pm.items(): q=q.replace(a,b)
  conditions.append(q)
 for l in source:
  head,tail=l[1:].split(']',1);ts=head.split('&')
  if not any(t.lstrip('!') in aliases for t in ts) and not any(p in tail for p in pm): continue
  ts=[('!' if t.startswith('!') else '')+aliases.get(t.lstrip('!'),t.lstrip('!')) for t in ts]
  if 'missionFour' not in ts: ts.append('missionFour')
  for a,b in pm.items():tail=tail.replace(a,b)
  rules.append('['+'&'.join(ts)+']'+tail)

# Scenery follows the native bank and vertical scroll. Palette checks keep
# the ground clear during tanker flight, while phase checks survive damage.
for material,phase,state in [('desert','m4DesertPhase','m4DesertPalette'),('rocky','m4RockyPhase','m4RockyPalette')]:
 surface=Image.open(S/f'mission4_{material}_master.png').convert('RGBA').resize((1280,1024),Image.Resampling.LANCZOS)
 for bank,slope in [(0,0),(-1,1/32),(-2,1/16),(-3,1/8),(1,-1/32),(2,-1/16),(3,-1/8)]:
  tag='zero' if bank==0 else ('left' if bank<0 else 'right')+str(abs(bank))
  base=Image.new('RGBA',(1280,1856));base.paste(surface,(0,766));a=np.array(base)
  a[:,:,3]=np.uint8(a[:,:,3]*np.clip((np.arange(base.height)-766)/8,0,1)[:,None])
  turned=Image.fromarray(a).transform((1024,1536),Image.Transform.AFFINE,(1,0,128,-slope,1,slope*512),Image.Resampling.BICUBIC)
  name=f'mission4_{material}_{tag}.png';save_png(turned,P/name)
  for gate in [state+'&'+phase,'impactPalette&'+phase]:
   backgrounds.append(f'[{scene}&envBank_{tag}&{gate}]<background>{name},1,0,1,7')
sky=Image.open(P/'mission4_sky_zero.png').convert('RGBA')
edge=Image.new('RGBA',(1024,960));edge.paste(sky.crop((0,500,1024,512)),(0,500));save_png(edge,P/'mission4_refuel_lower_edge.png')
backgrounds.insert(0,f'[{refuel}]<background>mission4_refuel_lower_edge.png,1,0,0,21')
# Native tanker scroll exposes solid-color fill cells from another palette
# at the wrap boundary. A sky plate above NES BG clears the complete flight
# window while leaving native sprites and the priority-31 tanker visible.
backgrounds.insert(0,f'[{refuel}&refuelAircraftVisible]<background>mission4_sky_zero.png,1,0,0,21')
# Upper/lower raster seams need separate priorities during tanker scrolling.
# On phase 8 the ground also resumes beneath the departing aircraft layer.
backgrounds.insert(0,f'[{refuel}&envBank_zero]<background>mission4_sky_edge_zero.png,1,0,0,22')
worldkeys=set(json.loads((S/'mission4_mappings.json').read_text())['world_keys'])
worldkeys.update(json.loads((S/'mission3_mappings.json').read_text())['terrain_keys'])
for p in sorted(worldkeys):
 for pal in ['0F37060C','0F00100F','0F30000C']:
  rules.insert(0,f'[{scene}&environmentWorld]<tile>0,{p},{pal},0,0,1,N')
for pal,keys in M['world_keys'].items():
 for p in keys:
  rules.insert(0,f'[{scene}&environmentWorld]<tile>0,{p},{pal},0,0,1,N')
  if pal!='0F30000C':
   phase='m4DesertPhase' if pal=='0F37060C' else 'm4RockyPhase'
   rules.insert(0,f'[{scene}&environmentWorld&{phase}]<tile>0,{p},0F301016,0,0,1,N')

# Additional boat sizes retain the approved hull. Mirrored OAM pieces are
# unmirrored before atlas storage, because the emulator applies that flag.
atlas=Image.new('RGBA',(1024,128));slot=0;new=[];fallback=[]
for kind in ['boats','aircraft']:
 art=Image.open(S/('mission2_boat_master.png' if kind=='boats' else 'mission2_reused_front.png')).convert('RGBA')
 art=art.crop(art.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())
 for e in M[kind]:
  src=ImageOps.mirror(art) if e['tiles'][0]['attr']&64 else art
  if kind=='aircraft':src=src.rotate(-55 if e['id'] in [11,20] else -25,Image.Resampling.BICUBIC,expand=True)
  w,h=e['size'];x0,y0,x1,y1=e['bbox'];im=Image.new('RGBA',(w*4,h*4))
  im.alpha_composite(src.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
  for ti,t in enumerate(e['tiles']):
   piece=im.crop((t['x']*4,t['y']*4,t['x']*4+32,t['y']*4+32))
   if t['attr']&64:piece=ImageOps.mirror(piece)
   if t['attr']&128:piece=ImageOps.flip(piece)
   ax,ay=slot%32*32,slot//32*32;slot+=1;atlas.alpha_composite(piece,(ax,ay))
   gates=[]
   for ai,anchor in enumerate([e['tiles'][0],e['tiles'][-1]]):
    name=f'm4Ext{e["id"]}_{ti}_{ai}';gates.append(name)
    conditions.append(f'<condition>{name},spriteNearby,{anchor["x"]-t["x"]},{anchor["y"]-t["y"]},{anchor["pattern"]},{e["palette"]},N')
   gate=flight+'&enemyWorld'+('&hmirror' if t['attr']&64 else '&!hmirror')+('&vmirror' if t['attr']&128 else '&!vmirror')
   tail=f'<tile>{index},{t["pattern"]},{e["palette"]},{ax},{ay},1,N'
   new.append('['+gate+'&'+'&'.join(gates)+']'+tail);fallback.append('['+gate+']'+tail)
rules=new+rules+fallback

# Exact palette keys disable generic defaults in Mesen. Preserve those
# alternatives outside the new scope, including their original order.
oldkeys=set();defaults=defaultdict(list)
for l in lines:
 if '<tile>' not in l:continue
 v=l.split('<tile>')[1].split(',');oldkeys.add(tuple(v[1:3]))
 if v[6]=='Y':defaults[v[1]].append(l)
newkeys={tuple(l.split('<tile>')[1].split(',')[1:3]) for l in rules if '<tile>' in l}
for p,pal in sorted(newkeys-oldkeys):
 for l in defaults[p]:
  v=l.split('<tile>')[1].split(',');v[2]=pal;v[6]='N';rules.append(l.split('<tile>')[0]+'<tile>'+','.join(v))
rules=list(dict.fromkeys(rules));backgrounds=list(dict.fromkeys(backgrounds))
save_png(atlas,P/'mission4_extension.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1;lines[i:i]=['<img>mission4_extension.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l);lines[i:i]=backgrounds+rules
lines[0]='# Top Gun HD v0.13.0 - Mission 4 ground combat and single-aircraft refueling'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
(S/'mission4_extension_build.json').write_text(json.dumps(dict(rules=len(rules),conditions=len(conditions),backgrounds=len(backgrounds),atlas_cells=slot),indent=2)+'\n')
print('Mission 4 extension:',len(rules),'rules,',len(backgrounds),'backgrounds')
