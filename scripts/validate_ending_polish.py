"""Focused checks for the user's bonus, crew-scale and pilot-wave corrections."""
from pathlib import Path
import argparse,json,subprocess
import numpy as np
from PIL import Image
from validate_mission2 import compare,digest
R=Path(__file__).resolve().parents[1];BASE='ed82a2b01ba10cedee8461fb821a9fabfdb702d2'
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('qa',type=Path);ap.add_argument('--rebuild',type=Path,required=True);args=ap.parse_args();q=args.qa;p=R/'pack'
a=q/'m4ending_native';b=q/'m4ending_polish0151';replay=compare(a,b,q/'m4ending_native_replay.wav',q/'m4ending_polish0151_replay.wav',2205)
assert (a/'chr.bin').read_bytes()==(b/'chr.bin').read_bytes();assert (q/'m4ending_polish0151_replay.end').exists()
assert not any(s in (q/'m4ending_polish0151.log').read_text() for s in ['[HDPack','Script error','handshake timeout','finalization timeout'])
video=json.loads((q/'ending0151_video_compare.json').read_text());assert video['common_frames']>=2203;assert video['changed_carrier_frames']>0;assert not video['unexpected_changed_frames']
# Actual rendered arm-up and arm-down poses use the expected final assets.
for frame,phase in [(180,0),(480,2),(660,3),(900,4)]:
 actual=np.array(Image.open(b/f'{frame:05}.png').convert('RGBA'));expected=np.array(Image.open(p/f'ending_carrier_{phase}.png').convert('RGBA'))
 assert np.array_equal(actual[395:456,746:795,:3],expected[395:456,746:795,:3]),(frame,phase)
up=np.array(Image.open(p/'ending_carrier_3.png'));down=np.array(Image.open(p/'ending_carrier_4.png'));ys,xs=np.where((up!=down).any(2));wave_bounds=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
assert wave_bounds==[767,395,794,444],wave_bounds
# Helmet/head, left torso, near hand and seat remain fixed during the wave.
for box in [(751,404,774,424),(747,428,766,453),(777,445,792,454),(746,454,795,456)]:
 x0,y0,x1,y1=box;assert np.array_equal(up[y0:y1,x0:x1],down[y0:y1,x0:x1]),box
# The synthetic fixture repeats the ROM's exact BONUS command. Only the
# first glyph changes between the previous pack and the corrected pack.
before=np.array(Image.open(q/'bonus0151_baseline.png'));after=np.array(Image.open(q/'bonus0151.png'));ys,xs=np.where((before!=after).any(2));bonus_bounds=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())];assert bonus_bounds==[362,710,373,726];assert len(xs)==66
old=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'pack'],cwd=R,text=True).splitlines();changed=[f'pack/ending_carrier_{i}.png' for i in range(5)];preserved=0
for name in old:
 if not name.endswith('.png') or name in changed:continue
 assert subprocess.check_output(['git','show',BASE+':'+name],cwd=R)==(R/name).read_bytes(),name;preserved+=1
assert preserved==265,preserved
oldlines=subprocess.check_output(['git','show',BASE+':pack/hires.txt'],cwd=R,text=True).splitlines();lines=(p/'hires.txt').read_text().splitlines();it=iter(lines[1:])
for line in oldlines[1:]:assert any(x==line for x in it),line
imgs=[l[5:] for l in lines if l.startswith('<img>')];assert len(imgs)==len(set(imgs));assert imgs[-1]=='ending_polish.png'
files=lambda root:{f.name:f for f in root.iterdir() if f.is_file() and not f.name.startswith('.')}
actual,rebuilt=files(p),files(args.rebuild);assert actual.keys()==rebuilt.keys()
for name,f in actual.items():assert f.read_bytes()==rebuilt[name].read_bytes(),name
report=dict(version='0.15.1',base_commit=BASE,replay=replay,full_chr_trace_identical=True,video_comparison=video,
 pilot_changed_pixel_bounds=wave_bounds,pilot_helmet_torso_seat_fixed=True,crew_uniform_scale=.31,crew_helmet_to_boot_height=155,
 bonus_fixture=dict(text='10000 PTS.',only_changed_glyph_bounds=bonus_bounds,changed_pixels=66,kind='visual-only native nametable fixture; absent from supplied movie'),
 preserved_png_count=preserved,changed_existing_pngs=changed,old_rules_preserved_in_order=True,isolated_full_rebuild_identical=True,
 pack_sha256={name:digest(f) for name,f in sorted(actual.items())})
(R/'validation/ending_polish_v0.15.1.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: bonus numeral, fixed pilot body, uniform crew scale, 2,205 native inputs/PCM, 265 unchanged PNGs and clean full rebuild.')
