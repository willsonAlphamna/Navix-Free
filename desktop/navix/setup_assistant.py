"""Guided public-distribution onboarding without bundled credentials.

The assistant does not provision Platform organizations or bypass account consent.
It only checks the local program, copies the short-lived pairing locally and opens
official documentation/settings after a user's explicit click.
"""
import importlib.metadata
import os
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import ttk
import webbrowser

TUNNEL_SETTINGS = 'https://platform.openai.com/settings/organization/tunnels'
TUNNEL_GUIDE = 'https://developers.openai.com/api/docs/guides/secure-mcp-tunnels'


def find_tunnel_client():
    executable = shutil.which('tunnel-client')
    if executable:
        return executable
    # Previous pilot installations used this per-user directory.
    base = Path(os.environ.get('LOCALAPPDATA', str(Path.home())))
    legacy = base / 'SuperConectorWilson' / 'TunnelClient' / 'extraido' / 'tunnel-client.exe'
    return str(legacy) if legacy.is_file() else None


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
        'packages': packages,
    }


def open_assistant(panel):
    """Scrollable onboarding, including diagnostics, even at high Windows DPI."""
    dialog = tk.Toplevel(panel.root)
    dialog.title('NavixX Desktop — Assistente de conexão')
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

    step(1, 'Autorize no Windows',
         'No painel principal, abra Permissões, marque os recursos desejados e clique em '
         'Conectar / Autorizar. O acesso nunca vem habilitado de fábrica.')
    local = step(2, 'Pareie um cliente MCP local',
                 'Quando o servidor estiver pronto, copie o pareamento somente para '
                 'um cliente confiável. Nunca publique esse código ou envie por e-mail.')
    panel._button(local, 'Copiar pareamento protegido', panel.copy_pairing,
                  tone='primary').pack(anchor='w', pady=(12, 0))
    remote = step(3, 'Acesso externo ao ChatGPT ou Codex',
                  'O servidor local não abre acesso à internet. É necessária uma conexão '
                  'autenticada própria para cada pessoa e computador.')
    links = tk.Frame(remote, bg=panel.COLORS['surface'])
    links.pack(anchor='w', pady=(12, 0))
    panel._button(links, 'Configurações OpenAI', lambda: webbrowser.open(TUNNEL_SETTINGS)
                  ).pack(side='left', padx=(0, 8))
    panel._button(links, 'Guia oficial', lambda: webbrowser.open(TUNNEL_GUIDE)
                  ).pack(side='left')

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
            f"Componentes incorporados:\n{packages}\n"
            'Conexão externa: não confirmada por este diagnóstico.'
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
