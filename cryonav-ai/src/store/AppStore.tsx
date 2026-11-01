/**
 * App State Management using React Context
 */
import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { RiskLevel, Iceberg, DriftPrediction, Route, RiskAssessment, RouteExplanation } from '../api/client';

interface DemoStep {
  id: number;
  time: string;
  title: string;
  message: string;
  shipPosition: { lat: number; lon: number };
  risk: RiskAssessment;
  icebergs: Iceberg[];
  recommendedAction?: string;
}

interface AppState {
  // Scenario
  currentScenario: number;
  demoStep: DemoStep | null;
  currentDate: string;
  
  // Map data
  icebergs: Iceberg[];
  selectedIceberg: string | null;
  icebergPrediction: DriftPrediction | null;
  
  // Routes
  routes: Route[];
  selectedRoute: string | null;
  routeExplanation: RouteExplanation | null;
  
  // Risk
  riskLevel: RiskLevel;
  riskAssessment: RiskAssessment | null;
  
  // UI
  showAlert: boolean;
  alertSent: boolean;
  routeChoice: 'accepted' | 'overridden' | null;
  
  // Loading states
  loading: {
    icebergs: boolean;
    prediction: boolean;
    routes: boolean;
    risk: boolean;
  };
}

interface AppContextValue extends AppState {
  setCurrentScenario: (scenario: number) => void;
  setDemoStep: (step: DemoStep | null) => void;
  setCurrentDate: (date: string) => void;
  setIcebergs: (icebergs: Iceberg[]) => void;
  setSelectedIceberg: (id: string | null) => void;
  setIcebergPrediction: (prediction: DriftPrediction | null) => void;
  setRoutes: (routes: Route[]) => void;
  setSelectedRoute: (id: string | null) => void;
  setRouteExplanation: (explanation: RouteExplanation | null) => void;
  setRiskLevel: (level: RiskLevel) => void;
  setRiskAssessment: (assessment: RiskAssessment | null) => void;
  setShowAlert: (show: boolean) => void;
  setAlertSent: (sent: boolean) => void;
  setRouteChoice: (choice: 'accepted' | 'overridden' | null) => void;
  setLoading: (key: keyof AppState['loading'], value: boolean) => void;
  resetState: () => void;
}

const initialState: AppState = {
  currentScenario: 0,
  demoStep: null,
  currentDate: new Date().toISOString().split('T')[0],
  icebergs: [],
  selectedIceberg: null,
  icebergPrediction: null,
  routes: [],
  selectedRoute: null,
  routeExplanation: null,
  riskLevel: 'GREEN',
  riskAssessment: null,
  showAlert: false,
  alertSent: false,
  routeChoice: null,
  loading: {
    icebergs: false,
    prediction: false,
    routes: false,
    risk: false,
  }
};

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const AppStoreProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AppState>(initialState);

  const setCurrentScenario = useCallback((scenario: number) => {
    setState(prev => ({ ...prev, currentScenario: scenario }));
  }, []);

  const setDemoStep = useCallback((step: DemoStep | null) => {
    setState(prev => ({ ...prev, demoStep: step }));
  }, []);

  const setCurrentDate = useCallback((date: string) => {
    setState(prev => ({ ...prev, currentDate: date }));
  }, []);

  const setIcebergs = useCallback((icebergs: Iceberg[]) => {
    setState(prev => ({ ...prev, icebergs }));
  }, []);

  const setSelectedIceberg = useCallback((id: string | null) => {
    setState(prev => ({ ...prev, selectedIceberg: id }));
  }, []);

  const setIcebergPrediction = useCallback((prediction: DriftPrediction | null) => {
    setState(prev => ({ ...prev, icebergPrediction: prediction }));
  }, []);

  const setRoutes = useCallback((routes: Route[]) => {
    setState(prev => ({ ...prev, routes }));
  }, []);

  const setSelectedRoute = useCallback((id: string | null) => {
    setState(prev => ({ ...prev, selectedRoute: id, routeChoice: null }));
  }, []);

  const setRouteExplanation = useCallback((explanation: RouteExplanation | null) => {
    setState(prev => ({ ...prev, routeExplanation: explanation }));
  }, []);

  const setRiskLevel = useCallback((level: RiskLevel) => {
    setState(prev => ({ ...prev, riskLevel: level }));
  }, []);

  const setRiskAssessment = useCallback((assessment: RiskAssessment | null) => {
    setState(prev => ({ ...prev, riskAssessment: assessment }));
  }, []);

  const setShowAlert = useCallback((show: boolean) => {
    setState(prev => ({ ...prev, showAlert: show }));
  }, []);

  const setAlertSent = useCallback((sent: boolean) => {
    setState(prev => ({ ...prev, alertSent: sent }));
  }, []);

  const setRouteChoice = useCallback((choice: 'accepted' | 'overridden' | null) => {
    setState(prev => ({ ...prev, routeChoice: choice }));
  }, []);

  const setLoading = useCallback((key: keyof AppState['loading'], value: boolean) => {
    setState(prev => ({
      ...prev,
      loading: { ...prev.loading, [key]: value }
    }));
  }, []);

  const resetState = useCallback(() => {
    setState(initialState);
  }, []);

  const value: AppContextValue = {
    ...state,
    setCurrentScenario,
    setDemoStep,
    setCurrentDate,
    setIcebergs,
    setSelectedIceberg,
    setIcebergPrediction,
    setRoutes,
    setSelectedRoute,
    setRouteExplanation,
    setRiskLevel,
    setRiskAssessment,
    setShowAlert,
    setAlertSent,
    setRouteChoice,
    setLoading,
    resetState,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppStore = (): AppContextValue => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppStore must be used within AppStoreProvider');
  }
  return context;
};
