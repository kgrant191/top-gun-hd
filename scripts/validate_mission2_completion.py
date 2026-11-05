"""Check v0.9.0 against the supplied private native movies and an isolated rebuild."""
from pathlib import Path
import argparse, hashlib, json, subprocess
import numpy as np
from PIL import Image
from validate_mission2 import compare, video_hashes

R = Path(__file__).resolve().parents[1]
BASE = '960018bdd237ed4ce7516e2a885065b0dcaccb44'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('qa',type=Path)
    ap.add_argument('--rebuild',type=Path,required=True)
    args = ap.parse_args(); q=args.qa; p=R/'pack'
    report={'version':'0.9.0','base_commit':BASE,'replays':{}}
    for movie,frames in [('after-refuel',1380),('boss',5877)]:
        d=q/movie
        check=compare(d/'native',d/'final3',d/'native_replay.wav',d/'final3_replay.wav',frames)
        for token in ['[HDPack','Script error','handshake timeout','finalization timeout']:
            assert token not in (d/'final3.log').read_text(),(movie,token)
        audit=json.loads((d/'final3_audit.json').read_text())
        assert audit['video_meta']['width']==1024 and audit['video_meta']['height']==960
        assert audit['video_frames'] in (frames-1,frames-2)
        assert not audit['native_blue_frames'],(movie,audit['native_blue_frames'])
        assert not audit['native_green_hud_frames'],(movie,audit['native_green_hud_frames'])
        assert not audit['native_green_meter_frames'],(movie,audit['native_green_meter_frames'])
        before=video_hashes(d/'before.md5');after=video_hashes(d/'final3.md5')
        assert len(before)==frames-1 and len(after) in (frames-1,frames-2)
        offsets=[offset for offset in (0,1) if before[offset:offset+10]==after[:10]]
        assert len(offsets)==1,offsets
        offset=offsets[0];first=offset+2
        assert audit['first_input_frame']==first
        changed=[i+first for i,(a,b) in enumerate(zip(before[offset:],after)) if a!=b]
        assert changed
        tr=np.fromfile(d/'native/trace.bin',np.uint8).reshape(-1,4384)
        def permitted(r):
            if r[0x30]!=2 or r[0x18]!=7:return False
            if movie=='after-refuel':return r[0x2e]==4 and r[0x9f] in (7,8)
            return r[0x9f]==0 or (r[0x2e]==5 and r[0x9f]==5 and r[0x9c]==0)
        # End-frame RAM can advance before the just-rendered frame. Permit
        # either adjacent state at those one-frame mode boundaries.
        assert all(permitted(tr[n-1]) or permitted(tr[n-2]) for n in changed)
        if movie=='boss':
            assert not any(1701<=n<=5444 or 5448<=n<=5877 for n in changed)
        check.update({'actual_hd_video':audit['video_meta'],
            'first_video_input':first,'last_video_input':first+len(after)-1,
            'alignment_verified_by_unchanged_opening_frames':True,
            'changed_hd_frames':changed,'unchanged_hd_frames':len(after)-len(changed),
            'changes_limited_to_requested_scenes':True,
            'native_blue_world_frames':0,'native_green_hud_frames':0,'native_green_meter_frames':0})
        report['replays'][movie]=check

    old=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines()
    pngs=[f for f in old if f.endswith('.png')];assert len(pngs)==139
    for f in pngs:assert (R/f).read_bytes()==subprocess.check_output(['git','show',BASE+':'+f],cwd=R),f
    plate=np.array(Image.open(p/'mission2_tanker.png').convert('RGBA'))
    departure=np.array(Image.open(p/'mission2_tanker_departure.png').convert('RGBA'))
    assert np.array_equal(plate[:,:1024],departure[:,:1024])
    assert not departure[:,1024:,3].any()
    assert {f.name for f in p.iterdir() if f.is_file()}=={f.name for f in args.rebuild.iterdir() if f.is_file()}
    for f in p.iterdir():
        if f.is_file():assert f.read_bytes()==(args.rebuild/f.name).read_bytes(),f.name

    lines=(p/'hires.txt').read_text().splitlines()
    images=[l[5:] for l in lines if l.startswith('<img>')]
    assert len(images)==len(set(images))
    conditions={l.split(',')[0][11:] for l in lines if l.startswith('<condition>')}|{'hmirror','vmirror','bgpriority'}
    sizes={}
    for f in p.glob('*.png'):
        with Image.open(f) as im:im.load();sizes[f.name]=im.size
    for line in lines:
        if line.startswith('['):assert all(x.lstrip('!') in conditions for x in line[1:line.index(']')].split('&')),line
        if '<tile>' in line:
            v=line.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[images[int(v[0])]]
            assert 0<=x<=w-32 and 0<=y<=h-32,line
        if '<background>' in line:assert line.split('<background>')[1].split(',')[0] in sizes,line
    assert not any('<'+tag+'>' in '\n'.join(lines) for tag in ['patch','bgm','sfx'])
    assert len(sizes)==141
    report.update({'preserved_v082_pngs':pngs,'new_pngs':['mission2_tanker_departure.png','mission2_completion.png'],
        'departure_left_page_exact_right_page_transparent':True,'isolated_rebuild_identical':True,
        'rom_or_audio_replacements':False,'install_zip':json.loads((q/'zip_check.json').read_text()),
        'limitations':['Only target sizes and states in the supplied movies are covered.',
                       'Later missions and unrecorded outcomes require additional coverage.'],
        'pack_sha256':{f.name:sha(f) for f in sorted(p.iterdir()) if f.is_file()}})
    (R/'validation/mission2_completion_v0.9.0.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 7,257 native frames and PCM identical; zero native blue/green artifacts; 139 previous PNGs preserved; exact rebuild and ZIP.')

if __name__=='__main__':main()
