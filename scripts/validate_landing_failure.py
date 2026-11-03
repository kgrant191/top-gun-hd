"""Validate the failed-water-landing follow-up against private replay captures.

Usage: python3 scripts/validate_landing_failure.py WORK
The WORK/frame_hashes directory holds ffmpeg framemd5 output for each HD replay.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import numpy as np
from PIL import Image
from validate_damage_hud import parity

R = Path(__file__).resolve().parents[1]

def frame_hashes(path):
    return [l.rsplit(',',1)[-1].strip() for l in path.read_text().splitlines()
            if l and not l.startswith('#')]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('work',type=Path)
    ap.add_argument('--failure-capture',default='fail_final')
    ap.add_argument('--success-capture',default='landing_v071final')
    ap.add_argument('--rebuild',type=Path)
    args = ap.parse_args(); w=args.work; c=w/'captures'; p=R/'pack'
    report = {'version':'0.7.1','base_commit':'22b85bb4943baf7c496eb9d8200afa05ad01caa8'}
    for label,native,hd,count in [
        ('failed_water_landing','fail_native',args.failure_capture,885),
        ('successful_landing','landing_native',args.success_capture,4302),
    ]:
        report[label] = parity(c/native,c/hd,count)
        installed=w/('runtime_'+hd)/'HdPacks/Top_Gun_HD'
        for f in p.iterdir():
            if f.suffix=='.png' or f.name=='hires.txt':
                assert f.read_bytes()==(installed/f.name).read_bytes(),(hd,f.name)
    report['total_native_parity_frames']=5187
    old=frame_hashes(w/'frame_hashes/landing_final.md5')
    new=frame_hashes(w/'frame_hashes'/f'{args.success_capture}.md5')
    assert len(old)==4301 and old==new,'Successful landing visuals changed'
    report['successful_landing_identical_video_frames']=len(old)
    old=frame_hashes(w/'frame_hashes/fail_before.md5')
    new=frame_hashes(w/'frame_hashes'/f'{args.failure_capture}.md5')
    assert len(old)==len(new)==884
    changed=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
    assert changed,'Failure artwork did not change'
    trace=np.fromfile(c/'fail_native/trace.bin',np.uint8).reshape(-1,4384)
    mappings=json.loads((R/'source/landing_failure_mappings.json').read_text())
    assert mappings['sprite_pattern_table']==4096
    for frame,entry in zip([357,361,365,369,373,377],mappings['layouts']):
        state=dict(l.split('=',1) for l in (c/'fail_native'/f'{frame:05d}.state').read_text().splitlines())
        bank=int(state['ppu.control.spritePatternAddr'])
        assert bank==mappings['sprite_pattern_table']
        chrdata=(c/'fail_native'/f'{frame:05d}.chr').read_bytes()
        for tile in entry['tiles']:
            offset=bank+tile['tile']*16
            assert chrdata[offset:offset+16].hex().upper()==tile['pattern']
    for i in changed:
        # The video skips the initial pre-input frame. HD scene conditions
        # read state before the following endFrame callback advances the trace.
        assert trace[i,0x18]==7 and trace[i,0x9f] in (6,7),(i,trace[i,0x9f])
    report['failure_video_changes']={'first_input_frame':changed[0]+2,
        'last_input_frame':changed[-1]+2,'changed_frame_count':len(changed),
        'restricted_to_native_failure_substates_6_7':True,
        'identical_frames_outside_failure':len(old)-len(changed)}
    baseline=w/'baseline_v070'
    preserved=sorted(baseline.glob('*.png'));assert len(preserved)==130
    for f in preserved:assert f.read_bytes()==(p/f.name).read_bytes(),f.name
    report['unchanged_v0_7_0_pngs']=[f.name for f in preserved]
    lines=(p/'hires.txt').read_text().splitlines()
    previous=(baseline/'hires.txt').read_text().splitlines()
    remaining=iter(lines[1:])
    for line in previous[1:]:assert any(l==line for l in remaining),line
    report['all_prior_rules_preserved_in_relative_order']=True
    sizes={}
    for f in p.glob('*.png'):
        with Image.open(f) as im:im.load();sizes[f.name]=im.size
    images=[l[5:] for l in lines if l.startswith('<img>')]
    assert len(images)==len(set(images))
    oldc=Counter(l.split(',')[0][11:] for l in previous if l.startswith('<condition>'))
    newc=Counter(l.split(',')[0][11:] for l in lines if l.startswith('<condition>'))
    assert {n:v for n,v in oldc.items() if v>1}=={n:v for n,v in newc.items() if v>1}
    conditions=set(newc)|{'hmirror','vmirror','bgpriority'}
    for l in lines:
        if l.startswith('['):
            assert all(x.lstrip('!') in conditions for x in l[1:l.index(']')].split('&')),l
        if '<tile>' in l:
            v=l.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);width,height=sizes[images[int(v[0])]]
            assert 0<=x<=width-32 and 0<=y<=height-32,l
        if '<background>' in l:assert l.split('<background>')[1].split(',')[0] in sizes,l
    assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
    report.update({'decoded_pngs':len(sizes),'native_crash_stages':6,
        'tested_artwork_matches_final_pack':True,'rom_or_audio_replacements':False,
        'visual_review':['Painted carrier, sky and water maintained through crash and aftermath.',
                         'Six fire-to-spray stages anchored at the native impact position.',
                         'Native transition, debrief values and following briefing preserved.'],
        'limitations':['Recorded water-impact failure only; other failure paths not newly covered.',
                       'Native landing physics, timing, game outcomes and audio unchanged.',
                       'Audio-device metadata omitted from state comparison; PCM compared separately.'],
        'pack_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.iterdir()) if f.is_file()}})
    if args.rebuild:
        for f in p.iterdir():
            if f.is_file():assert f.read_bytes()==(args.rebuild/f.name).read_bytes(),f.name
        report['isolated_rebuild_all_pack_bytes_identical']=True
    (R/'validation/landing_failure_v0.7.1.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 5187 native frames/PCM; 4301 identical successful-landing frames; 130 preserved PNGs')

if __name__=='__main__':main()
