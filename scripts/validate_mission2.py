"""Validate private Mesen captures: python3 scripts/validate_mission2.py QA --rebuild PACK."""
from pathlib import Path
import argparse, hashlib, json, subprocess, wave
from PIL import Image

R = Path(__file__).resolve().parents[1]
BASE = '9c05e3d0c25c468791894377cc250fd4086e9af4'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def state(p):
    return dict(l.split('=', 1) for l in p.read_text().splitlines()
                if not l.startswith('hdAudioDevice.'))

def pcm(p):
    with wave.open(str(p)) as w:
        return {'channels': w.getnchannels(), 'sample_width': w.getsampwidth(),
                'rate': w.getframerate(), 'sample_frames': w.getnframes(),
                'sha256': hashlib.sha256(w.readframes(w.getnframes())).hexdigest()}

def compare(a, b, aw, bw, frames):
    assert (a/'trace.bin').stat().st_size == frames*4384
    assert (a/'trace.bin').read_bytes() == (b/'trace.bin').read_bytes()
    counts = {}
    for ext in ['ram','chr','nt','oam','pal','state']:
        files = sorted(a.glob('*.'+ext)); assert files
        for f in files:
            g = b/f.name; assert g.exists(), g
            assert (state(f)==state(g) if ext=='state' else f.read_bytes()==g.read_bytes()), f
        counts[ext] = len(files)
    audio = pcm(aw); assert audio == pcm(bw)
    return {'identical_native_trace_frames':frames, 'identical_checkpoints':counts,
            'identical_pcm':audio, 'trace_sha256':digest(a/'trace.bin')}

def video_hashes(p):
    return [l.rsplit(',',1)[-1].strip() for l in p.read_text().splitlines() if l and not l.startswith('#')]

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('qa',type=Path)
    ap.add_argument('--rebuild',type=Path,required=True); args=ap.parse_args(); q=args.qa;p=R/'pack'
    report={'version':'0.8.0','base_commit':BASE,'replays':{}}
    report['replays']['mission2']=compare(q/'native',q/'final2',q/'native_capture.wav',q/'final2_capture.wav',14475)
    report['replays']['mission1']=compare(q/'m1baseline/capture',q/'m1final/capture',q/'m1baseline/replay.wav',q/'m1final/replay.wav',8253)
    a=video_hashes(q/'m1baseline/video.md5');b=video_hashes(q/'m1final/video.md5')
    assert len(a)==len(b)==8252,(len(a),len(b))
    changed=[i+2 for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    assert changed==list(range(8082,8254)),changed
    trace=(q/'m1final/capture/trace.bin').read_bytes()
    assert all(trace[(n-1)*4384+0x30]==2 and trace[(n-1)*4384+0x18]==5 for n in changed)
    report['replays']['mission1'].update({'identical_hd_video_frames':len(a)-len(changed),
        'changed_frames':{'first':8082,'last':8253,'count':172,'scene':'Mission 2 briefing after Mission 1 completion'}})
    # The only later pack edit lifts the tanker above clouds during refueling.
    # Route 4 plus active refueling never occurs in this regression recording.
    assert not any(trace[i+0x2e]==4 and trace[i+0x9f]>=1 for i in range(0,len(trace),4384))
    recorded_pack=(q.parent/'runtime/m1final/HdPacks/Top_Gun_HD/hires.txt').read_text()
    assert recorded_pack.replace('mission2_tanker.png,1,1,1,8','mission2_tanker.png,1,1,1,31')==(p/'hires.txt').read_text()
    report['replays']['mission1']['final_tanker_layer_predicate_never_active']=True
    for log in [q/'final2.log',q/'m1baseline/run.log',q/'m1final/run.log']:
        assert not any(s in log.read_text() for s in ['[HDPack','Script error','handshake timeout','finalization timeout']),log
    old=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines()
    approved=[f for f in old if f.endswith('.png')];assert len(approved)==132
    for f in approved:assert subprocess.check_output(['git','show',BASE+':'+f],cwd=R)==(R/f).read_bytes(),f
    lines=(p/'hires.txt').read_text().splitlines();imgs=[l[5:] for l in lines if l.startswith('<img>')]
    assert len(imgs)==len(set(imgs))
    cs=[l.split(',')[0][11:] for l in lines if l.startswith('<condition>')]
    oldlines=subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines()
    oc=[l.split(',')[0][11:] for l in oldlines if l.startswith('<condition>')]
    # The baseline repeats envSea20..29 identifiers for two anchor families.
    # Preserve those definitions and permit only their exact palette aliases.
    from collections import defaultdict
    groups=defaultdict(list);oldgroups=defaultdict(list)
    for l in lines:
        if l.startswith('<condition>'):groups[l.split(',')[0][11:]].append(l)
    for l in oldlines:
        if l.startswith('<condition>'):oldgroups[l.split(',')[0][11:]].append(l)
    for name,values in groups.items():
        if len(values)<2:continue
        if name in oldgroups:assert values==oldgroups[name],name
        else:
            assert name.endswith('M2') and name[:-2] in oldgroups,name
            expected=[]
            for l in oldgroups[name[:-2]]:
                l=l.replace('<condition>'+name[:-2]+',','<condition>'+name+',')
                for a,b in {'0F301131':'0F301121','0F001131':'0F001121','0F2A0A31':'0F2A0A21'}.items():l=l.replace(a,b)
                expected.append(l)
            assert values==expected,name
    cs=set(cs)|{'hmirror','vmirror','bgpriority'};sizes={}
    for f in p.glob('*.png'):
        with Image.open(f) as im: im.load();sizes[f.name]=im.size
    for l in lines:
        if l.startswith('['): assert all(n.lstrip('!') in cs for n in l[1:l.index(']')].split('&')),l
        if '<tile>' in l:
            v=l.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[imgs[int(v[0])]]
            assert 0<=x<=w-32 and 0<=y<=h-32,l
        if '<background>' in l: assert l.split('<background>')[1].split(',')[0] in sizes,l
    assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
    assert {f.name for f in p.iterdir() if f.is_file()}=={f.name for f in args.rebuild.iterdir() if f.is_file()}
    for f in p.iterdir():
        if f.is_file():assert f.read_bytes()==(args.rebuild/f.name).read_bytes(),f.name
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height,nb_frames','-of','json',str(q/'final2_capture.avi')]))['streams'][0]
    assert meta['width']==1024 and meta['height']==960 and int(meta['nb_frames'])==14474,meta
    report.update({'unchanged_v0_7_3_pngs':approved,'decoded_pngs':len(sizes),'actual_hd_video':meta,
        'isolated_rebuild_identical':True,'rom_or_audio_replacements':False,
        'limitations':['Recorded Mission 2 through refueling controls only; completion and later encounters untested.',
                       'Audio-device metadata excluded from state dictionaries; PCM checked separately.'],
        'pack_sha256':{f.name:digest(f) for f in sorted(p.iterdir()) if f.is_file()}})
    (R/'validation/mission2_v0.8.0.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Mission 2 14,475 native frames; Mission 1 8,253 native / 8,080 identical HD frames plus 172 Mission 2 briefing updates; PCM; 132 preserved PNGs; rebuild.')

if __name__=='__main__': main()
