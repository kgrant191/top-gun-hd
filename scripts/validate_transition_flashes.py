"""Validate v0.7.3 against the three private recordings and v0.7.2 video.

Usage: python3 scripts/validate_transition_flashes.py WORK --rebuild PACK
WORK/captures contains native/final replays and WORK/frame_hashes their
ffmpeg framemd5 results. The private replay runner and movies are not shipped.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, wave
import numpy as np
from PIL import Image
from validate_cockpit_colors import state

R = Path(__file__).resolve().parents[1]
FPS = 60.098811

def hashes(p):
    return [l.split(',')[-1].strip() for l in p.read_text().splitlines()
            if l and not l.startswith('#')]

def pcm(p):
    with wave.open(str(p)) as w:
        return (w.getnchannels(), w.getsampwidth(), w.getframerate(),
                w.getnframes(), hashlib.sha256(w.readframes(w.getnframes())).hexdigest())

def video_frames(p, first, last):
    # Input n corresponds to AVI frame n-2; the first input has no video frame.
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-threads', '1',
        '-ss', f'{(first-2)/FPS:.9f}', '-i', str(p), '-map', '0:v:0',
        '-frames:v', str(last-first+1), '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'])
    return np.frombuffer(raw, np.uint8).reshape(-1, 960, 1024, 3)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('work', type=Path);ap.add_argument('--rebuild', type=Path, required=True)
    args=ap.parse_args();w=args.work;c=w/'captures';p=R/'pack'
    report={'version':'0.7.3', 'base_commit':'918a176408d2ecdf31933851813d1abab01c9421',
            'replays':{}, 'total_native_parity_frames':5629}
    for name, count, before, allowed, region in [
        ('danger',1028,'danger_v072',(492,499),(312,568,716,840)),
        ('danger2',387,'danger2_v072',(121,184),(312,568,716,840)),
        ('landing',4214,'landing_before',(3725,3826),(0,0,1024,512)),
    ]:
        a=c/(name+'_native');b=c/(name+'_final')
        assert json.loads((a/'replay.json').read_text())['native']
        assert not json.loads((b/'replay.json').read_text())['native']
        assert (a/'trace.bin').stat().st_size == count*4384
        assert (a/'trace.bin').read_bytes() == (b/'trace.bin').read_bytes(),name
        checkpoints={}
        for ext in ['chr','nt','oam','pal','ram','state']:
            files=sorted(a.glob('*.'+ext));assert len(files)==count
            for f in files:
                q=b/f.name;assert q.exists(),q
                assert (state(f)==state(q) if ext=='state' else f.read_bytes()==q.read_bytes()),f
            checkpoints[ext]=len(files)
        audio=pcm(a.with_suffix('.wav'));assert audio==pcm(b.with_suffix('.wav')),name
        assert not any(t in (b/'run.log').read_text() for t in
                       ['[HDPack','Script error','handshake timeout','finalization timeout'])
        old=hashes(w/'frame_hashes'/f'{name}_before.md5')
        new=hashes(w/'frame_hashes'/f'{name}_final.md5')
        assert len(old)==len(new)==count-1,(name,len(old),len(new))
        changed=[i+2 for i,(x,y) in enumerate(zip(old,new)) if x!=y]
        assert changed and all(allowed[0]<=n<=allowed[1] for n in changed),(name,changed)
        if name!='landing':assert changed==list(range(allowed[0],allowed[1]+1))
        if name=='landing':
            assert (c/before/'trace.bin').read_bytes()==(a/'trace.bin').read_bytes()
            assert pcm((c/before).with_suffix('.wav'))==audio
        # Check all pixels through the changed interval, not only examples.
        first,last=min(changed),max(changed)
        av=video_frames((c/before).with_suffix('.avi'),first,last)
        bv=video_frames(b.with_suffix('.avi'),first,last)
        assert av.shape==bv.shape==(last-first+1,960,1024,3)
        diff=np.any(av!=bv,axis=3)
        altered=np.flatnonzero(diff.any(axis=(1,2)))+first
        assert list(altered)==changed,(name,list(altered),changed)
        yy,xx=np.where(diff.any(axis=0));bbox=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
        assert region[0]<=bbox[0]<bbox[2]<=region[2]
        assert region[1]<=bbox[1]<bbox[3]<=region[3]
        report['replays'][name]={'identical_native_trace_frames':count,
            'identical_checkpoints':checkpoints,'identical_pcm_sample_frames':audio[3],
            'pcm_sha256':audio[4], 'changed_input_frames':changed,
            'changed_pixel_bounds_xyxy':bbox,'unchanged_video_frames':len(old)-len(changed)}
        print(name,'PASS:',count,'native frames;',len(changed),'corrected frames',flush=True)
    baseline=w/'baseline_v072';approved=sorted(baseline.glob('*.png'));assert len(approved)==131
    for f in approved:assert f.read_bytes()==(p/f.name).read_bytes(),f.name
    lines=(p/'hires.txt').read_text().splitlines()
    images=[l[5:] for l in lines if l.startswith('<img>')];assert len(images)==len(set(images))
    conditions=[l.split(',')[0][11:] for l in lines if l.startswith('<condition>')]
    previous=[l.split(',')[0][11:] for l in (baseline/'hires.txt').read_text().splitlines() if l.startswith('<condition>')]
    assert len(conditions)-len(set(conditions))==len(previous)-len(set(previous))
    conditions=set(conditions)|{'hmirror','vmirror','bgpriority'};sizes={}
    for f in p.glob('*.png'):
        with Image.open(f) as im:im.load();sizes[f.name]=im.size
    for l in lines:
        if l.startswith('['):assert all(n.lstrip('!') in conditions for n in l[1:l.index(']')].split('&')),l
        if '<tile>' in l:
            v=l.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);width,height=sizes[images[int(v[0])]]
            assert 0<=x<=width-32 and 0<=y<=height-32,l
        if '<background>' in l:assert l.split('<background>')[1].split(',')[0] in sizes,l
    assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
    for f in p.iterdir():
        if f.is_file():assert f.read_bytes()==(args.rebuild/f.name).read_bytes(),f.name
    report.update({'unchanged_v0_7_2_pngs':[f.name for f in approved],
        'decoded_pngs':len(sizes),'isolated_rebuild_identical':True,
        'rom_or_audio_replacements':False,
        'limitations':['These three mission-one recordings only.','Audio-device metadata excluded from state comparison; native PCM checked separately.'],
        'pack_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.iterdir()) if f.is_file()}})
    (R/'validation/transition_flashes_v0.7.3.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 5,629 native frames/PCM, all 131 approved PNGs, and isolated rebuild')

if __name__=='__main__':main()
