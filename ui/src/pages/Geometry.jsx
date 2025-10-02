import { useCallback, useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { Button } from '../components/Button.jsx';
import { NumberField } from '../components/NumberField.jsx';
import { Table } from '../components/Table.jsx';
import { Switch } from '../components/Switch.jsx';
import { useDebounce } from '../hooks/useDebounce.js';
import { recommend, fetchPreset } from '../lib/apiClient.js';
import { validateHoleSpacing } from '../lib/validators.js';
import { loadSettings } from '../lib/storage.js';
import { useToast } from '../components/Toast.jsx';
import { useWorkspace } from '../lib/workspace.jsx';

export function GeometryPage() {
  const {
    geometry,
    setGeometry,
    constraints,
    setConstraints,
    autosimulate,
    setAutosimulate,
    setLastRecommendation
  } = useWorkspace();
  const [issues, setIssues] = useState([]);
  const debouncedGeometry = useDebounce(geometry, 320);
  const { notify } = useToast();

  useEffect(() => {
    setIssues(validateHoleSpacing(debouncedGeometry.tone_holes ?? [], constraints.minSpacingMm));
  }, [debouncedGeometry, constraints.minSpacingMm]);

  const spacingWarnings = useMemo(() => {
    const map = new Map();
    for (const issue of issues) {
      map.set(issue.index, issue.message);
    }
    return map;
  }, [issues]);

  const geometrySummary = useMemo(() => {
    const holes = geometry.tone_holes ?? [];
    const diameters = holes.map((hole) => hole.diameter_mm);
    const spacing = holes.slice(1).map((hole, index) => hole.axial_pos_mm - holes[index].axial_pos_mm);
    return {
      holeCount: holes.length,
      closed: holes.filter((hole) => hole.closed).length,
      minDiameter: diameters.length ? Math.min(...diameters) : null,
      maxDiameter: diameters.length ? Math.max(...diameters) : null,
      minSpacing: spacing.length ? Math.min(...spacing) : null,
      maxSpacing: spacing.length ? Math.max(...spacing) : null
    };
  }, [geometry]);

  const updateHole = useCallback(
    (index, patch) => {
      setGeometry((previous) => ({
        ...previous,
        tone_holes: previous.tone_holes.map((hole) => (hole.index === index ? { ...hole, ...patch } : hole))
      }));
    },
    [setGeometry]
  );

  const moveHole = useCallback(
    (index, direction) => {
      setGeometry((previous) => {
        const next = [...previous.tone_holes];
        const target = index + direction;
        if (target < 0 || target >= next.length) {
          return previous;
        }
        const [removed] = next.splice(index, 1);
        next.splice(target, 0, removed);
        return {
          ...previous,
          tone_holes: next.map((hole, idx) => ({ ...hole, index: idx }))
        };
      });
    },
    [setGeometry]
  );

  const removeHole = useCallback(
    (index) => {
      setGeometry((previous) => ({
        ...previous,
        tone_holes: previous.tone_holes.filter((hole) => hole.index !== index).map((hole, idx) => ({ ...hole, index: idx }))
      }));
    },
    [setGeometry]
  );

  const duplicateHole = useCallback(
    (index) => {
      setGeometry((previous) => {
        const base = previous.tone_holes[index];
        if (!base) return previous;
        const clone = {
          ...base,
          index: base.index + 1,
          axial_pos_mm: base.axial_pos_mm + 8
        };
        const next = [...previous.tone_holes];
        next.splice(index + 1, 0, clone);
        return {
          ...previous,
          tone_holes: next.map((hole, idx) => ({ ...hole, index: idx }))
        };
      });
    },
    [setGeometry]
  );

  const addHole = useCallback(() => {
    setGeometry((previous) => {
      if (previous.tone_holes.length >= constraints.maxHoleCount) {
        notify(`Maximum of ${constraints.maxHoleCount} tone holes reached`, 'error');
        return previous;
      }
      const lastHole = previous.tone_holes.at(-1);
      const next = {
        index: previous.tone_holes.length,
        axial_pos_mm: lastHole ? lastHole.axial_pos_mm + constraints.minSpacingMm + 2 : 30,
        diameter_mm: Math.max(8, constraints.minDiameterMm + 1),
        chimney_mm: 12,
        closed: false
      };
      return {
        ...previous,
        tone_holes: [...previous.tone_holes, next]
      };
    });
  }, [constraints.maxHoleCount, constraints.minSpacingMm, constraints.minDiameterMm, notify, setGeometry]);

  const handleRecommend = useCallback(async () => {
    try {
      const globals = loadSettings();
      const response = await recommend({
        target_a4_hz: globals.a4 ?? 440,
        scale: 'equal',
        constraints: {
          min_spacing_mm: constraints.minSpacingMm,
          max_holes: constraints.maxHoleCount,
          min_diameter_mm: constraints.minDiameterMm,
          max_diameter_mm: constraints.maxDiameterMm
        }
      });
      setGeometry(response.geometry);
      setLastRecommendation({
        type: 'recommendation',
        loadedAt: new Date().toISOString(),
        description: response.message ?? 'FastAPI adapter'
      });
      notify('Recommendation updated', 'success');
    } catch (error) {
      notify('Recommendation failed', 'error');
    }
  }, [
    constraints.maxDiameterMm,
    constraints.maxHoleCount,
    constraints.minDiameterMm,
    constraints.minSpacingMm,
    notify,
    setGeometry,
    setLastRecommendation
  ]);

  const handlePreset = useCallback(async () => {
    try {
      const preset = await fetchPreset();
      setGeometry(preset.geometry);
      setLastRecommendation({
        type: 'preset',
        loadedAt: new Date().toISOString(),
        description: preset.metadata?.name ?? 'Factory preset'
      });
      notify('Factory preset applied', 'success');
    } catch (error) {
      notify('Unable to load preset', 'error');
    }
  }, [notify, setGeometry, setLastRecommendation]);

  const renderNumericInput = useCallback(
    (row, key, { min, max, step = 0.1, warning } = {}) => (
      <div className="tone-hole-input">
        <input
          type="number"
          min={min}
          max={max}
          step={step}
          value={row[key] ?? 0}
          aria-label={`${key} for hole ${row.index + 1}`}
          aria-invalid={Boolean(warning)}
          onChange={(event) => updateHole(row.index, { [key]: Number(event.target.value) })}
        />
        {warning && <span className="input-warning">{warning}</span>}
      </div>
    ),
    [updateHole]
  );

  const columns = useMemo(
    () => [
      { header: '#', accessor: 'index' },
      {
        header: 'Axial (mm)',
        accessor: 'axial_pos_mm',
        cell: (row) =>
          renderNumericInput(row, 'axial_pos_mm', {
            min: 0,
            step: 0.5,
            warning: spacingWarnings.get(row.index)
          })
      },
      {
        header: 'Diameter (mm)',
        accessor: 'diameter_mm',
        cell: (row) =>
          renderNumericInput(row, 'diameter_mm', {
            min: constraints.minDiameterMm,
            max: constraints.maxDiameterMm,
            step: 0.1
          })
      },
      {
        header: 'Chimney (mm)',
        accessor: 'chimney_mm',
        cell: (row) => renderNumericInput(row, 'chimney_mm', { min: 4, step: 0.5 })
      },
      {
        header: 'State',
        accessor: 'closed',
        cell: (row) => (
          <button
            type="button"
            className={`chip ${row.closed ? 'chip-closed' : 'chip-open'}`}
            onClick={() => updateHole(row.index, { closed: !row.closed })}
            aria-pressed={row.closed}
          >
            {row.closed ? 'Closed' : 'Open'}
          </button>
        )
      },
      {
        header: 'Actions',
        accessor: 'actions',
        cell: (row) => (
          <div className="hole-actions">
            <Button variant="ghost" size="sm" onClick={() => moveHole(row.index, -1)} aria-label={`Move hole ${row.index + 1} up`}>
              ↑
            </Button>
            <Button variant="ghost" size="sm" onClick={() => moveHole(row.index, 1)} aria-label={`Move hole ${row.index + 1} down`}>
              ↓
            </Button>
            <Button variant="ghost" size="sm" onClick={() => duplicateHole(row.index)} aria-label={`Duplicate hole ${row.index + 1}`}>
              ⧉
            </Button>
            <Button variant="ghost" size="sm" onClick={() => removeHole(row.index)} aria-label={`Remove hole ${row.index + 1}`}>
              ✕
            </Button>
          </div>
        )
      }
    ],
    [
      constraints.maxDiameterMm,
      constraints.minDiameterMm,
      duplicateHole,
      moveHole,
      removeHole,
      renderNumericInput,
      spacingWarnings,
      updateHole
    ]
  );

  return (
    <div className="page-grid geometry-grid">
      <Card
        title="Bore and barrel"
        action={
          <div className="card-action-row">
            <Button variant="secondary" onClick={handlePreset}>
              Load preset
            </Button>
            <Button onClick={handleRecommend}>Recommend layout</Button>
          </div>
        }
      >
        <div className="grid-two">
          <NumberField label="Bore" value={geometry.bore_mm} unit="mm" onChange={(value) => setGeometry((prev) => ({ ...prev, bore_mm: value }))} />
          <NumberField label="Length" value={geometry.length_mm} unit="mm" onChange={(value) => setGeometry((prev) => ({ ...prev, length_mm: value }))} />
          <NumberField label="Barrel" value={geometry.barrel_length_mm} unit="mm" onChange={(value) => setGeometry((prev) => ({ ...prev, barrel_length_mm: value }))} />
        </div>
        <Switch
          id="autosimulate-toggle"
          label="Auto-simulate"
          description="Debounce simulation updates when geometry changes"
          checked={autosimulate}
          onChange={setAutosimulate}
        />
      </Card>
      <Card
        title="Tone holes"
        action={
          <Button variant="secondary" onClick={addHole} aria-label="Add tone hole">
            Add hole
          </Button>
        }
      >
        <Table columns={columns} data={geometry.tone_holes} />
        {issues.length > 0 && (
          <div className="validation-block" role="alert">
            <strong>Spacing warnings:</strong>
            <ul>
              {issues.map((item) => (
                <li key={item.index}>{item.message}</li>
              ))}
            </ul>
          </div>
        )}
      </Card>
      <Card title="Constraints">
        <div className="grid-two">
          <NumberField
            label="Minimum spacing"
            value={constraints.minSpacingMm}
            unit="mm"
            min={2}
            step={0.5}
            onChange={(value) => setConstraints({ minSpacingMm: value })}
          />
          <NumberField
            label="Minimum diameter"
            value={constraints.minDiameterMm}
            unit="mm"
            min={2}
            step={0.1}
            onChange={(value) => setConstraints({ minDiameterMm: value })}
          />
          <NumberField
            label="Maximum diameter"
            value={constraints.maxDiameterMm}
            unit="mm"
            min={constraints.minDiameterMm}
            step={0.1}
            onChange={(value) => setConstraints({ maxDiameterMm: value })}
          />
          <NumberField
            label="Maximum holes"
            value={constraints.maxHoleCount}
            min={1}
            step={1}
            onChange={(value) => setConstraints({ maxHoleCount: Math.round(value) })}
          />
        </div>
      </Card>
      <Card title="Geometry summary">
        <dl className="geometry-summary">
          <div>
            <dt>Tone holes</dt>
            <dd>{geometrySummary.holeCount}</dd>
          </div>
          <div>
            <dt>Open / closed</dt>
            <dd>
              {geometrySummary.holeCount - geometrySummary.closed} / {geometrySummary.closed}
            </dd>
          </div>
          <div>
            <dt>Diameter range</dt>
            <dd>
              {geometrySummary.minDiameter === null
                ? '—'
                : `${geometrySummary.minDiameter.toFixed(1)}–${geometrySummary.maxDiameter.toFixed(1)} mm`}
            </dd>
          </div>
          <div>
            <dt>Spacing range</dt>
            <dd>
              {geometrySummary.minSpacing === null
                ? '—'
                : `${geometrySummary.minSpacing.toFixed(1)}–${geometrySummary.maxSpacing.toFixed(1)} mm`}
            </dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
