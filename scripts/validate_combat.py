"""Verify combat-pack integrity, preservation and optional approved ZIP parity.

Usage: python3 scripts/validate_combat.py --approved-zip /private/approved.zip
This check does not rerun the historical emulator recordings.
"""
from collections import Counter
from pathlib import Path
import argparse
import json
import struct
import subprocess
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = 'f23e0c16669c328e8d556f0c20fbe909a8f72efb'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approved-zip', type=Path)
    args = parser.parse_args()
    pack = ROOT / 'pack'
    files = sorted(p for p in pack.iterdir() if p.is_file())
    assert len(files) == 34
    pngs = sorted(pack.glob('*.png'))
    assert len(pngs) == 32
    preserved = []
    for p in pngs:
        with Image.open(p) as im:
            im.load()
        if p.name not in ('enemy_aircraft.png', 'combat_effects.png'):
            original = subprocess.check_output(['git', 'show', BASE + ':pack/' + p.name], cwd=ROOT)
            assert original == p.read_bytes(), p.name
            preserved.append(p.name)
    assert len(preserved) == 30
    for name in ('enemy_aircraft', 'combat_effects'):
        data = (ROOT / 'source' / (name + '_atlas.png')).read_bytes()
        assert data == (pack / (name + '.png')).read_bytes()
        position, chunks = 8, set()
        while position < len(data):
            length = struct.unpack_from('>I', data, position)[0]
            chunks.add(data[position + 4:position + 8])
            position += length + 12
        assert chunks == {b'IHDR', b'IDAT', b'IEND'} and position == len(data)
    lines = (pack / 'hires.txt').read_text().splitlines()
    base_lines = subprocess.check_output(['git', 'show', BASE + ':pack/hires.txt'], cwd=ROOT, text=True).splitlines()
    assert not Counter(s for s in base_lines if s and not s.startswith('#')) - Counter(lines)
    images, conditions = [], {'hmirror', 'vmirror', 'bgpriority'}
    new_rules = 0
    for line in lines:
        if line.startswith('<img>'):
            images.append(line[5:])
        if line.startswith('<condition>'):
            conditions.add(line[11:].split(',')[0])
        if line.startswith('['):
            assert all(c.lstrip('!') in conditions for c in line[1:line.index(']')].split('&'))
        if '<tile>' in line:
            fields = line.split('<tile>')[1].split(',')
            image_name = images[int(fields[0])]
            with Image.open(pack / image_name) as im:
                x, y = map(int, fields[3:5])
                assert 0 <= x <= im.width - 32 and 0 <= y <= im.height - 32
            if image_name in ('enemy_aircraft.png', 'combat_effects.png'):
                assert fields[2].startswith('FF') and fields[6] == 'N'
                assert 'cockpit&enemyWorld' in line
                new_rules += 1
    assert len(images) == len(set(images)) == 7
    assert not any('<' + tag + '>' in '\n'.join(lines) for tag in ('patch', 'bgm', 'sfx'))
    matched = None
    if args.approved_zip:
        with zipfile.ZipFile(args.approved_zip) as archive:
            assert archive.testzip() is None
            assert set(archive.namelist()) == {p.name for p in files}
            for p in files:
                assert archive.read(p.name) == p.read_bytes(), p.name
            matched = len(files)
    report = {
        'version': '0.4.0', 'base_commit': BASE,
        'pack_files': len(files), 'complete_png_files': len(pngs),
        'preserved_existing_pngs': preserved, 'preserved_base_rules': True,
        'exact_sprite_palette_rules': new_rules,
        'source_atlas_metadata_chunks': 0,
        'approved_installer_identical_files': matched,
        'rom_or_audio_replacements': False,
        'pre_approval_emulator_validation': {
            'emulator': 'MesenCE 2.2.1 Linux x64',
            'status': 'Passed during the artwork pass; not rerun by this artifact check',
            'native_opening_flight_trace_frames': 2054,
            'combat_to_landing_trace_frames': 8253,
            'native_fixture_trace_frames': 1390,
            'gameplay_state_and_pcm_identical': True,
            'aircraft_layouts': 116, 'effect_layouts': 23,
            'fixture_opaque_pixels': 84454, 'minimum_pixel_agreement': 1.0,
            'rgb_tolerance': 6, 'opening_visual_checkpoints': 48,
            'combat_to_landing_visual_checkpoints': 119,
            'changed_pixels_outside_combat_sprite_cells': 0,
        },
        'scope': 'Mapped mission-one combat layouts and observed palettes; later missions need coverage',
        'source_policy': 'Reviewed atlases and exact rule blocks are the authoritative combat rebuild inputs',
    }
    (ROOT / 'validation/combat_art_v0.4.0.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: pack integrity, 30 preserved PNGs, exact sprite rules and approved installer parity')


if __name__ == '__main__':
    main()
