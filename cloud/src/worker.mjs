import {DurableObject} from 'cloudflare:workers';
import {DurablePairing} from './durable-pairing.mjs';
import {PendingCalls,TOOL_SET} from './relay-protocol.mjs';
import {DeviceOAuth,authMetadata,authorizationParams,htmlResponse,oauthRedirect,
  pairingPage,parseForm,resourceFor,splitCredential,CLIENT_ID,CALLBACK,SCOPE} from './device-oauth.mjs';
import {handleMcp,validateToolArguments,authenticationRequired} from './mcp-http.mjs';

const DEVICE = /^[A-Za-z0-9_-]{16,128}$/;
const json = (body,status=200) => new Response(JSON.stringify(body),{
  status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'},
});
const scopedDevice = url => {
  const id=new URL(url).searchParams.get('device_id');
  if(!id || !DEVICE.test(id)) throw new Error('Dispositivo inválido');
  return id;
};
const stubFor=(env,deviceId)=>env.DEVICE_RELAY.get(env.DEVICE_RELAY.idFromName('device-v1:'+deviceId));
const secretFrom=req=>req.headers.get('x-navix-agent-token')||'';
const publicControlEnabled=env=>env.NAVIX_PUBLIC_CONTROL==='enabled';
const deviceControlAllowed=(env,deviceId)=>publicControlEnabled(env)&&
  (!env.NAVIX_TEST_DEVICE_ID||env.NAVIX_TEST_DEVICE_ID===deviceId);

async function boundedJson(req,maxBytes=8192) {
  const reader=req.body?.getReader();
  if(!reader) throw new Error('Corpo JSON obrigatório');
  const chunks=[];let size=0;
  try {
    while(true){
      const {done,value}=await reader.read();
      if(done)break;
      size+=value.byteLength;
      if(size>maxBytes)throw new Error('Mensagem grande demais');
      chunks.push(value);
    }
  } catch(error){await reader.cancel().catch(()=>{});throw error;}
  const bytes=new Uint8Array(size);let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
  const data=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  if(!data || typeof data!=='object'||Array.isArray(data))throw new Error('JSON inválido');
  return data;
}

const challengeFor=request=>
  'Bearer resource_metadata="'+new URL(request.url).origin+'/.well-known/oauth-protected-resource", scope="'+SCOPE+'"';

async function authorizedDevice(request,env,deviceId=''){
  const match=/^Bearer ([A-Za-z0-9_.-]+)$/.exec(request.headers.get('authorization')||'');
  if(!match)throw new Error('Bearer ausente');
  const parsed=splitCredential(match[1]);
  if(deviceId&&deviceId!==parsed.deviceId)throw new Error('Token de outro computador');
  const result=await stubFor(env,parsed.deviceId).fetch(new Request('https://device.local/oauth/verify',{
    method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({token:match[1],resource:resourceFor(request.url)}),
  }));
  if(!result.ok)throw new Error('Credencial não autorizada');
  const response=await result.json();
  if(!response.ownerId)throw new Error('Titular desconhecido');
  return {deviceId:parsed.deviceId,ownerId:response.ownerId};
}

