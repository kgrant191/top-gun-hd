"""Validate the single-tanker correction against private v0.8.1 replays."""
from pathlib import Path
import argparse, hashlib, json, subprocess
import numpy as np
from PIL import Image
from validate_mission2 import compare, video_hashes

R = Path(__file__).resolve().parents[1]
BASE = '660db25f66a9b44a9927b45f5ee66d399b7d8375'

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('qa', type=Path)
    ap.add_argument('--rebuild', type=Path, required=True)
    a = ap.parse_args(); q = a.qa; v = q / 'v082'; p = R / 'pack'
    result = {'version': '0.8.2', 'base_commit': BASE}
    result['mission2'] = compare(q/'native', v/'full', q/'native_capture.wav', v/'full_replay.wav', 14475)
    before = video_hashes(v/'before.md5'); after = video_hashes(v/'full.md5')
    assert len(before) == 14474 and len(after) in (14473, 14474)
    # The native recorder can omit one additional frame at either endpoint.
    # Establish alignment from unchanged pre-arrival video, not frame count.
    offsets = [s for s in (0,1) if before[s:s+12000] == after[:12000]]
    assert len(offsets) == 1, offsets
    offset = offsets[0]; first = offset+2
    changed = [i+first for i,(b,c) in enumerate(zip(before[offset:],after)) if b != c]
    assert changed
    trace = np.fromfile(q/'native/trace.bin', dtype=np.uint8).reshape(-1,4384)
    assert all(trace[n-1,0x30] == 2 and trace[n-1,0x18] == 7 and
               trace[n-1,0x2e] == 4 and trace[n-1,0x9f] == 1 for n in changed)
    result['actual_hd_video'] = {'frames': len(after), 'first_input': first,
        'last_input':first+len(after)-1, 'alignment_verified_by_12000_unchanged_frames':True,
        'changed_frames': changed, 'unchanged_frames': len(after)-len(changed),
        'all_changes_within_native_tanker_arrival': True}

    # Only arrival pixels may differ from the validated v0.8.1 video. Also
    # check the entire recorded refueling interval for the fixed native flashes.
    start = (12840-first)/60.098811
    proc = subprocess.Popen(['ffmpeg','-v','error','-ss',str(start),'-i',str(v/'full_replay.avi'),
        '-vf','scale=256:240:flags=neighbor','-f','rawvideo','-pix_fmt','rgb24','-'], stdout=subprocess.PIPE)
    frames = 0
    while True:
        raw = proc.stdout.read(256*240*3)
        if not raw: break
        im = np.frombuffer(raw,np.uint8).reshape(240,256,3)
        blue = np.all(im[:128] == [100,176,255],axis=2) | np.all(im[:128] == [21,95,217],axis=2)
        green = np.all(im[144:208,80:176] == [92,228,48],axis=2)
        assert blue.sum() < 8 and not green.any(), frames
        frames += 1
    assert proc.wait() == 0 and frames >= 1600
    result['refueling_visual_audit'] = {'checked_frames':frames, 'native_blue_frames':0, 'native_green_hud_frames':0}

    files = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines()
    old_pngs = [f for f in files if f.endswith('.png')]; assert len(old_pngs) == 138
    for f in old_pngs:
        assert (R/f).read_bytes() == subprocess.check_output(['git','show',BASE+':'+f],cwd=R),f
    old = subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines()
    new = (p/'hires.txt').read_text().splitlines(); remaining = iter(new[1:])
    for line in old[1:]: assert any(line == x for x in remaining), line
    added = [line for line in new[1:] if line not in set(old)]
    assert added == [
        '<condition>refuelArrival,memoryCheckConstant,009F,==,01',
        '[cockpit&cockpitBorder&missionTwo&mission2Flight&refuelRoute&refuelArrival]'
        '<background>mission2_tanker_entry.png,1,1,1,31']
    m1 = np.fromfile(q/'v081_m1_release/capture/trace.bin',np.uint8).reshape(-1,4384)
    assert len(m1)==8253 and not ((m1[:,0x30]==2)&(m1[:,0x18]==7)&(m1[:,0x2e]==4)&(m1[:,0x9f]==1)).any()
    result['mission1'] = {'guard_checked_native_frames':8253,'new_layer_never_active':True,
        'prior_artwork_and_rules_preserved':True}
    for file in p.glob('*.png'):
        with Image.open(file) as im: im.load()
    original = np.array(Image.open(p/'mission2_tanker.png').convert('RGBA'))
    entry = np.array(Image.open(p/'mission2_tanker_entry.png').convert('RGBA'))
    assert not entry[:,:1024,3].any()
    assert np.array_equal(entry[:,1024:],original[:,1024:])
    assert {f.name for f in p.iterdir() if f.is_file()} == {f.name for f in a.rebuild.iterdir() if f.is_file()}
    for file in p.iterdir():
        if file.is_file(): assert file.read_bytes()==(a.rebuild/file.name).read_bytes(),file.name
    assert not any(t in (v/'full.log').read_text() for t in ['[HDPack','Script error','handshake timeout','finalization timeout'])
    result.update({'preserved_v081_pngs':old_pngs,'new_pngs':['mission2_tanker_entry.png'],
        'original_rules_preserved_in_order':True,'isolated_rebuild_identical':True,
        'limitations':['Recording ends during refueling controls; completion and later sections remain unrecorded.'],
        'pack_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.iterdir()) if f.is_file()}})
    result['install_zip'] = json.loads((v/'zip_check.json').read_text())
    (R/'validation/refuel_entry_v0.8.2.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: one tanker entrance; only arrival frames changed; native state/audio unchanged; 138 PNGs preserved; exact rebuild.')

if __name__=='__main__': main()
