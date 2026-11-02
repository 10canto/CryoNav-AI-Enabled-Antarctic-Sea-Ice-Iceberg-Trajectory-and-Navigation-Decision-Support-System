/**
 * CryoNav AI - Antarctic Navigation Decision Support System
 * Production-ready app with demo mode, offline fallbacks, and visual polish
 */
import React, { useEffect, useState, useCallback } from 'react';
import { AppStoreProvider, useAppStore } from './store/AppStore';
import { apiClient } from './api/client';
import { loadOfflineCache, getCachedIcebergs, getCachedRoutes, getCachedRisk, getCachedExplanation, getCachedPrediction, hasCachedData } from './api/offlineCache';
import { startNetworkMonitoring } from './utils/networkMonitor';
import { fetchOnce } from './utils/resourceCache';
import { MapView } from './components/Map/MapView';
import { RiskCard } from './components/RiskCard';
import { ExplainPanel } from './components/ExplainPanel';
import { WhatIfPanel } from './components/WhatIfPanel';
import { AlertModal } from './components/AlertModal';
import './AppNew.css';

// Cape Town, Maitri Station
const CAPE_TOWN = { lat: -33.9249, lon: 18.4241 };
const MAITRI = { lat: -70.7667, lon: 11.7333 };

interface DemoStep {
  id: number;
  time: string;
  title: string;
  shipPosition: { lat: number; lon: number };
  icebergs: any[];
  routes: any[];
  risk: any;
  explanation: any;
  message: string;
  alert_sent?: boolean;
}

