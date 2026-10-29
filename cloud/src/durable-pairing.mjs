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
    const outcome=await this.storage.transaction(async txn=>{
      const entry=await txn.get('device');
      if (!entry || entry.ownerId || entry.deviceId!==deviceId) throw new Error('Pareamento não encontrado');
      if (entry.expiresAt <= this.now()) {
        await txn.delete('device');return {error:'Código expirado'};
      }
      if (entry.attempts>=this.maxAttempts) return {error:'Tentativas excedidas'};
      const actual=await codeDigest(entry.salt,code);
      entry.attempts++;
      if (!safe(actual,entry.codeHash)) {
        if (entry.attempts>=this.maxAttempts) await txn.delete('device');
        else await txn.put('device',entry);
        return {error:'Código incorreto'};
      }
      await txn.put('device',{deviceId,ownerId,tokenHash:entry.tokenHash,approvedAt:this.now()});
      return {deviceId,linked:true};
    });
    if (outcome.error) throw new Error(outcome.error);
    return outcome;
  }
  /** Read-only proof that a code is still valid. Never claims ownership or
   * issues an OAuth grant. Wrong guesses consume the same five-try budget.
   */
  async checkCode({deviceId,code}) {
    if (typeof deviceId!=='string'||!DEVICE.test(deviceId)||
        typeof code!=='string'||!CODE.test(code)) return false;
    return this.storage.transaction(async txn=>{
      const state=await txn.get('device');
      if(!state||state.deviceId!==deviceId)return false;
      const pending=state.ownerId?state.oauthChallenge:state;
      if(!pending||pending.expiresAt<=this.now()||
         pending.attempts>=this.maxAttempts)return false;
      const valid=safe(await codeDigest(pending.salt,code),pending.codeHash);
      if(valid)return true;
      pending.attempts++;
      if(pending.attempts>=this.maxAttempts){
        if(state.ownerId){delete state.oauthChallenge;await txn.put('device',state);}
        else await txn.delete('device');
      } else await txn.put('device',state);
      return false;
    });
  }
  /** One-time browser sign-in using the code shown on the consenting PC.
   * No email address, OpenAI key or shared account credential is required.
   */
  async claimWithCode({deviceId,code}) {
    if(!DEVICE.test(deviceId)||!CODE.test(code))throw new Error('Código inválido');
    const result=await this.storage.transaction(async txn=>{
      const state=await txn.get('device');
      if(!state||state.deviceId!==deviceId)throw new Error('Computador não encontrado');
      const pending=state.ownerId?state.oauthChallenge:state;
      if(!pending||pending.expiresAt<=this.now())throw new Error('Código expirado');
      if(pending.attempts>=this.maxAttempts)throw new Error('Tentativas excedidas');
      const actual=await codeDigest(pending.salt,code);
      pending.attempts++;
      if(!safe(actual,pending.codeHash)){
        if(pending.attempts>=this.maxAttempts){
          if(state.ownerId)delete state.oauthChallenge;
          else {await txn.delete('device');return {error:'Tentativas excedidas'};}
        }
        if(await txn.get('device'))await txn.put('device',state);
        return {error:'Código incorreto'};
      }
      const ownerId=state.ownerId||'device:'+deviceId;
      await txn.put('device',{deviceId,ownerId,tokenHash:state.tokenHash,
                               approvedAt:state.approvedAt||this.now()});
      return {ownerId};
    });
    if(result.error)throw new Error(result.error);
    return result;
  }
  /** Existing owner can obtain a fresh one-time sign-in code via its agent secret. */
  async renewCode({deviceId,agentSecret,code}) {
    if(!DEVICE.test(deviceId)||!SECRET.test(agentSecret)||!CODE.test(code)){
      throw new Error('Solicitação inválida');
    }
    const hash=await digest(agentSecret);
    return this.storage.transaction(async txn=>{
      const state=await txn.get('device');
      if(!state?.ownerId||state.deviceId!==deviceId||!safe(state.tokenHash,hash)){
        throw new Error('Dispositivo não vinculado');
      }
      if(state.oauthChallenge?.expiresAt>this.now())throw new Error('Código anterior ainda ativo');
      const salt=randomSalt(),expiresAt=this.now()+this.ttlMs;
      state.oauthChallenge={salt,codeHash:await codeDigest(salt,code),expiresAt,attempts:0};
      await txn.put('device',state);
      return {deviceId,expiresAt};
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
