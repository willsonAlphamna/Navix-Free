import importlib.metadata
import json
import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from .core import Session
from .browser import Browser
from .desktop import Desktop
from .server import Service
from . import __version__


class Panel:
    """Native, low-memory Windows dashboard. All actions remain local and opt-in."""

    COLORS = {
        'base': '#0b1120', 'sidebar': '#101b2e', 'surface': '#152238',
        'surface2': '#1b2c46', 'outline': '#273a56', 'text': '#f2f7ff',
        'subtle': '#9fb1c9', 'blue': '#2878f0', 'blue_hover': '#4092ff',
        'cyan': '#60d6e7', 'green': '#58d5a1', 'red': '#ef6477', 'blood': '#d42642', 'shadow': '#080f1c',
    }

    def __init__(self, root):
        self.root = root
        directory = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'NavixDesktop'
        self.session = Session(directory)
        self.browser = Browser(self.session)
        self.service = Service(self.session, self.browser, Desktop(self.session), port=0)
        self.events = queue.Queue()
        self.busy = False
        self.tray = None
        self.browser_allowed = tk.BooleanVar(value=False)
        self.desktop_allowed = tk.BooleanVar(value=False)
        self.files_allowed = tk.BooleanVar(value=False)
        self.commands_allowed = tk.BooleanVar(value=False)
        self.duration_minutes = tk.IntVar(value=30)
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

    def _text(self, parent, value, size=10, weight='normal', color=None, **kwargs):
        return tk.Label(parent, text=value, bg=parent.cget('bg'),
                        fg=color or self.COLORS['text'],
                        font=('Segoe UI', size, weight), **kwargs)

    def _button(self, parent, label, action, tone='neutral', **kwargs):
        palette = {
            'primary': (self.COLORS['blue'], '#ffffff', self.COLORS['blue_hover']),
            'danger': ('#482738', '#ff9dac', '#5b2f43'),
            'neutral': (self.COLORS['surface2'], self.COLORS['text'], '#304666'),
            'subtle': (self.COLORS['sidebar'], self.COLORS['subtle'], self.COLORS['surface2']),
        }
        bg, fg, hover = palette[tone]
        button = tk.Button(parent, text=label, command=action, bg=bg, fg=fg,
                           activebackground=hover, activeforeground='#ffffff',
                           cursor='hand2', relief='raised', bd=1,
                           font=('Segoe UI', 10, 'bold'), padx=15, pady=11, **kwargs)
        button.bind('<Enter>', lambda event: button.configure(bg=hover))
        button.bind('<Leave>', lambda event: button.configure(bg=bg))
        return button

    def _card(self, parent, pad=18):
        # Layered highlight and drop shadow provide depth without a heavy GUI toolkit.
        shadow = tk.Frame(parent, bg=self.COLORS['shadow'], padx=1, pady=3)
        edge = tk.Frame(shadow, bg='#3b5877', padx=1, pady=1)
        edge.pack(fill='both', expand=True)
        inner = tk.Frame(edge, bg=self.COLORS['surface'], padx=pad, pady=pad)
        inner.pack(fill='both', expand=True)
        return shadow, inner

    def _wordmark(self, parent, large=False):
        row = tk.Frame(parent, bg=parent.cget('bg'))
        basic = 24 if large else 16
        self._text(row, 'Navi', basic, 'bold', '#3688ff').pack(side='left')
        self._text(row, 'x', basic - 6, 'bold', '#6cd9ee').pack(side='left', pady=(6, 0))
        self._text(row, 'X', basic + 4, 'bold', '#3688ff').pack(side='left')
        return row

    def _section_title(self, parent, title, detail):
        self._text(parent, title, 23, 'bold').pack(anchor='w')
        self._text(parent, detail, 10, color=self.COLORS['subtle'],
                   justify='left').pack(anchor='w', pady=(4, 20))

    def _build_ui(self):
        shell = tk.Frame(self.root, bg=self.COLORS['base'])
        shell.pack(fill='both', expand=True)
        side = tk.Frame(shell, width=250, bg=self.COLORS['sidebar'])
        side.pack(side='left', fill='y')
        side.pack_propagate(False)
        brand = tk.Frame(side, bg=self.COLORS['sidebar'], padx=16, pady=22)
        brand.pack(fill='x')
        try:
            from PIL import ImageTk
            from .brand import icon_image
            self.brand_photo = ImageTk.PhotoImage(icon_image(64))
            tk.Label(brand, image=self.brand_photo, bg=self.COLORS['sidebar']).pack(side='left')
        except Exception:
            self._text(brand, 'NX', 24, 'bold', self.COLORS['cyan']).pack(side='left')
        wordmark = tk.Frame(brand, bg=self.COLORS['sidebar'])
        wordmark.pack(side='left', padx=(8, 0))
        self._wordmark(wordmark).pack(anchor='w')
        self._text(wordmark, 'DESKTOP', 9, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(side, 'MENU', 9, 'bold', self.COLORS['subtle']).pack(
            anchor='w', padx=19, pady=(14, 10))
        self.nav_buttons = {}
        for key, label in (
            ('inicio', '⌂  Início'),
            ('permissoes', '✓  Permissões'),
            ('ferramentas', '▣  Ferramentas'),
            ('atividade', '≡  Atividade'),
        ):
            item = self._button(side, label, lambda selected=key: self.show_page(selected),
                                tone='subtle', anchor='w')
            item.pack(fill='x', padx=12, pady=4)
            self.nav_buttons[key] = item
        tk.Frame(side, bg=self.COLORS['outline'], height=1).pack(
            fill='x', padx=18, pady=(17, 12))
        self._button(side, '★  Assistente', self.open_setup, tone='subtle',
                     anchor='w').pack(fill='x', padx=12, pady=4)
        self._button(side, '↙  Minimizar', self.hide, tone='subtle',
                     anchor='w').pack(fill='x', padx=12, pady=4)

        # Live status occupies the otherwise empty part of the navigation rail.
        state_card = tk.Frame(side, bg=self.COLORS['surface'], padx=15, pady=16,
                              highlightbackground='#355575', highlightthickness=1,
                              relief='raised', bd=1)
        state_card.pack(fill='x', padx=14, pady=(30, 8))
        self._text(state_card, 'SESSÃO LOCAL', 9, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self.side_status_label = self._text(
            state_card, '', 11, 'bold', self.COLORS['red'],
            textvariable=self.side_connection, anchor='w', justify='left')
        self.side_status_label.pack(fill='x', pady=(13, 7))
        self._text(state_card, '', 9, color=self.COLORS['subtle'],
                   textvariable=self.side_service, anchor='w').pack(fill='x')
        self._text(state_card, '', 9, color=self.COLORS['subtle'],
                   textvariable=self.side_duration, anchor='w').pack(
            fill='x', pady=(5, 0))
        footer = tk.Frame(side, bg=self.COLORS['sidebar'])
        footer.pack(side='bottom', fill='x', padx=18, pady=15)
        self._text(footer, 'CONTROLE SOB SUA AUTORIZAÇÃO', 8, 'bold',
                   self.COLORS['green']).pack(anchor='w')
        self._text(footer, 'Nenhuma permissão permanente.\nVersão ' + __version__,
                   9, color=self.COLORS['subtle'], justify='left').pack(
            anchor='w', pady=(7, 0))

        main = tk.Frame(shell, bg=self.COLORS['base'], padx=24, pady=22)
        main.pack(side='left', fill='both', expand=True)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)
        self.pages = {}
        for key in ('inicio', 'permissoes', 'ferramentas', 'atividade'):
            page = tk.Frame(main, bg=self.COLORS['base'])
            page.grid(row=0, column=0, sticky='nsew')
            self.pages[key] = page
        self._home_page(self.pages['inicio'])
        self._permissions_page(self.pages['permissoes'])
        self._tools_page(self.pages['ferramentas'])
        self._activity_page(self.pages['atividade'])
        self.show_page('inicio')

    def show_page(self, key):
        self.pages[key].tkraise()
        for page_key, button in self.nav_buttons.items():
            active = page_key == key
            button.configure(bg=self.COLORS['surface2'] if active else self.COLORS['sidebar'],
                             fg=self.COLORS['text'] if active else self.COLORS['subtle'])

    def _home_page(self, page):
        headline = tk.Frame(page, bg=self.COLORS['base'])
        headline.pack(anchor='w', fill='x')
        self._text(headline, 'Bem-vindo', 23, 'bold', self.COLORS['blood']).pack(side='left')
        self._text(headline, ' ao ', 23, 'bold', '#ffffff').pack(side='left')
        self._wordmark(headline, large=True).pack(side='left')
        self._text(page, 'Seu computador e suas automações em um único lugar.',
                   10, color=self.COLORS['subtle']).pack(anchor='w', pady=(7, 18))
        frame, card = self._card(page, pad=24)
        frame.pack(fill='x', pady=(0, 16))
        top = tk.Frame(card, bg=self.COLORS['surface'])
        top.pack(fill='x')
        self._text(top, 'STATUS DA CONEXÃO', 9, 'bold', self.COLORS['cyan']).pack(side='left')
        self._text(top, 'MCP LOCAL', 9, 'bold', self.COLORS['subtle']).pack(side='right')
        self._text(card, 'Conexão protegida neste PC • uso remoto requer pareamento autenticado',
                   9, color=self.COLORS['subtle'], wraplength=580,
                   justify='left').pack(anchor='w', pady=(11, 0))
        self.status_label = self._text(card, '', 17, 'bold', self.COLORS['red'],
                                       textvariable=self.state, anchor='w',
                                       wraplength=610, justify='left')
        # Remove literal text so textvariable is the single source of truth.
        self.status_label.configure(text='')
        self.status_label.pack(fill='x', pady=(15, 8))
        self._text(card, '', 10, color=self.COLORS['subtle'],
                   textvariable=self.status_details, anchor='w',
                   justify='left').pack(fill='x')
        actions = tk.Frame(card, bg=self.COLORS['surface'])
        actions.pack(fill='x', pady=(20, 0))
        self._button(actions, 'Configurar acesso', lambda: self.show_page('permissoes'),
                     tone='primary').pack(side='left', padx=(0, 9))
        self._button(actions, 'PARAR ACESSO', self.stop, tone='danger').pack(side='left')
        cards = tk.Frame(page, bg=self.COLORS['base'])
        cards.pack(fill='x', pady=(0, 16))
        left_edge, left = self._card(cards, pad=18)
        left_edge.pack(side='left', fill='both', expand=True, padx=(0, 8))
        self._text(left, 'SERVIDOR MCP', 9, 'bold', self.COLORS['subtle']).pack(anchor='w')
        self._text(left, '', 11, 'bold', textvariable=self.port_details).pack(
            anchor='w', pady=(10, 0))
        right_edge, right = self._card(cards, pad=18)
        right_edge.pack(side='left', fill='both', expand=True, padx=(8, 0))
        self._text(right, 'PERMISSÕES ATIVAS', 9, 'bold', self.COLORS['subtle']).pack(anchor='w')
        self._text(right, '', 11, 'bold', textvariable=self.permission_details).pack(
            anchor='w', pady=(10, 0))
        foot_edge, foot = self._card(page)
        foot_edge.pack(fill='x')
        self._text(foot, 'ACESSO RÁPIDO', 10, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(foot, 'Abra o navegador ou use o assistente para configurar o pareamento.',
                   10, color=self.COLORS['subtle']).pack(anchor='w', pady=(7, 14))
        buttons = tk.Frame(foot, bg=self.COLORS['surface'])
        buttons.pack(fill='x')
        self._button(buttons, 'Abrir navegador', lambda: self.open_browser('integrado'),
                     tone='neutral').pack(side='left', padx=(0, 8))
        self._button(buttons, 'Assistente de conexão', self.open_setup,
                     tone='neutral').pack(side='left')
        self._text(page, 'Última atividade', 10, 'bold', self.COLORS['subtle']).pack(
            anchor='w', pady=(22, 4))
        self._text(page, '', 10, color=self.COLORS['text'],
                   textvariable=self.activity_text, wraplength=650,
                   anchor='w', justify='left').pack(fill='x')

    def _permission_item(self, parent, flag, title, subtitle):
        wrap = tk.Frame(parent, bg=self.COLORS['surface2'], pady=8, padx=12)
        wrap.pack(fill='x', pady=5)
        control = tk.Checkbutton(wrap, text=title, variable=flag,
                                 command=self.permissions_changed, bg=self.COLORS['surface2'],
                                 fg=self.COLORS['text'], selectcolor=self.COLORS['base'],
                                 activebackground=self.COLORS['surface2'],
                                 activeforeground='#ffffff', anchor='w', cursor='hand2',
                                 font=('Segoe UI', 10, 'bold'), padx=7, pady=2)
        control.pack(fill='x')
        self._text(wrap, subtitle, 9, color=self.COLORS['subtle']).pack(
            anchor='w', padx=31)

    def _permissions_page(self, page):
        self._section_title(page, 'Permissões e segurança',
                            'Escolha exatamente o que o NAVIX pode controlar neste PC.')
        frame, card = self._card(page, pad=18)
        frame.pack(fill='x', pady=(0, 15))
        self._permission_item(card, self.browser_allowed, 'Navegador',
                              'Abrir páginas, clicar, preencher e baixar arquivos autorizados.')
        self._permission_item(card, self.desktop_allowed, 'Mouse, teclado e tela',
                              'Controlar a área de trabalho e capturar imagens.')
        self._permission_item(card, self.files_allowed, 'Arquivos e pastas',
                              'Ler, criar, editar, mover ou apagar arquivos.')
        self._permission_item(card, self.commands_allowed, 'Comandos e programas',
                              'Executar PowerShell, Python e outros programas.')
        row = tk.Frame(page, bg=self.COLORS['base'])
        row.pack(fill='x', pady=(0, 15))
        self._text(row, 'Tempo de autorização:', 10, 'bold').pack(side='left', padx=(0, 10))
        ttk.Combobox(row, textvariable=self.duration_minutes, values=(30, 60, 120, 240),
                     style='Navix.TCombobox', state='readonly', width=7).pack(side='left')
        self._text(row, 'minutos', 10, color=self.COLORS['subtle']).pack(side='left', padx=10)
        actions = tk.Frame(page, bg=self.COLORS['base'])
        actions.pack(fill='x')
        self._button(actions, 'Marcar todas', self.select_all).pack(side='left', padx=(0, 8))
        self._button(actions, 'Conectar / Autorizar', self.connect,
                     tone='primary').pack(side='left', padx=(0, 8))
        self._button(actions, 'PARAR ACESSO', self.stop, tone='danger').pack(side='left')
        self._text(page, 'Alterar qualquer permissão revoga a sessão atual.\n'
                   'Acesso completo exige sua confirmação; não ultrapassa os limites do Windows.',
                   9, color=self.COLORS['subtle'], justify='left').pack(anchor='w', pady=(16, 0))

    def _tools_page(self, page):
        self._section_title(page, 'Ferramentas', 'Navegação, diagnóstico e pareamento em áreas separadas.')
        web_edge, web = self._card(page)
        web_edge.pack(fill='x', pady=(0, 16))
        self._text(web, 'NAVEGAÇÃO', 12, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(web, 'O navegador usa perfil próprio de automação.',
                   10, color=self.COLORS['subtle']).pack(anchor='w', pady=(7, 14))
        row = tk.Frame(web, bg=self.COLORS['surface'])
        row.pack(fill='x')
        self._button(row, 'Abrir navegador integrado',
                     lambda: self.open_browser('integrado'), tone='primary').pack(
            side='left', padx=(0, 8))
        self._button(row, 'Abrir Opera',
                     lambda: self.open_browser('opera')).pack(side='left')
        system_edge, system = self._card(page)
        system_edge.pack(fill='x', pady=(0, 16))
        self._text(system, 'DIAGNÓSTICO E REPARO', 12, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(system, 'Veja o estado real do servidor ou reinicie uma conexão parada.',
                   10, color=self.COLORS['subtle']).pack(anchor='w', pady=(7, 14))
        row = tk.Frame(system, bg=self.COLORS['surface'])
        row.pack(fill='x')
        self._button(row, 'Diagnosticar', self.diagnose).pack(side='left', padx=(0, 8))
        self._button(row, 'Reparar conexão', self.repair).pack(side='left')
        pair_edge, pair = self._card(page)
        pair_edge.pack(fill='x')
        self._text(pair, 'PAREAMENTO', 12, 'bold', self.COLORS['cyan']).pack(anchor='w')
        self._text(pair, 'Copie a credencial apenas para um cliente MCP autorizado.\n'
                   'Acesso pela internet não é ativado automaticamente.',
                   10, color=self.COLORS['subtle'], justify='left').pack(
            anchor='w', pady=(7, 14))
        row = tk.Frame(pair, bg=self.COLORS['surface'])
        row.pack(fill='x')
        self._button(row, 'Copiar pareamento', self.copy_pairing,
                     tone='primary').pack(side='left', padx=(0, 8))
        self._button(row, 'Assistente', self.open_setup).pack(side='left')

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
            messagebox.showinfo('Navix', 'Selecione pelo menos uma permissão.')
            return
        if set(permissions) == {'browser', 'desktop', 'files', 'commands'}:
            if not messagebox.askyesno('Autorizar acesso completo',
                    'Esta sessão permitirá controlar a tela, executar programas e alterar ou apagar '
                    'arquivos como seu usuário Windows. Autorizar pelo tempo selecionado?'):
                return
        minutes = self.duration_minutes.get()
        self.session.activate(permissions, minutes=minutes)
        self.service.start()
        self.show(f'Sessão autorizada por {minutes} minutos. Aguardando servidor MCP ficar pronto.')

    def stop(self):
        self.session.stop()
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

    def open_setup(self):
        from .setup_assistant import open_assistant
        open_assistant(self)

    def diagnose(self):
        self.show('Navix Desktop ' + __version__)
        self.show('Porta local: ' + str(self.service.port))
        self.show('Servidor MCP: ' + ('pronto' if self.service.ready else 'parado ou iniciando'))
        self.show('Sessão: ' + json.dumps(self.session.status(), ensure_ascii=False))
        for package in ('mcp', 'playwright', 'PyAutoGUI', 'Pillow'):
            try:
                self.show(package + ': ' + importlib.metadata.version(package))
            except importlib.metadata.PackageNotFoundError:
                self.show(package + ': metadados indisponíveis')
        self.show('Logs: ' + str(self.session.directory / 'audit.jsonl'))

    def repair(self):
        if self.service.ready:
            self.show('Servidor MCP funcionando. A autorização e a credencial foram preservadas.')
            if not self.session.status()['active']:
                self.show('Sessão encerrada. Clique em Conectar / Autorizar para autorizar uma nova sessão.')
            return
        if self.service.thread and self.service.thread.is_alive():
            self.show('Servidor MCP ainda iniciando. Aguarde; a autorização foi preservada.')
            return
        self.service.close()
        self.service = Service(self.session, self.browser, Desktop(self.session), port=0)
        self.service.start()
        self.show('Servidor MCP reiniciado em nova porta local. Copie novamente o pareamento quando estiver pronto.')
        if self.session.status()['active']:
            self.show('Autorização preservada com o tempo restante original.')
        else:
            self.show('Sessão encerrada. Clique em Conectar / Autorizar para autorizar uma nova sessão.')

    def tick(self):
        while not self.events.empty():
            event = self.events.get_nowait()
            if event is None: self.busy = False
            elif event == ('show',):
                self.root.deiconify()
                self.root.lift()
            elif event == ('stop',): self.stop()
            elif event == ('exit',):
                self.close()
                return
            else: self.show(event)
        status = self.session.status()
        if status['active'] and self.service.ready:
            self.state.set('LOCAL PRONTO — sessão autorizada: %ds' % status['remaining_seconds'])
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
        self.side_duration.set('Restam %02d:%02d:%02d' %
                               (remaining // 3600, (remaining // 60) % 60, remaining % 60)
                               if remaining else 'Sem sessão autorizada')
        self.root.after(500, self.tick)

    def close(self):
        if self.tray:
            self.tray.stop()
        self.session.stop()
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
