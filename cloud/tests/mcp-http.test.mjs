import test from 'node:test';
import assert from 'node:assert/strict';
import {handleMcp,MCP_INSTRUCTIONS,validateToolArguments} from '../src/mcp-http.mjs';
import {PUBLIC_TOOLS} from '../src/tool-schemas.mjs';

const request=(method,params={})=>new Request('https://navix.test/mcp',{
  method:'POST',headers:{'content-type':'application/json'},
  body:JSON.stringify({jsonrpc:'2.0',id:7,method,params}),
});
const invoke=async (method,params,execute=async()=>({content:[{type:'text',text:'ok'}]}))=>{
  const result=await handleMcp(request(method,params),{execute});
  return [result.status,await result.json()];
};

test('expõe 44 ferramentas com schemas reais sem argumentos arbitrários',()=>{
  assert.equal(PUBLIC_TOOLS.length,44);
  for(const tool of PUBLIC_TOOLS){
    assert.equal(tool.inputSchema.type,'object');
    assert.equal(tool.inputSchema.additionalProperties,false);
    assert.ok(tool.description);
    assert.deepEqual(tool._meta.securitySchemes[0].scopes,['navix:control']);
  }
  assert.match(MCP_INSTRUCTIONS,/Conector MCP do NavixX Desktop/);
});
test('inicialização e tools/list usam protocolo MCP Streamable HTTP',async()=>{
  const [status,body]=await invoke('initialize',{protocolVersion:'2025-06-18'});
  assert.equal(status,200);
  assert.equal(body.result.protocolVersion,'2025-06-18');
  const [_,list]=await invoke('tools/list');
  assert.equal(list.result.tools.length,44);
});
test('chamada MCP valida campos e devolve o resultado da ferramenta real',async()=>{
  const calls=[];
  const [status,body]=await invoke('tools/call',{name:'desktop_click',
    arguments:{x:123,y:456}},async(name,args)=>{
      calls.push([name,args]);return {content:[{type:'text',text:'clicked'}]};
    });
  assert.equal(status,200);
  assert.deepEqual(calls,[['desktop_click',{x:123,y:456}]]);
  assert.equal(body.result.content[0].text,'clicked');
  assert.throws(()=>validateToolArguments('desktop_click',{x:2,y:2,root:'/'}));
  assert.throws(()=>validateToolArguments('command_exec',{argv:'rm -rf'}));
  assert.throws(()=>validateToolArguments('missing_tool',{}));
});
test('não executa ferramenta com args inválidos nem método MCP desconhecido',async()=>{
  let invoked=false;
  const [_,bad]=await invoke('tools/call',{name:'files_delete',arguments:{path:12}},
    async()=>{invoked=true;});
  assert.equal(bad.error.code,-32602);
  assert.equal(invoked,false);
  const [__,unknown]=await invoke('change_everything');
  assert.equal(unknown.error.code,-32601);
});
