"""Windows-only geometry regression for the old 570px-height clipping bug."""

import sys

import pytest


@pytest.mark.skipif(sys.platform != 'win32', reason='Requires a native Windows desktop')
def test_narrow_sidebar_keeps_language_section_scrollable():
    import tkinter as tk
    from navix.gui import ScrollableFrame

    root = tk.Tk()
    try:
        root.geometry('270x300')
        viewport = ScrollableFrame(root, '#101b2e', width=250)
        viewport.pack(fill='both', expand=True)
        for i in range(16):
            tk.Label(viewport.content, text=f'Option {i}',
                     height=2, bg='#101b2e', fg='white').pack(fill='x')
        language = tk.Label(viewport.content, text='IDIOMA', bg='#101b2e', fg='white')
        language.pack(fill='x')
        root.update()
        assert viewport.canvas.winfo_height() < viewport.content.winfo_reqheight()
        viewport.canvas.yview_moveto(1.0)
        root.update()
        assert viewport.canvas.yview()[1] >= 0.99
        assert language.winfo_exists()
    finally:
        root.destroy()
