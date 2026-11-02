/**
 * Resource Cache
 * In-memory cache for scenario.json, geojson, etc. to prevent repeated requests
 */

const cache = new Map<string, any>();

export async function fetchOnce<T>(url: string): Promise<T> {
  if (cache.has(url)) {
    console.log(`[Cache] Hit: ${url}`);
    return cache.get(url);
  }
  
  console.log(`[Cache] Miss: ${url}`);
  const response = await fetch(url);
  const data = await response.json();
  cache.set(url, data);
  return data;
}

export function clearCache() {
  cache.clear();
}

export function getCacheSize() {
  return cache.size;
}
