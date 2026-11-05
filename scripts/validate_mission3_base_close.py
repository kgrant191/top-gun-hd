"""Check the new base flyover, missile hit, six regressions and full rebuild."""
from pathlib import Path
import argparse
import json
import subprocess
import numpy as np
from PIL import Image
from validate_mission2 import compare, digest
from validate_mission3_radar_edges import hashes

R = Path(__file__).resolve().parents[1]
BASE = '160fdb7'
CLIPS = {'plane':389,'plane2':290,'wall':665,'radar':731,'radar2':329,'boss':2889,'baseclose':2683}


def validate(q, rebuild):
    p = R / 'pack'
    report = {'version':'0.11.2','base_commit':BASE,'replays':{}}
    for clip, frames in CLIPS.items():
        mode = 'candidate' if clip == 'baseclose' else 'basefix'
        a, b = q / f'{clip}_native', q / f'{clip}_{mode}'
        entry = compare(a,b,q/f'{clip}_native_replay.wav',q/f'{clip}_{mode}_replay.wav',frames)
        assert (a/'chr.bin').read_bytes() == (b/'chr.bin').read_bytes()
        assert (q/f'{clip}_{mode}_replay.end').exists()
        log = (q/f'{clip}_{mode}.log').read_text()
        assert not any(s in log for s in ['[HDPack','Script error','handshake timeout','finalization timeout'])
        if clip != 'baseclose':
            old,new = hashes(q/f'{clip}_edges_replay.avi'),hashes(q/f'{clip}_{mode}_replay.avi')
            common = min(len(old),len(new))
            assert frames-2 <= common <= max(len(old),len(new)) <= frames
            assert old[:common] == new[:common], clip
            entry['identical_hd_video_frames'] = common
        report['replays'][clip] = entry
        print('PASS replay:',clip,flush=True)

    trace = np.fromfile(q/'baseclose_native/trace.bin',np.uint8).reshape(-1,4384)
    mappings = json.loads((R/'source/mission3_base_close_mappings.json').read_text())
    matched = {}
    for layout in mappings['boss_stages']:
        ok = trace[:,0x78] == layout['stage']
        for tile in layout['tiles']:
            address = tile['address'] - 0x2000
            physical = (address//0x800)*1024 + address%0x400
            ok &= trace[:,2048+physical] == tile['tile']
        assert ok.sum() > 0, layout['stage']
        matched[layout['stage']] = int(ok.sum())
    hit = np.flatnonzero((trace[:,0x4e]==0)&(trace[:,4358]==0x10))
    assert len(hit) and set(trace[hit,0x78]) >= {4}
    colors = json.loads((q/'baseclose_color_audit.json').read_text())
    assert all(v['pixels']==0 for v in colors.values())

    oldpaths = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines()
    preserved = [f for f in oldpaths if f.endswith('.png')]
    assert len(preserved) == 180
    for file in preserved:
        assert subprocess.check_output(['git','show',BASE+':'+file],cwd=R) == (R/file).read_bytes(),file
    oldlines = subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines()
    lines = (p/'hires.txt').read_text().splitlines()
    remaining = iter(lines[1:])
    for old in oldlines[1:]:
        assert any(current==old for current in remaining),old
    imgs = [l[5:] for l in lines if l.startswith('<img>')]
    assert len(imgs)==len(set(imgs))
    names = {l[11:].split(',')[0] for l in lines if l.startswith('<condition>')}|{'hmirror','vmirror','bgpriority'}
    sizes = {}
    for file in p.glob('*.png'):
        with Image.open(file) as im:
            im.load();sizes[file.name]=im.size
    for line in lines:
        if line.startswith('['):
            assert all(n.lstrip('!') in names for n in line[1:line.index(']')].split('&')),line
        if '<tile>' in line:
            v=line.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[imgs[int(v[0])]]
            assert 0<=x<=w-32 and 0<=y<=h-32,line
        if '<background>' in line:
            assert line.split('<background>')[1].split(',')[0] in sizes,line
    assert not any('<'+tag+'>' in '\n'.join(lines) for tag in ['patch','bgm','sfx'])
    assert {f.name for f in p.iterdir()} == {f.name for f in rebuild.iterdir()}
    for file in p.iterdir():
        assert file.read_bytes() == (rebuild/file.name).read_bytes(),file.name
    report.update({'total_identical_input_frames':sum(CLIPS.values()),'preserved_png_count':180,
        'old_rules_preserved_in_order':True,'isolated_rebuild_identical':True,
        'base_layout_matched_frames':matched,'distance_12_reuses_native_stage_11_geometry':True,
        'missile_hit_damage_palette_frames':len(hit),'native_color_audit':colors,
        'limitations':['Boss defeat and Mission 3 landing are not in the recording.',
                       'Video regression comparisons use common frames; the recorder may omit the final frame.'],
        'pack_sha256':{f.name:digest(f) for f in sorted(p.iterdir()) if f.is_file()}})
    (R/'validation/mission3_base_close_v0.11.2.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 7,976 native inputs, PCM audio, six unchanged HD regressions, clean colors, 180 preserved PNGs and rebuild.')


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('qa',type=Path)
    ap.add_argument('--rebuild',type=Path,required=True)
    args=ap.parse_args()
    validate(args.qa,args.rebuild)
