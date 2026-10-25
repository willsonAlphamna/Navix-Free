"""Native app icon; deterministic artwork, no external asset download."""
from pathlib import Path
from PIL import Image, ImageDraw


def icon_image(size=256):
    image = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 248, 248), radius=52, fill='#111827')
    draw.rounded_rectangle((15, 15, 241, 241), radius=47, outline='#334155', width=3)
    draw.polygon([(54,190),(54,66),(82,66),(151,151),(151,66),(180,66),(180,190),
                  (153,190),(83,104),(83,190)], fill='#60a5fa')
    draw.polygon([(168,120),(202,47),(225,31),(224,61),(196,101)], fill='#e0f2fe')
    draw.line((169,128,219,41), fill='#38bdf8', width=5)
    return image.resize((size, size), Image.Resampling.LANCZOS)


if __name__ == '__main__':
    path = Path('assets')
    path.mkdir(exist_ok=True)
    icon_image().save(path / 'navix.ico', sizes=[(16,16),(32,32),(48,48),(128,128),(256,256)])
