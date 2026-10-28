/** Opt-in test of one consenting Windows device. Keep the 0.2.11 agent untouched. */
import assert from 'node:assert/strict';
import {createHash,randomBytes} from 'node:crypto';
import {CLIENT_ID,CALLBACK,SCOPE} from './src/device-oauth.mjs';

const base=process.env.NAVIX_LIVE_STAGING_URL;
const deviceId=process.env.NAVIX_REAL_DEVICE_ID;
const code=process.env.NAVIX_REAL_PAIR_CODE;
if(!/^https:\/\/navixx-cloud-staging\.[a-z0-9-]+\.workers\.dev$/.test(base||'')||
   !/^[A-Za-z0-9_-]{16,128}$/.test(deviceId||'')||!/^[0-9]{6}$/.test(code||'')){
  throw new Error('URL de staging, ID autorizado ou código temporário inválido.');
}
const request=(path,options={})=>fetch(base+path,{redirect:'manual',...options});
const post=(path,body,headers={})=>request(path,{method:'POST',headers:{'content-type':'application/json',...headers},body:JSON.stringify(body)});
const form=(path,params)=>request(path,{method:'POST',headers:{'content-type':'application/x-www-form-urlencoded'},body:new URLSearchParams(params)});
const verifier=randomBytes(32).toString('base64url');
const challenge=createHash('sha256').update(verifier).digest('base64url');
const auth={client_id:CLIENT_ID,redirect_uri:CALLBACK,response_type:'code',
  code_challenge:challenge,code_challenge_method:'S256',state:'real-canary',scope:SCOPE,resource:base};
const start=await request('/healthz');
assert.equal(start.status,200);
assert.equal((await start.json()).restricted_to_canary,true);
console.log('Validating real-device OAuth pairing and PKCE...');
const authorized=await form('/oauth/authorize',{...auth,device_id:deviceId,code});
assert.equal(authorized.status,302,`Authorization returned ${authorized.status}`);
const authCode=new URL(authorized.headers.get('location')).searchParams.get('code');
const exchange=await form('/oauth/token',{grant_type:'authorization_code',client_id:CLIENT_ID,
  redirect_uri:CALLBACK,code:authCode,code_verifier:verifier,resource:base});
assert.equal(exchange.status,200,`Token returned ${exchange.status}`);
const tokens=await exchange.json();
const token=tokens.access_token;
const headers={authorization:'Bearer '+token};
console.log('Waiting for the isolated NavixX Cloud Preview device to connect...');
let connected=false;
for(let attempt=0;attempt<30;attempt++){
  const res=await request('/api/device/status?device_id='+encodeURIComponent(deviceId),{headers});
  assert.equal(res.status,200);
  if((await res.json()).connected){connected=true;break;}
  await new Promise(resolve=>setTimeout(resolve,2000));
}
assert.equal(connected,true,'No Windows WebSocket connection after 60 seconds');
const call=async(name,args={})=>{
  const r=await post('/mcp',{jsonrpc:'2.0',method:'tools/call',id:Math.floor(Math.random()*1e6),
    params:{name,arguments:args}},headers);
  assert.equal(r.status,200,`${name} HTTP ${r.status}`);
  const data=await r.json();
  if(data.error){
    const diagnostic=await post('/api/device/execute?device_id='+encodeURIComponent(deviceId),
      {tool:'status',args:{}},headers);
    console.log('DIAGNOSTIC',diagnostic.status,JSON.stringify(await diagnostic.json()));
  }
  assert.ok(!data.error,`${name} MCP error ${JSON.stringify(data.error)}`);
  const out=data.result?.content?.[0]?.text;
  assert.equal(typeof out,'string',`${name} missing tool output`);
  const obj=JSON.parse(out);
  assert.ok(!data.result?.isError,`${name} returned tool error`);
  return obj;
};
const status=await call('status');
assert.equal(status.active,true,'Windows local authorization missing');
console.log('PASS 1: real Windows status through Cloudflare MCP.');
const command=await call('command_run',{shell:'powershell',command:'$PSVersionTable.PSVersion.ToString()',timeout_seconds:20});
assert.equal(command.exit_code,0,`PowerShell command failed`);
console.log('PASS 2: real Windows PowerShell through Cloudflare MCP.');
const testDir='C:\\Users\\wills\\AppData\\Local\\NavixXCloudPreviewDownloads\\_navix_canary_20261028';
await call('files_mkdir',{path:testDir,parents:false});
console.log('PASS 3: created isolated temporary folder.');
await call('files_delete',{path:testDir,recursive:false});
console.log('PASS 4: deleted isolated empty test folder.');
console.log('PASS: authenticated ChatGPT-compatible OAuth + remote MCP to REAL NavixX 0.3 Windows; no 0.2.11 changes.');
