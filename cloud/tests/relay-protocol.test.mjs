import test from 'node:test';
import assert from 'node:assert/strict';
import {TOOL_NAMES, requiredPermission, makeCall, parseReply, PendingCalls} from '../src/relay-protocol.mjs';

test('catálogo preserva exatamente 44 nomes sem duplicidade',()=>{
  assert.equal(TOOL_NAMES.length,44);
  assert.equal(new Set(TOOL_NAMES).size,44);
  assert.equal(requiredPermission('status'),null);
  assert.equal(requiredPermission('command_exec'),'commands');
  assert.equal(requiredPermission('browser_open'),'browser');
  assert.equal(requiredPermission('desktop_type'),'desktop');
  assert.equal(requiredPermission('files_delete'),'files');
  assert.throws(()=>requiredPermission('system_admin'),/desconhecida/);
});
test('aceita chamada válida e recusa comandos fora da whitelist',()=>{
  const call=makeCall({tool:'status'});
  assert.equal(call.kind,'call');
  assert.match(call.id,/^[0-9a-f-]{36}$/);
  assert.throws(()=>makeCall({tool:'os_execute'}),/desconhecida/);
  assert.throws(()=>makeCall({tool:'files_read',args:[]}),/Argumentos/);
});
test('limita payload e deadline de mensagens',()=>{
  assert.throws(()=>makeCall({tool:'desktop_type',args:{text:'x'.repeat(9_000_000)}}),/grande/);
  assert.throws(()=>makeCall({tool:'status',deadline:Date.now()-10}),/Prazo/);
  assert.throws(()=>makeCall({tool:'status',deadline:Date.now()+120_000}),/Prazo/);
});
test('valida tipo, ID e tamanho das respostas',()=>{
  const id='12345678-1234-1234-1234-123456789012';
  assert.equal(parseReply(JSON.stringify({kind:'result',id,ok:true,result:{active:true}})).result.active,true);
  assert.throws(()=>parseReply('{'),/JSON/);
  assert.throws(()=>parseReply(JSON.stringify({kind:'call',id,ok:true})),/Formato/);
  assert.throws(()=>parseReply(JSON.stringify({kind:'result',id,ok:true})),/Resultado/);
  assert.throws(()=>parseReply(JSON.stringify({kind:'result',id,ok:false,error:42})),/remoto/);
  assert.throws(()=>parseReply('x'.repeat(12*1024*1024+1)),/excessiva/);
});
test('resposta correspondente resolve a requisição',async()=>{
  const sent=[];
  const pool=new PendingCalls({send: frame=>sent.push(JSON.parse(frame))});
  const pending=pool.call('browser_tabs');
  assert.equal(sent.length,1);
  assert.equal(pool.accept(JSON.stringify({kind:'result',id:sent[0].id,ok:true,result:['aba']})),true);
  assert.deepEqual(await pending,['aba']);
  pool.close();
});
test('resposta de ID inexistente nunca encerra chamada pendente',async()=>{
  const sent=[];
  const pool=new PendingCalls({send:frame=>sent.push(JSON.parse(frame))});
  const pending=pool.call('status');
  assert.equal(pool.accept(JSON.stringify({kind:'result',id:'12345678-1234-1234-1234-123456789012',ok:true,result:'falso'})),false);
  pool.accept(JSON.stringify({kind:'result',id:sent[0].id,ok:true,result:'verdadeiro'}));
  assert.equal(await pending,'verdadeiro');
  pool.close();
});
test('impede duas ações paralelas sobre o mesmo desktop',async()=>{
  const sent=[];
  const pool=new PendingCalls({send:frame=>sent.push(JSON.parse(frame))});
  const pending=pool.call('desktop_click',{x:10,y:10});
  await assert.rejects(pool.call('files_write',{path:'x'}),/ocupado/);
  pool.accept(JSON.stringify({kind:'result',id:sent[0].id,ok:true,result:{ok:true}}));
  await pending;
  pool.close();
});
test('erro vindo do agente rejeita chamada sem executar fallback',async()=>{
  const sent=[];
  const pool=new PendingCalls({send:frame=>sent.push(JSON.parse(frame))});
  const pending=pool.call('command_run',{command:'echo test'});
  pool.accept(JSON.stringify({kind:'result',id:sent[0].id,ok:false,error:'permissão revogada'}));
  await assert.rejects(pending,/revogada/);
  pool.close();
});
test('desconexão cancela chamadas e impede novos comandos',async()=>{
  const pool=new PendingCalls({send:()=>{}});
  const pending=pool.call('status');
  pool.close();
  await assert.rejects(pending,/desconectado/);
  await assert.rejects(pool.call('status'),/desconectado/);
  assert.equal(pool.pending.size,0);
});
test('falha de envio remove pendência imediatamente',async()=>{
  const pool=new PendingCalls({send:()=>{throw new Error('desconectou')}});
  await assert.rejects(pool.call('status'),/envio/);
  assert.equal(pool.pending.size,0);
  pool.close();
});
test('timeout expira e remove chamada antiga',async()=>{
  const pool=new PendingCalls({send:()=>{}});
  await assert.rejects(pool.call('status',{},100),/Tempo limite/);
  assert.equal(pool.pending.size,0);
  pool.close();
});
