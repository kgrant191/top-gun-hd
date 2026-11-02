"""Decorative dial markings registered to the preserved cockpit artwork.

Coordinates are pixels in the final 1024 x 960 HD background, after the
cockpit's vertical remapping. These faces are static decoration; no live
flight data or emulator mappings are changed.
"""
import math

from PIL import Image, ImageDraw


# Center and scale radii measured inside each painted glass face.
# The lower bezel is taller, and its bottom sits behind the foreground lip.
DIALS = (
    (806, 756, 44, 38),
    (943, 756, 44, 38),
    (875, 884, 43, 54),
)
LOWER_CLIP_Y = 903  # First excluded row; preserve the entire metal panel lip.


def draw_dials(base):
    """Draw antialiased scales centered on their individual painted bezels."""
    supersample = 4
    for index, (cx, cy, rx, ry) in enumerate(DIALS):
        left, top = cx - rx - 3, cy - ry - 3
        width, height = 2 * rx + 7, 2 * ry + 7
        layer = Image.new('RGBA', (width * supersample, height * supersample))
        draw = ImageDraw.Draw(layer)

        def point(x, y):
            return ((x - left) * supersample, (y - top) * supersample)

        for tick in range(24):
            angle = 2 * math.pi * tick / 24
            inner = 0.78 if tick % 3 == 0 else 0.88
            start = point(cx + inner * rx * math.cos(angle),
                          cy + inner * ry * math.sin(angle))
            end = point(cx + rx * math.cos(angle),
                        cy + ry * math.sin(angle))
            draw.line((start, end), fill=(143, 177, 180, 220),
                      width=2 * supersample)

        draw.line((point(cx - 25, cy), point(cx + 25, cy)),
                  fill=(191, 223, 218, 255), width=3 * supersample)
        draw.ellipse((*point(cx - 3.5, cy - 3.5),
                      *point(cx + 3.5, cy + 3.5)),
                     fill=(129, 172, 178, 255))
        layer = layer.resize((width, height), Image.Resampling.LANCZOS)
        if index == 2:
            # Clip after filtering so no antialiasing can bleed onto the lip.
            layer = layer.crop((0, 0, width, LOWER_CLIP_Y - top))
        base.alpha_composite(layer, (left, top))
