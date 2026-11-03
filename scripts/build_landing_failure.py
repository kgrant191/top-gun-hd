"""Keep the painted carrier scene through a native failed-landing water impact.

Crash sprites are render-only additions anchored to the game's original shadow.
Nearby native sprite signatures select all six frames, including the final
frame after the game has already switched to its post-impact pause state.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageOps
from pack_io import save_png

R = Path(__file__).resolve().parents[1]
P, S = R/'pack', R/'source'
M = json.loads((S/'landing_failure_mappings.json').read_text())
L = json.loads((S/'landing_mappings.json').read_text())
lines = (P/'hires.txt').read_text().splitlines()
assert '<img>landing_crash.png' not in lines, 'Rebuild the base pack first'
index = sum(l.startswith('<img>') for l in lines)
# The rendered scene identifies both successful touchdown and water impact.
# Native substates 6/7 also occur during successful cockpit rollout, so the
# side-scene signature is essential to keep that approved sequence unchanged.
extended = []
for line in lines:
    extended.append(line)
    if line.startswith('[landingMode&carrierSide&sideVisible'):
        extended.append(line.replace('&carrierSide&', '&landingFailureStart&landingFailureEnd&',1))
lines = extended
conditions = [
    '<condition>landingFailureStart,memoryCheckConstant,009F,>=,06',
    '<condition>landingFailureEnd,memoryCheckConstant,009F,<,08',
]
crash = 'landingMode&sideVisible&landingFailureStart&landingFailureEnd'
shadow = L['side_chr'][str(0xe6)]
rules = [f'[{crash}]<tile>0,{shadow},FF10000F,0,0,1,N']
additions = []
atlas = Image.new('RGBA',(1024,1024))
master = Image.open(S/'landing_crash_master.png').convert('RGBA')
cw, ch = master.width//3, master.height//2
art = []
for stage, width in enumerate([64,112,128,128,120,112]):
    cell = master.crop(((stage%3)*cw,(stage//3)*ch,(stage%3+1)*cw,(stage//3+1)*ch))
    box = cell.getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox()
    sprite = ImageOps.contain(cell.crop(box),(width,128),Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA',(128,160))
    canvas.alpha_composite(sprite,((128-sprite.width)//2,144-sprite.height))
    art.append(canvas)

# Remove only the original crash-effect keys within the failure side scene.
for pattern,palette in sorted({(t['pattern'],e['palette']) for e in M['layouts'] for t in e['tiles']}):
    rules.append(f'[{crash}]<tile>0,{pattern},{palette},0,0,1,N')

slot = 0
for row in range(5):
    for col in range(4):
        dx, dy = -12+col*8, -40+row*8
        key = hashlib.sha256(f'TopGunWaterImpactPiece{col}_{row}'.encode()).hexdigest()[:32].upper()
        additions.append(f'<addition>{shadow},FF10000F,{dx},{dy},{key},FF10000F,N')
        for stage, entry in enumerate(M['layouts']):
            names = []
            for j, sig in enumerate(entry['signature']):
                name = f'waterImpact{stage}_{row}_{col}_{j}'; names.append(name)
                conditions.append(f'<condition>{name},spriteNearby,{sig["x"]-dx},{sig["y"]-dy},{sig["pattern"]},{entry["palette"]},N')
            x,y = slot%32*32,slot//32*32;slot+=1
            atlas.alpha_composite(art[stage].crop((col*32,row*32,col*32+32,row*32+32)),(x,y))
            rules.append(f'[{crash}&'+ '&'.join(names)+f']<tile>{index},{key},FF10000F,{x},{y},1,N')
        # Additions cannot alter any other scene or persist after native spray.
        rules.append(f'<tile>0,{key},FF10000F,0,0,1,N')

save_png(atlas,P/'landing_crash.png')
i = max(i for i,l in enumerate(lines) if l.startswith('<img>'))+1
lines[i:i] = ['<img>landing_crash.png']+conditions+additions
i = next(i for i,l in enumerate(lines) if '<tile>' in l)
lines[i:i] = rules
lines[0] = '# Top Gun HD v0.7.1 - successful landing and water-impact coverage'
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
print('Failed landing:',len(M['layouts']),'native crash stages;',slot,'detail tiles')
