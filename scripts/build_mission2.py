"""Mission 2 native palette, naval targets, briefing and refuelling coverage.

Only read-only Mesen HD-pack predicates are emitted. Existing artwork stays
byte-identical; artwork geometry follows captured native tile/nametable data.
"""
from pathlib import Path
import json,re
from collections import defaultdict
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from pack_io import save_png
R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
M=json.loads((S/'mission2_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines()
assert not any('mission2_sprites.png' in l for l in lines),'Rebuild the base before this stage'
original=list(lines);conditions=[];rules=[];backgrounds=[];images=[]
idx=sum(l.startswith('<img>') for l in lines)
atlas=Image.new('RGBA',(1024,1024));slot=0
FONT=str(S/'fonts/DejaVuSansMono-Bold.ttf')
conditions += ['<condition>missionTwo,memoryCheckConstant,0030,==,02',
 '<condition>refuelRoute,memoryCheckConstant,002E,==,04',
 '<condition>mission2Flight,memoryCheckConstant,0018,==,07',
 '<condition>mission2BeforeLanding,memoryCheckConstant,002E,<,05',
 '<condition>refuelActive,memoryCheckConstant,009F,>=,01',
 '<condition>refuelControl,memoryCheckConstant,009F,>=,02',
 '<condition>refuelHudX0,positionCheckX,>=,80','<condition>refuelHudX1,positionCheckX,<,176',
 '<condition>refuelHudY0,positionCheckY,>=,144','<condition>refuelHudY1,positionCheckY,<,208',
]
scene='cockpit&cockpitBorder';world=scene+'&environmentWorld';refuel=scene+'&refuelRoute&refuelActive'
# Landing and refuelling share main mode 7 and $009F state numbers. Route 4
# selects refuelling. Restore normal cockpit layers there and exclude only
# the landing-specific clauses, including the black transition overlays.
rewritten=[]
for l in lines:
 if l.startswith('['):
  c,tail=l[1:].split(']',1);tokens=c.split('&')
  if '!landingMode' in tokens:
   rewritten.append('['+'&'.join('refuelRoute' if t=='!landingMode' else t for t in tokens)+']'+tail)
  if 'landingMode' in tokens:tokens.append('!refuelRoute')
  l='['+'&'.join(tokens)+']'+tail
 rewritten.append(l)
lines=rewritten
# Mission 2 uses sky color $21 instead of $31. Duplicate the exact keys and
# palette-dependent anchors; original rules and PNGs remain unchanged.
palettes={'0F301131':'0F301121','0F001131':'0F001121','0F2A0A31':'0F2A0A21'}
cond_alias={}
for l in lines:
 if l.startswith('<condition>') and any(k in l for k in palettes):
  name=l.split(',')[0][11:];cond_alias[name]=name+'M2';q=l.replace('<condition>'+name+',','<condition>'+name+'M2,')
  for a,b in palettes.items():q=q.replace(a,b)
  conditions.append(q)
for l in lines:
 if not l.startswith('['):continue
 c,tail=l[1:].split(']',1);tokens=c.split('&');changed=any(t.lstrip('!') in cond_alias for t in tokens)
 nc='&'.join(('!' if t.startswith('!') else '')+cond_alias.get(t.lstrip('!'),t.lstrip('!')) for t in tokens)
 nt=tail
 for a,b in palettes.items():nt=nt.replace(a,b)
 if changed or nt!=tail:
  # Only the alternate palette copies are newly scoped to Mission 2.
  q='['+nc+'&missionTwo]'+nt
  (backgrounds if '<background>' in q else rules).append(q)
# Reuse enemy/effect art under the Mission 2 aircraft palette.
for l in lines:
 if l.startswith('[') and '<tile>' in l and ',FF2A100F,' in l and ('enemyWorld' in l or 'combat' in l):
  q=l.replace(',FF2A100F,',',FF381A0F,');q=q.replace(']<tile>','&missionTwo]<tile>');rules.append(q)

def dec(p):
 b=np.frombuffer(bytes.fromhex(p),np.uint8);return np.unpackbits(b[:8,None],axis=1)+2*np.unpackbits(b[8:,None],axis=1)
def trimmed(name):
 im=Image.open(S/name).convert('RGBA');box=im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox();return im.crop(box)
def add(im,pattern,pal,cond,mirror=None):
 global slot
 if mirror is not None:cond+=('&hmirror' if mirror&64 else '&!hmirror')+('&vmirror' if mirror&128 else '&!vmirror')
 x,y=slot%32*32,slot//32*32;slot+=1;assert slot<=1024
 atlas.alpha_composite(im,(x,y));rules.append(f'[{cond}]<tile>{idx},{pattern},{pal},{x},{y},1,N')
def blank(p,pal,cond):rules.append(f'[{cond}]<tile>0,{p},{pal},0,0,1,N')
def save(name,im):save_png(im,P/name);return name
# Native sea/sky edge patterns include additional banked rows in Mission 2.
for p in M['ocean_keys']:
 blank(p,'0F301121',world+'&missionTwo&mission2Flight&mission2BeforeLanding')
# Mission 2 menus reuse the approved panel, weapon diagrams and native text.
conditions += [f'<condition>menuMissionTwo,tileAtPosition,80,32,{M["mission_two_pattern"]},00000000,Y',f'<condition>menuMapTwo,tileAtPosition,80,112,{M["map_anchor"]},00000000,Y']
menu='menuMissionM&menuMissionN&menuMissionTwo&menuHeaderPresent';mapcond=menu+'&menuMapTwo'
for l in original:
 if l.startswith('[') and 'menuMissionOne' in l:
  if 'menuMapAnchor' in l:continue
  q=l.replace('menuMissionOne','menuMissionTwo');(backgrounds if '<background>' in q else rules).append(q)
# Smooth contour tracing retains the actual Mission 2 geography and islands.
def contours(mask):
 h,w=mask.shape;edges=defaultdict(list)
 for y,x in zip(*np.where(mask)):
  if y==0 or not mask[y-1,x]:edges[(x,y)].append((x+1,y))
  if x==w-1 or not mask[y,x+1]:edges[(x+1,y)].append((x+1,y+1))
  if y==h-1 or not mask[y+1,x]:edges[(x+1,y+1)].append((x,y+1))
  if x==0 or not mask[y,x-1]:edges[(x,y+1)].append((x,y))
 while edges:
  start=next(iter(edges));p=start;poly=[p]
  while True:
   q=edges[p].pop()
   if not edges[p]:del edges[p]
   poly.append(q);p=q
   if p==start:break
  yield poly
def simplify(points,eps=1.15):
 if len(points)<3:return points
 a,b=np.array(points[0],float),np.array(points[-1],float);p=np.array(points,float);v=b-a
 if np.dot(v,v)==0:dist=np.linalg.norm(p-a,axis=1)
 else:
  t=np.clip((p-a)@v/np.dot(v,v),0,1);dist=np.linalg.norm(p-(a+t[:,None]*v),axis=1)
 j=int(np.argmax(dist))
 if dist[j]<=eps:return [points[0],points[-1]]
 return simplify(points[:j+1],eps)[:-1]+simplify(points[j:],eps)
def area(poly):return sum(x0*y1-x1*y0 for (x0,y0),(x1,y1) in zip(poly,poly[1:]+poly[:1]))/2
mapimage=Image.new('RGBA',(1024,960));d=ImageDraw.Draw(mapimage);d.rounded_rectangle((144,364,880,916),radius=12,fill='#04111b',outline='#608b91',width=2)
layer=Image.new('RGBA',(704,512),'#092332');d=ImageDraw.Draw(layer);polys=[simplify(p) for p in contours(np.array(M['map_pixels'])==0x17)]
for poly in sorted(polys,key=lambda p:abs(area(p)),reverse=True):
 d.polygon([(int(x*4),int(y*4)) for x,y in poly],fill='#21494b' if area(poly)>0 else '#092332')
for poly in polys:d.line([(int(x*4),int(y*4)) for x,y in poly],fill='#83aaa3',width=2,joint='curve')
for x in range(0,704,64):d.line((x,0,x,512),fill='#31505b70',width=1)
for y in range(0,512,64):d.line((0,y,704,y),fill='#31505b70',width=1)
mapimage.alpha_composite(layer,(160,384));save('mission2_map.png',mapimage)
backgrounds.append(f'[{mapcond}]<background>mission2_map.png,1,0,0,11')
mapregion=mapcond+'&menuMapX0&menuMapX1&menuMapY0&menuMapY1'
for e in M['map_markers']:
 mask=Image.fromarray(np.uint8(e['mask'])*255).resize((32,32),Image.Resampling.LANCZOS);im=Image.new('RGBA',(32,32),'#edc78b');im.putalpha(mask)
 for pal in ['0F17212A','0F2A0F0F']:add(im,e['pattern'],pal,mapregion)
for p in M['map_keys']:
 for pal in ['0F17212A','0F2A0F0F']:blank(p,pal,mapregion)
# Naval targets and additional aircraft use existing native sprite coordinates.
masters={k:trimmed(f'mission2_{k}_master.png') for k in ['boat','submarine','tanker','boom']}
# The game supplies its own moving boom; the tanker plate contains the body.
masters['tanker']=masters['tanker'].crop((0,0,masters['tanker'].width,round(masters['tanker'].height*.89)))
front=trimmed('mission2_reused_front.png');rear=trimmed('mission2_reused_rear.png')
angles={0:0,1:-20,2:25,4:20,6:0,11:0,13:30,14:-25,18:0,19:0,20:25,21:0,22:25,24:-25,26:-25,27:-35,28:0,29:-25,32:25,33:0,59:0}
# Most common complete native layouts define shared pieces; partial objects
# at screen edges continue to use the same per-pattern image.
assigned=set()
for e in sorted(M['objects'],key=lambda e:e['count'],reverse=True):
 tiles=e['tiles'];w,h=e['size'];bbox=e['bbox'];x0,y0,x1,y1=bbox
 if e['kind']=='aircraft':
  art=front if e['id']<17 else rear
  art=art.rotate(angles.get(e['id'],0),Image.Resampling.BICUBIC,expand=True)
  # Native inversion changes both axes; the CHR attribute is handled per tile.
 else:art=masters[e['kind']]
 im=Image.new('RGBA',(w*4,h*4));im.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 for t in tiles:
  key=t['pattern']
  if key in assigned:continue
  assigned.add(key);x,y=t['x']*4,t['y']*4;piece=im.crop((x,y,x+32,y+32))
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  pals=['FF381A0F','FF38210F','FF10000F','FF162630','FF153630'] if e['kind']=='aircraft' else ['FF10000F']
  for pal in pals:add(piece,t['pattern'],pal,scene+'&missionTwo&enemyWorld&rearCombatPhase')
# Additional distant aircraft and compact native impact/projectile patterns.
for e in M['tiny_sprites']:
 a=dec(e['pattern']);ys,xs=np.where(a>0);im=Image.new('RGBA',(32,32))
 if len(xs):
  x0,y0,x1,y1=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)
  art=front if e['tile']==0xCA else trimmed('impact_burst_master.png')
  im.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
  pals=['FF381A0F','FF38210F','FF162630','FF153630'] if e['a']&3==2 else ['FF10000F']
  for pal in pals:add(im,e['pattern'],pal,scene+'&missionTwo&enemyWorld&rearCombatPhase')
# One tanker plate follows the native nametable scroll in both axes.
x0,y0,x1,y1=M['tanker']['bbox'];plate=Image.new('RGBA',(2048,1536));art=masters['tanker'].resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS)
for dx in [0,1024]:plate.alpha_composite(art,(x0*4+dx,y0*4))
save('mission2_tanker.png',plate);backgrounds.insert(0,f'[{refuel}]<background>mission2_tanker.png,1,1,1,31')
# Refuelling has a different CHR bank and gray tanker palette. Remove only its
# upper background, leaving the scrolled art and the unchanged sky behind it.
for p in M['tanker_mask_keys']:
 blank(p,'0F300021',refuel+'&environmentWorld')
