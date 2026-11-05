"""Recorded Mission 4 night flight; read-only native palette/scroll predicates."""
from pathlib import Path
from collections import defaultdict
import json,re
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from pack_io import save_png
from map_geometry import contours,simplify,area
R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
M=json.loads((S/'mission4_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines();assert not any('missionFour,' in l for l in lines)
index=sum(l.startswith('<img>') for l in lines)
conditions=['<condition>missionFour,memoryCheckConstant,0030,==,04',
 '<condition>m4Clouds,ppuMemoryCheckConstant,3F06,==,31',
 '<condition>m4Ocean,ppuMemoryCheckConstant,3F06,==,0C',
 '<condition>m4CloudPhase,memoryCheckConstant,0037,==,00',
 '<condition>m4SeaPhase,memoryCheckConstant,0037,==,01',
 f'<condition>menuMissionFour,tileAtPosition,80,32,{M["mission_four_pattern"]},00000000,Y',
 f'<condition>menuMapFour,tileAtPosition,80,112,{M["map_anchor"]},00000000,Y']
scene='cockpit&cockpitBorder&missionFour';flight=scene+'&mission2Flight&rearCombatPhase'
backgrounds=[];rules=[];atlas=Image.new('RGBA',(1024,128));slot=0
# Generic typography remains native-driven. Copy Mission 2 menu layout to 4.
for l in lines:
 if l.startswith('[') and 'menuMissionTwo' in l and 'menuMapTwo' not in l:
  q=l.replace('menuMissionTwo','menuMissionFour');(backgrounds if '<background>' in q else rules).append(q)
# Carry the approved naval/aircraft fixes forward in their original priority.
# Boss carrier/base geometries are separate encounters and not cloned here.
for l in lines:
 if not l.startswith('[') or '<tile>' not in l:continue
 if 'missionTwo' in l and '!missionTwo' not in l:
  if any(k in l for k in ['bossBodyPresent','bossPart','bossSize','bossDistance','bossMeter','mission2BossRoute','menuMission']):continue
  if '<tile>15,' in l:continue
  rules.append(l.replace('missionTwo','missionFour'))
# Additional Mission 3 aircraft poses, including opposite-bank corrections.
air3=json.loads((S/'mission3_mappings.json').read_text())['missing_aircraft']
airpatterns={t['pattern'] for e in air3 for t in e['tiles']}
complete=json.loads((S/'mission3_completion_mappings.json').read_text())
airpatterns.update(t['pattern'] for e in complete['new_layouts'] if e['kind']=='aircraft' for t in e['tiles'])
extra=[]
for l in lines:
 if not l.startswith('[') or '<tile>' not in l or 'missionThree' not in l:continue
 v=l.split('<tile>')[1].split(',')
 if v[0] in ['5','6','7','9','14','16'] or (v[0] in ['17','18'] and v[1] in airpatterns):
  extra.append(l.replace('missionThree','missionFour'))
rules=extra+rules
# Each phase has native palettes for HUD, runway and sky. Exact aliases keep
# the approved instrument styling without changing their values or timing.
phase_maps=[{'0F2A0A21':'0F2A0A03','0F001121':'0F001103','0F301121':'0F301103'},
 {'0F2A0A21':'0F2A0A13','0F001121':'0F001113','0F301121':'0F333103'},
 {'0F2A0A21':'0F2A0A11','0F001121':'0F001111','0F301121':'0F120C01'}]
for phase,pm in enumerate(phase_maps):
 aliases={}
 for l in lines:
  if not l.startswith('<condition>') or not any(p in l for p in pm):continue
  name=l.split(',')[0][11:];new=f'{name}M4P{phase}';aliases[name]=new;q=l.replace('<condition>'+name+',','<condition>'+new+',')
  for a,b in pm.items():q=q.replace(a,b)
  conditions.append(q)
 for l in lines:
  if not l.startswith('['):continue
  head,tail=l[1:].split(']',1);ts=head.split('&')
  if any(t in ts for t in ['missionThree','!missionTwo','!missionThree']) or 'menuMission' in head:continue
  if 'missionTwo' in ts:ts=[t for t in ts if t!='missionTwo']
  mapped=any(t.lstrip('!') in aliases for t in ts) or any(p in tail for p in pm)
  if not mapped:continue
  ts=[('!' if t.startswith('!') else '')+aliases.get(t.lstrip('!'),t.lstrip('!')) for t in ts]
  for a,b in pm.items():tail=tail.replace(a,b)
  q='['+'&'.join(ts+['missionFour'])+']'+tail
  (backgrounds if '<background>' in q else rules).append(q)
# Additional gray aircraft use the same art, with palette-aware relative anchors.
gray={}
for l in lines:
 if l.startswith('<condition>') and ',FF381A0F,' in l:
  name=l.split(',')[0][11:];gray[name]=name+'M4Gray';conditions.append(l.replace('<condition>'+name+',','<condition>'+name+'M4Gray,').replace(',FF381A0F,',',FF10000F,'))
for l in list(rules):
 if '<tile>' not in l:continue
 v=l.split('<tile>')[1].split(',')
 if v[2]!='FF381A0F' or not (v[0] in ['5','16'] or (v[0] in ['17','18'] and v[1] in airpatterns)):continue
 head,tail=l[1:].split(']',1);ts=head.split('&');head='&'.join(('!' if t.startswith('!') else '')+gray.get(t.lstrip('!'),t.lstrip('!')) for t in ts)
 rules.append('['+head+']'+tail.replace(',FF381A0F,',',FF10000F,'))
# Night sky and surfaces follow the same native bank/scroll geometry as v0.5.1.
sky=Image.open(S/'mission4_sky_master.png').convert('RGBA').resize((1024,512),Image.Resampling.LANCZOS)
cloud=Image.open(S/'mission4_clouddeck_master.png').convert('RGBA');cloud=cloud.crop((0,int(cloud.height*.1),cloud.width,cloud.height))
water=Image.open(S/'mission4_water_master.png').convert('RGBA')
for bank,slope in [(0,0),(-1,1/32),(-2,1/16),(-3,1/8),(1,-1/32),(2,-1/16),(3,-1/8)]:
 tag='zero' if bank==0 else ('left' if bank<0 else 'right')+str(abs(bank));gate=scene+'&envBank_'+tag
 wide=Image.fromarray(np.pad(np.array(sky),((64,64),(128,128),(0,0)),mode='reflect'))
 turned=wide.transform((1024,512),Image.Transform.AFFINE,(1,0,128,-slope,1,64+slope*512),Image.Resampling.BICUBIC)
 plate=Image.new('RGBA',(1024,960));plate.paste(turned,(0,0));name=f'mission4_sky_{tag}.png';save_png(plate,P/name)
 backgrounds.insert(0,f'[{gate}]<background>{name},1,0,0,6')
 edge=f'mission4_sky_edge_{tag}.png';save_png(turned.crop((0,0,1024,12)),P/edge);backgrounds.insert(0,f'[{gate}]<background>{edge},1,0,0,21')
 for material,master in [('clouds',cloud),('ocean',water)]:
  surface=master.resize((1280,1024),Image.Resampling.LANCZOS);start=752 if material=='clouds' else 766;fade=48 if material=='clouds' else 8
  base=Image.new('RGBA',(1280,1856));base.paste(surface,(0,start));a=np.array(base);a[:,:,3]=np.uint8(a[:,:,3]*np.clip((np.arange(base.height)-start)/fade,0,1)[:,None]);base=Image.fromarray(a)
  turned=base.transform((1024,1536),Image.Transform.AFFINE,(1,0,128,-slope,1,slope*512),Image.Resampling.BICUBIC);name=f'mission4_{material}_{tag}.png';save_png(turned,P/name)
  state='m4Clouds' if material=='clouds' else 'm4Ocean'
  backgrounds.insert(0,f'[{gate}&{state}]<background>{name},1,0,1,7')
  impact_state='m4CloudPhase' if material=='clouds' else 'm4SeaPhase'
  backgrounds.insert(0,f'[{gate}&impactPalette&{impact_state}]<background>{name},1,0,1,7')
# Captured world CHR keys mask only scenery, confined above the cockpit.
for p in M['world_keys']:
 for pal in ['0F333103','0F120C01','0F301103','0F301016']:
  rules.insert(0,f'[{scene}&environmentWorld]<tile>0,{p},{pal},0,0,1,N')
# Native briefing geography, styled as the earlier tactical maps.
mapim=Image.new('RGBA',(1024,960));d=ImageDraw.Draw(mapim);d.rounded_rectangle((144,364,880,916),radius=12,fill='#04111b',outline='#608b91',width=2)
layer=Image.new('RGBA',(704,512),'#152a47');d=ImageDraw.Draw(layer);polys=[simplify(p) for p in contours(np.array(M['map_pixels'])==0x17)]
for p in sorted(polys,key=lambda p:abs(area(p)),reverse=True):d.polygon([(int(x*4),int(y*4)) for x,y in p],fill='#655950' if area(p)>0 else '#152a47')
for p in polys:d.line([(int(x*4),int(y*4)) for x,y in p],fill='#c2b6a1',width=2,joint='curve')
for x in range(0,704,64):d.line((x,0,x,512),fill='#35465e70',width=1)
for y in range(0,512,64):d.line((0,y,704,y),fill='#35465e70',width=1)
mapim.alpha_composite(layer,(160,384));save_png(mapim,P/'mission4_map.png')
menu='menuMissionM&menuMissionN&menuMissionFour&menuHeaderPresent&menuMapFour';region=menu+'&menuMapX0&menuMapX1&menuMapY0&menuMapY1'
backgrounds.insert(0,f'[{menu}]<background>mission4_map.png,1,0,0,11')
# Reuse marker masks captured in prior maps; the black X and moving ship
# patterns are shared while their native positions remain under game control.
for e in json.loads((S/'mission3_mappings.json').read_text())['map_markers']:
 mask=Image.fromarray(np.uint8(e['mask'])*255).resize((32,32),Image.Resampling.LANCZOS);im=Image.new('RGBA',(32,32),'#efc58d');im.putalpha(mask);x=slot*32;slot+=1;atlas.alpha_composite(im,(x,0))
 for pal in ['0F17212A','0F2A0F0F']:rules.append(f'[{region}]<tile>{index},{e["pattern"]},{pal},{x},0,1,N')
for p in M['map_keys']:
 for pal in ['0F17212A','0F2A0F0F']:rules.append(f'[{region}]<tile>0,{p},{pal},0,0,1,N')
# Six captured close banked layouts were absent from earlier missions.
# Complete relative signatures precede per-cell fallbacks for clipped edges.
planes=[];fallback=[]
for li,e in enumerate(json.loads((S/'mission4_aircraft_mappings.json').read_text())):
 art=Image.open(S/('mission2_reused_front.png' if e['id'] in [38,40,42] else 'mission2_reused_rear.png')).convert('RGBA')
 art=art.crop(art.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())
 angle={38:-38,40:-48,42:-20,129:38,130:10,131:55}[e['id']]
 art=art.rotate(angle,Image.Resampling.BICUBIC,expand=True)
 w,h=e['size'];x0,y0,x1,y1=e['bbox'];im=Image.new('RGBA',(w*4,h*4));im.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 for ti,t in enumerate(e['tiles']):
  piece=im.crop((t['x']*4,t['y']*4,t['x']*4+32,t['y']*4+32))
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  ax,ay=slot%32*32,slot//32*32;slot+=1;assert slot<=128;atlas.alpha_composite(piece,(ax,ay))
  for pi,pal in enumerate(['FF381A0F','FF10000F']):
   gates=[]
   for ai,anchor in enumerate([e['tiles'][0],e['tiles'][-1]]):
    name=f'm4Plane{li}_{ti}_{pi}_{ai}';gates.append(name);conditions.append(f'<condition>{name},spriteNearby,{anchor["x"]-t["x"]},{anchor["y"]-t["y"]},{anchor["pattern"]},{pal},N')
   gate=flight+'&enemyWorld'+('&hmirror' if t['attr']&64 else '&!hmirror')+('&vmirror' if t['attr']&128 else '&!vmirror')
   tail=f'<tile>{index},{t["pattern"]},{pal},{ax},{ay},1,N'
   planes.append('['+gate+'&'+'&'.join(gates)+']'+tail);fallback.append('['+gate+']'+tail)
rules=planes+rules+fallback
# Newly recorded far silhouette and close boat view use the approved vessel.
boat=Image.open(S/'mission2_boat_master.png').convert('RGBA')
boat=boat.crop(boat.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())
for e in M['new_boat_layouts']:
 w,h=e['size'];x0,y0,x1,y1=e['bbox'];im=Image.new('RGBA',(w*4,h*4))
 im.alpha_composite(boat.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 for t in e['tiles']:
  piece=im.crop((t['x']*4,t['y']*4,t['x']*4+32,t['y']*4+32));ax,ay=slot%32*32,slot//32*32;slot+=1
  atlas.alpha_composite(piece,(ax,ay))
  rules.insert(0,f'[{flight}&enemyWorld]<tile>{index},{t["pattern"]},FF10000F,{ax},{ay},1,N')
# Exact keys must preserve generic alternatives outside Mission 4.
oldkeys=set();defaults=defaultdict(list)
for l in lines:
 if '<tile>' not in l:continue
 v=l.split('<tile>')[1].split(',');oldkeys.add(tuple(v[1:3]))
 if v[6]=='Y':defaults[v[1]].append(l)
newkeys={tuple(l.split('<tile>')[1].split(',')[1:3]) for l in rules if '<tile>' in l}
for p,pal in sorted(newkeys-oldkeys):
 for l in defaults[p]:
  v=l.split('<tile>')[1].split(',');v[2]=pal;v[6]='N';rules.append(l.split('<tile>')[0]+'<tile>'+','.join(v))
# Remove duplicate copies without changing priority.
rules=list(dict.fromkeys(rules));backgrounds=list(dict.fromkeys(backgrounds))
save_png(atlas,P/'mission4_details.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1;lines[i:i]=['<img>mission4_details.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l);lines[i:i]=backgrounds+rules
lines[0]='# Top Gun HD v0.12.0 - Mission 4 night flight and ocean combat'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
(S/'mission4_build.json').write_text(json.dumps(dict(rules=len(rules),conditions=len(conditions),backgrounds=len(backgrounds),world_keys=len(M['world_keys'])),indent=2)+'\n')
print('Mission 4:',len(rules),'rules,',len(backgrounds),'backgrounds')
