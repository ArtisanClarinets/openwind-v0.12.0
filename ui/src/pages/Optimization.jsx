import { useEffect, useMemo, useRef, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { NumberField } from '../components/NumberField.jsx';
import { Button } from '../components/Button.jsx';
import { Switch } from '../components/Switch.jsx';
import { ChartConvergence } from '../components/ChartConvergence.jsx';
import { startOptimization, fetchOptimizationResult } from '../lib/apiClient.js';
import { useToast } from '../components/Toast.jsx';
import { useWorkspace } from '../lib/workspace.jsx';

export function OptimizationPage() {
  const {
    geometry,
    setGeometry,
    optimizationResult,
    setOptimizationResult,
    simulationOptions,
    selectedNotes

  } = useWorkspace();
  const [bounds, setBounds] = useState({
    bore_delta_mm: 0.4,
    hole_diameter_delta_mm: 0.5,
    hole_position_delta_mm: 2
  });
  const [objective, setObjective] = useState({
    intonation: 1,
    impedance_smoothness: 0.25,
    register_alignment: 0.5
  });
  const [maxIter, setMaxIter] = useState(40);
  const [seed, setSeed] = useState(1234);
  const [autoApply, setAutoApply] = useState(false);
  const [job, setJob] = useState(null);
  const [events, setEvents] = useState([]);
  const [progress, setProgress] = useState(0);
  const [streaming, setStreaming] = useState(false);
  const eventSourceRef = useRef(null);
  const { notify } = useToast();

  useEffect(() => {
    if (!job?.job_id || !streaming) {
      return undefined;
    }
    const source = new EventSource(`http://127.0.0.1:8001/api/v1/optimize/stream?job_id=${job.job_id}`);
    eventSourceRef.current = source;
    source.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents((current) => [...current, data]);
      if (typeof data.pct === 'number') {
        setProgress(Math.max(0, Math.min(100, data.pct)));
      }
      if (data.msg === 'done') {
        setStreaming(false);
        fetchOptimizationResult(job.job_id)
          .then((payload) => {
            setOptimizationResult(payload);
            if (autoApply && payload?.geometry) {
              setGeometry(payload.geometry);
            }
            notify('Optimization completed', 'success');
          })
          .catch(() => notify('Failed to retrieve optimization result', 'error'));
      }
    };
    source.onerror = () => {
      source.close();
      setStreaming(false);
    };
    return () => {
      source.close();
      eventSourceRef.current = null;
    };
  }, [autoApply, job, notify, setGeometry, setOptimizationResult, streaming]);

  const start = async () => {
    if (!geometry) {
      notify('No geometry to optimize', 'error');
      return;
    }
    try {
      const response = await startOptimization({
        geometry,
        bounds,
        objective,
        seed,
        max_iter: maxIter,
        simulation: simulationOptions,
        fingering_notes: selectedNotes
      });
      setJob(response);
      setEvents([]);
      setProgress(0);
      setStreaming(true);
      notify(`Optimization job ${response.job_id} started`, 'info');
    } catch (error) {
      notify('Optimization failed', 'error');
    }
  };

  const stop = () => {
    eventSourceRef.current?.close();
    setStreaming(false);
    setEvents((current) => [...current, { pct: progress, msg: 'Stopped by user' }]);
    notify('Optimization stopped', 'warning');
  };

  const convergence = useMemo(() => {
    if (optimizationResult?.convergence) {
      return optimizationResult.convergence;
    }
    return events
      .filter((event) => typeof event.score === 'number')
      .map((event) => event.score);

  }, [events, optimizationResult]);

  return (
    <div className="page-grid optimization-grid">
      <Card title="Objective weights">
        <div className="grid-two">
          <NumberField label="Intonation" value={objective.intonation} onChange={(value) => setObjective((prev) => ({ ...prev, intonation: value }))} />
          <NumberField label="Impedance smoothness" value={objective.impedance_smoothness} onChange={(value) => setObjective((prev) => ({ ...prev, impedance_smoothness: value }))} />
          <NumberField label="Register alignment" value={objective.register_alignment} onChange={(value) => setObjective((prev) => ({ ...prev, register_alignment: value }))} />
        </div>
      </Card>
      <Card
        title="Bounds & settings"
        action={
          <div className="card-action-row">
            <Button onClick={start} disabled={streaming}>Start optimization</Button>
            <Button variant="secondary" onClick={stop} disabled={!streaming}>
              Stop
            </Button>
          </div>
        }
      >
        <div className="grid-two">
          <NumberField label="Bore delta" value={bounds.bore_delta_mm} unit="mm" onChange={(value) => setBounds((prev) => ({ ...prev, bore_delta_mm: value }))} />
          <NumberField label="Hole diameter delta" value={bounds.hole_diameter_delta_mm} unit="mm" onChange={(value) => setBounds((prev) => ({ ...prev, hole_diameter_delta_mm: value }))} />
          <NumberField label="Hole position delta" value={bounds.hole_position_delta_mm} unit="mm" onChange={(value) => setBounds((prev) => ({ ...prev, hole_position_delta_mm: value }))} />
          <NumberField label="Max iterations" value={maxIter} onChange={(value) => setMaxIter(Math.max(5, Math.round(value)))} />
          <NumberField label="Seed" value={seed} onChange={(value) => setSeed(Math.round(value))} />
        </div>
        <div className="progress-row">
          <label htmlFor="optimization-progress">Progress</label>
          <progress id="optimization-progress" value={progress} max={100} />
          <span>{progress}%</span>
        </div>
        <Switch
          id="auto-apply-optimized"
          label="Auto-apply result"
          description="Replace the geometry with the optimized version on completion"
          checked={autoApply}
          onChange={setAutoApply}
        />
      </Card>
      <Card title="Progress log">
        <ul className="log" aria-live="polite">
          {events.map((event, index) => (
            <li key={index}>
              <span>{event.msg}</span>
              {typeof event.pct === 'number' && <span> ({event.pct}%)</span>}
              {typeof event.score === 'number' && <span> • score {event.score.toFixed(3)}</span>}
              {typeof event.intonation_rmse === 'number' && <span> • RMSE {event.intonation_rmse.toFixed(2)}¢</span>}
            </li>

          ))}
        </ul>
      </Card>
      <Card title="Convergence">
        <ChartConvergence data={convergence} />
      </Card>
      {optimizationResult && (
        <Card
          title="Latest result"
          action={
            <Button variant="secondary" onClick={() => setGeometry(optimizationResult.geometry)}>
              Apply to workspace
            </Button>
          }
        >
          <p>Job {optimizationResult.job_id} finished {optimizationResult.status}.</p>
        </Card>
      )}
    </div>
  );
}
