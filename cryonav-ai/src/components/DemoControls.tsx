/**
 * Demo Scenario Controls Component
 * Steps through pre-scripted scenario demonstrating risk escalation and resolution
 */
import React, { useState } from 'react';
import './DemoControls.css';

interface DemoStep {
  id: number;
  time: string;
  title: string;
  message: string;
  risk: {
    level: string;
    distance_km: number;
    nearest_iceberg: string;
    reasons: string[];
  };
}

interface DemoControlsProps {
  onStepChange: (step: DemoStep) => void;
}

export const DemoControls: React.FC<DemoControlsProps> = ({ onStepChange }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isActive, setIsActive] = useState(false);

  const scenario = {
    name: "Antarctic Navigation Crisis Demo",
    steps: [
      {
        id: 1,
        time: "T+0h",
        title: "Departure - All Clear",
        message: "Route A initiated. Weather favorable. All systems nominal.",
        risk: {
          level: "GREEN",
          distance_km: 28.5,
          nearest_iceberg: "A81",
          reasons: ["Clear navigation - Nearest iceberg: 28.5 km", "Low risk - Continue monitoring"]
        }
      },
      {
        id: 2,
        time: "T+2h",
        title: "New Iceberg Detected",
        message: "Satellite alert: New iceberg A85-NEW detected on route. Risk elevated to YELLOW.",
        risk: {
          level: "YELLOW",
          distance_km: 18.2,
          nearest_iceberg: "A85-NEW",
          reasons: ["New iceberg detected: 18.2 km away", "Moderate risk - Maintain awareness"]
        }
      },
      {
        id: 3,
        time: "T+4h",
        title: "Route A Blocked - High Risk",
        message: "ORANGE ALERT: Route A predicted blocked. Physics model shows 72h drift cone intersects planned path.",
        risk: {
          level: "ORANGE",
          distance_km: 9.3,
          nearest_iceberg: "A85-NEW",
          reasons: [
            "Iceberg within 10 km (9.3 km)",
            "High risk - Prepare evasive action",
            "Drift cone blocks Route A in 2 hours"
          ]
        }
      },
      {
        id: 4,
        time: "T+4.5h",
        title: "Crisis Averted - Route B",
        message: "Reroute successful. Risk reduced to GREEN. ETA adjusted +1.2 hours. Crisis management effective.",
        risk: {
          level: "GREEN",
          distance_km: 22.1,
          nearest_iceberg: "A81",
          reasons: [
            "Successfully rerouted to Route B",
            "Clear navigation - 22.1 km clearance",
            "Route B adds 12 km but maintains safety buffer"
          ]
        }
      }
    ]
  };

  const handleStart = () => {
    setIsActive(true);
    setCurrentStep(0);
    onStepChange(scenario.steps[0]);
  };

  const handleNext = () => {
    if (currentStep < scenario.steps.length - 1) {
      const nextStep = currentStep + 1;
      setCurrentStep(nextStep);
      onStepChange(scenario.steps[nextStep]);
    }
  };

  const handleReset = () => {
    setIsActive(false);
    setCurrentStep(0);
  };

  if (!isActive) {
    return (
      <div className="demo-controls">
        <button className="btn-demo-start" onClick={handleStart}>
          ▶ Start Demo Scenario
        </button>
        <div className="demo-description">
          Scripted 6-hour scenario: GREEN → YELLOW → ORANGE → Crisis Averted
        </div>
      </div>
    );
  }

  const currentScenarioStep = scenario.steps[currentStep];
  const isLastStep = currentStep === scenario.steps.length - 1;

  return (
    <div className="demo-controls active">
      <div className="demo-header">
        <span className="demo-badge">SCRIPTED SCENARIO</span>
        <span className="demo-step">{currentScenarioStep.time}</span>
      </div>
      
      <div className="demo-title">{currentScenarioStep.title}</div>
      <div className="demo-message">{currentScenarioStep.message}</div>
      
      <div className="demo-progress">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${((currentStep + 1) / scenario.steps.length) * 100}%` }}
          />
        </div>
        <div className="progress-label">
          Step {currentStep + 1} of {scenario.steps.length}
        </div>
      </div>
      
      <div className="demo-actions">
        {!isLastStep && (
          <button className="btn-demo-next" onClick={handleNext}>
            Next 6 Hours →
          </button>
        )}
        <button className="btn-demo-reset" onClick={handleReset}>
          Reset Demo
        </button>
      </div>
    </div>
  );
};
