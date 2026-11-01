// Windows Admin Full Cloud 0.2.0. No bundled credentials.
const VERSION = '0.2.0';
const COOKIE = '__Host-waf_owner';
const PLUGIN = 'https://chatgpt.com/plugins/plugins_6ae69e16f12c8191b27f4641140363bd';
const now = () => Date.now();
const random = () => Array.from(crypto.getRandomValues(new Uint8Array(32)),x=>x.toString(16).padStart(2,'0')).join('');
const hash = async s => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))),x=>x.toString(16).padStart(2,'0')).join('');
const b64sha = async s => btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))))).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
const esc = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const headers = {'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'"};
const json = (v,status=200,extra={}) => new Response(JSON.stringify(v),{status,headers:{...headers,'Content-Type':'application/json',...extra}});
const html = s => new Response('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Windows Admin Full</title><style>body{font:18px system-ui;background:#101620;color:#f2f5fa;max-width:700px;margin:60px auto;padding:24px}button,a{font:inherit;color:#6fcfff}button{background:#202f45;padding:16px;border:1px solid #79b9fa;border-radius:8px;cursor:pointer}input{font:inherit}</style>'+s+'</html>',{headers:{...headers,'Content-Type':'text/html; charset=utf-8'}});
const error = (s,status=400) => json({error:s},status);
const bearer = r => r.headers.get('Authorization')?.match(/^Bearer ([A-Za-z0-9_-]{32,256})$/)?.[1] || '';
const ownerCookie = r => r.headers.get('Cookie')?.split(';').map(s=>s.trim()).find(s=>s.startsWith(COOKIE+'='))?.slice(COOKIE.length+1) || '';
const textResult = value => ({content:[{type:'text',text:JSON.stringify(value)}]});
const toolError = text => ({isError:true,content:[{type:'text',text}]});
// Inserted from the authoritative agent's tool schema during packaging.
const TOOLS = [{"name": "status", "description": "Estado real das permissões e tempo restante da sessão local.", "inputSchema": {"type": "object", "properties": {}, "required": []}}, {"name": "browser_tabs", "description": "Lista abas do navegador de automação aberto pelo proprietário.", "inputSchema": {"type": "object", "properties": {}, "required": []}}, {"name": "browser_open", "description": "Abre URL HTTP/HTTPS numa nova aba do perfil de automação.", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}, {"name": "browser_read", "description": "Lê até 30 mil caracteres visíveis da aba.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}}, {"name": "browser_click", "description": "Clica um elemento pelo papel acessível e nome exato, sem ambiguidades.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "role": {"type": "string"}, "name": {"type": "string"}}, "required": ["page_id", "role", "name"]}}, {"name": "browser_fill", "description": "Preenche um campo identificado por papel e nome acessível exatos.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "role": {"type": "string"}, "name": {"type": "string"}, "text": {"type": "string"}}, "required": ["page_id", "role", "name", "text"]}}, {"name": "browser_scroll", "description": "Rola verticalmente uma aba, até 2000 pixels por chamada.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "pixels": {"type": "integer"}}, "required": ["page_id", "pixels"]}}, {"name": "browser_screenshot", "description": "Captura a área visível da aba autorizada.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}}, {"name": "desktop_screenshot", "description": "Captura a tela inteira somente com permissão de desktop ativa.", "inputSchema": {"type": "object", "properties": {}, "required": []}}, {"name": "desktop_click", "description": "Clica numa coordenada válida da tela; exige sessão autorizada.", "inputSchema": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "button": {"type": "string", "default": "left"}, "clicks": {"type": "integer", "default": 1}}, "required": ["x", "y"]}}, {"name": "desktop_type", "description": "Digita texto na janela em foco, com suporte a acentos no Windows.", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}, {"name": "desktop_key", "description": "Pressiona uma tecla reconhecida pelo teclado do Windows.", "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}, {"name": "desktop_scroll", "description": "Rola o mouse até 20 passos por chamada.", "inputSchema": {"type": "object", "properties": {"steps": {"type": "integer"}}, "required": ["steps"]}}, {"name": "desktop_position", "description": "Retorna a posição atual do cursor do mouse.", "inputSchema": {"type": "object", "properties": {}, "required": []}}, {"name": "desktop_screen_info", "description": "Dimensões da tela principal e posição do cursor.", "inputSchema": {"type": "object", "properties": {}, "required": []}}, {"name": "desktop_move", "description": "Move o cursor para uma coordenada da tela.", "inputSchema": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "duration": {"type": "string", "default": 0.2}}, "required": ["x", "y"]}}, {"name": "desktop_drag", "description": "Arrasta do cursor atual até uma coordenada da tela.", "inputSchema": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "duration": {"type": "string", "default": 0.5}, "button": {"type": "string", "default": "left"}}, "required": ["x", "y"]}}, {"name": "desktop_hotkey", "description": "Executa combinação de teclas, por exemplo ['ctrl', 's'] ou ['alt', 'tab'].", "inputSchema": {"type": "object", "properties": {"keys": {"type": "array", "items": {"type": "string"}}}, "required": ["keys"]}}, {"name": "browser_start", "description": "Abre o navegador integrado ou Opera com perfil separado autorizado.", "inputSchema": {"type": "object", "properties": {"kind": {"type": "string", "default": "integrado"}}, "required": []}}, {"name": "browser_navigate", "description": "Navega uma aba existente para uma URL HTTP/HTTPS.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "url": {"type": "string"}}, "required": ["page_id", "url"]}}, {"name": "browser_close_tab", "description": "Fecha uma aba do perfil de automação.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}}, {"name": "browser_back", "description": "Volta à página anterior na aba.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}}, {"name": "browser_forward", "description": "Avança no histórico da aba.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}}, {"name": "browser_reload", "description": "Recarrega a página e aguarda o DOM.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}}, {"name": "browser_snapshot", "description": "Árvore acessível com nomes e funções dos elementos para localizar campos e botões.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}}, {"name": "browser_select", "description": "Seleciona valores em uma lista HTML identificada por nome e função exatos.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "role": {"type": "string"}, "name": {"type": "string"}, "values": {"type": "array", "items": {"type": "string"}}}, "required": ["page_id", "role", "name", "values"]}}, {"name": "browser_press", "description": "Pressiona tecla ou atalho em um elemento identificado, por exemplo Enter.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "role": {"type": "string"}, "name": {"type": "string"}, "key": {"type": "string"}}, "required": ["page_id", "role", "name", "key"]}}, {"name": "browser_hover", "description": "Posiciona o mouse sobre um elemento da página.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "role": {"type": "string"}, "name": {"type": "string"}}, "required": ["page_id", "role", "name"]}}, {"name": "browser_wait", "description": "Aguarda estado de um elemento, até 30 segundos.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "role": {"type": "string"}, "name": {"type": "string"}, "state": {"type": "string", "default": "visible"}, "timeout_ms": {"type": "integer", "default": 10000}}, "required": ["page_id", "role", "name"]}}, {"name": "browser_upload", "description": "Seleciona arquivos locais em input[type=file]; exige navegador e arquivos.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "selector": {"type": "string"}, "paths": {"type": "array", "items": {"type": "string"}}}, "required": ["page_id", "selector", "paths"]}}, {"name": "browser_download", "description": "Clica um link/botão de download e salva no caminho local explícito, sem sobrescrever.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}, "role": {"type": "string"}, "name": {"type": "string"}, "destination": {"type": "string"}, "timeout_ms": {"type": "integer", "default": 30000}}, "required": ["page_id", "role", "name", "destination"]}}, {"name": "files_list", "description": "Lista arquivos e subpastas de um diretório local.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer", "default": 500}}, "required": ["path"]}}, {"name": "files_read", "description": "Lê um arquivo UTF-8, indicando truncamento quando exceder o limite.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "max_bytes": {"type": "integer", "default": 1000000}}, "required": ["path"]}}, {"name": "files_write", "description": "Cria arquivo UTF-8; substituir um existente exige overwrite=true.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "text": {"type": "string"}, "overwrite": {"type": "boolean", "default": false}}, "required": ["path", "text"]}}, {"name": "files_edit", "description": "Substitui texto exato num arquivo. Recusa correspondência ambígua sem replace_all.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}, "replace_all": {"type": "boolean", "default": false}}, "required": ["path", "old_text", "new_text"]}}, {"name": "files_mkdir", "description": "Cria uma pasta no caminho indicado.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "parents": {"type": "boolean", "default": true}}, "required": ["path"]}}, {"name": "files_copy", "description": "Copia arquivo ou pasta para um destino explícito.", "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}, "overwrite": {"type": "boolean", "default": false}}, "required": ["source", "destination"]}}, {"name": "files_move", "description": "Move ou renomeia arquivo/pasta; não sobrescreve por padrão.", "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}, "overwrite": {"type": "boolean", "default": false}}, "required": ["source", "destination"]}}, {"name": "files_delete", "description": "Apaga permanentemente um arquivo ou pasta vazia. Árvore de pastas exige recursive=true.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "recursive": {"type": "boolean", "default": false}}, "required": ["path"]}}, {"name": "files_read_binary", "description": "Retorna arquivo em base64 para transferir ao cliente MCP.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "max_bytes": {"type": "integer", "default": 5000000}}, "required": ["path"]}}, {"name": "files_write_binary", "description": "Recebe conteúdo base64 do cliente MCP e grava arquivo binário local.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "content_base64": {"type": "string"}, "overwrite": {"type": "boolean", "default": false}}, "required": ["path", "content_base64"]}}, {"name": "files_download", "description": "Baixa HTTP/HTTPS para caminho local, com limite de tempo e tamanho.", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}, "destination": {"type": "string"}, "overwrite": {"type": "boolean", "default": false}, "max_bytes": {"type": "integer", "default": 100000000}, "timeout_seconds": {"type": "integer", "default": 30}}, "required": ["url", "destination"]}}, {"name": "command_run", "description": "Executa PowerShell, cmd ou Python, retornando saída e código de término. Exige comandos.", "inputSchema": {"type": "object", "properties": {"command": {"type": "string"}, "shell": {"type": "string", "default": "powershell"}, "cwd": {"type": "string", "default": ""}, "timeout_seconds": {"type": "integer", "default": 60}}, "required": ["command"]}}, {"name": "command_exec", "description": "Executa programa por lista de argumentos, sem interpretação implícita por shell.", "inputSchema": {"type": "object", "properties": {"argv": {"type": "array", "items": {"type": "string"}}, "cwd": {"type": "string", "default": ""}, "timeout_seconds": {"type": "integer", "default": 60}}, "required": ["argv"]}}];

export class Bridge {
  constructor(ctx,env) { this.ctx=ctx; this.db=ctx.storage; this.env=env; }
  async put(key,value,expires=now()+86400000) { await this.db.put(key,{...value,expires}); if(!await this.db.getAlarm()) await this.db.setAlarm(now()+60000); }
  async get(key) { const v=await this.db.get(key); if(!v || v.expires<now()) {if(v)await this.db.delete(key); return null;} return v; }
  async take(key) { return this.db.transaction(async tx=>{const v=await tx.get(key); if(v)await tx.delete(key);return v&&v.expires>=now()?v:null;}); }
  async rate(key,max,window=60000) { return this.db.transaction(async tx=>{const k='rate:'+key;let v=await tx.get(k);if(!v||v.expires<now())v={n:0,expires:now()+window};v.n++;await tx.put(k,v);return v.n<=max;}); }
  async alarm() { const rows=await this.db.list(); for(const [key,v] of rows) if(v.expires && v.expires<now()) await this.db.delete(key); if(rows.size) await this.db.setAlarm(now()+60000); }
  async owner(r) { const t=ownerCookie(r); return t?this.get('owner:'+await hash(t)):null; }
  async agent(r) { const t=bearer(r); return t?this.get('agent:'+await hash(t)):null; }
  async access(r) { const t=bearer(r); return t?this.get('access:'+await hash(t)):null; }
  async issue(device,client) {
    const access=random(),refresh=random();
    await this.put('access:'+await hash(access),{device,client},now()+3600000);
    await this.put('refresh:'+await hash(refresh),{device,client},now()+90*86400000);
    return {access_token:access,token_type:'Bearer',expires_in:3600,refresh_token:refresh,scope:'windows.admin'};
  }
  async fetch(r) {
    try { return await this.route(r); } catch(e) { return error('Falha na requisicao',400); }
  }
  async route(r) {
    const u=new URL(r.url),path=u.pathname,base=u.origin;
    if(r.headers.get('Origin') && r.headers.get('Origin')!==base) return error('Origem recusada',403);
    if(Number(r.headers.get('Content-Length')||0)>2200000) return error('Requisicao muito grande',413);
    if(path==='/health') return json({service:'windows-admin-full',version:VERSION,cloud:true,windows_verified:false});
    if(path.startsWith('/.well-known/oauth-protected-resource')) return json({resource:base+'/mcp',authorization_servers:[base],scopes_supported:['windows.admin']});
    if(path==='/.well-known/oauth-authorization-server') return json({issuer:base,authorization_endpoint:base+'/authorize',token_endpoint:base+'/token',registration_endpoint:base+'/register',revocation_endpoint:base+'/revoke',response_types_supported:['code'],grant_types_supported:['authorization_code','refresh_token'],code_challenge_methods_supported:['S256'],token_endpoint_auth_methods_supported:['none'],scopes_supported:['windows.admin']});
    if(path==='/setup.js') return new Response(`(async()=>{const secret=location.hash.slice(1);history.replaceState(null,'','/setup');if(!secret){document.getElementById('s').textContent='Reabra VINCULAR_CHATGPT.cmd no PC.';return;}const r=await fetch('/pair',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({setup_token:secret})});const d=await r.json();document.getElementById('s').textContent=r.ok?'PC vinculado neste navegador. Agora abra o plugin e autorize o acesso.':d.error;document.getElementById('plugin').hidden=!r.ok;})();`,{headers:{...headers,'Content-Type':'text/javascript'}});
    if(path==='/setup' && r.method==='GET') return html('<h1>Windows Admin Full</h1><p id="s">Vinculando seu PC...</p><p id="plugin" hidden><a href="'+PLUGIN+'">Abrir plugin no ChatGPT</a></p><script src="/setup.js"></script>');
    if(path==='/device/register' && r.method==='POST') {
      const ip=r.headers.get('CF-Connecting-IP')||'local';
      if(!await this.rate('enroll:'+ip,5,3600000)) return error('Limite temporario de instalacoes',429);
      const count=await this.db.list({prefix:'device:'}); if(count.size>=25) return error('Limite de dispositivos atingido',429);
      const a=await r.json(); if(typeof a.name!=='string'||a.name.length>100)return error('Nome invalido');
      const device=random(),token=random(),setup=random();
      await this.put('device:'+device,{name:a.name,last_seen:0,active:true},now()+365*86400000);
      await this.put('agent:'+await hash(token),{device},now()+365*86400000);
      await this.put('setup:'+await hash(setup),{device},now()+600000);
      return json({device_id:device,agent_token:token,setup_url:base+'/setup#'+setup});
    }
    if(path==='/device/setup' && r.method==='POST') {
      const a=await this.agent(r);if(!a)return error('Nao autorizado',401);
      const setup=random();await this.put('setup:'+await hash(setup),{device:a.device},now()+600000);
      return json({setup_url:base+'/setup#'+setup});
    }
    if(path==='/pair' && r.method==='POST') {
      const a=await r.json(); if(typeof a.setup_token!=='string')return error('Vinculo invalido');
      const link=await this.take('setup:'+await hash(a.setup_token));if(!link)return error('Vinculo expirado; reabra VINCULAR_CHATGPT.cmd',401);
      const cookie=random();await this.put('owner:'+await hash(cookie),{device:link.device},now()+365*86400000);
      return json({linked:true},200,{'Set-Cookie':COOKIE+'='+cookie+'; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=31536000'});
    }
    if(path==='/register' && r.method==='POST') {
      if(!await this.rate('client:'+(r.headers.get('CF-Connecting-IP')||'local'),30,3600000))return error('Limite temporario',429);
      const a=await r.json();
      if(!Array.isArray(a.redirect_uris)||!a.redirect_uris.length||a.redirect_uris.length>5)return error('redirect_uris invalido');
      for(const uri of a.redirect_uris){const x=new URL(uri);if(x.protocol!=='https:'||!['chatgpt.com','chat.openai.com','platform.openai.com'].includes(x.hostname)||x.username||x.password||x.hash) return error('Callback precisa pertencer ao ChatGPT');}
      const client=random();await this.put('client:'+client,{redirects:a.redirect_uris,name:String(a.client_name||'Cliente ChatGPT').slice(0,100)},now()+365*86400000);
      return json({client_id:client,redirect_uris:a.redirect_uris,token_endpoint_auth_method:'none',grant_types:['authorization_code','refresh_token'],response_types:['code']},201);
    }
    if(path==='/authorize' && r.method==='GET') {
      const client=await this.get('client:'+u.searchParams.get('client_id'));
      const redirect=u.searchParams.get('redirect_uri'),challenge=u.searchParams.get('code_challenge');
      if(!client||!client.redirects.includes(redirect)||u.searchParams.get('response_type')!=='code'||u.searchParams.get('code_challenge_method')!=='S256'||!challenge?.match(/^[A-Za-z0-9_-]{43}$/))return error('Parametros OAuth invalidos');
      const owner=await this.owner(r);
      if(!owner)return html('<h1>Vincule seu PC primeiro</h1><p>No Windows, abra <b>VINCULAR_CHATGPT.cmd</b> e use este mesmo navegador. Depois volte aqui e atualize esta pagina.</p>');
      const device=await this.get('device:'+owner.device);if(!device?.active)return error('Dispositivo desativado',403);
      const consent=random();await this.put('consent:'+consent,{device:owner.device,owner:await hash(ownerCookie(r)),client:u.searchParams.get('client_id'),redirect,challenge,state:u.searchParams.get('state')||''},now()+600000);
      return html('<h1>Autorizar administracao do Windows</h1><p>Computador: <b>'+esc(device.name)+'</b></p><p>Cliente: '+esc(client.name)+'</p><p>Permite comandos, alteracao e exclusao de arquivos, programas, servicos, captura de tela, mouse e teclado, com os privilegios do agente. Autorize apenas se voce iniciou esta conexao no ChatGPT.</p><form method="post" action="/approve"><input type="hidden" name="consent" value="'+consent+'"><button>Autorizar este ChatGPT</button></form>');
    }
    if(path==='/approve' && r.method==='POST') {
      const form=await r.formData(),owner=await this.owner(r);if(!owner)return error('Sessao ausente',401);
      const id=form.get('consent');const c=await this.get('consent:'+id);
      if(!c||c.device!==owner.device||c.owner!==await hash(ownerCookie(r)))return error('Autorizacao invalida',403);
      if(!await this.take('consent:'+id))return error('Autorizacao ja utilizada',403);
      const code=random();await this.put('code:'+await hash(code),c,now()+120000);
      const dest=new URL(c.redirect);dest.searchParams.set('code',code);dest.searchParams.set('state',c.state);
      return new Response(null,{status:303,headers:{...headers,Location:dest.href}});
    }
    if(path==='/token' && r.method==='POST') {
      const form=await r.formData(),client=form.get('client_id');
      if(form.get('grant_type')==='authorization_code') {
        const code=form.get('code');if(typeof code!=='string')return error('invalid_grant');
        const c=await this.get('code:'+await hash(code)),verifier=form.get('code_verifier');
        if(!c||c.client!==client||c.redirect!==form.get('redirect_uri')||typeof verifier!=='string'||!/^[A-Za-z0-9._~-]{43,128}$/.test(verifier)||await b64sha(verifier)!==c.challenge)return error('invalid_grant');
        if(!await this.take('code:'+await hash(code)))return error('invalid_grant');
        return json(await this.issue(c.device,client));
      }
      if(form.get('grant_type')==='refresh_token') {
        const token=form.get('refresh_token');if(typeof token!=='string')return error('invalid_grant');
        const c=await this.get('refresh:'+await hash(token));if(!c||c.client!==client||!(await this.get('device:'+c.device))?.active)return error('invalid_grant');
        if(!await this.take('refresh:'+await hash(token)))return error('invalid_grant');
        return json(await this.issue(c.device,client));
      }
      return error('unsupported_grant_type');
    }
    if(path==='/revoke' && r.method==='POST') {
      const form=await r.formData(),t=form.get('token');if(typeof t==='string'){const h=await hash(t);for(const prefix of ['access:','refresh:'])await this.db.delete(prefix+h);}return json({});
    }
    if(path==='/device/poll' && r.method==='POST') {
      const a=await this.agent(r);if(!a)return error('Nao autorizado',401);
      const d=await this.get('device:'+a.device);if(!d?.active)return error('Desativado',403);
      const body=await r.json();
      const tools=Array.isArray(body.tools)&&body.tools.length<=80&&JSON.stringify(body.tools).length<60000?body.tools:d.tools;
      await this.put('device:'+a.device,{...d,last_seen:now(),status:body.status||{},tools},now()+365*86400000);
      const rows=await this.db.list({prefix:'job:'+a.device+':'});
      for(const [key,job] of rows){
        if(job.expires<now()){await this.db.delete(key);continue;}
        if(job.state==='queued'){
          const claimed=await this.db.transaction(async tx=>{const j=await tx.get(key);if(!j||j.state!=='queued'||j.expires<now())return null;j.state='running';await tx.put(key,j);return j;});
          if(claimed)return json({job_id:key,request:claimed.request});
        }
      }
      return json({idle:true});
    }
    if(path==='/device/result' && r.method==='POST') {
      const a=await this.agent(r);if(!a)return error('Nao autorizado',401);
      const body=await r.json();
      if(typeof body.job_id!=='string'||!body.job_id.startsWith('job:'+a.device+':'))return error('Trabalho invalido',403);
      const job=await this.get(body.job_id);if(!job||!['running','done'].includes(job.state))return error('Trabalho expirado',410);
      if(job.state==='done')return json({ok:true});
      const result=JSON.stringify(body.result);if(result.length>2000000)return error('Resposta muito grande',413);
      const count=Math.ceil(result.length/25000);
      for(let i=0;i<count;i++)await this.put('chunk:'+body.job_id+':'+i,{text:result.slice(i*25000,(i+1)*25000)},now()+300000);
      await this.put(body.job_id,{...job,state:'done',chunks:count,request:null},now()+300000);
      return json({ok:true});
    }
    if(path==='/mcp') {
      const access=await this.access(r),device=access?await this.get('device:'+access.device):null;
      if(!access||!device?.active)return error('Unauthorized',401,);
      if(r.method!=='POST')return error('Use POST',405);
      const msg=await r.json();
      if(msg.jsonrpc!=='2.0'||typeof msg.method!=='string')return json({jsonrpc:'2.0',id:null,error:{code:-32600,message:'Invalid Request'}});
      if(!('id' in msg))return new Response(null,{status:202,headers});
      let result;
      if(msg.method==='initialize')result={protocolVersion:['2025-03-26','2025-06-18','2025-11-25'].includes(msg.params?.protocolVersion)?msg.params.protocolVersion:'2025-11-25',serverInfo:{name:'windows-admin-full',version:VERSION},capabilities:{tools:{listChanged:false}}};
      else if(msg.method==='ping')result={};
      else if(msg.method==='tools/list')result={tools:device.tools||TOOLS};
      else if(msg.method==='tools/call') {
        const p=msg.params;
        if(!p||!(device.tools||TOOLS).some(t=>t.name===p.name))result=toolError('Ferramenta desconhecida');
        else if(p.arguments?.timeout_seconds>35)result=toolError('A ponte aceita comandos de ate 35 segundos. Inicie tarefas longas em segundo plano e consulte seu estado.');
        else if(now()-device.last_seen>30000)result=toolError('PC desconectado. Abra INICIAR_ADMIN.cmd no Windows. Nenhuma acao foi enviada.');
        else if(new TextEncoder().encode(JSON.stringify(p)).length>48000)result=toolError('Argumentos excedem 48 KB. Transfira arquivos em blocos.');
        else {
          if(['command_run','command_exec'].includes(p.name)){p.arguments={...p.arguments,timeout_seconds:Math.min(p.arguments?.timeout_seconds||30,35)};}
          const jobs=await this.db.list({prefix:'job:'+access.device+':'});
          if([...jobs.values()].some(j=>['queued','running'].includes(j.state)&&j.expires>now()))result=toolError('Ja existe uma acao em andamento neste PC. Aguarde o resultado.');
          else {
            const id='job:'+access.device+':'+random();
            const slot='slot:'+access.device;
            const claimed=await this.db.transaction(async tx=>{
              const current=await tx.get(slot);if(current&&current.expires>now())return false;
              const expires=now()+55000;
              await tx.put(slot,{job:id,expires});
              await tx.put(id,{state:'queued',request:{jsonrpc:'2.0',id:msg.id,method:'tools/call',params:p},expires});
              return true;
            });
            if(!claimed)return json({jsonrpc:'2.0',id:msg.id,result:toolError('Ja existe uma acao em andamento neste PC.')});
            if(!await this.db.getAlarm())await this.db.setAlarm(now()+60000);
            const deadline=now()+50000;
            while(now()<deadline){
              const job=await this.get(id);
              if(job?.state==='done'){
                let combined='';for(let i=0;i<job.chunks;i++){const chunk=await this.get('chunk:'+id+':'+i);combined+=chunk?.text||'';await this.db.delete('chunk:'+id+':'+i);}
                result=JSON.parse(combined);await this.db.delete(id);await this.db.delete(slot);break;
              }
              await new Promise(resolve=>setTimeout(resolve,400));
            }
            if(!result){const job=await this.get(id);if(job?.state==='queued'){await this.db.delete(id);await this.db.delete(slot);}result=toolError(job?.state==='running'?'Tempo de resposta esgotado. A acao pode ter sido executada; confira o estado antes de repetir.':'PC nao recebeu a acao dentro do prazo.');}
          }
        }
      } else return json({jsonrpc:'2.0',id:msg.id,error:{code:-32601,message:'Method not found'}});
      return json({jsonrpc:'2.0',id:msg.id,result});
    }
    if(path==='/')return html('<h1>Windows Admin Full</h1><p>Ponte privada de administracao do Windows. Instale o agente e abra VINCULAR_CHATGPT.cmd para conectar seu computador.</p><a href="'+PLUGIN+'">Abrir plugin</a>');
    return error('Nao encontrado',404);
  }
}
export default {async fetch(request,env){const id=env.BRIDGE.idFromName('private-windows-admin-v1');const response=await env.BRIDGE.get(id).fetch(request);if(new URL(request.url).pathname==='/mcp'&&response.status===401){const h=new Headers(response.headers);h.set('WWW-Authenticate','Bearer resource_metadata="'+new URL(request.url).origin+'/.well-known/oauth-protected-resource/mcp"');return new Response(response.body,{status:401,headers:h});}return response;}};
