"""Opt-in donation payload supplied by the project owner.

This is a BR Code, not a bank-account verification. The UUID key and the
email-based QR are different payment aliases. Never imply an official bank
partnership or initiate a transfer from this application.
"""

PIX_RANDOM_KEY = '918497d5-3d7a-428a-a2af-66064de489eb'
PIX_COPY_AND_PASTE = (
    '00020126680014br.gov.bcb.pix0139willson.alfamna+bancodobrasil@gmail.com'
    '0203Pix5204000053039865802BR5923WILSON_NEVES_DE_ALMEIDA'
    '6012CAMPO_GRANDE62290525ybbHJikxIqqp86ZQS6k4n2EVC6304F73A'
)


def crc16_ccitt(data):
    """CRC-16/CCITT-FALSE of the BR Code up to and including '6304'."""
    crc = 0xFFFF
    for value in data.encode('ascii'):
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f'{crc:04X}'


def pix_fields(payload):
    """Parse root TLV fields, rejecting truncated and malformed input."""
    fields = {}
    offset = 0
    while offset < len(payload):
        if offset + 4 > len(payload):
            raise ValueError('Cabeçalho Pix incompleto')
        code = payload[offset:offset + 2]
        size_text = payload[offset + 2:offset + 4]
        if not code.isdigit() or not size_text.isdigit():
            raise ValueError('Campo Pix inválido')
        size = int(size_text)
        offset += 4
        if offset + size > len(payload) or code in fields:
            raise ValueError('Comprimento ou repetição Pix inválida')
        fields[code] = payload[offset:offset + size]
        offset += size
    return fields


def validate_pix_payload(payload=PIX_COPY_AND_PASTE):
    try:
        fields = pix_fields(payload)
        account = pix_fields(fields['26'])
    except (ValueError, KeyError):
        return False
    return (payload.endswith('6304' + crc16_ccitt(payload[:-4]))
            and fields.get('00') == '01'
            and fields.get('53') == '986'
            and fields.get('58') == 'BR'
            and fields.get('63') == payload[-4:]
            and account.get('00') == 'br.gov.bcb.pix'
            and account.get('01') == 'willson.alfamna+bancodobrasil@gmail.com')


def pix_qr_image(size=218):
    """Render QR from the exact validated owner-supplied payload, without network."""
    if not validate_pix_payload():
        raise ValueError('O Pix fornecido não passou na validação de formato/CRC')
    import qrcode
    from PIL import Image
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=5, border=3)
    qr.add_data(PIX_COPY_AND_PASTE)
    qr.make(fit=True)
    return qr.make_image(fill_color='#091526', back_color='#ffffff').convert('RGB').resize(
        (size, size), Image.Resampling.NEAREST)
