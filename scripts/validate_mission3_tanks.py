"""Validate the recorded tank fix and its scope; private QA is not packaged."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import subprocess
import zipfile
import numpy as np
from PIL import Image
from validate_mission2 import compare

R = Path(__file__).resolve().parents[1]
BASE = 'db32be23953e31ff5fb003bec59e4014ef847738'


def trace(path):
    count = (path / 'trace.bin').stat().st_size // 4384
    ram = np.memmap(path / 'trace.bin', np.uint8, mode='r', shape=(count, 4384))
    chr_data = np.memmap(path / 'chr.bin', np.uint8, mode='r', shape=(count, 8192))
    return ram, chr_data


def affected(path, layout):
    ram, chr_data = trace(path)
    patterns = {bytes.fromhex(tile['pattern']): tile for tile in layout['tiles']}
    bounds = {}
    for index, row in enumerate(ram):
        if row[0x30] != 3 or row[0x18] != 7 or row[0x9f] != 0:
            continue
        sprites = []
        for y, tile, attr, x in row[4096:4352].reshape(64, 4):
            if y >= 127:
                continue
            pattern = bytes(chr_data[index, 4096 + int(tile)*16:4112 + int(tile)*16])
            palette = 'FF' + bytes(row[4352 + 16 + int(attr & 3)*4 + 1:
                                       4352 + 16 + int(attr & 3)*4 + 4]).hex().upper()
            sprites.append((int(x), int(y)+1, int(attr), pattern, palette))
        for x, y, attr, pattern, palette in sprites:
            if attr & 0xc0 or pattern not in patterns or palette not in ('FF101B0F', 'FF381A0F'):
                continue
            tile = patterns[pattern]
            if tile['tile'] == 0xf8:
                # F8 has no new fallback; it requires the complete signature.
                anchors = [layout['tiles'][0], layout['tiles'][-1]]
                if not all(any(sx == x + anchor['x'] - tile['x']
                               and sy == y + anchor['y'] - tile['y']
                               and sp == bytes.fromhex(anchor['pattern']) and pal == palette
                               for sx, sy, sa, sp, pal in sprites) for anchor in anchors):
                    continue
            bounds.setdefault(index + 1, []).append([x*4, y*4, (x+8)*4, (y+8)*4])
    return bounds


def video_difference(before, after, bounds):
    def reader(path):
        return subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(path),
                                 '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    a, b = reader(before), reader(after)
    # This capture flushes 899 images for 901 input callbacks. Image 1
    # corresponds to trace input 1; the last two callbacks have no image.
    frame, changed = 0, []
    try:
        while True:
            first, second = a.stdout.read(1024*960*3), b.stdout.read(1024*960*3)
            if not first or not second:
                assert not first and not second
                break
            frame += 1
            assert len(first) == len(second) == 1024*960*3
            if first == second:
                continue
            changed.append(frame)
            assert frame in bounds, ('Unexpected changed frame', frame)
            diff = np.any(np.frombuffer(first, np.uint8).reshape(960, 1024, 3)
                          != np.frombuffer(second, np.uint8).reshape(960, 1024, 3), axis=2)
            for x0, y0, x1, y1 in bounds[frame]:
                diff[max(0,y0):min(960,y1), max(0,x0):min(1024,x1)] = False
            assert not diff.any(), ('Pixels changed outside native tank bounds', frame)
        assert a.wait() == b.wait() == 0
    finally:
        for process in (a, b):
            if process.poll() is None:
                process.kill()
    assert frame == 899 and changed == sorted(bounds), (frame, len(changed), len(bounds))
    return {'frames': frame, 'changed_tank_frames': len(changed),
            'unchanged_frames': frame-len(changed), 'all_changes_within_native_tank_tiles': True,
            'changed_inputs': changed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('qa', type=Path)
    parser.add_argument('--zip', type=Path, required=True)
    args = parser.parse_args()
    q, pack = args.qa, R / 'pack'
    report = {'version': '0.10.1', 'base_commit': BASE}
    report['replay'] = compare(q/'tank_native', q/'tank_fixed', q/'tank_native_replay.wav',
                               q/'tank_fixed_replay.wav', 901)
    assert (q/'tank_native/chr.bin').read_bytes() == (q/'tank_fixed/chr.bin').read_bytes()
    for name in ['tank_native', 'tank_fixed']:
        log = (q/(name+'.log')).read_text()
        assert not any(token in log for token in ['[HDPack', 'Script error', 'handshake timeout', 'finalization timeout'])
    layout = json.loads((R/'source/mission3_tank_close.json').read_text())['layout']
    assert not affected(q/'native', layout)
    report['earlier_mission3_trace_frames_with_new_rules_active'] = 0
    bounds = affected(q/'tank_native', layout)
    report['video'] = video_difference(q/'tank_before_replay.avi', q/'tank_fixed_replay.avi', bounds)
    old = subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines()
    current = (pack/'hires.txt').read_text().splitlines()
    added = list((collections.Counter(current[1:])-collections.Counter(old[1:])).elements())
    assert not collections.Counter(old[1:])-collections.Counter(current[1:])
    assert len(added) == 70
    assert sum(line.startswith('<condition>m3TankClose') for line in added) == 36
    keys = {tuple(line.split('<tile>')[1].split(',')[1:3]) for line in old if '<tile>' in line}
    for line in added:
        if '<tile>' in line:
            assert 'missionThree&mission2Flight&rearCombatPhase&enemyWorld&!hmirror&!vmirror' in line
            assert tuple(line.split('<tile>')[1].split(',')[1:3]) in keys
    pngs = sorted(pack.glob('*.png'))
    assert len(pngs) == 171
    for path in pngs:
        assert path.read_bytes() == subprocess.check_output(['git','show',BASE+':pack/'+path.name],cwd=R)
    images = [line[5:] for line in current if line.startswith('<img>')]
    names = {line.split(',')[0][11:] for line in current if line.startswith('<condition>')}
    names |= {'hmirror', 'vmirror', 'bgpriority'}
    for line in added:
        if line.startswith('['):
            assert all(name.lstrip('!') in names for name in line[1:line.index(']')].split('&'))
        if '<tile>' in line:
            fields = line.split('<tile>')[1].split(',')
            with Image.open(pack/images[int(fields[0])]) as im:
                assert 0 <= int(fields[3]) <= im.width-32 and 0 <= int(fields[4]) <= im.height-32
    assert (q/'tank_rebuild/pack/hires.txt').read_bytes() == (pack/'hires.txt').read_bytes()
    with zipfile.ZipFile(args.zip) as archive:
        assert set(archive.namelist()) == {path.name for path in pack.iterdir() if path.is_file()}
        for path in pack.iterdir():
            if path.is_file():
                assert archive.read(path.name) == path.read_bytes()
    report.update({'unchanged_pngs':171, 'new_exact_keys':0, 'added_rules':34,
                   'added_conditions':36, 'removed_rules':0, 'rebuild_identical':True,
                   'installer_sha256':hashlib.sha256(args.zip.read_bytes()).hexdigest(),
                   'limitations':['Recorded close tank views only; unrecorded views and outcomes need footage.',
                                  'Earlier long movie checked by evaluating all added rules over its native trace.',
                                  'Audio-device state excluded from CPU state comparison; PCM verified separately.']})
    (R/'validation/mission3_tanks_v0.10.1.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:', report['video'], '; 901 native frames and PCM identical; 171 PNGs unchanged')


if __name__ == '__main__':
    main()
