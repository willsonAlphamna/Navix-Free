/** The relay never infers permissions from a remote caller's arguments. */
export const TOOL_NAMES = Object.freeze([
  'browser_back','browser_click','browser_close_tab','browser_download','browser_fill',
  'browser_forward','browser_hover','browser_navigate','browser_open','browser_press',
  'browser_read','browser_reload','browser_screenshot','browser_scroll','browser_select',
  'browser_snapshot','browser_start','browser_tabs','browser_upload','browser_wait',
  'command_exec','command_run','desktop_click','desktop_drag','desktop_hotkey','desktop_key',
  'desktop_move','desktop_position','desktop_screen_info','desktop_screenshot','desktop_scroll',
  'desktop_type','files_copy','files_delete','files_download','files_edit','files_list',
  'files_mkdir','files_move','files_read','files_read_binary','files_write','files_write_binary',
  'status',
]);
export const TOOL_SET = new Set(TOOL_NAMES);
const PERMISSIONS = Object.freeze({browser:'browser',command:'commands',desktop:'desktop',files:'files'});
const ID_RE = /^[0-9a-f-]{36}$/i;
const MAX_REQUEST_BYTES = 8 * 1024 * 1024;
const MAX_RESPONSE_BYTES = 12 * 1024 * 1024;
const MAX_WAIT_MS = 60_000;

export function requiredPermission(tool) {
  if (!TOOL_SET.has(tool)) throw new Error('Ferramenta desconhecida');
  if (tool === 'status') return null;
  return PERMISSIONS[tool.split('_')[0]];
}

export function makeCall({tool, args={}, id=crypto.randomUUID(), deadline=Date.now()+30_000}) {
  requiredPermission(tool);
  if (!ID_RE.test(id)) throw new Error('ID de chamada inválido');
  if (!args || typeof args !== 'object' || Array.isArray(args)) throw new Error('Argumentos inválidos');
  if (!Number.isFinite(deadline) || deadline <= Date.now() || deadline > Date.now()+MAX_WAIT_MS) {
    throw new Error('Prazo de chamada inválido');
  }
  const payload = {kind:'call',id,tool,args,deadline};
  if (new TextEncoder().encode(JSON.stringify(payload)).length > MAX_REQUEST_BYTES) throw new Error('Comando muito grande');
  return payload;
}

export function parseReply(frame) {
  if (typeof frame !== 'string' || new TextEncoder().encode(frame).length > MAX_RESPONSE_BYTES) {
    throw new Error('Resposta inválida ou excessiva');
  }
  let value;
  try { value=JSON.parse(frame); } catch { throw new Error('JSON inválido'); }
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      value.kind !== 'result' || !ID_RE.test(value.id) ||
      typeof value.ok !== 'boolean') {
    throw new Error('Formato de resposta inválido');
  }
  if (value.ok && !Object.hasOwn(value,'result')) throw new Error('Resultado ausente');
  if (!value.ok && (typeof value.error !== 'string' || value.error.length > 1000)) {
    throw new Error('Erro remoto inválido');
  }
  return value;
}

/** One live connection per device; disconnect rejects all pending requests. */
export class PendingCalls {
  constructor({send, now=Date.now, maxPending=1}={}) {
    if (typeof send !== 'function') throw new TypeError('send obrigatório');
    this.send=send;
    this.now=now;
    this.maxPending=maxPending;
    this.pending=new Map();
    this.closed=false;
  }
  async call(tool,args={},timeoutMs=30_000) {
    if (this.closed) throw new Error('Dispositivo desconectado');
    if (this.pending.size >= this.maxPending) throw new Error('Dispositivo ocupado');
    if (!Number.isInteger(timeoutMs) || timeoutMs<100 || timeoutMs>MAX_WAIT_MS) {
      throw new Error('Tempo excede limites');
    }
    const id=crypto.randomUUID();
    const payload=makeCall({tool,args,id,deadline:this.now()+timeoutMs});
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{
        this.pending.delete(id);
        reject(new Error('Tempo limite da execução remota'));
      },timeoutMs);
      this.pending.set(id,{resolve,reject,timer});
      try { this.send(JSON.stringify(payload)); }
      catch { clearTimeout(timer); this.pending.delete(id); reject(new Error('Falha no envio')); }
    });
  }
  accept(frame) {
    const reply=parseReply(frame);
    const awaiting=this.pending.get(reply.id);
    if (!awaiting) return false; // A stale reply cannot satisfy another invocation.
    this.pending.delete(reply.id);
    clearTimeout(awaiting.timer);
    if (reply.ok) awaiting.resolve(reply.result);
    else awaiting.reject(new Error('Falha no dispositivo: '+reply.error));
    return true;
  }
  close() {
    this.closed=true;
    for(const item of this.pending.values()) {
      clearTimeout(item.timer);
      item.reject(new Error('Dispositivo desconectado'));
    }
    this.pending.clear();
  }
}
