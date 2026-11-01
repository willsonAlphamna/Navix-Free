import assert from 'node:assert/strict';
const base='https://windows-admin-full.navixx-alfamna.workers.dev';
for (const [path,key] of [['/health','cloud'],['/.well-known/oauth-authorization-server','authorization_endpoint'],['/.well-known/oauth-protected-resource/mcp','authorization_servers']]) {
 const r=await fetch(base+path,{signal:AbortSignal.timeout(20000)});assert.equal(r.status,200);const data=await r.json();assert.ok(data[key]);
}
const r=await fetch(base+'/mcp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/list'}),signal:AbortSignal.timeout(20000)});
assert.equal(r.status,401);assert.ok(r.headers.get('www-authenticate')?.includes('resource_metadata'));
console.log('HTTPS, metadados OAuth e rejeicao de acesso anonimo: OK. Windows real nao testado.');
