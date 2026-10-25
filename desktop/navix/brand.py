"""NAVIX visual identity: circuit-inspired, vector-like graphics rendered by Pillow.

No remote assets, third-party trademarks or user-specific credentials are bundled.
The exact Circuito Vivo channel artwork was not available for reliable reuse.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _gradient(size):
    width, height = size
    canvas = Image.new('RGB', size)
    paint = ImageDraw.Draw(canvas)
    for y in range(height):
        k = y / max(height - 1, 1)
        paint.line((0, y, width, y),
                   fill=(int(12 + 4 * k), int(29 + 9 * k), int(52 + 18 * k)))
    return canvas


def icon_image(size=256):
    """Transparent rounded-tile app mark with a circuit-styled N."""
    scale = 2
    s = 256 * scale
    image = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    tile = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)
    tile_draw.rounded_rectangle((18, 18, 494, 494), radius=118, fill='#10223f')
    tile_draw.rounded_rectangle((25, 25, 487, 487), radius=112, outline='#2e5879', width=5)
    glow = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((105, 70, 395, 370), fill=(17, 184, 218, 74))
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(65)))
    image.alpha_composite(tile)
    d = ImageDraw.Draw(image)
    # Four circuit pathways link to the central monogram.
    d.line([(89, 153), (145, 153), (175, 183)], fill='#259fbc', width=11, joint='curve')
    d.line([(340, 320), (378, 355), (426, 355)], fill='#259fbc', width=11, joint='curve')
    d.line([(340, 183), (379, 145), (415, 145)], fill='#259fbc', width=11, joint='curve')
    d.line([(96, 350), (132, 350), (171, 311)], fill='#259fbc', width=11, joint='curve')
    # A strong N remains identifiable in the taskbar at 16 × 16 pixels.
    d.line([(178, 338), (178, 169), (336, 339), (336, 170)],
           fill='#73e0ed', width=39, joint='curve')
    d.line([(178, 338), (178, 169), (336, 339), (336, 170)],
           fill='#d6f9ff', width=7, joint='curve')
    for x, y, radius in ((87,153,13), (426,355,13), (416,145,13), (94,350,13)):
        d.ellipse((x-radius, y-radius, x+radius, y+radius),
                  fill='#72e5ee', outline='#d6ffff', width=3)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def _font(size, bold=False):
    names = ('C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/seguisb.ttf') if bold else (
        'C:/Windows/Fonts/segoeui.ttf',)
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def wizard_image(size=(480, 918)):
    """Premium dark gradient for the Inno Setup welcome/finish pages."""
    canvas = _gradient(size).convert('RGBA')
    paint = ImageDraw.Draw(canvas)
    width, height = size
    for x in range(-200, width + 200, 80):
        paint.line([(x, 0), (x + 320, height)], fill=(25, 54, 84, 255), width=2)
    art = icon_image(215)
    canvas.alpha_composite(art, ((width - art.width) // 2, 170))
    paint = ImageDraw.Draw(canvas)
    title = 'NAVIX'
    f = _font(65, bold=True)
    box = paint.textbbox((0, 0), title, font=f)
    paint.text(((width - (box[2]-box[0])) // 2, 440),
               title, font=f, fill='#f2f9ff')
    sub = 'DESKTOP'
    f2 = _font(28, bold=True)
    box = paint.textbbox((0, 0), sub, font=f2)
    paint.text(((width - (box[2]-box[0])) // 2, 530),
               sub, font=f2, fill='#66d9e9')
    paint.rounded_rectangle((115, 608, width-115, 613), radius=2, fill='#2878f0')
    for i, line in enumerate(('SEU PC.', 'SUAS PERMISSÕES.', 'SEU CONTROLE.')):
        font = _font(20, bold=(i == 2))
        box = paint.textbbox((0, 0), line, font=font)
        paint.text(((width - (box[2]-box[0])) // 2, 672 + 34*i),
                   line, font=font, fill='#bed3e8' if i < 2 else '#ffffff')
    return canvas.convert('RGB')


if __name__ == '__main__':
    path = Path('assets')
    path.mkdir(exist_ok=True)
    icon_image().save(path / 'navix.ico', sizes=[(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)])
    wizard_image().save(path / 'wizard.png')
    icon_image(256).convert('RGB').save(path / 'wizard-small.png')
