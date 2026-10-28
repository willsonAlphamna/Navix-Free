import test from 'node:test';
import assert from 'node:assert/strict';
import {protectedResourceMetadata,oauthChallenge} from '../src/oauth-resource.mjs';

const env={OIDC_ISSUER:'https://login.navixx.example',
  OIDC_AUDIENCE:'https://api.navixx.example/mcp',
  OIDC_JWKS_URL:'https://login.navixx.example/.well-known/jwks.json'};
test('metadata OAuth anuncia emissor e recurso exatos',()=>{
  const metadata=protectedResourceMetadata(env,'https://api.navixx.example/mcp');
  assert.equal(metadata.resource,env.OIDC_AUDIENCE);
  assert.deepEqual(metadata.authorization_servers,[env.OIDC_ISSUER]);
  assert.deepEqual(metadata.scopes_supported,['navix:control']);
});
test('sem configuração não inventa login anônimo',()=>{
  assert.throws(()=>protectedResourceMetadata({},'https://api.navixx.example/mcp'),/configurado/);
  assert.throws(()=>oauthChallenge({},'https://api.navixx.example/mcp'),/configurado/);
});
test('rejeita descoberta em HTTP inseguro',()=>{
  assert.throws(()=>protectedResourceMetadata(env,'http://api.navixx.example/mcp'),/HTTPS/);
  assert.throws(()=>oauthChallenge(env,'http://api.navixx.example/mcp'),/HTTPS/);
});
test('desafio WWW-Authenticate aponta URL do próprio recurso',()=>{
  const value=oauthChallenge(env,'https://api.navixx.example/mcp');
  assert.match(value,/Bearer resource_metadata=/);
  assert.match(value,/https:\/\/api.navixx.example\/\.well-known\/oauth-protected-resource/);
  assert.match(value,/navix:control/);
});
