/** Read-only audit of the actual Cloudflare staging MCP. No Windows commands or personal tokens. */
import assert from 'node:assert/strict';
import {CLIENT_ID,CALLBACK,SCOPE} from './src/device-oauth.mjs';
const origin='https://navixx-cloud-staging.navixx-alfamna.workers.dev';
const read=async(path,init={})=>{
  const response=await fetch(origin+path,{redirect:'manual',signal:AbortSignal.timeout(15000),...init});
  return response;
};
const health=await read('/healthz');
assert.equal(health.status,200,'O backend Cloudflare precisa estar publicado e acessível');
const info=await health.json();
assert.equal(info.service,'navixx-cloud');
console.log('Cloudflare reachable:',info.service,'remote control enabled:',info.public_tools_enabled);
const resource=await read('/.well-known/oauth-protected-resource');
assert.equal(resource.status,200,'Descoberta do recurso OAuth indisponível');
const resourceInfo=await resource.json();
assert.equal(resourceInfo.resource,origin);
assert.ok(resourceInfo.authorization_servers.includes(origin));
const auth=await read('/.well-known/oauth-authorization-server');
assert.equal(auth.status,200,'Descoberta do emissor OAuth indisponível');
const authInfo=await auth.json();
assert.equal(authInfo.issuer,origin);
assert.equal(authInfo.authorization_endpoint,origin+'/oauth/authorize');
assert.equal(authInfo.token_endpoint,origin+'/oauth/token');
assert.equal(authInfo.client_id_metadata_document_supported,true);
const challenge=await read('/mcp',{method:'POST',headers:{'content-type':'application/json'},
  body:JSON.stringify({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-06-18'}})});
if(challenge.status===401){
  // Old staging still requires OAuth before tools/list; alpha.8 deployment is pending.
  assert.match(challenge.headers.get('www-authenticate')||'',/Bearer resource_metadata=/);
  console.warn('STAGING AINDA ANTIGO: resposta 401 antes da descoberta das ferramentas; versão mista NÃO implantada.');
}else{
  assert.equal(challenge.status,200,'O MCP deve responder 200 à inicialização anônima ou usar desafio OAuth 401');
  const init=await challenge.json();
  assert.equal(init.result.serverInfo.name,'NavixX Cloud');
  const catalog=await read('/mcp',{method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({jsonrpc:'2.0',id:2,method:'tools/list'})});
  assert.equal(catalog.status,200);
  assert.ok((await catalog.json()).result.tools.some(x=>x.name==='navixx_cloud_connection_status'));
}
const query=new URLSearchParams({
  client_id:CLIENT_ID,redirect_uri:CALLBACK,response_type:'code',code_challenge:'a'.repeat(43),
  code_challenge_method:'S256',state:'navix-read-only-audit',scope:SCOPE,resource:origin});
const page=await read('/oauth/authorize?'+query.toString());
assert.equal(page.status,200,'A página do código de vínculo precisa existir');
assert.match(await page.text(),/ID do computador/);
console.log('PASS: OAuth discovery + 401 challenge + pairing page; Windows PC intentionally NOT touched.');
