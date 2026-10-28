import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {DurablePairing} from '../src/durable-pairing.mjs';
import {DeviceOAuth,CLIENT_ID,CALLBACK,SCOPE,authorizationParams,authMetadata,
  oauthRedirect,splitCredential,pairingPage} from '../src/device-oauth.mjs';

const device='device_abcdefgh1234';
const other='device_zxywvuts9876';
const secret='A'.repeat(43),code='051289',origin='https://navix.example.workers.dev';
const verifier='v'.repeat(43);
const challenge=createHash('sha256').update(verifier).digest('base64url');
class Store {
  state=new Map();
  async get(key){return this.state.get(key);}
  async put(key,value){this.state.set(key,structuredClone(value));}
  async delete(key){this.state.delete(key);}
  async transaction(cb){return cb(this);}
}
const setup=()=>{
  let time=1_000_000;
  const store=new Store(),now=()=>time;
  const pairing=new DurablePairing(store,{now});
  const oauth=new DeviceOAuth(store,pairing,{now});
  return {pairing,oauth,store,advance:ms=>time+=ms};
};
const details={deviceId:device,code,clientId:CLIENT_ID,redirectUri:CALLBACK,
  challenge,resource:origin};

test('metadados anunciam OAuth público com PKCE S256 e issuer compatível',()=>{
  const meta=authMetadata(origin);
  assert.equal(meta.issuer,origin);
  assert.equal(meta.code_challenge_methods_supported[0],'S256');
  assert.equal(meta.client_id_metadata_document_supported,true);
  assert.equal(meta.authorization_response_iss_parameter_supported,true);
});
test('só aceita o cliente ChatGPT conhecido, callback fixo e resource exato',()=>{
  const p=new URLSearchParams({client_id:CLIENT_ID,redirect_uri:CALLBACK,
    response_type:'code',code_challenge:challenge,code_challenge_method:'S256',
    scope:SCOPE,resource:origin,state:'stateXYZ'});
  assert.equal(authorizationParams(p,origin).clientId,CLIENT_ID);
  for(const [key,value] of [['client_id','https://evil.test/oauth.json'],
    ['redirect_uri','https://evil.test/callback'],['resource','https://evil.test'],
    ['code_challenge_method','plain'],['scope','admin']]){
    const copy=new URLSearchParams(p);copy.set(key,value);
    assert.throws(()=>authorizationParams(copy,origin));
  }
  const page=pairingPage(authorizationParams(p,origin));
  assert.match(page,/Código temporário/);
  assert.doesNotMatch(page,/script src=/);
  const redirect=oauthRedirect(authorizationParams(p,origin),device+'.'+secret,origin);
  assert.equal(new URL(redirect).searchParams.get('iss'),origin);
});
test('pareia dono apenas após código no dispositivo e emite token de uma única utilização',async()=>{
  const {pairing,oauth}=setup();
  await pairing.start({deviceId:device,code,agentSecret:secret});
  const authCode=await oauth.createCode(details);
  assert.equal(await pairing.verifyAgent(secret),true);
  const tokens=await oauth.exchangeCode({code:authCode,clientId:CLIENT_ID,
    redirectUri:CALLBACK,verifier,resource:origin});
  assert.equal(tokens.token_type,'Bearer');
  assert.equal(splitCredential(tokens.access_token).deviceId,device);
  assert.equal((await oauth.verifyAccess(tokens.access_token,origin)).deviceId,device);
  await assert.rejects(oauth.exchangeCode({code:authCode,clientId:CLIENT_ID,
    redirectUri:CALLBACK,verifier,resource:origin}));
  await assert.rejects(oauth.verifyAccess(tokens.access_token,'https://evil.test'));
});
test('PKCE incorreto recusa sem consumir o código válido',async()=>{
  const {pairing,oauth}=setup();
  await pairing.start({deviceId:device,code,agentSecret:secret});
  const authCode=await oauth.createCode(details);
  await assert.rejects(oauth.exchangeCode({code:authCode,clientId:CLIENT_ID,
    redirectUri:CALLBACK,verifier:'x'.repeat(43),resource:origin}),/PKCE/);
  const tokens=await oauth.exchangeCode({code:authCode,clientId:CLIENT_ID,
    redirectUri:CALLBACK,verifier,resource:origin});
  assert.ok(tokens.access_token);
});
test('refresh rotaciona, invalida token anterior e rejeita outra conta',async()=>{
  const {pairing,oauth}=setup();
  await pairing.start({deviceId:device,code,agentSecret:secret});
  const authCode=await oauth.createCode(details);
  const original=await oauth.exchangeCode({code:authCode,clientId:CLIENT_ID,
    redirectUri:CALLBACK,verifier,resource:origin});
  const replacement=await oauth.refresh({refreshToken:original.refresh_token,
    clientId:CLIENT_ID,resource:origin});
  await assert.rejects(oauth.refresh({refreshToken:original.refresh_token,
    clientId:CLIENT_ID,resource:origin}));
  await assert.rejects(oauth.verifyAccess(original.access_token,origin));
  assert.equal((await oauth.verifyAccess(replacement.access_token,origin)).deviceId,device);
  await assert.rejects(oauth.refresh({refreshToken:other+'.'+splitCredential(replacement.refresh_token).secret,
    clientId:CLIENT_ID,resource:origin}));
});
test('token expira; revogação do computador bloqueia acesso na mesma hora',async()=>{
  const {pairing,oauth,advance}=setup();
  await pairing.start({deviceId:device,code,agentSecret:secret});
  const authCode=await oauth.createCode(details);
  const tokens=await oauth.exchangeCode({code:authCode,clientId:CLIENT_ID,
    redirectUri:CALLBACK,verifier,resource:origin});
  advance(3600001);
  await assert.rejects(oauth.verifyAccess(tokens.access_token,origin));
  advance(-3600001);
  assert.equal(await pairing.revoke({ownerId:'device:'+device}),true);
  await assert.rejects(oauth.verifyAccess(tokens.access_token,origin));
});
test('reconexão exige outro código gerado pelo mesmo PC, e rejeita segredo alheio',async()=>{
  const {pairing,oauth}=setup();
  await pairing.start({deviceId:device,code,agentSecret:secret});
  await oauth.createCode(details);
  await assert.rejects(oauth.createCode(details));
  await assert.rejects(pairing.renewCode({deviceId:device,agentSecret:'B'.repeat(43),code}));
  await pairing.renewCode({deviceId:device,agentSecret:secret,code:'951753'});
  const newCode=await oauth.createCode({...details,code:'951753'});
  assert.ok(newCode.startsWith(device+'.'));
});
test('código de outro dispositivo e tentativas repetidas não autorizam',async()=>{
  const {pairing,oauth}=setup();
  await pairing.start({deviceId:device,code,agentSecret:secret});
  for(let n=0;n<5;n++)await assert.rejects(oauth.createCode({...details,code:'999999'}));
  await assert.rejects(oauth.createCode(details));
  await assert.rejects(oauth.createCode({...details,deviceId:other}));
});
