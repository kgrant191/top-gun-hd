"""Painted world layers follow the native bank and PPU vertical scroll.

RAM $0050 is the signed native bank stage (-3..3). The world scroll written
from $00FC is already available to Mesen's background parallax renderer.
The native world horizon is at nametable y=192, independent of screen pitch.
"""
from PIL import Image
import numpy as np
from pack_io import save_png


def build_horizon(root, sky, water, solid):
    pack = root / 'pack'
    source = root / 'source'
    deck = Image.open(source / 'environment_clouddeck_master.png').convert('RGBA')
    # The upper part is atmospheric haze; retain a little of it, then use the
    # distributed cloud detail across the whole field instead of one big puff.
    deck = deck.crop((0, int(deck.height * .10), deck.width, deck.height))
    conditions = [
        f'<condition>envRunwayPresent,tileAtPosition,8,127,{solid[1]},0F001131,N',
        '<condition>envCloudLayer,ppuMemoryCheckConstant,3F06,==,30',
    ]
    backgrounds = []
    mapping = {0: 0.0, 1: -1/32, 2: -1/16, 3: -1/8,
               -1: 1/32, -2: 1/16, -3: 1/8}
    for bank, slope in mapping.items():
        tag = 'zero' if bank == 0 else ('left' if bank < 0 else 'right') + str(abs(bank))
        cond = 'envBank_' + tag
        conditions.append(f'<condition>{cond},memoryCheckConstant,0050,==,{bank & 255:02X}')
        sky_name = 'environment_sky.png'
        if bank:
            sky_name = f'environment_sky_{tag}.png'
            # Extend the existing plate without changing its scale. Resizing
            # here would cause a visible zoom at the first bank stage.
            wide = Image.fromarray(np.pad(np.array(sky),
                ((64,64),(128,128),(0,0)), mode='reflect'))
            turned = wide.transform((1024,512), Image.Transform.AFFINE,
                (1,0,128,-slope,1,64+slope*512), Image.Resampling.BICUBIC)
            plate = Image.new('RGBA',(1024,960));plate.paste(turned,(0,0))
            save_png(plate,pack/sky_name)
        backgrounds.append(f'[cockpit&cockpitBorder&{cond}]<background>{sky_name},1,0,0,6')
        for material, image in [('ocean',water),('cloudtop',deck)]:
            # Canvas matches native world coordinates. Its extra depth covers
            # a horizon above the viewport without exposing a lower edge.
            surface = image.resize((1280,1024),Image.Resampling.LANCZOS)
            base = Image.new('RGBA',(1280,1856))
            # Cloud haze begins four native pixels before the nominal horizon;
            # water uses a tighter transition to retain a clear sea line.
            start = 752 if material=='cloudtop' else 766
            base.paste(surface,(0,start))
            a = np.array(base)
            fade_height = 48 if material=='cloudtop' else 8
            alpha = np.clip((np.arange(base.height)-start)/fade_height,0,1)
            a[:,:,3] = np.uint8(a[:,:,3] * alpha[:,None])
            base = Image.fromarray(a)
            turned = base.transform((1024,1536),Image.Transform.AFFINE,
                (1,0,128,-slope,1,slope*512),Image.Resampling.BICUBIC)
            name = f'environment_{material}_flight_{tag}.png'
            save_png(turned,pack/name)
            palette_condition = 'envCloudLayer' if material=='cloudtop' else '!envCloudLayer'
            backgrounds.append(f'[cockpit&cockpitBorder&!envRunwayPresent&{cond}&{palette_condition}]<background>{name},1,0,1,7')
    backgrounds.append('[cockpit&cockpitBorder]<background>environment_sky.png,1,0,0,6')
    return conditions, backgrounds
