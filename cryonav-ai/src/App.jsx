import { useCallback, useEffect, useMemo, useState } from 'react';
import { advanceTime, getHealth, getIcebergs, resetDemo, setUseMockData } from './services/api';
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
import RouteDetailsModal from './components/Modals/RouteDetailsModal';
import { MOCK_ADDITIONAL_ROUTES } from './components/Map/RouteLines';

function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [scenario, setScenario] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState('safest');
  const [toasts, setToasts] = useState([]);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [detailsRoute, setDetailsRoute] = useState(null);
  const [backendIcebergs, setBackendIcebergs] = useState(null); // null = not yet loaded

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

  useEffect(() => {
    if (scene.riskAssessment?.status === 'EMERGENCY') {
      setShowEmergencyModal(true);
    }
  }, [scenario, scene.riskAssessment?.status]);

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
              scenario={{ ...scene, icebergs: activeIcebergs }}
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
        onAcknowledge={() => setShowEmergencyModal(false)}
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
