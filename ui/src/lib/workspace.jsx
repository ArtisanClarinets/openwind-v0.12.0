import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { DEFAULT_NOTES } from './constants.js';
import { loadSettings, saveSettings } from './storage.js';
import { sanitizeGeometry } from './validators.js';

const defaultGeometry = {
  bore_mm: 14.6,
  length_mm: 660,
  barrel_length_mm: 65,
  mouthpiece_params: {},
  tone_holes: [],
  metadata: {}
};

const defaultConstraints = {
  minSpacingMm: 6,
  minDiameterMm: 3.5,
  maxDiameterMm: 15.5,
  maxHoleCount: 19
};

const defaultSimulationOptions = {
  temp_C: 22,
  freq_min_hz: 100,
  freq_max_hz: 2200,
  n_points: 2048,
  modes: 8,
  concert_pitch_hz: 440,
  transposition: 'Bb'
};

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  const stored = useMemo(() => loadSettings(), []);
  const [geometry, setGeometryState] = useState(() => {
    const base = stored.geometry ?? defaultGeometry;
    return sanitizeGeometry({ ...defaultGeometry, ...base });
  });
  const [constraints, setConstraintsState] = useState(() => ({
    ...defaultConstraints,
    ...(stored.constraints ?? {})
  }));
  const [simulationOptions, setSimulationOptionsState] = useState(() => ({
    ...defaultSimulationOptions,
    ...(stored.simulationOptions ?? {})
  }));
  const [selectedNotes, setSelectedNotesState] = useState(() => stored.selectedNotes ?? DEFAULT_NOTES);
  const [autosimulate, setAutosimulateState] = useState(() => stored.autosimulate ?? true);
  const [simulationResult, setSimulationResult] = useState(() => stored.simulation ?? null);
  const [optimizationResult, setOptimizationResult] = useState(() => stored.optimization ?? null);
  const [lastRecommendation, setLastRecommendation] = useState(() => stored.lastRecommendation ?? null);

  useEffect(() => {
    saveSettings({
      geometry,
      constraints,
      simulationOptions,
      selectedNotes,
      autosimulate,
      simulation: simulationResult,
      optimization: optimizationResult,
      lastRecommendation
    });
  }, [
    geometry,
    constraints,
    simulationOptions,
    selectedNotes,
    autosimulate,
    simulationResult,
    optimizationResult,
    lastRecommendation
  ]);

  const setGeometry = useCallback((update) => {
    setGeometryState((previous) => {
      const next = typeof update === 'function' ? update(previous) : update;
      return sanitizeGeometry({ ...defaultGeometry, ...next });
    });
  }, []);

  const setConstraints = useCallback((update) => {
    setConstraintsState((previous) => ({
      ...previous,
      ...(typeof update === 'function' ? update(previous) : update)
    }));
  }, []);

  const setSimulationOptions = useCallback((update) => {
    setSimulationOptionsState((previous) => ({
      ...previous,
      ...(typeof update === 'function' ? update(previous) : update)
    }));
  }, []);

  const setSelectedNotes = useCallback((update) => {
    setSelectedNotesState((previous) =>
      typeof update === 'function' ? update(previous) : update
    );
  }, []);

  const setAutosimulate = useCallback((value) => {
    setAutosimulateState(Boolean(value));
  }, []);

  const resetWorkspace = useCallback(() => {
    setGeometryState(sanitizeGeometry(defaultGeometry));
    setConstraintsState(defaultConstraints);
    setSimulationOptionsState(defaultSimulationOptions);
    setSelectedNotesState(DEFAULT_NOTES);
    setAutosimulateState(true);
    setSimulationResult(null);
    setOptimizationResult(null);
    setLastRecommendation(null);
  }, []);

  const value = useMemo(
    () => ({
      geometry,
      setGeometry,
      constraints,
      setConstraints,
      simulationOptions,
      setSimulationOptions,
      selectedNotes,
      setSelectedNotes,
      autosimulate,
      setAutosimulate,
      simulationResult,
      setSimulationResult,
      optimizationResult,
      setOptimizationResult,
      lastRecommendation,
      setLastRecommendation,
      resetWorkspace
    }),
    [
      geometry,
      setGeometry,
      constraints,
      setConstraints,
      simulationOptions,
      selectedNotes,
      autosimulate,
      simulationResult,
      optimizationResult,
      lastRecommendation,
      resetWorkspace
    ]
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within WorkspaceProvider');
  }
  return context;
}
