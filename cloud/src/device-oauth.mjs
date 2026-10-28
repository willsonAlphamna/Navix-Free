/** Public-client OAuth 2.1 + PKCE, anchored to a one-time code on the Windows PC.
 * No user shares a Cloudflare login, ChatGPT API key, or any universal secret.
 * Only the official ChatGPT CIMD client/redirect is accepted in this release.
 */
export const CLIENT_ID='https://chatgpt.com/oauth/client.json';
export const CALLBACK='https://chatgpt.com/connector_platform_oauth_redirect';
export const SCOPE='navix:control';
const DEVICE=/^[A-Za-z0-9_-]{16,128}$/;
const PKCE=/^[A-Za-z0-9_-]{43}$/;
const CODE=/^\d{6}$/;
const TOKEN=/^[A-Za-z0-9_-]{43,128}$/;
const toHex=bytes=>[...new Uint8Array(bytes)].map(v=>v.toString(16).padStart(2,'0')).join('');
const digest=async v=>toHex(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(v)));
const safe=(a,b)=>{
  if(typeof a!=='string'||typeof b!=='string'||a.length!==b.length)return false;
  let d=0;for(let i=0;i<a.length;i++)d|=a.charCodeAt(i)^b.charCodeAt(i);
  return d===0;
};
const random=()=>{
  const raw=crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...raw)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
};
export const splitCredential=value=>{
  if(typeof value!=='string')throw new Error('Credencial inválida');
  const dot=value.indexOf('.');
  if(dot<0)throw new Error('Credencial inválida');
  const deviceId=value.slice(0,dot),secret=value.slice(dot+1);
  if(!DEVICE.test(deviceId)||!TOKEN.test(secret))throw new Error('Credencial inválida');
  return {deviceId,secret};
};
export const resourceFor=origin=>new URL(origin).origin;
export function authMetadata(origin){
  return {
    issuer:resourceFor(origin),
    authorization_endpoint:resourceFor(origin)+'/oauth/authorize',
    token_endpoint:resourceFor(origin)+'/oauth/token',
    response_types_supported:['code'],
    grant_types_supported:['authorization_code','refresh_token'],
    code_challenge_methods_supported:['S256'],
    token_endpoint_auth_methods_supported:['none'],
    client_id_metadata_document_supported:true,
    authorization_response_iss_parameter_supported:true,
    scopes_supported:[SCOPE],
  };
}
export function authorizationParams(params,origin){
  const get=k=>params.get(k)||'';
  const clientId=get('client_id'),redirectUri=get('redirect_uri'),
        challenge=get('code_challenge'),state=get('state'),resource=get('resource');
  if(get('response_type')!=='code'||clientId!==CLIENT_ID||redirectUri!==CALLBACK||
     get('code_challenge_method')!=='S256'||!PKCE.test(challenge)||
     !state||state.length>1024||resource!==resourceFor(origin)||
     get('scope')!==SCOPE){
    throw new Error('Solicitação OAuth incompatível');
  }
  return {clientId,redirectUri,challenge,state,resource,scope:SCOPE};
}
const escapeHtml=v=>String(v).replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;',
}[c]));
export function pairingPage(params,{error=''}={}){
  const fields={client_id:params.clientId,redirect_uri:params.redirectUri,
    response_type:'code',code_challenge:params.challenge,code_challenge_method:'S256',
    state:params.state,scope:params.scope,resource:params.resource};
  const hidden=Object.entries(fields).map(([k,v])=>
    `<input type="hidden" name="${escapeHtml(k)}" value="${escapeHtml(v)}">`).join('');
  return `<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Vincular NavixX</title>
<style>body{font:16px system-ui;background:#0b1120;color:#eef6ff;display:grid;place-items:center;min-height:95vh}
main{width:min(440px,90vw);background:#152238;border:1px solid #385475;padding:24px;border-radius:18px}
input{box-sizing:border-box;width:100%;font:inherit;padding:12px;margin:7px 0 14px;border-radius:8px}
button{background:#2878f0;color:white;border:0;border-radius:8px;padding:13px;width:100%;font-weight:bold}
small{color:#aac2e0}.error{color:#ffb1bc}</style>
<main><h1>NavixX Desktop</h1><p>Vincule somente o computador que você está autorizando.</p>
${error?`<p class="error">${escapeHtml(error)}</p>`:''}
<form method="POST" action="/oauth/authorize">${hidden}
<label>ID do computador<input name="device_id" required minlength="16" maxlength="128" autocomplete="off"></label>
<label>Código temporário de 6 números<input name="code" pattern="[0-9]{6}" maxlength="6" required inputmode="numeric" autocomplete="one-time-code"></label>
<button type="submit">Autorizar este computador no ChatGPT</button></form>
<p><small>O código aparece no painel do NavixX e expira em 2 minutos. Nenhuma chave OpenAI ou Cloudflare é necessária neste PC. Pare o acesso pelo próprio aplicativo.</small></p>
</main></html>`;
}
export function htmlResponse(html,status=200){return new Response(html,{status,headers:{
  'content-type':'text/html; charset=utf-8','cache-control':'no-store','x-frame-options':'DENY',
  'referrer-policy':'no-referrer',
  'content-security-policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
}});}
export function oauthRedirect(params,authorizationCode,origin){
  const url=new URL(params.redirectUri);
  url.searchParams.set('code',authorizationCode);
  url.searchParams.set('state',params.state);
  url.searchParams.set('iss',resourceFor(origin));
  return url.href;
}
export async function parseForm(request,maxBytes=8192){
  if(!request.headers.get('content-type')?.toLowerCase().startsWith('application/x-www-form-urlencoded')){
    throw new Error('Formato de formulário inválido');
  }
  if(Number(request.headers.get('content-length')||0)>maxBytes)throw new Error('Formulário excessivo');
  const body=await request.text();
  if(new TextEncoder().encode(body).length>maxBytes)throw new Error('Formulário excessivo');
  return new URLSearchParams(body);
}
export class DeviceOAuth {
  constructor(storage,pairing,{now=Date.now}={}){
    this.storage=storage;this.pairing=pairing;this.now=now;
  }
  async createCode({deviceId,code,clientId,redirectUri,challenge,resource}){
    if(!DEVICE.test(deviceId)||!CODE.test(code)||clientId!==CLIENT_ID||
       redirectUri!==CALLBACK||!PKCE.test(challenge))throw new Error('Solicitação inválida');
    const {ownerId}=await this.pairing.claimWithCode({deviceId,code});
    const raw=random(),value=deviceId+'.'+raw;
    await this.storage.put('oauth:code',{hash:await digest(raw),expiresAt:this.now()+90_000,
      clientId,redirectUri,challenge,resource,ownerId});
    return value;
  }
  async exchangeCode({code,clientId,redirectUri,verifier,resource}){
    const {deviceId,secret}=splitCredential(code);
    if(clientId!==CLIENT_ID||redirectUri!==CALLBACK||
       typeof verifier!=='string'||!(/^[A-Za-z0-9._~-]{43,128}$/).test(verifier)){
      throw new Error('Cliente ou PKCE inválido');
    }
    const candidate=await digest(secret);
    return this.storage.transaction(async txn=>{
      const entry=await txn.get('oauth:code'),device=await txn.get('device');
      if(!entry||!device?.ownerId||device.deviceId!==deviceId||entry.ownerId!==device.ownerId||
         entry.expiresAt<=this.now()||!safe(entry.hash,candidate)||
         entry.clientId!==clientId||entry.redirectUri!==redirectUri||entry.resource!==resource){
        throw new Error('Código inválido, expirado ou já utilizado');
      }
      const check=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier));
      const challenge=btoa(String.fromCharCode(...new Uint8Array(check)))
        .replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
      if(!safe(challenge,entry.challenge))throw new Error('PKCE inválido');
      await txn.delete('oauth:code');
      return this._issue(txn,device.ownerId,clientId,resource);
    });
  }
  async refresh({refreshToken,clientId,resource}){
    const {deviceId,secret}=splitCredential(refreshToken);
    const hash=await digest(secret);
    return this.storage.transaction(async txn=>{
      const entry=await txn.get('oauth:refresh'),device=await txn.get('device');
      if(!entry||!device?.ownerId||device.deviceId!==deviceId||!safe(entry.hash,hash)||
         entry.expiresAt<=this.now()||entry.ownerId!==device.ownerId||
         entry.clientId!==clientId||entry.resource!==resource||clientId!==CLIENT_ID){
        throw new Error('Atualização de sessão não autorizada');
      }
      await txn.delete('oauth:refresh');
      return this._issue(txn,device.ownerId,clientId,resource);
    });
  }
  async _issue(txn,ownerId,clientId,resource){
    const deviceId=(await txn.get('device'))?.deviceId;
    if(!DEVICE.test(deviceId))throw new Error('Dispositivo inválido');
    const access=random(),refresh=random();
    await txn.put('oauth:access',{hash:await digest(access),expiresAt:this.now()+3600000,
      ownerId,clientId,resource});
    await txn.put('oauth:refresh',{hash:await digest(refresh),expiresAt:this.now()+30*86400000,
      ownerId,clientId,resource});
    return {access_token:deviceId+'.'+access,refresh_token:deviceId+'.'+refresh,
      token_type:'Bearer',expires_in:3600,scope:SCOPE};
  }
  async verifyAccess(token,resource){
    const {deviceId,secret}=splitCredential(token);
    const current=await this.storage.get('oauth:access'),device=await this.storage.get('device');
    if(!current||!device?.ownerId||device.deviceId!==deviceId||!safe(current.hash,await digest(secret))||
       current.expiresAt<=this.now()||current.resource!==resource||
       current.ownerId!==device.ownerId){
      throw new Error('Token inválido ou revogado');
    }
    return {deviceId:device.deviceId,ownerId:device.ownerId};
  }
}
