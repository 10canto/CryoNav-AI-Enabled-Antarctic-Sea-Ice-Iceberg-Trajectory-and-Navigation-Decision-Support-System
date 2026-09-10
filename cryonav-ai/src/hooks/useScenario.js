import { useState, useCallback } from 'react';
import { advanceTime, resetDemo, setUseMockData } from '../services/api';
import { SCENARIO_TRANSITION_DELAY } from '../config';
import { scenarioMetadata } from '../services/scenarioData';

export const useScenario = () => {
  const [scenario, setScenario] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  const nextScenario = useCallback(async () => {
    setIsTransitioning(true);
    try {
      const result = await advanceTime();
      if (result && result.scenario !== undefined) {
        setScenario(result.scenario);
      } else {
        // Fallback to local increment if API fails
        setScenario(prev => (prev + 1) % 4);
      }
      // Pause to let data settle
      await new Promise(resolve => setTimeout(resolve, SCENARIO_TRANSITION_DELAY));
    } catch (error) {
      console.error('Scenario advancement error:', error);
      setScenario(prev => (prev + 1) % 4); // Fallback
    } finally {
      setIsTransitioning(false);
    }
  }, []);
  
  const prevScenario = useCallback(() => {
    setScenario(prev => (prev - 1 + 4) % 4);
  }, []);
  
  const resetScenario = useCallback(async () => {
    setIsTransitioning(true);
    try {
      await resetDemo();
      setScenario(0);
      await new Promise(resolve => setTimeout(resolve, SCENARIO_TRANSITION_DELAY));
    } catch (error) {
      console.error('Reset error:', error);
      setScenario(0); // Fallback
    } finally {
      setIsTransitioning(false);
    }
  }, []);
  
  return {
    scenario,
    nextScenario,
    prevScenario,
    resetScenario,
    isTransitioning,
    metadata: scenarioMetadata[scenario],
  };
};
