import {createHash, randomBytes, randomInt, timingSafeEqual} from 'node:crypto';

const CAPS = new Set(['browser', 'desktop', 'files', 'commands']);
const validId = value => typeof value === 'string' && /^[A-Za-z0-9_-]{8,128}$/.test(value);
const digest = value => createHash('sha256').update(value, 'utf8').digest();
const same = (left, right) => timingSafeEqual(left, right);

export class PairingRegistry {
  constructor({now = Date.now, ttlMs = 120_000, maxAttempts = 5} = {}) {
    this.now = now;
    this.ttlMs = ttlMs;
    this.maxAttempts = maxAttempts;
    this.pending = new Map();
    this.devices = new Map();
  }
  begin({ownerId, deviceId, publicKey}) {
    if (!validId(ownerId) || !validId(deviceId) || !publicKey || typeof publicKey !== 'string') {
      throw new TypeError('Identidade, dispositivo e chave pública obrigatórios.');
    }
    if (this.devices.has(deviceId)) {
      throw new Error('Dispositivo já vinculado. Revogue antes de parear novamente.');
    }
    for (const [id, entry] of this.pending) if (entry.deviceId === deviceId) this.pending.delete(id);
    const pairingId = randomBytes(16).toString('hex');
    const code = String(randomInt(0, 1_000_000)).padStart(6, '0');
    const expiresAt = this.now() + this.ttlMs;
    this.pending.set(pairingId, {ownerId, deviceId, publicKey, codeHash: digest(code), expiresAt, attempts: 0});
    return {pairingId, verificationCode: code, expiresAt};
  }
  approve({ownerId, pairingId, verificationCode}) {
    const entry = this.pending.get(pairingId);
    if (!entry || entry.ownerId !== ownerId) throw new Error('Pareamento não encontrado.');
    if (this.now() >= entry.expiresAt) {
      this.pending.delete(pairingId);
      throw new Error('Pareamento expirado.');
    }
    if (entry.attempts >= this.maxAttempts) {
      this.pending.delete(pairingId);
      throw new Error('Limite de tentativas.');
    }
    entry.attempts++;
    const value = typeof verificationCode === 'string' && /^\d{6}$/.test(verificationCode)
      ? digest(verificationCode) : digest('');
    if (!same(entry.codeHash, value)) {
      if (entry.attempts >= this.maxAttempts) this.pending.delete(pairingId);
      throw new Error('Código incorreto.');
    }
    if (this.devices.has(entry.deviceId)) throw new Error('Dispositivo já vinculado.');
    this.pending.delete(pairingId);
    this.devices.set(entry.deviceId, {ownerId, publicKey: entry.publicKey, approvedAt: this.now()});
    return {deviceId: entry.deviceId, ownerId};
  }
  authorize({ownerId, deviceId, capability, localPermissions}) {
    const entry = this.devices.get(deviceId);
    if (!entry || entry.ownerId !== ownerId) return false;
    if (!CAPS.has(capability)) return false;
    return Array.isArray(localPermissions) && localPermissions.includes(capability);
  }
  revoke({ownerId, deviceId}) {
    const entry = this.devices.get(deviceId);
    if (!entry || entry.ownerId !== ownerId) return false;
    this.devices.delete(deviceId);
    return true;
  }
}
