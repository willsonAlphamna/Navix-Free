import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const catalog = readFileSync(new URL('../MCP_CATALOG.md', import.meta.url),'utf8');

test('catálogo público conserva exatamente 44 ferramentas e a descrição do proprietário', () => {
  const names = [...catalog.matchAll(/^- \`([a-z][a-z0-9_]*)\`$/gm)].map(row => row[1]);
  assert.equal(names.length,44);
  assert.equal(new Set(names).size,44);
  for (const tool of ['status','desktop_screenshot','desktop_click','desktop_type',
                      'browser_start','browser_open','browser_screenshot',
                      'files_read','files_delete','command_run','command_exec']) {
    assert.ok(names.includes(tool),tool);
  }
  assert.ok(catalog.includes('Conector MCP do NavixX Desktop'));
  assert.ok(catalog.includes('PowerShell, CMD e Python'));
});
