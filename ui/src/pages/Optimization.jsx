import { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { NumberField } from '../components/NumberField.jsx';
import { Button } from '../components/Button.jsx';
import { ChartConvergence } from '../components/ChartConvergence.jsx';
import { startOptimization, fetchOptimizationResult } from '../lib/apiClient.js';
import { loadSettings } from '../lib/storage.js';
import { useToast } from '../components/Toast.jsx';

export function OptimizationPage() {
  const [geometry] = useState(loadSettings().geometry ?? null);
  const [bounds, setBounds] = useState({ bore_delta_mm: 0.4, hole_diameter_delta_mm: 0.5, hole_position_delta_mm: 2 });
  const [objective, setObjective] = useState({ intonation: 1, impedance_smoothness: 0.25, register_alignment: 0.5 });
  const [job, setJob] = useState(null);
  const [events, setEvents] = useState([]);
  const [result, setResult] = useState(null);
  const { notify } = useToast();

  useEffect(() => {
    if (!job?.job_id) return undefined;
    const source = new EventSource(`http://127.0.0.1:8001/api/v1/optimize/stream?job_id=${job.job_id}`);
    source.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents((current) => [...current, data]);
      if (data.msg === 'done') {
        fetchOptimizationResult(job.job_id).then(setResult).catch(() => notify('Failed to retrieve optimization result', 'error'));
      }
    };
    source.onerror = () => source.close();
    return () => source.close();
  }, [job, notify]);

  const start = async () => {
    if (!geometry) {
      notify('No geometry to optimize', 'error');
      return;
    }
    try {
      const response = await startOptimization({ geometry, bounds, objective, seed: 1234 });
      setJob(response);
      setEvents([]);
      notify('Optimization started', 'info');
    } catch (error) {
      notify('Optimization failed', 'error');
    }
  };

  const convergence = useMemo(() => result?.convergence ?? events.map((event, index) => event.score ?? (events[index - 1]?.score ?? 0)), [result, events]);

  return (
    <div className="page-grid">
      <Card title="Objective weights">
        <div className="grid-two">
          <NumberField label="Intonation" value={objective.intonation} onChange={(value) => setObjective((prev) => ({ ...prev, intonation: value }))} />
          <NumberField label="Impedance smoothness" value={objective.impedance_smoothness} onChange={(value) => setObjective((prev) => ({ ...prev, impedance_smoothness: value }))} />
          <NumberField label="Register alignment" value={objective.register_alignment} onChange={(value) => setObjective((prev) => ({ ...prev, register_alignment: value }))} />
        </div>
      </Card>
      <Card title="Bounds">
        <div className="grid-two">
          <NumberField label="Bore delta" value={bounds.bore_delta_mm} unit="mm" onChange={(value) => setBounds((prev) => ({ ...prev, bore_delta_mm: value }))} />
          <NumberField label="Hole diameter delta" value={bounds.hole_diameter_delta_mm} unit="mm" onChange={(value) => setBounds((prev) => ({ ...prev, hole_diameter_delta_mm: value }))} />
          <NumberField label="Hole position delta" value={bounds.hole_position_delta_mm} unit="mm" onChange={(value) => setBounds((prev) => ({ ...prev, hole_position_delta_mm: value }))} />
        </div>
        <Button onClick={start}>Start optimization</Button>
      </Card>
      <Card title="Progress log">
        <ul className="log">
          {events.map((event, index) => (
            <li key={index}>{event.msg} ({event.pct}%)</li>
          ))}
        </ul>
      </Card>
      <Card title="Convergence">
        <ChartConvergence data={convergence} />
      </Card>
    </div>
  );
}
