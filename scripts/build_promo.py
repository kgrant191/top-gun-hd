"""Compose authentic paired emulator captures into 1080x1920 promotion media.

Requires FFmpeg, Pillow and a private capture manifest; no ROM is distributed.
Usage: python scripts/build_promo.py /path/to/capture_manifest.json --out output
Input videos must start at the same emulated input. AVI frame 0 is input 2;
the corresponding separate PCM recordings start at input 1.
"""
import argparse
import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FPS = 60098811 / 1000000
SIZE = (1080, 1920)
PICTURE = (864, 810)
ORIG_POS = (108, 158)
HD_POS = (108, 1030)
GOLD = '#e5b86f'
WHITE = '#f0f4f7'
MUTED = '#98acbd'


def font(size):
    return ImageFont.truetype(str(ROOT / 'source/fonts/DejaVuSansMono-Bold.ttf'), size)


def plate(scene):
    im = Image.new('RGB', SIZE, '#09131e')
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1079, 4), fill=GOLD)
    d.line((108, 92, 972, 92), fill='#344453', width=2)
    d.text((108, 23), 'TOP GUN HD', font=font(49), fill=WHITE)
    d.text((972, 44), 'v1.0.0', anchor='rm', font=font(25), fill=GOLD)
    d.text((108, 111), 'BEFORE', font=font(30), fill=WHITE)
    d.text((972, 128), 'ORIGINAL NES', anchor='rm', font=font(23), fill=MUTED)
    d.text((108, 984), 'AFTER', font=font(30), fill=GOLD)
    d.text((972, 1001), 'HD REMAKE', anchor='rm', font=font(23), fill=GOLD)
    for x,y in (ORIG_POS, HD_POS):
        d.rectangle((x-2,y-2,x+PICTURE[0]+1,y+PICTURE[1]+1), outline='#344453', width=2)
    d.text((540, 1882), scene.upper(), anchor='mm', font=font(27), fill=MUTED)
    return im


def frame(path, index):
    # Input-side seeking retains the first decoded frame at/after this exact PTS.
    data = subprocess.check_output([
        'ffmpeg','-v','error','-ss',f'{index/FPS:.9f}','-i',str(path),
        '-frames:v','1','-f','image2pipe','-vcodec','png','-threads','1','-'
    ])
    return Image.open(io.BytesIO(data)).convert('RGB')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('manifest', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--stills-only', action='store_true')
    a=p.parse_args()
    m=json.loads(a.manifest.read_text())
    a.out.mkdir(parents=True, exist_ok=True)
    work=a.out/'promo-work';work.mkdir(exist_ok=True)
    evidence=[]
    for i,s in enumerate(m['stills'],1):
        capture=m['captures'][s['capture']]
        im=plate(s['title'])
        before=frame(capture['native'],s['input']-2)
        after=frame(capture['hd'],s['input']-2)
        assert before.size==(256,240) and after.size==(1024,960)
        im.paste(before.resize(PICTURE,Image.Resampling.NEAREST),ORIG_POS)
        im.paste(after.resize(PICTURE,Image.Resampling.LANCZOS),HD_POS)
        name=f'Top_Gun_HD_Before_After_{i:02d}_{s["slug"]}.png'
        im.save(a.out/name, optimize=True)
        evidence.append({'file':name,'capture':s['capture'],'input':s['input'],
                         'original_size':before.size,'hd_size':after.size})
        print('Saved',name,flush=True)
    (work/'stills.json').write_text(json.dumps(evidence,indent=2)+'\n')
    if a.stills_only:return
    segments=[]
    for i,s in enumerate(m['segments']):
        c=m['captures'][s['capture']]
        start=(s['input']-2)/FPS
        duration=s['seconds']
        bg=work/f'plate-{i:02d}.png';plate(s['title']).save(bg)
        out=work/f'segment-{i:02d}.mp4'
        # Both video views use the same trim and FPS conversion, never independent
        # speed changes. Exactly one native audio track accompanies both views.
        filt=(f'[0:v]fps=60,scale=864:810:flags=neighbor,setsar=1[b];'
              f'[1:v]fps=60,scale=864:810:flags=lanczos,setsar=1[h];'
              '[3:v][b]overlay=108:158:shortest=1[v0];'
              '[v0][h]overlay=108:1030:shortest=1,format=yuv420p[v];'
              f'[2:a]afade=t=in:d=0.035,afade=t=out:st={duration-.035}:d=0.035[a]')
        subprocess.run([
            'ffmpeg','-v','error','-y','-threads','2','-ss',f'{start:.9f}','-i',c['native'],
            '-threads','2','-ss',f'{start:.9f}','-i',c['hd'],
            '-ss',f'{start+1/FPS:.9f}','-i',c['audio'],
            '-loop','1','-framerate','60','-i',str(bg),
            '-filter_complex_threads','2','-filter_complex',filt,
            '-map','[v]','-map','[a]','-t',str(duration),
            '-c:v','libx264','-preset','fast','-crf','19','-threads','4',
            '-c:a','aac','-b:a','192k','-ar','48000',
            '-movflags','+faststart',str(out)
        ], check=True)
        segments.append(out)
        print('Encoded',s['title'],duration,'seconds',flush=True)
    concat=work/'concat.txt'
    concat.write_text(''.join(f"file '{p.resolve()}'\n" for p in segments))
    target=a.out/'Top_Gun_HD_v1.0.0_TikTok_Before_After.mp4'
    # Re-encode the concatenated audio only, avoiding AAC packet padding at cuts.
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),
                    '-c:v','copy','-c:a','aac','-b:a','192k',
                    '-movflags','+faststart',str(target)],check=True)
    print('Saved',target,flush=True)


if __name__=='__main__':main()
