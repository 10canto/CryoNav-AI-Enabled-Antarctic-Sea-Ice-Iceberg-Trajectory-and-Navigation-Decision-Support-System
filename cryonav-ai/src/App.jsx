import { useCallback, useEffect, useMemo, useState } from 'react';
import { advanceTime, getHealth, getIceAnalysis, getIcebergs, getPredictions, resetDemo, setUseMockData } from './services/api';
import { getMockPredictions } from './services/mockData';
import { SCENARIO_MOCKS } from './services/scenarioDataRequirements';
import { SCENARIO_TRANSITION_DELAY } from './config';
import { Notification } from './components/Common/Notification';
import HeaderBar from './components/Panels/HeaderBar';
import MainMap from './components/Map/MainMap';
import RiskStatusPanel from './components/Panels/RiskStatusPanel';
import RouteOptionsPanel from './components/Panels/RouteOptionsPanel';
import ExplanationPanel from './components/Panels/ExplanationPanel';
import TimelineControl from './components/Panels/TimelineControl';
import EmergencyAlertModal from './components/Modals/EmergencyAlertModal';
import SuccessModal from './components/Modals/SuccessModal';
import RouteDetailsModal from './components/Modals/RouteDetailsModal';
import { MOCK_ADDITIONAL_ROUTES } from './components/Map/RouteLines';

// Routes that are SAFE — show success in scenario 3
const SAFE_ROUTES = new Set(['safest']);

// Routes that trigger the collision warning — B, C, and mock alternatives
const RISKY_ROUTES = new Set(['fastest', 'fuel', 'alternative_1', 'alternative_2']);

