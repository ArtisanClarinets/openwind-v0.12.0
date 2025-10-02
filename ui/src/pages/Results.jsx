import { useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { Table } from '../components/Table.jsx';
import { Button } from '../components/Button.jsx';
import { exportGeometry, fetchOptimizationResult } from '../lib/apiClient.js';
import { loadSettings } from '../lib/storage.js';
import { useToast } from '../components/Toast.jsx';

export function ResultsPage() {
  const { geometry } = loadSettings();
  const [jobId, setJobId] = useState('');
  const [optimization, setOptimization] = useState(null);
  const { notify } = useToast();

  const holeColumns = useMemo(
    () => [
      { header: '#', accessor: 'index' },
      { header: 'Axial (mm)', accessor: 'axial_pos_mm' },
      { header: 'Diameter (mm)', accessor: 'diameter_mm' },
      { header: 'Chimney (mm)', accessor: 'chimney_mm' }
    ],
    []
  );

  const sensitivityColumns = useMemo(
    () => [
      { header: 'Iteration', accessor: 'iteration' },
      { header: 'Score', accessor: 'score' }
    ],
    []
  );

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
      setOptimization(response);
      notify('Loaded optimization results', 'success');
    } catch (error) {
      notify('Unable to fetch result', 'error');
    }
  };

  if (!geometry) {
    return <p>Run the geometry builder to create a clarinet design.</p>;
  }

  return (
    <div className="page-grid">
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
      <Card title="Current geometry">
        <Table columns={holeColumns} data={geometry.tone_holes} />
      </Card>
      {optimization && (
        <Card title="Optimization sensitivity">
          <Table columns={sensitivityColumns} data={optimization.history} />
        </Card>
      )}
    </div>
  );
}
