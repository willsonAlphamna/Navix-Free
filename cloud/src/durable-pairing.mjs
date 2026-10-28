/**
 * Durable per-device pairing. The server never stores a plaintext agent secret
 * or 6-digit verification code. One Durable Object must own each device ID.
 */
const DEVICE = /^[A-Za-z0-9_-]{16,128}$/;
const SECRET = /^[A-Za-z0-9_-]{43,128}$/;
const CODE = /^\d{6}$/;
const encoder = new TextEncoder();
const toHex = buffer => [...new Uint8Array(buffer)].map(v=>v.toString(16).padStart(2,'0')).join('');
const digest = async value => toHex(await crypto.subtle.digest('SHA-256',encoder.encode(value)));
const randomSalt = () => {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return toHex(bytes);
};
const codeDigest=(salt,code)=>digest(salt+':'+code);
const safe = (a,b) => {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let mismatch=0;
  for(let i=0;i<a.length;i++) mismatch|=a.charCodeAt(i)^b.charCodeAt(i);
  return mismatch===0;
};
export class DurablePairing {
  constructor(storage,{now=Date.now,ttlMs=120_000,maxAttempts=5}={}) {
    this.storage=storage;this.now=now;this.ttlMs=ttlMs;this.maxAttempts=maxAttempts;
  }
  async start({deviceId,code,agentSecret}) {
    if (!DEVICE.test(deviceId) || typeof agentSecret !== 'string' || !SECRET.test(agentSecret) ||
        typeof code !== 'string' || !CODE.test(code)) throw new Error('Pedido de pareamento inválido');
    const salt=randomSalt(),codeHash=await codeDigest(salt,code),tokenHash=await digest(agentSecret);
    return this.storage.transaction(async txn=>{
      const previous=await txn.get('device');
      if (previous?.ownerId) throw new Error('Dispositivo já pertence a uma conta');
      if (previous?.expiresAt > this.now()) throw new Error('Pareamento já aguardando aprovação');
      const expiresAt=this.now()+this.ttlMs;
      await txn.put('device',{deviceId,expiresAt,salt,codeHash,tokenHash,attempts:0});
      return {deviceId,expiresAt};
    });
  }
  async approve({ownerId,deviceId,code}) {
    if (typeof ownerId !== 'string' || ownerId.length<1 || ownerId.length>256 ||
        !DEVICE.test(deviceId) || typeof code !== 'string' || !CODE.test(code)) {
      throw new Error('Confirmação inválida');
    }
    return this.storage.transaction(async txn=>{
      const entry=await txn.get('device');
      if (!entry || entry.ownerId || entry.deviceId!==deviceId) throw new Error('Pareamento não encontrado');
      if (entry.expiresAt <= this.now()) {
        await txn.delete('device');throw new Error('Código expirado');
      }
      if (entry.attempts>=this.maxAttempts) throw new Error('Tentativas excedidas');
      const actual=await codeDigest(entry.salt,code);
      entry.attempts++;
      if (!safe(actual,entry.codeHash)) {
        if (entry.attempts>=this.maxAttempts) await txn.delete('device');
        else await txn.put('device',entry);
        throw new Error('Código incorreto');
      }
      await txn.put('device',{deviceId,ownerId,tokenHash:entry.tokenHash,approvedAt:this.now()});
      return {deviceId,linked:true};
    });
  }
  async verifyAgent(agentSecret) {
    if (typeof agentSecret !== 'string' || !SECRET.test(agentSecret)) return false;
    const state=await this.storage.get('device');
    if (!state?.ownerId) return false;
    return safe(await digest(agentSecret),state.tokenHash);
  }
  async verifyOwner(ownerId) {
    const state=await this.storage.get('device');
    return typeof ownerId==='string' && !!state?.ownerId && safe(ownerId,state.ownerId);
  }
  async status({deviceId,agentSecret}) {
    if (!DEVICE.test(deviceId) || typeof agentSecret!=='string' || !SECRET.test(agentSecret)) return {linked:false};
    const state=await this.storage.get('device');
    if (!state || state.deviceId!==deviceId || !safe(await digest(agentSecret),state.tokenHash)) {
      return {linked:false};
    }
    return {linked:!!state.ownerId};
  }
  async revoke({ownerId}) {
    return this.storage.transaction(async txn=>{
      const state=await txn.get('device');
      if (!state?.ownerId || !safe(ownerId,state.ownerId)) return false;
      await txn.delete('device');
      return true;
    });
  }
}
