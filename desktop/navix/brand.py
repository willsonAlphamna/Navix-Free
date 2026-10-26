"""NAVIX visual identity: circuit-inspired, vector-like graphics rendered by Pillow.

The emblem is provided by the owner of the Circuito Vivo channel.
No remote assets or user-specific credentials are bundled.
"""
from pathlib import Path
import math
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
    """Use the owner's Circuito Vivo emblem for NAVIX, retaining a local fallback."""
    emblem = Path(__file__).resolve().parent.parent / 'assets' / 'circuitovivo_navix.png'
    if emblem.is_file():
        with Image.open(emblem) as source:
            return source.convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
    # Fallback only for running the source without the bundled asset.
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
    names = ('C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/seguisb.ttf',
             'DejaVuSans-Bold.ttf') if bold else (
        'C:/Windows/Fonts/segoeui.ttf', 'DejaVuSans.ttf')
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def wordmark_image(large=False):
    """One continuous, embossed NavixX logotype; the x remains lowercase."""
    width, height = (230, 60) if large else (147, 42)
    font = _font(40 if large else 25, bold=True)
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    # Use a single text run, avoiding separate Tk labels and accidental gaps.
    draw.text((4, 2), 'NavixX', font=font, fill=255,
              stroke_width=0)
    # Composite a shifted shadow without changing the original glyph mask.
    shadow_mask = Image.new('L', (width, height), 0)
    shadow_mask.paste(mask, (0, 3))
    drop = Image.new('RGBA', (width, height), (2, 9, 25, 0))
    drop.putalpha(shadow_mask.filter(ImageFilter.GaussianBlur(2)))
    image.alpha_composite(drop)
    fill = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = fill.load()
    for y in range(height):
        mix = y / max(1, height - 1)
        for x in range(width):
            pixels[x, y] = (int(116 - 69*mix), int(211 - 83*mix),
                            int(255 - 7*mix), 255)
    fill.putalpha(mask)
    image.alpha_composite(fill)
    shine_mask = Image.new('L', (width, height), 0)
    shade = ImageDraw.Draw(shine_mask)
    shade.rectangle((0, 0, width, height//2), fill=70)
    import PIL.ImageChops
    # Fine highlight around the upper half of the type.
    highlight = Image.new('RGBA', (width, height), (215, 246, 255, 0))
    highlight.putalpha(PIL.ImageChops.multiply(mask, shine_mask))
    image.alpha_composite(highlight)
    return image


def raised_label_image(label, size=15):
    """Compact embossed headings for the sidebar, rendered once per UI build."""
    font = _font(size, bold=True)
    sample = Image.new('RGBA', (300, 60), (0, 0, 0, 0))
    bounds = ImageDraw.Draw(sample).textbbox((0, 0), label, font=font)
    width, height = max(1, bounds[2] + 10), max(1, bounds[3] - bounds[1] + 12)
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    brush = ImageDraw.Draw(image)
    y = 2 - bounds[1]
    brush.text((4, y + 3), label, font=font, fill=(2, 8, 23, 230))
    brush.text((3, y + 1), label, font=font, fill=(37, 91, 143, 255))
    brush.text((3, y), label, font=font, fill=(211, 242, 255, 255))
    return image


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


def wizard_small_image(size=(256, 256)):
    """Brand inset from the right trim line of the installer header."""
    image = _gradient(size).convert('RGBA')
    emblem = icon_image(174)
    # Asymmetric spacing keeps the emblem visibly away from the right border.
    image.alpha_composite(emblem, (25, (size[1] - emblem.height) // 2))
    return image.convert('RGB')


def navigation_icon(name, size=22):
    """Glossy vector-like navigation tiles, legible at small Windows DPI."""
    factor = 3
    s = size * factor
    image = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    # Subtle 3D bezel, top specular highlight and cast shadow.
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((4, 6, s-3, s-2), radius=17,
                        fill=(2, 9, 24, 145))
    d.rounded_rectangle((4, 2, s-4, s-7), radius=16,
                        fill=(24, 58, 95, 240), outline=(70, 144, 207, 255), width=3)
    d.arc((8, 4, s-8, s//2+11), 185, 350, fill=(138, 224, 252, 150), width=3)
    color = (238, 249, 255, 255)
    accent = (68, 225, 242, 255)
    line = max(3, 2 * factor)
    if name == 'inicio':
        d.line([(8, 31), (33, 9), (58, 31)], fill=color, width=line, joint='curve')
        d.line([(16, 29), (16, 57), (50, 57), (50, 29)], fill=color, width=line)
        d.rectangle((29, 42, 38, 57), outline=accent, width=3)
    elif name == 'permissoes':
        d.rounded_rectangle((15, 9, 51, 57), radius=11, outline=color, width=line)
        d.line([(24, 32), (31, 39), (44, 25)], fill=accent, width=line, joint='curve')
    elif name == 'ferramentas':
        d.ellipse((12, 12, 40, 40), outline=color, width=line)
        d.line([(37, 36), (56, 55)], fill=accent, width=line)
        d.ellipse((8, 8, 15, 15), fill=accent)
    elif name == 'atividade':
        d.rounded_rectangle((10, 8, 55, 58), radius=8, outline=color, width=line)
        for y in (24, 35, 46):
            d.line([(23, y), (46, y)], fill=accent if y == 35 else color, width=4)
    elif name == 'doacoes':
        d.polygon([(33, 54), (12, 34), (11, 23), (16, 17), (24, 16),
                   (33, 25), (42, 16), (50, 17), (55, 23), (54, 34)],
                  fill=accent, outline=color)
    elif name == 'assistente':
        d.ellipse((18, 18, 48, 48), outline=color, width=line)
        d.line([(33, 8), (33, 18), (33, 48), (33, 58)], fill=accent, width=4)
        d.line([(8, 33), (18, 33), (48, 33), (58, 33)], fill=accent, width=4)
    elif name == 'minimizar':
        d.rounded_rectangle((8, 11, 58, 55), radius=7, outline=color, width=line)
        d.line([(22, 45), (44, 45)], fill=accent, width=line)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def brazil_flag_frames(size=(32, 20), count=4):
    """Subtle 4-frame wave, tiny enough for older dual-core Windows PCs."""
    width, height = size
    frames = []
    for index in range(count):
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        d = ImageDraw.Draw(image)
        for x in range(width):
            sway = math.sin((x / width) * math.pi * 2 + index * math.pi / 2)
            shift = round(sway * 1.1)
            d.line((x, max(1, 1 + shift), x, min(height - 2, height - 2 + shift)),
                   fill=(22, 143, 76, 255))
        diamond = [(width//2, 3), (width-5, height//2),
                   (width//2, height-4), (4, height//2)]
        d.polygon(diamond, fill=(249, 210, 52, 255))
        d.ellipse((width//2-5, height//2-5, width//2+5, height//2+5),
                  fill=(25, 76, 166, 255))
        d.arc((width//2-6, height//2-2, width//2+6, height//2+5),
              180, 345, fill=(255, 255, 255, 240), width=1)
        frames.append(image)
    return frames


if __name__ == '__main__':
    path = Path('assets')
    path.mkdir(exist_ok=True)
    icon_image().save(path / 'navix.ico', sizes=[(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)])
    wizard_image().save(path / 'wizard.png')
    wizard_small_image().save(path / 'wizard-small.png')
