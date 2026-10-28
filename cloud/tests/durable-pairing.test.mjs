import test from 'node:test';
import assert from 'node:assert/strict';
import {DurablePairing} from '../src/durable-pairing.mjs';

const deviceId='device_abcdefgh1234';
const ownerA='owner-A';
const ownerB='owner-B';
const secret='A'.repeat(43);
const another='B'.repeat(43);
const code='071234';
class MemoryStore {
  state=new Map();
  async get(key) {return this.state.get(key);}
  async put(key,value) {this.state.set(key,structuredClone(value));}
  async delete(key) {this.state.delete(key);}
  async transaction(callback) {return callback(this);}
}
const make=()=>{let t=100000;const store=new MemoryStore();return {
  store,pair:new DurablePairing(store,{now:()=>t}),advance:ms=>t+=ms,
};};
test('inicia e aprova com código no computador e login do proprietário',async()=>{
  const {pair,store}=make();
  const challenge=await pair.start({deviceId,code,agentSecret:secret});
  assert.equal(challenge.deviceId,deviceId);
  assert.equal(await pair.verifyAgent(secret),false);
  assert.equal(await pair.verifyOwner(ownerA),false);
  const obj=await store.get('device');
  assert.equal(obj.codeHash.includes(code),false);
  assert.equal(obj.tokenHash.includes(secret),false);
  await pair.approve({ownerId:ownerA,deviceId,code});
  assert.equal(await pair.verifyAgent(secret),true);
  assert.equal(await pair.verifyOwner(ownerA),true);
  assert.equal(await pair.verifyOwner(ownerB),false);
});
test('contas diferentes não recebem acesso ao dispositivo',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  await pair.approve({ownerId:ownerA,deviceId,code});
  assert.equal(await pair.verifyOwner(ownerB),false);
  assert.equal(await pair.revoke({ownerId:ownerB}),false);
  assert.equal(await pair.verifyOwner(ownerA),true);
});
test('código incorreto contabilizado e rejeitado após cinco tentativas',async()=>{
  const {pair,store}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  for(let i=0;i<5;i++) await assert.rejects(pair.approve({ownerId:ownerA,deviceId,code:'999999'}));
  assert.equal(await store.get('device'),undefined);
  await assert.rejects(pair.approve({ownerId:ownerA,deviceId,code}),/não encontrado/);
});
test('pairing expira e exige reiniciar',async()=>{
  const {pair,advance}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  advance(120000);
  await assert.rejects(pair.approve({ownerId:ownerA,deviceId,code}),/expirado/);
  const next=await pair.start({deviceId,code,agentSecret:another});
  assert.ok(next.expiresAt);
});
test('não permite outro desafio ativo para o mesmo ID',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  await assert.rejects(pair.start({deviceId,code,agentSecret:another}),/aguardando/);
});
test('dispositivo aprovado não pode ser vinculado novamente sem revogação',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  await pair.approve({ownerId:ownerA,deviceId,code});
  await assert.rejects(pair.start({deviceId,code,agentSecret:another}),/pertence/);
});
test('segredo de outro PC não identifica a máquina',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  assert.deepEqual(await pair.status({deviceId,agentSecret:another}),{linked:false});
  await pair.approve({ownerId:ownerA,deviceId,code});
  assert.equal(await pair.verifyAgent(another),false);
  assert.deepEqual(await pair.status({deviceId,agentSecret:secret}),{linked:true});
});
test('revogação invalida imediatamente segredo e titularidade',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  await pair.approve({ownerId:ownerA,deviceId,code});
  assert.equal(await pair.revoke({ownerId:ownerA}),true);
  assert.equal(await pair.verifyAgent(secret),false);
  assert.equal(await pair.verifyOwner(ownerA),false);
});
test('não aceita ID curto, código não numérico nem token fraco',async()=>{
  const {pair}=make();
  for(const bad of [
    {deviceId:'a',code,agentSecret:secret},
    {deviceId,code:'abcdef',agentSecret:secret},
    {deviceId,code,agentSecret:'short'},
  ]) await assert.rejects(pair.start(bad));
});

test('repetir aprovação depois de vinculado é recusado',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  await pair.approve({ownerId:ownerA,deviceId,code});
  await assert.rejects(pair.approve({ownerId:ownerA,deviceId,code}),/não encontrado/);
});
test('mesmo código com identificador adulterado não vincula dispositivo',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  await assert.rejects(pair.approve({ownerId:ownerA,deviceId:'device_WRONGabcdefgh',code}),/não encontrado/);
  assert.equal(await pair.verifyOwner(ownerA),false);
});
test('revogado não pode reutilizar segredo antigo em novo pareamento',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  await pair.approve({ownerId:ownerA,deviceId,code});
  await pair.revoke({ownerId:ownerA});
  await pair.start({deviceId,code,agentSecret:another});
  await pair.approve({ownerId:ownerA,deviceId,code});
  assert.equal(await pair.verifyAgent(secret),false);
  assert.equal(await pair.verifyAgent(another),true);
});
test('status de token correto só confirma pareamento depois da aprovação',async()=>{
  const {pair}=make();
  await pair.start({deviceId,code,agentSecret:secret});
  assert.deepEqual(await pair.status({deviceId,agentSecret:secret}),{linked:false});
  await pair.approve({ownerId:ownerA,deviceId,code});
  assert.deepEqual(await pair.status({deviceId,agentSecret:secret}),{linked:true});
});
