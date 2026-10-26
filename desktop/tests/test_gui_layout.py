"""Windows-only geometry regression for the old 570px-height clipping bug."""

import sys
import time

import pytest


def _tk_root(tk):
    """Cloud runners occasionally provide a broken Tcl path; retry once."""
    for attempt in range(2):
        try:
            return tk.Tk()
        except tk.TclError as error:
            if attempt:
                pytest.skip(f'Interface Tk indisponível neste executor Windows: {error}')
            time.sleep(0.3)


@pytest.mark.skipif(sys.platform != 'win32', reason='Requires a native Windows desktop')
def test_narrow_sidebar_keeps_language_section_scrollable():
    import tkinter as tk
    from navix.gui import ScrollableFrame

    root = _tk_root(tk)
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


@pytest.mark.skipif(sys.platform != 'win32', reason='Requires a native Windows desktop')
def test_pinned_language_footer_remains_visible_while_menu_scrolls():
    import tkinter as tk
    from navix.gui import ScrollableFrame

    root = _tk_root(tk)
    try:
        root.geometry('220x420')
        sidebar = tk.Frame(root, bg='#0d2936', width=220)
        sidebar.pack(fill='both', expand=True)
        sidebar.pack_propagate(False)
        view = ScrollableFrame(sidebar, '#0d2936')
        view.pack(side='top', fill='both', expand=True)
        for i in range(16):
            tk.Label(view.content, text=f'Menu {i}', height=2,
                     bg='#0d2936', fg='white').pack(fill='x')
        footer = tk.Frame(sidebar, bg='#0d2936', height=95)
        footer.pack(side='bottom', fill='x')
        footer.pack_propagate(False)
        language = tk.Label(footer, text='IDIOMA', bg='#0d2936', fg='white')
        language.pack()
        root.update()
        assert language.winfo_viewable()
        old_y = language.winfo_rooty()
        view.canvas.yview_moveto(1.0)
        root.update()
        assert language.winfo_viewable()
        assert language.winfo_rooty() == old_y
    finally:
        root.destroy()
