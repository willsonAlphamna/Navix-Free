import test from 'node:test';
import assert from 'node:assert/strict';
import {Bridge} from './worker.mjs';
class Storage {
  data=new Map(); alarm=null; pending=Promise.resolve();
  async get(k){return structuredClone(this.data.get(k));}
  async put(k,v){this.data.set(k,structuredClone(v));}
  async delete(k){return this.data.delete(k);}
  async list(o={}){return new Map([...this.data].filter(([k])=>!o.prefix||k.startsWith(o.prefix)).map(([k,v])=>[k,structuredClone(v)]));}
  async getAlarm(){return this.alarm;} async setAlarm(t){this.alarm=t;}
  async transaction(fn){let release;const previous=this.pending;this.pending=new Promise(r=>release=r);await previous;try{return await fn(this);}finally{release();}}
}
const origin='https://windows-admin-full.example';
function harness(){const db=new Storage();const bridge=new Bridge({storage:db},{});return {db,bridge,req:async(path,body,headers={},method)=>{
 const r=new Request(origin+path,{method:method||(body===undefined?'GET':'POST'),headers:{...(body instanceof URLSearchParams?{}:body!==undefined?{'Content-Type':'application/json'}:{}),...headers},body:body===undefined?undefined:body instanceof URLSearchParams?body:JSON.stringify(body)});return bridge.fetch(r);
}};}
async function device(h,name='PC Wilson'){
 const response=await h.req('/device/register',{name});assert.equal(response.status,200);const d=await response.json();
 const paired=await h.req('/pair',{setup_token:d.setup_url.split('#')[1]});assert.equal(paired.status,200);
 return {...d,cookie:paired.headers.get('set-cookie').split(';')[0]};
}
async function oauth(h,d){
 const client=await (await h.req('/register',{client_name:'ChatGPT',redirect_uris:['https://chatgpt.com/connector/oauth/callback']})).json();
 const verifier='x'.repeat(64);const challenge=Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier))).toString('base64url');
 const q=new URLSearchParams({response_type:'code',client_id:client.client_id,redirect_uri:client.redirect_uris[0],code_challenge:challenge,code_challenge_method:'S256',state:'abc'});
 const r=await h.req('/authorize?'+q,undefined,{Cookie:d.cookie});assert.equal(r.status,200);const page=await r.text();const consent=page.match(/name="consent" value="([a-f0-9]+)"/)[1];
 const approval=await h.req('/approve',new URLSearchParams({consent}),{Cookie:d.cookie});assert.equal(approval.status,303);
 const url=new URL(approval.headers.get('location'));assert.equal(url.searchParams.get('state'),'abc');
 const form=new URLSearchParams({grant_type:'authorization_code',client_id:client.client_id,redirect_uri:client.redirect_uris[0],code:url.searchParams.get('code'),code_verifier:verifier});
 const tokens=await (await h.req('/token',form)).json();assert.ok(tokens.access_token);
 return {client,tokens,form,consent};
}
test('sem autenticacao, sem execucao e sem registro de callback malicioso',async()=>{
 const h=harness();assert.equal((await h.req('/mcp',{})).status,401);
 assert.equal((await h.req('/device/poll',{})).status,401);
 assert.equal((await h.req('/register',{redirect_uris:['https://evil.example/callback']})).status,400);
 assert.equal((await h.req('/device/register',{name:'x'},{Origin:'https://evil.example'})).status,403);
});
test('pareamento e codigo OAuth sao de uso unico; PKCE e refresh funcionam',async()=>{
 const h=harness(),d=await device(h),o=await oauth(h,d);
 assert.equal((await h.req('/pair',{setup_token:d.setup_url.split('#')[1]})).status,401);
 assert.equal((await h.req('/token',o.form)).status,400);
 const refresh=new URLSearchParams({grant_type:'refresh_token',refresh_token:o.tokens.refresh_token,client_id:o.client.client_id});
 assert.ok((await (await h.req('/token',refresh)).json()).access_token);
 assert.equal((await h.req('/token',refresh)).status,400);
 assert.equal((await h.req('/approve',new URLSearchParams({consent:o.consent}),{Cookie:d.cookie})).status,403);
});
test('cookie de outro PC nao autoriza o consentimento original',async()=>{
 const h=harness(),a=await device(h,'PC A'),b=await device(h,'PC B');
 await h.bridge.put('consent:test',{device:a.device_id,owner:'unknown',client:'c'});
 assert.equal((await h.req('/approve',new URLSearchParams({consent:'test'}),{Cookie:b.cookie})).status,403);
});
test('PC offline: ferramenta retorna erro sem enfileirar comando',async()=>{
 const h=harness(),d=await device(h),o=await oauth(h,d);
 const r=await (await h.req('/mcp',{jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'command_run',arguments:{command:'whoami'}}},{Authorization:'Bearer '+o.tokens.access_token})).json();
 assert.equal(r.result.isError,true);assert.equal((await h.db.list({prefix:'job:'})).size,0);
});
test('ponte completa simulada: OAuth, envio ao PC, resultado em blocos e isolamento',async()=>{
 const h=harness(),d=await device(h),other=await device(h,'Other PC'),o=await oauth(h,d);
 const auth={Authorization:'Bearer '+d.agent_token};
 await h.req('/device/poll',{status:{administrator:true}},auth);
 const pending=h.req('/mcp',{jsonrpc:'2.0',id:3,method:'tools/call',params:{name:'status',arguments:{}}},{Authorization:'Bearer '+o.tokens.access_token});
 let job;for(let i=0;i<30;i++){await new Promise(r=>setTimeout(r,10));job=await (await h.req('/device/poll',{status:{}},auth)).json();if(job.job_id)break;}
 assert.ok(job.job_id);
 assert.equal((await h.req('/device/result',{job_id:job.job_id,result:{}},{Authorization:'Bearer '+other.agent_token})).status,403);
 const value={content:[{type:'text',text:'x'.repeat(150000)}]};
 assert.equal((await h.req('/device/result',{job_id:job.job_id,result:value},auth)).status,200);
 const response=await (await pending).json();assert.equal(response.result.content[0].text.length,150000);
 assert.equal((await h.db.list({prefix:'chunk:'})).size,0);
});
test('metadados OAuth e descoberta MCP',async()=>{
 const h=harness(),d=await device(h),o=await oauth(h,d);
 const meta=await (await h.req('/.well-known/oauth-authorization-server')).json();assert.deepEqual(meta.code_challenge_methods_supported,['S256']);
 const r=await (await h.req('/mcp',{jsonrpc:'2.0',id:1,method:'tools/list'},{Authorization:'Bearer '+o.tokens.access_token})).json();assert.equal(r.result.tools.length,44);
});
