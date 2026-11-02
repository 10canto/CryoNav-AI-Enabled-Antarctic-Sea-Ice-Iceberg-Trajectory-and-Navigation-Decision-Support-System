/**
 * Network Request Monitor
 * Logs all network requests in dev mode using PerformanceObserver
 */

let requestLog: Array<{ url: string; time: string; type: string }> = [];
let observer: PerformanceObserver | null = null;

export function startNetworkMonitoring() {
  if (import.meta.env.PROD) return; // Only in dev mode
  
  requestLog = [];
  
  try {
    observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'resource') {
          const resourceEntry = entry as PerformanceResourceTiming;
          const url = resourceEntry.name;
          const time = new Date().toISOString();
          const type = resourceEntry.initiatorType;
          
          requestLog.push({ url, time, type });
          console.log(`[Network] ${type}: ${url} at ${time}`);
        }
      });
    });
    
    observer.observe({ entryTypes: ['resource'] });
    console.log('[Network Monitor] Started - logging all requests');
  } catch (error) {
    console.warn('[Network Monitor] Not supported:', error);
  }
}

export function stopNetworkMonitoring() {
  if (observer) {
    observer.disconnect();
    observer = null;
  }
}

export function getRequestLog() {
  return [...requestLog];
}

export function clearRequestLog() {
  requestLog = [];
}