# Boom growth and steering stay native. Shared shaft patterns use one stable
# crop, while the game selects the progressively larger fin/nozzle patterns.
assigned=set()
# The connecting tube is reused at several growth stages and overlaps the
# nozzle. Fit an invariant straight metal strip to its original opaque mask.
shaft_ids={0xC5,0xD5,0xCE,0xCF,0xE9,0xE1}
for e in M['boom']:
 for t in e['tiles']:
  if t['tile'] not in shaft_ids:continue
  key=(t['pattern'],t['attr']&192)
  if key in assigned:continue
  assigned.add(key);a=dec(t['pattern']);ys,xs=np.where(a>0)
  if not len(xs):continue
  x0,y0,x1,y1=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)
  art=masters['boom'];row=round(art.height*.22);xs0=np.where(np.array(art.getchannel('A'))[row]>=128)[0];mid=(int(xs0.min())+int(xs0.max())+1)//2
  strip=art.crop((int(xs0.min()),row,mid,row+1))
  piece=Image.new('RGBA',(32,32));piece.alpha_composite(strip.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
  mask=Image.fromarray(np.uint8(a>0)*255).resize((32,32),Image.Resampling.LANCZOS);piece.putalpha(mask)
  add(piece,t['pattern'],'FF10000F',refuel+'&enemyWorld',t['attr'])
for e in sorted(M['boom'],key=lambda e:e['count'],reverse=True):
 # The trailing 2/4/8 OAM entries are the independently extending shaft.
 ts=e['tiles'];main_count={8:6,10:8,12:10,22:18,30:26,44:36}.get(len(ts),len(ts));ts=ts[:main_count]
 w=max(t['x'] for t in ts)+8;h=max(t['y'] for t in ts)+8;native=Image.new('L',(w,h))
 for t in ts:
  a=Image.fromarray(np.uint8(dec(t['pattern'])>0)*255)
  if t['attr']&64:a=ImageOps.mirror(a)
  if t['attr']&128:a=ImageOps.flip(a)
  native.paste(a,(t['x'],t['y']),a)
 box=native.getbbox()
 if not box:continue
 x0,y0,x1,y1=box;im=Image.new('RGBA',(w*4,h*4));im.alpha_composite(masters['boom'].resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
 for t in ts:
  key=(t['pattern'],t['attr']&192)
  if key in assigned:continue
  assigned.add(key);x,y=t['x']*4,t['y']*4;piece=im.crop((x,y,x+32,y+32))
  if t['attr']&64:piece=ImageOps.mirror(piece)
  if t['attr']&128:piece=ImageOps.flip(piece)
  add(piece,t['pattern'],'FF10000F',refuel+'&enemyWorld',t['attr'])
# Native control labels and moving coupling schematic over a clean monitor.
hudcond=refuel+'&refuelControl&refuelHudX0&refuelHudX1&refuelHudY0&refuelHudY1'
monitor=Image.new('RGBA',(1024,960));d=ImageDraw.Draw(monitor);d.rectangle((320,576,703,831),fill='#071b22')
for yy in range(608,824,32):d.line((324,yy,331,yy),fill='#486e70',width=2);d.line((692,yy,699,yy),fill='#486e70',width=2)
save('mission2_refuel_monitor.png',monitor);backgrounds.insert(0,f'[{refuel}&refuelControl]<background>mission2_refuel_monitor.png,1,0,0,12')
letters={0x10+i:chr(65+i) for i in range(26) if i!=14};letters.update({1:'O',2:'I',6:'S',0x18:':',0x0b:"'",0x0c:'.',0x0e:'!',0x3e:'-'})
for p,t in M['hud'].items():
 im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
 if t in letters:d.text((16,16),letters[t],font=ImageFont.truetype(FONT,24),anchor='mm',fill='#b8e9d2')
 else:
  mask=Image.fromarray(np.uint8(dec(p)==1)*255).resize((32,32),Image.Resampling.LANCZOS);im=Image.new('RGBA',(32,32),'#9ce0ca');im.putalpha(mask)
 add(im,p,'0F2A0A21',hudcond)
for e in M['hud_sprites']:
 mask=Image.fromarray(np.uint8(dec(e['pattern'])==1)*255).resize((32,32),Image.Resampling.LANCZOS)
 im=Image.new('RGBA',(32,32),'#b9eed7');im.putalpha(mask)
 add(im,e['pattern'],e['palette'],hudcond)
# The native tanker's sky-mask sprites must reveal the painted sky as well.
blank('0000000000000000FFFFFFFFFFFFFFFF','FF38210F',refuel+'&enemyWorld')
# New exact keys suppress defaults even when their predicates fail. Carry all
# prior default alternatives forward for each new key to preserve other scenes.
oldkeys=set();defaults=defaultdict(list)
for l in lines:
 if '<tile>' not in l:continue
 p=l.split('<tile>')[1].split(',');oldkeys.add((p[1],p[2]))
 if p[6]=='Y':defaults[p[1]].append(l)
newkeys=set()
for l in rules:
 if '<tile>' in l:
  p=l.split('<tile>')[1].split(',');newkeys.add((p[1],p[2]))
fallback=[]
for p,pal in sorted(newkeys-oldkeys):
 for l in defaults[p]:
  a=l.split('<tile>')[1].split(',');a[2]=pal;a[6]='N';fallback.append(l.split('<tile>')[0]+'<tile>'+','.join(a))
save('mission2_sprites.png',atlas)
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1;lines[i:i]=['<img>mission2_sprites.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l);lines[i:i]=backgrounds+rules+fallback
lines[0]='# Top Gun HD v0.8.0 - Mission 2 naval combat and refuelling'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
(S/'mission2_build.json').write_text(json.dumps({'sprite_cells':slot,'conditions':len(conditions),'rules':len(rules),'backgrounds':len(backgrounds),'new_exact_keys':len(newkeys-oldkeys)},indent=2)+'\n')
print('Mission 2:',slot,'atlas cells,',len(rules),'rules,',len(backgrounds),'background clauses')
