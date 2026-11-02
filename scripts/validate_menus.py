"""Check menu replay outputs without printing captured state or binary data.

Usage: python3 scripts/validate_menus.py CAPTURES PRESERVED_PACK
The capture names and input-only variants are documented in SCREEN_POLISH_NOTES.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import wave

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FRAMES = 777
TRACE_FRAME_BYTES = 4384


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audio(path):
    with wave.open(str(path)) as stream:
        return {
            'channels': stream.getnchannels(),
            'sample_width': stream.getsampwidth(),
            'sample_rate': stream.getframerate(),
            'sample_frames': stream.getnframes(),
            'pcm_sha256': hashlib.sha256(stream.readframes(stream.getnframes())).hexdigest(),
        }


def state(path):
    return dict(line.split('=', 1) for line in path.read_text().splitlines()
                if not line.startswith('hdAudioDevice.'))


def compare(captures, native, hd):
    a, b = captures / native, captures / hd
    trace_a, trace_b = a / 'trace.bin', b / 'trace.bin'
    assert trace_a.stat().st_size == FRAMES * TRACE_FRAME_BYTES
    assert trace_a.read_bytes() == trace_b.read_bytes(), (native, hd, 'trace')
    counts = {}
    for ext in ['ram', 'oam', 'chr', 'nt', 'pal', 'state']:
        files = sorted(a.glob('*.' + ext))
        assert files
        for p in files:
            q = b / p.name
            assert q.exists(), q.name
            assert (state(p) == state(q) if ext == 'state' else p.read_bytes() == q.read_bytes()), (hd, p.name)
        counts[ext] = len(files)
    native_audio = audio(captures / (native + '.wav'))
    assert native_audio == audio(captures / (hd + '.wav')), (hd, 'audio')
    log = (captures / (hd + '.log')).read_text()
    assert not any(s in log for s in ['[HDPack', 'Script error', 'handshake timeout', 'AVI finalization timeout'])
    avi = captures / (hd + '.avi')
    with avi.open('rb') as stream:
        assert stream.read(4) == b'RIFF', hd
    stream = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height,nb_frames,r_frame_rate', '-of', 'json', str(avi)
    ]))['streams'][0]
    assert (stream['width'], stream['height'], int(stream['nb_frames'])) == (1024, 960, 776)
    return {'native_capture': native, 'hd_capture': hd,
            'identical_trace_frames': FRAMES, 'trace_sha256': sha(trace_a),
            'identical_checkpoints': counts, 'audio_identical': True, 'audio': native_audio,
            'hd_video': stream, 'loader_or_capture_errors': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path)
    parser.add_argument('preserved_pack', type=Path)
    args = parser.parse_args()
    report = {
        'version': '0.3.0', 'base_commit': '135f618af35893614cd921c084e7134f40b0efc7',
        'emulator': 'User-supplied MesenCE 2.2.1 Linux x64',
        'movie': 'reference/Top_Gun_HD_menus.mmo',
        'movie_sha256': sha(ROOT / 'reference/Top_Gun_HD_menus.mmo'),
        'input_frames_per_run': FRAMES,
        'choices': {},
    }
    for choice, native, hd, pulses in [
        ('hound', 'native_original', 'review_final', []),
        ('wolf', 'probe_select', 'wolf_select_hd', [[330, 333]]),
        ('tiger', 'tiger_select_native', 'tiger_final_hd', [[330, 333], [355, 358]]),
    ]:
        result = compare(args.captures, native, hd)
        result['select_button_frames_inclusive'] = pulses
        report['choices'][choice] = result
    pack = ROOT / 'pack'
    preserved = {}
    for p in sorted(args.preserved_pack.glob('*.png')):
        assert p.read_bytes() == (pack / p.name).read_bytes(), p.name
        preserved[p.name] = sha(p)
    assert len(preserved) == 20
    report['preserved_png_sha256'] = preserved
    old_lines = [s for s in (args.preserved_pack / 'hires.txt').read_text().splitlines()
                 if s and not s.startswith('#')]
    lines = (pack / 'hires.txt').read_text().splitlines()
    it = iter(lines)
    assert all(any(line == old for line in it) for old in old_lines)
    report['previous_pack_rules_preserved_in_order'] = True
    imgs = [line[5:] for line in lines if line.startswith('<img>')]
    sizes = {}
    for p in pack.glob('*.png'):
        with Image.open(p) as im:
            sizes[p.name] = im.size
            im.verify()
    for line in lines:
        if '<tile>' in line:
            t = line.split('<tile>')[1].split(',')
            width, height = sizes[imgs[int(t[0])]]
            x, y = map(int, t[3:5])
            assert 0 <= x <= width - 32 and 0 <= y <= height - 32
        for tag in ['<img>', '<background>']:
            if tag in line:
                assert (pack / line.split(tag)[1].split(',')[0]).is_file()
    assert not any('<' + tag + '>' in '\n'.join(lines) for tag in ['patch', 'bgm', 'sfx'])
    report['rom_or_audio_replacements'] = False
    report['pack_png_count'] = len(sizes)
    report['pack_sha256'] = {p.name: sha(p) for p in sorted(pack.iterdir()) if p.is_file()}
    unchanged = []
    for p in sorted((args.captures / 'baseline_hd').glob('*.png')):
        if int(p.stem) >= 581:
            q = args.captures / 'review_final' / p.name
            with Image.open(p) as a, Image.open(q) as b:
                assert a.size == b.size and a.convert('RGBA').tobytes() == b.convert('RGBA').tobytes(), p.name
            unchanged.append(int(p.stem))
    assert unchanged
    report['transition_and_cockpit_checkpoint_frames_identical_to_v021'] = unchanged
    report['state_comparison_note'] = 'All exported emulation fields compared; HD-only hdAudioDevice metadata excluded.'
    report['visual_review'] = [
        'Mission 1 map and carrier marker', 'Three missile diagrams, power and quantity',
        'Hound, Wolf and Tiger selector positions and confirmation visibility', 'Transition back to the preserved cockpit',
    ]
    report['limitations'] = [
        'Mission 1 opening only; no new later-mission, landing or refuelling QA claim.',
        'Recorder begins after initial state load: 777 input/trace frames, 776 video frames.',
        'Full emulator states, traces and raw recordings are local validation inputs, not installable pack files.',
    ]
    output = ROOT / 'validation/menu_validation_v0.3.0.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: 3 choices × 777 identical trace frames; PCM audio and all checkpoints match.')
    print('PASS: 20 previous PNGs and previous rules preserved; transition/cockpit checkpoints:', unchanged)
    print('Report:', output.relative_to(ROOT))


if __name__ == '__main__':
    main()
