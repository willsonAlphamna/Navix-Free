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
    """Accessible, themed onboarding. User consent remains in the main panel."""
    dialog = tk.Toplevel(panel.root)
    dialog.title('NAVIX Desktop — Assistente de conexão')
    dialog.geometry('770x710')
    dialog.minsize(690, 660)
    dialog.configure(bg=panel.COLORS['base'])
    dialog.transient(panel.root)
    page = tk.Frame(dialog, bg=panel.COLORS['base'], padx=28, pady=24)
    page.pack(fill='both', expand=True)
    panel._text(page, 'Vamos configurar seu NAVIX', 21, 'bold').pack(anchor='w')
    panel._text(page, 'Três etapas claras para deixar o programa pronto no seu computador.',
                10, color=panel.COLORS['subtle']).pack(anchor='w', pady=(6, 18))

    def step(number, title, detail):
        outer, inside = panel._card(page, pad=14)
        outer.pack(fill='x', pady=5)
        header = tk.Frame(inside, bg=panel.COLORS['surface'])
        header.pack(fill='x')
        panel._text(header, str(number).zfill(2), 12, 'bold',
                    panel.COLORS['cyan']).pack(side='left', padx=(0, 12))
        panel._text(header, title, 12, 'bold').pack(side='left')
        panel._text(inside, detail, 10, color=panel.COLORS['subtle'],
                    justify='left', wraplength=635).pack(anchor='w', pady=(8, 0))
        return inside

    step(1, 'Autorize no Windows',
         'No painel principal, abra Permissões, marque os recursos desejados e clique em '
         'Conectar / Autorizar. O acesso nunca vem habilitado de fábrica.')
    local = step(2, 'Pareie um cliente MCP local',
                 'Quando o servidor estiver pronto, copie o pareamento somente para '
                 'um cliente confiável. Não publique esse código nem envie por e-mail.')
    panel._button(local, 'Copiar pareamento protegido', panel.copy_pairing,
                  tone='primary').pack(anchor='w', pady=(10, 0))
    remote = step(3, 'Acesso externo ao ChatGPT/Codex',
                  'O servidor local não abre acesso à internet. É necessário configurar '
                  'conexão autenticada própria para cada pessoa e computador.')
    links = tk.Frame(remote, bg=panel.COLORS['surface'])
    links.pack(anchor='w', pady=(10, 0))
    panel._button(links, 'Configurações OpenAI', lambda: webbrowser.open(TUNNEL_SETTINGS)
                  ).pack(side='left', padx=(0, 8))
    panel._button(links, 'Guia oficial', lambda: webbrowser.open(TUNNEL_GUIDE)
                  ).pack(side='left')

    diagnostic_edge, diagnostic = panel._card(page, pad=15)
    diagnostic_edge.pack(fill='both', expand=True, pady=(14, 8))
    panel._text(diagnostic, 'DIAGNÓSTICO LOCAL', 10, 'bold', panel.COLORS['cyan']).pack(anchor='w')
    summary = tk.StringVar()

    def refresh():
        data = local_diagnostic(panel)
        ready = data['server_ready'] and data['session_active']
        summary.set(
            f"Servidor MCP: {'PRONTO' if ready else 'PARADO / NÃO AUTORIZADO'}   |   "
            f"Porta: {data['port']}\n"
            f"Permissões: {', '.join(data['permissions']) or 'nenhuma'}\n"
            f"Cliente de túnel detectado: {'sim' if data['tunnel_client_found'] else 'não'}\n"
            'Conexão externa: não confirmada por este diagnóstico.'
        )
    panel._text(diagnostic, '', 10, color=panel.COLORS['text'],
                textvariable=summary, justify='left', wraplength=635).pack(
        anchor='w', pady=(10, 8))
    buttons = tk.Frame(diagnostic, bg=panel.COLORS['surface'])
    buttons.pack(anchor='w')
    panel._button(buttons, 'Atualizar diagnóstico', refresh).pack(side='left', padx=(0, 8))
    panel._button(buttons, 'Fechar', dialog.destroy).pack(side='left')
    refresh()
