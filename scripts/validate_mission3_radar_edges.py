"""Compare the radar correction against native state and the v0.11.0 videos."""
from pathlib import Path
import argparse
import json
import subprocess
import numpy as np
from PIL import Image
from validate_mission2 import compare, digest

R = Path(__file__).resolve().parents[1]
BASE = '9ba93d6'
CLIPS = {'plane': 389, 'plane2': 290, 'wall': 665, 'radar': 731, 'radar2': 329, 'boss': 2889}


def hashes(path):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:v:0', '-f', 'framemd5', '-'], text=True)
    return [line.rsplit(',', 1)[-1] for line in data.splitlines() if line and not line.startswith('#')]


def radar_pixels(q, clip, count):
    """Every changed video pixel must lie in an added cell of a live radar."""
    trace = np.fromfile(q / f'{clip}_native/trace.bin', np.uint8).reshape(-1, 4384)
    chrs = np.memmap(q / f'{clip}_native/chr.bin', np.uint8, mode='r', shape=(count, 8192))
    mapping = json.loads((R / 'source/mission3_radar_edges_build.json').read_text())
    offsets = {}
    for entry in mapping['coverage']:
        source = json.loads((R / 'source' / entry['source']).read_text())
        group = source.get('objects', source.get('new_layouts'))
        layout = next(e for e in group if e['id'] == entry['layout'])
        anchor = layout['tiles'][0]
        offsets.setdefault(entry['anchor'], []).append((entry['cell'][0]-anchor['x'], entry['cell'][1]-anchor['y']))

    def raw(mode):
        return subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(q / f'{clip}_{mode}_replay.avi'), '-map', '0:v:0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)

    before, after = raw('release'), raw('edges')
    size = 1024 * 960 * 3
    changed, pixels, n = 0, 0, 0
    try:
        while True:
            a, b = before.stdout.read(size), after.stdout.read(size)
            if not a or not b:
                # The asynchronous recorder may omit the final frame. Native
                # traces/audio still cover every input; compare common video.
                assert len(a) in {0, size} and len(b) in {0, size}
                assert not before.stdout.read(size) and not after.stdout.read(size)
                break
            assert len(a) == size
            n += 1
            if a == b:
                continue
            diff = np.any(np.frombuffer(a, np.uint8).reshape(960,1024,3) != np.frombuffer(b, np.uint8).reshape(960,1024,3), axis=2)
            allowed = np.zeros((960, 1024), bool)
            # Video starts at input 2. End-frame OAM may describe the following
            # rendered frame, so include the adjacent trace snapshots.
            for frame in range(max(0, n-1), min(count, n+2)):
                row = trace[frame]
                for sy, tile, attr, sx in row[4096:4352].reshape(64,4):
                    sy, tile, attr, sx = map(int, (sy, tile, attr, sx))
                    if sy >= 127 or attr & 192:
                        continue
                    pal = 'FF' + bytes(row[4352+16+(attr&3)*4+1:4352+16+(attr&3)*4+4]).hex().upper()
                    if pal not in {'FF101B0F', 'FF381A0F'}:
                        continue
                    key = chrs[frame, 4096+tile*16:4096+tile*16+16].tobytes().hex().upper()
                    for dx, dy in offsets.get(key, []):
                        x, y = (sx+dx)*4, (sy+1+dy)*4
                        if x < 1024 and x+32 > 0 and y < 960 and y+32 > 0:
                            allowed[max(0,y):min(960,y+32),max(0,x):min(1024,x+32)] = True
            assert not np.any(diff & ~allowed), (clip, n, int((diff & ~allowed).sum()))
            changed += 1
            pixels += int(diff.sum())
    finally:
        before.stdout.close()
        after.stdout.close()
        assert before.wait() == after.wait() == 0
    assert count-2 <= n <= count and changed > 0
    return {'video_frames': n, 'changed_frames': changed, 'changed_pixels': pixels, 'all_changes_inside_missing_radar_cells': True}


def validate(q, rebuild):
    p = R / 'pack'
    report = {'version': '0.11.1', 'base_commit': BASE, 'replays': {}}
    for clip, frames in CLIPS.items():
        a, b = q / f'{clip}_native', q / f'{clip}_edges'
        entry = compare(a, b, q / f'{clip}_native_replay.wav', q / f'{clip}_edges_replay.wav', frames)
        assert (a / 'chr.bin').read_bytes() == (b / 'chr.bin').read_bytes()
        assert (q / f'{clip}_edges_replay.end').exists()
        log = (q / f'{clip}_edges.log').read_text()
        assert not any(s in log for s in ['[HDPack', 'Script error', 'handshake timeout'])
        if clip in {'radar', 'radar2'}:
            entry.update(radar_pixels(q, clip, frames))
        else:
            old, new = hashes(q / f'{clip}_release_replay.avi'), hashes(q / f'{clip}_edges_replay.avi')
            common = min(len(old), len(new))
            assert frames-2 <= common <= max(len(old), len(new)) <= frames, clip
            assert old[:common] == new[:common], clip
            entry['identical_hd_video_frames'] = common
        report['replays'][clip] = entry
        print('PASS replay:', clip, flush=True)
    oldpaths = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines()
    preserved = [f for f in oldpaths if f.endswith('.png')]
    assert len(preserved) == 179
    for file in preserved:
        assert subprocess.check_output(['git','show',BASE+':'+file],cwd=R) == (R / file).read_bytes(), file
    oldlines = subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines()
    lines = (p / 'hires.txt').read_text().splitlines()
    remaining = iter(lines[1:])
    for old in oldlines[1:]:
        assert any(current == old for current in remaining), old
    imgs = [line[5:] for line in lines if line.startswith('<img>')]
    assert len(imgs) == len(set(imgs))
    names = {line[11:].split(',')[0] for line in lines if line.startswith('<condition>')} | {'hmirror','vmirror','bgpriority'}
    sizes = {}
    for file in p.glob('*.png'):
        with Image.open(file) as im:
            im.load()
            sizes[file.name] = im.size
    for line in lines:
        if line.startswith('['):
            assert all(name.lstrip('!') in names for name in line[1:line.index(']')].split('&')), line
        if '<tile>' in line:
            v = line.split('<tile>')[1].split(',')
            x,y = map(int,v[3:5]);w,h = sizes[imgs[int(v[0])]]
            assert 0 <= x <= w-32 and 0 <= y <= h-32, line
    assert not any('<'+tag+'>' in '\n'.join(lines) for tag in ['patch','bgm','sfx'])
    assert {f.name for f in p.iterdir()} == {f.name for f in rebuild.iterdir()}
    for file in p.iterdir():
        assert file.read_bytes() == (rebuild / file.name).read_bytes(), file.name
    report.update({'total_identical_input_frames': sum(CLIPS.values()), 'preserved_png_count': 179,
                   'old_rules_preserved_in_order': True, 'isolated_rebuild_identical': True,
                   'pack_sha256': {f.name:digest(f) for f in sorted(p.iterdir()) if f.is_file()}})
    (R / 'validation/mission3_radar_edges_v0.11.1.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 5,293 native inputs, PCM audio, radar-only image changes, 179 preserved PNGs and rebuild.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('qa', type=Path)
    ap.add_argument('--rebuild', type=Path, required=True)
    args = ap.parse_args()
    validate(args.qa, args.rebuild)