function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [scenario, setScenario] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState('safest');
  const [toasts, setToasts] = useState([]);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [detailsRoute, setDetailsRoute] = useState(null);
  const [backendIcebergs, setBackendIcebergs] = useState(null);
  const [backendIceZones, setBackendIceZones] = useState(null);
  const [backendPredictions, setBackendPredictions] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const scene = SCENARIO_MOCKS[scenario] || SCENARIO_MOCKS[0];

  // Icebergs: use backend JSON data when connected, fall back to frontend mock
  const activeIcebergs = useMemo(() => {
    if (backendIcebergs !== null) return backendIcebergs;
    return scene.icebergs || [];
  }, [backendIcebergs, scene.icebergs]);
  
  // Combine backend routes with mock routes for display
  const allRoutes = useMemo(() => {
    return [...(scene.routes || []), ...MOCK_ADDITIONAL_ROUTES];
  }, [scene.routes]);

  const addToast = useCallback((type, message, duration = 6000) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [...prev, { id, type, message, duration }]);
  }, []);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await getHealth();
        if (response?.status && String(response.status).toLowerCase().includes('running')) {
          setBackendStatus('connected');
          setUseMockData(false);
        } else {
          setBackendStatus('offline');
          setUseMockData(true);
        }
      } catch {
        setBackendStatus('offline');
        setUseMockData(true);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (backendStatus === 'offline') {
      addToast('warning', 'Backend offline — running expedition simulation with onboard scenario data');
    }
  }, [backendStatus, addToast]);

  // Fetch icebergs from backend whenever scenario changes (if backend connected)
  useEffect(() => {
    if (backendStatus !== 'connected') {
      setBackendIcebergs(null); // fall back to mock
      return;
    }
    getIcebergs()
      .then((data) => {
        const list = data?.icebergs ?? null;
        setBackendIcebergs(list);
      })
      .catch(() => setBackendIcebergs(null));
  }, [backendStatus, scenario]);

  // Fetch ice zone analysis from backend whenever scenario changes (if backend connected)
  useEffect(() => {
    if (backendStatus !== 'connected') {
      setBackendIceZones(null); // fall back to ICE_ZONES_DATA constant
      return;
    }
    getIceAnalysis()
      .then((data) => {
        setBackendIceZones(data ?? null);
      })
      .catch(() => setBackendIceZones(null));
  }, [backendStatus, scenario]);

  // Fetch predictions on every scenario change.
  // Strategy: always load from mock immediately so trajectories are never blank,
  // then try backend and upgrade if available.
  useEffect(() => {
    // 1. Set mock data immediately — guarantees circles are visible right away
    const mockPreds = getMockPredictions(scenario)?.predictions ?? [];
    setBackendPredictions(mockPreds);

    // 2. If backend connected, try to upgrade with real data
    if (backendStatus === 'connected') {
      getPredictions(null, scenario)
        .then((data) => {
          const preds = Array.isArray(data) ? data : (data?.predictions ?? null);
          // Only upgrade if backend returned non-empty data
          if (preds && preds.length > 0) {
            setBackendPredictions(preds);
          }
        })
        .catch(() => { /* keep mock data already set */ });
    }
  }, [scenario, backendStatus]);

  // Scenario 3 modal logic — depends on which route the captain chose
  useEffect(() => {
    if (scene.riskAssessment?.status !== 'EMERGENCY') return;

    if (SAFE_ROUTES.has(selectedRoute)) {
      // Route A — ship safely avoids all icebergs
      setShowSuccessModal(true);
      setShowEmergencyModal(false);
    } else if (RISKY_ROUTES.has(selectedRoute)) {
      // Route B / C / alternatives — iceberg collision warning
      setShowEmergencyModal(true);
      setShowSuccessModal(false);
    } else {
      // Unknown route — default to emergency
      setShowEmergencyModal(true);
      setShowSuccessModal(false);
    }
  }, [scenario, scene.riskAssessment?.status, selectedRoute]);

  const nextScenario = useCallback(async () => {
    setIsTransitioning(true);
    try {
      const result = await advanceTime();
      setScenario((prev) => Math.min(
        backendStatus === 'connected' && Number.isInteger(result?.scenario) ? result.scenario : prev + 1,
        3,
      ));
    } catch {
      setScenario((prev) => Math.min(prev + 1, 3));
    }
    window.setTimeout(() => setIsTransitioning(false), SCENARIO_TRANSITION_DELAY);
  }, [backendStatus]);

  const prevScenario = useCallback(() => {
    setScenario((prev) => Math.max(prev - 1, 0));
  }, []);

  const resetScenario = useCallback(async () => {
    await resetDemo().catch(() => {});
    setScenario(0);
    setSelectedRoute('safest');
    setShowEmergencyModal(false);
    setShowSuccessModal(false);
    addToast('info', 'Expedition timeline reset to baseline departure');
  }, [addToast]);

  const riskForModal = useMemo(
    () => ({
      level: scene.riskAssessment.status,
      metrics: {
        nearest_iceberg_km: scene.riskAssessment.nearestIceberg,
        collision_risk_percent: scene.riskAssessment.collisionRisk,
        ice_concentration: scene.riskAssessment.iceConcentration,
        temperature_celsius: scene.riskAssessment.temperature,
        wind_speed_kmh: scene.riskAssessment.windSpeed,
        wind_direction: scene.riskAssessment.windDirection,
        visibility: scene.riskAssessment.visibility,
      },
    }),
    [scene],
  );

  return (
    <div className="app-container">
      <Notification notifications={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((n) => n.id !== id))} />

      <div className="dashboard-header">
        <HeaderBar connectionStatus={backendStatus} missionTime={scene.time} />
      </div>

      <div className="dashboard-grid">
        <div className="map-column">
          <div className="map-wrapper">
            <MainMap
              scenario={{ ...scene, icebergs: activeIcebergs, predictions: backendPredictions }}
              iceZoneData={backendIceZones}
              selectedRoute={selectedRoute}
              onSelectRoute={setSelectedRoute}
            />
          </div>
          <div className="timeline-wrapper">
            <TimelineControl
              scenario={scenario}
              nextScenario={nextScenario}
              prevScenario={prevScenario}
              resetScenario={resetScenario}
              isTransitioning={isTransitioning}
              missionTime={scene.time}
            />
          </div>
        </div>

        <div className="panels-column">
          <div className="dashboard-card">
            <RiskStatusPanel risk={scene.riskAssessment} />
          </div>
          <div className="dashboard-card">
          <ExplanationPanel
            explanation={scene.explanation}
            onAcceptRoute={() => { setSelectedRoute('fastest'); addToast('success', 'Route B northern detour accepted'); }}
            onKeepCurrent={() => addToast('info', 'Current route retained — hazard monitoring continues')}
          />
          </div>
          <div className="dashboard-card">
            <RouteOptionsPanel
              routes={allRoutes}
              selectedRoute={selectedRoute}
              onRouteSelect={setSelectedRoute}
              onShowDetails={setDetailsRoute}
            />
          </div>
        </div>
      </div>

      <EmergencyAlertModal
        show={showEmergencyModal}
        riskData={riskForModal}
        selectedRoute={selectedRoute}
        onAcknowledge={() => setShowEmergencyModal(false)}
      />

      <SuccessModal
        show={showSuccessModal}
        routeName="Route A — Eastern Ice-Avoidance"
        onAcknowledge={() => {
          setShowSuccessModal(false);
          addToast('success', 'Mission complete — R/V Bharati Pioneer arrived safely at Maitri Station');
        }}
      />

      <RouteDetailsModal
        isOpen={Boolean(detailsRoute)}
        route={detailsRoute}
        onClose={() => setDetailsRoute(null)}
        onSelectRoute={(id) => {
          setSelectedRoute(id);
          setDetailsRoute(null);
        }}
      />
    </div>
  );
}

export default App;
