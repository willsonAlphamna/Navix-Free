"""One-time owner-guided setup; future runs reuse securely saved credentials."""
import importlib.metadata
import os
from pathlib import Path
import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from .tunnel_manager import bundled_tunnel_client
from .i18n import translate

TUNNEL_SETTINGS = 'https://platform.openai.com/settings/organization/tunnels'
TUNNEL_GUIDE = 'https://developers.openai.com/api/docs/guides/secure-mcp-tunnels'


def find_tunnel_client():
    executable = bundled_tunnel_client()
    if executable:
        return executable
    # Previous pilot installations used this per-user directory.
    base = Path(os.environ.get('LOCALAPPDATA', str(Path.home())))
    legacy = base / 'SuperConectorWilson' / 'TunnelClient' / 'extraido' / 'tunnel-client.exe'
    return str(legacy) if legacy.is_file() else None


def existing_tunnel_id():
    """Import only a non-secret ID from an existing local pilot profile."""
    base = Path(os.environ.get('APPDATA', str(Path.home()))) / 'tunnel-client'
    for name in ('navixx.yaml', 'playwright-opera.yaml'):
        profile = base / name
        try:
            result = re.search(r'\btunnel_[0-9a-fA-F]{32}\b',
                               profile.read_text(encoding='utf-8'))
            if result:
                return result.group(0)
        except OSError:
            pass
    return ''


