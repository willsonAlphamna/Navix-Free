import {configFromEnv} from './auth.mjs';

/** RFC 9728 protected resource metadata for ChatGPT MCP OAuth discovery. */
export function protectedResourceMetadata(env,requestUrl) {
  const {issuer,audience}=configFromEnv(env);
  const base=new URL(requestUrl);
  if(base.protocol!=='https:') throw new Error('HTTPS obrigatório');
  return {
    resource:audience,
    authorization_servers:[issuer],
    scopes_supported:['navix:control'],
    bearer_methods_supported:['header'],
    resource_documentation:'https://github.com/willsonAlphamna/Navix-Free/blob/main/desktop/README.md',
  };
}

export function oauthChallenge(env,requestUrl) {
  const url=new URL(requestUrl);
  const metadata=url.origin+'/.well-known/oauth-protected-resource';
  if(url.protocol!=='https:') throw new Error('HTTPS obrigatório');
  configFromEnv(env);
  return 'Bearer resource_metadata="'+metadata+'", scope="navix:control"';
}
