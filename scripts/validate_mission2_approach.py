"""Validate v0.9.1 against private native captures, decoded HD video and rebuild.

Usage: python3 scripts/validate_mission2_approach.py QA_ROOT --rebuild PACK
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile
import numpy as np
from PIL import Image
from validate_mission2 import compare, video_hashes

R = Path(__file__).resolve().parents[1]
BASE = '2d0953ef9dc4c2e1342b2f805e36b6092794e517'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('qa', type=Path)
    ap.add_argument('--rebuild', type=Path, required=True)
    args = ap.parse_args()
    q, p = args.qa, R/'pack'
    report = {'version': '0.9.1', 'base_commit': BASE, 'replays': {}}
    movies = [
        ('close_approach', q/'v091', 'final4', 'before', 2445),
        ('earlier_boss_landing_debrief', q/'v090/boss', 'v091_complete', 'final3', 5877),
    ]
    for name, d, final, before, frames in movies:
        check = compare(d/'native', d/final, d/'native_replay.wav',
                        d/(final+'_replay.wav'), frames)
        for token in ['[HDPack', 'Script error', 'handshake timeout', 'finalization timeout']:
            assert token not in (d/(final+'.log')).read_text(), (name, token)
        audit = json.loads((d/(final+'_audit.json')).read_text())
        old = json.loads((d/(before+'_audit.json')).read_text())
        assert audit['video_meta']['width'] == 1024
        assert audit['video_meta']['height'] == 960
        assert audit['video_frames'] in (frames-1, frames-2)
        colors = ['native_blue_frames', 'native_green_hud_frames',
                  'native_green_world_frames', 'native_green_meter_frames',
                  'native_fighter_color_frames']
        for field in colors:
            assert not audit[field], (name, field, audit[field][:12])
        # The left cockpit panel is unchanged by this build. Its live counters
        # establish video alignment even when capture omits an endpoint.
        a, b = old['unchanged_panel_sha256'], audit['unchanged_panel_sha256']
        offsets = [o for o in (0, 1) if a[o:o+min(len(a)-o, len(b))]
                   == b[:min(len(a)-o, len(b))]]
        assert len(offsets) == 1, (name, offsets)
        first = old['first_input_frame']+offsets[0]
        assert audit['first_input_frame'] == first
        check.update({
            'actual_hd_video': audit['video_meta'], 'first_video_input': first,
            'last_video_input': first+audit['video_frames']-1,
            'unchanged_left_cockpit_alignment': True,
            'color_audit_frame_counts': {k: len(audit[k]) for k in colors},
        })
        if name == 'earlier_boss_landing_debrief':
            # Generate these with -an -pix_fmt rgb24; audio has a separate PCM check.
            a, b = video_hashes(d/'final3.md5'), video_hashes(d/'v091_complete.md5')
            assert len(a) == old['video_frames'] and len(b) == audit['video_frames']
            changed = [i+first for i, (x, y) in enumerate(zip(a[offsets[0]:], b)) if x != y]
            assert changed
            tr = np.fromfile(d/'native/trace.bin', np.uint8).reshape(-1, 4384)

            def combat(r):
                return r[0x30] == 2 and r[0x18] == 7 and r[0x9f] == 0

            # End-frame RAM can already describe the next rendered scene.
            assert all(combat(tr[n-1]) or combat(tr[n-2]) for n in changed)
            check.update({'changed_hd_frames': changed,
                          'unchanged_hd_frames': min(len(a)-offsets[0], len(b))-len(changed),
                          'changes_limited_to_mission2_combat': True})
        report['replays'][name] = check

    old = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, 'pack'],
                                  cwd=R, text=True).splitlines()
    previous = [f for f in old if f.endswith('.png')]
    assert len(previous) == 141
    for f in previous:
        assert (R/f).read_bytes() == subprocess.check_output(['git', 'show', BASE+':'+f], cwd=R), f
    lines = (p/'hires.txt').read_text().splitlines()
    imgs = [l[5:] for l in lines if l.startswith('<img>')]
    assert len(imgs) == len(set(imgs))
    conditions = {l.split(',')[0][11:] for l in lines if l.startswith('<condition>')}
    conditions |= {'hmirror', 'vmirror', 'bgpriority'}
    sizes = {}
    for f in p.glob('*.png'):
        with Image.open(f) as im:
            im.load()
            sizes[f.name] = im.size
    assert len(sizes) == 154
    for line in lines:
        if line.startswith('['):
            assert all(c.lstrip('!') in conditions for c in line[1:line.index(']')].split('&')), line
        if '<tile>' in line:
            v = line.split('<tile>')[1].split(',')
            x, y = map(int, v[3:5])
            w, h = sizes[imgs[int(v[0])]]
            assert 0 <= x <= w-32 and 0 <= y <= h-32, line
        if '<background>' in line:
            assert line.split('<background>')[1].split(',')[0] in sizes, line
    assert not any('<'+t+'>' in '\n'.join(lines) for t in ['patch', 'bgm', 'sfx'])
    files = sorted(f for f in p.iterdir() if f.is_file())
    assert {f.name for f in files} == {f.name for f in args.rebuild.iterdir() if f.is_file()}
    for f in files:
        assert f.read_bytes() == (args.rebuild/f.name).read_bytes(), f.name
    archive = q.parent/'deliverables/Top_Gun_HD_v0.9.1.zip'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {f.name for f in files}
        for f in files:
            assert z.read(f.name) == f.read_bytes(), f.name
    report.update({
        'preserved_v090_pngs': previous, 'decoded_pack_pngs': len(sizes),
        'isolated_rebuild_identical': True, 'rom_or_audio_replacements': False,
        'install_zip': {'filename': archive.name, 'file_count': len(files),
                        'sha256': sha(archive), 'crc_and_pack_bytes_identical': True},
        'visual_review': ['Twelve intact carrier approach sizes and transitions',
                          'Separate native-timed bridge and gun sprites',
                          'Close wake and top-edge scroll seam',
                          'Three missing banked fighter layouts',
                          '1ST TARGET! numeral and original text timing'],
        'limitations': ['Only supplied movie sizes and outcomes are covered.',
                        'Audio-device metadata excluded from CPU state dictionaries; PCM checked separately.',
                        'Exact-color audits supplement visual review; they do not prove all artwork is correct.'],
        'pack_sha256': {f.name: sha(f) for f in files},
    })
    (R/'validation/mission2_approach_v0.9.1.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS: 8,322 native frames and PCM identical; decoded HD color audits clean; '
          '141 prior PNGs preserved; exact rebuild and install ZIP.')


if __name__ == '__main__':
    main()
