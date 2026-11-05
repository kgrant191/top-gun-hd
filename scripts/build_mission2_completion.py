"""Finish recorded Mission 2 refueling and carrier combat with render-only rules."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
from pack_io import save_png

R = Path(__file__).resolve().parents[1]
P, S = R/'pack', R/'source'
M = json.loads((S/'mission2_completion_mappings.json').read_text())
lines = (P/'hires.txt').read_text().splitlines()
assert '<img>mission2_completion.png' not in lines, 'Rebuild the base first'
index = sum(l.startswith('<img>') for l in lines)
scene = 'cockpit&cockpitBorder&missionTwo&mission2Flight'
boss = scene+'&mission2BossRoute'
combat = scene+'&rearCombatPhase'
conditions = [
    '<condition>refuelDeparture,memoryCheckConstant,009F,==,07',
    '<condition>refuelAircraftVisible,memoryCheckConstant,009F,<,08',
    '<condition>mission2BossRoute,memoryCheckConstant,002E,==,06',
    '<condition>bossMeterY0,originPositionCheckY,>=,28',
    '<condition>bossMeterY1,originPositionCheckY,<,30',
    '<condition>mission2LandingRoute,memoryCheckConstant,002E,==,05',
    '<condition>rolloutInitPhase,memoryCheckConstant,009F,==,05',
    '<condition>rolloutInitTimer,memoryCheckConstant,009C,==,00',
]
rules, backgrounds = [], []
atlas = Image.new('RGBA',(512,64)); slot = 0

def add(im, pattern, palette, condition):
    global slot
    x, y = slot%16*32, slot//16*32
    slot += 1
    assert slot <= 32
    atlas.alpha_composite(im,(x,y))
    rules.append(f'[{condition}]<tile>{index},{pattern},{palette},{x},{y},1,N')

def trimmed(name):
    im = Image.open(S/name).convert('RGBA')
    return im.crop(im.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox())

# Departure scrolls the left page off-screen. The right page must stay empty,
# then both copies must disappear before stage 8 resets horizontal scroll.
plate = Image.open(P/'mission2_tanker.png').convert('RGBA')
departure = Image.new('RGBA',plate.size)
departure.paste(plate.crop((0,0,1024,1536)),(0,0))
save_png(departure,P/'mission2_tanker_departure.png')
backgrounds.append(f'[{scene}&refuelRoute&refuelDeparture]'
                   '<background>mission2_tanker_departure.png,1,1,1,31')
# Native rollout initialization is blank while the mode has already advanced
# from phase 4 to 5. Keep its stale top scanline covered until the timer starts.
backgrounds.append('[missionTwo&mission2Flight&mission2LandingRoute&rolloutInitPhase&rolloutInitTimer]'
                   '<background>landing_black.png,1,0,0,39')
old = '[cockpit&cockpitBorder&refuelRoute&refuelActive]<background>mission2_tanker.png,1,1,1,31'
assert lines.count(old) == 1
i = lines.index(old)
lines[i:i+1] = [
    old.replace(']<background>','&!missionTwo]<background>'),
    old.replace(']<background>','&missionTwo&refuelAircraftVisible]<background>'),
]

# Boss route 6 was excluded by the earlier route<5 sea mask. These exact
# captured patterns contain only sea/sky colors; ship pixels remain separate.
for pattern in M['boss_ocean_keys']:
    rules.append(f'[{boss}&environmentWorld]<tile>0,{pattern},0F301121,0,0,1,N')

# Keep native target position and size. Reuse the approved carrier and impact
# artwork, with a new damaged carrier matching the second recorded pose.
masters = [trimmed('landing_broadside_master.png'),
           trimmed('mission2_boss_damaged_master.png'),
           trimmed('impact_burst_master.png')]
for layout, art in zip(M['boss_layouts'],masters):
    w,h = layout['size']; x0,y0,x1,y1 = layout['bbox']
    im = Image.new('RGBA',(w*4,h*4))
    im.alpha_composite(art.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
    for tile in layout['cells']:
        x,y = tile['x']*4,tile['y']*4
        # The target persists briefly after a hit changes route 6 to route 3.
        for palette in ['0F301121','0F301016']:
            add(im.crop((x,y,x+32,y+32)),tile['pattern'],palette,combat+'&environmentWorld')

# Six native meter cells retain their exact filled/empty state. The title is
# cut across those same cells, so it appears and clears with the actual meter.
title = Image.new('RGBA',(192,32),'#061b20df')
d = ImageDraw.Draw(title)
font = ImageFont.truetype(str(S/'fonts/DejaVuSansMono-Bold.ttf'),13)
d.text((96,0),'CARRIER',font=font,anchor='mt',fill='#e3d8b3')
for cell in range(6):
    x = 192+cell*8
    name = f'bossMeterX{cell}'
    conditions.append(f'<condition>{name},originPositionCheckX,==,{x}')
    for pattern, entry in M['boss_health'].items():
        im = title.crop((cell*32,0,cell*32+32,32)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((2,16,29,29),radius=2,fill='#132d32',outline='#77908a',width=1)
        if entry['tile'] == 16:
            d.rounded_rectangle((4,18,27,27),radius=1,fill='#efbb62')
            d.line((5,18,26,18),fill='#ffe4a0',width=1)
        add(im,pattern,'FF2A100F',combat+'&bossMeterY0&bossMeterY1&'+name)

# The lethal palette has explicit warning-letter mappings that suppress
# normal font defaults even after the warning ends. Reuse the approved
# flight-display glyphs for the radar during that captured loss/retry pause.
for pattern in M['loss_radar_letters'].values():
    donor = next(line for line in lines if f'<tile>3,{pattern},0F2A0A31,' in line
                 and '&flightY1' in line)
    tail = donor.split(']<tile>')[1].replace(',0F2A0A31,',',0F2A0A16,').replace(',1,Y',',1,N')
    rules.append(f'[{combat}&!rearThreatL&flightX0&flightX1&flightY0&flightY1]<tile>'+tail)

# A new explicit palette key disables Mesen's default-palette fallback for
# that key. Carry any prior default mappings forward outside the new scope.
oldkeys, defaults = set(), {}
for line in lines:
    if '<tile>' not in line: continue
    v = line.split('<tile>')[1].split(',')
    oldkeys.add((v[1],v[2]))
    if v[6] == 'Y': defaults.setdefault(v[1],[]).append(line)
newkeys = {(v[1],v[2]) for line in rules for v in [line.split('<tile>')[1].split(',')]}
for pattern,palette in sorted(newkeys-oldkeys):
    for line in defaults.get(pattern,[]):
        v = line.split('<tile>')[1].split(',');v[2]=palette;v[6]='N'
        rules.append(line.split('<tile>')[0]+'<tile>'+','.join(v))

save_png(atlas,P/'mission2_completion.png')
i = max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1
lines[i:i] = ['<img>mission2_completion.png']+conditions
i = next(i for i,l in enumerate(lines) if '<tile>' in l or '<background>' in l)
lines[i:i] = backgrounds+rules
lines[0] = '# Top Gun HD v0.9.0 - Single tanker departure and Mission 2 carrier boss'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
(S/'mission2_completion_build.json').write_text(json.dumps({
    'atlas_cells':slot,'rules':len(rules),'backgrounds':len(backgrounds),
    'boss_layouts':len(M['boss_layouts']),'preserved_v082_pngs':139,
},indent=2)+'\n')
print('Mission 2 completion:',slot,'atlas cells;',len(rules),'rules')
