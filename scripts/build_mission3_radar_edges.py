"""Restore radar artwork in cells omitted by the native metasprite.

The original dish fits an L-shaped tile footprint. The painted dish has a
different silhouette, so its intact image extends into several absent cells.
Render-only additions fill those cells using the exact existing art transform.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageOps
from pack_io import save_png

R = Path(__file__).resolve().parents[1]
P, S = R / 'pack', R / 'source'
lines = (P / 'hires.txt').read_text().splitlines()
assert '<img>mission3_radar_edges.png' not in lines
index = sum(line.startswith('<img>') for line in lines)
scene = 'cockpit&cockpitBorder&missionThree&mission2Flight&rearCombatPhase&enemyWorld'
raw = Image.open(S / 'mission3_radar_master.png').convert('RGBA')
art = raw.crop(raw.getchannel('A').point(lambda a: 255 if a >= 24 else 0).getbbox())
atlas = Image.new('RGBA', (512, 32))
conditions, additions, rules, coverage = [], [], [], []
slot = 0

for filename, group, mirrored in [
    ('mission3_mappings.json', 'objects', {47, 62, 79, 90}),
    ('mission3_completion_mappings.json', 'new_layouts', {71}),
]:
    for entry in json.loads((S / filename).read_text())[group]:
        if entry['kind'] != 'radar':
            continue
        # These are screen-clipped fragments, not complete native layouts.
        # Their intact families below provide the additions as they enter/exit.
        if filename == 'mission3_mappings.json' and entry['id'] in {99, 100, 101, 105}:
            continue
        w, h = entry['size']
        x0, y0, x1, y1 = entry['bbox']
        view = ImageOps.mirror(art) if entry['id'] in mirrored else art
        canvas = Image.new('RGBA', (w * 4, h * 4))
        canvas.alpha_composite(view.resize(((x1-x0)*4, (y1-y0)*4), Image.Resampling.LANCZOS), (x0*4, y0*4))
        occupied = {(t['x'], t['y']) for t in entry['tiles']}
        anchor = entry['tiles'][0]
        assert all(t['attr'] & 192 == 0 for t in entry['tiles']) or occupied == {(0, 0)}
        for y in range(0, h, 8):
            for x in range(0, w, 8):
                if (x, y) in occupied:
                    continue
                piece = canvas.crop((x*4, y*4, x*4+32, y*4+32))
                if piece.getchannel('A').getbbox() is None:
                    continue
                key = hashlib.sha256(f'TopGunRadarEdge:{filename}:{entry["id"]}:{x}:{y}'.encode()).hexdigest()[:32].upper()
                assert key not in '\n'.join(lines)
                ax, ay = slot * 32, 0
                assert ax + 32 <= atlas.width
                atlas.alpha_composite(piece, (ax, ay))
                slot += 1
                for pi, pal in enumerate(['FF101B0F', 'FF381A0F']):
                    additions.append(f'<addition>{anchor["pattern"]},{pal},{x-anchor["x"]},{y-anchor["y"]},{key},{pal},N')
                    gates = []
                    for ai, sig in enumerate([entry['tiles'][0], entry['tiles'][-1]]):
                        name = f'm3RadarEdge{slot}_{pi}_{ai}'
                        gates.append(name)
                        conditions.append(f'<condition>{name},spriteNearby,{sig["x"]-x},{sig["y"]-y},{sig["pattern"]},{pal},N')
                    rules.append(f'[{scene}&!hmirror&!vmirror&'+ '&'.join(gates)+f']<tile>{index},{key},{pal},{ax},{ay},1,N')
                    # Synthetic cells are transparent outside the exact radar
                    # signature and scene, including destruction and reuse.
                    rules.append(f'<tile>0,{key},{pal},0,0,1,N')
                coverage.append({'source': filename, 'layout': entry['id'], 'cell': [x, y], 'anchor': anchor['pattern'], 'key': key})

save_png(atlas, P / 'mission3_radar_edges.png')
i = max(i for i, line in enumerate(lines) if line.startswith('<img>')) + 1
lines[i:i] = ['<img>mission3_radar_edges.png'] + conditions + additions
i = next(i for i, line in enumerate(lines) if '<tile>' in line or '<background>' in line)
lines[i:i] = rules
lines[0] = '# Top Gun HD v0.11.1 - Complete radar silhouettes at every recorded size'
(P / 'hires.txt').write_text('\n'.join(lines) + '\n')
report = {'atlas_cells': slot, 'additions': len(additions), 'conditions': len(conditions), 'coverage': coverage}
(S / 'mission3_radar_edges_build.json').write_text(json.dumps(report, indent=2) + '\n')
print('Radar edge cells:', slot, '; existing tiles and images unchanged')
