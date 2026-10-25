"""Offline user-interface translations (PT-BR, English, Español)."""
import json
from pathlib import Path

LANGUAGES = {'pt-BR': 'Português (Brasil)', 'en': 'English', 'es': 'Español'}
INSTALLER_CODES = {'brazilianportuguese': 'pt-BR', 'english': 'en', 'spanish': 'es'}

# Each key is the original Portuguese UI string. Keep technical names unchanged.
WORDS = {
    'Início': ('Home', 'Inicio'),
    'Permissões': ('Permissions', 'Permisos'),
    'Ferramentas': ('Tools', 'Herramientas'),
    'Atividade': ('Activity', 'Actividad'),
    'Assistente': ('Assistant', 'Asistente'),
    'Minimizar': ('Minimize', 'Minimizar'),
    'MENU': ('MENU', 'MENÚ'),
    'SESSÃO LOCAL': ('LOCAL SESSION', 'SESIÓN LOCAL'),
    '● DESCONECTADO': ('● DISCONNECTED', '● DESCONECTADO'),
    '● CONECTADO LOCAL': ('● CONNECTED LOCALLY', '● CONECTADO LOCAL'),
    '● INICIANDO': ('● STARTING', '● INICIANDO'),
    'Servidor inativo': ('Server offline', 'Servidor inactivo'),
    'Sem sessão autorizada': ('No authorized session', 'Sin sesión autorizada'),
    'CONTROLE SOB SUA AUTORIZAÇÃO': ('YOU CONTROL ACCESS', 'TÚ CONTROLAS EL ACCESO'),
    'Bem-vindo': ('Welcome', 'Bienvenido'),
    ' ao ': (' to ', ' a '),
    'Seu computador e suas automações em um único lugar.': (
        'Your computer and automations in one place.',
        'Tu ordenador y tus automatizaciones en un solo lugar.'),
    'STATUS DA CONEXÃO': ('CONNECTION STATUS', 'ESTADO DE CONEXIÓN'),
    'MCP LOCAL': ('LOCAL MCP', 'MCP LOCAL'),
    'Conexão protegida neste PC • uso remoto requer pareamento autenticado': (
        'Protected on this PC • remote use requires authenticated pairing',
        'Protegido en este PC • el acceso remoto requiere vinculación autenticada'),
    'Configurar acesso': ('Configure access', 'Configurar acceso'),
    'PARAR ACESSO': ('STOP ACCESS', 'DETENER ACCESO'),
    'SERVIDOR MCP': ('MCP SERVER', 'SERVIDOR MCP'),
    'PERMISSÕES ATIVAS': ('ACTIVE PERMISSIONS', 'PERMISOS ACTIVOS'),
    'ACESSO RÁPIDO': ('QUICK ACCESS', 'ACCESO RÁPIDO'),
    'Abra o navegador ou use o assistente para configurar o pareamento.': (
        'Open the browser or use the wizard to set up pairing.',
        'Abre el navegador o usa el asistente para configurar la vinculación.'),
    'Abrir navegador': ('Open browser', 'Abrir navegador'),
    'Assistente de conexão': ('Connection wizard', 'Asistente de conexión'),
    'Última atividade': ('Latest activity', 'Última actividad'),
    'Permissões e segurança': ('Permissions & security', 'Permisos y seguridad'),
    'Escolha exatamente o que o NAVIX pode controlar neste PC.': (
        'Choose exactly what NAVIX may control on this PC.',
        'Elige exactamente qué puede controlar NAVIX en este PC.'),
    'Navegador': ('Browser', 'Navegador'),
    'Mouse, teclado e tela': ('Mouse, keyboard & screen', 'Ratón, teclado y pantalla'),
    'Arquivos e pastas': ('Files & folders', 'Archivos y carpetas'),
    'Comandos e programas': ('Commands & programs', 'Comandos y programas'),
    'Abrir páginas, clicar, preencher e baixar arquivos autorizados.': (
        'Open pages, click, fill forms and download authorized files.',
        'Abrir páginas, pulsar, rellenar y descargar archivos autorizados.'),
    'Controlar a área de trabalho e capturar imagens.': (
        'Control desktop and capture screenshots.',
        'Controlar el escritorio y capturar pantallas.'),
    'Ler, criar, editar, mover ou apagar arquivos.': (
        'Read, create, edit, move or delete files.',
        'Leer, crear, editar, mover o eliminar archivos.'),
    'Executar PowerShell, Python e outros programas.': (
        'Run PowerShell, Python and other programs.',
        'Ejecutar PowerShell, Python y otros programas.'),
    'Tempo de autorização:': ('Authorization duration:', 'Duración del permiso:'),
    'minutos': ('minutes', 'minutos'),
    'Marcar todas': ('Select all', 'Seleccionar todos'),
    'Conectar / Autorizar': ('Connect / Authorize', 'Conectar / Autorizar'),
    'Alterar qualquer permissão revoga a sessão atual.\nAcesso completo exige sua confirmação; não ultrapassa os limites do Windows.': (
        'Changing a permission revokes this session.\nFull access requires confirmation and never bypasses Windows controls.',
        'Cambiar un permiso revoca la sesión.\nEl acceso total requiere confirmación y no elude controles de Windows.'),
    'Navegação, diagnóstico e pareamento em áreas separadas.': (
        'Navigation, diagnostics and pairing in separate sections.',
        'Navegación, diagnóstico y vinculación por separado.'),
    'NAVEGAÇÃO': ('BROWSER', 'NAVEGACIÓN'),
    'O navegador usa perfil próprio de automação.': (
        'Automation uses a separate browser profile.',
        'La automatización usa un perfil del navegador separado.'),
    'Abrir navegador integrado': ('Open integrated browser', 'Abrir navegador integrado'),
    'Abrir Opera': ('Open Opera', 'Abrir Opera'),
    'DIAGNÓSTICO E REPARO': ('DIAGNOSTICS & REPAIR', 'DIAGNÓSTICO Y REPARACIÓN'),
    'Veja o estado real do servidor ou reinicie uma conexão parada.': (
        'Check server status or restart a stopped connection.',
        'Consulta el estado o reinicia una conexión detenida.'),
    'Diagnosticar': ('Run diagnostics', 'Diagnosticar'),
    'Reparar conexão': ('Repair connection', 'Reparar conexión'),
    'PAREAMENTO': ('PAIRING', 'VINCULACIÓN'),
    'Copie a credencial apenas para um cliente MCP autorizado.\nAcesso pela internet não é ativado automaticamente.': (
        'Only copy credentials to an authorized MCP client.\nInternet access is not enabled automatically.',
        'Copia las credenciales solo a un cliente MCP autorizado.\nNo se activa el acceso por Internet automáticamente.'),
    'Copiar pareamento': ('Copy pairing', 'Copiar vinculación'),
    'Atividade e eventos': ('Activity & events', 'Actividad y eventos'),
    'Mensagens locais da sessão. O histórico de auditoria fica no computador.': (
        'Local session messages. Audit history stays on this PC.',
        'Mensajes locales. El historial de auditoría permanece en este PC.'),
    'Limpar visualização': ('Clear view', 'Limpiar vista'),
    'Logs / Diagnóstico': ('Logs / Diagnostics', 'Registros / Diagnóstico'),
    'Ver logs': ('View logs', 'Ver registros'),
    'Exportar diagnóstico': ('Export diagnostics', 'Exportar diagnóstico'),
    'IDIOMA': ('LANGUAGE', 'IDIOMA'),
    'ALFAMNA © 2026 — Todos os direitos reservados.': (
        'ALFAMNA © 2026 — All rights reserved.',
        'ALFAMNA © 2026 — Todos los derechos reservados.'),
    'Conectar com ChatGPT': ('Connect to ChatGPT', 'Conectar con ChatGPT'),
    'Desconectar túnel': ('Disconnect tunnel', 'Desconectar túnel'),
    'Sem prazo': ('No time limit', 'Sin límite'),
    'Assistente NavixX': ('NavixX connection wizard', 'Asistente de conexión NavixX'),
    'Configuração guiada e diagnóstico sem esconder informações.': (
        'Guided configuration and transparent diagnostics.',
        'Configuración guiada y diagnóstico transparente.'),
    'Autorize este computador': ('Authorize this computer', 'Autorizar este ordenador'),
    'Na tela Permissões, selecione os recursos e clique em Conectar / Autorizar. '
    'O acesso vem desligado de fábrica e pode ser revogado a qualquer momento.': (
        'On Permissions, choose features and click Connect / Authorize. Access is disabled by default and can be revoked any time.',
        'En Permisos, elige recursos y pulsa Conectar / Autorizar. El acceso está desactivado inicialmente y se puede revocar siempre.'),
    'Conecte com um clique — sem PowerShell': (
        'Connect with one click — no PowerShell',
        'Conecta con un clic — sin PowerShell'),
    'Uma única vez, informe o ID do seu túnel e a chave restrita da sua '
    'conta OpenAI. O NavixX verifica a conexão, inicia o cliente de túnel '
    'incorporado e tenta reconectar quando há falhas temporárias.': (
        'Once, enter your own OpenAI tunnel ID and restricted API key. NavixX checks connectivity, starts the bundled client and retries temporary failures.',
        'Una sola vez, introduce el ID del túnel y tu clave restringida de OpenAI. NavixX verifica la conexión, inicia el cliente incorporado e intenta reconectar tras fallos temporales.'),
    'ID do túnel (tunnel_…)': ('Tunnel ID (tunnel_…)', 'ID del túnel (tunnel_…)'),
    'Chave da sua conta OpenAI (não aparece na tela)': (
        'Your OpenAI account key (hidden)', 'Clave de tu cuenta OpenAI (oculta)'),
    'Lembrar chave criptografada neste usuário Windows (DPAPI)': (
        'Remember encrypted key for this Windows user (DPAPI)',
        'Recordar clave cifrada para este usuario Windows (DPAPI)'),
    'Vincule no ChatGPT uma única vez': (
        'Link in ChatGPT once', 'Vincula una sola vez en ChatGPT'),
    'Abra ChatGPT → Plugins → + → Adicionar servidor MCP personalizado → Tunnel. '
    'Escolha o mesmo ID. O ChatGPT precisa solicitar sua autorização; '
    'o NavixX não pode aceitar permissões por outra pessoa.': (
        'In ChatGPT open Plugins → + → Add custom MCP server → Tunnel. Choose your tunnel ID and approve the security warning. NavixX cannot grant your consent for you.',
        'En ChatGPT abre Plugins → + → Agregar servidor MCP personalizado → Tunnel. Elige tu ID y acepta la advertencia de seguridad. NavixX no puede dar consentimiento por ti.'),
    'Pareamento local avançado (opcional)': (
        'Advanced local pairing (optional)', 'Vinculación local avanzada (opcional)'),
    'Para clientes MCP no mesmo computador, o botão abaixo copia a credencial '
    'de curta duração. A conexão automática acima não exige copiar esse código.': (
        'For MCP clients on this computer, copy the short-lived pairing below. The automated connection above does not need it.',
        'Para clientes MCP de este ordenador, copia la vinculación temporal abajo. La conexión automática no la requiere.'),
    'Configurações OpenAI': ('OpenAI settings', 'Configuración OpenAI'),
    'Abrir ChatGPT': ('Open ChatGPT', 'Abrir ChatGPT'),
    'Guia oficial': ('Official guide', 'Guía oficial'),
    'Copiar pareamento protegido': ('Copy protected pairing', 'Copiar vinculación protegida'),
    'DIAGNÓSTICO LOCAL': ('LOCAL DIAGNOSTICS', 'DIAGNÓSTICO LOCAL'),
    'Atualizar diagnóstico': ('Refresh diagnostics', 'Actualizar diagnóstico'),
    'Fechar assistente': ('Close wizard', 'Cerrar asistente'),
    'Role para conferir todas as etapas e versões.': (
        'Scroll to review every step and version.',
        'Desplázate para ver todos los pasos y versiones.'),
    'Sessão sem prazo': ('Unlimited session', 'Sesión sin límite'),
    'Autorizar acesso completo': ('Authorize full access', 'Autorizar acceso completo'),
    'Selecione pelo menos uma permissão.': (
        'Select at least one permission.', 'Selecciona al menos un permiso.'),
    'Esta sessão permitirá controlar a tela, executar programas e alterar ou apagar '
    'arquivos como seu usuário Windows. Autorizar pelo tempo selecionado?': (
        'This session allows screen control, program execution and file modification or deletion as your Windows user. Authorize for the selected duration?',
        'Esta sesión permite controlar la pantalla, ejecutar programas y modificar o eliminar archivos como tu usuario Windows. ¿Autorizar por el tiempo seleccionado?'),
    'As permissões permanecerão ativas enquanto este programa estiver aberto. '
    'Não use em computador compartilhado ou sem supervisão. '
    'O botão PARAR ACESSO revoga imediatamente a sessão. Confirmar?': (
        'Permissions stay active while this app is open. Do not use on an unattended or shared PC. STOP ACCESS immediately revokes this session. Confirm?',
        'Los permisos siguen activos mientras la aplicación esté abierta. No lo uses sin supervisión ni en un PC compartido. DETENER ACCESO revoca la sesión. ¿Confirmar?'),
}


def translate(text, lang):
    if lang not in ('en', 'es'):
        return text
    translations = WORDS.get(text)
    return translations[0 if lang == 'en' else 1] if translations else text


def load_language(directory, installer_hint=None):
    path = Path(directory) / 'ui-settings.json'
    try:
        saved = json.loads(path.read_text(encoding='utf-8')).get('language')
        if saved in LANGUAGES:
            return saved
    except (OSError, ValueError, TypeError):
        pass
    return INSTALLER_CODES.get(installer_hint, installer_hint) if installer_hint in (
        *INSTALLER_CODES, *LANGUAGES) else 'pt-BR'


def save_language(directory, lang):
    if lang not in LANGUAGES:
        raise ValueError('Idioma indisponível.')
    path = Path(directory) / 'ui-settings.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'language': lang}), encoding='utf-8')
