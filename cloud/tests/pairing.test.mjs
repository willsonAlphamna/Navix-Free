import test from 'node:test';
import assert from 'node:assert/strict';
import {PairingRegistry} from '../src/pairing.mjs';

const setup = () => {
  let clock = 1000;
  return {pair: new PairingRegistry({now: () => clock}), advance: ms => {clock += ms;}};
};
const userA = 'user_A12345', userB = 'user_B12345';
const deviceA = 'device_A12345';

test('vincula um dispositivo apenas à identidade verificada', () => {
  const {pair} = setup();
  const req = pair.begin({ownerId:userA,deviceId:deviceA,publicKey:'public-key-A'});
  assert.equal(pair.approve({ownerId:userA,pairingId:req.pairingId,verificationCode:req.verificationCode}).ownerId,userA);
  assert.equal(pair.authorize({ownerId:userA,deviceId:deviceA,capability:'files',localPermissions:['files']}),true);
  assert.equal(pair.authorize({ownerId:userB,deviceId:deviceA,capability:'files',localPermissions:['files']}),false);
});
test('não transfere dispositivos entre contas nem aceita códigos cruzados', () => {
  const {pair} = setup();
  const req = pair.begin({ownerId:userA,deviceId:deviceA,publicKey:'key'});
  assert.throws(() => pair.approve({ownerId:userB,pairingId:req.pairingId,verificationCode:req.verificationCode}));
  assert.throws(() => pair.approve({ownerId:userA,pairingId:req.pairingId,verificationCode:'000000'}),/Código incorreto/);
  pair.approve({ownerId:userA,pairingId:req.pairingId,verificationCode:req.verificationCode});
  assert.throws(() => pair.begin({ownerId:userB,deviceId:deviceA,publicKey:'key'}),/já vinculado/);
});
test('expira o desafio e invalida o código após aprovação', () => {
  const {pair,advance} = setup();
  const first = pair.begin({ownerId:userA,deviceId:deviceA,publicKey:'key'});
  advance(120000);
  assert.throws(() => pair.approve({ownerId:userA,pairingId:first.pairingId,verificationCode:first.verificationCode}),/expirado/);
  const next = pair.begin({ownerId:userA,deviceId:deviceA,publicKey:'key'});
  pair.approve({ownerId:userA,pairingId:next.pairingId,verificationCode:next.verificationCode});
  assert.throws(() => pair.approve({ownerId:userA,pairingId:next.pairingId,verificationCode:next.verificationCode}),/não encontrado/);
});
test('desabilita controle quando falta permissão local', () => {
  const {pair} = setup();
  const req = pair.begin({ownerId:userA,deviceId:deviceA,publicKey:'key'});
  pair.approve({ownerId:userA,pairingId:req.pairingId,verificationCode:req.verificationCode});
  assert.equal(pair.authorize({ownerId:userA,deviceId:deviceA,capability:'commands',localPermissions:['files']}),false);
  assert.equal(pair.authorize({ownerId:userA,deviceId:deviceA,capability:'unknown',localPermissions:['unknown']}),false);
  assert.equal(pair.authorize({ownerId:userA,deviceId:deviceA,capability:'browser',localPermissions:['browser']}),true);
});
test('revogação bloqueia acesso imediatamente', () => {
  const {pair} = setup();
  const req = pair.begin({ownerId:userA,deviceId:deviceA,publicKey:'key'});
  pair.approve({ownerId:userA,pairingId:req.pairingId,verificationCode:req.verificationCode});
  assert.equal(pair.revoke({ownerId:userB,deviceId:deviceA}),false);
  assert.equal(pair.revoke({ownerId:userA,deviceId:deviceA}),true);
  assert.equal(pair.authorize({ownerId:userA,deviceId:deviceA,capability:'browser',localPermissions:['browser']}),false);
});
test('limita tentativas de código', () => {
  const {pair} = setup();
  const req = pair.begin({ownerId:userA,deviceId:deviceA,publicKey:'key'});
  for (let i=0;i<5;i++) assert.throws(() => pair.approve({ownerId:userA,pairingId:req.pairingId,verificationCode:'não é código'}));
  assert.throws(() => pair.approve({ownerId:userA,pairingId:req.pairingId,verificationCode:req.verificationCode}),/não encontrado/);
});

