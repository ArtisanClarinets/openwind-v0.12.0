import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { Button } from '../components/Button.jsx';
import { NumberField } from '../components/NumberField.jsx';
import { Table } from '../components/Table.jsx';
import { Switch } from '../components/Switch.jsx';
import { useDebounce } from '../hooks/useDebounce.js';
import { recommend, fetchPreset } from '../lib/apiClient.js';
import { validateHoleSpacing } from '../lib/validators.js';
import { useToast } from '../components/Toast.jsx';
import { useWorkspace } from '../lib/workspace.jsx';
import {
  PLAYER_ARTICULATIONS,
  PLAYER_BRIGHTNESS,
  PLAYER_PROFILES,
  RECOMMENDATION_SCALES,
  REGISTER_OPTIONS
} from '../lib/constants.js';

export function GeometryPage() {
  const {
    geometry,
    setGeometry,
    constraints,
    setConstraints,
    autosimulate,
    setAutosimulate,
    setLastRecommendation,
    recommendationOptions,
    setRecommendationOptions
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
    const undercuts = holes.map((hole) => hole.undercut_mm ?? 0);
    return {
      holeCount: holes.length,
      closed: holes.filter((hole) => hole.closed).length,
      minDiameter: diameters.length ? Math.min(...diameters) : null,
      maxDiameter: diameters.length ? Math.max(...diameters) : null,
      minSpacing: spacing.length ? Math.min(...spacing) : null,
      maxSpacing: spacing.length ? Math.max(...spacing) : null,
      minUndercut: undercuts.length ? Math.min(...undercuts) : null,
      maxUndercut: undercuts.length ? Math.max(...undercuts) : null
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
          undercut_mm: lastHole?.undercut_mm ?? 0.8,
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
      const response = await recommend({
        target_a4_hz: recommendationOptions.targetA4Hz,
        scale: recommendationOptions.scale,
        constraints: {
          min_spacing_mm: constraints.minSpacingMm,
          max_holes: constraints.maxHoleCount,
          min_diameter_mm: constraints.minDiameterMm,
          max_diameter_mm: constraints.maxDiameterMm
        },
        player_pref: {
          profile: recommendationOptions.playerProfile,
          articulation: recommendationOptions.playerArticulation,
          brightness: recommendationOptions.playerBrightness
        },
        include_register: recommendationOptions.includeRegister
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
    setLastRecommendation,
    recommendationOptions
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
        header: 'Undercut (mm)',
        accessor: 'undercut_mm',
        cell: (row) => renderNumericInput(row, 'undercut_mm', { min: 0, step: 0.05 })
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
            <Button
              variant="ghost"
              size="sm"
              onClick={() => moveHole(row.index, -1)}
              aria-label={`Move hole ${row.index + 1} up`}
            >
              ↑
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => moveHole(row.index, 1)}
              aria-label={`Move hole ${row.index + 1} down`}
            >
              ↓
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => duplicateHole(row.index)}
              aria-label={`Duplicate hole ${row.index + 1}`}
            >
              ⧉
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => removeHole(row.index)}
              aria-label={`Remove hole ${row.index + 1}`}
            >
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
      <Card className="guidance-card" title="How to shape your instrument">
        <p>
          Start with the bore dimensions, then review each tone hole row in the table below. You can
          drag the order, duplicate entries or remove them entirely. If a value falls outside the
          recommended range, a red hint will appear so you know what to adjust.
        </p>
        <ol>
          <li>
            Set your desired concert pitch and player preferences in “Recommendation options” to
            receive tailored layouts.
          </li>
          <li>
            Confirm the bore, instrument length and barrel dimensions – these set the physical scale
            for every calculation.
          </li>
          <li>
            Edit tone holes directly in the table. Buttons on the right let you reorder, clone or
            delete rows in one click.
          </li>
          <li>
            Adjust the constraints at the bottom if you want the automatic tools to explore a wider
            (or tighter) range of designs.
          </li>
        </ol>
      </Card>
      <Card title="Recommendation options">
        <p>
          Tell OpenWInD what kind of player and repertoire you are targeting. These preferences feed
          into the server-side recommender that can populate the tone-hole layout for you.
        </p>
        <div className="grid-two">
          <NumberField
            label="Target A4"
            value={recommendationOptions.targetA4Hz}
            unit="Hz"
            step={0.1}
            min={430}
            max={450}
            description="Sets the reference pitch for all automatic suggestions."
            onChange={(value) => setRecommendationOptions((prev) => ({ ...prev, targetA4Hz: value }))}
          />
          <label className="ow-select">
            <span>Pitch scale</span>
            <p className="select-help">
              Choose the tuning system that best matches your ensemble. Equal temperament is the
              modern default.
            </p>
            <select
              value={recommendationOptions.scale}
              onChange={(event) => setRecommendationOptions((prev) => ({ ...prev, scale: event.target.value }))}
            >
              {RECOMMENDATION_SCALES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="ow-select">
            <span>Register focus</span>
            <p className="select-help">Tell the recommender which playing register to favour.</p>
            <select
              value={recommendationOptions.includeRegister}
              onChange={(event) =>
                setRecommendationOptions((prev) => ({ ...prev, includeRegister: event.target.value }))
              }
            >
              {REGISTER_OPTIONS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="ow-select">
            <span>Player profile</span>
            <p className="select-help">Match the response to the experience level of the player.</p>
            <select
              value={recommendationOptions.playerProfile}
              onChange={(event) =>
                setRecommendationOptions((prev) => ({ ...prev, playerProfile: event.target.value }))
              }
            >
              {PLAYER_PROFILES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="ow-select">
            <span>Articulation</span>
            <p className="select-help">Fine-tune how resistant or flexible the tone holes should feel.</p>
            <select
              value={recommendationOptions.playerArticulation}
              onChange={(event) =>
                setRecommendationOptions((prev) => ({ ...prev, playerArticulation: event.target.value }))
              }
            >
              {PLAYER_ARTICULATIONS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="ow-select">
            <span>Brightness</span>
            <p className="select-help">Pick a tonal colour ranging from dark and mellow to bright.</p>
            <select
              value={recommendationOptions.playerBrightness}
              onChange={(event) =>
                setRecommendationOptions((prev) => ({ ...prev, playerBrightness: event.target.value }))
              }
            >
              {PLAYER_BRIGHTNESS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Card>
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
        <p>
          These core dimensions define the clarinet body. They accept sensible defaults, so feel free
          to experiment – you can always reload the preset above.
        </p>
        <div className="grid-two">
          <NumberField
            label="Bore"
            value={geometry.bore_mm}
            unit="mm"
            description="Internal diameter of the main bore. Larger values generally darken the tone."
            onChange={(value) => setGeometry((prev) => ({ ...prev, bore_mm: value }))}
          />
          <NumberField
            label="Length"
            value={geometry.length_mm}
            unit="mm"
            description="Overall tube length from mouthpiece to bell end."
            onChange={(value) => setGeometry((prev) => ({ ...prev, length_mm: value }))}
          />
          <NumberField
            label="Barrel"
            value={geometry.barrel_length_mm}
            unit="mm"
            description="Length of the detachable barrel section at the top of the clarinet."
            onChange={(value) => setGeometry((prev) => ({ ...prev, barrel_length_mm: value }))}
          />
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
        <p>
          Enter measurements for each tone hole. Hover over the “State” chip to toggle between open
          and closed fingerings. Use the arrow buttons to reorder the layout without retyping values.
        </p>
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
      <Card title="Visualise the clarinet body">
        <p>
          These interactive visuals mirror the OpenWInD demo: the chart shows where each chimney
          sits along the tube and how its diameter compares to the bore, while the preview sketches a
          simplified clarinet body so you can spot spacing or height imbalances at a glance.
        </p>
        <div className="geometry-visual-grid">
          <ChartToneHoles
            toneHoles={geometry.tone_holes}
            boreMm={geometry.bore_mm}
            lengthMm={geometry.length_mm}
          />
          <ClarinetPreview
            toneHoles={geometry.tone_holes}
            lengthMm={geometry.length_mm}
            boreMm={geometry.bore_mm}
          />
        </div>
      </Card>
      <Card title="Constraints">
        <p>
          Constraints keep automatic tools within practical limits. If you want broader
          experimentation, widen these values; for production-ready plans, tighten them.
        </p>
        <div className="grid-two">
          <NumberField
            label="Minimum spacing"
            value={constraints.minSpacingMm}
            unit="mm"
            min={2}
            step={0.5}
            description="Enforces a safe minimum distance between tone holes."
            onChange={(value) => setConstraints({ minSpacingMm: value })}
          />
          <NumberField
            label="Minimum diameter"
            value={constraints.minDiameterMm}
            unit="mm"
            min={2}
            step={0.1}
            description="Prevents the recommender from suggesting unplayably small holes."
            onChange={(value) => setConstraints({ minDiameterMm: value })}
          />
          <NumberField
            label="Maximum diameter"
            value={constraints.maxDiameterMm}
            unit="mm"
            min={constraints.minDiameterMm}
            step={0.1}
            description="Upper limit for hole size, keeping ergonomics comfortable."
            onChange={(value) => setConstraints({ maxDiameterMm: value })}
          />
          <NumberField
            label="Maximum holes"
            value={constraints.maxHoleCount}
            min={1}
            step={1}
            description="Caps how many tone holes the automatic tools may create."
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
          <div>
            <dt>Undercut range</dt>
            <dd>
              {geometrySummary.minUndercut === null
                ? '—'
                : `${geometrySummary.minUndercut.toFixed(2)}–${geometrySummary.maxUndercut.toFixed(2)} mm`}
            </dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
