import { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { Button } from '../components/Button.jsx';
import { getHealth, fetchPreset } from '../lib/apiClient.js';
import { useToast } from '../components/Toast.jsx';
import { useWorkspace } from '../lib/workspace.jsx';
import { Link } from 'react-router-dom';

export function Home() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const { notify } = useToast();
  const {
    geometry,
    setGeometry,
    simulationResult,
    optimizationResult,
    resetWorkspace,
    lastRecommendation,
    setLastRecommendation
  } = useWorkspace();

  useEffect(() => {
    getHealth().then(setHealth).catch(() => notify('API unreachable', 'error'));
  }, [notify]);

  const loadPreset = async () => {
    try {
      setLoading(true);
      const preset = await fetchPreset();
      setGeometry(preset.geometry);
      setLastRecommendation({
        type: 'preset',
        loadedAt: new Date().toISOString(),
        description: preset.metadata?.name ?? 'Factory preset'
      });
      notify('Preset geometry loaded into workspace', 'success');
    } catch (error) {
      notify('Failed to load preset', 'error');
    } finally {
      setLoading(false);
    }
  };

  const summary = useMemo(() => {
    const holes = geometry?.tone_holes ?? [];
    const closed = holes.filter((hole) => hole.closed).length;
    const spacing = holes
      .slice(1)
      .map((hole, index) => hole.axial_pos_mm - holes[index].axial_pos_mm)
      .filter((value) => Number.isFinite(value));
    const minSpacing = spacing.length ? Math.min(...spacing) : null;
    const maxSpacing = spacing.length ? Math.max(...spacing) : null;
    return {
      count: holes.length,
      closed,
      open: holes.length - closed,
      minSpacing,
      maxSpacing
    };
  }, [geometry]);

  return (
    <div className="page-grid">
      <Card
        title="Quick start"
        action={
          <Button onClick={loadPreset} disabled={loading} aria-live="polite">
            {loading ? 'Loading…' : 'Load Bb preset'}
          </Button>
        }
      >
        <p>
          Use the preset to populate the geometry builder, then adjust the tone holes and simulate the impedance in real-time.
        </p>
        <ul>
          <li>Geometry Builder: adjust bore, barrel and tone-hole layout with validation.</li>
          <li>Simulation: visualize impedance and intonation against the concert pitch.</li>
          <li>Optimization: stream progress with SSE and compare convergence.</li>
          <li>Results: export JSON, CSV, DXF and STEP (when CadQuery is available).</li>
        </ul>
        <div className="quick-links">
          <Button as={Link} to="/geometry" variant="secondary">
            Open geometry builder
          </Button>
          <Button as={Link} to="/simulation" variant="ghost">
            Go to simulation
          </Button>
        </div>
      </Card>
      <Card
        title="Workspace snapshot"
        action={
          <Button variant="ghost" onClick={resetWorkspace} aria-label="Reset workspace">
            Reset workspace
          </Button>
        }
      >
        <dl className="workspace-summary">
          <div>
            <dt>Tone holes</dt>
            <dd>{summary.count}</dd>
          </div>
          <div>
            <dt>Open / closed</dt>
            <dd>
              {summary.open} / {summary.closed}
            </dd>
          </div>
          <div>
            <dt>Spacing range</dt>
            <dd>
              {summary.minSpacing === null
                ? '—'
                : `${summary.minSpacing.toFixed(1)}–${summary.maxSpacing.toFixed(1)} mm`}
            </dd>
          </div>
          <div>
            <dt>Last recommendation</dt>
            <dd>{lastRecommendation ? new Date(lastRecommendation.loadedAt).toLocaleString() : 'Not yet'}</dd>
          </div>
        </dl>
        <div className="workspace-status-grid">
          <section>
            <h3>Simulation</h3>
            <p>{simulationResult ? `Last run: ${simulationResult.freq_hz.length} points` : 'No runs yet.'}</p>
            <Button as={Link} to="/simulation" variant="secondary" size="sm">
              Review simulation
            </Button>
          </section>
          <section>
            <h3>Optimization</h3>
            <p>{optimizationResult ? `Job ${optimizationResult.job_id} (${optimizationResult.status})` : 'No jobs yet.'}</p>
            <Button as={Link} to="/optimization" variant="secondary" size="sm">
              Manage optimization
            </Button>
          </section>
        </div>
      </Card>
      <Card title="API status">
        <pre className="status-block">{JSON.stringify(health, null, 2)}</pre>
      </Card>
    </div>
  );
}
