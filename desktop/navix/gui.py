import importlib.metadata
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .core import Session
from .browser import Browser
from .desktop import Desktop
from .server import Service
from .diagnostics import Diagnostics
from .i18n import LANGUAGES, load_language, save_language, translate
from .owner_auth import OwnerAccount
from .tunnel_manager import TunnelManager, TunnelSettings
from .donations import PIX_COPY_AND_PASTE, PIX_RANDOM_KEY, pix_qr_image
from . import __version__


class ScrollableFrame(tk.Frame):
    """A width-aware vertical viewport for low-resolution and high-DPI screens."""

    def __init__(self, parent, background, **kwargs):
        super().__init__(parent, bg=background, **kwargs)
        self.canvas = tk.Canvas(self, bg=background, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.content = tk.Frame(self.canvas, bg=background)
        self._window = self.canvas.create_window((0, 0), window=self.content, anchor='nw')
        self.content.bind('<Configure>', self._update_scrollregion)
        self.canvas.bind('<Configure>', self._resize_content)
        self.canvas.bind('<Enter>', lambda event: self.canvas.bind_all('<MouseWheel>', self._mousewheel))
        self.canvas.bind('<Leave>', lambda event: self.canvas.unbind_all('<MouseWheel>'))
        self.bind('<Destroy>', self._cleanup, add='+')

    def _update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _resize_content(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)

    def _mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(-int(event.delta / 120), 'units')

    def _cleanup(self, event):
        if event.widget is self:
            self.canvas.unbind_all('<MouseWheel>')


class Panel:
    """Native, low-memory Windows dashboard. All actions remain local and opt-in."""

    COLORS = {
        'base': '#0b1120', 'sidebar': '#0d2936', 'surface': '#152238',
        'surface2': '#1b2c46', 'outline': '#273a56', 'text': '#f2f7ff',
        'subtle': '#9fb1c9', 'blue': '#2878f0', 'blue_hover': '#4092ff',
        'cyan': '#60d6e7', 'green': '#58d5a1', 'red': '#ef6477', 'blood': '#d42642', 'shadow': '#080f1c',
    }

    def __init__(self, root):
        self.root = root
        directory = Path(os.environ.get('NAVIX_PROFILE_DIR') or
                         (Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'NavixDesktop'))
        self.directory = directory
        installer_lang = None
        if '--lang' in sys.argv:
            try:
                installer_lang = sys.argv[sys.argv.index('--lang') + 1]
            except IndexError:
                pass
        self.language = load_language(directory, installer_lang)
        self.selected_language_name = tk.StringVar(value=LANGUAGES[self.language])
        self.session = Session(directory)
        self.owner_account = OwnerAccount(directory)
        self._authenticated = False
        self._login_dialog = None
        self.diagnostics = Diagnostics(directory)
        self.browser = Browser(self.session)
        self.service = Service(self.session, self.browser, Desktop(self.session), port=0)
        self.tunnel_settings = TunnelSettings(directory)
        self.tunnel = TunnelManager(self.session, self.service, self._tunnel_event)
        # Staging only: never starts cloud access on application launch.
        self.cloud_controller = None
        cloud_url = os.environ.get('NAVIX_CLOUD_WSS_URL', '')
        if cloud_url:
            from .cloud_controller import CloudController
            self.cloud_controller = CloudController(
                directory, self.session, self.service, cloud_url,
                on_status=lambda status: self.events.put(status))
        self.tunnel_state = tk.StringVar(value='Túnel desligado')
        self._tunnel_worker_running = False
        self._last_tunnel_state = ''
        self._last_health = None
        self._flag_timer = None
        self._cloud_start_pending = False
        self._cloud_next_retry = 0.0
        self._local_next_repair = 0.0
        self.cloud_state_text = tk.StringVar(value='Nuvem: desconectada')
        self.cloud_details = tk.StringVar(value='Conecte localmente para iniciar o Cloud.')
        self.events = queue.Queue()
        self.busy = False
        self.tray = None
        self._permission_preferences = directory / 'permissions.json'
        try:
            preferred = json.loads(self._permission_preferences.read_text(encoding='utf-8'))
            preferred = preferred if isinstance(preferred, list) else []
        except (OSError, ValueError):
            preferred = []
        # Remember checkboxes only, never an authorization or an active token.
        self.browser_allowed = tk.BooleanVar(value='browser' in preferred)
        self.desktop_allowed = tk.BooleanVar(value='desktop' in preferred)
        self.files_allowed = tk.BooleanVar(value='files' in preferred)
        self.commands_allowed = tk.BooleanVar(value='commands' in preferred)
        self.duration_minutes = tk.StringVar(value='30')
        self.state = tk.StringVar(value='DESCONECTADO — acesso desativado')
        self.status_details = tk.StringVar(value='Ative uma sessão para usar as ferramentas locais.')
        self.port_details = tk.StringVar(value='Aguardando inicialização')
        self.permission_details = tk.StringVar(value='0 de 4 recursos autorizados')
        self.activity_text = tk.StringVar(value='Aguardando a primeira ação')
        self.side_connection = tk.StringVar(value='● DESCONECTADO')
        self.side_service = tk.StringVar(value='Servidor inativo')
        self.side_duration = tk.StringVar(value='Sem sessão autorizada')
        self.root.title('NavixX Desktop ' + __version__ + ' • Central de Controle')
        available_w, available_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.compact_mode = available_h <= 800 or available_w <= 1050
        window_w = min(1120, max(800, available_w - 80))
        window_h = min(780, max(570, available_h - 90))
        self.root.geometry(f'{window_w}x{window_h}')
        self.root.minsize(min(800, window_w), min(570, window_h))
        self.root.configure(bg=self.COLORS['base'])
        icon = Path(getattr(sys, '_MEIPASS', Path(__file__).parent.parent)) / 'assets/navix.ico'
        if icon.is_file():
            self.root.iconbitmap(str(icon))
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Navix.TCombobox', fieldbackground='#243550', background='#243550',
                        foreground='#ffffff', arrowcolor='#dce8fc', padding=7)
        style.map('Navix.TCombobox', fieldbackground=[('readonly', '#243550')],
                  foreground=[('readonly', '#ffffff')])
        self._build_ui()
        self.show('Pronto para configurar. Escolha as permissões e clique em Conectar / Autorizar.\n'
                  'O servidor MCP funciona neste computador. Conexão remota exige autenticação própria.')
        self.setup_tray()
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.after(500, self.tick)
        # Check bundled package versions automatically without granting access.
        self.root.after(1600, self.diagnose)
        # Native owner authentication is separate from OpenAI and MCP permissions.
        self.root.withdraw()
        self.root.after(20, self.require_owner_login)

    def _text(self, parent, value, size=10, weight='normal', color=None, **kwargs):
        return tk.Label(parent, text=translate(value, self.language), bg=parent.cget('bg'),
                        fg=color or self.COLORS['text'],
                        font=('Segoe UI', size, weight), **kwargs)

    def _button(self, parent, label, action, tone='neutral', **kwargs):
        palette = {
            'primary': (self.COLORS['blue'], '#ffffff', self.COLORS['blue_hover']),
            'danger': ('#482738', '#ff9dac', '#5b2f43'),
            'neutral': (self.COLORS['surface2'], self.COLORS['text'], '#304666'),
            'subtle': (self.COLORS['sidebar'], '#bed9e6', '#16495f'),
        }
        bg, fg, hover = palette[tone]
        button = tk.Button(parent, text=translate(label, self.language), command=action, bg=bg, fg=fg,
                           activebackground=hover, activeforeground='#ffffff',
                           cursor='hand2', relief='raised', bd=1,
                           font=('Segoe UI', 10, 'bold'),
                           padx=10 if self.compact_mode else 15,
                           pady=5 if self.compact_mode else 9, **kwargs)
        button.bind('<Enter>', lambda event: button.configure(bg=hover))
        button.bind('<Leave>', lambda event: button.configure(bg=bg))
        return button

    def _card(self, parent, pad=18):
        # Layered highlight and drop shadow provide depth without a heavy GUI toolkit.
        if self.compact_mode:
            pad = max(10, round(pad * 0.65))
        shadow = tk.Frame(parent, bg=self.COLORS['shadow'], padx=1, pady=3)
        edge = tk.Frame(shadow, bg='#3b5877', padx=1, pady=1)
        edge.pack(fill='both', expand=True)
        inner = tk.Frame(edge, bg=self.COLORS['surface'], padx=pad, pady=pad)
        inner.pack(fill='both', expand=True)
        return shadow, inner

    def _wordmark(self, parent, large=False):
        row = tk.Frame(parent, bg=parent.cget('bg'))
        try:
            from PIL import ImageTk
            from .brand import wordmark_image
            photo = ImageTk.PhotoImage(wordmark_image(large=large))
            if not hasattr(self, '_brand_words'):
                self._brand_words = []
            self._brand_words.append(photo)
            tk.Label(row, image=photo, bg=row.cget('bg')).pack(side='left')
        except Exception:
            self._text(row, 'NavixX', 24 if large else 16,
                       'bold', '#3688ff').pack(side='left')
        return row

    def require_owner_login(self):
        """Show a real local password gate; never start an MCP session here."""
        if self._login_dialog and self._login_dialog.winfo_exists():
            self._login_dialog.lift()
            return
        self.root.withdraw()
        self._authenticated = False
        create = not self.owner_account.exists
        box = tk.Toplevel(self.root)
        self._login_dialog = box
        box.title('NavixX Desktop — ' + translate(
                  'Criar login local' if create else 'Entrar', self.language))
        box.geometry('450x355' if create else '450x300')
        box.resizable(False, False)
        box.configure(bg=self.COLORS['sidebar'])
        box.protocol('WM_DELETE_WINDOW', self.close)
        panel = tk.Frame(box, bg=self.COLORS['sidebar'], padx=28, pady=20)
        panel.pack(fill='both', expand=True)
        self._text(panel, 'NAVIX DESKTOP', 19, 'bold',
                   self.COLORS['cyan']).pack(anchor='w')
        self._text(panel, 'Proteção do painel deste usuário Windows', 10,
                   color=self.COLORS['subtle']).pack(anchor='w', pady=(3, 14))
        self._text(panel, 'Crie uma senha local' if create else 'Digite a senha local',
                   11, 'bold').pack(anchor='w', pady=(0, 5))
        password = tk.StringVar()
        entry = tk.Entry(panel, textvariable=password, show='•',
                         bg=self.COLORS['surface2'], fg='#ffffff',
                         insertbackground='#ffffff', relief='flat',
                         font=('Segoe UI', 12))
        entry.pack(fill='x', ipady=7)
        confirmation = tk.StringVar()
        if create:
            self._text(panel, 'Confirme a senha (mínimo 10 caracteres)', 10,
                       color=self.COLORS['subtle']).pack(anchor='w', pady=(12, 5))
            tk.Entry(panel, textvariable=confirmation, show='•',
                     bg=self.COLORS['surface2'], fg='#ffffff',
                     insertbackground='#ffffff', relief='flat',
                     font=('Segoe UI', 12)).pack(fill='x', ipady=7)
        feedback = tk.StringVar(value=translate(
            'Login local, não é sua senha OpenAI.', self.language))
        self._text(panel, '', 9, color=self.COLORS['cyan'],
                   textvariable=feedback, wraplength=390).pack(anchor='w', pady=(14, 8))

        def submit():
            try:
                if create:
                    if password.get() != confirmation.get():
                        raise ValueError('As duas senhas não coincidem.')
                    self.owner_account.enroll(password.get())
                elif not self.owner_account.verify(password.get()):
                    wait = self.owner_account.seconds_until_retry()
                    raise ValueError('Senha incorreta.' +
                                     (f' Aguarde {wait}s para tentar de novo.' if wait else ''))
            except (ValueError, OSError) as error:
                feedback.set(str(error))
                password.set('')
                confirmation.set('')
                return
            password.set('')
            confirmation.set('')
            self._authenticated = True
            box.grab_release()
            box.destroy()
            self._login_dialog = None
            self.root.deiconify()
            self.root.lift()
            self.diagnostics.record('owner', 'login_success')

        self._button(panel, 'Criar login e entrar' if create else 'Entrar no NavixX',
                     submit, tone='primary').pack(fill='x', pady=(7, 0))
        entry.bind('<Return>', lambda event: submit())
        # Tk can reject a grab until Windows has actually mapped the dialog.
        def activate_login_dialog():
            if not box.winfo_exists():
                return
            try:
                box.grab_set()
                entry.focus_force()
            except tk.TclError:
                box.after(100, activate_login_dialog)
        box.after(100, activate_login_dialog)

    def lock_panel(self):
        """Lock always revokes remote control, including unlimited sessions."""
        self.stop()
        self.diagnostics.record('owner', 'panel_locked')
        self.require_owner_login()

    def _section_title(self, parent, title, detail):
        self._text(parent, title, 19 if self.compact_mode else 23, 'bold').pack(anchor='w')
        self._text(parent, detail, 9 if self.compact_mode else 10,
                   color=self.COLORS['subtle'],
                   wraplength=435 if self.compact_mode else 650,
                   justify='left').pack(anchor='w', pady=(3, 9 if self.compact_mode else 20))

    def _build_ui(self):
        shell = tk.Frame(self.root, bg=self.COLORS['base'])
        self.shell = shell
        shell.pack(fill='both', expand=True)
        sidebar = tk.Frame(shell, bg=self.COLORS['sidebar'],
                           width=220 if self.compact_mode else 250)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        side_view = ScrollableFrame(sidebar, self.COLORS['sidebar'])
        side_view.pack(side='top', fill='both', expand=True)
        side = side_view.content
        self.side_view = side_view
        brand = tk.Frame(side, bg=self.COLORS['sidebar'],
                         padx=10 if self.compact_mode else 16,
                         pady=8 if self.compact_mode else 22)
        brand.pack(fill='x')
        try:
            from PIL import ImageTk
            from .brand import icon_image
            self.brand_photo = ImageTk.PhotoImage(icon_image(48 if self.compact_mode else 64))
            tk.Label(brand, image=self.brand_photo, bg=self.COLORS['sidebar']).pack(side='left')
        except Exception:
            self._text(brand, 'NX', 24, 'bold', self.COLORS['cyan']).pack(side='left')
        wordmark = tk.Frame(brand, bg=self.COLORS['sidebar'])
        wordmark.pack(side='left', padx=(5 if self.compact_mode else 8, 0))
        self._wordmark(wordmark).pack(anchor='w')
        from .brand import raised_label_image
        self.desktop_word = ImageTk.PhotoImage(raised_label_image('DESKTOP', 12))
        tk.Label(wordmark, image=self.desktop_word,
                 bg=self.COLORS['sidebar']).pack(anchor='w')
        self.menu_word = ImageTk.PhotoImage(raised_label_image('MENU', 13))
        tk.Label(side, image=self.menu_word, bg=self.COLORS['sidebar']).pack(
            anchor='w', padx=14 if self.compact_mode else 19,
            pady=(6, 3) if self.compact_mode else (14, 10))
        self.nav_buttons = {}
        from PIL import ImageTk
        from .brand import navigation_icon
        self.nav_icons = {key: ImageTk.PhotoImage(navigation_icon(key, size=24 if self.compact_mode else 26)) for key in
                          ('inicio', 'permissoes', 'ferramentas', 'atividade',
                           'doacoes', 'assistente', 'minimizar', 'bloquear')}
        for key, label in (
            ('inicio', 'Início'),
            ('permissoes', 'Permissões'),
            ('ferramentas', 'Ferramentas'),
            ('atividade', 'Atividade'),
            ('doacoes', 'Apoie o projeto'),
        ):
            item = self._button(side, label, lambda selected=key: self.show_page(selected),
                                tone='subtle', anchor='w', image=self.nav_icons[key],
                                compound='left')
            item.pack(fill='x', padx=8 if self.compact_mode else 12,
                      pady=2 if self.compact_mode else 4)
            self.nav_buttons[key] = item
        tk.Frame(side, bg=self.COLORS['outline'], height=1).pack(
            fill='x', padx=18, pady=(7, 6) if self.compact_mode else (17, 12))
        self._button(side, 'Assistente', self.open_setup, tone='subtle',
                     anchor='w', image=self.nav_icons['assistente'],
                     compound='left').pack(fill='x', padx=8, pady=2 if self.compact_mode else 4)
        self._button(side, 'Minimizar', self.hide, tone='subtle',
                     anchor='w', image=self.nav_icons['minimizar'],
                     compound='left').pack(fill='x', padx=8, pady=2 if self.compact_mode else 4)
        self._button(side, 'Bloquear painel', self.lock_panel, tone='subtle',
                     anchor='w', image=self.nav_icons['bloquear'],
                     compound='left').pack(fill='x', padx=8, pady=2 if self.compact_mode else 4)

        # Live status occupies the otherwise empty part of the navigation rail.
        state_card = tk.Frame(side, bg=self.COLORS['surface'],
                              padx=9 if self.compact_mode else 15,
                              pady=7 if self.compact_mode else 16,
                              highlightbackground='#355575', highlightthickness=1,
                              relief='raised', bd=1)
        state_card.pack(fill='x', padx=8 if self.compact_mode else 14,
                        pady=(8, 4) if self.compact_mode else (30, 8))
        self._text(state_card, 'SESSÃO LOCAL', 9, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self.side_status_label = self._text(
            state_card, '', 11, 'bold', self.COLORS['red'],
            textvariable=self.side_connection, anchor='w', justify='left')
        self.side_status_label.pack(fill='x', pady=(4, 3) if self.compact_mode else (13, 7))
        self._text(state_card, '', 9, color=self.COLORS['subtle'],
                   textvariable=self.side_service, anchor='w').pack(fill='x')
        self._text(state_card, '', 9, color=self.COLORS['subtle'],
                   textvariable=self.side_duration, anchor='w').pack(
            fill='x', pady=(5, 0))
        # Keep language selection visible even when navigation has to scroll.
        footer = tk.Frame(sidebar, bg=self.COLORS['sidebar'])
        footer.pack(side='bottom', fill='x', padx=10 if self.compact_mode else 18,
                    pady=(6, 8) if self.compact_mode else (16, 20))
        self._text(footer, 'IDIOMA', 8, 'bold', self.COLORS['cyan']).pack(anchor='w')
        language_picker = ttk.Combobox(footer, textvariable=self.selected_language_name,
                                      values=list(LANGUAGES.values()), style='Navix.TCombobox',
                                      state='readonly', width=19)
        language_picker.pack(fill='x', pady=(3, 5) if self.compact_mode else (5, 9))
        language_picker.bind('<<ComboboxSelected>>', self.change_language)
        self._text(footer, 'CONTROLE SOB SUA AUTORIZAÇÃO', 8, 'bold',
                   self.COLORS['green']).pack(anchor='w')
        from PIL import ImageTk
        from .brand import brazil_flag_frames
        self.flag_images = [ImageTk.PhotoImage(frame) for frame in brazil_flag_frames()]
        copyright_line = tk.Frame(footer, bg=self.COLORS['sidebar'])
        copyright_line.pack(fill='x', pady=(7, 0))
        self.flag_widget = tk.Label(copyright_line, image=self.flag_images[0],
                                    bg=self.COLORS['sidebar'])
        self.flag_widget.pack(side='left', padx=(0, 5))
        self._text(copyright_line, 'ALFAMNA © 2026 — Todos os direitos reservados.',
                   7, color=self.COLORS['subtle'], wraplength=155,
                   justify='left').pack(side='left')
        self._text(footer, 'Versão ' + __version__, 8,
                   color=self.COLORS['subtle']).pack(anchor='w', pady=(2, 0))
        self._start_flag_animation()

        main = tk.Frame(shell, bg=self.COLORS['base'],
                        padx=13 if self.compact_mode else 24,
                        pady=12 if self.compact_mode else 22)
        main.pack(side='left', fill='both', expand=True)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)
        self.pages = {}
        self.page_frames = {}
        for key in ('inicio', 'permissoes', 'ferramentas', 'atividade', 'doacoes'):
            if key == 'atividade':
                page = tk.Frame(main, bg=self.COLORS['base'])
                view = page
            else:
                view = ScrollableFrame(main, self.COLORS['base'])
                page = view.content
            view.grid(row=0, column=0, sticky='nsew')
            self.page_frames[key] = view
            self.pages[key] = page
        self._home_page(self.pages['inicio'])
        self._permissions_page(self.pages['permissoes'])
        self._tools_page(self.pages['ferramentas'])
        self._activity_page(self.pages['atividade'])
        self._donations_page(self.pages['doacoes'])
        self.show_page('inicio')

    def _start_flag_animation(self):
        if self._flag_timer:
            self.root.after_cancel(self._flag_timer)
            self._flag_timer = None
        if os.environ.get('NAVIX_REDUCED_MOTION') == '1':
            return
        self._flag_index = 0
        def next_frame():
            if self.flag_widget.winfo_exists():
                self._flag_index = (self._flag_index + 1) % len(self.flag_images)
                self.flag_widget.configure(image=self.flag_images[self._flag_index])
                self._flag_timer = self.root.after(480, next_frame)
        self._flag_timer = self.root.after(480, next_frame)

    def change_language(self, event=None):
        desired = next((key for key, name in LANGUAGES.items()
                        if name == self.selected_language_name.get()), 'pt-BR')
        if desired == self.language:
            return
        old_log = self.output.get('1.0', 'end')
        self.language = desired
        save_language(self.directory, desired)
        if self._flag_timer:
            self.root.after_cancel(self._flag_timer)
            self._flag_timer = None
        self._brand_words = []
        self.shell.destroy()
        self._build_ui()
        self.root.title('NavixX Desktop ' + __version__)
        self.output.insert('end', old_log)

    def _tunnel_event(self, event, result):
        self.session.audit(event, result)
        self.diagnostics.record('tunnel', event, result,
                                'error' if result == 'error' else 'info')
        self.events.put(('tunnel_event', event, result))
        if event == 'tunnel.process_exited':
            self.events.put(('tunnel_message', self.tunnel.error))

    def _launch_tunnel_worker(self):
        if self._tunnel_worker_running:
            return
        self._tunnel_worker_running = True
        def work():
            try:
                message = self.tunnel.connect()
                self.events.put(('tunnel_message', message))
            finally:
                self.events.put(('tunnel_done',))
        threading.Thread(target=work, daemon=True).start()

    def connect_tunnel(self, tunnel_id, api_key, remember=False):
        """User-initiated from wizard; credentials stay out of argv/log files."""
        self.tunnel_settings.save(tunnel_id, api_key, remember=remember)
        self.tunnel.configure(tunnel_id, api_key)
        self._launch_tunnel_worker()

    def disconnect_tunnel(self):
        self.tunnel.stop()
        self.tunnel_state.set('Túnel desligado')
        self.show('Túnel remoto desconectado pelo proprietário.')

    def show_page(self, key):
        self.page_frames[key].tkraise()
        for page_key, button in self.nav_buttons.items():
            active = page_key == key
            button.configure(bg='#18556d' if active else self.COLORS['sidebar'],
                             fg=self.COLORS['text'] if active else '#bed9e6')

    def _home_page(self, page):
        gap = 8 if self.compact_mode else 16
        headline = tk.Frame(page, bg=self.COLORS['base'])
        headline.pack(anchor='w', fill='x')
        self._text(headline, 'Bem-vindo', 19 if self.compact_mode else 23,
                   'bold', self.COLORS['blood']).pack(side='left')
        self._text(headline, ' ao ', 19 if self.compact_mode else 23,
                   'bold', '#ffffff').pack(side='left')
        self._wordmark(headline, large=True).pack(side='left')
        self._text(page, 'Seu computador e suas automações em um único lugar.',
                   10, color=self.COLORS['subtle']).pack(anchor='w', pady=(4, gap))
        frame, card = self._card(page, pad=24)
        frame.pack(fill='x', pady=(0, gap))
        top = tk.Frame(card, bg=self.COLORS['surface'])
        top.pack(fill='x')
        self._text(top, 'STATUS DA CONEXÃO', 9, 'bold', self.COLORS['cyan']).pack(side='left')
        self._text(top, 'MCP LOCAL', 9, 'bold', self.COLORS['subtle']).pack(side='right')
        self._text(card, 'Conexão protegida neste PC • uso remoto requer pareamento autenticado',
                   9, color=self.COLORS['subtle'],
                   wraplength=420 if self.compact_mode else 580,
                   justify='left').pack(anchor='w', pady=(5 if self.compact_mode else 11, 0))
        self.status_label = self._text(card, '', 14 if self.compact_mode else 17,
                                       'bold', self.COLORS['red'],
                                       textvariable=self.state, anchor='w',
                                       wraplength=420 if self.compact_mode else 610,
                                       justify='left')
        # Remove literal text so textvariable is the single source of truth.
        self.status_label.configure(text='')
        self.status_label.pack(fill='x', pady=(8 if self.compact_mode else 15,
                                             4 if self.compact_mode else 8))
        self._text(card, '', 10, color=self.COLORS['subtle'],
                   textvariable=self.status_details, anchor='w',
                   justify='left').pack(fill='x')
        actions = tk.Frame(card, bg=self.COLORS['surface'])
        actions.pack(fill='x', pady=(9 if self.compact_mode else 20, 0))
        self._button(actions, 'Configurar acesso', lambda: self.show_page('permissoes'),
                     tone='primary').pack(side='left', padx=(0, 9))
        self._button(actions, 'PARAR ACESSO', self.stop, tone='danger').pack(side='left')
        cards = tk.Frame(page, bg=self.COLORS['base'])
        cards.pack(fill='x', pady=(0, gap))
        left_edge, left = self._card(cards, pad=18)
        left_edge.pack(side='left', fill='both', expand=True, padx=(0, 8))
        self._text(left, 'SERVIDOR MCP', 9, 'bold', self.COLORS['subtle']).pack(anchor='w')
        self._text(left, '', 11, 'bold', textvariable=self.port_details).pack(
            anchor='w', pady=(4 if self.compact_mode else 10, 0))
        right_edge, right = self._card(cards, pad=18)
        right_edge.pack(side='left', fill='both', expand=True, padx=(8, 0))
        self._text(right, 'PERMISSÕES ATIVAS', 9, 'bold', self.COLORS['subtle']).pack(anchor='w')
        self._text(right, '', 11, 'bold', textvariable=self.permission_details).pack(
            anchor='w', pady=(4 if self.compact_mode else 10, 0))
        foot_edge, foot = self._card(page)
        foot_edge.pack(fill='x')
        self._text(foot, 'ACESSO RÁPIDO', 10, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(foot, 'Abra o navegador ou use o assistente para configurar o pareamento.',
                   9 if self.compact_mode else 10,
                   color=self.COLORS['subtle']).pack(anchor='w',
                        pady=(4, 7) if self.compact_mode else (7, 14))
        buttons = tk.Frame(foot, bg=self.COLORS['surface'])
        buttons.pack(fill='x')
        self._button(buttons, 'Abrir navegador', lambda: self.open_browser('integrado'),
                     tone='neutral').pack(side='left', padx=(0, 8))
        self._button(buttons, 'Assistente de conexão', self.open_setup,
                     tone='neutral').pack(side='left')
        self._text(page, 'Última atividade', 10, 'bold', self.COLORS['subtle']).pack(
            anchor='w', pady=(9 if self.compact_mode else 22, 3))
        self._text(page, '', 10, color=self.COLORS['text'],
                   textvariable=self.activity_text,
                   wraplength=440 if self.compact_mode else 650,
                   anchor='w', justify='left').pack(fill='x')

    def _permission_item(self, parent, flag, title, subtitle):
        wrap = tk.Frame(parent, bg=self.COLORS['surface2'],
                        pady=4 if self.compact_mode else 8,
                        padx=9 if self.compact_mode else 12)
        wrap.pack(fill='x', pady=2 if self.compact_mode else 5)
        control = tk.Checkbutton(wrap, text=title, variable=flag,
                                 command=self.permissions_changed, bg=self.COLORS['surface2'],
                                 fg=self.COLORS['text'], selectcolor=self.COLORS['base'],
                                 activebackground=self.COLORS['surface2'],
                                 activeforeground='#ffffff', anchor='w', cursor='hand2',
                                 font=('Segoe UI', 10, 'bold'), padx=7,
                                 pady=0 if self.compact_mode else 2)
        control.pack(fill='x')
        self._text(wrap, subtitle, 8 if self.compact_mode else 9,
                   color=self.COLORS['subtle'],
                   wraplength=425 if self.compact_mode else 535).pack(
            anchor='w', padx=31)

    def _permissions_page(self, page):
        gap = 7 if self.compact_mode else 15
        self._section_title(page, 'Permissões e segurança',
                            'Escolha exatamente o que o NAVIX pode controlar neste PC.')
        frame, card = self._card(page, pad=18)
        frame.pack(fill='x', pady=(0, gap))
        self._permission_item(card, self.browser_allowed, 'Navegador',
                              'Abrir páginas, clicar, preencher e baixar arquivos autorizados.')
        self._permission_item(card, self.desktop_allowed, 'Mouse, teclado e tela',
                              'Controlar a área de trabalho e capturar imagens.')
        self._permission_item(card, self.files_allowed, 'Arquivos e pastas',
                              'Ler, criar, editar, mover ou apagar arquivos.')
        self._permission_item(card, self.commands_allowed, 'Comandos e programas',
                              'Executar PowerShell, Python e outros programas.')
        row = tk.Frame(page, bg=self.COLORS['base'])
        row.pack(fill='x', pady=(0, gap))
        self._text(row, 'Tempo de autorização:', 10, 'bold').pack(side='left', padx=(0, 10))
        ttk.Combobox(row, textvariable=self.duration_minutes,
                     values=('30', '60', '120', '240', translate('Sem prazo', self.language)),
                     style='Navix.TCombobox', state='readonly', width=12).pack(side='left')
        self._text(row, 'minutos', 10, color=self.COLORS['subtle']).pack(side='left', padx=10)
        actions = tk.Frame(page, bg=self.COLORS['base'])
        actions.pack(fill='x')
        self._button(actions, 'Marcar todas', self.select_all).pack(side='left', padx=(0, 8))
        self._button(actions, 'Conectar / Autorizar', self.connect,
                     tone='primary').pack(side='left', padx=(0, 8))
        self._button(actions, 'PARAR ACESSO', self.stop, tone='danger').pack(side='left')
        self._text(page, 'Alterar qualquer permissão revoga a sessão atual.\n'
                   'Acesso completo exige sua confirmação; não ultrapassa os limites do Windows.',
                   9, color=self.COLORS['subtle'], justify='left').pack(
                       anchor='w', pady=(7 if self.compact_mode else 16, 0))

    def _tools_page(self, page):
        gap = 7 if self.compact_mode else 16
        self._section_title(page, 'Ferramentas', 'Navegação, diagnóstico e pareamento em áreas separadas.')
        web_edge, web = self._card(page)
        web_edge.pack(fill='x', pady=(0, gap))
        self._text(web, 'NAVEGAÇÃO', 12, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(web, 'O navegador usa perfil próprio de automação.',
                   9 if self.compact_mode else 10, color=self.COLORS['subtle']).pack(
                       anchor='w', pady=(4, 6) if self.compact_mode else (7, 14))
        row = tk.Frame(web, bg=self.COLORS['surface'])
        row.pack(fill='x')
        self._button(row, 'Abrir navegador integrado',
                     lambda: self.open_browser('integrado'), tone='primary').pack(
            side='left', padx=(0, 8))
        self._button(row, 'Abrir Opera',
                     lambda: self.open_browser('opera')).pack(side='left')
        system_edge, system = self._card(page)
        system_edge.pack(fill='x', pady=(0, gap))
        self._text(system, 'DIAGNÓSTICO E REPARO', 12, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(system, 'Veja o estado real do servidor ou reinicie uma conexão parada.',
                   9 if self.compact_mode else 10, color=self.COLORS['subtle']).pack(
                       anchor='w', pady=(4, 6) if self.compact_mode else (7, 14))
        row = tk.Frame(system, bg=self.COLORS['surface'])
        row.pack(fill='x')
        self._button(row, 'Diagnosticar', self.diagnose).pack(side='left', padx=(0, 8))
        self._button(row, 'Reparar conexão', self.repair).pack(side='left')
        pair_edge, pair = self._card(page)
        pair_edge.pack(fill='x')
        if not self.cloud_controller:
            self._text(pair, 'PAREAMENTO LOCAL AVANÇADO', 12, 'bold',
                       self.COLORS['cyan']).pack(anchor='w')
            self._text(pair, 'Copie a credencial apenas para um cliente MCP local autorizado. '
                       'Este código não conecta automaticamente o ChatGPT.',
                       9, color=self.COLORS['subtle'], wraplength=530,
                       justify='left').pack(anchor='w', pady=(5, 10))
            row = tk.Frame(pair, bg=self.COLORS['surface'])
            row.pack(fill='x')
            self._button(row, 'Copiar pareamento local', self.copy_pairing,
                         tone='primary').pack(side='left', padx=(0, 8))
            self._button(row, 'Assistente', self.open_setup).pack(side='left')
        else:
            # Keep the unrelated localhost bearer token out of the Cloud UI.
            self._text(pair, 'NAVIX CLOUD 0.3 — cada PC usa um código temporário próprio.',
                       10, 'bold', self.COLORS['cyan']).pack(anchor='w', pady=(12, 4))
            self._text(pair, '', 11, 'bold', self.COLORS['cyan'],
                       textvariable=self.cloud_state_text).pack(anchor='w', pady=(7, 2))
            self._text(pair, '', 9, color=self.COLORS['text'],
                       textvariable=self.cloud_details, wraplength=530,
                       justify='left').pack(anchor='w', pady=(0, 10))
            cloud_actions = tk.Frame(pair, bg=self.COLORS['surface'])
            cloud_actions.pack(fill='x')
            self._button(cloud_actions, 'Vincular ao ChatGPT', self.enroll_cloud,
                         tone='primary').pack(side='left', padx=(0, 8))
            self._button(cloud_actions, 'Reparar conexão Cloud', self.repair).pack(side='left')
            self._text(pair, 'O Cloud dispensa chave Runtime no cofre e não usa o túnel antigo. '
                       'A confirmação inicial de vínculo no ChatGPT continua obrigatória.',
                       9, color=self.COLORS['subtle'], wraplength=530,
                       justify='left').pack(anchor='w', pady=(10, 0))

        uninstall_edge, uninstall_card = self._card(page)
        uninstall_edge.pack(fill='x', pady=(gap, 4 if self.compact_mode else 8))
        self._text(uninstall_card, 'DESINSTALAÇÃO', 12, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(uninstall_card, 'Remova o aplicativo pelo desinstalador oficial. '
                   'Você poderá escolher se deseja excluir também credenciais, configurações e logs.',
                   9 if self.compact_mode else 10,
                   color=self.COLORS['subtle'], wraplength=550,
                   justify='left').pack(anchor='w',
                      pady=(4, 6) if self.compact_mode else (7, 14))
        self._button(uninstall_card, 'Desinstalar NavixX Desktop',
                     self.uninstall_application, tone='danger').pack(anchor='w')

    def _donations_page(self, page):
        self._section_title(page, 'Apoie o NavixX',
                            'Contribuição voluntária para o desenvolvimento do projeto ALFAMNA.')
        edge, card = self._card(page, pad=19)
        edge.pack(fill='x', pady=(0, 16))
        self._text(card, 'DOAÇÃO VIA PIX', 12, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(card, 'Valor livre. Nenhuma doação é necessária para usar o NavixX.',
                   10, color=self.COLORS['subtle']).pack(anchor='w', pady=(7, 12))
        from PIL import ImageTk
        self.pix_photo = ImageTk.PhotoImage(pix_qr_image(
            size=170 if self.compact_mode else 218))
        tk.Label(card, image=self.pix_photo, bg='#ffffff', padx=8, pady=8).pack(anchor='w')
        self._text(card, 'Beneficiário informado: Wilson Neves de Almeida • Campo Grande/MS',
                   10, color=self.COLORS['text'], wraplength=550).pack(anchor='w', pady=(12, 5))
        self._text(card, 'Chave Pix aleatória informada (opção adicional):',
                   9, color=self.COLORS['subtle']).pack(anchor='w', pady=(4, 2))
        self._text(card, PIX_RANDOM_KEY, 9, color=self.COLORS['text']).pack(anchor='w')
        row = tk.Frame(card, bg=self.COLORS['surface'])
        row.pack(fill='x', pady=(13, 0))
        self._button(row, 'Copiar Pix Copia e Cola',
                     lambda: self._copy_donation(PIX_COPY_AND_PASTE), tone='primary').pack(
                         side='left', padx=(0, 9))
        self._button(row, 'Copiar chave aleatória',
                     lambda: self._copy_donation(PIX_RANDOM_KEY)).pack(side='left')
        self._text(card, 'O QR Code usa uma chave Pix do tipo e-mail, diferente da chave aleatória. '
                   'Confira o beneficiário e a instituição no aplicativo bancário antes de confirmar. '
                   'Este projeto é independente do Banco do Brasil.',
                   9, color=self.COLORS['subtle'], wraplength=530,
                   justify='left').pack(anchor='w', pady=(15, 0))

    def _copy_donation(self, value):
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        messagebox.showinfo('Pix copiado',
                            'Código copiado. Confira o destinatário no seu banco antes de pagar.',
                            parent=self.root)

    def uninstall_application(self):
        """Delegate removal to Inno Setup; its own UI decides optional data erasure."""
        if sys.platform != 'win32':
            messagebox.showinfo('Desinstalar NavixX',
                                'A desinstalação está disponível no Windows instalado.',
                                parent=self.root)
            return
        uninstaller = Path(sys.executable).resolve().parent / 'unins000.exe'
        if not uninstaller.is_file():
            messagebox.showinfo('Desinstalar NavixX',
                                'Abra Configurações do Windows → Aplicativos → NavixX Desktop '
                                '→ Desinstalar. O desinstalador não foi encontrado nesta pasta.',
                                parent=self.root)
            return
        if not messagebox.askyesno('Desinstalar NavixX',
                                   'Deseja abrir o desinstalador? O acesso remoto será encerrado. '
                                   'O assistente perguntará separadamente sobre apagar os dados locais.',
                                   parent=self.root):
            return
        self.stop()
        try:
            subprocess.Popen([str(uninstaller)], cwd=str(uninstaller.parent))
        except OSError as error:
            messagebox.showerror('Desinstalar NavixX', str(error), parent=self.root)
            return
        self.root.after(500, self.close)

    def _activity_page(self, page):
        self._section_title(page, 'Atividade e eventos',
                            'Mensagens locais da sessão. O histórico de auditoria fica no computador.')
        log_edge, log_frame = self._card(page, pad=12)
        log_edge.pack(fill='both', expand=True)
        self.output = tk.Text(log_frame, bg='#0e192a', fg='#dbeafa', insertbackground='white',
                              selectbackground='#305f9e', relief='flat', highlightthickness=0,
                              wrap='word', font=('Consolas', 10), padx=12, pady=12)
        scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.output.pack(side='left', fill='both', expand=True)
        self._button(page, 'Limpar visualização', lambda: self.output.delete('1.0', 'end')
                     ).pack(anchor='e', pady=(12, 0))
        row = tk.Frame(page, bg=self.COLORS['base'])
        row.pack(anchor='w', pady=(7, 0))
        self._button(row, 'Ver logs', self.open_logs).pack(side='left', padx=(0, 8))
        self._button(row, 'Exportar diagnóstico', self.export_diagnostics).pack(side='left')

    def open_logs(self):
        self.diagnostics.record('gui', 'logs_open')
        if self.diagnostics.path.exists() and sys.platform == 'win32':
            os.startfile(str(self.diagnostics.path))
        else:
            self.show('Nenhum log disponível para abrir neste ambiente.')

    def export_diagnostics(self):
        destination = filedialog.asksaveasfilename(parent=self.root,
                      title='Exportar diagnóstico sem dados sensíveis',
                      defaultextension='.json',
                      filetypes=[('JSON', '*.json')],
                      initialfile='navix-diagnostico.json')
        if not destination:
            return
        report = self.diagnostics.report(self.session, self.service, self.tunnel, self.browser)
        Path(destination).write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                     encoding='utf-8')
        self.diagnostics.record('gui', 'diagnostics_export')
        self.show('Diagnóstico exportado sem chaves, tokens ou conteúdo privado.')

    def setup_tray(self):
        if sys.platform != 'win32':
            return
        try:
            import pystray
            from .brand import icon_image
            menu = pystray.Menu(
                pystray.MenuItem('Abrir painel', lambda icon, item: self.events.put(('show',))),
                pystray.MenuItem('Interromper acesso', lambda icon, item: self.events.put(('stop',))),
                pystray.MenuItem('Sair', lambda icon, item: self.events.put(('exit',))))
            self.tray = pystray.Icon('NavixDesktop', icon_image(), 'Navix Desktop', menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception:
            self.tray = None
            self.show('Ícone da bandeja indisponível; mantenha o painel aberto.')

    def hide(self):
        if self.tray and self.tray.visible:
            self.root.withdraw()
        else:
            self.root.iconify()

    def show(self, text):
        self.output.insert('end', text + '\n')
        self.output.see('end')
        if hasattr(self, 'activity_text'):
            self.activity_text.set(text.splitlines()[-1][:140])

    def permissions_changed(self):
        self.stop()
        self.show('Permissões alteradas. Autorize uma nova sessão para aplicar.')

    def select_all(self):
        for option in (self.browser_allowed, self.desktop_allowed,
                       self.files_allowed, self.commands_allowed):
            option.set(True)
        self.permissions_changed()
        self.show('Todas as permissões marcadas. Clique em Conectar / Autorizar para confirmar.')

    def connect(self):
        permissions = []
        if self.browser_allowed.get(): permissions.append('browser')
        if self.desktop_allowed.get(): permissions.append('desktop')
        if self.files_allowed.get(): permissions.append('files')
        if self.commands_allowed.get(): permissions.append('commands')
        if not permissions:
            messagebox.showinfo('Navix', translate('Selecione pelo menos uma permissão.',
                                                getattr(self, 'language', 'pt-BR')))
            return
        if set(permissions) == {'browser', 'desktop', 'files', 'commands'}:
            if not messagebox.askyesno(translate('Autorizar acesso completo', getattr(self, 'language', 'pt-BR')),
                    translate('Esta sessão permitirá controlar a tela, executar programas e alterar ou apagar '
                    'arquivos como seu usuário Windows. Autorizar pelo tempo selecionado?',
                    getattr(self, 'language', 'pt-BR'))):
                return
        selection = self.duration_minutes.get()
        minutes = None if selection in ('Sem prazo', 'No time limit', 'Sin límite') else int(selection)
        if minutes is None:
            if not messagebox.askyesno(translate('Sessão sem prazo', getattr(self, 'language', 'pt-BR')),
                    translate('As permissões permanecerão ativas enquanto este programa estiver aberto. '
                    'Não use em computador compartilhado ou sem supervisão. '
                    'O botão PARAR ACESSO revoga imediatamente a sessão. Confirmar?',
                    getattr(self, 'language', 'pt-BR'))):
                return
        self.session.activate(permissions, minutes=minutes)
        if hasattr(self, '_permission_preferences'):
            self._permission_preferences.write_text(json.dumps(permissions), encoding='utf-8')
        if hasattr(self, 'diagnostics'):
            self.diagnostics.record('session', 'authorized', code='UNLIMITED' if minutes is None else 'TIMED')
        self.service.start()
        self.show('Sessão autorizada sem prazo neste processo.' if minutes is None else
                  f'Sessão autorizada por {minutes} minutos. Aguardando servidor MCP ficar pronto.')
        if getattr(self, 'cloud_controller', None):
            # The owner already approved the local permissions. Reuse only an
            # existing device pairing; never silently grant ChatGPT consent.
            self._request_cloud_start(manual=False)
        elif hasattr(self, 'tunnel_settings'):
            tunnel_id = self.tunnel_settings.load()
            key = self.tunnel_settings.load_key()
            if tunnel_id and key:
                self.tunnel.configure(tunnel_id, key)
                self.root.after(1400, self._launch_tunnel_worker)

    def stop(self):
        if getattr(self, 'cloud_controller', None):
            self.cloud_controller.stop()
        self.tunnel.stop()
        self.session.stop()
        self.diagnostics.record('session', 'revoked')
        self.show('Acesso interrompido. Credencial anterior revogada.')

    def open_browser(self, kind):
        if self.busy:
            return
        status = self.session.status()
        if not status['active'] or 'browser' not in status['permissions']:
            self.show('Navegador não autorizado. Marque a permissão de navegador e clique em Conectar / Autorizar.')
            return
        self.busy = True
        def work():
            try:
                self.browser.call('start', kind=kind)
                self.events.put('Navegador de automação aberto.')
            except Exception as error:
                self.events.put('Falha ao abrir navegador: ' + str(error))
            finally:
                self.events.put(None)
        threading.Thread(target=work, daemon=True).start()

    def copy_pairing(self):
        if not self.session.status()['active'] or not self.service.ready:
            messagebox.showinfo('Navix', 'Conecte e aguarde o servidor ficar pronto.')
            return
        data = {'url': 'http://127.0.0.1:%d/mcp' % self.service.port,
                'headers': {'Authorization': 'Bearer ' + self.session.token}}
        self.root.clipboard_clear()
        self.root.clipboard_append(json.dumps(data, indent=2))
        self.show('Pareamento copiado. Cole apenas no cliente MCP autorizado. Não publique a credencial.')

    def _cloud_code_dialog(self, data):
        previous=getattr(self, '_cloud_pair_dialog', None)
        if previous is not None and previous.winfo_exists():
            previous.destroy()  # A renewed code invalidates the prior dialog.
        box=tk.Toplevel(self.root)
        self._cloud_pair_dialog=box
        box.title('NavixX Cloud — código temporário')
        box.configure(bg=self.COLORS['surface'])
        box.geometry('580x340')
        box.transient(self.root)
        box.lift()
        self._text(box, 'Vincule seu PC à sua conta ChatGPT', 15, 'bold',
                   self.COLORS['cyan']).pack(pady=(15, 9))
        feedback=tk.StringVar(value='Use Copiar para transferir os valores sem digitá-los.')
        for name, value in [('ID do computador', data['device_id']),
                            ('Código de 6 dígitos (válido por 2 minutos)', data['verification_code'])]:
            line=tk.Frame(box,bg=self.COLORS['surface'])
            line.pack(fill='x',padx=12,pady=4)
            self._text(line,name,9,color=self.COLORS['subtle']).pack(anchor='w')
            # Windows Tk changes a readonly Entry's background to system white,
            # leaving its white foreground invisible. An ordinary Label keeps
            # the exact colors across Windows themes; copying is explicit.
            display=tk.Label(line,text=value,bg=self.COLORS['surface2'],
                             fg=self.COLORS['text'],font=('Consolas',11),
                             anchor='w',padx=12,pady=9)
            display.pack(side='left',fill='x',expand=True)
            self._button(line,'Copiar',lambda value=value:
                         self._copy_cloud_value(value,feedback)).pack(
                side='left',padx=(7,0))
        tk.Label(box,textvariable=feedback,bg=self.COLORS['surface'],
                 fg=self.COLORS['green'],font=('Segoe UI',9)).pack(pady=(7,2))
        self._text(box, 'No ChatGPT, conecte o plugin NavixX Cloud. Na página de autorização, '
                   'cole o ID e o código e confirme. Se o plugin negar acesso (401), '
                   'reautorize-o no ChatGPT; o PC não pode conceder essa permissão sozinho.',
                   9,color=self.COLORS['subtle'],wraplength=545).pack(pady=4)
        countdown=tk.StringVar(value='Código válido por até 2 minutos.')
        tk.Label(box,textvariable=countdown,bg=self.COLORS['surface'],
                 fg=self.COLORS['cyan'],font=('Segoe UI',9,'bold')).pack(pady=(3,2))

        def refresh_countdown():
            if not box.winfo_exists():
                return
            remaining=max(0,int((data['expires_at']-time.time()*1000+999)//1000))
            countdown.set(f'Código válido por {remaining}s.' if remaining else
                          'Código expirado. Clique em Vincular ao ChatGPT para gerar outro.')
            if remaining:
                box.after(1000,refresh_countdown)
        box.after(0,refresh_countdown)

    def _copy_cloud_value(self,value,feedback=None):
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        if feedback is not None:
            feedback.set('Copiado! Cole no formulário de autorização do ChatGPT.')

    def enroll_cloud(self):
        if not self.cloud_controller:
            self.show('Navix Cloud não configurado no instalador.')
            return
        if not self.session.status()['active'] or not self.service.ready:
            messagebox.showinfo('NavixX','Autorize primeiro uma sessão local e aguarde o MCP ficar pronto.')
            return
        self.show('NavixX Cloud: solicitando código de vínculo. Aguarde...')
        def work():
            try:
                data=self.cloud_controller.enroll()
                self.root.after(0,lambda:self._cloud_code_dialog(data))
                self.events.put('Código temporário gerado. Confirme o dispositivo no ChatGPT.')
                deadline=time.monotonic()+118
                while self.session.status()['active'] and time.monotonic()<deadline:
                    if self.cloud_controller.paired():
                        self.cloud_controller.start()
                        self.events.put('Navix Cloud: dispositivo vinculado e conexão iniciada.')
                        return
                    time.sleep(3)
                self.events.put('Pareamento não concluído neste prazo; gere outro código.')
            except Exception:
                self.events.put('Navix Cloud: não foi possível gerar/verificar o código. '
                                'Confirme a internet e tente Vincular novamente.')
        threading.Thread(target=work,daemon=True,name='NavixCloudEnrollment').start()

    def _request_cloud_start(self, manual=False):
        if not self.cloud_controller:
            self.show('Navix Cloud não está configurado neste instalador.')
            return
        if self._cloud_start_pending:
            self.show('Navix Cloud: a verificação da conexão já está em andamento.')
            return
        self._cloud_start_pending = True
        self.show('Navix Cloud: verificando servidor local e vínculo com o ChatGPT...')

        def work():
            try:
                # MCP uses port=0; wait for the dynamically chosen local port.
                deadline=time.monotonic()+20
                while self.session.status()['active'] and not self.service.ready:
                    if time.monotonic() >= deadline:
                        self.events.put(('cloud_failure',
                                         'O MCP local não ficou pronto em 20 segundos. '
                                         'Use Reparar conexão novamente.', manual))
                        return
                    time.sleep(0.4)
                started=self.cloud_controller.start()
                self.events.put('Navix Cloud: conexão iniciada. Aguardando confirmação do canal...'
                                if started else 'Navix Cloud: ' +
                                self.cloud_controller.status()['message'])
            except (PermissionError, ConnectionError, ValueError):
                self.events.put(('cloud_failure',
                                 self.cloud_controller.status()['message'], manual))
            except Exception:
                self.events.put(('cloud_failure',
                                 'Falha inesperada na conexão Cloud. Use Reparar conexão.', manual))
            finally:
                self.events.put(('cloud_start_done',))
        threading.Thread(target=work,daemon=True,name='NavixCloudReconnect').start()

    def start_cloud(self):
        """Explicit button action, with immediate feedback before network I/O."""
        self._request_cloud_start(manual=True)

    def open_setup(self):
        from .setup_assistant import open_assistant
        open_assistant(self)

    def diagnose(self):
        self.show('Navix Desktop ' + __version__)
        self.show('Porta local: ' + str(self.service.port))
        self.show('Servidor MCP: ' + ('pronto' if self.service.ready else 'parado ou iniciando'))
        self.show('Sessão: ' + json.dumps(self.session.status(), ensure_ascii=False))
        if getattr(self, 'cloud_controller', None):
            self.show('Nuvem: ' + self.cloud_controller.status()['message'])
        for package in ('mcp', 'playwright', 'PyAutoGUI', 'Pillow'):
            try:
                self.show(package + ': ' + importlib.metadata.version(package))
            except importlib.metadata.PackageNotFoundError:
                self.show(package + ': metadados indisponíveis')
        self.show('Logs: ' + str(self.session.directory / 'audit.jsonl'))

    def repair(self, automatic=False):
        if getattr(self, 'cloud_controller', None):
            if not self.session.status()['active']:
                self.show('Reparo Cloud: a autorização local expirou. '
                          'Clique em Conectar / Autorizar; não é possível renová-la sem você.')
                return
            if self.service.ready:
                self.show('Reparo Cloud: MCP local pronto; verificando a conexão remota...')
                self._request_cloud_start(manual=not automatic)
                return
            if self.service.thread and self.service.thread.is_alive():
                self.show('Reparo Cloud: MCP local ainda iniciando. Aguardando...')
                self._request_cloud_start(manual=not automatic)
                return
            self.show('Reparo Cloud: reiniciando o MCP local e a conexão remota...')
            self.service.close()
            self.service = Service(self.session, self.browser, Desktop(self.session), port=0)
            self.cloud_controller.service = self.service
            self.service.start()
            self._request_cloud_start(manual=not automatic)
            return
        if self.service.ready:
            self.show('Servidor MCP local funcionando. Verificando também o cliente de túnel.')
            if not self.session.status()['active']:
                self.show('Sessão encerrada. Clique em Conectar / Autorizar para autorizar uma nova sessão.')
            elif getattr(self, 'tunnel', None) is not None and self.tunnel.request_reconnect():
                self.show('Reiniciando o túnel e repetindo o diagnóstico automaticamente. '
                          'A autorização existente foi preservada.')
                self._launch_tunnel_worker()
                self.show('O acesso do ChatGPT ainda depende de o plugin aceitar uma chamada real.')
            elif getattr(self, 'tunnel', None) is not None:
                self.show('Túnel ainda não configurado. Abra Assistente para vincular sua conta.')
            return
        if self.service.thread and self.service.thread.is_alive():
            self.show('Servidor MCP ainda iniciando. Aguarde; a autorização foi preservada.')
            return
        self.service.close()
        self.service = Service(self.session, self.browser, Desktop(self.session), port=0)
        self.service.start()
        if hasattr(self, 'tunnel'):
            self.tunnel.service = self.service
        self.show('Servidor MCP reiniciado em nova porta local. '
                  'O cliente de túnel detectará a troca e tentará se reconectar.')
        if self.session.status()['active']:
            self.show('Autorização preservada com o tempo restante original.')
        else:
            self.show('Sessão encerrada. Clique em Conectar / Autorizar para autorizar uma nova sessão.')

    def tick(self):
        while not self.events.empty():
            event = self.events.get_nowait()
            if event is None: self.busy = False
            elif isinstance(event, tuple) and event[0] == 'tunnel_event':
                self.show(f'Túnel: {event[1]} ({event[2]})')
            elif event == ('tunnel_done',):
                self._tunnel_worker_running = False
            elif event == ('cloud_start_done',):
                self._cloud_start_pending = False
            elif isinstance(event, tuple) and event[0] == 'cloud_failure':
                self.show('Reparo Cloud: ' + event[1])
                if event[2]:
                    messagebox.showwarning('NavixX Cloud — reparo', event[1], parent=self.root)
            elif isinstance(event, tuple) and event[0] == 'tunnel_message':
                self.show(event[1])
            elif event == ('show',):
                if self._authenticated:
                    self.root.deiconify()
                    self.root.lift()
                else:
                    self.require_owner_login()
            elif event == ('stop',): self.stop()
            elif event == ('exit',):
                self.close()
                return
            else: self.show(event)
        status = self.session.status()
        if getattr(self, 'cloud_controller', None):
            cloud = self.cloud_controller.status()
            cloud_labels = {
                'disconnected': 'DESCONECTADA', 'checking': 'VERIFICANDO',
                'pairing': 'AGUARDANDO VÍNCULO', 'unpaired': 'VÍNCULO NECESSÁRIO',
                'connecting': 'CONECTANDO', 'connected': 'CANAL ATIVO',
                'verified': 'CHATGPT CONFIRMADO',
                'retrying': 'RECONECTANDO', 'network_error': 'FALHA DE REDE',
                'authorization_required': 'AUTORIZAÇÃO NECESSÁRIA',
                'local_expired': 'SESSÃO LOCAL EXPIRADA',
                'local_starting': 'INICIANDO MCP', 'stopped': 'DESATIVADA',
            }
            self.cloud_state_text.set('Nuvem: ' +
                                      cloud_labels.get(cloud['state'], 'VERIFICANDO'))
            self.cloud_details.set(cloud['message'])
            now=time.monotonic()
            # A dead local MCP is repaired while the *existing* owner grant is
            # valid. Neither expired permissions nor ChatGPT OAuth are bypassed.
            if (status['active'] and not self.service.ready and
                    (not self.service.thread or not self.service.thread.is_alive()) and
                    now >= self._local_next_repair):
                self._local_next_repair = now + 20
                self.repair(automatic=True)
            elif (status['active'] and self.service.ready and
                  cloud['state'] in ('disconnected', 'network_error', 'stopped') and
                  not self._cloud_start_pending and now >= self._cloud_next_retry):
                self._cloud_next_retry = now + 20
                self._request_cloud_start(manual=False)
        tunnel_state = self.tunnel.check()
        self.tunnel_state.set(tunnel_state)
        health = (bool(self.service.ready), status['active'], tunnel_state)
        if health != self._last_health:
            self.diagnostics.record('watchdog', 'health_change',
                                    'ok' if health[0] else 'degraded',
                                    'info' if health[0] else 'warning',
                                    code='LOCAL_READY' if health[0] else 'LOCAL_NOT_READY')
            self._last_health = health
        if not getattr(self, 'cloud_controller', None) and tunnel_state == 'reconectar' and not self._tunnel_worker_running:
            self._launch_tunnel_worker()
        if status['active'] and self.service.ready:
            self.state.set('LOCAL PRONTO — sessão sem prazo' if status.get('unlimited') else
                           'LOCAL PRONTO — sessão autorizada: %ds' % status['remaining_seconds'])
        elif status['active']:
            self.state.set('SERVIDOR INDISPONÍVEL — clique em Diagnosticar')
        else:
            self.state.set('DESCONECTADO — acesso desativado')
        self.status_details.set('Servidor ativo somente neste computador.' if status['active'] and self.service.ready
                                else 'Sessão inativa. Autorize novamente para conectar.')
        self.port_details.set('Porta local: ' + str(self.service.port) if self.service.ready else 'Serviço não iniciado')
        self.permission_details.set(str(len(status['permissions']) if status['active'] else 0) + ' de 4 recursos autorizados')
        local_ready = bool(status['active'] and self.service.ready)
        self.status_label.configure(fg=self.COLORS['green'] if local_ready
                                    else self.COLORS['red'])
        self.side_connection.set('● CONECTADO LOCAL' if local_ready else
                                 ('● INICIANDO' if status['active'] else '● DESCONECTADO'))
        self.side_status_label.configure(fg=self.COLORS['green'] if local_ready
                                         else (self.COLORS['cyan'] if status['active'] else self.COLORS['red']))
        self.side_service.set('MCP: porta ' + str(self.service.port) if self.service.ready
                              else 'Servidor não iniciado')
        remaining = status['remaining_seconds'] if status['active'] else 0
        self.side_duration.set('Sem prazo • até desconectar' if status.get('unlimited') else
                               ('Restam %02d:%02d:%02d' %
                               (remaining // 3600, (remaining // 60) % 60, remaining % 60)
                                if remaining else 'Sem sessão autorizada'))
        self.root.after(500, self.tick)

    def close(self):
        if self.tray:
            self.tray.stop()
        if getattr(self, 'cloud_controller', None):
            self.cloud_controller.stop()
        self.session.stop()
        self.tunnel.stop()
        self.service.close()
        try:
            self.browser.close()
        except Exception:
            pass
        self.browser.worker.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


def main():
    root = tk.Tk()
    Panel(root)
    root.mainloop()
