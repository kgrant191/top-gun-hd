"""Add the opposite close tank view using the unchanged Mission 3 atlas."""
from pathlib import Path
import json

R = Path(__file__).resolve().parents[1]
P = R / 'pack'
S = R / 'source'
lines = (P / 'hires.txt').read_text().splitlines()
assert not any('m3TankClose' in line for line in lines), 'Already applied'
objects = sorted(json.loads((S / 'mission3_mappings.json').read_text())['objects'],
                 key=lambda entry: -entry['count'])
source_index, source = next((i, entry) for i, entry in enumerate(objects)
                            if entry['id'] == 79)
target = json.loads((S / 'mission3_tank_close.json').read_text())['layout']
source_tiles = {tile['pattern']: (i, tile) for i, tile in enumerate(source['tiles'])}
assert source['size'] == target['size'] == [24, 24]
assert set(source_tiles) == {tile['pattern'] for tile in target['tiles']}

conditions, specific, fallback = [], [], []
for palette_index, palette in enumerate(['FF101B0F', 'FF381A0F']):
    for tile_index, tile in enumerate(target['tiles']):
        old_index, old_tile = source_tiles[tile['pattern']]
        assert tile['x'] == 16 - old_tile['x'] and tile['y'] == old_tile['y']
        assert tile['attr'] == old_tile['attr'] ^ 0x40
        marker = f'&m3Object{source_index}_{old_index}_0&'
        old_rule = next(line for line in lines if marker in line
                        and '<tile>' in line and f',{source["palette"]},' in line)
        head, payload = old_rule.split('<tile>')
        head = head.split('&m3Object')[0].replace('&hmirror', '&!hmirror')
        payload = payload.replace(',' + source['palette'] + ',', ',' + palette + ',')
        gates = []
        for anchor_index, anchor in enumerate([target['tiles'][0], target['tiles'][-1]]):
            name = f'm3TankClose{palette_index}_{tile_index}_{anchor_index}'
            gates.append(name)
            conditions.append(f'<condition>{name},spriteNearby,'
                              f'{anchor["x"] - tile["x"]},{anchor["y"] - tile["y"]},'
                              f'{anchor["pattern"]},{palette},N')
        specific.append(head + '&' + '&'.join(gates) + ']<tile>' + payload)
        # F8 also forms a separate frontal-tank piece. Preserve its existing
        # fallback; the full close-view signature overrides it only as a group.
        fallback_head = head + ']<tile>'
        key = ',' + tile['pattern'] + ',' + palette + ','
        if not any(line.startswith(fallback_head) and key in line for line in lines):
            fallback.append(fallback_head + payload)

# Every exact CHR/palette key already exists; no generic lookup is displaced.
old_keys = {tuple(line.split('<tile>')[1].split(',')[1:3])
            for line in lines if '<tile>' in line}
assert all(tuple(line.split('<tile>')[1].split(',')[1:3]) in old_keys
           for line in specific + fallback)
index = next(i for i, line in enumerate(lines) if '<tile>' in line or '<background>' in line)
lines[index:index] = conditions + specific + fallback
lines[0] = '# Top Gun HD v0.10.1 - Mission 3 close tank orientation fix'
(P / 'hires.txt').write_text('\n'.join(lines) + '\n')
report = {'specific_rules': len(specific), 'fallback_rules': len(fallback),
          'conditions': len(conditions), 'new_images': 0, 'new_exact_keys': 0,
          'source_layout': source['id'], 'native_close_size': target['size']}
(S / 'mission3_tanks_build.json').write_text(json.dumps(report, indent=2) + '\n')
print('Mission 3 tank fix:', report)
