from navix.brand import icon_image, wizard_image


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
