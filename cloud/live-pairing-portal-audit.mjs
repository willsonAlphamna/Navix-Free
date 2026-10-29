/** Safe live canary probe. GET only: never consumes a device code or touches Windows. */
import assert from 'node:assert/strict';
const origin='https://navixx-cloud-staging.navixx-alfamna.workers.dev';
let found=0,old=0;
for(let i=0;i<50;i++){
  const response=await fetch(origin+'/vincular',{headers:{'cache-control':'no-cache'},
    signal:AbortSignal.timeout(12000)});
  if(response.status===404){old++;continue;}
  assert.equal(response.status,200,`Unexpected /vincular status: ${response.status}`);
  const html=await response.text();
  assert.match(html,/Vincular seu computador/);
  assert.match(html,/name="device_id"/);
  assert.match(html,/name="code"/);
  assert.match(html,/action="\/vincular"/);
  assert.match(response.headers.get('cache-control')||'',/no-store/);
  found++;
  if(found>=3)break;
}
assert.ok(found>=1,`New portal never appeared: old=${old}, new=${found}`);
console.log('LIVE CANARY OK: portal status=200, html fields verified, new=',found,'old=',old);
console.log('Only GET was used; no code claim, OAuth token or Windows command.');

const fakeId='audit_'+crypto.randomUUID().replaceAll('-','');
const form=new URLSearchParams({device_id:fakeId,code:'000000'});
const rejected=await fetch(origin+'/vincular',{
  method:'POST',
  headers:{'content-type':'application/x-www-form-urlencoded',
           'origin':origin},
  body:form,
  signal:AbortSignal.timeout(12000),
});
assert.equal(rejected.status,400,'An unknown device/code must be rejected by the actual backend');
assert.match(await rejected.text(),/incorreto, expirado ou bloqueado/);
console.log('LIVE POST OK: fictitious device rejected (400), no OAuth grant, no Windows touched.');
