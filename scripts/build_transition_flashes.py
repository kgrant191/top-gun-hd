"""Cover native HUD clearing, lethal palette and missing carrier-rollout phases."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from pack_io import save_png

R = Path(__file__).resolve().parents[1]
P = R / 'pack'
M = json.loads((R / 'source/transition_flash_mappings.json').read_text())
L = json.loads((R / 'source/landing_mappings.json').read_text())
lines = (P / 'hires.txt').read_text().splitlines()
assert '<img>transition_flashes.png' not in lines, 'Rebuild the base pack first'
index = sum(l.startswith('<img>') for l in lines)
atlas = Image.new('RGBA', (512, 512))
rules, conditions = [], ['<condition>rearCombatPhase,memoryCheckConstant,009F,==,00']
slot = 0
scene = 'cockpit&cockpitBorder'
rollout = scene + '&landingMode&rolloutStart&rolloutEnd'

def add(im, pattern, palette, condition):
    global slot
    x, y = slot % 16 * 32, slot // 16 * 32
    atlas.alpha_composite(im, (x, y))
    slot += 1
    rules.append(f'[{condition}]<tile>{index},{pattern},{palette},{x},{y},1,N')

def decode(pattern):
    b = np.frombuffer(bytes.fromhex(pattern), np.uint8)
    return np.unpackbits(b[:8, None], axis=1) + 2 * np.unpackbits(b[8:, None], axis=1)

# Lethal damage changes only the last background-palette entry, 31 -> 16.
# Exact-palette masks and warning text must retain their existing HD styling.
rules.extend(l.replace(',0F2A0A31,', ',0F2A0A16,') for l in lines
             if '<tile>' in l and 'rearThreatL&rearThreatR' in l
             and ',0F2A0A31,' in l)

# The radar overwrites the danger display one native row at a time. The old
# whole-display anchor disappears at row 21 while rows 22-25 still contain
# the rear aircraft. Cover those remaining cells with slices of approved art;
# the new radar rows and their native update timing remain visible.
rear = Image.open(P / 'rear_threat_center.png').convert('RGBA')
for k, cell in enumerate(M['rear_cells']):
    x, y = cell['x'], cell['y']
    names = []
    for axis, value in [('X', x), ('Y', y)]:
        for edge, op, bound in [(0, '>=', value-1), (1, '<', value+2)]:
            name = f'rearRemainder{k}{axis}{edge}'
            conditions.append(f'<condition>{name},originPositionCheck{axis},{op},{bound}')
            names.append(name)
    im = rear.crop((x*4, y*4, (x+8)*4, (y+8)*4))
    for gate in ['!rearThreatL', 'rearThreatL&!rearThreatR']:
        for palette in ['0F2A0A31', '0F2A0A16']:
            add(im, cell['pattern'], palette,
                scene+'&landingMode&rearCombatPhase&'+gate+'&'+'&'.join(names))

# Additional native sprite patterns use the same ivory moving deck lights.
for pattern in M['rollout_marks']:
    mask = Image.fromarray(np.uint8(decode(pattern) == 1)*255).resize(
        (32, 32), Image.Resampling.LANCZOS)
    im = Image.new('RGBA', (32, 32), '#f2eacb')
    im.putalpha(mask)
    add(im, pattern, 'FF2A100F', rollout+'&enemyWorld')

patterns = L['rollout_backgrounds'] + M['rollout_backgrounds']
for pattern in M['rollout_backgrounds']:
    for palette in ['0F301131', '0F001131']:
        rules.append(f'[{rollout}&environmentWorld]<tile>0,{pattern},{palette},0,0,1,N')

# Include every observed partial edge in the existing first-visible-row sort.
# Simply prepending new backgrounds would pick a lower boundary over an
# earlier existing match because Mesen uses the first match at each priority.
backgrounds = []
for value, material, priority in [(2, 'ocean', 7), (1, 'runway', 8)]:
    candidates = []
    for k, pattern in enumerate(patterns):
        rows = np.where(np.any(decode(pattern) == value, axis=1))[0]
        if not len(rows):
            continue
        for y in range(128):
            name = f'landing{material}{k}_{y}'
            if k >= len(L['rollout_backgrounds']):
                conditions.append(f'<condition>{name},tileAtPosition,8,{y},{pattern},00000000,Y')
            candidates.append((y+int(rows[0]), y, k, name))
    for first, _, _, name in sorted(candidates):
        backgrounds.append(f'[{rollout}&{name}]<background>environment_{material}_plane.png,1,0,0,{priority},0,{128-first}')
old = [i for i, l in enumerate(lines) if l.startswith('['+rollout+'&landing')
       and '<background>environment_' in l]
assert old
first_old = old[0]
old_set = set(old)
lines = [l for i, l in enumerate(lines) if i not in old_set]
lines[first_old:first_old] = backgrounds

save_png(atlas, P / 'transition_flashes.png')
i = max(i for i,l in enumerate(lines) if l.startswith('<img>')) + 1
lines[i:i] = ['<img>transition_flashes.png'] + conditions
i = next(i for i,l in enumerate(lines) if '<tile>' in l)
lines[i:i] = rules
lines[0] = '# Top Gun HD v0.7.3 - danger, loss and carrier-rollout flash coverage'
(P / 'hires.txt').write_text('\n'.join(lines)+'\n')
print('Transition coverage:', slot, 'detail tiles;', len(M['rollout_backgrounds']), 'new deck-edge phases')
