import { lazy, Suspense, useEffect, useState } from 'react';
import { AlertModal } from './components/AlertModal';
import { ExplainPanel } from './components/ExplainPanel';
import { Footer } from './components/Footer';
import { MapView } from './components/MapView';
import { NarrationBar } from './components/NarrationBar';
import { RiskCard } from './components/RiskCard';
import { RouteTable } from './components/RouteTable';
import { ShortcutsModal } from './components/ShortcutsModal';
import { Timeline } from './components/Timeline';
import { TopBar } from './components/TopBar';
import { WhatsRealModal } from './components/WhatsRealModal';
import { WhatIfPanel } from './components/WhatIfPanel';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useStore } from './store/useStore';

// Dev-only overlay: the condition is a build-time constant, so it is dropped from production builds.
const DevOverlay = import.meta.env.DEV ? lazy(() => import('./dev/DevOverlay')) : null;

export default function App() {
  const init = useStore((s) => s.init);
  const warning = useStore((s) => s.warning);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [whatsRealOpen, setWhatsRealOpen] = useState(false);

  useKeyboardShortcuts(() => setShortcutsOpen(true));

  useEffect(() => {
    void init(); // first (and only automatic) data load: /demo/scenario.json
  }, [init]);

  return (
    <div className="app">
      <TopBar onOpenShortcuts={() => setShortcutsOpen(true)} onOpenWhatsReal={() => setWhatsRealOpen(true)} />
      <NarrationBar />
      <main className="main">
        <section className="left">
          <MapView />
          <Timeline />
        </section>
        <aside className="right">
          {warning && <div className="notice" role="status">{warning}</div>}
          <RiskCard />
          <RouteTable />
          <ExplainPanel />
          <WhatIfPanel />
        </aside>
      </main>
      <Footer />
      <AlertModal />
      <ShortcutsModal open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
      <WhatsRealModal open={whatsRealOpen} onClose={() => setWhatsRealOpen(false)} />
      {DevOverlay && (
        <Suspense fallback={null}>
          <DevOverlay />
        </Suspense>
      )}
    </div>
  );
}
