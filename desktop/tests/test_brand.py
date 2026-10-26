from navix.brand import (icon_image, wizard_image, wizard_small_image,
                         navigation_icon, brazil_flag_frames, wordmark_image,
                         raised_label_image)


def test_navix_icon_has_alpha_and_scales():
    for size in (16, 32, 64, 256):
        image = icon_image(size)
        assert image.size == (size, size)
        assert image.mode == 'RGBA'
        assert image.getbbox() is not None


def test_wizard_art_is_generated_without_network():
    image = wizard_image()
    assert image.size == (480, 918)
    assert image.mode == 'RGB'
    assert image.getpixel((10, 10)) != image.getpixel((10, 900))


def test_circuito_vivo_emblem_is_the_primary_icon():
    from pathlib import Path
    from PIL import Image
    file = Path(__file__).resolve().parents[1] / 'assets' / 'circuitovivo_navix.png'
    assert file.is_file()
    with Image.open(file) as source:
        expected = source.convert('RGBA').resize((256, 256), Image.Resampling.LANCZOS)
    assert icon_image(256).tobytes() == expected.tobytes()


def test_installer_logo_has_right_margin_and_modern_nav_icons():
    small = wizard_small_image()
    assert small.size == (256, 256)
    assert small.mode == 'RGBA'
    assert small.getpixel((0, 0))[3] == 0  # no blue background tile
    assert small.getpixel((253, 125)) == small.getpixel((240, 125))
    signatures = set()
    for kind in ('inicio', 'permissoes', 'ferramentas', 'atividade',
                 'doacoes', 'assistente', 'minimizar', 'bloquear'):
        picture = navigation_icon(kind)
        assert picture.size == (22, 22)
        assert picture.mode == 'RGBA'
        assert picture.getpixel((0, 0))[3] == 0  # no generic square tile
        assert picture.getbbox()
        signatures.add(picture.tobytes())
    assert len(signatures) == 8  # every action has a distinct professional icon
    assert len(brazil_flag_frames()) == 4


def test_embossed_brand_has_compact_lettering_and_visible_alpha():
    for large, expected in ((False, (147, 42)), (True, (230, 60))):
        picture = wordmark_image(large=large)
        assert picture.size == expected
        assert picture.mode == 'RGBA'
        assert picture.getbbox()
    assert raised_label_image('MENU').getbbox()
