"""Validate the transition-only correction using both private landing replays.

Usage: python3 scripts/validate_landing_transition.py WORK --rebuild PACK_DIR
WORK/frame_hashes contains ffmpeg framemd5 output for the before/after replays.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
from PIL import Image
from validate_damage_hud import parity
from validate_landing_failure import frame_hashes

R=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('work',type=Path);ap.add_argument('--rebuild',type=Path)
    args=ap.parse_args();w=args.work;c=w/'captures';p=R/'pack'
    report={'version':'0.7.2','base_commit':'20544f0ccff39b29e06d9c6916942ccb1b105fe3'}
    hashes={}
    for label,native,before,after,count,expected in [
        ('failed_landing','fail_native','fail_final','fail_v072final',885,[510,705]),
        ('successful_landing','landing_native','landing_v071final','landing_v072final',4302,[4143,4144,4146,4148]),
    ]:
        report[label]=parity(c/native,c/after,count)
        old=frame_hashes(w/'frame_hashes'/f'{before}.md5')
        new=frame_hashes(w/'frame_hashes'/f'{after}.md5')
        assert len(old)==len(new)==count-1
        changed=[i+2 for i,(a,b) in enumerate(zip(old,new)) if a!=b]
        assert changed==expected,(label,changed)
        report[label]['changed_input_frames']=changed
        report[label]['identical_video_frames']=len(old)-len(changed)
        hashes[label]=(old,new)
        installed=w/('runtime_'+after)/'HdPacks/Top_Gun_HD'
        for f in p.iterdir():
            if f.suffix=='.png' or f.name=='hires.txt':
                assert f.read_bytes()==(installed/f.name).read_bytes(),(after,f.name)
    old,new=hashes['failed_landing']
    black=old[509-2]
    assert new[510-2]==black,'Carrier flash must be replaced by the ongoing black transition'
    assert new[705-2]==old[704-2],'Outgoing results must retain the HD panel and live text'
    assert all(hashes['successful_landing'][1][f-2]==black for f in [4143,4144,4146,4148])
    report['transition_pixel_checks']={'outgoing_carrier_frame_is_black':True,
        'outgoing_cockpit_frame_is_black':True,'outgoing_results_match_previous_hd_frame':True}
    baseline=w/'baseline_v071';approved=sorted(baseline.glob('*.png'))
    assert len(approved)==131
    for f in approved:assert f.read_bytes()==(p/f.name).read_bytes(),f.name
    lines=(p/'hires.txt').read_text().splitlines();previous=(baseline/'hires.txt').read_text().splitlines()
    remaining=iter(lines[1:])
    for line in previous[1:]:assert any(l==line for l in remaining),line
    oldc=Counter(l.split(',')[0][11:] for l in previous if l.startswith('<condition>'))
    newc=Counter(l.split(',')[0][11:] for l in lines if l.startswith('<condition>'))
    assert {n:v for n,v in oldc.items() if v>1}=={n:v for n,v in newc.items() if v>1}
    sizes={}
    for f in p.glob('*.png'):
        with Image.open(f) as im:im.load();sizes[f.name]=im.size
    images=[l[5:] for l in lines if l.startswith('<img>')]
    assert len(images)==len(set(images))
    conditions=set(newc)|{'hmirror','vmirror','bgpriority'}
    for l in lines:
        if l.startswith('['):assert all(n.lstrip('!') in conditions for n in l[1:l.index(']')].split('&')),l
        if '<tile>' in l:
            v=l.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);width,height=sizes[images[int(v[0])]]
            assert 0<=x<=width-32 and 0<=y<=height-32,l
        if '<background>' in l:assert l.split('<background>')[1].split(',')[0] in sizes,l
    assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
    report.update({'total_native_parity_frames':5187,'unchanged_v0_7_1_pngs':[f.name for f in approved],
        'all_prior_rules_preserved_in_relative_order':True,'decoded_pngs':len(sizes),
        'tested_artwork_matches_final_pack':True,'rom_or_audio_replacements':False,
        'limitations':['Recorded successful and failed water landings only.',
                       'Later-mission artwork and other failed-landing paths remain outside this correction.',
                       'Audio-device metadata omitted from state comparison; PCM compared separately.'],
        'pack_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.iterdir()) if f.is_file()}})
    if args.rebuild:
        for f in p.iterdir():
            if f.is_file():assert f.read_bytes()==(args.rebuild/f.name).read_bytes(),f.name
        report['isolated_rebuild_all_pack_bytes_identical']=True
    (R/'validation/landing_transition_v0.7.2.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 5187 native frames/PCM; exactly six corrected transition frames; 131 unchanged PNGs')

if __name__=='__main__':main()
