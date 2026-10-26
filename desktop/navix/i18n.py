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
    'Apoie o projeto': ('Support the project', 'Apoya el proyecto'),
    'Assistente': ('Assistant', 'Asistente'),
    'Desinstalar NavixX Desktop': ('Uninstall NavixX Desktop', 'Desinstalar NavixX Desktop'),
    'DESINSTALAÇÃO': ('UNINSTALL', 'DESINSTALACIÓN'),
    'Remova o aplicativo pelo desinstalador oficial. Você poderá escolher se deseja excluir também credenciais, configurações e logs.': (
        'Remove the app with its official uninstaller. You may also choose to delete credentials, settings and logs.',
        'Elimina la aplicación con su desinstalador oficial. También puedes borrar credenciales, ajustes y registros.'),
    'Apoie o NavixX': ('Support NavixX', 'Apoya NavixX'),
    'Contribuição voluntária para o desenvolvimento do projeto ALFAMNA.': (
        'Voluntary contribution to the ALFAMNA project.',
        'Contribución voluntaria al proyecto ALFAMNA.'),
    'DOAÇÃO VIA PIX': ('DONATE BY PIX', 'DONAR POR PIX'),
    'Valor livre. Nenhuma doação é necessária para usar o NavixX.': (
        'Any amount. Donations are never required to use NavixX.',
        'Cualquier importe. No es necesario donar para usar NavixX.'),
    'Beneficiário informado: Wilson Neves de Almeida • Campo Grande/MS': (
        'Stated beneficiary: Wilson Neves de Almeida • Campo Grande, Brazil',
        'Beneficiario indicado: Wilson Neves de Almeida • Campo Grande, Brasil'),
    'Chave Pix aleatória informada (opção adicional):': (
        'Provided random Pix key (additional option):',
        'Clave Pix aleatoria proporcionada (opción adicional):'),
    'Copiar Pix Copia e Cola': ('Copy Pix payment code', 'Copiar código Pix'),
    'Copiar chave aleatória': ('Copy random Pix key', 'Copiar clave Pix aleatoria'),
    'O QR Code usa uma chave Pix do tipo e-mail, diferente da chave aleatória. Confira o beneficiário e a instituição no aplicativo bancário antes de confirmar. Este projeto é independente do Banco do Brasil.': (
        'The QR uses an email Pix key, different from the random key. Verify the payee and bank in your banking app before confirming. This project is independent of Banco do Brasil.',
        'El QR usa una clave Pix de correo distinta de la clave aleatoria. Comprueba beneficiario y banco antes de confirmar. Este proyecto es independiente del Banco do Brasil.'),
    'Minimizar': ('Minimize', 'Minimizar'),
    'Bloquear painel': ('Lock panel', 'Bloquear panel'),
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
    'Chave Runtime OpenAI (Tunnels Read + Use; oculta)': (
        'OpenAI Runtime key (Tunnels Read + Use; hidden)',
        'Clave Runtime OpenAI (Tunnels Read + Use; oculta)'),
    'Lembrar chave criptografada neste usuário Windows (DPAPI)': (
        'Remember encrypted key for this Windows user (DPAPI)',
        'Recordar clave cifrada para este usuario Windows (DPAPI)'),
    'Sua conta OpenAI: túnel e chave Runtime': (
        'Your OpenAI account: tunnel and Runtime key',
        'Tu cuenta OpenAI: túnel y clave Runtime'),
    '① Entre na Plataforma OpenAI com sua conta.\n'
    '② Na organização correta, abra Tunnels e crie um túnel para o NavixX. '
    'A criação exige Tunnels Read + Manage. Copie o ID tunnel_…\n'
    '③ Abra API Keys e crie uma chave Runtime restrita, com Tunnels Read + Use. '
    'Dê um nome como “NavixX deste computador”.\n'
    '④ Copie a chave uma vez, cole abaixo e marque o cofre criptografado. '
    'Nunca envie a chave por e-mail, chat ou captura de tela.\n'
    'Uma chave API comum sem permissão de túnel NÃO conecta o NavixX.': (
        '① Sign in to OpenAI Platform.\n'
        '② In the correct organization, open Tunnels and create a NavixX tunnel. '
        'Creation requires Tunnels Read + Manage. Copy the tunnel_… ID.\n'
        '③ Open API Keys and create a restricted Runtime key with Tunnels Read + Use. '
        'Name it “NavixX on this PC”.\n'
        '④ Copy the key once, paste below and enable the encrypted vault. '
        'Never send the key in email, chat or screenshots.\n'
        'A general API key without tunnel access WILL NOT connect NavixX.',
        '① Inicia sesión en OpenAI Platform.\n'
        '② En tu organización, abre Tunnels y crea el túnel NavixX. '
        'Se necesita Tunnels Read + Manage. Copia el ID tunnel_…\n'
        '③ Abre API Keys y crea una clave Runtime restringida con Tunnels Read + Use. '
        'Nómbrala “NavixX de este equipo”.\n'
        '④ Copia la clave una vez, pégala abajo y activa la bóveda cifrada. '
        'Nunca la envíes por correo, chat ni capturas.\n'
        'Una clave API general sin permisos del túnel NO conectará NavixX.'),
    '1. Entrar na OpenAI': ('1. Open OpenAI', '1. Entrar en OpenAI'),
    '2. Criar túnel': ('2. Create tunnel', '2. Crear túnel'),
    '3. Chaves API': ('3. API keys', '3. Claves API'),
    'Cole o ID de túnel e a chave Runtime criada na sua própria conta. '
    'O NavixX verifica a conexão, inicia o cliente incorporado e tenta '
    'reconectar quando houver falhas temporárias.': (
        'Enter your own tunnel ID and Runtime key. NavixX verifies the connection, '
        'starts its bundled client and retries temporary failures.',
        'Introduce tu ID del túnel y clave Runtime. NavixX verifica la conexión, '
        'inicia el cliente incorporado y reintenta los fallos temporales.'),
    'Meu cofre • ver chave salva com senha': (
        'My vault • reveal saved key with password',
        'Mi bóveda • ver clave guardada con contraseña'),
    'Chave armazenada:': ('Saved key:', 'Clave guardada:'),
    'Sim, protegida pelo Windows': ('Yes, protected by Windows', 'Sí, protegida por Windows'),
    'Não': ('No', 'No'),
    ' • deixe o campo vazio para reutilizar a chave salva.': (
        ' • leave blank to reuse saved key.',
        ' • deja vacío para reutilizar la clave guardada.'),
    'Criar login local': ('Create local login', 'Crear acceso local'),
    'Entrar': ('Sign in', 'Entrar'),
    'Proteção do painel deste usuário Windows': (
        'Panel protection for this Windows user',
        'Protección del panel de este usuario Windows'),
    'Crie uma senha local': ('Create a local password', 'Crea una contraseña local'),
    'Digite a senha local': ('Enter your local password', 'Introduce tu contraseña local'),
    'Confirme a senha (mínimo 10 caracteres)': (
        'Confirm password (at least 10 characters)',
        'Confirma la contraseña (mínimo 10 caracteres)'),
    'Login local, não é sua senha OpenAI.': (
        'Local login, not your OpenAI password.',
        'Acceso local, no es tu contraseña de OpenAI.'),
    'Criar login e entrar': ('Create login and sign in', 'Crear acceso y entrar'),
    'Entrar no NavixX': ('Sign in to NavixX', 'Entrar en NavixX'),
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
