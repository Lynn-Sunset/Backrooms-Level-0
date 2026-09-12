"""Regenerate the included bottle label: python blender/generate_label.py (Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / 'textures' / 'almond_label.png'
OUT.parent.mkdir(exist_ok=True)
img = Image.new('RGB', (1024, 512), '#e9e1c8')
draw = ImageDraw.Draw(img)
ink, gold = '#193b40', '#ae8544'


def font(size, serif=False):
    candidates = ([Path('C:/Windows/Fonts/georgiab.ttf')] if serif else [Path('C:/Windows/Fonts/arial.ttf')])
    candidates += [Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf' if serif else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


draw.rectangle((0, 15, 1024, 32), fill=ink)
draw.rectangle((0, 480, 1024, 497), fill=ink)
draw.line((0, 48, 1024, 48), fill=gold, width=3)
draw.line((0, 464, 1024, 464), fill=gold, width=3)
for x in (256, 768):
    draw.text((x, 85), 'F I E L D   S U P P L Y', font=font(18), fill=ink, anchor='mm')
    draw.ellipse((x - 17, 113, x + 17, 166), outline=gold, width=3)
    draw.line((x - 5, 158, x + 5, 121), fill=gold, width=2)
    draw.text((x, 214), 'ALMOND', font=font(52, True), fill=ink, anchor='mm')
    draw.text((x, 274), 'W A T E R', font=font(32), fill=ink, anchor='mm')
    draw.line((x - 79, 323, x + 79, 323), fill=gold, width=2)
    draw.text((x, 359), 'EMERGENCY RESERVE', font=font(17), fill=ink, anchor='mm')
    draw.text((x, 407), '500 mL  /  AW-01', font=font(16), fill=ink, anchor='mm')
img.save(OUT)
print(OUT)
