"""Mission-one briefing and native-driven missile selection presentation.

Only verified mission-one menu scenes are replaced. Native text, selection,
confirmation timing, and the return to the cockpit remain under game control.
"""
from pathlib import Path
import json
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pack_io import save_png

R = Path(__file__).resolve().parents[1]
P = R / 'pack'
REF = R / 'source/menu_reference'
FONT = str(R / 'source/fonts/DejaVuSansMono-Bold.ttf')
S = 4


def reference(frame):
    return {ext: (REF / f'{frame}.{ext}').read_bytes()
            for ext in ('chr', 'nt', 'pal')}


brief = reference('00090')
weapons = reference('00270')


def pattern(data, tile):
    return data['chr'][tile * 16:(tile + 1) * 16].hex().upper()


def tile_at(data, x, y):
    return data['nt'][y // 8 * 32 + x // 8]


def colors(data, x0, y0, width, height):
    out = np.zeros((height, width), np.uint8)
    for y in range(height):
        for x in range(width):
            sx, sy = x + x0, y + y0
            tx, ty = sx // 8, sy // 8
            t = tile_at(data, sx, sy)
            a = data['chr'][t * 16 + sy % 8]
            b = data['chr'][t * 16 + sy % 8 + 8]
            v = ((a >> (7 - sx % 8)) & 1) + 2 * ((b >> (7 - sx % 8)) & 1)
            attr = data['nt'][960 + ty // 4 * 8 + tx // 4]
            group = (attr >> ((ty % 4 // 2) * 4 + (tx % 4 // 2) * 2)) & 3
            out[y, x] = data['pal'][group * 4 + v] if v else data['pal'][0]
    return out


def text(draw, xy, label, size=14, fill='#8aa9af', anchor='mm'):
    draw.text(tuple(v * S for v in xy), label,
              font=ImageFont.truetype(FONT, size), fill=fill, anchor=anchor)


def panel(draw, rect, fill='#06151c', outline='#41636d', radius=3):
    draw.rounded_rectangle(tuple(round(v * S) for v in rect),
                           radius=radius * S, fill=fill, outline=outline, width=2)


def simplify(points, eps=1.15):
    if len(points) < 3:
        return points
    a, b = np.array(points[0], float), np.array(points[-1], float)
    p = np.array(points, float)
    v = b - a
    if np.dot(v, v) == 0:
        dist = np.linalg.norm(p - a, axis=1)
    else:
        t = np.clip((p - a) @ v / np.dot(v, v), 0, 1)
        dist = np.linalg.norm(p - (a + t[:, None] * v), axis=1)
    j = int(np.argmax(dist))
    if dist[j] <= eps:
        return [points[0], points[-1]]
    return simplify(points[:j + 1], eps)[:-1] + simplify(points[j:], eps)


def contours(mask):
    h, w = mask.shape
    edges = defaultdict(list)
    for y, x in zip(*np.where(mask)):
        if y == 0 or not mask[y - 1, x]: edges[(x, y)].append((x + 1, y))
        if x == w - 1 or not mask[y, x + 1]: edges[(x + 1, y)].append((x + 1, y + 1))
        if y == h - 1 or not mask[y + 1, x]: edges[(x + 1, y + 1)].append((x, y + 1))
        if x == 0 or not mask[y, x - 1]: edges[(x, y + 1)].append((x, y))
    while edges:
        start = next(iter(edges))
        point = start
        poly = [start]
        while True:
            q = edges[point].pop()
            if not edges[point]: del edges[point]
            poly.append(q)
            point = q
            if point == start: break
        yield simplify(poly)


def signed_area(poly):
    """Positive for outer land, negative for water holes in screen coordinates."""
    return sum(x0 * y1 - x1 * y0
               for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1])) / 2


base = Image.open(R / 'source/briefing_console_master.png').convert('RGBA')
base = base.resize((1024, 960), Image.Resampling.LANCZOS)
d = ImageDraw.Draw(base)
text(d, (128, 14), 'MISSION BRIEFING', 17, '#c1d4d2')
panel(d, (11, 27, 245, 80), '#07151c', '#355360')
d.line((16 * S, 23 * S, 240 * S, 23 * S), fill='#a27d48', width=2)
text(d, (128, 233), 'F-14 / MISSION SYSTEMS', 12, '#719393')
save_png(base,P / 'menu_console.png')

# Coastline geometry comes from the original map, not a newly invented map.
map_image = Image.new('RGBA', base.size)
d = ImageDraw.Draw(map_image)
panel(d, (36, 91, 220, 229), '#04111b', '#608b91')
native_map = colors(brief, 40, 96, 176, 128)
land = native_map == 0x17
map_layer = Image.new('RGBA', (176 * S, 128 * S), '#092332')
md = ImageDraw.Draw(map_layer)
map_contours = [poly for poly in contours(land) if len(poly) > 3]
# Fill enclosing regions first, then their holes (and any islands inside holes).
# The traced winding distinguishes land from enclosed water without changing
# the original coastline geometry.
for poly in sorted(map_contours, key=lambda p: abs(signed_area(p)), reverse=True):
    pts = [(round(x * S), round(y * S)) for x, y in poly]
    md.polygon(pts, fill='#21494b' if signed_area(poly) > 0 else '#092332')
for poly in map_contours:
    pts = [(round(x * S), round(y * S)) for x, y in poly]
    md.line(pts, fill='#83aaa3', width=2, joint='curve')
for x in range(0, 176 * S, 16 * S):
    md.line((x, 0, x, 128 * S), fill='#31505b70', width=1)
for y in range(0, 128 * S, 16 * S):
    md.line((0, y, 176 * S, y), fill='#31505b70', width=1)
map_image.alpha_composite(map_layer, (40 * S, 96 * S))
save_png(map_image,P / 'menu_map.png')


def draw_missile(canvas, y, length, family):
    """Vector silhouettes retain the original left-facing schematic layout."""
    d = ImageDraw.Draw(canvas)
    x, mid = 48, y + 5
    tail = x + length
    def polygon(points, fill, outline='#b1c8c5'):
        pts = [(int(a * S), int(b * S)) for a, b in points]
        d.polygon(pts, fill=fill)
        d.line(pts + [pts[0]], fill=outline, width=2, joint='curve')
    # Rear stabilizers are distinctive for each of the three original types.
    polygon([(tail - 19, mid - 2), (tail - 4, mid - 8), (tail - 1, mid - 8),
             (tail - 5, mid - 2)], '#4b6b75')
    polygon([(tail - 19, mid + 2), (tail - 4, mid + 8), (tail - 1, mid + 8),
             (tail - 5, mid + 2)], '#2b4554')
    if family == 'tiger':
        for sign in (-1, 1):
            polygon([(x + 33, mid + sign * 2), (x + 52, mid + sign * 9),
                     (x + 59, mid + sign * 9), (x + 53, mid + sign * 2)], '#3b626c')
    if family == 'wolf':
        polygon([(x + 32, mid - 2), (x + 47, mid - 6),
                 (x + 56, mid - 6), (x + 53, mid - 2)], '#46656d')
    polygon([(x, mid), (x + 12, mid - 3), (tail - 1, mid - 3),
             (tail + 2, mid), (tail - 1, mid + 3), (x + 12, mid + 3)], '#617d85')
    d.line((int((x + 13) * S), int((mid - 1.3) * S),
            int((tail - 4) * S), int((mid - 1.3) * S)), fill='#d8e2d4', width=3)
    d.line(((x + 13) * S, (mid + 1) * S, (tail - 4) * S, (mid + 1) * S),
           fill='#314650', width=3)
    polygon([(x, mid), (x + 12, mid - 3), (x + 12, mid + 3)], '#b99a67', '#e1c795')
    for bx in [x + 17, tail - 24, tail - 7]:
        d.line((bx * S, (mid - 3) * S, bx * S, (mid + 3) * S), fill='#233843', width=2)


for y, length, family in [(144, 77, 'hound'), (176, 93, 'wolf'), (208, 109, 'tiger')]:
    row = Image.new('RGBA', base.size)
    d = ImageDraw.Draw(row)
    panel(d, (13, y - 18, 242, y + 15), '#0b1c26e8', '#344e59')
    d.line((164 * S, (y - 15) * S, 164 * S, (y + 11) * S), fill='#324d57', width=1)
    d.line((211 * S, (y - 15) * S, 211 * S, (y + 11) * S), fill='#324d57', width=1)
    draw_missile(row, y, length, family)
    save_png(row,P / f'menu_{family}.png')

headers = Image.new('RGBA',base.size)
hd = ImageDraw.Draw(headers)
text(hd,(184,122),'POWER',20,'#8daeb4')
text(hd,(223,122),'QTY',20,'#8daeb4')
save_png(headers,P/'menu_weapon_headers.png')

lines = (P / 'hires.txt').read_text().splitlines()
atlas_index = sum(line.startswith('<img>') for line in lines)
atlas = Image.new('RGBA', (512, 512))
rules, conditions = [], []
slot = 0


def at(name, data, x, y):
    conditions.append(f'<condition>{name},tileAtPosition,{x},{y},{pattern(data, tile_at(data,x,y))},00000000,Y')


at('menuMissionM', weapons, 16, 32)
at('menuMissionN', weapons, 64, 32)
at('menuMissionOne', weapons, 80, 32)
at('menuMapAnchor', brief, 80, 112)
at('menuSelectAnchor', weapons, 24, 104)
at('menuPowerAnchor', weapons, 144, 120)
for name, y in [('Hound',128),('Wolf',160),('Tiger',192)]:
    at('menu'+name, weapons, 16, y)
# Mesen retains rendered tile anchors while the game disables the PPU to load
# the cockpit. Also check live nametable RAM so art vanishes with the header.
conditions.append(f'<condition>menuHeaderPresent,ppuMemoryCheckConstant,2082,==,{tile_at(weapons,16,32):02X}')
menu = 'menuMissionM&menuMissionN&menuMissionOne&menuHeaderPresent'
map_cond = menu + '&menuMapAnchor'
weapon_cond = menu + '&menuSelectAnchor'
conditions += [
    '<condition>menuMapX0,positionCheckX,>=,40', '<condition>menuMapX1,positionCheckX,<,216',
    '<condition>menuMapY0,positionCheckY,>=,96', '<condition>menuMapY1,positionCheckY,<,224',
    '<condition>menuStatsX,positionCheckX,>=,176', '<condition>menuStatsY,positionCheckY,>=,136',
    '<condition>menuPowerSymbolX,positionCheckX,>=,168',
    '<condition>menuHeaderX,positionCheckX,>=,136',
    '<condition>menuHeaderY0,positionCheckY,>=,120', '<condition>menuHeaderY1,positionCheckY,<,128',
    '<condition>menuMissionNumX0,positionCheckX,>=,72', '<condition>menuMissionNumX1,positionCheckX,<,96',
    '<condition>menuMissionNumY0,positionCheckY,>=,32', '<condition>menuMissionNumY1,positionCheckY,<,40',
    '<condition>menuTypeX0,positionCheckX,>=,32', '<condition>menuTypeX1,positionCheckX,<,48',
    '<condition>menuTypeY,positionCheckY,>=,128',
    '<condition>menuArtX0,positionCheckX,>=,40', '<condition>menuArtX1,positionCheckX,<,168',
]
for name, y in [('Hound',136),('Wolf',168),('Tiger',200)]:
    conditions += [f'<condition>menuArt{name}Y0,positionCheckY,>=,{y}',
                   f'<condition>menuArt{name}Y1,positionCheckY,<,{y+24}']


def glyph(char, color='#b7e6d2', size=25):
    im = Image.new('RGBA', (32,32))
    dr = ImageDraw.Draw(im)
    dr.text((16,16), char, font=ImageFont.truetype(FONT,size), anchor='mm', fill=color)
    return im


def add(key, im, cond, sprite=False):
    global slot
    x,y = slot%16*32, slot//16*32
    assert y < atlas.height
    atlas.alpha_composite(im,(x,y))
    slot += 1
    palette = 'FF280F2A' if sprite else '0F2A0F0F'
    rules.append(f'[{cond}]<tile>{atlas_index},{key},{palette},{x},{y},1,Y')


def blank(key, cond):
    rules.append(f'[{cond}]<tile>0,{key},0F2A0F0F,0,0,1,Y')


# Map markers use their original tile occurrence, preserving their visibility.
for ty in range(12,28):
    for tx in range(5,27):
        pixels = native_map[(ty-12)*8:(ty-11)*8,(tx-5)*8:(tx-4)*8]
        if np.any(pixels == 0x0f):
            mask = Image.fromarray((pixels == 0x0f).astype('uint8')*255).resize((32,32),Image.Resampling.LANCZOS)
            im = Image.new('RGBA',(32,32),'#edc78b');im.putalpha(mask)
            add(pattern(brief,tile_at(brief,tx*8,ty*8)),im,
                map_cond+'&menuMapX0&menuMapX1&menuMapY0&menuMapY1')
for t in set(brief['nt'][y*32+x] for y in range(12,28) for x in range(5,27)):
    blank(pattern(brief,t),map_cond+'&menuMapX0&menuMapX1&menuMapY0&menuMapY1')

# Remove original missile outlines only in their original diagram windows.
for name, y in [('Hound',136),('Wolf',168),('Tiger',200)]:
    cond=weapon_cond+f'&menuArtX0&menuArtX1&menuArt{name}Y0&menuArt{name}Y1'
    for t in set(weapons['nt'][yy*32+x] for yy in range(y//8,(y+24)//8) for x in range(5,22)):
        blank(pattern(weapons,t),cond)

# Numeric positions take precedence over shared O/0, I/1, and S/5 patterns.
for t in set(weapons['nt'][15*32+17:15*32+30]):
    blank(pattern(weapons,t),weapon_cond+'&menuHeaderX&menuHeaderY0&menuHeaderY1')
for number in range(10):
    for region in ['menuStatsX&menuStatsY','menuMissionNumX0&menuMissionNumX1&menuMissionNumY0&menuMissionNumY1',
                   'menuTypeX0&menuTypeX1&menuTypeY']:
        add(pattern(weapons,number+1),glyph(str(number),'#d9efd9'),menu+'&'+region)
letters={0x10+i:chr(65+i) for i in range(26) if i!=14}
letters.update({1:'O',2:'I',6:'S',0x18:':',0x0b:"'",0x0c:'.',0x0e:'!',0x3e:'-'})
seen=set()
for t,char in letters.items():
    key=pattern(weapons,t)
    if key in seen:continue
    seen.add(key)
    add(key,glyph(char),menu)
add(pattern(weapons,tile_at(weapons,168,144)),glyph('×','#90b7ac',21),weapon_cond+'&menuPowerSymbolX&menuStatsY')
# The cursor remains a native sprite and retains its original input response.
cursor=Image.new('RGBA',(32,32));cd=ImageDraw.Draw(cursor)
cd.polygon([(5,5),(27,16),(5,27)],fill='#e6bc78',outline='#fff0c8')
add(pattern(weapons,256+46),cursor,weapon_cond,True)

# Clear only flat background tile patterns in the scoped mission menu.
for t in set(weapons['nt'][:960]):
    raw=weapons['chr'][t*16:(t+1)*16]
    if all(v==raw[0] for v in raw[:8]) and all(v==raw[8] for v in raw[8:]) and raw[0] in (0,255) and raw[8] in (0,255):
        blank(pattern(weapons,t),menu)
save_png(atlas,P/'menu_ui.png')
backgrounds=[f'[{menu}]<background>menu_console.png,1,0,0,10',
             f'[{map_cond}]<background>menu_map.png,1,0,0,11',
             f'[{weapon_cond}&menuPowerAnchor]<background>menu_weapon_headers.png,1,0,0,14']
for layer,name in enumerate(['Hound','Wolf','Tiger'],11):
    backgrounds.append(f'[{weapon_cond}&menu{name}]<background>menu_{name.lower()}.png,1,0,0,{layer}')
idx=next(i for i,l in enumerate(lines) if l.startswith('<condition>'))
lines[idx:idx]=['<img>menu_ui.png']+conditions
idx=next(i for i,l in enumerate(lines) if '<tile>' in l)
lines[idx:idx]=rules+backgrounds
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
manifest=json.loads((R/'source/build_manifest.json').read_text())
manifest['version']='0.3.0'
manifest['features'].append('Mission-one tactical briefing and native-driven missile selection')
manifest['not_yet_redrawn']=[
    'Later-mission briefing maps and menus' if value=='Briefing map and weapon diagrams' else value
    for value in manifest['not_yet_redrawn']
]
manifest['assets']['briefing_console']='source/briefing_console_master.png'
(R/'source/build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Mission menus:',slot,'native-driven glyphs; geography and selection preserved')
