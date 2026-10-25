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
    dialog = tk.Toplevel(panel.root)
    dialog.title('NAVIX Desktop — assistente de conexão')
    dialog.geometry('710x660')
    dialog.minsize(650, 570)
    dialog.transient(panel.root)
    frame = ttk.Frame(dialog, padding=20)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Configurar NAVIX Desktop', font=('Segoe UI', 19, 'bold')).pack(anchor='w')
    ttk.Label(frame, text='Passo a passo para uso próprio ou instalação por outras pessoas.',
              wraplength=650).pack(anchor='w', pady=(4, 12))

    first = ttk.LabelFrame(frame, text='1. Ativar no próprio computador', padding=12)
    first.pack(fill='x', pady=6)
    ttk.Label(first, text='No painel principal, selecione as permissões e clique em Conectar / Autorizar. '
              'Cada computador concede suas próprias permissões; nenhuma vem habilitada de fábrica.',
              wraplength=620).pack(anchor='w')

    second = ttk.LabelFrame(frame, text='2. Parear um cliente MCP local', padding=12)
    second.pack(fill='x', pady=6)
    ttk.Label(second, text='Com o servidor pronto, copie a URL local e o cabeçalho de autenticação '
              'somente para um cliente MCP confiável neste computador. Nunca publique esse conteúdo.',
              wraplength=620).pack(anchor='w', pady=(0, 6))
    ttk.Button(second, text='Copiar pareamento protegido', command=panel.copy_pairing).pack(anchor='w')

    third = ttk.LabelFrame(frame, text='3. Conectar ChatGPT ou Codex pela internet', padding=12)
    third.pack(fill='x', pady=6)
    ttk.Label(third, text='O servidor local não fica acessível na internet automaticamente. '
              'Uma conexão externa exige autenticação própria, permissões da conta OpenAI '
              'e um túnel ou serviço HTTPS compatível. O túnel de outra pessoa não serve.',
              wraplength=620).pack(anchor='w', pady=(0, 6))
    row = ttk.Frame(third)
    row.pack(anchor='w')
    ttk.Button(row, text='Abrir túneis OpenAI',
               command=lambda: webbrowser.open(TUNNEL_SETTINGS)).pack(side='left', padx=(0, 8))
    ttk.Button(row, text='Ler guia oficial',
               command=lambda: webbrowser.open(TUNNEL_GUIDE)).pack(side='left')

    diagnostic = tk.StringVar()
    fourth = ttk.LabelFrame(frame, text='Diagnóstico da instalação', padding=12)
    fourth.pack(fill='both', expand=True, pady=8)
    ttk.Label(fourth, textvariable=diagnostic, wraplength=620, justify='left').pack(anchor='w')

    def refresh():
        data = local_diagnostic(panel)
        local = 'PRONTO' if data['server_ready'] and data['session_active'] else 'NÃO AUTORIZADO / INDISPONÍVEL'
        components = ', '.join(f'{key}: {value}' for key, value in data['packages'].items())
        diagnostic.set(
            f'Servidor MCP local: {local}\n'
            f'Porta: {data["port"]}\n'
            f'Permissões nesta sessão: {", ".join(data["permissions"]) or "nenhuma"}\n'
            f'Cliente de túnel encontrado: {"sim" if data["tunnel_client_found"] else "não"}\n'
            f'Componentes: {components}\n'
            'Conexão externa: não confirmada neste diagnóstico.'
        )
    ttk.Button(fourth, text='Atualizar diagnóstico', command=refresh).pack(anchor='w', pady=(8, 0))
    refresh()
