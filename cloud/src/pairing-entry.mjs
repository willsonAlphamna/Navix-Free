/** Public, bounded preflight for a device code.
 * Checking does not issue OAuth tokens or authorize a Windows session.
 */
const esc = value => String(value).replace(/[&<>"']/g, c => ({
  '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;',
}[c]));
export const PLUGIN_URL='https://chatgpt.com/plugins/Plugin_155473c5545c819185cd0e8ace28143f';

export function pairingEntryPage({verified=false,error='',deviceId=''}={}) {
  return `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Vincular computador — NavixX Cloud</title>
<style>
body{font:16px system-ui,sans-serif;background:#0b1120;color:#eef6ff;min-height:95vh;display:grid;place-items:center}
main{box-sizing:border-box;width:min(490px,94vw);background:#152238;border:1px solid #385475;border-radius:16px;padding:22px}
label{display:block;margin:12px 0}input{box-sizing:border-box;width:100%;font:inherit;padding:12px;margin-top:6px;border-radius:8px}
button,a.action{display:block;box-sizing:border-box;background:#2878f0;color:#fff;border:0;border-radius:8px;padding:13px;width:100%;font:inherit;font-weight:700;text-align:center;text-decoration:none;cursor:pointer}
small{color:#bacbe3}.ok{color:#8be6c0}.error{color:#ffb1bc}p{line-height:1.45}
</style></head><body><main>
<h1>Vincular seu computador</h1><p>Digite o ID e o código de seis números mostrados em <strong>NavixX Desktop Cloud → Vincular ao ChatGPT</strong>.</p>
${verified?'<p class="ok" role="status">Código reconhecido pelo servidor NavixX Cloud. Esta verificação NÃO autorizou acesso ao computador.</p>':''}
${error?`<p class="error" role="alert">${esc(error)}</p>`:''}
<form method="POST" action="/vincular">
<label for="device">ID do computador</label><input id="device" name="device_id" value="${esc(deviceId)}" required minlength="16" maxlength="128" pattern="[A-Za-z0-9_-]{16,128}" autocomplete="off">
<label for="code">Código temporário (6 números)</label><input id="code" name="code" required maxlength="6" pattern="[0-9]{6}" inputmode="numeric" autocomplete="one-time-code">
<button type="submit">Verificar código no NavixX Cloud</button></form>
<p><small>O código expira em até 2 minutos. Após a verificação, é necessário concluir a autorização OAuth dentro do plugin ChatGPT, usando os mesmos dados se solicitados. Não compartilhe o código nem o coloque na URL.</small></p>
<a class="action" href="${PLUGIN_URL}" rel="noopener noreferrer">Abrir plugin NavixX Desktop Cloud</a>
<p><small>O vínculo e o acesso remoto somente são confirmados depois da autorização no ChatGPT e de uma chamada real ao computador. Não é necessário criar chave nova ou usar o ConectaX.</small></p>
</main></body></html>`;
}
