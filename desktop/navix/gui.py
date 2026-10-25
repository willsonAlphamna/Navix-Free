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
    def __init__(self, root):
        self.root = root
        directory = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'NavixDesktop'
        self.session = Session(directory)
        self.browser = Browser(self.session)
        self.service = Service(self.session, self.browser, Desktop(self.session), port=0)
        self.events = queue.Queue()
        self.busy = False
        self.tray = None
        self.root.title('Navix Desktop ' + __version__ + ' — Superconector')
        self.root.geometry('800x740')
        self.root.minsize(700, 700)
        self.root.configure(bg='#111827')
        icon = Path(getattr(sys, '_MEIPASS', Path(__file__).parent.parent)) / 'assets/navix.ico'
        if icon.is_file():
            self.root.iconbitmap(str(icon))
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 11), background='#111827', foreground='#f3f4f6')
        style.configure('TButton', padding=9, background='#2563eb', foreground='white')
        style.configure('TCheckbutton', background='#111827', foreground='white')
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='N  NAVIX DESKTOP', font=('Segoe UI', 23, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Seu computador. Suas permissões. Sua sessão.').pack(anchor='w', pady=(4, 18))
        self.state = tk.StringVar(value='DESCONECTADO — acesso desativado')
        ttk.Label(frame, textvariable=self.state, font=('Segoe UI', 12, 'bold'), wraplength=680).pack(anchor='w', pady=8)
        self.browser_allowed = tk.BooleanVar()
        self.desktop_allowed = tk.BooleanVar()
        self.files_allowed = tk.BooleanVar()
        self.commands_allowed = tk.BooleanVar()
        ttk.Checkbutton(frame, text='Permitir navegador de automação', variable=self.browser_allowed,
                        command=self.permissions_changed).pack(anchor='w', pady=4)
        ttk.Checkbutton(frame, text='Permitir mouse, teclado e captura da tela inteira', variable=self.desktop_allowed,
                        command=self.permissions_changed).pack(anchor='w', pady=4)
        ttk.Checkbutton(frame, text='Permitir ler, editar, copiar, apagar e transferir arquivos', variable=self.files_allowed,
                        command=self.permissions_changed).pack(anchor='w', pady=4)
        ttk.Checkbutton(frame, text='Permitir executar PowerShell, Python e outros programas', variable=self.commands_allowed,
                        command=self.permissions_changed).pack(anchor='w', pady=4)
        ttk.Label(frame, text='Sessão de 30 minutos. Desmarcar uma permissão interrompe a sessão.',
                  wraplength=680).pack(anchor='w', pady=8)
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=8)
        ttk.Button(row, text='Conectar / Autorizar', command=self.connect).pack(side='left', padx=(0,8))
        ttk.Button(row, text='PARAR ACESSO', command=self.stop).pack(side='left')
        row2 = ttk.Frame(frame)
        row2.pack(fill='x', pady=8)
        ttk.Button(row2, text='Abrir navegador integrado', command=lambda:self.open_browser('integrado')).pack(side='left', padx=(0,8))
        ttk.Button(row2, text='Abrir Opera', command=lambda:self.open_browser('opera')).pack(side='left')
        row3 = ttk.Frame(frame)
        row3.pack(fill='x', pady=8)
        ttk.Button(row3, text='Copiar pareamento', command=self.copy_pairing).pack(side='left', padx=(0,8))
        ttk.Button(row3, text='Diagnosticar', command=self.diagnose).pack(side='left', padx=(0,8))
        ttk.Button(row3, text='Reparar conexão', command=self.repair).pack(side='left')
        self.output = tk.Text(frame, height=9, bg='#1f2937', fg='#e5e7eb', relief='flat',
                              wrap='word', font=('Consolas', 10))
        self.output.pack(fill='both', expand=True, pady=12)
        self.show('Pronto para configurar. Marque as permissões e clique em Conectar.\n'
                  'Pareamento local: cliente MCP com URL e cabeçalho Bearer.\n'
                  'Acesso pela internet/ChatGPT exige integração autenticada compatível; não é automático.')
        ttk.Button(frame, text='Minimizar na bandeja', command=self.hide).pack(anchor='w')
        self.setup_tray()
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.after(500, self.tick)

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

    def permissions_changed(self):
        self.stop()
        self.show('Permissões alteradas. Autorize uma nova sessão para aplicar.')

    def connect(self):
        permissions = []
        if self.browser_allowed.get(): permissions.append('browser')
        if self.desktop_allowed.get(): permissions.append('desktop')
        if self.files_allowed.get(): permissions.append('files')
        if self.commands_allowed.get(): permissions.append('commands')
        if not permissions:
            messagebox.showinfo('Navix', 'Selecione pelo menos uma permissão.')
            return
        self.service.start()
        self.session.activate(permissions)
        self.show('Sessão autorizada por 30 minutos. Aguardando servidor MCP ficar pronto.')

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
