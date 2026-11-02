"""Install the exact reviewed combat atlas and its native matching rules."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def install_stage(stage, atlas_name, source_name):
    pack = ROOT / 'pack'
    definition = pack / 'hires.txt'
    lines = definition.read_text().splitlines()
    image_tag = '<img>' + atlas_name
    if image_tag in lines:
        raise ValueError('Rebuild the base pack before installing combat stages')
    if stage == 'combat_effects' and '<img>enemy_aircraft.png' not in lines:
        raise ValueError('Aircraft rules must be installed before combat effects')
    index = sum(line.startswith('<img>') for line in lines)
    rules = (ROOT / 'source' / (stage + '_rules.txt')).read_text()
    rules = rules.replace('@IMAGE@', str(index)).splitlines()
    source = ROOT / 'source' / source_name
    with Image.open(source) as image:
        image.load()
        if image.mode != 'RGBA' or image.size != (512, 512):
            raise ValueError('Unexpected combat atlas format')
    image_at = max(i for i, line in enumerate(lines) if line.startswith('<img>')) + 1
    lines.insert(image_at, image_tag)
    rule_at = next(i for i, line in enumerate(lines) if '<tile>' in line)
    lines[rule_at:rule_at] = rules
    temporary = pack / (atlas_name + '.tmp')
    temporary.write_bytes(source.read_bytes())
    temporary.replace(pack / atlas_name)
    temporary = definition.with_suffix('.tmp')
    temporary.write_text('\n'.join(lines) + '\n')
    temporary.replace(definition)
    print('Installed reviewed', stage, 'atlas and', len(rules), 'rules/conditions')
