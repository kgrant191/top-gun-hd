"""Validate v0.3.1 using the supplied replay and a short native impact replay.

Usage: python3 scripts/validate_cockpit_colors.py <validation-work-root> --movie <user-movie>
See source/COCKPIT_COLOR_NOTES.md for capture names and setup.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import wave
import zipfile

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FRAME_BYTES = 4384


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pcm(path):
    with wave.open(str(path)) as stream:
        return {'channels': stream.getnchannels(), 'sample_width': stream.getsampwidth(),
                'sample_rate': stream.getframerate(), 'sample_frames': stream.getnframes(),
                'sha256': hashlib.sha256(stream.readframes(stream.getnframes())).hexdigest()}


def state(path):
    return dict(line.split('=', 1) for line in path.read_text().splitlines()
                if not line.startswith('hdAudioDevice.'))


def compare(captures, native, hd, frames):
    a, b = captures / native, captures / hd
    assert (a / 'trace.bin').stat().st_size == frames * FRAME_BYTES
    assert (a / 'trace.bin').read_bytes() == (b / 'trace.bin').read_bytes()
    checkpoints = {}
    for ext in ['ram', 'oam', 'chr', 'nt', 'pal', 'state']:
        files = sorted(a.glob('*.' + ext))
        assert files
        for p in files:
            q = b / p.name
            assert q.exists(), q.name
            assert (state(p) == state(q) if ext == 'state' else p.read_bytes() == q.read_bytes()), p.name
        checkpoints[ext] = len(files)
    audio = pcm(captures / (native + '.wav'))
    assert audio == pcm(captures / (hd + '.wav'))
    log = (captures / (hd + '.log')).read_text()
    assert not any(s in log for s in ['[HDPack', 'Script error', 'handshake timeout', 'AVI finalization timeout'])
    video = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height,nb_frames', '-of', 'json', str(captures / (hd + '.avi'))
    ]))['streams'][0]
    assert (video['width'], video['height'], int(video['nb_frames'])) == (1024, 960, frames - 1)
    return {'input_and_identical_trace_frames': frames,
            'identical_checkpoint_counts': checkpoints,
            'identical_pcm_audio': {k: v for k, v in audio.items() if k != 'sha256'},
            'hd_video': video, 'loader_or_capture_errors': 0}


def rgb(path):
    with Image.open(path) as im:
        return np.array(im.convert('RGB'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('work_root', type=Path)
    parser.add_argument('--movie', type=Path, required=True, help='Original user-supplied .mmo, kept outside the repository')
    args = parser.parse_args()
    work = args.work_root
    with zipfile.ZipFile(args.movie) as movie:
        assert len(movie.read('Input.txt').splitlines()) == 2054
    captures = work / 'captures'
    report = {'version': '0.3.1', 'base_commit': 'afef647b114539c8e1a84f3e1df9933b74d7280e',
              'emulator': 'User-supplied MesenCE 2.2.1 Linux x64'}
    report['runway_flight_clouds'] = compare(captures, 'color_native', 'color_fixed_final', 2054)
    report['impact'] = compare(work / 'impact/captures', 'impact_native', 'impact_fixed', 180)

    # The entire windshield cap stays equal to the intended metal surface,
    # including the native sky/sea/cloud color changes between checkpoints.
    data = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(captures / 'color_fixed_final.avi'),
        '-vf', 'crop=1024:8:0:512', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'
    ])
    rows = np.frombuffer(data, np.uint8).reshape(-1, 8, 1024, 3)
    assert len(rows) == 2053
    assert np.all(rows == rgb(ROOT / 'pack/cockpit.png')[512:520])
    report['windshield_cap_identical_to_metal_for_all_video_frames'] = len(rows)

    # Outside the first coaming segment, only the 2x1 native-pixel tick changes.
    reviewed = []
    for p in sorted((captures / 'color_before').glob('*.png')):
        if not p.stat().st_size:
            continue
        a, b = rgb(p), rgb(captures / 'color_fixed_final' / p.name)
        changed = np.any(a != b, axis=2)
        changed[512:576] = False
        changed[756:760, 248:256] = False
        assert not changed.any(), p.name
        assert np.all(b[756:760, 248:256] == [206, 219, 212]), p.name
        reviewed.append(int(p.stem))
    assert reviewed
    report['checkpoint_frames_with_only_requested_visual_changes'] = reviewed
    report['right_attitude_tick_rgb'] = [206, 219, 212]

    # Preserve the established native impact sequence and registration.
    expected = [0, 0] + [-4, 4] * 8 + [0, 0]
    shifts = []
    variants = {0: 'cockpit.png', -4: 'cockpit_left.png', 4: 'cockpit_right.png'}
    for n in range(75, 95):
        frame = rgb(work / 'impact/captures/impact_fixed' / f'{n:05d}.png')[512:520]
        matches = [dx for dx, name in variants.items() if np.array_equal(frame, rgb(ROOT / 'pack' / name)[512:520])]
        assert len(matches) == 1, (n, matches)
        shifts.append(matches[0])
    assert shifts == expected, shifts
    report['impact']['checked_frames'] = [75, 94]
    report['impact']['windshield_hd_pixel_offsets'] = shifts

    changed_assets = []
    preserved = {}
    for p in sorted((work / 'baseline_pack').glob('*.png')):
        q = ROOT / 'pack' / p.name
        if p.read_bytes() != q.read_bytes():
            changed_assets.append(p.name)
        else:
            preserved[p.name] = digest(p)
    assert changed_assets == ['cockpit.png', 'cockpit_left.png', 'cockpit_right.png', 'panel_details.png']
    report['changed_existing_pngs'] = changed_assets
    report['preserved_pngs'] = list(preserved)
    report['new_pngs'] = ['windshield_cap.png', 'windshield_cap_left.png', 'windshield_cap_right.png']
    pngs = list((ROOT / 'pack').glob('*.png'))
    assert len(pngs) == 30
    for p in pngs:
        with Image.open(p) as im:
            im.load()
    report['complete_png_files'] = len(pngs)
    lines = (ROOT / 'pack/hires.txt').read_text().splitlines()
    imgs = [line[5:] for line in lines if line.startswith('<img>')]
    for line in lines:
        if '<tile>' in line:
            t = line.split('<tile>')[1].split(',')
            with Image.open(ROOT / 'pack' / imgs[int(t[0])]) as im:
                x, y = map(int, t[3:5])
                assert 0 <= x <= im.width - 32 and 0 <= y <= im.height - 32
        if '<background>' in line:
            assert (ROOT / 'pack' / line.split('<background>')[1].split(',')[0]).is_file()
    assert not any('<' + tag + '>' in '\n'.join(lines) for tag in ['patch', 'bgm', 'sfx'])
    report['rom_or_audio_replacements'] = False
    report['pack_files'] = [p.name for p in sorted((ROOT / 'pack').iterdir()) if p.is_file()]
    report['limitations'] = [
        'Supplied opening/combat replay plus the first 180 frames of the previous impact movie.',
        'No new later-mission, landing, refuelling or full-game QA claim.',
        'HD-only audio-device metadata excluded from exported-state comparison.',
    ]
    output = ROOT / 'validation/cockpit_colors_v0.3.1.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: 2054 supplied replay frames + 180 impact frames; state and PCM audio identical.')
    print('PASS: windshield edge stable across every recorded flight frame; impact registration preserved.')
    print('PASS: checkpoint changes confined to coaming and right tick; 23 previous PNGs preserved.')
    print('Report:', output.relative_to(ROOT))


if __name__ == '__main__':
    main()
