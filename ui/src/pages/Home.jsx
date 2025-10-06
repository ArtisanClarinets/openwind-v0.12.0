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
    const undercuts = holes.map((hole) => hole.undercut_mm ?? 0).filter((value) => Number.isFinite(value));
    const minSpacing = spacing.length ? Math.min(...spacing) : null;
    const maxSpacing = spacing.length ? Math.max(...spacing) : null;
    const minUndercut = undercuts.length ? Math.min(...undercuts) : null;
    const maxUndercut = undercuts.length ? Math.max(...undercuts) : null;
    return {
      count: holes.length,
      closed,
      open: holes.length - closed,
      minSpacing,
      maxSpacing,
      minUndercut,
      maxUndercut
    };
  }, [geometry]);

  return (
    <div className="page-grid">
      <Card className="guidance-card" title="Welcome to OpenWInD">
        <p>
          This workspace walks you through the complete clarinet design cycle. If you are new to
          acoustics or CAD, follow the numbered steps below – the defaults are safe, and every
          screen offers plain-language summaries before you commit to a change.
        </p>
        <ol>
          <li>
            <strong>Geometry:</strong> describe the physical instrument by editing tone holes, bore
            length and constraints. Helpful hints explain every field.
          </li>
          <li>
            <strong>Simulation:</strong> run OpenWInD’s physics model to hear how your design will
            respond. Charts and tables highlight what the numbers mean.
          </li>
          <li>
            <strong>Optimization &amp; Results:</strong> let the server suggest improvements, compare
            them to your baseline and download shareable files when you are satisfied.
          </li>
        </ol>
        <p>
          You can jump back to this overview at any time; nothing is saved until you explicitly
          export or copy a design.
        </p>
      </Card>
      <Card
        title="Quick start"
        action={
          <Button onClick={loadPreset} disabled={loading} aria-live="polite">
            {loading ? 'Loading…' : 'Load Bb preset'}
          </Button>
        }
      >
        <p>
          Not sure where to start? Load a factory Bb clarinet to explore how values change. You can
          always return to the preset or undo changes later.
        </p>
        <ul>
          <li>
            <strong>1. Geometry builder:</strong> adjust bore, barrel and tone-hole layout with live
            validation messages.
          </li>
          <li>
            <strong>2. Simulation:</strong> visualize how the instrument will sound compared with
            standard concert pitch.
          </li>
          <li>
            <strong>3. Optimization:</strong> stream server-side suggestions in real time and decide
            whether to apply them.
          </li>
          <li>
            <strong>4. Results:</strong> export JSON, CSV, DXF or STEP files to share with makers or
            CAD tools.
          </li>
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
        <p>
          These figures summarise your current design. Use them as a dashboard – if anything looks
          unusual, revisit the geometry before running a new simulation or export.
        </p>
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
            <dt>Undercut range</dt>
            <dd>
              {summary.minUndercut === null
                ? '—'
                : `${summary.minUndercut.toFixed(2)}–${summary.maxUndercut.toFixed(2)} mm`}
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
            <p>
              {simulationResult
                ? `Last run: ${simulationResult.freq_hz.length} frequency points evaluated.`
                : 'No runs yet – head to Simulation to test how your design behaves.'}
            </p>
            <Button as={Link} to="/simulation" variant="secondary" size="sm">
              Review simulation
            </Button>
          </section>
          <section>
            <h3>Optimization</h3>
            <p>
              {optimizationResult
                ? `Job ${optimizationResult.job_id} (${optimizationResult.status}).`
                : 'No jobs yet – visit Optimization to request server suggestions.'}
            </p>
            <Button as={Link} to="/optimization" variant="secondary" size="sm">
              Manage optimization
            </Button>
          </section>
        </div>
      </Card>
      <Card title="API status">
        <p>
          If you ever see errors, check this status block – it mirrors the server response used by
          the UI. A value of <code>null</code> simply means the application is still loading.
        </p>
        <pre className="status-block">{JSON.stringify(health, null, 2)}</pre>
      </Card>
    </div>
  );
}
