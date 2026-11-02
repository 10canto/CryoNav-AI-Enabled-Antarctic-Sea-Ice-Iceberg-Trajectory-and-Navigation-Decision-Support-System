import { useEffect } from 'react';
import { useStore } from '../store/useStore';

export function useKeyboardShortcuts(onOpenShortcuts: () => void) {
  const next = useStore((s) => s.next);
  const prev = useStore((s) => s.prev);
  const reset = useStore((s) => s.reset);
  const mode = useStore((s) => s.mode);
  const scenario = useStore((s) => s.scenario);

  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      // Ignore shortcuts when typing in inputs
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;

      // Only navigation shortcuts work in demo mode
      if (mode === 'demo' && scenario) {
        if (e.key === 'ArrowRight') {
          e.preventDefault();
          next();
        } else if (e.key === 'ArrowLeft') {
          e.preventDefault();
          prev();
        } else if (e.key === 'r' || e.key === 'R') {
          e.preventDefault();
          reset();
        }
      }

      // D for dev overlay (handled by DevOverlay itself)
      // ? for shortcuts
      if (e.key === '?' && !e.shiftKey) {
        e.preventDefault();
        onOpenShortcuts();
      }
    };

    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, [next, prev, reset, mode, scenario, onOpenShortcuts]);
}
