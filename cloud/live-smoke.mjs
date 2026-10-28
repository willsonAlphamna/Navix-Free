/** Opt-in smoke test of STAGING only. Does not connect to a real Windows PC. */
import assert from 'node:assert/strict';
import {createHash,randomBytes} from 'node:crypto';
import WebSocket from 'ws';
import {HttpsProxyAgent} from 'https-proxy-agent';
import {CLIENT_ID,CALLBACK,SCOPE} from './src/device-oauth.mjs';

const endpoint=process.env.NAVIX_LIVE_STAGING_URL;
if(!endpoint||!/^https:\/\/navixx-cloud-staging\.[a-z0-9-]+\.workers\.dev$/.test(endpoint)){
  throw new Error('Informe a URL HTTPS EXATA do servidor de staging, nunca produção.');
}
const suffix=randomBytes(14).toString('base64url');
const deviceId='smoke_'+suffix;
const agentSecret=randomBytes(32).toString('base64url');
const code=String(Math.floor(Math.random()*1e6)).padStart(6,'0');
const verifier=randomBytes(32).toString('base64url');
const challenge=createHash('sha256').update(verifier).digest('base64url');
const resource=endpoint;
const req=(path,options={})=>fetch(endpoint+path,{redirect:'manual',...options});
const postJson=(path,body,headers={})=>req(path,{method:'POST',headers:{
  'content-type':'application/json',...headers},body:JSON.stringify(body)});
const form=(path,body)=>req(path,{method:'POST',headers:{
  'content-type':'application/x-www-form-urlencoded'},body:new URLSearchParams(body)});

console.log('Testing staging health and OAuth discovery...');
const health=await req('/healthz');
assert.equal(health.status,200);
const remoteControlEnabled=(await health.json()).public_tools_enabled;
assert.equal(typeof remoteControlEnabled,'boolean');
const meta=await(await req('/.well-known/oauth-authorization-server')).json();
assert.equal(meta.issuer,endpoint);
assert.ok(meta.code_challenge_methods_supported.includes('S256'));
const protectedMeta=await(await req('/.well-known/oauth-protected-resource')).json();
assert.equal(protectedMeta.resource,endpoint);

console.log('Registering a disposable simulated device...');
const started=await postJson('/api/pair/start',{device_id:deviceId,
  agent_secret:agentSecret,code});
assert.equal(started.status,201);
const pending=await req('/api/pair/state?device_id='+deviceId,{
  headers:{'x-navix-agent-token':agentSecret}});
assert.deepEqual(await pending.json(),{linked:false});

const authorization={client_id:CLIENT_ID,redirect_uri:CALLBACK,response_type:'code',
  code_challenge:challenge,code_challenge_method:'S256',state:'smoke-test',scope:SCOPE,resource};
assert.equal((await req('/oauth/authorize?'+new URLSearchParams(authorization))).status,200);
const denied=await form('/oauth/authorize',{...authorization,device_id:deviceId,code:'999999'});
assert.equal(denied.status,403);
const authorized=await form('/oauth/authorize',{...authorization,device_id:deviceId,code});
assert.equal(authorized.status,302);
const location=new URL(authorized.headers.get('location'));
assert.equal(location.origin,'https://chatgpt.com');
assert.equal(location.searchParams.get('iss'),endpoint);
const loginCode=location.searchParams.get('code');
assert.ok(loginCode);

console.log('Exchanging PKCE code, testing isolation, refreshing and revoking...');
const getTokens=await form('/oauth/token',{grant_type:'authorization_code',
  client_id:CLIENT_ID,redirect_uri:CALLBACK,code:loginCode,code_verifier:verifier,resource});
assert.equal(getTokens.status,200);
const tokens=await getTokens.json();
assert.equal(tokens.scope,SCOPE);
assert.equal((await form('/oauth/token',{grant_type:'authorization_code',
  client_id:CLIENT_ID,redirect_uri:CALLBACK,code:loginCode,code_verifier:verifier,resource})).status,400);
const status=()=>req('/api/device/status?device_id='+deviceId,{
  headers:{authorization:'Bearer '+tokens.access_token}});
const before=await status();
assert.equal(before.status,200);
assert.deepEqual(await before.json(),{connected:false});
console.log('Opening synthetic WebSocket transport with local-device credentials...');
const ws=new WebSocket(endpoint.replace('https://','wss://')+
  '/api/device/connect?device_id='+encodeURIComponent(deviceId),{
    headers:{'x-navix-agent-token':agentSecret},handshakeTimeout:20000,
    ...(process.env.wss_proxy||process.env.https_proxy||process.env.HTTPS_PROXY?{
      agent:new HttpsProxyAgent(process.env.wss_proxy||process.env.https_proxy||process.env.HTTPS_PROXY),
    }:{}),
});
await new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>reject(new Error('WebSocket connection timed out')),25000);
  ws.once('open',()=>{clearTimeout(timer);resolve()});
  ws.once('error',error=>{clearTimeout(timer);reject(error)});
});
const online=await status();
assert.equal(online.status,200);
assert.deepEqual(await online.json(),{connected:true});
if(remoteControlEnabled){
  console.log('Testing full authenticated MCP tool dispatch to the synthetic socket...');
  ws.on('message',data=>{
    const frame=JSON.parse(data.toString());
    assert.equal(frame.tool,'status');
    ws.send(JSON.stringify({kind:'result',id:frame.id,ok:true,result:{smoke:true}}));
  });
  const result=await postJson('/mcp',{jsonrpc:'2.0',method:'tools/call',id:7,
    params:{name:'status',arguments:{}}},{authorization:'Bearer '+tokens.access_token});
  assert.equal(result.status,200);
  const resultJson=await result.json();
  assert.equal(resultJson.result.content[0].type,'text');
  assert.deepEqual(JSON.parse(resultJson.result.content[0].text),{smoke:true});
  const noToken=await postJson('/mcp',{jsonrpc:'2.0',method:'tools/list',id:8});
  assert.equal(noToken.status,401);
}else{
  const disabled=await postJson('/mcp',{jsonrpc:'2.0',method:'tools/list',id:8},
    {authorization:'Bearer '+tokens.access_token});
  assert.equal(disabled.status,503);
}
ws.close();
await new Promise(resolve=>ws.once('close',resolve));
const refreshResponse=await form('/oauth/token',{grant_type:'refresh_token',
  client_id:CLIENT_ID,refresh_token:tokens.refresh_token,resource});
assert.equal(refreshResponse.status,200);
const next=await refreshResponse.json();
assert.equal((await status()).status,401);
const revoked=await postJson('/api/pair/revoke',{device_id:deviceId},{
  authorization:'Bearer '+next.access_token});
assert.equal(revoked.status,200);
assert.equal((await revoked.json()).revoked,true);
assert.equal((await req('/api/device/status?device_id='+deviceId,{
  headers:{authorization:'Bearer '+next.access_token}})).status,401);
console.log('PASS: live Cloudflare OAuth + PKCE + pair + WebSocket + refresh + revoke; '+
  (remoteControlEnabled?'synthetic MCP call delivered.':'public remote control stayed disabled.'));
