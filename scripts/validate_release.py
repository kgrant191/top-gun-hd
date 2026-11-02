from pathlib import Path
from PIL import Image
import hashlib,json,wave,re
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'captures/native_original';B=R/'captures/release_hd'
frames=len((R/'movie/Input.txt').read_text().splitlines())
report={'version':'0.2.0','movie_input_frames':frames,'reference_emulator':'User-supplied MesenCE 2.2.1 Linux','matched_samples':{},'differences':{}}
for ext in ['ram','oam','chr','nt','pal','state']:
 pairs=[(p,B/p.name) for p in sorted(A.glob('*.'+ext))]
 assert pairs and all(q.exists() for p,q in pairs)
 def read(p):
  return dict(line.split('=',1) for line in p.read_text().splitlines() if not line.startswith('hdAudioDevice.')) if ext=='state' else p.read_bytes()
 bad=[p.name for p,q in pairs if read(p)!=read(q)]
 report['matched_samples'][ext]=len(pairs)-len(bad);report['differences'][ext]=bad
assert not any(report['differences'].values()),report
assert (A/'trace.bin').stat().st_size==frames*4384
assert (A/'trace.bin').read_bytes()==(B/'trace.bin').read_bytes()
report['every_frame_ram_nametable_oam_palette_identical']=frames
pcm=[]
for name in ['native_original','release_hd']:
 with wave.open(str(R/'captures'/f'{name}.wav')) as f:
  b=f.readframes(f.getnframes());pcm.append({'channels':f.getnchannels(),'sample_rate':f.getframerate(),'sample_frames':f.getnframes(),'pcm_sha256':hashlib.sha256(b).hexdigest()})
report['audio']=pcm;report['audio_identical']=pcm[0]==pcm[1];assert report['audio_identical']
log=(R/'captures/release_hd.log').read_text();assert '[HDPack' not in log
report['hdpack_loader_errors']=0
report['state_comparison_note']='Every common emulation field compared. HD-only hdAudioDevice metadata excluded; no replacement tracks.'
lines=(R/'pack/hires.txt').read_text().splitlines();imgs=[line[5:] for line in lines if line.startswith('<img>')]
for name in imgs:
 with Image.open(R/'pack'/name) as im:im.verify()
for line in lines:
 if '<tile>' in line:
  tok=line.split('<tile>')[1].split(',');im=Image.open(R/'pack'/imgs[int(tok[0])]);x,y=map(int,tok[3:5]);assert x>=0 and y>=0 and x+32<=im.width and y+32<=im.height
 for tag in ['<img>','<background>']:
  if tag in line:assert (R/'pack'/line.split(tag)[1].split(',')[0]).is_file()
assert not any('<'+t+'>' in '\n'.join(lines) for t in ['patch','bgm','sfx'])
report['tile_rules']=sum('<tile>' in l for l in lines);report['rom_audio_patches']=False
# Every impact frame must render the same HD coaming at exactly the native displacement.
ref=np.array(Image.open(B/'00075.png').convert('RGB'));shifts=[]
for n in range(75,95):
 a=np.array(Image.open(B/f'{n:05d}.png').convert('RGB'))
 fits=[dx for dx in [-4,0,4] if np.array_equal(a[520:560,310+dx:700+dx],ref[520:560,310:700])]
 assert len(fits)==1,(n,fits);shifts.append(fits[0])
expected=[0,0]+[-4,4]*8+[0,0]
assert shifts==expected,shifts
report['impact']={'checked_frames':[75,94],'hd_cockpit_present_every_frame':True,'native_one_pixel_shake_matched':True,'hd_pixel_offsets':shifts}
# The source's approved assets are copied by build_pack.py without visual changes.
protected=['title.png','title_prompt.png','carrier.png','director_0.png','director_1.png']+[f'exhaust_{i:02X}.png' for i in [2,8,16,27,40,58,80,104]]
previous=R.parent/'topgun_v011/pack'
report['approved_intro_assets_unchanged']={name:hashlib.sha256((R/'pack'/name).read_bytes()).hexdigest() for name in protected}
if previous.exists():
 assert all((R/'pack'/name).read_bytes()==(previous/name).read_bytes() for name in protected)
intro=R/'captures/intro_qa';previous_intro=R.parent/'topgun_v011/captures/release_hd'
if intro.exists() and previous_intro.exists():
 matches=[]
 for p in sorted(intro.glob('*.png')):
  n=int(p.stem)
  if 180<=n<=2340:
   a=np.array(Image.open(p).convert('RGB'));b=np.array(Image.open(previous_intro/p.name).convert('RGB'))
   assert np.array_equal(a,b),('Intro changed',p.name)
   matches.append(n)
 assert len(matches)==13,matches
 report['approved_opening_render_checkpoints_identical']=matches
report['missile_digits']=json.loads((R/'source/digit_validation.json').read_text())
report['coverage']=['Combat radar and enemy contacts','Damage shake','Changing fuel and attitude','Landing transition and directions','Landing through mission accomplished']
report['limitations']=['Enemy/world/projectile art remains original','Later missions and refuelling need capture/art/testing']
(R/'source/validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
