"""Scoped refueling corrections and forward-condition resolution for v1.0.1."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def fix_lines(lines):
    assert not any('v101RefuelComplete' in line for line in lines), 'Fix already applied'
    pattern = (ROOT/'captures/baseline/03240.chr').read_bytes()[32:48].hex().upper()
    palettes = sorted({line.split('<tile>',1)[1].split(',')[2] for line in lines
                       if '<tile>' in line and pattern in line
                       and line.split('<tile>',1)[1].split(',')[2].startswith('0F2A0A')})
    # The native I/1 tile is shared. Override only the I cell in the completion
    # message, retaining numeric counters and all other flight-display rules.
    definitions = [
        '<condition>v101RefuelComplete,memoryCheckConstant,009F,==,06',
        '<condition>v101RefuelI_X,originPositionCheckX,==,136',
        '<condition>v101RefuelI_Y,originPositionCheckY,==,144',
    ]
    images = [line[5:] for line in lines if line.startswith('<img>')]
    flight_index = images.index('flight_ui.png')
    cond = 'cockpit&cockpitBorder&refuelRoute&v101RefuelComplete&v101RefuelI_X&v101RefuelI_Y'
    additions = [f'[{cond}]<tile>{flight_index},{pattern},{pal},32,160,1,N' for pal in palettes]
    # The connected pose was captured during Mission 3 and mapped there and
    # in Mission 4, but omitted from Mission 2. Reuse the approved tile art.
    for line in lines:
        if line.startswith('[') and '<tile>' in line:
            tokens = line[1:line.index(']')].split('&')
            if 'missionThree' in tokens and 'm3BoomConnected' in tokens:
                additions.append(line.replace('missionThree','missionTwo'))
    # Install specific matches before generic/default alternatives.
    first = next(i for i,line in enumerate(lines) if '<tile>' in line)
    lines = lines[:first]+definitions+additions+lines[first:]
    # Mesen resolves conditions as it reads each rule. Move only definitions
    # used before declaration; keep rule order and later redefinitions intact.
    first_defs = {}
    for i,line in enumerate(lines):
        if line.startswith('<condition>'):
            first_defs.setdefault(line[11:].split(',')[0], (i,line))
    known = {'hmirror','vmirror'}
    moved = set(); output = []; resolved = 0
    for i,line in enumerate(lines):
        if i in moved: continue
        if line.startswith('<condition>'):
            known.add(line[11:].split(',')[0])
        if line.startswith('['):
            for token in line[1:line.index(']')].split('&'):
                name = token.lstrip('!')
                if name not in known:
                    assert name in first_defs, f'Undefined condition: {name}'
                    idx, definition = first_defs[name]
                    assert idx > i
                    output.append(definition);moved.add(idx);known.add(name);resolved += 1
        output.append(line)
    return output, {'completion_palettes':len(palettes),'mission2_boom_rules':len(additions)-len(palettes),'promoted_conditions':resolved}


if __name__=='__main__':
    path=ROOT/'pack/hires.txt'
    lines,summary=fix_lines(path.read_text().splitlines())
    path.write_text('\n'.join(lines)+'\n')
    print(summary)