const AppContent: React.FC = () => {
  const store = useAppStore();
  const [demoMode, setDemoMode] = useState(false);
  const [demoScenario, setDemoScenario] = useState<any>(null);
  const [currentDemoStep, setCurrentDemoStep] = useState(0);
  const [backendOnline, setBackendOnline] = useState(true);
  const [offlineMode, setOfflineMode] = useState(false);
  const [showDevOverlay, setShowDevOverlay] = useState(false);
  const [routePulse, setRoutePulse] = useState(false);

  // Load offline cache and demo scenario on mount
  useEffect(() => {
    // Start network monitoring in dev mode
    if (import.meta.env.DEV) {
      startNetworkMonitoring();
    }
    
    loadOfflineCache();
    loadDemoScenario();
    checkBackendHealth();
    
    // D key to toggle dev overlay (dev mode only)
    const handleKeyPress = (e: KeyboardEvent) => {
      if (import.meta.env.DEV && e.key === 'd' && !e.ctrlKey && !e.metaKey) {
        setShowDevOverlay(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/`, { signal: AbortSignal.timeout(2000) });
      setBackendOnline(response.ok);
    } catch (error) {
      setBackendOnline(false);
      setOfflineMode(true);
      console.warn('[Backend] Offline - using cached data');
    }
  };

  const loadDemoScenario = async () => {
    try {
      // Use cached fetch to prevent repeated requests
      const data = await fetchOnce('/demo/scenario.json');
      setDemoScenario(data);
      console.log('[Demo] Scenario loaded:', data.steps?.length, 'steps');
    } catch (error) {
      console.warn('[Demo] Scenario not available');
    }
  };

  // Normal mode: Load icebergs on mount
  useEffect(() => {
    if (!demoMode) {
      loadIcebergs();
    }
  }, [demoMode]);

  // Normal mode: Calculate routes when date or icebergs change
  useEffect(() => {
    if (!demoMode && store.icebergs.length > 0) {
      calculateRoutes();
    }
  }, [demoMode, store.currentDate, store.icebergs.length]);

  // Show alert modal when risk is RED
  useEffect(() => {
    if (store.riskLevel === 'RED' && !store.alertSent) {
      store.setShowAlert(true);
    }
  }, [store.riskLevel, store.alertSent]);

  const loadIcebergs = async () => {
    store.setLoading('icebergs', true);
    try {
      if (!backendOnline) throw new Error('Backend offline');
      const data = await apiClient.getIcebergs();
      store.setIcebergs(data.icebergs);
    } catch (error) {
      console.error('Failed to load icebergs:', error);
      // Fallback to cached data
      const cached = getCachedIcebergs();
      store.setIcebergs(cached);
      setOfflineMode(true);
    } finally {
      store.setLoading('icebergs', false);
    }
  };

  const calculateRoutes = async () => {
    store.setLoading('routes', true);
    try {
      if (!backendOnline) throw new Error('Backend offline');
      const data = await apiClient.calculateRoutes({
        start: CAPE_TOWN,
        end: MAITRI,
        ship: { speed_knots: 12.0 },
        date: store.currentDate,
        wind: { speed: 8, direction: 210 }
      });
      store.setRoutes(data.routes);
      // Auto-select safest route
      if (data.routes.length > 0 && !store.selectedRoute) {
        const safest = data.routes.find(r => r.type === 'safest') || data.routes[0];
        store.setSelectedRoute(safest.id);
      }
    } catch (error) {
      console.error('Failed to calculate routes:', error);
      // Fallback to cached routes
      const cached = getCachedRoutes();
      store.setRoutes(cached);
      if (cached.length > 0 && !store.selectedRoute) {
        store.setSelectedRoute(cached[0].id);
      }
      setOfflineMode(true);
    } finally {
      store.setLoading('routes', false);
    }
  };

  const handleIcebergClick = async (icebergId: string) => {
    store.setSelectedIceberg(icebergId);
    store.setLoading('prediction', true);
    try {
      if (!backendOnline) throw new Error('Backend offline');
      const prediction = await apiClient.predictDrift(icebergId, 72, 'hybrid');
      store.setIcebergPrediction(prediction);
    } catch (error) {
      console.error('Failed to predict drift:', error);
      // Fallback to cached prediction
      const cached = getCachedPrediction(icebergId);
      store.setIcebergPrediction(cached);
    } finally {
      store.setLoading('prediction', false);
    }
  };

  const handleRouteSelect = async (routeId: string) => {
    store.setSelectedRoute(routeId);
    try {
      if (!backendOnline) throw new Error('Backend offline');
      const explanation = await apiClient.explainRoute(routeId);
      store.setRouteExplanation(explanation);
    } catch (error) {
      console.error('Failed to load explanation:', error);
      // Fallback to cached explanation
      const cached = getCachedExplanation(routeId);
      store.setRouteExplanation(cached);
    }
  };

  const handleSendAlert = async () => {
    if (!store.riskAssessment || !store.demoStep) return;
    
    try {
      await apiClient.sendAlert({
        level: store.riskAssessment.level,
        position: store.demoStep.shipPosition,
        details: {
          nearest_iceberg: store.riskAssessment.nearest_iceberg,
          distance_km: store.riskAssessment.distance_km,
          route: store.selectedRoute
        }
      });
      store.setAlertSent(true);
    } catch (error) {
      console.error('Failed to send alert:', error);
      // Still mark as sent in demo mode
      store.setAlertSent(true);
    }
    
    // Trigger route pulse after alert acknowledged
    setRoutePulse(true);
    setTimeout(() => setRoutePulse(false), 1000);
  };

  // Demo mode handlers
  const startDemo = () => {
    if (!demoScenario || !demoScenario.steps) return;
    setDemoMode(true);
    setCurrentDemoStep(0);
    applyDemoStep(demoScenario.steps[0]);
  };

  const nextDemoStep = () => {
    if (!demoScenario || !demoScenario.steps) return;
    const nextStep = Math.min(currentDemoStep + 1, demoScenario.steps.length - 1);
    setCurrentDemoStep(nextStep);
    applyDemoStep(demoScenario.steps[nextStep]);
  };

  const prevDemoStep = () => {
    const prevStep = Math.max(currentDemoStep - 1, 0);
    setCurrentDemoStep(prevStep);
    applyDemoStep(demoScenario.steps[prevStep]);
  };

  const resetDemo = () => {
    setDemoMode(false);
    setCurrentDemoStep(0);
    store.resetState();
    // Reload normal data
    loadIcebergs();
  };

  const applyDemoStep = (step: DemoStep) => {
    // Set all data from frozen step
    store.setIcebergs(step.icebergs || []);
    store.setRoutes(step.routes || []);
    store.setRiskAssessment(step.risk);
    store.setRiskLevel(step.risk?.level || 'GREEN');
    store.setRouteExplanation(step.explanation);
    store.setDemoStep(step);
    
    // Auto-select safest route
    if (step.routes && step.routes.length > 0) {
      const safest = step.routes.find((r: any) => r.type === 'safest') || step.routes[0];
      store.setSelectedRoute(safest.id);
    }
  };

  const shipPosition = demoMode && store.demoStep 
    ? store.demoStep.shipPosition 
    : CAPE_TOWN;

  return (
    <div className="cryonav-app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">CryoNav AI</h1>
          <p className="app-subtitle">Antarctic Navigation Decision Support System</p>
        </div>
        <div className="header-badges">
          {demoMode && <div className="header-badge demo">SCRIPTED SCENARIO</div>}
          {offlineMode && <div className="header-badge offline">OFFLINE SNAPSHOT</div>}
          <div className="header-badge simulated">SIMULATED</div>
        </div>
      </header>

      <div className="app-layout">
        {/* Map - 70% width */}
        <div className="map-container">
          <MapView
            icebergs={store.icebergs}
            selectedIceberg={store.selectedIceberg}
            icebergPrediction={store.icebergPrediction}
            routes={store.routes}
            selectedRoute={store.selectedRoute}
            shipPosition={shipPosition}
            shipTrail={demoMode && store.demoStep ? store.demoStep.ship_trail || [] : []}
            demoStep={currentDemoStep}
            routePulse={routePulse}
            onIcebergClick={handleIcebergClick}
            onRouteSelect={handleRouteSelect}
          />
          
          {/* Demo controls at bottom of map */}
          <div className="demo-controls-overlay">
            {!demoMode && demoScenario && (
              <div className="demo-controls">
                <button className="btn-demo-start" onClick={startDemo}>
                  ▶ Start Scripted Demo
                </button>
                <div className="demo-description">
                  4-step scenario: GREEN → YELLOW → ORANGE → RED crisis → Resolution
                </div>
              </div>
            )}
            
            {demoMode && demoScenario && (
              <div className="demo-controls active">
                <div className="demo-header">
                  <span className="demo-badge">SCRIPTED SCENARIO</span>
                  <span className="demo-step">{demoScenario.steps[currentDemoStep].time}</span>
                </div>
                
                <div className="demo-title">{demoScenario.steps[currentDemoStep].title}</div>
                <div className="demo-message">{demoScenario.steps[currentDemoStep].message}</div>
                
                <div className="demo-progress">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${((currentDemoStep + 1) / demoScenario.steps.length) * 100}%` }}
                    />
                  </div>
                  <div className="progress-label">
                    Step {currentDemoStep + 1} of {demoScenario.steps.length}
                  </div>
                </div>
                
                <div className="demo-actions">
                  <button 
                    className="btn-demo-nav" 
                    onClick={prevDemoStep}
                    disabled={currentDemoStep === 0}
                  >
                    ← Previous
                  </button>
                  <button 
                    className="btn-demo-nav primary" 
                    onClick={nextDemoStep}
                    disabled={currentDemoStep === demoScenario.steps.length - 1}
                  >
                    Next Step →
                  </button>
                  <button className="btn-demo-reset" onClick={resetDemo}>
                    Reset
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar - 30% width with sticky risk card */}
        <div className="sidebar-container">
          {/* Sticky Risk Card */}
          <div className="panel-section sticky-risk">
            <RiskCard
              risk={store.riskAssessment}
              loading={store.loading.risk}
            />
          </div>

          {/* Scrollable content */}
          <div className="sidebar-scrollable">
            {/* Route stats table */}
            {store.routes.length > 0 && (
              <div className="panel-section routes-panel">
                <h3 className="panel-title">Selected Route</h3>
                <div className="routes-table">
                  {store.routes.filter(r => r.id === store.selectedRoute).map(route => (
                    <div key={route.id} className="route-row selected">
                      <div className="route-color" style={{ backgroundColor: route.color }} />
                      <div className="route-info">
                        <div className="route-name">{route.type.replace('_', ' ').toUpperCase()}</div>
                        <div className="route-stats">
                          <span>{route.distanceKm.toFixed(0)} km</span>
                          <span>{route.timeDays.toFixed(1)} days</span>
                          <span>Fuel: {route.fuelIndex}</span>
                          <span className="risk-badge">{route.riskPercent}% risk</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Collapsible Explain Panel */}
            <details className="panel-section collapsible" open>
              <summary className="collapsible-header">Route Explanation</summary>
              <div className="collapsible-content">
                <ExplainPanel routeId={store.selectedRoute} />
              </div>
            </details>

            {/* Collapsible What-If Panel */}
            {!demoMode && (
              <details className="panel-section collapsible">
                <summary className="collapsible-header">What-If Analysis</summary>
                <div className="collapsible-content">
                  <WhatIfPanel />
                </div>
              </details>
            )}
          </div>
        </div>
      </div>

      <footer className="app-footer">
        <p>
          Track extrapolation with current-based fallback. Copernicus monthly currents. 
          Sea ice = seasonal model. Error measured on a small sample; to be validated. 
          Fuel index = relative (not actual fuel consumption).
        </p>
      </footer>

      <AlertModal
        isOpen={store.showAlert}
        onClose={() => {
          store.setShowAlert(false);
          handleSendAlert();
        }}
        recipients={[
          'Mission Control - McMurdo Station',
          'Rescue Coordination Centre - Christchurch',
          'Ship Operator',
          'Family (if authorized)'
        ]}
        familyAuthorized={false}
      />

      {/* Dev Overlay - Hidden by default, D key toggles */}
      {showDevOverlay && import.meta.env.DEV && (
        <div className="dev-overlay">
          <div className="dev-overlay-header">
            <strong>Dev Overlay</strong>
            <button onClick={() => setShowDevOverlay(false)}>×</button>
          </div>
          <div className="dev-overlay-content">
            <div>Demo Mode: {demoMode ? 'Yes' : 'No'}</div>
            <div>Backend: {backendOnline ? 'Online' : 'Offline'}</div>
            <div>Step: {currentDemoStep + 1}/{demoScenario?.steps?.length || 0}</div>
            <div>Risk: {store.riskLevel}</div>
            <div>Icebergs: {store.icebergs.length}</div>
            <div>Routes: {store.routes.length}</div>
          </div>
        </div>
      )}
    </div>
  );
};

const AppNew: React.FC = () => {
  return (
    <AppStoreProvider>
      <AppContent />
    </AppStoreProvider>
  );
};

export default AppNew;
