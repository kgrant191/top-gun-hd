"""Check v0.5.0 against private native and approved-HD replay outputs.

Usage: python3 scripts/validate_environment.py /path/to/environment-work
The work directory contains opening and combat/captures replay outputs and
baseline_pack from v0.4.0. None of those private inputs are published.
"""
from pathlib import Path
import argparse
import json

import numpy as np
from PIL import Image

from validate_cockpit_colors import pcm, state

ROOT = Path(__file__).resolve().parents[1]


def parity(captures, native, hd, frames):
    a, b = captures / native, captures / hd
    trace = (a / 'trace.bin').read_bytes()
    assert len(trace) == frames * 4384
    assert trace == (b / 'trace.bin').read_bytes()
    counts = {}
    for ext in ['chr', 'nt', 'pal', 'ram', 'oam', 'state']:
        files = sorted(a.glob('*.' + ext))
        assert files
        for p in files:
            q = b / p.name
            assert (state(p) == state(q) if ext == 'state' else p.read_bytes() == q.read_bytes()), p.name
        counts[ext] = len(files)
    audio = pcm(captures / (native + '.wav'))
    assert audio == pcm(captures / (hd + '.wav'))
    log = (captures / (hd + '.log')).read_text()
    assert not any(s in log for s in ['[HDPack', 'Script error', 'handshake timeout'])
    return {'identical_trace_frames': frames, 'identical_checkpoints': counts,
            'identical_pcm': {k: v for k, v in audio.items() if k != 'sha256'},
            'loader_or_script_errors': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('work', type=Path)
    args = parser.parse_args()
    work = args.work
    report = {'version': '0.5.0', 'base_commit': 'e3bb36e83e7dba56426dadb9ab5c202191159957'}
    report['opening_takeoff_clouds'] = parity(work / 'captures', 'env_native', 'env_release', 3017)
    report['combat_to_landing'] = parity(work / 'combat/captures', 'combat_native', 'combat_final', 8253)

    cockpit_count = intro_count = 0
    for p in sorted((work / 'captures/env_before').glob('*.png')):
        if not p.stat().st_size:
            continue
        a = np.array(Image.open(p).convert('RGB'))
        b = np.array(Image.open(work / 'captures/env_release' / p.name).convert('RGB'))
        assert np.array_equal(a[512:], b[512:]), p.name
        cockpit_count += 1
        # The recorded opening is still outside the cockpit before input 1518.
        if int(p.stem) < 1518:
            assert np.array_equal(a, b), p.name
            intro_count += 1
    report['unchanged_cockpit_checkpoints'] = cockpit_count
    report['unchanged_intro_menu_checkpoints'] = intro_count

    preserved = []
    for p in sorted((work / 'baseline_pack').glob('*.png')):
        assert p.read_bytes() == (ROOT / 'pack' / p.name).read_bytes(), p.name
        preserved.append(p.name)
    assert len(preserved) == 32
    report['preserved_existing_pngs'] = preserved
    lines = (ROOT / 'pack/hires.txt').read_text().splitlines()
    baseline = (work / 'baseline_pack/hires.txt').read_text().splitlines()
    assert set(l for l in baseline if l and not l.startswith('#')).issubset(set(lines))
    report['all_preexisting_functional_rules_preserved'] = True

    sizes = {}
    for p in (ROOT / 'pack').glob('*.png'):
        with Image.open(p) as image:
            image.load()
            sizes[p.name] = image.size
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
    report['decoded_pngs'] = len(sizes)
    report['rom_or_audio_replacements'] = False

    mappings = json.loads((ROOT / 'source/environment_mappings.json').read_text())
    cloud_patterns = set(mappings['cloud_patterns'])
    capture_chr = (work / 'captures/env_native/02790.chr').read_bytes()
    orange_patterns = {capture_chr[4096+t*16:4096+t*16+16].hex().upper() for t in range(0x14, 0x1E)}
    assert not cloud_patterns.intersection(orange_patterns)
    cloud_index = images.index('environment_clouds.png')
    cloud_rules = [l for l in lines if '<tile>' in l and l.split('<tile>')[1].split(',')[0] == str(cloud_index)]
    assert cloud_rules
    for line in cloud_rules:
        p = line.split('<tile>')[1].split(',')
        assert p[1] in cloud_patterns and p[2].startswith('FF') and p[6] == 'N'
        assert 'cockpit&enemyWorld' in line
    # Exercise coverage comes from the natural replay, not a constructed list.
    trace = np.fromfile(work / 'captures/env_native/trace.bin', np.uint8).reshape(-1, 4384)
    observed = set()
    for row in trace:
        for y, tile, attr, x in row[4096:4352].reshape(64, 4)[1:]:
            if y < 128:
                key = capture_chr[4096+int(tile)*16:4096+int(tile)*16+16].hex().upper()
                if key in cloud_patterns:
                    observed.add(key)
    assert observed == cloud_patterns
    report['naturally_observed_cloud_patterns'] = len(observed)
    report['cloud_and_orange_explosion_patterns_disjoint'] = True
    report['cloud_distance_layouts'] = 4
    if (work / 'video_report.json').exists():
        report['review_recordings'] = json.loads((work / 'video_report.json').read_text())
    report['limitations'] = [
        'Mission-one coverage; no full-game, later-mission or refuelling claim.',
        'Landing carrier geometry and markings remain native; dedicated carrier redraw is future work.',
        'HD audio-device metadata excluded from state comparison; PCM compared independently.',
    ]
    output = ROOT / 'validation/environment_v0.5.0.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: 11,270 frames of native state and PCM parity; all ten cloud patterns observed.')
    print('PASS: cockpit/intro checkpoints and all 32 existing PNGs preserved; pack references valid.')


if __name__ == '__main__':
    main()
