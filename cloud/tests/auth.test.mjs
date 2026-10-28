import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPair, SignJWT, exportJWK, createLocalJWKSet} from 'jose';
import {verifyOAuthToken, readBearer, configFromEnv} from '../src/auth.mjs';

const issuer = 'https://auth.navix.test';
const audience = 'https://api.navix.test';
async function fixture(scope='navix:control') {
  const pair = await generateKeyPair('RS256');
  const jwk = await exportJWK(pair.publicKey);
  jwk.kid = 'test-key';
  const keySet = createLocalJWKSet({keys:[jwk]});
  const token = await new SignJWT({scope})
    .setProtectedHeader({alg:'RS256',kid:'test-key'})
    .setIssuer(issuer).setAudience(audience).setSubject('owner_12345678')
    .setIssuedAt().setExpirationTime('5m').sign(pair.privateKey);
  return {token,keySet};
}
test('confirma assinatura, identidade, emissor, audiência e escopo', async () => {
  const {token,keySet} = await fixture();
  const result = await verifyOAuthToken(token,keySet,{issuer,audience,requiredScope:'navix:control'});
  assert.equal(result.ownerId,'owner_12345678');
  await assert.rejects(verifyOAuthToken(token,keySet,{issuer,audience:'https://outro',requiredScope:'navix:control'}));
  await assert.rejects(verifyOAuthToken(token,keySet,{issuer:'https://falso',audience,requiredScope:'navix:control'}));
  await assert.rejects(verifyOAuthToken(token,keySet,{issuer,audience,requiredScope:'navix:agent'}),/Escopo/);
});
test('rejeita assinatura de outro titular e token manipulado', async () => {
  const a=await fixture();
  const b=await fixture();
  await assert.rejects(verifyOAuthToken(a.token,b.keySet,{issuer,audience,requiredScope:'navix:control'}));
  const modified=a.token.slice(0,-2)+'xx';
  await assert.rejects(verifyOAuthToken(modified,a.keySet,{issuer,audience,requiredScope:'navix:control'}));
});
test('não aceita cabeçalho diferente de Bearer', () => {
  const request = new Request('https://api.navix.test',{headers:{Authorization:'Bearer abc.def.ghi'}});
  assert.equal(readBearer(request),'abc.def.ghi');
  assert.throws(()=>readBearer(new Request('https://api.navix.test')),/ausente/);
  assert.throws(()=>readBearer(new Request('https://api.navix.test',{headers:{Authorization:'Basic xyz'}})),/inválido/);
});
test('bloqueia configuração incompleta e URL sem HTTPS', () => {
  assert.throws(()=>configFromEnv({}),/não configurado/);
  assert.throws(()=>configFromEnv({OIDC_ISSUER:'http://local',OIDC_AUDIENCE:audience,OIDC_JWKS_URL:issuer}),/HTTPS/);
  const c=configFromEnv({OIDC_ISSUER:issuer,OIDC_AUDIENCE:audience,OIDC_JWKS_URL:issuer+'/jwks'});
  assert.equal(c.issuer,issuer);
});

