import type { components } from '../../../packages/contracts/api';

export type Catalog = components['schemas']['Catalog'];

export async function fetchCatalog(signal: AbortSignal): Promise<Catalog> {
  const response = await fetch('/api/v1/catalog', { signal });
  if (!response.ok) throw new Error(`Catalogue request failed (${response.status}).`);
  const data: unknown = await response.json();
  // Full telemetry validation stays on the API. Guard the shell against an incompatible server.
  if (!data || typeof data !== 'object' || !('schema_version' in data)
    || data.schema_version !== '1.1.0' || !('comparisons' in data)
    || !Array.isArray(data.comparisons)) {
    throw new Error('The API returned an unsupported catalogue.');
  }
  return data as Catalog;
}
