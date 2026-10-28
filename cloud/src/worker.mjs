import {DurableObject} from 'cloudflare:workers';
import {authenticate, configFromEnv} from './auth.mjs';
import {DurablePairing} from './durable-pairing.mjs';
import {PendingCalls} from './relay-protocol.mjs';
import {protectedResourceMetadata,oauthChallenge} from './oauth-resource.mjs';

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

async function boundedJson(req) {
  const reader=req.body?.getReader();
  if(!reader) throw new Error('Corpo JSON obrigatório');
  const chunks=[];let size=0;
  try {
    while(true){
      const {done,value}=await reader.read();
      if(done)break;
      size+=value.byteLength;
      if(size>8192)throw new Error('Mensagem grande demais');
      chunks.push(value);
    }
  } catch(error){await reader.cancel().catch(()=>{});throw error;}
  const bytes=new Uint8Array(size);let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
  const data=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  if(!data || typeof data!=='object'||Array.isArray(data))throw new Error('JSON inválido');
  return data;
}

export default {
  async fetch(request,env) {
    const url=new URL(request.url);
    if(url.pathname==='/healthz' && request.method==='GET'){
      return json({service:'navixx-cloud',version:'0.3.0-alpha.2',public_tools_enabled:false});
    }
    if(url.pathname==='/.well-known/oauth-protected-resource' && request.method==='GET'){
      try{return json(protectedResourceMetadata(env,request.url));}
      catch{return json({error:'Identidade não configurada'},503);}
    }
    if(url.pathname==='/mcp'){
      // No public access until OAuth/OIDC + Windows consent + cross-user e2e tests.
      try{configFromEnv(env);}catch{return json({error:'Identidade não configurada'},503);}
      try{await authenticate(request,env,'navix:control');}
      catch {
        return new Response(JSON.stringify({error:'Não autorizado'}),{status:401,headers:{
          'content-type':'application/json','cache-control':'no-store',
          'www-authenticate':oauthChallenge(env,request.url),
        }});
      }
      return json({error:'MCP público ainda não habilitado'},503);
    }
    const route=url.pathname;
    if(!['/api/pair/start','/api/pair/state','/api/pair/approve','/api/pair/revoke',
         '/api/device/connect','/api/device/status','/api/device/execute'].includes(route)){
      return json({error:'Não encontrado'},404);
    }
    let deviceId,payload;
    try {
      if(route==='/api/pair/start'||route==='/api/pair/approve'||route==='/api/pair/revoke'){
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
      return stub.fetch(new Request('https://device.local/pair/start',{method:'POST',
        headers:{'content-type':'application/json'},
        body:JSON.stringify({deviceId,code:payload.code,agentSecret:payload.agent_secret}),
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
    // From here only owner-verified OAuth requests (no shared master API key).
    try {configFromEnv(env);} catch {return json({error:'Identidade não configurada'},503);}
    let owner;
    try {owner=(await authenticate(request,env,'navix:control')).ownerId;}
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
    try{payload=await boundedJson(request);}catch{return json({error:'JSON inválido'},400);}
    // Status is the only permitted call until the MCP protocol and consent UI ship.
    if(payload.tool!=='status' || Object.keys(payload).some(k=>!['tool','args'].includes(k))){
      return json({error:'Comandos ainda não habilitados'},503);
    }
    return stub.fetch(new Request('https://device.local/execute',{
      method:'POST',headers:{'content-type':'application/json','x-navix-owner':owner},
      body:JSON.stringify(payload),
    }));
  },
};

export class DeviceRelay extends DurableObject {
  get pairing(){return new DurablePairing(this.ctx.storage);}
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
      if(command?.tool!=='status'||!this.calls){
        return json({error:'Dispositivo indisponível ou ferramenta bloqueada'},503);
      }
      try{return json({result:await this.calls.call('status',command.args||{},15_000)});}
      catch{return json({error:'Dispositivo sem resposta'},504);}
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
