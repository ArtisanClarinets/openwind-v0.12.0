import { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { Button } from '../components/Button.jsx';
import { NumberField } from '../components/NumberField.jsx';
import { Table } from '../components/Table.jsx';
import { useDebounce } from '../hooks/useDebounce.js';
import { recommend } from '../lib/apiClient.js';
import { sanitizeGeometry, validateHoleSpacing } from '../lib/validators.js';
import { loadSettings, saveSettings } from '../lib/storage.js';
import { useToast } from '../components/Toast.jsx';

const MIN_SPACING = 6;

export function GeometryPage() {
  const stored = loadSettings();
  const [geometry, setGeometry] = useState(
    stored.geometry ?? {
      bore_mm: 14.6,
      length_mm: 660,
      barrel_length_mm: 65,
      tone_holes: [],
      mouthpiece_params: {},
      metadata: {}
    }
  );
  const [issues, setIssues] = useState([]);
  const debouncedGeometry = useDebounce(geometry, 400);
  const { notify } = useToast();

  useEffect(() => {
    const sanitized = sanitizeGeometry(debouncedGeometry);
    saveSettings({ geometry: sanitized });
    setIssues(validateHoleSpacing(sanitized.tone_holes, MIN_SPACING));
  }, [debouncedGeometry]);

  const columns = useMemo(
    () => [
      { header: '#', accessor: 'index' },
      { header: 'Axial position (mm)', accessor: 'axial_pos_mm', cell: (row) => renderEditable(row, 'axial_pos_mm') },
      { header: 'Diameter (mm)', accessor: 'diameter_mm', cell: (row) => renderEditable(row, 'diameter_mm') },
      { header: 'Chimney (mm)', accessor: 'chimney_mm', cell: (row) => renderEditable(row, 'chimney_mm') },
      {
        header: 'Actions',
        accessor: 'actions',
        cell: (row) => (
          <Button variant="ghost" size="sm" onClick={() => removeHole(row.index)}>
            Remove
          </Button>
        )
      }
    ],
    [geometry]
  );

  function renderEditable(row, key) {
    return (
      <input
        type="number"
        min={0}
        step={0.1}
        value={row[key]}
        aria-label={`${key} for hole ${row.index + 1}`}
        onChange={(event) => updateHole(row.index, key, Number(event.target.value))}
      />
    );
  }

  const updateHole = (index, key, value) => {
    setGeometry((prev) => ({
      ...prev,
      tone_holes: prev.tone_holes.map((hole) => (hole.index === index ? { ...hole, [key]: value } : hole))
    }));
  };

  const removeHole = (index) => {
    setGeometry((prev) => ({
      ...prev,
      tone_holes: prev.tone_holes.filter((hole) => hole.index !== index).map((hole, idx) => ({ ...hole, index: idx }))
    }));
  };

  const addHole = () => {
    setGeometry((prev) => ({
      ...prev,
      tone_holes: [
        ...prev.tone_holes,
        {
          index: prev.tone_holes.length,
          axial_pos_mm: prev.tone_holes.length ? prev.tone_holes.at(-1).axial_pos_mm + 20 : 30,
          diameter_mm: 8,
          chimney_mm: 12,
          closed: false
        }
      ]
    }));
  };

  const handleRecommend = async () => {
    try {
      const response = await recommend({ target_a4_hz: 440, scale: 'equal' });
      setGeometry(response.geometry);
      notify('Recommendation updated', 'success');
    } catch (error) {
      notify('Recommendation failed', 'error');
    }
  };

  return (
    <div className="page-grid">
      <Card title="Bore and barrel">
        <div className="grid-two">
          <NumberField label="Bore" value={geometry.bore_mm} unit="mm" onChange={(value) => setGeometry((prev) => ({ ...prev, bore_mm: value }))} />
          <NumberField label="Length" value={geometry.length_mm} unit="mm" onChange={(value) => setGeometry((prev) => ({ ...prev, length_mm: value }))} />
          <NumberField label="Barrel" value={geometry.barrel_length_mm} unit="mm" onChange={(value) => setGeometry((prev) => ({ ...prev, barrel_length_mm: value }))} />
        </div>
        <Button onClick={handleRecommend}>Recommend layout</Button>
      </Card>
      <Card title="Tone holes" action={<Button variant="secondary" onClick={addHole}>Add hole</Button>}>
        <Table columns={columns} data={geometry.tone_holes} />
        {issues.length > 0 && (
          <div className="validation-block">
            <strong>Spacing warnings:</strong>
            <ul>
              {issues.map((item) => (
                <li key={item.index}>{item.message}</li>
              ))}
            </ul>
          </div>
        )}
      </Card>
    </div>
  );
}