export default {
  async fetch(request,env) {
    const url=new URL(request.url);
    if(url.pathname==='/healthz' && request.method==='GET'){
      return json({service:'navixx-cloud',version:'0.3.0-alpha.8',
        public_tools_enabled:publicControlEnabled(env),
        restricted_to_canary:Boolean(env.NAVIX_TEST_DEVICE_ID)});
    }
    if(url.pathname==='/.well-known/oauth-protected-resource' && request.method==='GET'){
      return json({resource:url.origin,authorization_servers:[url.origin],
        scopes_supported:[SCOPE],bearer_methods_supported:['header'],
        resource_documentation:'https://github.com/willsonAlphamna/Navix-Free'});
    }
    if(url.pathname==='/.well-known/oauth-authorization-server' && request.method==='GET'){
      return json(authMetadata(url.origin));
    }
    if(url.pathname==='/oauth/authorize'){
      if(!['GET','POST'].includes(request.method))return json({error:'Método inválido'},405);
      let params,body;
      try {
        body=request.method==='POST'?await parseForm(request):url.searchParams;
        params=authorizationParams(body,url.origin);
      } catch {return htmlResponse('<h1>Solicitação OAuth inválida</h1>',400);}
      if(request.method==='GET')return htmlResponse(pairingPage(params));
      const deviceId=body.get('device_id'),code=body.get('code');
      if(!deviceId||!DEVICE.test(deviceId)||!/^\d{6}$/.test(code||'')){
        return htmlResponse(pairingPage(params,{error:'Confira o ID e o código do NavixX.'}),400);
      }
      const response=await stubFor(env,deviceId).fetch(new Request('https://device.local/oauth/code',{
        method:'POST',headers:{'content-type':'application/json'},
        body:JSON.stringify({...params,deviceId,code}),
      }));
      if(!response.ok)return htmlResponse(pairingPage(params,{
        error:'Código expirado, incorreto ou vinculação indisponível. Gere outro no PC.'}),403);
      const {authorizationCode}=await response.json();
      return new Response(null,{status:302,headers:{Location:oauthRedirect(params,authorizationCode,url.origin),
        'cache-control':'no-store','referrer-policy':'no-referrer'}});
    }
    if(url.pathname==='/oauth/token'){
      if(request.method!=='POST')return json({error:'invalid_request'},405);
      try {
        const params=await parseForm(request);
        const grant=params.get('grant_type'),clientId=params.get('client_id');
        const resource=params.get('resource')||url.origin;
        if(clientId!==CLIENT_ID||resource!==url.origin)throw new Error('Cliente não autorizado');
        const credential=grant==='authorization_code'?params.get('code'):
          grant==='refresh_token'?params.get('refresh_token'):null;
        const {deviceId}=splitCredential(credential);
        const path=grant==='authorization_code'?'/oauth/token':'/oauth/refresh';
        const payload=grant==='authorization_code'?{
          code:credential,clientId,redirectUri:params.get('redirect_uri'),
          verifier:params.get('code_verifier'),resource,
        }:{refreshToken:credential,clientId,resource};
        const response=await stubFor(env,deviceId).fetch(new Request('https://device.local'+path,{
          method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload),
        }));
        if(!response.ok)throw new Error('Grant inválido');
        return json(await response.json());
      } catch{return json({error:'invalid_grant'},400);}
    }
    if(url.pathname==='/mcp'){
      // OAuth must be discoverable even while remote control is disabled.
      // A connection check can then tell the user the real cause of a block.
      let identity;
      try{identity=await authorizedDevice(request,env);}
      catch {
        // Mixed OAuth: expose the MCP catalog without credentials so ChatGPT
        // can choose the NavixX Cloud tool, and let tool-level OAuth prompt
        // the user. NEVER call a device or return private status anonymously.
        return handleMcp(request,{allowRemoteTools:publicControlEnabled(env),
          execute:async ()=>authenticationRequired(challengeFor(request))});
      }
      const canControl=deviceControlAllowed(env,identity.deviceId);
      return handleMcp(request,{allowRemoteTools:canControl,execute:async (tool,args)=>{
        const stub=stubFor(env,identity.deviceId);
        if(tool==='navixx_cloud_connection_status'){
          const response=await stub.fetch(new Request('https://device.local/status',{
            headers:{'x-navix-owner':identity.ownerId},
          }));
          // Never confuse the transport handshake with a successful PC command.
          const online=response.ok&&Boolean((await response.json()).connected);
          return {plugin:'navixx-cloud',authorized:true,paired:true,
            cloud_control_enabled:canControl,windows_channel_active:online,
            windows_command_verified:false,
            next_step:!canControl?'Controle remoto ainda não autorizado neste gateway/dispositivo.':
              !online?'Abra o NavixX Desktop Cloud e autorize a sessão local; o canal remoto precisa conectar.':
              'Canal ativo. Para comprovar execução real no Windows, use a ferramenta status DESTE plugin.'};
        }
        if(!canControl)throw new Error('Controle remoto não autorizado neste dispositivo');
        const response=await stub.fetch(new Request('https://device.local/execute',{
          method:'POST',headers:{'content-type':'application/json','x-navix-owner':identity.ownerId},
          body:JSON.stringify({tool,args}),
        }));
        if(!response.ok){
          const failure=await response.json().catch(()=>({}));
          return {isError:true,content:[{type:'text',text:'NavixX Cloud: o Windows não respondeu à ferramenta ('+
            String(failure.category||'indisponível')+'). Use navixx_cloud_connection_status.'}]};
        }
        const body=await response.json();
        return body.result;
      }});
    }
    const route=url.pathname;
    if(!['/api/pair/start','/api/pair/renew','/api/pair/state','/api/pair/approve','/api/pair/revoke',
         '/api/device/connect','/api/device/status','/api/device/execute'].includes(route)){
      return json({error:'Não encontrado'},404);
    }
    let deviceId,payload;
    try {
      if(route==='/api/pair/start'||route==='/api/pair/renew'||route==='/api/pair/approve'||route==='/api/pair/revoke'){
        if(request.method!=='POST')return json({error:'Método inválido'},405);
        payload=await boundedJson(request);
        deviceId=payload.device_id;
        if(typeof deviceId!=='string'||!DEVICE.test(deviceId))throw new Error('ID inválido');
      } else {
        deviceId=scopedDevice(request.url);
      }
    } catch{return json({error:'Requisição inválida'},400);}
    const stub=stubFor(env,deviceId);

    if(route==='/api/pair/start'){
      if(!env.PAIR_RATE_LIMITER)return json({error:'Cadastro temporariamente indisponível'},503);
      const ip=request.headers.get('cf-connecting-ip')||'unknown';
      const {success}=await env.PAIR_RATE_LIMITER.limit({key:'pair-start:'+ip});
      if(!success)return json({error:'Limite de cadastros excedido'},429);
      return stub.fetch(new Request('https://device.local/pair/start',{method:'POST',
        headers:{'content-type':'application/json'},
        body:JSON.stringify({deviceId,code:payload.code,agentSecret:payload.agent_secret}),
      }));
    }
    if(route==='/api/pair/renew'){
      return stub.fetch(new Request('https://device.local/pair/renew',{method:'POST',
        headers:{'content-type':'application/json','x-navix-agent-token':secretFrom(request)},
        body:JSON.stringify({deviceId,code:payload.code}),
      }));
    }
    if(route==='/api/pair/state'){
      if(request.method!=='GET')return json({error:'Método inválido'},405);
      return stub.fetch(new Request('https://device.local/pair/state',{
        headers:{'x-navix-agent-token':secretFrom(request)},
      }));
    }
    if(route==='/api/device/connect'){
      if(request.method!=='GET')return json({error:'Método inválido'},405);
      if(request.headers.get('upgrade')?.toLowerCase()!=='websocket'){
        return json({error:'WebSocket obrigatório'},426);
      }
      return stub.fetch(new Request('https://device.local/connect',{
        headers:{Upgrade:'websocket','x-navix-agent-token':secretFrom(request)},
      }));
    }
    let owner;
    try {owner=(await authorizedDevice(request,env,deviceId)).ownerId;}
    catch{return json({error:'Não autorizado'},401);}

    if(route==='/api/pair/approve'||route==='/api/pair/revoke'){
      return stub.fetch(new Request('https://device.local/pair/'+
        (route.endsWith('approve')?'approve':'revoke'),{
        method:'POST',headers:{'content-type':'application/json','x-navix-owner':owner},
        body:JSON.stringify({code:payload.code}),
      }));
    }
    if(route==='/api/device/status'){
      if(request.method!=='GET')return json({error:'Método inválido'},405);
      return stub.fetch(new Request('https://device.local/status',{
        headers:{'x-navix-owner':owner},
      }));
    }
    if(request.method!=='POST')return json({error:'Método inválido'},405);
    if(!deviceControlAllowed(env,deviceId))return json({error:'Controle remoto indisponível para este dispositivo'},503);
    try{payload=await boundedJson(request,8*1024*1024);
      validateToolArguments(payload.tool,payload.args||{});
    }catch{return json({error:'JSON ou ferramenta inválida'},400);}
    return stub.fetch(new Request('https://device.local/execute',{
      method:'POST',headers:{'content-type':'application/json','x-navix-owner':owner},
      body:JSON.stringify(payload),
    }));
  },
};

