"""Validate v0.5.1 against private native, v0.5.0 and final replay outputs.

Usage: python3 scripts/validate_horizon.py BANK_WORK ENVIRONMENT_WORK
Private replays/captures are not needed for rebuilding the installable pack.
"""
from pathlib import Path
import argparse
import json
import numpy as np
from PIL import Image
from validate_environment import parity

ROOT = Path(__file__).resolve().parents[1]


def preserved_viewports(captures, before, after, intro_end=0):
    cockpit = intro = 0
    for p in sorted((captures / before).glob('*.png')):
        if not p.stat().st_size:
            continue
        a = np.array(Image.open(p).convert('RGB'))
        b = np.array(Image.open(captures / after / p.name).convert('RGB'))
        assert np.array_equal(a[512:], b[512:]), p.name
        cockpit += 1
        if int(p.stem) < intro_end:
            assert np.array_equal(a, b), p.name
            intro += 1
    return {'unchanged_cockpit_checkpoints': cockpit,
            'unchanged_intro_checkpoints': intro}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bank_work', type=Path)
    parser.add_argument('environment_work', type=Path)
    args = parser.parse_args()
    bank, env = args.bank_work, args.environment_work
    report = {'version': '0.5.1',
              'base_commit': '9da7d3df6267525d13f228328d614bc6dbf12cac'}
    report['cloud_turns_and_pitch'] = parity(bank / 'captures', 'bank_native', 'bank_final', 1020)
    report['landing_controller_inputs'] = parity(bank / 'captures', 'ocean_native', 'ocean_final', 4520)
    report['opening_takeoff_clouds'] = parity(env / 'captures', 'env_native', 'env_bank_final', 3017)
    report['combat_to_landing'] = parity(env / 'combat/captures', 'combat_native', 'combat_bank_final', 8253)
    report['cloud_turn_viewports'] = preserved_viewports(bank / 'captures', 'bank_before', 'bank_final')
    report['opening_viewports'] = preserved_viewports(env / 'captures', 'env_release', 'env_bank_final', 1518)
    report['combat_viewports'] = preserved_viewports(env / 'combat/captures', 'combat_final', 'combat_bank_final')
    bank_coverage = {}
    for name, start in [('bank_native', 0), ('ocean_native', 3500)]:
        trace = np.fromfile(bank / f'captures/{name}/trace.bin', np.uint8).reshape(-1, 4384)
        stages = sorted(set(trace[start:, 0x50].view(np.int8).tolist()))
        assert stages == (list(range(-3, 4)) if name == 'bank_native' else [0])
        bank_coverage[name] = {'native_bank_stages': stages,
                               'vertical_scroll_range': [int(trace[start:, 0xfc].min()), int(trace[start:, 0xfc].max())],
                               'world_palette_values': sorted(set(trace[start:, 4352+6].tolist()))}
    report['controller_driven_turn_coverage'] = bank_coverage

    preserved = []
    for p in sorted((env / 'baseline_pack').glob('*.png')):
        assert p.read_bytes() == (ROOT / 'pack' / p.name).read_bytes(), p.name
        preserved.append(p.name)
    assert len(preserved) == 32
    assert (bank / 'baseline_pack/environment_clouds.png').read_bytes() == (ROOT / 'pack/environment_clouds.png').read_bytes()
    report['preserved_pre_environment_pngs'] = preserved
    report['v0_5_0_cloud_sprite_atlas_unchanged'] = True
    lines = (ROOT / 'pack/hires.txt').read_text().splitlines()
    original = (env / 'baseline_pack/hires.txt').read_text().splitlines()
    assert set(l for l in original if l and not l.startswith('#')).issubset(set(lines))
    sizes = {}
    for p in (ROOT / 'pack').glob('*.png'):
        with Image.open(p) as im:
            im.load()
            sizes[p.name] = im.size
    images = [l[5:] for l in lines if l.startswith('<img>')]
    conditions = {l.split(',')[0][11:] for l in lines if l.startswith('<condition>')}
    conditions.update(['hmirror', 'vmirror', 'bgpriority'])
    for line in lines:
        if line.startswith('['):
            assert all(c.lstrip('!') in conditions for c in line[1:line.index(']')].split('&')), line
        if '<tile>' in line:
            p = line.split('<tile>')[1].split(',')
            width, height = sizes[images[int(p[0])]]
            x, y = map(int, p[3:5])
            assert 0 <= x <= width - 32 and 0 <= y <= height - 32
        if '<background>' in line:
            assert line.split('<background>')[1].split(',')[0] in sizes
    assert not any('<' + tag + '>' in '\n'.join(lines) for tag in ['patch', 'bgm', 'sfx'])
    report['decoded_pack_pngs'] = len(sizes)
    report['rom_or_audio_replacements'] = False
    report['visual_review'] = [
        'Matched cloud-bank frames reviewed in both directions and after pitch input.',
        'Landing input fixture stays level in native game; no ocean free-turn coverage claimed.',
        'Native blue/white dither masks removed from the painted flight horizon.',
        'Cloud deck extends across the field and fades into sky; no isolated enlarged cloud.',
        'Banked sky uses padded original pixels without a bank-entry scale change.',
    ]
    report['limitations'] = [
        'Mission-one coverage; no full-game, later-mission or refuelling claim.',
        'Native seven-stage bank drives painted shears; this is not a 3D world renderer.',
        'Landing carrier geometry and markings remain native.',
        'HD audio-device metadata excluded from state comparison; PCM compared independently.',
    ]
    if (bank / 'video_report.json').exists():
        report['review_recordings'] = json.loads((bank / 'video_report.json').read_text())
    (ROOT / 'validation/horizon_v0.5.1.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: 16,810 frames of native trace/state and PCM parity.')
    print('PASS: cockpit/intro preserved, seven bank stages exercised, pack references valid.')


if __name__ == '__main__':
    main()
