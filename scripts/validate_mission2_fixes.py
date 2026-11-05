"""Validate v0.8.1 private replays and an isolated full rebuild."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from PIL import Image
from validate_mission2 import compare,video_hashes

R=Path(__file__).resolve().parents[1]
BASE='7abdedf0ef4cabecfa255afcfffd5f4c7a8a5685'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path)
    ap.add_argument('--rebuild',type=Path,required=True);a=ap.parse_args();q=a.qa;p=R/'pack'
    result={'version':'0.8.1','base_commit':BASE,'replays':{}}
    result['replays']['mission2']=compare(q/'native',q/'v081_release',q/'native_capture.wav',q/'v081_release_capture.wav',14475)
    result['replays']['mission1']=compare(q/'m1final/capture',q/'v081_m1_release/capture',q/'m1final/replay.wav',q/'v081_m1_release/replay.wav',8253)
    old=video_hashes(q/'m1final/video.md5');new=video_hashes(q/'v081_m1_release/video.md5')
    assert old==new and len(new)==8252
    result['replays']['mission1']['identical_hd_video_frames']=len(new)
    assert (q/'v081_native/trace.bin').read_bytes()==(q/'native/trace.bin').read_bytes()
    assert (q/'v081_native/chr.bin').stat().st_size==14475*8192
    result['every_frame_chr_captures']=14475
    before=json.loads((q/'v081_before_audit.json').read_text())
    after=json.loads((q/'v081_after_audit.json').read_text())
    assert before['video_frames']==14474
    assert after['video_frames'] in (14473,14474)
    offset=after['first_input_frame']-before['first_input_frame']
    assert offset in (0,1)
    assert before['unchanged_panel_sha256'][offset:]==after['unchanged_panel_sha256']
    assert after['video_meta']['width']==1024 and after['video_meta']['height']==960
    assert before['native_blue_frames'] and before['native_green_hud_frames']
    assert not after['native_blue_frames'],after['native_blue_frames'][:10]
    assert not after['native_green_hud_frames'],after['native_green_hud_frames'][:10]
    result['frame_visual_audit']={'native_blue_frames_before':len(before['native_blue_frames']),
        'native_blue_frames_after':0,'native_green_hud_frames_before':len(before['native_green_hud_frames']),
        'native_green_hud_frames_after':0,'checked_frames':after['video_frames'],
        'first_recorded_input_frame':after['first_input_frame'],
        'unchanged_panel_alignment_identical':True,
        'regions_native_pixels':{'world':[0,0,256,128],'hud':[80,144,176,208]},
        'colors_rgb':{'sea':[21,95,217],'sky':[100,176,255],'hud':[92,228,48]}}
    for log in [q/'v081_release.log',q/'v081_m1_release/run.log']:
        assert not any(t in log.read_text() for t in ['[HDPack','Script error','handshake timeout','finalization timeout']),log
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines()
    pngs=[n for n in names if n.endswith('.png')];assert len(pngs)==136
    for n in pngs:assert (R/n).read_bytes()==subprocess.check_output(['git','show',BASE+':'+n],cwd=R),n
    lines=(p/'hires.txt').read_text().splitlines()
    original=subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines()
    remaining=iter(lines[1:])
    for oldline in original[1:]:assert any(l==oldline for l in remaining),oldline
    conditions={l.split(',')[0][11:] for l in lines if l.startswith('<condition>')}|{'hmirror','vmirror','bgpriority'}
    imgs=[l[5:] for l in lines if l.startswith('<img>')];assert len(imgs)==len(set(imgs))
    sizes={}
    for f in p.glob('*.png'):
        with Image.open(f) as im:im.load();sizes[f.name]=im.size
    for l in lines:
        if l.startswith('['):assert all(x.lstrip('!') in conditions for x in l[1:l.index(']')].split('&')),l
        if '<tile>' in l:
            v=l.split('<tile>')[1].split(',');x,y=map(int,v[3:5]);w,h=sizes[imgs[int(v[0])]]
            assert 0<=x<=w-32 and 0<=y<=h-32,l
        if '<background>' in l:assert l.split('<background>')[1].split(',')[0] in sizes,l
    added=[l for l in lines if l.startswith('[') and l not in set(original)]
    fallback=[]
    for l in added:
        if 'missionTwo' in l:continue
        # New exact palette keys must retain the same fallback that their
        # patterns previously received from default-palette rules.
        prefix,v=l.split('<tile>');v=v.split(',');matches=[]
        for oldline in original:
            if '<tile>' not in oldline:continue
            op,ov=oldline.split('<tile>');ov=ov.split(',')
            if op==prefix and ov[:2]==v[:2] and ov[3:6]==v[3:6] and ov[6]=='Y':matches.append(oldline)
        assert matches and v[6]=='N',l
        fallback.append(l)
    assert not any('<'+x+'>' in '\n'.join(lines) for x in ['patch','bgm','sfx'])
    for f in p.iterdir():
        if f.is_file():assert f.read_bytes()==(a.rebuild/f.name).read_bytes(),f.name
    result.update({'preserved_v080_pngs':pngs,'decoded_pngs':len(sizes),
        'original_rules_preserved_in_order':True,'new_rules_scoped_to_mission2':len(added)-len(fallback),
        'inherited_default_palette_fallbacks':len(fallback),
        'isolated_rebuild_identical':True,'rom_or_audio_replacements':False,
        'limitations':['Movie ends during refueling controls; completion, failure and subsequent mission sections unrecorded.',
                       'Native pixel audit complements focused visual review; it is not proof of complete game coverage.'],
        'pack_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.iterdir()) if f.is_file()}})
    result['install_zip']=json.loads((q/'v081_zip_check.json').read_text())
    (R/'validation/mission2_fixes_v0.8.1.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: five-issue replay, native state/PCM, 8,252 unchanged Mission 1 HD frames, 136 preserved PNGs, exact rebuild.')

if __name__=='__main__':main()
