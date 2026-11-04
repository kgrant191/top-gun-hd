"""Native carrier distance stages, separate bridge/guns, missing fighters and ordinal."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pack_io import save_png

R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
M=json.loads((S/'mission2_approach_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines()
assert '<img>mission2_approach.png' not in lines
index=sum(l.startswith('<img>') for l in lines)
scene='cockpit&cockpitBorder&missionTwo&mission2Flight&rearCombatPhase'
world=scene+'&environmentWorld'
conditions=['<condition>bossBodyPresent,ppuMemoryCheckConstant,2330,>=,C0',
 '<condition>targetOrdinalS,ppuMemoryCheckConstant,2AAB,==,22',
 '<condition>targetOrdinalT,ppuMemoryCheckConstant,2AAC,==,23',
 '<condition>targetOrdinalX,originPositionCheckX,==,80',
 '<condition>targetOrdinalY,originPositionCheckY,==,168']
rules=[]
# The first scanline retains the previous vertical scroll before the game's
# raster split. Reuse the approved level-flight sky edge so the closest
# carrier's wake cannot wrap onto the top of the windshield.
backgrounds=[f'[{scene}&bossBodyPresent&envBank_zero]<background>mission2_refuel_sky_edge.png,1,0,0,21']
atlas=Image.new('RGBA',(1024,512));slot=0
def trim(im):return im.crop(im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())
def master(name):return trim(Image.open(S/name).convert('RGBA'))
def add(im,pattern,palette,cond):
 global slot
 x,y=slot%32*32,slot//32*32;slot+=1;assert slot<=512
 atlas.alpha_composite(im,(x,y));rule=f'[{cond}]<tile>{index},{pattern},{palette},{x},{y},1,N';rules.append(rule);return rule

sheet=Image.open(S/'mission2_boss_components_master.png').convert('RGBA')
parts={name:trim(sheet.crop(box)) for name,box in M['component_crops'].items()}
full=master('mission2_boss_approach_master.png');side=master('landing_broadside_master.png')
plates={}
for entry in M['stages']:
 stage=entry['stage'];ox,oy=entry['origin'];x0,y0,x1,y1=entry['bbox']
 art=side if stage==0 else full if stage<4 else parts['deck']
 art=art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS)
 plate=Image.new('RGBA',(2048,1536))
 for dx in [0,1024]:plate.alpha_composite(art,((ox+x0)*4+dx,(oy+y0)*4))
 name=f'mission2_carrier_{stage:02d}.png';save_png(plate,P/name);plates[stage]=name
 gates=[]
 for i,test in enumerate(entry['checks']):
  tag=f'bossSize{stage}Tile{i}';gates.append(tag)
  conditions.append(f'<condition>{tag},ppuMemoryCheckConstant,{test["address"]:04X},==,{test["value"]:02X}')
 backgrounds.append(f'[{scene}&bossBodyPresent&'+ '&'.join(gates)+f']<background>{name},1,1,1,9')
# The native size counter advances before the nametable transfer finishes.
# Stable native layouts win above; a transfer's partial layout uses its one
# current size as a fallback, never two overlaid ships or an empty frame.
for stage in range(13):
 tag=f'bossDistance{stage}';conditions.append(f'<condition>{tag},memoryCheckConstant,0078,==,{stage:02X}')
 backgrounds.append(f'[{scene}&bossBodyPresent&{tag}]<background>{plates[min(stage,11)]},1,1,1,9')

# The earlier two-cell "damaged"/"explosion" images were healthy distance
# stages. Hide all captured native carrier BG keys, revealing the new opaque
# deck plate, including shared blue interior cells and bank-transfer frames.
for pattern in sorted(set(M['boss_background_keys'])|set(M['ocean_keys'])):
 for palette in ['0F301121','0F301016']:
  rules.append(f'[{world}]<tile>0,{pattern},{palette},0,0,1,N')

# The native impact-center sprites survive the hullImpact RAM flag by two
# frames in the close-approach movie. Keep these exact center keys masked
# through their own sprite lifetime so they cannot cover the HD flame burst.
damage=json.loads((S/'damage_hud_mappings.json').read_text())
for pattern in damage['impact_center']:
 rules.append(f'[{scene}&enemyWorld]<tile>0,{pattern},FF2A100F,0,0,1,N')

# Keep native bridge/gun sprites independent from the hull. They can move,
# animate, clip and disappear without leaving a painted tower on the deck.
# Nearby signatures disambiguate shared tile pieces between distance sizes.
fallback={}
for li,e in enumerate(sorted(M['boss_sprite_layouts'],key=lambda e:-e['count'])):
 x0,y0,x1,y1=e['bbox'];w,h=e['size'];im=Image.new('RGBA',(w*4,h*4))
 im.alpha_composite(parts[e['kind']].resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 anchors=[e['tiles'][0]]
 if len(e['tiles'])>1:anchors.append(e['tiles'][-1])
 for ti,t in enumerate(e['tiles']):
  x,y=t['x']*4,t['y']*4;piece=im.crop((x,y,x+32,y+32));gates=[]
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  for ai,a in enumerate(anchors):
   name=f'bossPart{li}_{ti}_{ai}';gates.append(name)
   conditions.append(f'<condition>{name},spriteNearby,{a["x"]-t["x"]},{a["y"]-t["y"]},{a["pattern"]},FF2A100F,N')
  rule=add(piece,t['pattern'],'FF2A100F',scene+'&enemyWorld&'+'&'.join(gates))
  fallback.setdefault(t['pattern'],rule.split(']<tile>')[1])
for pattern,tail in fallback.items():rules.append(f'[{scene}&enemyWorld]<tile>'+tail)

# Three newly recorded right-bank fighter layouts reuse the approved front
# view, rotated to the native silhouette and sliced at the native tile edges.
fighter=master('mission2_reused_front.png').rotate(-35,Image.Resampling.BICUBIC,expand=True)
airkeys=set()
for e in sorted(M['aircraft_layouts'],key=lambda e:-e['count']):
 x0,y0,x1,y1=e['bbox'];w,h=e['size'];im=Image.new('RGBA',(w*4,h*4))
 im.alpha_composite(fighter.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 for t in e['tiles']:
  key=(t['pattern'],t['attr']&192)
  if key in airkeys:continue
  airkeys.add(key);x,y=t['x']*4,t['y']*4;piece=im.crop((x,y,x+32,y+32))
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  gate=scene+'&enemyWorld'+('&hmirror' if t['attr']&64 else '&!hmirror')+('&vmirror' if t['attr']&128 else '&!vmirror')
  for palette in ['FF381A0F','FF38210F','FF153630']:add(piece,t['pattern'],palette,gate)

# Native tile 02 is shared by numeral 1 and letter I. Only the ordinal before
# the native ST sequence gets a numeral; instruction words retain their I.
im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
d.text((16,15),'1',font=ImageFont.truetype(str(S/'fonts/DejaVuSansMono-Bold.ttf'),23),anchor='mm',fill='#a7eac6')
for palette in ['0F2A0A21','0F2A0A16']:
 add(im,M['ordinal_one_pattern'],palette,scene+'&targetOrdinalS&targetOrdinalT&targetOrdinalX&targetOrdinalY')

# Preserve prior palette-default alternatives whenever adding an exact key.
oldkeys=set();defaults={}
for line in lines:
 if '<tile>' not in line:continue
 v=line.split('<tile>')[1].split(',');oldkeys.add((v[1],v[2]))
 if v[6]=='Y':defaults.setdefault(v[1],[]).append(line)
newkeys={(v[1],v[2]) for line in rules for v in [line.split('<tile>')[1].split(',')]}
for pattern,palette in sorted(newkeys-oldkeys):
 for line in defaults.get(pattern,[]):
  v=line.split('<tile>')[1].split(',');v[2]=palette;v[6]='N'
  rules.append(line.split('<tile>')[0]+'<tile>'+','.join(v))
save_png(atlas,P/'mission2_approach.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1
lines[i:i]=['<img>mission2_approach.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l)
lines[i:i]=backgrounds+rules
lines[0]='# Top Gun HD v0.9.1 - Carrier approach sizes, bridge, guns, fighters and 1ST TARGET'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
(S/'mission2_approach_build.json').write_text(json.dumps({'atlas_cells':slot,'rules':len(rules),'backgrounds':len(backgrounds),'carrier_sizes':len(plates),'fighter_layouts':len(M['aircraft_layouts']),'preserved_v090_pngs':141},indent=2)+'\n')
print('Carrier approach:',len(plates),'sizes,',slot,'atlas cells,',len(rules),'rules')
