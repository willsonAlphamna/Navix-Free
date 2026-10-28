import {PUBLIC_TOOLS} from './tool-schemas.mjs';
import {TOOL_SET} from './relay-protocol.mjs';

export const MCP_VERSION='2025-06-18';
export const CLOUD_STATUS_TOOL = Object.freeze({
  name: 'navixx_cloud_connection_status',
  title: 'NavixX Cloud — verificar conexão',
  description: 'Use para verificar EXCLUSIVAMENTE o NavixX Desktop Cloud, nunca o conectaX ou NavixX Desktop antigo. Informa se este plugin foi autorizado, se o gateway Cloud está liberado e se o Windows mantém um canal WebSocket ativo. É leitura apenas: não executa comandos no PC nem comprova controle remoto de ponta a ponta.',
  inputSchema: {type:'object',properties:{},required:[],additionalProperties:false},
  annotations: {readOnlyHint:true,destructiveHint:false,openWorldHint:false},
  securitySchemes: [{type:'oauth2',scopes:['navix:control']}],
});
export const ADVERTISED_TOOLS = Object.freeze([CLOUD_STATUS_TOOL,...PUBLIC_TOOLS]);


const MAX_INPUT=8*1024*1024;
const error=(id,code,message)=>({jsonrpc:'2.0',id,error:{code,message}});
const reply=(id,result)=>({jsonrpc:'2.0',id,result});
export const MCP_INSTRUCTIONS='Este é o NavixX Desktop Cloud, independente do conectaX e do NavixX Desktop antigo. Para perguntas de conexão use primeiro navixx_cloud_connection_status: um canal WebSocket ativo NÃO comprova comando executado no Windows. Para confirmar controle remoto, execute somente a ferramenta status do próprio NavixX Cloud com permissão do titular. Se o serviço não estiver vinculado, explique o bloqueio; nunca substitua silenciosamente pelo conectaX.';

export function validateToolArguments(name,args){
  if(name===CLOUD_STATUS_TOOL.name){
    if(!args||typeof args!=='object'||Array.isArray(args)||Object.keys(args).length){
      throw new Error('Argumentos inválidos para o estado do NavixX Cloud');
    }
    return args;
  }
  const spec=PUBLIC_TOOLS.find(item=>item.name===name);
  if(!spec||!TOOL_SET.has(name))throw new Error('Ferramenta desconhecida');
  if(!args||typeof args!=='object'||Array.isArray(args))throw new Error('Argumentos inválidos');
  const {properties,required}=spec.inputSchema;
  for(const key of required){if(!Object.hasOwn(args,key))throw new Error('Argumento obrigatório ausente');}
  for(const [key,value] of Object.entries(args)){
    if(!Object.hasOwn(properties,key))throw new Error('Argumento não reconhecido');
    const type=properties[key].type;
    if(!((type==='string'&&typeof value==='string')||
          (type==='integer'&&Number.isSafeInteger(value))||
          (type==='number'&&typeof value==='number'&&Number.isFinite(value))||
          (type==='boolean'&&typeof value==='boolean')||
          (type==='array'&&Array.isArray(value)&&value.every(x=>
             properties[key].items.type==='string'&&typeof x==='string')))){
      throw new Error('Tipo de argumento inválido');
    }
  }
  return args;
}

export async function handleMcp(request,{execute,allowRemoteTools=true}={}){
  if(request.method!=='POST')return new Response(null,{status:405,headers:{Allow:'POST'}});
  let body;
  try {
    const text=await request.text();
    if(new TextEncoder().encode(text).length>MAX_INPUT)throw new Error('Tamanho excedido');
    body=JSON.parse(text);
    if(!body||typeof body!=='object'||Array.isArray(body)||body.jsonrpc!=='2.0'||
        typeof body.method!=='string')throw new Error('Requisição inválida');
  } catch {return new Response(JSON.stringify(error(null,-32700,'JSON inválido')),{status:400,
    headers:{'content-type':'application/json','cache-control':'no-store'}});}
  const id=body.id??null;
  let response;
  try {
    if(body.method==='initialize'){
      const requested=body.params?.protocolVersion;
      if(typeof requested!=='string')throw new Error('Versão do protocolo ausente');
      response=reply(id,{protocolVersion:MCP_VERSION,
        capabilities:{tools:{listChanged:false}},serverInfo:{name:'NavixX Cloud',version:'0.3.0'},
        instructions:MCP_INSTRUCTIONS});
    }else if(body.method==='notifications/initialized'){
      return new Response(null,{status:202});
    }else if(body.method==='tools/list'){
      response=reply(id,{tools:allowRemoteTools?ADVERTISED_TOOLS:[CLOUD_STATUS_TOOL]});
    }else if(body.method==='tools/call'){
      const name=body.params?.name,args=body.params?.arguments??{};
      validateToolArguments(name,args);
      if(!allowRemoteTools && name!==CLOUD_STATUS_TOOL.name){
        response=error(id,-32003,'Controle remoto do NavixX Cloud indisponível neste servidor ou dispositivo.');
      }else{
      const result=await execute(name,args);
      response=reply(id,result&&Array.isArray(result.content)?result:
        {content:[{type:'text',text:JSON.stringify(result)}]});
      }
    }else{
      response=error(id,-32601,'Método MCP desconhecido');
    }
  } catch(e){
    response=error(id,-32602,e instanceof Error&&/Argumento|Ferramenta|Tipo/.test(e.message)?
      'Parâmetros MCP inválidos':'Ferramenta indisponível');
  }
  return new Response(JSON.stringify(response),{status:200,headers:{
    'content-type':'application/json; charset=utf-8','cache-control':'no-store',
    'mcp-protocol-version':MCP_VERSION,
  }});
}
