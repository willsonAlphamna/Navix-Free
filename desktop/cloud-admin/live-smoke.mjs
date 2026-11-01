import assert from 'node:assert/strict';
const base='https://windows-admin-full.navixx-alfamna.workers.dev';
async function req(path,body,headers={}) {
 const r=await fetch(base+path,{method:body===undefined?'GET':'POST',headers:{...(body===undefined||body instanceof URLSearchParams?{}:{'Content-Type':'application/json'}),...headers},body:body===undefined?undefined:body instanceof URLSearchParams?body:JSON.stringify(body),redirect:'manual',signal:AbortSignal.timeout(60000)});
 return r;
}
for(const [path,key] of [['/health','cloud'],['/.well-known/oauth-authorization-server','authorization_endpoint'],['/.well-known/oauth-protected-resource/mcp','authorization_servers']]) {
 const r=await req(path);assert.equal(r.status,200);assert.ok((await r.json())[key]);
}
const anonymous=await req('/mcp',{jsonrpc:'2.0',id:1,method:'tools/list'});
assert.equal(anonymous.status,401);assert.ok(anonymous.headers.get('www-authenticate')?.includes('resource_metadata'));
let device;
try {
 const enrolled=await req('/device/register',{name:'CI SIMULADOR - sem acesso ao Windows'});assert.equal(enrolled.status,200);device=await enrolled.json();
 const paired=await req('/pair',{setup_token:device.setup_url.split('#')[1]});assert.equal(paired.status,200);const cookie=paired.headers.get('set-cookie').split(';')[0];
 const registered=await req('/register',{client_name:'CI teste descartavel',redirect_uris:['https://chatgpt.com/connector/oauth/callback']});assert.equal(registered.status,201);const client=await registered.json();
 const verifier='v'.repeat(64),challenge=Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier))).toString('base64url');
 const query=new URLSearchParams({client_id:client.client_id,response_type:'code',redirect_uri:client.redirect_uris[0],code_challenge:challenge,code_challenge_method:'S256',state:'test'});
 const authorize=await req('/authorize?'+query,undefined,{Cookie:cookie});const page=await authorize.text();const consent=page.match(/name="consent" value="([a-f0-9]+)"/)?.[1];assert.ok(consent);
 const approved=await req('/approve',new URLSearchParams({consent}),{Cookie:cookie});assert.equal(approved.status,303);const code=new URL(approved.headers.get('location')).searchParams.get('code');
 const form=new URLSearchParams({grant_type:'authorization_code',client_id:client.client_id,redirect_uri:client.redirect_uris[0],code,code_verifier:verifier});
 const tokenReply=await req('/token',form);assert.equal(tokenReply.status,200);const tokens=await tokenReply.json();assert.ok(tokens.access_token);
 const agent={Authorization:'Bearer '+device.agent_token},auth={Authorization:'Bearer '+tokens.access_token};
 await req('/device/poll',{status:{simulated:true}},agent);
 const pending=req('/mcp',{jsonrpc:'2.0',id:7,method:'tools/call',params:{name:'status',arguments:{}}},auth);
 let job;
 for(let i=0;i<20;i++) {await new Promise(r=>setTimeout(r,300));const polled=await req('/device/poll',{status:{simulated:true}},agent);assert.equal(polled.status,200);job=await polled.json();if(job.job_id)break;}
 assert.ok(job?.job_id);
 const result={content:[{type:'text',text:JSON.stringify({simulated:true,windows_verified:false})}]};
 const sent=await req('/device/result',{job_id:job.job_id,result},agent);assert.equal(sent.status,200);
 const response=await pending;assert.equal(response.status,200);assert.deepEqual((await response.json()).result,result);
 console.log('Ponte HTTPS real: descoberta, OAuth PKCE, pareamento, fila e retorno: OK. Agente simulado; Windows do usuario nao testado.');
} finally {
 if(device?.agent_token) {const removed=await req('/device/remove',{}, {Authorization:'Bearer '+device.agent_token});assert.equal(removed.status,200);}
}
