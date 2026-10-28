import {createRemoteJWKSet, jwtVerify} from 'jose';

function secureAddress(value, label) {
  if (typeof value !== 'string' || !value) throw new Error(label + ' não configurado.');
  const parsed = new URL(value);
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password) {
    throw new Error(label + ' exige HTTPS sem credenciais na URL.');
  }
  return parsed;
}
export function readBearer(request) {
  const authorization = request.headers.get('authorization') || '';
  const match = /^Bearer ([A-Za-z0-9_~+/=.-]+)$/.exec(authorization);
  if (!match || match[1].length > 8192) throw new Error('Bearer ausente ou inválido.');
  return match[1];
}
export function configFromEnv(env) {
  const issuer = secureAddress(env.OIDC_ISSUER, 'OIDC_ISSUER').href.replace(/\/$/, '');
  const audience = secureAddress(env.OIDC_AUDIENCE, 'OIDC_AUDIENCE').href.replace(/\/$/, '');
  const jwksUrl = secureAddress(env.OIDC_JWKS_URL, 'OIDC_JWKS_URL');
  return {issuer, audience, jwksUrl};
}
export async function verifyOAuthToken(token, keySet, {issuer, audience, requiredScope}) {
  const {payload} = await jwtVerify(token, keySet, {
    issuer, audience, algorithms: ['RS256', 'ES256'], clockTolerance: 5,
  });
  if (typeof payload.sub !== 'string' || !payload.sub || payload.sub.length > 256) {
    throw new Error('Identidade não verificada.');
  }
  const scopes = typeof payload.scope === 'string' ? payload.scope.split(/\s+/) : [];
  if (!scopes.includes(requiredScope)) throw new Error('Escopo não autorizado.');
  return {ownerId: payload.sub, scopes};
}
export async function authenticate(request, env, requiredScope) {
  const config = configFromEnv(env);
  const keySet = createRemoteJWKSet(config.jwksUrl);
  return verifyOAuthToken(readBearer(request), keySet, {...config, requiredScope});
}
