"""Validate the v1.0.1 pack and its preserved artwork, without requiring a ROM."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'pack'


def verify():
    version=(ROOT/'VERSION').read_text().strip()
    assert version=='1.0.1', version
    assert json.loads((ROOT/'source/build_manifest.json').read_text())['version']==version
    approved=json.loads((ROOT/'validation/ending_polish_v0.15.1.json').read_text())['pack_sha256']
    actual={p.name for p in PACK.iterdir() if p.is_file()}
    assert actual==set(approved), (actual-set(approved),set(approved)-actual)
    assert len(actual)==273
    for name,digest in approved.items():
        if name not in ('README.txt','hires.txt'):
            assert hashlib.sha256((PACK/name).read_bytes()).hexdigest()==digest, name
    text=(PACK/'hires.txt').read_text()
    lines=text.splitlines()
    # Resolve references in loader order, including deliberate later redefinitions.
    known={'hmirror','vmirror'}
    for line in lines:
        if line.startswith('<condition>'):
            known.add(line[11:].split(',')[0])
        if line.startswith('['):
            assert all(n.lstrip('!') in known for n in line[1:line.index(']')].split('&')), line
    assert '<condition>v101RefuelI_X,originPositionCheckX,==,136' in lines
    assert '<condition>v101RefuelI_Y,originPositionCheckY,==,144' in lines
    assert any('missionTwo' in l and 'm3BoomConnected' in l for l in lines)
    assert lines[0]=='# Top Gun HD v1.0.1 - refueling regression fixes'
    assert '<scale>4' in lines and '<ver>109' in lines
    assert not re.search(r'<(?:patch|bgm|sfx)>',text)
    sizes={}
    for p in PACK.glob('*.png'):
        with Image.open(p) as im:
            sizes[p.name]=im.size
            im.verify()
    images=[s[5:] for s in lines if s.startswith('<img>')]
    tiles=0
    for line in lines:
        if '<tile>' in line:
            t=line.split('<tile>',1)[1].split(',')
            name=images[int(t[0])];x,y=map(int,t[3:5]);w,h=sizes[name]
            assert 0<=x<=w-32 and 0<=y<=h-32,(name,x,y,w,h)
            tiles+=1
        for tag in ('<img>','<background>'):
            if tag in line:
                name=line.split(tag,1)[1].split(',')[0]
                assert name in sizes,name
    assert (PACK/'README.txt').read_bytes()==(ROOT/'README.txt').read_bytes()
    print(f'PASS v{version}: {len(sizes)} preserved PNGs, {tiles} tile rules, 273 install files; no ROM/audio patches.')
    return {'version':version,'approved_pngs':len(sizes),'tile_rules':tiles,'install_files':273,
            'unresolved_condition_references':0,'rom_audio_patches':False}


if __name__=='__main__':verify()
