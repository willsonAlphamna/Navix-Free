import {DurableObject} from 'cloudflare:workers';
import {authenticate, configFromEnv} from './auth.mjs';
import {PendingCalls} from './relay-protocol.mjs';

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
    if (!['/api/device/connect','/api/device/status','/api/device/execute'].includes(url.pathname)) {
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
    if (url.pathname === '/api/device/status') {
      if (request.method !== 'GET') return json({error:'Método inválido'},405);
      return stub.fetch('https://device.local/status');
    }
    if (request.method !== 'POST') return json({error:'Método inválido'},405);
    let command;
    try {
      if (Number(request.headers.get('content-length') || '0') > 16_384) throw new Error('Excessivo');
      command=await request.json();
    } catch { return json({error:'JSON inválido'},400); }
    // Until real device pairing, ONLY status (no mouse, file or command execution).
    if (!command || command.tool !== 'status' || Object.keys(command).some(k=>!['tool','args'].includes(k))) {
      return json({error:'Comandos ainda não habilitados'},503);
    }
    return stub.fetch(new Request('https://device.local/execute',{
      method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(command),
    }));
  },
};

export class DeviceRelay extends DurableObject {
  connectSocket(server) {
    if (this.calls) this.calls.close();
    this.liveSocket=server;
    this.calls=new PendingCalls({send: frame => server.send(frame)});
  }
  disconnectSocket(ws) {
    if (this.liveSocket === ws) {
      this.calls?.close();
      this.calls=null;
      this.liveSocket=null;
    }
  }
  async fetch(request) {
    const url=new URL(request.url);
    if (url.pathname === '/status') {
      return json({connected:this.ctx.getWebSockets().length > 0});
    }
    if (url.pathname === '/execute') {
      if (request.method !== 'POST') return json({error:'Método inválido'},405);
      let command;
      try {command=await request.json();} catch {return json({error:'JSON inválido'},400);}
      if (!command || command.tool !== 'status' || !this.calls) {
        return json({error:'Dispositivo indisponível ou ferramenta bloqueada'},503);
      }
      try {
        const result=await this.calls.call('status',command.args||{},15_000);
        return json({result});
      } catch {
        return json({error:'Dispositivo sem resposta'},504);
      }
    }
    if (url.pathname !== '/connect' || request.headers.get('upgrade')?.toLowerCase() !== 'websocket') {
      return json({error:'Rota interna inválida'},404);
    }
    for(const socket of this.ctx.getWebSockets()) socket.close(1000,'Sessão substituída');
    const pair=new WebSocketPair();
    const client=pair[0], server=pair[1];
    this.ctx.acceptWebSocket(server);
    this.connectSocket(server);
    return new Response(null,{status:101,webSocket:client});
  }
  async webSocketMessage(ws,data) {
    if (ws !== this.liveSocket || !this.calls) return;
    try {this.calls.accept(data);}
    catch {ws.close(1008,'Resposta inválida');this.disconnectSocket(ws);}
  }
  async webSocketClose(ws) {this.disconnectSocket(ws);}
  async webSocketError(ws) {this.disconnectSocket(ws);}
}
