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
    """Floating brand emblem; transparent pixels avoid the blue square in Setup."""
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    emblem = icon_image(round(min(size) * 0.69))
    # A small offset to the left preserves the right-side breathing room.
    image.alpha_composite(emblem, (round(size[0] * 0.10),
                                   (size[1] - emblem.height) // 2))
    return image


def navigation_icon(name, size=22):
    """Contemporary, transparent line icons, inspired by the Lucide visual language.

    No square badge: the petroleum-blue sidebar itself provides the background.
    Supersampling gives rounded, sharp lines on low-DPI Windows displays.
    """
    factor = 5
    extent = 24 * factor
    image = Image.new('RGBA', (extent, extent), (0, 0, 0, 0))
    glow = Image.new('RGBA', image.size, (0, 0, 0, 0))
    canvas = ImageDraw.Draw(image)
    halo = ImageDraw.Draw(glow)
    white = (226, 245, 255, 255)
    cyan = (70, 222, 234, 255)
    blue = (113, 166, 252, 255)

    def pos(point):
        return (round(point[0] * factor), round(point[1] * factor))

    def line(points, color=white, weight=1.8):
        points = [pos(p) for p in points]
        radius = max(1, round(weight * factor / 2))
        halo.line(points, fill=(30, 170, 227, 110), width=round((weight + 1.9) * factor),
                  joint='curve')
        canvas.line([(x, y + round(0.5 * factor)) for x, y in points],
                    fill=(3, 20, 38, 190), width=round((weight + 0.4) * factor),
                    joint='curve')
        canvas.line(points, fill=color, width=round(weight * factor), joint='curve')
        for x, y in (points[0], points[-1]):
            canvas.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)

    def circle(center, radius, color=cyan, width=1.7, fill=None):
        x, y = pos(center)
        rr = round(radius * factor)
        canvas.ellipse((x-rr, y-rr, x+rr, y+rr), fill=fill,
                       outline=color, width=round(width * factor))

    if name == 'inicio':
        line([(3.4, 10.9), (12, 3.8), (20.6, 10.9)], cyan, 2)
        line([(5.8, 10), (5.8, 20), (18.2, 20), (18.2, 10)], white)
        line([(10, 20), (10, 13.6), (14, 13.6), (14, 20)], blue)
    elif name == 'permissoes':
        line([(12, 2.6), (20, 5.8), (19.4, 13.6), (17, 17.6), (12, 21.6),
              (7, 17.6), (4.6, 13.6), (4, 5.8), (12, 2.6)], white, 1.8)
        line([(8.2, 12.4), (10.8, 15), (16, 9.4)], cyan, 2.3)
    elif name == 'ferramentas':
        for y, knob in ((6, 8), (12, 16), (18, 10)):
            line([(3, y), (21, y)], blue, 1.5)
            circle((knob, y), 2.5, white, 1.65, (16, 44, 71, 255))
    elif name == 'atividade':
        line([(2.6, 12.2), (7.4, 12.2), (10, 5.7), (13.8, 18.4),
              (16.5, 10.8), (18, 12.2), (21.4, 12.2)], cyan, 1.9)
        circle((12, 12), 10, blue, 1.0)
    elif name == 'doacoes':
        heart = []
        for i in range(37):
            t = i * math.pi * 2 / 36
            x = 12 + 0.49 * (16 * math.sin(t)**3)
            y = 12.3 - 0.50 * (13 * math.cos(t) - 5 * math.cos(2*t)
                                - 2 * math.cos(3*t) - math.cos(4*t))
            heart.append((x, y))
        line(heart, cyan, 1.85)
    elif name == 'assistente':
        line([(8, 3.4), (8, 8.2), (6.4, 8.2), (6.4, 12.2),
              (10.2, 16), (13.7, 16), (17.5, 12.2), (17.5, 8.2),
              (15.9, 8.2), (15.9, 3.4)], white)
        line([(12, 16), (12, 21)], cyan, 2)
        line([(6.5, 9), (17.5, 9)], blue, 1.35)
        line([(4, 3), (4, 6)], cyan, 1.2)
        line([(2.5, 4.5), (5.5, 4.5)], cyan, 1.2)
    elif name == 'minimizar':
        line([(3.7, 3.7), (9.7, 9.7)], cyan)
        line([(9.7, 5.6), (9.7, 9.7), (5.6, 9.7)], white)
        line([(20.3, 20.3), (14.3, 14.3)], cyan)
        line([(14.3, 18.4), (14.3, 14.3), (18.4, 14.3)], white)
    elif name == 'bloquear':
        line([(7.4, 10), (7.4, 7.4), (8.6, 4.7), (12, 3.6),
              (15.4, 4.7), (16.6, 7.4), (16.6, 10)], cyan, 1.9)
        line([(5.5, 10), (18.5, 10), (18.5, 21), (5.5, 21), (5.5, 10)], white)
        circle((12, 15), 1.1, cyan, 0.8, cyan)

    image = Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(2.5 * factor)), image)
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    # Discard nearly invisible edge spill from the glow so Windows never paints
    # a faint square around the glyph on light installer/desktop backgrounds.
    image.putalpha(image.getchannel('A').point(lambda alpha: 0 if alpha < 12 else alpha))
    return image


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