export class DeviceRelay extends DurableObject {
  constructor(ctx,env){
    super(ctx,env);
    // Cloudflare may hibernate a Durable Object while its WebSocket stays
    // connected. Instance fields (including PendingCalls) do not survive.
    // Reattach the surviving socket before the next MCP command arrives.
    const sockets=ctx.getWebSockets();
    if(sockets.length){
      this.connectSocket(sockets[0]);
      for(const stale of sockets.slice(1))stale.close(1000,'Sessão substituída');
    }
  }
  get pairing(){return new DurablePairing(this.ctx.storage);}
  get oauth(){return new DeviceOAuth(this.ctx.storage,this.pairing);}
  connectSocket(server){
    this.calls?.close();
    this.liveSocket=server;
    this.calls=new PendingCalls({send:frame=>server.send(frame)});
  }
  disconnectSocket(ws){
    if(this.liveSocket===ws){
      this.calls?.close();
      this.calls=null;
      this.liveSocket=null;
    }
  }
  async fetch(request){
    const url=new URL(request.url),route=url.pathname;
    const owner=request.headers.get('x-navix-owner')||'';
    if(route==='/pair/start'){
      try {
        const data=await request.json();
        return json(await this.pairing.start(data),201);
      } catch{return json({error:'Pareamento indisponível'},409);}
    }
    if(route==='/pair/renew'){
      try {
        const body=await request.json();
        return json(await this.pairing.renewCode({...body,agentSecret:secretFrom(request)}));
      } catch{return json({error:'Código não renovado'},403);}
    }
    if(route==='/oauth/code'){
      try {
        const body=await request.json();
        return json({authorizationCode:await this.oauth.createCode(body)});
      }catch{return json({error:'Não foi possível vincular'},403);}
    }
    if(route==='/oauth/token'||route==='/oauth/refresh'){
      try {
        const body=await request.json();
        return json(route==='/oauth/token'?await this.oauth.exchangeCode(body):
          await this.oauth.refresh(body));
      }catch{return json({error:'invalid_grant'},400);}
    }
    if(route==='/oauth/verify'){
      try {
        const {token,resource}=await request.json();
        return json(await this.oauth.verifyAccess(token,resource));
      }catch{return json({error:'Não autorizado'},401);}
    }
    if(route==='/pair/state'){
      // The bearer token is opaque and local to this Windows installation.
      const agentSecret=secretFrom(request);
      const deviceId=(await this.ctx.storage.get('device'))?.deviceId||'';
      const state=await this.pairing.status({deviceId,agentSecret});
      return json(state);
    }
    if(route==='/pair/approve'){
      try{
        const data=await request.json();
        const deviceId=(await this.ctx.storage.get('device'))?.deviceId||'';
        return json(await this.pairing.approve({ownerId:owner,deviceId,code:data.code}));
      }catch{return json({error:'Não foi possível aprovar'},400);}
    }
    if(route==='/pair/revoke'){
      if(!await this.pairing.revoke({ownerId:owner}))return json({error:'Não autorizado'},403);
      for(const ws of this.ctx.getWebSockets())ws.close(1000,'Permissão revogada');
      this.calls?.close();this.calls=null;this.liveSocket=null;
      return json({revoked:true});
    }
    if(route==='/status'||route==='/execute'){
      if(!await this.pairing.verifyOwner(owner))return json({error:'Não autorizado'},403);
      if(route==='/status')return json({connected:this.ctx.getWebSockets().length>0});
      if(request.method!=='POST')return json({error:'Método inválido'},405);
      let command;
      try{command=await request.json();}catch{return json({error:'JSON inválido'},400);}
      if(!command||!TOOL_SET.has(command.tool)||!this.calls){
        return json({error:'Dispositivo indisponível ou ferramenta bloqueada'},503);
      }
      try{
        validateToolArguments(command.tool,command.args||{});
        return json({result:await this.calls.call(command.tool,command.args||{},command.tool==='status'?8000:30_000)});
      }
      catch(error){
        const message=String(error?.message||'');
        const category=message.includes('Tempo limite')?'timeout':
          message.includes('Falha no dispositivo')?'device_reply_error':
          message.includes('Falha no envio')?'socket_send_failed':
          message.includes('Dispositivo desconectado')?'device_disconnected':'relay_error';
        return json({error:'Dispositivo sem resposta',category},504);
      }
    }
    if(route==='/connect'){
      if(request.headers.get('upgrade')?.toLowerCase()!=='websocket')return json({error:'Upgrade obrigatório'},426);
      if(!await this.pairing.verifyAgent(secretFrom(request)))return json({error:'Agente não vinculado'},403);
      for(const ws of this.ctx.getWebSockets())ws.close(1000,'Sessão substituída');
      const pair=new WebSocketPair(),client=pair[0],server=pair[1];
      this.ctx.acceptWebSocket(server);
      this.connectSocket(server);
      return new Response(null,{status:101,webSocket:client});
    }
    return json({error:'Rota interna inválida'},404);
  }
  async webSocketMessage(ws,data){
    if(ws!==this.liveSocket||!this.calls)return;
    try{this.calls.accept(data);}catch{
      ws.close(1008,'Resposta inválida');this.disconnectSocket(ws);
    }
  }
  async webSocketClose(ws){this.disconnectSocket(ws);}
  async webSocketError(ws){this.disconnectSocket(ws);}
}
