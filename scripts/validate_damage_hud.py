"""Validate the private damage replays and mission-one regressions.

Usage: python3 scripts/validate_damage_hud.py DAMAGE_WORK PREVIOUS_WORK
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import wave
import numpy as np
from PIL import Image
from validate_cockpit_colors import state

R = Path(__file__).resolve().parents[1]

def pcm(path):
    with wave.open(str(path)) as f:
        return (f.getnchannels(),f.getsampwidth(),f.getframerate(),
                f.getnframes(),f.readframes(f.getnframes()))

def parity(a,b,frames):
    trace=(a/'trace.bin').read_bytes()
    assert len(trace)==frames*4384
    assert trace==(b/'trace.bin').read_bytes(), (a,b,'trace')
    checks={}
    for ext in ['chr','nt','pal','ram','oam','state']:
        count=0
        for p in a.glob('*.'+ext):
            q=b/p.name
            if not q.exists():continue
            assert (state(p)==state(q) if ext=='state' else p.read_bytes()==q.read_bytes()),p
            count+=1
        checks[ext]=count
    aa=pcm(a.with_suffix('.wav'));bb=pcm(b.with_suffix('.wav'))
    assert aa==bb,(a,b,'PCM')
    log=b.with_suffix('.log').read_text()
    assert not any(s in log for s in ['[HDPack','Script error','handshake timeout'])
    return {'identical_trace_frames':frames,'identical_common_checkpoints':checks,
            'identical_pcm_frames':aa[3],'pcm_sample_rate':aa[2],
            'loader_or_script_errors':0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('work',type=Path);p.add_argument('previous',type=Path)
    args=p.parse_args();w=args.work;c=w/'captures';old=args.previous
    report={'version':'0.6.0','base_commit':'c373a9e665690780c72ecb3613c97cd304c83c20'}
    for name,a,b,frames in [
        ('incoming_missile',c/'missle_native',c/'missle_release',1406),
        ('bullet_damage_and_danger',c/'danger_native',c/'danger_release',547),
        ('opening_takeoff',old/'environment_work/captures/env_native',c/'opening_release',3017),
        ('combat_to_landing',old/'environment_work/combat/captures/combat_native',c/'combat_release',8253),
    ]:report[name]=parity(a,b,frames)
    report['total_native_parity_frames']=13223
    preserved=[]
    for f in sorted((w/'baseline_pack').glob('*.png')):
        assert f.read_bytes()==(R/'pack'/f.name).read_bytes(),f.name
        preserved.append(f.name)
    assert len(preserved)==58
    report['unchanged_v0_5_1_pngs']=preserved
    report['health_fixture']={}
    for frame,hp in [(30,12),(90,9),(150,6),(210,3),(270,0)]:
        a=np.array(Image.open(c/'fixture_final'/f'{frame:05d}.png').convert('RGB'))
        actual=[bool(a[875,340+j*30].max()>100) for j in range(12)]
        assert actual==[j<hp for j in range(12)],(frame,hp,actual)
        report['health_fixture'][str(hp)]={'percent':round(hp/12*100),'lit_segments':sum(actual)}
    report['natural_health_transitions']={}
    for name in ['danger','missle']:
        trace=np.fromfile(c/f'{name}_release/trace.bin',np.uint8).reshape(-1,4384)
        hp=trace[:,0x4e]
        transitions=[{'frame':1,'health':int(hp[0])}]
        transitions += [{'frame':int(i+1),'health':int(hp[i])}
                        for i in np.flatnonzero(hp[1:]!=hp[:-1])+1]
        report['natural_health_transitions'][name]=transitions
    lines=(R/'pack/hires.txt').read_text().splitlines()
    sizes={}
    for f in (R/'pack').glob('*.png'):
        with Image.open(f) as im:im.load();sizes[f.name]=im.size
    images=[l[5:] for l in lines if l.startswith('<img>')]
    conditions={l.split(',')[0][11:] for l in lines if l.startswith('<condition>')}
    conditions.update(['hmirror','vmirror','bgpriority'])
    for l in lines:
        if l.startswith('['):
            assert all(x.lstrip('!') in conditions for x in l[1:l.index(']')].split('&')),l
        if '<tile>' in l:
            fields=l.split('<tile>')[1].split(',');x,y=map(int,fields[3:5])
            width,height=sizes[images[int(fields[0])]]
            assert 0<=x<=width-32 and 0<=y<=height-32,l
        if '<background>' in l:assert l.split('<background>')[1].split(',')[0] in sizes
    assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
    report['decoded_pngs']=len(sizes)
    report['rom_or_audio_replacements']=False
    # A final sort only changes the order of disjoint warning-outline keys.
    tested=(w/'runtime/HdPacks/Top_Gun_HD/hires.txt').read_text().splitlines()
    def canonical(ls):
        independent=[l for l in ls if l.startswith('[cockpit&cockpitBorder&rearThreatL&rearThreatR&flightX0&flightX1&flightY0&flightY1]<tile>0,')]
        return [l for l in ls if not l.startswith('#') and l not in independent]+sorted(independent)
    assert canonical(tested)==canonical(lines),'Final rules differ from tested rules'
    for f in (w/'runtime/HdPacks/Top_Gun_HD').glob('*.png'):
        assert f.read_bytes()==(R/'pack'/f.name).read_bytes(),f.name
    report['tested_artwork_matches_final_pack']=True
    report['final_rule_difference']='Comment/version and stable ordering of disjoint warning-outline keys only'
    report['visual_review']=[
        'Bullet health 75% to 50%; warning on/off and moving rear target.',
        'Incoming missile at each growth stage, including overlap with its flame.',
        'Complete impact burst, preserved cloud scenery and warm damage tint.',
        'Health reset to 100% after death; 100/75/50/25/0% fixture.',
        'Opening/takeoff and combat/landing replay checkpoints inspected.',
    ]
    report['limitations']=['Mission-one coverage only; later missions/refuelling not newly tested.',
                          'Health-level fixture writes test RAM; it is excluded from the pack.',
                          'HD audio metadata excluded from state comparison; PCM compared separately.']
    (R/'validation/damage_hud_v0.6.0.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',report['total_native_parity_frames'],'native frames and PCM; 58 approved PNGs; all five native health levels.')

if __name__=='__main__':main()
