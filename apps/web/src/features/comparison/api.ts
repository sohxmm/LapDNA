import type { components } from '../../../../../packages/contracts/api';

type Schema = components['schemas'];
type JsonObject = Record<string, unknown>;
function object(value: unknown): value is JsonObject {
  return typeof value === 'object' && value !== null;
}
const supportedVersion = (value:unknown) => value === '1.2.0' || value === '1.3.0';

async function request(path: string, init: RequestInit): Promise<JsonObject> {
  const response = await fetch('/api/v1/' + path, init);
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = object(body) && object(body.error) ? body.error : null;
    throw new Error(typeof detail?.message === 'string' ? detail.message : 'The data service returned HTTP ' + response.status + '.');
  }
  if (!object(body)) throw new Error('The data service returned an unreadable response.');
  return body;
}

export async function loadSessions(signal: AbortSignal): Promise<Schema['SessionInventory']> {
  const body = await request('sessions', { signal });
  if (!supportedVersion(body.schema_version) || !Array.isArray(body.sessions)) throw new Error('Unsupported session inventory.');
  return body as Schema['SessionInventory'];
}

export async function loadLaps(sessionId: string, signal: AbortSignal): Promise<Schema['SessionLapIndex']> {
  const body = await request('sessions/' + encodeURIComponent(sessionId) + '/laps', { signal });
  if (!supportedVersion(body.schema_version) || !Array.isArray(body.drivers) || !Array.isArray(body.laps)
    || !object(body.session) || body.session.session_id !== sessionId) throw new Error('Unsupported lap inventory.');
  return body as Schema['SessionLapIndex'];
}

export async function compareLaps(input: Schema['CompareRequest'], signal: AbortSignal): Promise<Schema['CompareResponse']> {
  const body = await request('compare', { signal, method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(input) });
  const artifact = body.artifact;
  if (typeof body.swapped !== 'boolean' || !object(artifact) || !supportedVersion(artifact.schema_version)
    || !['telemetry','sector_only'].includes(String(artifact.detail_level)) || !object(artifact.lap_a) || !object(artifact.lap_b)
    || !object(artifact.session) || artifact.session.session_id !== input.session_id
    || (body.swapped ? artifact.lap_b : artifact.lap_a).lap_id !== input.lap_a_id
    || (body.swapped ? artifact.lap_a : artifact.lap_b).lap_id !== input.lap_b_id) {
    throw new Error('The data service returned a result for an unsupported selection.');
  }
  return body as Schema['CompareResponse'];
}
