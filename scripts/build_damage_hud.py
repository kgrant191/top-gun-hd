"""Native health, rear-threat display and incoming missile/impact coverage.

All production conditions are read-only. Capture-derived CHR keys are retained
as source data, so rebuilding does not require a ROM or private replay.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
from pack_io import save_png

R = Path(__file__).resolve().parents[1]
P = R / 'pack'
M = json.loads((R / 'source/damage_hud_mappings.json').read_text())
lines = (P / 'hires.txt').read_text().splitlines()
assert '<img>damage_hud.png' not in lines, 'Rebuild the base pack first'
lines[0] = '# Top Gun HD v0.6.0 - native health, rear threat, incoming missiles and impact'
index = sum(l.startswith('<img>') for l in lines)
font = R / 'source/fonts/DejaVuSansMono-Bold.ttf'
atlas = Image.new('RGBA', (512, 512))
slot = 0
rules = []
conditions = [
    '<condition>hullImpact,memoryCheckConstant,004E,==,00',
    '<condition>cloudImpact,ppuMemoryCheckConstant,3F06,==,10',
    '<condition>impactPalette,ppuMemoryCheckConstant,3F07,==,16',
    '<condition>rearThreatL,ppuMemoryCheckConstant,2AAC,==,AD',
    '<condition>rearThreatR,ppuMemoryCheckConstant,2AB3,==,B0',
    '<condition>rearTextY0,originPositionCheckY,>=,143',
    '<condition>rearTextY1,originPositionCheckY,<,153',
]
backgrounds = []
scene = 'cockpit&cockpitBorder'
rear = scene + '&rearThreatL&rearThreatR'
flight = '&flightX0&flightX1&flightY0&flightY1'

def add(image, pattern, palette, cond):
    global slot
    x, y = slot % 16 * 32, slot // 16 * 32
    atlas.alpha_composite(image, (x, y))
    slot += 1
    rules.append(f'[{cond}]<tile>{index},{pattern},{palette},{x},{y},1,N')

def registered(image, stem, cond, priority=33):
    """Register additions with the same native shake as the approved cockpit."""
    for tag, dx, shake in [('left',-4,'impactLeft'),('right',4,'impactRight'),
                           ('center',0,'!impactLeft&!impactRight')]:
        shifted = Image.new('RGBA', image.size)
        shifted.paste(image, (dx, 0))
        filename = f'{stem}_{tag}.png'
        save_png(shifted, P / filename)
        backgrounds.append(f'[{cond}&{shake}]<background>{filename},1,0,0,{priority}')

# The game initializes $4E to 12 and subtracts 3 for each bullet hit. Missiles
# set it to zero; respawn restores 12. Show the actual value, never a timer.
for hp in range(13):
    name = f'hull{hp}'
    conditions.append(f'<condition>{name},memoryCheckConstant,004E,==,{hp:02X}')
    im = Image.new('RGBA', (1024,960)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((318,842,706,891), radius=5, fill='#081419', outline='#779491', width=2)
    color = '#9bf4ca' if hp > 6 else '#ffbf66' if hp > 3 else '#ff6f58'
    d.text((328,845),'HULL',font=ImageFont.truetype(str(font),15),fill='#afc7c3')
    d.text((694,845),f'{round(hp/12*100):3d}%',font=ImageFont.truetype(str(font),15),fill=color,anchor='rt')
    for j in range(12):
        x = 328 + j*30
        d.rounded_rectangle((x,868,x+25,882),radius=2,
                            fill=color if j<hp else '#14282b',
                            outline='#d6ffde' if j<hp else '#345050',width=1)
    registered(im, f'hull_{hp:02d}', scene+'&'+name)

# Rear-threat framing is a native UI illustration. Draw it as clean instrument
# lines, while the original sprite positions and flashing text stay live.
im = Image.new('RGBA',(1024,960)); d = ImageDraw.Draw(im)
d.rectangle((319,576,703,831),fill='#061619')
for y in range(608,831,16): d.line((324,y,698,y),fill='#0a2326',width=1)
d.text((512,626),'REAR THREAT',font=ImageFont.truetype(str(font),13),fill='#b58e69',anchor='mt')
points=[(320,818),(395,818),(411,806),(419,679),(434,715),(440,799),
        (463,813),(480,818),(544,818),(560,813),(584,799),(590,715),
        (605,679),(613,806),(629,818),(703,818)]
d.line(points,fill='#734d38',width=7,joint='curve')
d.line(points,fill='#e5af75',width=3,joint='curve')
d.line((440,799,452,825,480,825,484,818),fill='#c88e60',width=3)
d.line((584,799,572,825,544,825,540,818),fill='#c88e60',width=3)
for x in [336,688]:
    d.line((x,650,x,670),fill='#4d6e68',width=2)
registered(im,'rear_threat',rear,15)
for pattern in sorted(set(M['danger_background'].values())):
    rules.append(f'[{rear}{flight}]<tile>0,{pattern},0F2A0A31,0,0,1,N')
# Redraw the warning letters only within their native heading row.
for t,ch in [(0x13,'D'),(0x10,'A'),(0x1d,'N'),(0x16,'G'),(0x14,'E'),(0x21,'R'),(0x0e,'!')]:
    tile=Image.new('RGBA',(32,32));d=ImageDraw.Draw(tile)
    d.text((16,15),ch,font=ImageFont.truetype(str(font),24),fill='#ffb271',anchor='mm')
    add(tile,M['danger_text'][str(t)],'0F2A0A31',rear+flight+'&rearTextY0&rearTextY1')
# Preserve the original moving 24x16 threat footprint, including the top tile.
target=Image.new('RGBA',(96,64));d=ImageDraw.Draw(target)
plane=[(48,6),(52,26),(59,34),(91,43),(91,48),(56,43),(54,56),
       (65,60),(65,63),(48,60),(31,63),(31,60),(42,56),(40,43),
       (5,48),(5,43),(37,34),(44,26)]
d.polygon(plane,fill='#ffc58a');d.line(plane+[plane[0]],fill='#4c2d1b',width=2)
d.line((48,13,48,51),fill='#fff4d2',width=3)
for t,x,y in [(0x2a,32,0),(0x2b,0,32),(0x2c,32,32),(0x2d,64,32)]:
    add(target.crop((x,y,x+32,y+32)),M['danger_target'][str(t)],'FF2A100F',rear+flight)

# Incoming missiles use palette zero, unlike clouds/explosions. Two growth
# stages contain unique CHR variants that the original combat atlas missed.
master=Image.open(R/'source/incoming_missile_master.png').convert('RGBA')
master=master.crop(master.getbbox())
def fitted(size):
    out=Image.new('RGBA',(size,size))
    art=ImageOps.contain(master,(size-2,size-2),Image.Resampling.LANCZOS)
    out.alpha_composite(art,((size-art.width)//2,(size-art.height)//2))
    return out
add(fitted(32),M['missile'][str(0x3f)],'FF2A100F',scene+'&enemyWorld')
layouts=[[(0x3b,0,0,0),(0x3c,8,0,0),(0x39,0,8,0),(0x3a,8,8,0)],
         [(0x3d,0,0,0),(0x3e,8,0,0),(0x3e,0,8,192),(0x2f,8,8,0)]]
for k,layout in enumerate(layouts):
    art=fitted(52 if k==0 else 64)
    if k==0:
        pad=Image.new('RGBA',(64,64));pad.alpha_composite(art,(6,6));art=pad
    for j,(t,x,y,attr) in enumerate(layout):
        checks=[]
        for n,(nt,nx,ny,_) in enumerate(layout):
            if n==j:continue
            cname=f'incoming{k}_{j}_{n}';checks.append(cname)
            conditions.append(f'<condition>{cname},spriteNearby,{(nx-x)*(-1 if attr&64 else 1)},{(ny-y)*(-1 if attr&128 else 1)},{M["missile"][str(nt)]},FF2A100F,N')
        piece=art.crop((x*4,y*4,x*4+32,y*4+32))
        if attr&64:piece=ImageOps.mirror(piece)
        if attr&128:piece=ImageOps.flip(piece)
        mirrors=('hmirror' if attr&64 else '!hmirror')+'&'+('vmirror' if attr&128 else '!vmirror')
        add(piece,M['missile'][str(t)],'FF2A100F',scene+'&enemyWorld&'+mirrors+'&'+'&'.join(checks))

# Assemble every complete flame layout observed in the supplied replays,
# largest first. This covers native size/rotation variants absent from v0.4.
master=Image.open(R/'source/impact_burst_master.png').convert('RGBA')
master=master.crop(master.getbbox())
for k,entry in enumerate(sorted(M['explosion_layouts'],key=lambda v:-v['width'])):
    size=entry['width']*4
    burst=ImageOps.contain(master,(size-2,size-2),Image.Resampling.LANCZOS)
    art=Image.new('RGBA',(size,size));art.alpha_composite(burst,((size-burst.width)//2,(size-burst.height)//2))
    if k%2:art=art.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    layout=entry['tiles']
    for j,tile in enumerate(layout):
        x,y,attr=tile['x'],tile['y'],tile['attr']
        checks=[]
        for n,other in enumerate(layout):
            # Check the exposed top rim. Incoming missile sprites can occlude
            # the flame center, making whole-layout neighborhood checks fail.
            if n==j or other["y"]!=0:continue
            cname=f'impactBurst{k}_{j}_{n}';checks.append(cname)
            conditions.append(f'<condition>{cname},spriteNearby,{(other["x"]-x)*(-1 if attr&64 else 1)},{(other["y"]-y)*(-1 if attr&128 else 1)},{other["pattern"]},{entry["palette"]},N')
        piece=art.crop((x*4,y*4,x*4+32,y*4+32))
        if attr&64:piece=ImageOps.mirror(piece)
        if attr&128:piece=ImageOps.flip(piece)
        mirrors=('hmirror' if attr&64 else '!hmirror')+'&'+('vmirror' if attr&128 else '!vmirror')
        cond=scene+'&enemyWorld&'+mirrors
        if checks:cond+='&'+'&'.join(checks)
        add(piece,tile['pattern'],entry['palette'],cond)
# Native solid-center sprites would cover the center of the new burst.
for pattern in M['impact_center']:
    rules.append(f'[{scene}&hullImpact&enemyWorld]<tile>0,{pattern},FF2A100F,0,0,1,N')

# Death flash changes the scenery palette. Reuse the banked HD world and add
# a translucent damage wash, preserving the game's timing and visible action.
for line in lines:
    if '<tile>' in line and 'environmentWorld' in line and ',0F203031,' in line:
        rules.append(line.replace(',0F203031,',',0F301016,'))
    if '<background>environment_cloudtop_flight_' in line:
        backgrounds.append(line.replace('&envCloudLayer]', '&cloudImpact&impactPalette]'))
lines=[l.replace('&!envCloudLayer]', '&!envCloudLayer&!cloudImpact]') if '<background>environment_ocean_flight_' in l else l for l in lines]
yy,xx=np.mgrid[0:512,0:1024]
edge=np.maximum(np.abs(xx-511.5)/511.5,np.abs(yy-255.5)/255.5)
a=np.uint8(25+100*edge**3)
wash=np.zeros((960,1024,4),np.uint8);wash[:512,:,:3]=(244,59,19);wash[:512,:,3]=a
save_png(Image.fromarray(wash),P/'missile_impact_wash.png')
backgrounds.append(f'[{scene}&hullImpact&impactPalette]<background>missile_impact_wash.png,1,0,0,34')

save_png(atlas,P/'damage_hud.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1
lines[i:i]=['<img>damage_hud.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l)
lines[i:i]=backgrounds+rules
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
print('Damage HUD:',slot,'tiles;',len(backgrounds),'read-only display layers')
