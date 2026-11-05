"""Make deterministic, pack-only and promotion ZIPs using standard Python."""
from pathlib import Path
import argparse
import hashlib
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def archive(target,files):
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(files):
            info=zipfile.ZipInfo(p.name,date_time=(2026,11,5,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print(target)


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'output/release')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    version=(ROOT/'VERSION').read_text().strip()
    packfiles=sorted((ROOT/'pack').iterdir())
    assert len(packfiles)==273 and all(p.is_file() and p.suffix in ('.png','.txt') for p in packfiles)
    archive(a.out/f'Top_Gun_HD_v{version}.zip',packfiles)
    pictures=sorted((ROOT/'docs/images').glob('Top_Gun_HD_Before_After_*.png'))
    assert len(pictures)==4
    archive(a.out/f'Top_Gun_HD_v{version}_Before_After_Images.zip',pictures)
    files=[a.out/f'Top_Gun_HD_v{version}.zip',
           a.out/f'Top_Gun_HD_v{version}_Before_After_Images.zip']
    (a.out/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files))


if __name__=='__main__':main()
