import { useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { Table } from '../components/Table.jsx';
import { Button } from '../components/Button.jsx';
import { ChartConvergence } from '../components/ChartConvergence.jsx';
import { ChartSensitivity } from '../components/ChartSensitivity.jsx';
import { exportGeometry, fetchOptimizationResult } from '../lib/apiClient.js';
import { useToast } from '../components/Toast.jsx';
import { useWorkspace } from '../lib/workspace.jsx';

export function ResultsPage() {
  const {
    geometry,
    optimizationResult,
    setOptimizationResult,
    setGeometry,
    simulationResult
  } = useWorkspace();
  const [jobId, setJobId] = useState('');
  const { notify } = useToast();

  const holeColumns = useMemo(
    () => [
      { header: '#', accessor: 'index' },
      { header: 'Axial (mm)', accessor: 'axial_pos_mm', cell: (row) => row.axial_pos_mm?.toFixed?.(2) ?? row.axial_pos_mm },
      { header: 'Diameter (mm)', accessor: 'diameter_mm', cell: (row) => row.diameter_mm?.toFixed?.(2) ?? row.diameter_mm },
      { header: 'Chimney (mm)', accessor: 'chimney_mm', cell: (row) => row.chimney_mm?.toFixed?.(2) ?? row.chimney_mm }
    ],
    []
  );

  const comparisonColumns = useMemo(
    () => [
      { header: 'Hole', accessor: 'hole' },
      { header: 'Baseline axial', accessor: 'baseline_axial' },
      { header: 'Optimized axial', accessor: 'optimized_axial' },
      { header: 'Δ axial', accessor: 'delta_axial' },
      { header: 'Baseline dia', accessor: 'baseline_diameter' },
      { header: 'Optimized dia', accessor: 'optimized_diameter' },
      { header: 'Δ dia', accessor: 'delta_diameter' }
    ],
    []
  );

  const comparisonData = useMemo(() => {
    const base = geometry?.tone_holes ?? [];
    const optimized = optimizationResult?.geometry?.tone_holes ?? [];
    const size = Math.max(base.length, optimized.length);
    const rows = [];
    for (let index = 0; index < size; index += 1) {
      const baseline = base[index];
      const opt = optimized[index];
      rows.push({
        hole: index + 1,
        baseline_axial: baseline ? baseline.axial_pos_mm.toFixed(2) : '—',
        optimized_axial: opt ? opt.axial_pos_mm.toFixed(2) : '—',
        delta_axial: baseline && opt ? (opt.axial_pos_mm - baseline.axial_pos_mm).toFixed(2) : '—',
        baseline_diameter: baseline ? baseline.diameter_mm.toFixed(2) : '—',
        optimized_diameter: opt ? opt.diameter_mm.toFixed(2) : '—',
        delta_diameter: baseline && opt ? (opt.diameter_mm - baseline.diameter_mm).toFixed(2) : '—'
      });
    }
    return rows;
  }, [geometry, optimizationResult]);

  const metricsSummary = useMemo(() => {
    if (!optimizationResult?.history || optimizationResult.history.length === 0) {
      return null;
    }
    return optimizationResult.history[optimizationResult.history.length - 1];
  }, [optimizationResult]);

  const runExport = async (fmt) => {
    try {
      const payload = await exportGeometry(fmt, { geometry, metadata: { fmt } });
      notify(`Exported ${fmt.toUpperCase()} to ${payload.path}`, 'success');
    } catch (error) {
      notify('Export failed', 'error');
    }
  };

  const loadResult = async () => {
    try {
      const response = await fetchOptimizationResult(jobId);
      setOptimizationResult(response);
      notify('Loaded optimization results', 'success');
    } catch (error) {
      notify('Unable to fetch result', 'error');
    }
  };

  const applyOptimized = () => {
    if (!optimizationResult?.geometry) {
      notify('No optimized geometry available', 'error');
      return;
    }
    setGeometry(optimizationResult.geometry);
    notify('Applied optimized geometry to workspace', 'success');
  };

  if (!geometry) {
    return <p>Run the geometry builder to create a clarinet design.</p>;
  }

  return (
    <div className="page-grid results-grid">
      <Card title="Exports" action={<Button onClick={loadResult}>Load job</Button>}>
        <div className="export-actions">
          <input value={jobId} onChange={(event) => setJobId(event.target.value)} placeholder="Optimization job id" />
          <div className="export-buttons">
            <Button onClick={() => runExport('json')}>JSON</Button>
            <Button onClick={() => runExport('csv')}>CSV</Button>
            <Button onClick={() => runExport('dxf')}>DXF</Button>
            <Button onClick={() => runExport('step')}>STEP</Button>
          </div>
        </div>
      </Card>
      <Card
        title="Workspace geometry"
        action={
          optimizationResult?.geometry && (
            <Button variant="secondary" onClick={applyOptimized}>
              Apply optimized layout
            </Button>
          )
        }
      >
        <Table columns={holeColumns} data={geometry.tone_holes ?? []} />
      </Card>
      {optimizationResult && (
        <>
          <Card title="Before vs after">
            <Table columns={comparisonColumns} data={comparisonData} />
          </Card>
          <Card title="Convergence">
            <ChartConvergence data={optimizationResult.convergence} />
          </Card>
          <Card title="Sensitivity">
            <ChartSensitivity data={optimizationResult.sensitivity} />
          </Card>
          {metricsSummary && (
            <Card title="Final metrics">
              <dl className="metrics-grid">
                <div>
                  <dt>Composite score</dt>
                  <dd>{metricsSummary.score?.toFixed?.(3) ?? metricsSummary.score}</dd>
                </div>
                <div>
                  <dt>Intonation RMSE</dt>
                  <dd>{metricsSummary.intonation_rmse?.toFixed?.(2) ?? metricsSummary.intonation_rmse} cents</dd>
                </div>
                <div>
                  <dt>Impedance smoothness</dt>
                  <dd>{metricsSummary.impedance_smoothness?.toFixed?.(3) ?? metricsSummary.impedance_smoothness}</dd>
                </div>
                <div>
                  <dt>Register alignment</dt>
                  <dd>{metricsSummary.register_alignment?.toFixed?.(2) ?? metricsSummary.register_alignment} cents</dd>
                </div>
              </dl>
            </Card>
          )}
        </>
      )}
      {simulationResult && (
        <Card title="Last simulation snapshot">
          <p>
            {simulationResult.intonation.length} notes analysed with frequency range {simulationResult.freq_hz[0].toFixed(1)}–
            {simulationResult.freq_hz.at(-1).toFixed(1)} Hz.
          </p>
        </Card>
      )}
    </div>
  );
}
