import test from 'node:test';
import assert from 'node:assert/strict';
import {pairingEntryPage,PLUGIN_URL} from '../src/pairing-entry.mjs';

test('página pública mostra campos e envio POST sem expor código na URL',()=>{
  const html=pairingEntryPage();
  assert.match(html,/<form method="POST" action="\/vincular">/);
  assert.match(html,/name="device_id"/);
  assert.match(html,/name="code"/);
  assert.match(html,/pattern="\[0-9\]\{6\}"/);
  assert.match(html,/Não compartilhe o código/);
  assert.ok(html.includes(PLUGIN_URL));
});
test('entrada potencialmente maliciosa é escapada no HTML',()=>{
  const html=pairingEntryPage({deviceId:'"><script>alert(1)</script>',
    error:'<img src=x onerror=alert(1)>'});
  assert.doesNotMatch(html,/<script>alert/);
  assert.doesNotMatch(html,/<img src=x/);
  assert.match(html,/&lt;script&gt;/);
  assert.match(html,/&lt;img/);
});
test('verificação positiva não afirma autorização, nem reproduz código',()=>{
  const html=pairingEntryPage({verified:true,deviceId:'device_abcdefgh1234'});
  assert.match(html,/NÃO autorizou acesso/);
  assert.match(html,/OAuth/);
  assert.doesNotMatch(html,/001234/);
});
