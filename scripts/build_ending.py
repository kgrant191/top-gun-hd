"""Close shuttle views and recorded award/carrier endings; read-only HD art."""
from pathlib import Path
from collections import defaultdict
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
from pack_io import save_png
R=Path(__file__).resolve().parents[1];S=R/'source';P=R/'pack'
M=json.loads((S/'ending_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines();assert '<img>ending_details.png' not in lines
index=sum(l.startswith('<img>') for l in lines)
conditions=[];rules=[];backgrounds=[];additions=[]
scene='cockpit&cockpitBorder&missionFour&mission2Flight&rearCombatPhase'
world=scene+'&environmentWorld'
font=str(S/'fonts/DejaVuSansMono-Bold.ttf')
def face(n):return ImageFont.truetype(font,n)
def trim(im):return im.crop(im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())
def cond(name,kind,*args):conditions.append('<condition>'+','.join(map(str,[name,kind,*args])));return name
def memory(name,address,value):return cond(name,'memoryCheckConstant',f'{address:04X}','==',f'{value:02X}')
def ppu(name,address,value):return cond(name,'ppuMemoryCheckConstant',f'{address:04X}','==',f'{value:02X}')
def bg(gate,name,priority=20,x=0,y=0,scroll=False):backgrounds.append(f'[{gate}]<background>{name},1,{int(scroll)},{int(scroll)},{priority},{x},{y}')
def label(im,x,y,text,size,fill='#ede1bf'):
 ImageDraw.Draw(im).text((x,y),text,font=face(size),anchor='mm',fill=fill)

# Larger native layouts cross into the second nametable. The final layout's
# upper tower is native sprites; its geometry is included in the same plate.
shuttle=trim(Image.open(S/'mission4_shuttle_master.png').convert('RGBA'))
plates={}
for e in M['boss_stages']:
 st=e['stage'];ox,oy=e['origin'];w,h=e['size'];plate=Image.new('RGBA',(2048,1536))
 art=shuttle.resize((w*4,h*4),Image.Resampling.LANCZOS)
 for dx in [0,1024]:plate.alpha_composite(art,(ox*4+dx,oy*4))
 fn=f'mission4_shuttle_{st:02}.png';save_png(plate,P/fn);plates[st]=fn
 gates=[ppu(f'endShuttle{st}_{i}',t['address'],t['tile']) for i,t in enumerate(e['tiles'])]
 bg(scene+'&bossBodyPresent&'+'&'.join(gates),fn,9,scroll=True)
# Signatures above remain ahead of fallbacks during multi-frame transfers.
for st,fn in plates.items():bg(scene+f'&bossBodyPresent&bossDistance{st}',fn,9,scroll=True)
for pattern in M['boss_background_keys']:
 for pal in ['0F00100F','0F301016']:
  rules.append(f'[{world}&bossBodyPresent]<tile>0,{pattern},{pal},0,0,1,N')
for pattern in M['boss_upper_sprite_keys']:
 for pal in ['FF10000F','FF301016']:
  rules.append(f'[{scene}&enemyWorld&bossBodyPresent]<tile>0,{pattern},{pal},0,0,1,N')

# Overlapping native bursts can obscure their neighboring anchor pixels.
# These three edge patterns have unique atlas positions for their mirror pose.
# Keep the same approved explosion cells while the Mission 4 hull is hit.
for key,mirror,x,y in [
 ('E13C1C7F87637F181F03030000000007','hmirror&vmirror',352,32),
 ('E13C1C7F87637F181F03030000000007','!hmirror&!vmirror',384,32),
 ('7C8EF053DF1F1E04FFFF0F0C00000000','!hmirror&!vmirror',32,64)]:
 rules.append(f'[cockpit&cockpitBorder&enemyWorld&missionFour&hullImpact&bossBodyPresent&{mirror}]<tile>9,{key},FF162630,{x},{y},1,N')

# Scene signatures honor the game's blank setup and outgoing transfer frames.
for n in [8,9,10,11,4]:memory(f'endMode{n}',0x18,n)
ppu('endAwardVisible',0x212a,0x12)
ppu('endGameOverVisible',0x216b,0x16)
ppu('endSuccessVisible',0x2125,0x1c)
ppu('endCarrierVisible',0x2288,0x8a)
award='endMode9&endAwardVisible'
gameovers=['endMode8&endGameOverVisible','endMode9&endGameOverVisible']
success='endMode10&missionFour&endSuccessVisible'
carrier=['endMode11&endCarrierVisible','endMode4&endCarrierVisible']

awardbase=Image.open(S/'ending_award_master.png').convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
awardim=awardbase.copy();label(awardim,512,312,'TOP GUN',52);label(awardim,512,370,'CONGRATULATIONS',31,'#e4b969')
paragraph=['LIEUTENANT, YOU HAVE SAVED YOUR COUNTRY','WITH HONOR & COURAGE.','YOU ARE ONE OF THE ELITE NOW —','THE BEST OF THE BEST.','WE ARE PROUD TO BESTOW UPON YOU','THE DESIGNATION OF TOP GUN.']
for i,t in enumerate(paragraph):label(awardim,512,440+i*42,t,26)
label(awardim,512,760,'HIGH SCORE',22,'#d4b279');label(awardim,512,895,'KONAMI',15,'#9f9277')
save_png(awardim,P/'ending_award.png');bg(award,'ending_award.png')
for name,title,gates in [('gameover','GAME OVER',gameovers),('success','MISSION ACCOMPLISHED',[success])]:
 im=awardbase.copy();label(im,512,312,'TOP GUN',52);label(im,512,380,title,30,'#e4b969')
 d=ImageDraw.Draw(im);d.rounded_rectangle((208,438,816,594),radius=12,fill='#07151d',outline='#6b674e',width=2)
 label(im,345,494,'SCORE',25);label(im,345,558,'HI-SCORE',25)
 if name=='success':label(im,432,654,'PLAYER REMAIN:',25)
 save_png(im,P/f'ending_{name}.png')
 for gate in gates:bg(gate,f'ending_{name}.png')

# Native nametable selects every digit. Background offsets crop from the
# source, so put the shared glyph at (192,200) and crop toward its position.
for digit in range(10):
 im=Image.new('RGBA',(800,848));label(im,784,824,str(digit),32,'#eae2c8');save_png(im,P/f'ending_digit_{digit}.png')
def digits(prefix,gates,address,count,x,y,priority):
 for i in range(count):
  for n in range(10):
   gate=ppu(f'{prefix}{i}_{n}',address+i,0x30+n)
   for base in gates:bg(base+'&'+gate,f'ending_digit_{n}.png',priority+i,192-(x+i*8),200-y)
digits('endAwardScore',[award],0x2262,7,100,194,21)
digits('endOverScore',gameovers,0x21f1,7,136,118,21)
digits('endOverBest',gameovers,0x2231,7,136,134,28)
digits('endSuccessScore',[success],0x21f1,7,136,118,21)
digits('endSuccessBest',[success],0x2231,7,136,134,28)
digits('endSuccessLives',[success],0x2297,1,184,158,35)
for sid,gates in [('8',gameovers),('9',[award]),('10',[success])]:
 for pattern,pal in M['card_sprite_keys'][sid]:
  for gate in gates:rules.append(f'[{gate}]<tile>0,{pattern},{pal},0,0,1,N')

# Keep one registered carrier/aircraft body. Only the generated canopy crop
# changes, under the five observed native sprite-layout states.
base=Image.open(S/'ending_carrier_closed_master.png').convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
opened=Image.open(S/'ending_carrier_open_master.png').convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
half=Image.open(S/'ending_carrier_half_master.png').convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
box=(600,316,880,484);mask=Image.new('L',(box[2]-box[0],box[3]-box[1]),0);ImageDraw.Draw(mask).rectangle((8,8,mask.width-9,mask.height-9),fill=255);mask=mask.filter(ImageFilter.GaussianBlur(4))
fig=Image.open(S/'ending_figures_master.png').convert('RGBA')
crops=[(0,0,320,680),(320,0,620,680),(620,0,980,680),(980,190,1300,590),(1300,170,1640,590),(1640,60,1970,590)]
figures=[trim(fig.crop(b)) for b in crops]
# The native deck figures are static background poses, not a new timer.
for i,(x,y,w,h) in enumerate([(28,180,25,44),(110,188,20,36),(166,178,27,46),(230,200,18,31)]):
 art=figures[i%3].resize((w*4,h*4),Image.Resampling.LANCZOS);base.alpha_composite(art,(x*4-w*2,y*4))
for phase,e in enumerate(M['canopy_phases']):
 im=base.copy()
 if phase:
  src=half if phase==1 else opened;im.paste(src.crop(box),box,mask)
  # Rear seat remains seated; front pilot follows native rise/wave poses.
  pilot=figures[3].resize((36,48),Image.Resampling.LANCZOS);im.alpha_composite(pilot,(680,408))
  front=figures[4 if phase==3 else 3];height=68 if phase==3 else 48
  im.alpha_composite(front.resize((44,height),Image.Resampling.LANCZOS),(748,456-height))
 fn=f'ending_carrier_{phase}.png';save_png(im,P/fn)
 # All sprite anchors are stable while the native canopy/arm pose is shown.
 anchors=e['tiles']
 chosen=anchors
 assert chosen
 gates=[cond(f'endCanopy{phase}_{j}','spriteAtPosition',t['x'],t['y'],t['pattern'],'FF10000F','N') for j,t in enumerate(chosen)]
 for c in carrier:bg(c+'&'+'&'.join(gates),fn)
# Two setup frames precede the first canopy sprite. Use the closed pose only
# after the native carrier graphic is present, then restore native timing.
for c in carrier:bg(c,'ending_carrier_0.png')
# Native effects retain their original lifetime, poses and movement.
flames=Image.open(S/'flames_sheet.png').convert('RGBA');fw,fh=flames.size
for j,e in enumerate(M['exhaust']):
 cell=flames.crop(((j%2)*fw//2,(j//2)*fh//2,(j%2+1)*fw//2,(j//2+1)*fh//2))
 layer=Image.new('RGBA',(1024,960));layer.alpha_composite(cell.resize((180,88),Image.Resampling.LANCZOS),(-20,510))
 fn=f'ending_exhaust_{j}.png';save_png(layer,P/fn)
 gate=cond(f'endExhaust{j}','spriteAtPosition',e['x'],e['y'],e['pattern'],e['palette'],'N')
 for c in carrier:backgrounds.append(f'[{c}&{gate}]<background>{fn},1,0,0,22,0,0,Add')
# Approved aircraft art for the small native flypast, registered independently
# from the stationary foreground plane and its opening canopy.
jet=ImageOps.mirror(trim(Image.open(S/'landing_jet_master.png').convert('RGBA'))).resize((128,64),Image.Resampling.LANCZOS)
flyby=Image.new('RGBA',(1120,864));flyby.alpha_composite(jet,(992,800));save_png(flyby,P/'ending_flyby.png')
for j,e in enumerate(M['flyby']):
 gate=cond(f'endFlyby{j}','spriteAtPosition',e['x'],e['y'],e['pattern'],e['palette'],'N')
 for c in carrier:bg(c+'&'+gate,'ending_flyby.png',23,248-e['x'],200-e['y'])
details=Image.new('RGBA',(32,32));ImageDraw.Draw(details).text((16,16),'♥',font=face(27),anchor='mm',fill='#edc773')
save_png(details,P/'ending_details.png')
for c in carrier:rules.append(f"[{c}]<tile>{index},{M['heart']['pattern']},{M['heart']['palette']},0,0,1,N")
for pattern,pal in M['ending_sprite_keys']:
 for c in carrier:rules.append(f'[{c}]<tile>0,{pattern},{pal},0,0,1,N')
# The start prompt appears/blinks exactly when its native nametable word does.
ppu('endPromptVisible',0x20ea,0x1f)
prompt=Image.new('RGBA',(1024,960));d=ImageDraw.Draw(prompt);d.rounded_rectangle((304,170,720,218),radius=10,fill='#07151dc0',outline='#b59d68',width=1);label(prompt,512,194,'PUSH START KEY',23)
save_png(prompt,P/'ending_prompt.png')
for c in carrier:bg(c+'&endPromptVisible','ending_prompt.png',21)

# Preserve default alternatives when introducing exact-palette tile keys.
oldkeys=set();defaults=defaultdict(list)
for line in lines:
 if '<tile>' not in line:continue
 v=line.split('<tile>')[1].split(',');oldkeys.add(tuple(v[1:3]))
 if v[6]=='Y':defaults[v[1]].append(line)
for pattern,pal in sorted({tuple(l.split('<tile>')[1].split(',')[1:3]) for l in rules}-oldkeys):
 for line in defaults[pattern]:
  v=line.split('<tile>')[1].split(',');v[2]=pal;v[6]='N';rules.append(line.split('<tile>')[0]+'<tile>'+','.join(v))

i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1;lines[i:i]=['<img>ending_details.png']+conditions+additions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l);lines[i:i]=backgrounds+list(dict.fromkeys(rules))
lines[0]='# Top Gun HD v0.15.0 - recorded close shuttle and endings'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
report=dict(new_shuttle_stages=len(plates),canopy_poses=5,conditions=len(conditions),backgrounds=len(backgrounds),rules=len(set(rules)))
(S/'ending_build.json').write_text(json.dumps(report,indent=2)+'\n');print('Ending build:',report)
