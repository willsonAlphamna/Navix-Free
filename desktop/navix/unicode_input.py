"""Windows SendInput, including UTF-16 surrogate pairs, on 32/64 bit."""
import ctypes
import sys


def type_unicode(text, session):
    if sys.platform != 'win32':
        raise RuntimeError('Digitação Unicode disponível somente no Windows.')
    from ctypes import wintypes
    class Mouse(ctypes.Structure):
        _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG), ('mouseData', wintypes.DWORD),
                    ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('extra', ctypes.c_size_t)]
    class Keyboard(ctypes.Structure):
        _fields_ = [('vk', wintypes.WORD), ('scan', wintypes.WORD), ('flags', wintypes.DWORD),
                    ('time', wintypes.DWORD), ('extra', ctypes.c_size_t)]
    class Hardware(ctypes.Structure):
        _fields_ = [('message', wintypes.DWORD), ('low', wintypes.WORD), ('high', wintypes.WORD)]
    class Union(ctypes.Union):
        _fields_ = [('mi', Mouse), ('ki', Keyboard), ('hi', Hardware)]
    class Input(ctypes.Structure):
        _anonymous_ = ('u',)
        _fields_ = [('kind', wintypes.DWORD), ('u', Union)]
    send = ctypes.windll.user32.SendInput
    send.argtypes = (wintypes.UINT, ctypes.POINTER(Input), ctypes.c_int)
    send.restype = wintypes.UINT
    encoded = text.encode('utf-16-le')
    for index in range(0, len(encoded), 2):
        session.require('desktop')
        unit = int.from_bytes(encoded[index:index+2], 'little')
        events = (Input * 2)(Input(kind=1, ki=Keyboard(scan=unit, flags=4)),
                             Input(kind=1, ki=Keyboard(scan=unit, flags=6)))
        if send(2, events, ctypes.sizeof(Input)) != 2:
            raise RuntimeError('Windows bloqueou a digitação nesta janela.')
