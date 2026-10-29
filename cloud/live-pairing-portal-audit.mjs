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
