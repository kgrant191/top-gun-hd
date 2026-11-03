"""Native-masked mission-one scenery and corrected cloud sprite family.

The existing CHR/palettes select materials and silhouettes. No game memory,
ROM, horizon geometry, sprite timing or audio is changed.
"""
from pathlib import Path
import json, re
from PIL import Image, ImageOps
import numpy as np
from pack_io import save_png

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'pack'; S=ROOT/'source'
M=json.loads((S/'environment_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines()
assert '<img>environment_clouds.png' not in lines, 'Environment stage already installed'
conditions=['<condition>environmentWorld,positionCheckY,<,128']
rules=[];images=[]

def add_image(name,im):
 index=sum(l.startswith('<img>') for l in lines)+len(images)
 save_png(im,P/name);images.append('<img>'+name);return index

def decode(pattern):
 a=np.frombuffer(bytes.fromhex(pattern),np.uint8)
 return np.unpackbits(a[:8,None],axis=1)+2*np.unpackbits(a[8:,None],axis=1)

# Cloud shapes 7–10 are distance sizes of native white clouds, not fireballs.
cloud=Image.open(S/'environment_cloud_master.png').convert('RGBA')
cloud=cloud.crop(cloud.getbbox())
def fitted(size):
 out=Image.new('RGBA',size);im=ImageOps.contain(cloud,size,Image.Resampling.LANCZOS)
 out.alpha_composite(im,((size[0]-im.width)//2,(size[1]-im.height)//2));return out
layouts={7:([(x,y,0) for x in [0,8,16] for y in [0,8,16]],(96,96)),
 8:([(0,0,192),(0,8,0),(8,0,0),(8,8,64)],(64,64)),
 9:([(0,0,0),(8,0,0)],(64,32))}
cloud_atlas=Image.new('RGBA',(512,512));slot=0;old_to_new={};contexts={}
source_rules=(S/'combat_effects_rules.txt').read_text().splitlines()
for line in source_rules:
 if '<tile>@IMAGE@' not in line:continue
 p=line.split('<tile>')[1].split(',');m=re.search(r'combat(7|8|9)_(\d+)_',line)
 if not m:continue
 li,ti=map(int,m.groups());key=(li,ti)
 if key not in contexts:
  coords,size=layouts[li];x,y,attr=coords[ti]
  im=fitted(size).crop((x*4,y*4,x*4+32,y*4+32))
  if attr&64:im=ImageOps.mirror(im)
  if attr&128:im=ImageOps.flip(im)
  xy=(slot%16*32,slot//16*32);slot+=1;cloud_atlas.paste(im,xy);contexts[key]=xy
 old_to_new[tuple(map(int,p[3:5]))]=contexts[key]
# Native single-tile cloud at the farthest distance.
single=(slot%16*32,slot//16*32);cloud_atlas.paste(fitted((32,32)),single)
idx=add_image('environment_clouds.png',cloud_atlas)
cloud_keys=set(M['cloud_patterns'])
for line in source_rules:
 if '<tile>@IMAGE@' not in line:continue
 p=line.split('<tile>')[1].split(',')
 if p[1] not in cloud_keys:continue
 old=tuple(map(int,p[3:5]));xy=old_to_new.get(old,single)
 p[0]=str(idx);p[3:5]=map(str,xy)
 rules.append(line.split('<tile>')[0]+'<tile>'+','.join(p))

# Continuous material planes sit behind native silhouettes. The first fully
# water/gray tile at the left edge selects each plane's vertical crop once per
# frame. This avoids hundreds of position tests for every ocean pixel.
sky=Image.open(S/'environment_sky_master.png').convert('RGBA').resize((1024,512),Image.Resampling.LANCZOS)
plate=Image.new('RGBA',(1024,960));plate.paste(sky,(0,0));save_png(plate,P/'environment_sky.png')
water=Image.open(S/'environment_water_master.png').convert('RGBA').resize((1024,512),Image.Resampling.LANCZOS)
runway=Image.open(S/'environment_runway_master.png').convert('RGBA').resize((1024,512),Image.Resampling.LANCZOS)
# Atmospheric haze at the waterline makes distant ripples less prominent.
a=np.array(water).astype(float);fade=np.exp(-np.arange(512)/32)[:,None,None]*0.75
fog=np.array([115,153,174,255]);a=a*(1-fade)+fog*fade;water=Image.fromarray(np.uint8(a))
cloudtop=Image.new('RGBA',(1024,512),(227,239,247,255))
cloudtop.alpha_composite(cloud.resize((1024,600),Image.Resampling.LANCZOS),(0,-80))
cloudtop=Image.blend(Image.new('RGBA',(1024,512),(230,240,248,255)),cloudtop,0.65)
for name,material in [('ocean',water),('cloudtop',cloudtop),('runway',runway)]:
 im=Image.new('RGBA',(1024,1024));im.paste(material,(0,512));save_png(im,P/('environment_'+name+'_plane.png'))
shield=Image.new('RGBA',(1024,960));shield.paste((0,0,0,255),(0,512,1024,960));save_png(shield,P/'environment_lower_mask.png')
backgrounds=['[cockpit&cockpitBorder]<background>environment_sky.png,1,0,0,6',
 '[cockpit&cockpitBorder]<background>environment_lower_mask.png,1,0,0,9']
solid={}
for items in M['backgrounds'].values():
 for entry in items:
  a=decode(entry['pattern'])
  if len(set(a.ravel().tolist()))==1:solid[int(a[0,0])]=entry['pattern']
for y in range(128):
 for suffix,palette,material in [('Sea','0F301131','ocean'),('Cloud','0F203031','cloudtop'),('Sea2','0F001131','ocean')]:
  name=f'env{suffix}{y}'
  conditions.append(f'<condition>{name},tileAtPosition,8,{y},{solid[2]},{palette},N')
  backgrounds.append(f'[cockpit&cockpitBorder&{name}]<background>environment_{material}_plane.png,1,0,0,7,0,{128-y}')
 name=f'envDeck{y}'
 conditions.append(f'<condition>{name},tileAtPosition,8,{y},{solid[1]},0F001131,N')
 backgrounds.append(f'[cockpit&cockpitBorder&{name}]<background>environment_runway_plane.png,1,0,0,8,0,{128-y}')

# Masks preserve partial horizon tiles, moving dashes and carrier silhouettes.
# Only edge/detail tiles need artwork; full fields expose the selected plane.
atlas=Image.new('RGBA',(1024,1024));entries=[];newkeys=set();counts={};slot=0
for bank,pal,mode in [(1,'0F301131','ocean'),(1,'0F203031','cloudtop'),(2,'0F001131','runway')]:
 patterns={e['pattern']:e for e in M['backgrounds'][str(bank)] if not (e.get('carrier') and mode=='cloudtop')}
 count=0
 for pattern,entry in patterns.items():
  a=decode(pattern);newkeys.add((pattern,pal));carrier=entry.get('carrier',False)
  colors=set(a.ravel().tolist())
  # Fully solid native fields are all part of the landscape planes.
  if len(colors)==1 and next(iter(colors)) in [1,2,3] and not carrier:
   rules.append(f'[cockpit&cockpitBorder&environmentWorld]<tile>0,{pattern},{pal},0,0,1,N');continue
  im=Image.new('RGBA',(32,32))
  masks={v:Image.fromarray(np.uint8(a==v)*255).resize((32,32),Image.Resampling.NEAREST) for v in range(4)}
  if carrier:
   # Keep the native carrier's outline/paint. Water is transparent to the
   # ocean plane, removing blue squares around all captured distance banks.
   for value,color in [(0,(0,0,0,255)),(1,((100,100,100,255) if bank==2 else (254,254,254,255))),(3,(192,224,255,255))]:
    im.paste(color,(0,0,32,32),masks[value])
  else:
   if bank==1:
    im.paste((228,239,247,255),(0,0,32,32),masks[1])
    # Partial tiles immediately above the first solid field bridge the
    # native dithered water/cloud boundary with a quiet atmospheric color.
    if 3 in colors:
     im.paste((228,239,247,255) if mode=='cloudtop' else (100,140,163,255),(0,0,32,32),masks[2])
   else:
    im.paste((222,220,201,255),(0,0,32,32),masks[0])
    for ry in np.where(np.all(a==0,axis=1))[0]:
     im.paste((29,44,53,255),(0,int(ry)*4,32,int(ry+1)*4))
    # A partial runway edge precedes the first completely gray tile.
    if 3 in colors or 2 in colors or np.any(np.all(a==0,axis=1)):
     im.paste((57,65,69,255),(0,0,32,32),masks[1])
  if not im.getbbox():
   rules.append(f'[cockpit&cockpitBorder&environmentWorld]<tile>0,{pattern},{pal},0,0,1,N');continue
  x,y=slot%32*32,slot//32*32;atlas.paste(im,(x,y));slot+=1;count+=1;entries.append((pattern,pal,x,y))
 counts[mode]={'patterns':len(patterns),'detail_tiles':count}
assert slot<=1024
idx=add_image('environment_details.png',atlas)
for pattern,pal,x,y in entries:rules.append(f'[cockpit&cockpitBorder&environmentWorld]<tile>{idx},{pattern},{pal},{x},{y},1,N')

# New exact keys suppress Mesen's default lookup even if their conditions fail.
# Preserve every existing alternative for those keys outside the world viewport.
old_exact=set()
for line in lines:
 if '<tile>' in line:
  p=line.split('<tile>')[1].split(',');old_exact.add((p[1],p[2]))
fallbacks=[]
for pattern,pal in sorted(newkeys-old_exact):
 for line in lines:
  if '<tile>' not in line:continue
  p=line.split('<tile>')[1].split(',')
  if p[1]==pattern and p[6]=='Y':
   p[2]=pal;p[6]='N';fallbacks.append(line.split('<tile>')[0]+'<tile>'+','.join(p))
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1
lines[i:i]=images+conditions
idx=next(i for i,l in enumerate(lines) if '<tile>' in l)
lines[idx:idx]=backgrounds+rules+fallbacks
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
(S/'environment_build.json').write_text(json.dumps({'version':'0.5.0','materials':counts,'cloud_patterns':len(cloud_keys),'new_rules':len(rules),'preserved_default_alternatives':len(fallbacks),'field_rendering':'Per-frame native tile anchors select continuous material planes'},indent=2)+'\n')
print('Built environment:',counts,'cloud family',len(cloud_keys))
