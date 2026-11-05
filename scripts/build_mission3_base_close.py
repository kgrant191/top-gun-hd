"""Complete the recorded base flyover and preserve its art during missile hits."""
from pathlib import Path
from collections import defaultdict
import json
from PIL import Image
from pack_io import save_png

R = Path(__file__).resolve().parents[1]
P, S = R / 'pack', R / 'source'
M = json.loads((S / 'mission3_base_close_mappings.json').read_text())
lines = (P / 'hires.txt').read_text().splitlines()
assert '<img>mission3_base_guns.png' not in lines
index = sum(line.startswith('<img>') for line in lines)
scene = 'cockpit&cockpitBorder&missionThree&mission2Flight&rearCombatPhase'
world, sprite = scene + '&environmentWorld', scene + '&enemyWorld'
conditions, rules, backgrounds, fallbacks = [], [], [], []


def trim(im):
    return im.crop(im.getchannel('A').point(lambda a: 255 if a >= 24 else 0).getbbox())


base = trim(Image.open(S / 'mission3_base_master.png').convert('RGBA'))
plates = {}
for entry in M['boss_stages']:
    stage = entry['stage']
    ox, oy = entry['origin']
    x0, y0, x1, y1 = entry['bbox']
    art = base.resize(((x1-x0)*4, (y1-y0)*4), Image.Resampling.LANCZOS)
    plate = Image.new('RGBA', (2048, 1536))
    # Later native sizes cross the vertical nametable boundary at y=240.
    # The continuous plate includes both pages, following the same scroll.
    for dx in [0, 1024]:
        plate.alpha_composite(art, ((ox+x0)*4+dx, (oy+y0)*4))
    filename = f'mission3_base_{stage:02d}.png'
    save_png(plate, P / filename)
    plates[stage] = filename
    gates = []
    for ti, tile in enumerate(entry['tiles']):
        name = f'm3CloseBase{stage}Tile{ti}'
        gates.append(name)
        conditions.append(f'<condition>{name},ppuMemoryCheckConstant,{tile["address"]:04X},==,{tile["tile"]:02X}')
    backgrounds.append(f'[{scene}&bossBodyPresent&' + '&'.join(gates) + f']<background>{filename},1,1,1,9')
for stage in range(7, 13):
    fallbacks.append(f'[{scene}&bossBodyPresent&bossDistance{stage}]<background>{plates[min(stage,11)]},1,1,1,9')

# All captured building keys need both the normal desert and impact palette.
# Earlier damage coverage only included the smaller base present in that hit.
for pattern in M['boss_background_keys']:
    for palette in ['0F302721', '0F301016']:
        rules.append(f'[{world}&bossBodyPresent]<tile>0,{pattern},{palette},0,0,1,N')

components = Image.open(S / 'mission2_boss_components_master.png').convert('RGBA')
box = json.loads((S / 'mission2_approach_mappings.json').read_text())['component_crops']['turret']
gun = trim(components.crop(box))
atlas = Image.new('RGBA', (1024, 32))
slot = 0
gun_fallbacks = []
for li, entry in enumerate(M['gun_layouts']):
    w, h = entry['size']
    x0, y0, x1, y1 = entry['bbox']
    canvas = Image.new('RGBA', (w*4, h*4))
    canvas.alpha_composite(gun.resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS),(x0*4,y0*4))
    # Adjacent ground guns are separate native objects, even where their
    # sprite cells overlap. Each captured component keeps its own lifetime.
    for ti, tile in enumerate(entry['tiles']):
        assert tile['attr'] & 192 == 0
        x, y = tile['x']*4, tile['y']*4
        ax = slot*32
        assert ax+32 <= atlas.width
        atlas.alpha_composite(canvas.crop((x,y,x+32,y+32)),(ax,0))
        slot += 1
        for pi, palette in enumerate(['FF101B0F','FF381A0F']):
            gates = []
            for ai, anchor in enumerate([entry['tiles'][0],entry['tiles'][-1]]):
                name = f'm3CloseGun{li}_{ti}_{pi}_{ai}'
                gates.append(name)
                conditions.append(f'<condition>{name},spriteNearby,{anchor["x"]-tile["x"]},{anchor["y"]-tile["y"]},{anchor["pattern"]},{palette},N')
            gate = sprite+'&!hmirror&!vmirror'
            tail = f'<tile>{index},{tile["pattern"]},{palette},{ax},0,1,N'
            rules.append('['+gate+'&'+'&'.join(gates)+']'+tail)
            gun_fallbacks.append('['+gate+']'+tail)
rules += gun_fallbacks

# Preserve generic alternatives wherever a new exact-palette key is created.
oldkeys = set()
defaults = defaultdict(list)
for line in lines:
    if '<tile>' not in line:
        continue
    v = line.split('<tile>')[1].split(',')
    oldkeys.add(tuple(v[1:3]))
    if v[6] == 'Y':
        defaults[v[1]].append(line)
newkeys = {tuple(line.split('<tile>')[1].split(',')[1:3]) for line in rules}
for pattern, palette in sorted(newkeys-oldkeys):
    for line in defaults[pattern]:
        v = line.split('<tile>')[1].split(',')
        v[2], v[6] = palette, 'N'
        rules.append(line.split('<tile>')[0]+'<tile>'+','.join(v))

save_png(atlas,P/'mission3_base_guns.png')
i = max(i for i,line in enumerate(lines) if line.startswith('<img>'))+1
lines[i:i] = ['<img>mission3_base_guns.png']+conditions
# Keep every old stable-size signature ahead of the new transfer fallbacks.
i = next(i for i,line in enumerate(lines) if '&bossDistance0]<background>mission3_base_00.png' in line)
lines[i:i] = fallbacks
i = next(i for i,line in enumerate(lines) if '<tile>' in line or '<background>' in line)
lines[i:i] = backgrounds+rules
lines[0] = '# Top Gun HD v0.11.2 - Complete base flyover and missile-hit palette'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
report = {'new_base_plates':len(plates),'last_distance_alias':11,'gun_layouts':len(M['gun_layouts']),
          'atlas_cells':slot,'base_pattern_keys':len(M['boss_background_keys']),
          'rules':len(rules),'conditions':len(conditions),'backgrounds':len(backgrounds)+len(fallbacks)}
(S/'mission3_base_close_build.json').write_text(json.dumps(report,indent=2)+'\n')
print('Base close approach:',report)
