import { useEffect, useRef } from 'react';
import { REFRESH_INTERVAL } from '../config';

export const usePolling = (callback, dependencies = [], isPaused = false) => {
  const savedCallback = useRef();
  
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);
  
  useEffect(() => {
    if (isPaused) return; // Don't poll during transitions
    
    const tick = () => {
      savedCallback.current();
    };
    
    // Call immediately on mount
    tick();
    
    // Then set up interval
    const id = setInterval(tick, REFRESH_INTERVAL);
    
    return () => clearInterval(id);
  }, [...dependencies, isPaused]);
};