def local_diagnostic(panel):
    status = panel.session.status()
    packages = {}
    for name in ('mcp', 'playwright', 'PyAutoGUI'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = 'não detectado'
    return {
        'server_ready': bool(panel.service.ready),
        'session_active': bool(status['active']),
        'permissions': status['permissions'],
        'port': panel.service.port,
        'tunnel_client_found': bool(find_tunnel_client()),
        'tunnel_state': panel.tunnel.check() if hasattr(panel, 'tunnel') else 'desligado',
        'packages': packages,
    }


def open_assistant(panel):
    """Scrollable onboarding, including diagnostics, even at high Windows DPI."""
    dialog = tk.Toplevel(panel.root)
    dialog.title('NavixX Desktop — ' + translate('Assistente de conexão', panel.language))
    display_w, display_h = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
    window_w = min(790, max(620, display_w - 80))
    window_h = min(720, max(510, display_h - 120))
    dialog.geometry(f'{window_w}x{window_h}')
    dialog.minsize(min(620, window_w), min(510, window_h))
    dialog.configure(bg=panel.COLORS['base'])
    dialog.transient(panel.root)

    shell = tk.Frame(dialog, bg=panel.COLORS['base'])
    shell.pack(fill='both', expand=True)
    content_canvas = tk.Canvas(shell, bg=panel.COLORS['base'],
                               highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(shell, orient='vertical', command=content_canvas.yview)
    content_canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')
    content_canvas.pack(side='left', fill='both', expand=True)
    page = tk.Frame(content_canvas, bg=panel.COLORS['base'], padx=22, pady=18)
    viewport = content_canvas.create_window((0, 0), window=page, anchor='nw')

    def sync_region(event=None):
        content_canvas.configure(scrollregion=content_canvas.bbox('all'))

    def sync_width(event):
        content_canvas.itemconfigure(viewport, width=event.width)

    page.bind('<Configure>', sync_region)
    content_canvas.bind('<Configure>', sync_width)
    def mouse_wheel(event):
        delta = -1 if getattr(event, 'delta', 0) > 0 else 1
        content_canvas.yview_scroll(delta, 'units')

    dialog.bind('<MouseWheel>', mouse_wheel)
    dialog.bind('<Button-4>', lambda event: content_canvas.yview_scroll(-1, 'units'))
    dialog.bind('<Button-5>', lambda event: content_canvas.yview_scroll(1, 'units'))

    panel._text(page, 'Assistente NavixX', 21, 'bold').pack(anchor='w')
    panel._text(page, 'Configuração guiada e diagnóstico sem esconder informações.',
                10, color=panel.COLORS['subtle'], wraplength=560,
                justify='left').pack(anchor='w', pady=(6, 18))

    def step(number, title, detail):
        outer, inside = panel._card(page, pad=14)
        outer.pack(fill='x', pady=6)
        header = tk.Frame(inside, bg=panel.COLORS['surface'])
        header.pack(fill='x')
        panel._text(header, str(number).zfill(2), 12, 'bold',
                    panel.COLORS['cyan']).pack(side='left', padx=(0, 12))
        panel._text(header, title, 12, 'bold', wraplength=550,
                    justify='left').pack(side='left')
        panel._text(inside, detail, 10, color=panel.COLORS['subtle'],
                    justify='left', wraplength=590).pack(anchor='w', pady=(10, 0))
        return inside

    step(1, 'Autorize este computador',
         'Na tela Permissões, selecione os recursos e clique em Conectar / Autorizar. '
         'O acesso vem desligado de fábrica e pode ser revogado a qualquer momento.')
    remote = step(2, 'Conecte com um clique — sem PowerShell',
                  'Uma única vez, informe o ID do seu túnel e a chave restrita da sua '
                  'conta OpenAI. O NavixX verifica a conexão, inicia o cliente de túnel '
                  'incorporado e tenta reconectar quando há falhas temporárias.')
    tunnel_id = tk.StringVar(value=panel.tunnel_settings.load() or existing_tunnel_id())
    secret = tk.StringVar(value=panel.tunnel_settings.load_key())
    remember = tk.BooleanVar(value=panel.tunnel_settings.secret.is_file())
    panel._text(remote, 'ID do túnel (tunnel_…)', 10, 'bold').pack(anchor='w', pady=(10, 4))
    id_entry = tk.Entry(remote, textvariable=tunnel_id, font=('Consolas', 10),
                        bg='#243550', fg='white', insertbackground='white', relief='flat')
    id_entry.pack(fill='x', ipady=8)
    panel._text(remote, 'Chave da sua conta OpenAI (não aparece na tela)',
                10, 'bold').pack(anchor='w', pady=(12, 4))
    key_entry = tk.Entry(remote, textvariable=secret, show='*', font=('Consolas', 10),
                         bg='#243550', fg='white', insertbackground='white', relief='flat')
    key_entry.pack(fill='x', ipady=8)
    tk.Checkbutton(remote, text=translate('Lembrar chave criptografada neste usuário Windows (DPAPI)',
                                         panel.language),
                   variable=remember, bg=panel.COLORS['surface'],
                   fg=panel.COLORS['text'], selectcolor=panel.COLORS['sidebar'],
                   activebackground=panel.COLORS['surface'],
                   activeforeground=panel.COLORS['text']).pack(anchor='w', pady=(8, 0))

    tunnel_feedback = tk.StringVar(value='Aguardando autorização e configuração.')
    panel._text(remote, '', 10, color=panel.COLORS['cyan'],
                textvariable=tunnel_feedback, anchor='w', justify='left',
                wraplength=560).pack(fill='x', pady=(12, 8))
    def connect_remote():
        if not panel.session.status()['active'] or not panel.service.ready:
            messagebox.showwarning('NavixX', 'Autorize uma sessão e aguarde MCP pronto primeiro.',
                                   parent=dialog)
            return
        try:
            panel.connect_tunnel(tunnel_id.get().strip(), secret.get().strip(), remember.get())
        except (OSError, ValueError) as exc:
            messagebox.showerror('Configuração do túnel', str(exc), parent=dialog)
            return
        secret.set('')
        tunnel_feedback.set('Verificando segurança e iniciando o túnel em segundo plano…')

    actions = tk.Frame(remote, bg=panel.COLORS['surface'])
    actions.pack(fill='x', pady=(7, 0))
    panel._button(actions, 'Conectar com ChatGPT', connect_remote,
                  tone='primary').pack(side='left', padx=(0, 8))
    panel._button(actions, 'Desconectar túnel', panel.disconnect_tunnel,
                  tone='danger').pack(side='left')

    def refresh_tunnel_label():
        if dialog.winfo_exists():
            tunnel_feedback.set('Estado do túnel: ' + panel.tunnel.check())
            dialog.after(1800, refresh_tunnel_label)
    dialog.after(2200, refresh_tunnel_label)

    remote = step(3, 'Vincule no ChatGPT uma única vez',
                  'Abra ChatGPT → Plugins → + → Adicionar servidor MCP personalizado → Tunnel. '
                  'Escolha o mesmo ID. O ChatGPT precisa solicitar sua autorização; '
                  'o NavixX não pode aceitar permissões por outra pessoa.')
    links = tk.Frame(remote, bg=panel.COLORS['surface'])
    links.pack(anchor='w', pady=(12, 0))
    panel._button(links, 'Configurações OpenAI', lambda: webbrowser.open(TUNNEL_SETTINGS)
                  ).pack(side='left', padx=(0, 8))
    panel._button(links, 'Abrir ChatGPT', lambda: webbrowser.open('https://chatgpt.com')
                  ).pack(side='left', padx=(0, 8))
    panel._button(links, 'Guia oficial', lambda: webbrowser.open(TUNNEL_GUIDE)
                  ).pack(side='left')

    local = step(4, 'Pareamento local avançado (opcional)',
                 'Para clientes MCP no mesmo computador, o botão abaixo copia a credencial '
                 'de curta duração. A conexão automática acima não exige copiar esse código.')
    panel._button(local, 'Copiar pareamento protegido', panel.copy_pairing).pack(
        anchor='w', pady=(12, 0))

    diagnostic_edge, diagnostic = panel._card(page, pad=16)
    diagnostic_edge.pack(fill='x', pady=(14, 12))
    panel._text(diagnostic, 'DIAGNÓSTICO LOCAL', 11, 'bold',
                panel.COLORS['cyan']).pack(anchor='w')
    summary = tk.StringVar()

    def refresh():
        data = local_diagnostic(panel)
        ready = bool(data['server_ready'] and data['session_active'])
        packages = '\n'.join(f"  {key}: {value}" for key, value in data['packages'].items())
        summary.set(
            f"Servidor MCP: {'PRONTO' if ready else 'PARADO / NÃO AUTORIZADO'}\n"
            f"Porta local: {data['port']}\n"
            f"Permissões: {', '.join(data['permissions']) or 'nenhuma'}\n"
            f"Cliente de túnel detectado: {'sim' if data['tunnel_client_found'] else 'não'}\n"
            f"Túnel externo: {data['tunnel_state']}\n"
            f"Componentes incorporados:\n{packages}\n"
            'O estado executando indica processo local vivo; valide uma chamada real no ChatGPT.'
        )

    panel._text(diagnostic, '', 10, color=panel.COLORS['text'],
                textvariable=summary, justify='left',
                wraplength=520, anchor='w').pack(fill='x', pady=(12, 14))
    panel._button(diagnostic, 'Atualizar diagnóstico', refresh).pack(anchor='w')
    refresh()

    footer = tk.Frame(dialog, bg=panel.COLORS['sidebar'], padx=18, pady=10)
    footer.pack(side='bottom', fill='x')
    panel._text(footer, 'Role para conferir todas as etapas e versões.',
                9, color=panel.COLORS['subtle']).pack(side='left')
    panel._button(footer, 'Fechar assistente', dialog.destroy,
                  tone='primary').pack(side='right')
