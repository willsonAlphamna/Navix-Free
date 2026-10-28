import {DurableObject} from 'cloudflare:workers';
import {authenticate, configFromEnv} from './auth.mjs';

const DEVICE = /^[A-Za-z0-9_-]{8,128}$/;
const json = (body, status=200) => new Response(JSON.stringify(body), {
  status, headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'},
});
const boundedDeviceId = url => {
  const id = new URL(url).searchParams.get('device_id');
  if (!id || !DEVICE.test(id)) throw new Error('Identificador de dispositivo inválido.');
  return id;
};
const namespaceName = (ownerId, deviceId) => JSON.stringify([ownerId, deviceId]);

export default {
  async fetch(request, env) {
    const url=new URL(request.url);
    if (url.pathname === '/healthz' && request.method === 'GET') {
      return json({service:'navixx-cloud',version:'0.3.0-alpha.1',public_tools_enabled:false});
    }
    if (url.pathname === '/mcp') {
      // Fail closed until the complete authenticated MCP/OAuth flow is implemented.
      return json({error:'MCP público ainda não habilitado'},503);
    }
    if (url.pathname !== '/api/device/connect' && url.pathname !== '/api/device/status') {
      return json({error:'Não encontrado'},404);
    }
    try {
      // Missing OIDC settings are deployment errors, not anonymous fallback.
      configFromEnv(env);
    } catch {
      return json({error:'Identidade do serviço não configurada'},503);
    }
    let identity, deviceId;
    try {
      const scope=url.pathname.endsWith('/connect') ? 'navix:agent' : 'navix:control';
      identity=await authenticate(request,env,scope);
      deviceId=boundedDeviceId(request.url);
    } catch {
      return json({error:'Não autorizado'},401);
    }
    const name=namespaceName(identity.ownerId,deviceId);
    const stub=env.DEVICE_RELAY.get(env.DEVICE_RELAY.idFromName(name));
    if (url.pathname === '/api/device/connect') {
      if (request.headers.get('upgrade')?.toLowerCase() !== 'websocket') {
        return json({error:'WebSocket obrigatório'},426);
      }
      return stub.fetch(new Request('https://device.local/connect',{headers:{Upgrade:'websocket'}}));
    }
    if (request.method !== 'GET') return json({error:'Método inválido'},405);
    return stub.fetch('https://device.local/status');
  },
};

export class DeviceRelay extends DurableObject {
  async fetch(request) {
    const url=new URL(request.url);
    if (url.pathname === '/status') {
      return json({connected:this.ctx.getWebSockets().length > 0});
    }
    if (url.pathname !== '/connect' || request.headers.get('upgrade')?.toLowerCase() !== 'websocket') {
      return json({error:'Rota interna inválida'},404);
    }
    // One live agent per scoped (authenticated owner, device).
    for(const socket of this.ctx.getWebSockets()) socket.close(1000,'Sessão substituída');
    const pair=new WebSocketPair();
    const client=pair[0], server=pair[1];
    this.ctx.acceptWebSocket(server);
    return new Response(null,{status:101,webSocket:client});
  }
  async webSocketMessage(ws,data) {
    // No commands are accepted while the public command protocol is disabled.
    ws.send(JSON.stringify({kind:'not_ready',message:'Protocolo de controle ainda não publicado'}));
  }
}
