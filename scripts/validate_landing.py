"""Validate private landing captures and the v0.7.0 pack.

Usage: python3 scripts/validate_landing.py LANDING_WORK DAMAGE_WORK EARLIER_ROOT
Replay each movie with the final pack, retaining the native captures as baseline.
"""
from pathlib import Path
import argparse
import hashlib
import json
from collections import Counter
from PIL import Image
from validate_damage_hud import parity

R = Path(__file__).resolve().parents[1]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('work', type=Path)
    ap.add_argument('damage', type=Path)
    ap.add_argument('earlier', type=Path)
    ap.add_argument('--rebuild', type=Path, help='Pack directory from an isolated full rebuild')
    args = ap.parse_args()
    w, d, old = args.work, args.damage/'captures', args.earlier
    c = w/'captures'
    report = {'version':'0.7.0', 'base_commit':'b8c0ea52fe609bbdcb103f5cc4004187cb77ddb0'}
    cases = [
        ('successful_landing', c/'landing_native', 'landing', 4302),
        ('combat_to_landing', old/'environment_work/combat/captures/combat_native', 'combat', 8253),
        ('bullet_damage_and_danger', d/'danger_native', 'danger', 547),
        ('incoming_missile', d/'missle_native', 'missle', 1406),
        ('opening_takeoff', old/'environment_work/captures/env_native', 'opening', 3017),
    ]
    for label, native, name, frames in cases:
        report[label] = parity(native, c/(name+'_final'), frames)
        tested = w/('runtime_'+name+'_final')/'HdPacks/Top_Gun_HD'
        for f in (R/'pack').iterdir():
            if f.suffix=='.png' or f.name=='hires.txt':
                assert f.read_bytes()==(tested/f.name).read_bytes(), (name, f.name)
    report['total_native_parity_frames'] = sum(case[3] for case in cases)
    preserved = sorted((w/'baseline_pack').glob('*.png'))
    assert len(preserved)==102
    for p in preserved:
        assert p.read_bytes()==(R/'pack'/p.name).read_bytes(), p.name
    report['unchanged_v0_6_0_pngs'] = [p.name for p in preserved]
    lines = (R/'pack/hires.txt').read_text().splitlines()
    sizes = {}
    for p in (R/'pack').glob('*.png'):
        with Image.open(p) as im:
            im.load(); sizes[p.name] = im.size
    images = [l[5:] for l in lines if l.startswith('<img>')]
    assert len(images)==len(set(images))
    declared = [l.split(',')[0][11:] for l in lines if l.startswith('<condition>')]
    previous = (w/'baseline_pack/hires.txt').read_text().splitlines()
    old_names = Counter(l.split(',')[0][11:] for l in previous if l.startswith('<condition>'))
    new_names = Counter(declared)
    assert {n:c for n,c in new_names.items() if c>1} == {n:c for n,c in old_names.items() if c>1}
    report['new_duplicate_condition_names'] = 0
    conditions = set(declared)|{'hmirror','vmirror','bgpriority'}
    for l in lines:
        if l.startswith('['):
            assert all(x.lstrip('!') in conditions for x in l[1:l.index(']')].split('&')), l
        if '<tile>' in l:
            v = l.split('<tile>')[1].split(',')
            x, y = map(int, v[3:5]); width, height = sizes[images[int(v[0])]]
            assert 0<=x<=width-32 and 0<=y<=height-32, l
        if '<background>' in l:
            assert l.split('<background>')[1].split(',')[0] in sizes, l
    assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
    mappings = json.loads((R/'source/landing_mappings.json').read_text())
    assert set(map(int,mappings['combat_chr']))=={0x0d,0x0e,0x0f,0x13}
    assert len(mappings['approach'])==21
    report.update({
        'decoded_pngs':len(sizes), 'native_approach_sizes':21,
        'tested_artwork_matches_final_pack':True, 'rom_or_audio_replacements':False,
        'pack_sha256':{p.name:digest(p) for p in sorted((R/'pack').iterdir()) if p.is_file()},
        'visual_review':[
            'Opaque approach carrier at near and far native distance stages.',
            'Side touchdown, wheel/deck contact, soft shadow and animated water.',
            'Black native transitions, moving rollout edge and ivory deck markings.',
            'Mission debrief with original live values.',
            'Incoming and outgoing cannon tracers; distant aircraft and actual missiles retained.',
        ],
        'limitations':[
            'Successful mission-one landing; failure outcomes and later missions not newly covered.',
            'Original landing physics, trajectories and animation timing remain game-controlled.',
            'Audio-device metadata omitted from state comparison; PCM compared separately.',
        ],
    })
    if args.rebuild:
        for p in (R/'pack').iterdir():
            if p.is_file():assert p.read_bytes()==(args.rebuild/p.name).read_bytes(), p.name
        report['isolated_rebuild_all_pack_bytes_identical'] = True
    (R/'validation/landing_v0.7.0.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',report['total_native_parity_frames'],'native frames and PCM; 102 approved PNGs retained.')

if __name__=='__main__':
    main()
