from navix.donations import (PIX_COPY_AND_PASTE, PIX_RANDOM_KEY,
                             crc16_ccitt, pix_fields, validate_pix_payload)


def test_owner_pix_payload_tlv_and_crc():
    fields = pix_fields(PIX_COPY_AND_PASTE)
    assert fields['26'].startswith('0014br.gov.bcb.pix')
    assert fields['59'] == 'WILSON_NEVES_DE_ALMEIDA'
    assert fields['60'] == 'CAMPO_GRANDE'
    assert crc16_ccitt(PIX_COPY_AND_PASTE[:-4]) == 'F73A'
    assert validate_pix_payload()


def test_pix_uuid_not_accidentally_confused_with_qr_email():
    fields = pix_fields(PIX_COPY_AND_PASTE)
    assert PIX_RANDOM_KEY not in fields['26']
    assert 'willson.alfamna+bancodobrasil@gmail.com' in fields['26']


def test_pix_corruption_is_rejected():
    assert not validate_pix_payload(PIX_COPY_AND_PASTE[:-1] + '0')
    assert not validate_pix_payload('0002012605abc')
    assert not validate_pix_payload('0002015204xx')


def test_generated_qr_uses_valid_payload():
    import importlib.util
    import pytest
    if importlib.util.find_spec('qrcode') is None:
        pytest.skip('qrcode installed in the application build environment')
    from navix.donations import pix_qr_image
    image = pix_qr_image(218)
    assert image.size == (218, 218)
    assert image.getpixel((0, 0)) == (255, 255, 255)
