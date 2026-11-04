"""Fix the five recorded Mission 2 regressions without changing prior PNGs."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageOps
from pack_io import save_png

R=Path(__file__).resolve().parents[1];P=R/'pack';S=R/'source'
M=json.loads((S/'mission2_fix_mappings.json').read_text())
old=json.loads((S/'mission2_mappings.json').read_text())
lines=(P/'hires.txt').read_text().splitlines()
assert '<img>mission2_fixes.png' not in lines
index=sum(l.startswith('<img>') for l in lines)
atlas=Image.new('RGBA',(512,512));slot=0;rules=[]
conditions=['<condition>mission2Takeoff,memoryCheckConstant,0018,==,06']
scene='cockpit&cockpitBorder&missionTwo'
flight=scene+'&mission2Flight&rearCombatPhase'

def add(im,pattern,palette,cond):
    global slot
    x,y=slot%16*32,slot//16*32;slot+=1;assert slot<=256
    atlas.alpha_composite(im,(x,y))
    rules.append(f'[{cond}]<tile>{index},{pattern},{palette},{x},{y},1,N')

def trimmed(name):
    im=Image.open(S/name).convert('RGBA')
    return im.crop(im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())

# The missing edge rows occur in takeoff mode 6, before flight mode 7.
# Route values during takeoff are animation stages rather than flight routes.
for pattern in M['horizon_keys']:
    rules.append(f'[{scene}&mission2Takeoff&environmentWorld]<tile>0,{pattern},0F301121,0,0,1,N')

# The refueling transition exposes a native strip across the first three
# scanlines even when its tile candidates are masked. Extend the existing
# level-flight sky above native background pixels for this entry phase only.
# Foreground sprites and the tanker remain above this small edge layer.
sky=Image.open(P/'environment_sky.png').convert('RGBA').crop((0,0,1024,12))
save_png(sky,P/'mission2_refuel_sky_edge.png')
backgrounds=[f'[{scene}&mission2Flight&refuelRoute&refuelActive&!refuelControl&envBank_zero]<background>mission2_refuel_sky_edge.png,1,0,0,21']

# A separate tiny enemy pattern (CB) was never mapped in v0.8.0. Give the
# distant silhouette a readable six-pixel footprint within its existing cell.
art=trimmed('mission2_reused_front.png')
im=Image.new('RGBA',(32,32));im.alpha_composite(art.resize((26,16),Image.Resampling.LANCZOS),(3,9))
for pal in ['FF381A0F','FF38210F','FF153630']:
    add(im,M['distant_enemy'],pal,flight+'&enemyWorld')

# B9 is the smallest approaching boat, not an impact burst. Larger boat
# poses continue using the original Mission 2 atlas.
art=trimmed('mission2_boat_master.png');im=Image.new('RGBA',(32,32))
art=ImageOps.contain(art,(28,30),Image.Resampling.LANCZOS)
im.alpha_composite(art,((32-art.width)//2,(32-art.height)//2))
add(im,M['small_boat'],'FF10000F',flight+'&enemyWorld')

# Brighter steel and white wake improve separation from the dark ocean.
# Keep the same native tile geometry, mirroring and distance stages.
master=trimmed('mission2_submarine_bright_master.png');assigned=set()
for e in sorted((e for e in old['objects'] if e['kind']=='submarine'),key=lambda e:-e['count']):
    w,h=e['size'];x0,y0,x1,y1=e['bbox']
    im=Image.new('RGBA',(w*4,h*4))
    im.alpha_composite(master.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
    for t in e['tiles']:
        p=t['pattern']
        if p in assigned:continue
        assigned.add(p);x,y=t['x']*4,t['y']*4;piece=im.crop((x,y,x+32,y+32))
        if t['attr']&64:piece=ImageOps.mirror(piece)
        if t['attr']&128:piece=ImageOps.flip(piece)
        add(piece,p,'FF10000F',flight+'&enemyWorld')

# The threat sprite precedes the full rear-display anchors and can outlast
# them. Retain its approved amber drawing for its entire native HUD lifetime.
danger=json.loads((S/'damage_hud_mappings.json').read_text())
target_keys=set(danger['danger_target'].values())
for l in lines:
    if '<tile>9,' not in l or ',FF2A100F,' not in l:continue
    v=l.split('<tile>')[1].split(',')
    if v[1] in target_keys:
        rules.append('['+flight+'&flightX0&flightX1&flightY0&flightY1]<tile>'+','.join(v))

# The early refueling radar introduces long vertical segments (native 9A).
# A new exact key had no usable radar fallback, exposing bright native cells.
im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
d.line((16,0,16,31),fill='#285e4d',width=2)
add(im,M['radar_vertical'],'0F2A0A21',scene+'&mission2Flight&refuelRoute&!refuelControl&!rearThreatL&flightX0&flightX1&flightY0&flightY1')

# All new keys either already exist or have their original default preserved.
oldkeys=set();defaults={}
for l in lines:
    if '<tile>' not in l:continue
    v=l.split('<tile>')[1].split(',');oldkeys.add((v[1],v[2]))
    if v[6]=='Y':defaults.setdefault(v[1],[]).append(l)
newkeys={(v[1],v[2]) for l in rules for v in [l.split('<tile>')[1].split(',')]}
for pattern,pal in sorted(newkeys-oldkeys):
    for l in defaults.get(pattern,[]):
        v=l.split('<tile>')[1].split(',');v[2]=pal;v[6]='N'
        rules.append(l.split('<tile>')[0]+'<tile>'+','.join(v))

save_png(atlas,P/'mission2_fixes.png')
i=max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1
lines[i:i]=['<img>mission2_fixes.png']+conditions
i=next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l)
lines[i:i]=rules+backgrounds
lines[0]='# Top Gun HD v0.8.1 - Mission 2 horizon, naval targets and HUD corrections'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
(S/'mission2_fix_build.json').write_text(json.dumps({'atlas_cells':slot,'rules':len(rules),'backgrounds':len(backgrounds),'preserved_v080_pngs':136},indent=2)+'\n')
print('Mission 2 corrections:',slot,'atlas cells;',len(rules),'rules')
