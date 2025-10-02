import { useEffect, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { Button } from '../components/Button.jsx';
import { getHealth, fetchPreset } from '../lib/apiClient.js';
import { saveSettings } from '../lib/storage.js';
import { useToast } from '../components/Toast.jsx';

export function Home() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const { notify } = useToast();

  useEffect(() => {
    getHealth().then(setHealth).catch(() => notify('API unreachable', 'error'));
  }, [notify]);

  const loadPreset = async () => {
    try {
      setLoading(true);
      const preset = await fetchPreset();
      saveSettings({ geometry: preset.geometry });
      notify('Preset geometry loaded into workspace', 'success');
    } catch (error) {
      notify('Failed to load preset', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-grid">
      <Card title="Quick start" action={<Button onClick={loadPreset} disabled={loading}>{loading ? 'Loading…' : 'Load Bb preset'}</Button>}>
        <p>Use the preset to populate the geometry builder, then adjust the tone holes and simulate the impedance in real-time.</p>
        <ul>
          <li>Geometry Builder: adjust bore, barrel and tone-hole layout with validation.</li>
          <li>Simulation: visualize impedance and intonation against the concert pitch.</li>
          <li>Optimization: stream progress with SSE and compare convergence.</li>
          <li>Results: export JSON, CSV, DXF and STEP (when CadQuery is available).</li>
        </ul>
      </Card>
      <Card title="API status">
        <pre className="status-block">{JSON.stringify(health, null, 2)}</pre>
      </Card>
    </div>
  );
}
