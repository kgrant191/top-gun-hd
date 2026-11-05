"""Register adult crew and a fixed pilot body; distinguish the bonus numeral."""
from pathlib import Path
from collections import defaultdict
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pack_io import save_png
R=Path(__file__).resolve().parents[1];S=R/'source';P=R/'pack'
lines=(P/'hires.txt').read_text().splitlines();assert '<img>ending_polish.png' not in lines
index=sum(l.startswith('<img>') for l in lines)
# Register every adult by the same source helmet/boot geometry. Arm reach
# changes the full bounding box, so never stretch a pose to a requested box.
fig=Image.open(S/'ending_figures_master.png').convert('RGBA')
base=Image.open(S/'ending_carrier_closed_master.png').convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
crew=[dict(crop=[0,0,320,680],head_x=150,x=112,feet=896),
      dict(crop=[320,0,620,680],head_x=155,x=440,feet=896),
      dict(crop=[620,0,980,680],head_x=150,x=664,feet=896),
      dict(crop=[0,0,320,680],head_x=150,x=920,feet=912)]
scale=.31
for e in crew:
 crop=fig.crop(e['crop']);art=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
 base.alpha_composite(art,(round(e['x']-e['head_x']*scale),round(e['feet']-630*scale)))
# Both front-pilot frames share one canvas, scale and seat anchor. Only the
# far arm is replaced; helmet, head, torso, near arm and seat are identical.
up=fig.crop((1300,170,1640,590));edit=Image.open(S/'ending_pilot_arm_down_master.png').convert('RGBA').resize(up.size,Image.Resampling.LANCZOS)
mask=Image.new('L',up.size,0)
ImageDraw.Draw(mask).polygon([(210,0),(339,0),(339,326),(257,326),(219,304),(180,276),(164,245),(199,212),(212,180)],fill=255)
# A narrow feather avoids a cut seam while retaining fixed pixels elsewhere.
mask=mask.filter(ImageFilter.GaussianBlur(1))
down=up.copy();down.paste(edit,(0,0),mask)
# Retain the native foreground seat anchor for the shared pilot canvas.
pilot_scale=.145;size=(round(up.width*pilot_scale),round(up.height*pilot_scale))
poses=[down.resize(size,Image.Resampling.LANCZOS),up.resize(size,Image.Resampling.LANCZOS)]
rear=down.resize((round(up.width*.11),round(up.height*.11)),Image.Resampling.LANCZOS)
opened=Image.open(S/'ending_carrier_open_master.png').convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
half=Image.open(S/'ending_carrier_half_master.png').convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
box=(600,316,880,484);canopy_mask=Image.new('L',(280,168),0);ImageDraw.Draw(canopy_mask).rectangle((8,8,271,159),fill=255);canopy_mask=canopy_mask.filter(ImageFilter.GaussianBlur(4))
for phase in range(5):
 im=base.copy()
 if phase:
  im.paste((half if phase==1 else opened).crop(box),box,canopy_mask)
  im.alpha_composite(rear,(675,411));im.alpha_composite(poses[int(phase==3)],(746,395))
 save_png(im,P/f'ending_carrier_{phase}.png')
# The ROM bonus command writes BONUS at $2A8D and 10000 PTS at $2ACB.
# Tile 02 shares its pattern with I; restrict numeral 1 to this exact phrase.
font=S/'fonts/DejaVuSansMono-Bold.ttf';atlas=Image.new('RGBA',(32,32));ImageDraw.Draw(atlas).text((16,15),'1',font=ImageFont.truetype(str(font),23),anchor='mm',fill='#a7eac6');save_png(atlas,P/'ending_polish.png')
chrdata=(R/'captures/baseline/03240.chr').read_bytes();key=chrdata[2*16:3*16].hex().upper()
conditions=[];gates=[]
for i,value in enumerate([2,1,1,1,1,0x0f,0x1f,0x23,0x22]):
 name=f'bonus10000_{i}';gates.append(name);conditions.append(f'<condition>{name},ppuMemoryCheckConstant,{0x2acb+i:04X},==,{value:02X}')
for axis,value in [('X',88),('Y',176)]:
 name=f'bonusDigit{axis}';gates.append(name);conditions.append(f'<condition>{name},originPositionCheck{axis},==,{value}')
basegate='cockpit&cockpitBorder&'+'&'.join(gates)
# Cover every existing palette family without changing word forms elsewhere.
oldkeys=set();defaults=defaultdict(list);palettes=set()
for line in lines:
 if '<tile>' not in line:continue
 v=line.split('<tile>')[1].split(',');oldkeys.add(tuple(v[1:3]))
 if v[6]=='Y':defaults[v[1]].append(line)
 if v[1]==key and not v[2].startswith('FF'):palettes.add(v[2])
rules=[f'[{basegate}]<tile>{index},{key},{pal},0,0,1,N' for pal in sorted(palettes)]
for pal in sorted(palettes):
 if (key,pal) not in oldkeys:
  for line in defaults[key]:
   v=line.split('<tile>')[1].split(',');v[2]=pal;v[6]='N';rules.append(line.split('<tile>')[0]+'<tile>'+','.join(v))
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1;lines[i:i]=['<img>ending_polish.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l);lines[i:i]=rules
lines[0]='# Top Gun HD v0.15.1 - bonus numeral and registered crew/pilot'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
report=dict(crew_scale=scale,crew_helmet_to_boot_height=(630-130)*scale,crew_registration=crew,pilot_scale=pilot_scale,pilot_canvas=list(size),pilot_anchor=[746,395],bonus_address='2ACB',bonus_text='10000 PTS.',bonus_pattern=key,bonus_palettes=sorted(palettes),changed_existing_pngs=[f'ending_carrier_{i}.png' for i in range(5)])
(S/'ending_polish_build.json').write_text(json.dumps(report,indent=2)+'\n');print('Ending polish:',report)
