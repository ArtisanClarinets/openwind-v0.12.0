import { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { ChartImpedance } from '../components/ChartImpedance.jsx';
import { ChartIntonation } from '../components/ChartIntonation.jsx';
import { NumberField } from '../components/NumberField.jsx';
import { Button } from '../components/Button.jsx';
import { Table } from '../components/Table.jsx';
import { Switch } from '../components/Switch.jsx';
import { simulate } from '../lib/apiClient.js';
import { useDebounce } from '../hooks/useDebounce.js';
import { useToast } from '../components/Toast.jsx';
import { useWorkspace } from '../lib/workspace.jsx';
import { DEFAULT_NOTES, TRANSPOSITIONS } from '../lib/constants.js';

function downloadFile(filename, content, type = 'application/json') {
  const blob = new Blob([content], { type });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

export function SimulationPage() {
  const {
    geometry,
    simulationOptions,
    setSimulationOptions,
    autosimulate,
    setAutosimulate,
    simulationResult,
    setSimulationResult,
    selectedNotes,
    setSelectedNotes
  } = useWorkspace();
  const [loading, setLoading] = useState(false);
  const debouncedOptions = useDebounce(simulationOptions, 320);
  const debouncedNotes = useDebounce(selectedNotes, 320);
  const { notify } = useToast();

  useEffect(() => {
    if (!geometry || !autosimulate) return;
    runSimulation(geometry, debouncedOptions, debouncedNotes, true);
  }, [geometry, autosimulate, debouncedOptions, debouncedNotes]);

  const runSimulation = async (geom, options, notes, silent = false) => {
    try {
      setLoading(true);
      const payload = { geometry: geom, options, fingering_notes: notes };
      const response = await simulate(payload);
      setSimulationResult(response);
      if (!silent) {
        notify('Simulation completed', 'success');
      }
    } catch (error) {
      notify('Simulation failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const impedanceData = useMemo(() => {
    if (!simulationResult) return [];
    return simulationResult.freq_hz.map((freq, index) => ({
      freq,
      abs: simulationResult.zin_abs[index],
      re: simulationResult.zin_re[index]
    }));
  }, [simulationResult]);

  const intonationData = useMemo(
    () => simulationResult?.intonation?.map((item) => ({ note: item.note, cents: item.cents, midi: item.midi })) ?? [],
    [simulationResult]
  );

  const metrics = useMemo(() => {
    if (!simulationResult?.intonation || simulationResult.intonation.length === 0) {
      return null;
    }
    const cents = simulationResult.intonation.map((item) => item.cents);
    const avg = cents.reduce((sum, value) => sum + value, 0) / cents.length;
    const maxAbs = Math.max(...cents.map((value) => Math.abs(value)));
    return {
      average: avg,
      maxDeviation: maxAbs,
      noteCount: cents.length
    };
  }, [simulationResult]);

  const notesColumns = useMemo(
    () => [
      { header: 'Note', accessor: 'note' },
      { header: 'Cents', accessor: 'cents', cell: (row) => row.cents.toFixed(2) },
      {
        header: 'Resonance (Hz)',
        accessor: 'resonance_hz',
        cell: (row) => (typeof row.resonance_hz === 'number' ? row.resonance_hz.toFixed(1) : '—')
      },
      {
        header: 'Target (Hz)',
        accessor: 'target_hz',
        cell: (row) => (typeof row.target_hz === 'number' ? row.target_hz.toFixed(1) : '—')
      }
    ],
    []
  );

  const handleExport = (format) => {
    if (!simulationResult) {
      notify('Run a simulation first', 'error');
      return;
    }
    if (format === 'json') {
      downloadFile(
        `simulation-${Date.now()}.json`,
        JSON.stringify(simulationResult, null, 2),
        'application/json'
      );
    } else if (format === 'csv') {
      const header = 'note,cents,resonance_hz,target_hz';
      const rows = simulationResult.intonation
        .map((item) => `${item.note},${item.cents.toFixed(2)},${item.resonance_hz.toFixed(2)},${item.target_hz.toFixed(2)}`)
        .join('\n');
      downloadFile(`simulation-${Date.now()}.csv`, `${header}\n${rows}`, 'text/csv');
    }
    notify(`Exported ${format.toUpperCase()} snapshot`, 'success');
  };

  const toggleNote = (note) => {
    setSelectedNotes((current) => {
      const exists = current.includes(note);
      if (exists) {
        return current.filter((item) => item !== note);
      }
      const ordered = [...current, note];
      return DEFAULT_NOTES.filter((item) => ordered.includes(item));
    });
  };

  if (!geometry) {
    return <p>Load a geometry in the builder to simulate.</p>;
  }

  return (
    <div className="page-grid simulation-grid">
      <Card className="guidance-card" title="Understand how your design will sound">
        <p>
          This page sends your current geometry to the OpenWInD physics engine. You can run it once
          or let it update automatically as you tweak values. The summaries below translate the
          technical output into plain language so you can focus on musical decisions.
        </p>
        <ol>
          <li>Review the simulation options – defaults suit a typical rehearsal room.</li>
          <li>Select the fingerings you care about most. The model only computes the notes you pick.</li>
          <li>
            Compare the charts and tables. Peaks in the impedance graph indicate strong resonances;
            the intonation view reports how sharp or flat each note is.
          </li>
        </ol>
      </Card>
      <Card
        title="Simulation options"
        action={
          <div className="card-action-row">
            <Button onClick={() => runSimulation(geometry, simulationOptions, selectedNotes)}>Simulate now</Button>
            <Button variant="secondary" onClick={() => handleExport('json')} disabled={!simulationResult}>
              Export JSON
            </Button>
            <Button variant="secondary" onClick={() => handleExport('csv')} disabled={!simulationResult}>
              Export CSV
            </Button>
          </div>
        }
      >
        <p>
          These controls mirror the settings a player might encounter. Small adjustments can help
          you replicate concert hall conditions or outdoor performances.
        </p>
        <div className="grid-two">
          <NumberField
            label="Temperature"
            value={simulationOptions.temp_C}
            unit="°C"
            description="Warmer air lowers pitch slightly; colder air raises it."
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, temp_C: value }))}
          />
          <NumberField
            label="Freq. min"
            value={simulationOptions.freq_min_hz}
            unit="Hz"
            description="Lowest frequency to analyse. Keep it near the instrument's fundamental."
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, freq_min_hz: value }))}
          />
          <NumberField
            label="Freq. max"
            value={simulationOptions.freq_max_hz}
            unit="Hz"
            description="Highest frequency to include. Larger ranges take longer to compute."
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, freq_max_hz: value }))}
          />
          <NumberField
            label="Points"
            value={simulationOptions.n_points}
            description="How many samples to calculate between the min and max frequency."
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, n_points: value }))}
          />
          <NumberField
            label="Modes"
            value={simulationOptions.modes}
            step={1}
            min={1}
            description="Number of acoustic modes to consider. Higher counts add detail."
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, modes: Math.max(1, Math.round(value)) }))}
          />
          <NumberField
            label="Concert pitch"
            value={simulationOptions.concert_pitch_hz}
            unit="Hz"
            step={0.1}
            description="Reference tuning (A4) used when calculating intonation offsets."
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, concert_pitch_hz: value }))}
          />
        </div>
        <label className="ow-select">
          <span>Transposition</span>
          <p className="select-help">Match the written part to the sounding pitch of your instrument.</p>
          <select
            value={simulationOptions.transposition}
            onChange={(event) => setSimulationOptions((prev) => ({ ...prev, transposition: event.target.value }))}
          >
            {TRANSPOSITIONS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <Switch
          id="simulation-autosim"
          label="Auto-run"
          description="Debounced runs when geometry or parameters change"
          checked={autosimulate}
          onChange={setAutosimulate}
        />
        {loading && <p aria-live="polite">Simulating…</p>}
        {metrics && (
          <div className="metrics-inline" aria-live="polite">
            <span>{metrics.noteCount} notes analysed.</span>
            <span>Avg deviation {metrics.average.toFixed(2)} cents.</span>
            <span>Max abs deviation {metrics.maxDeviation.toFixed(2)} cents.</span>
          </div>
        )}

      </Card>
      <Card title="Fingerings">
        <p>
          Click the notes you would like to analyse. We preserve your selection order, so feel free
          to focus on one register at a time.
        </p>
        <div className="fingerings-grid">
          {DEFAULT_NOTES.map((note) => {
            const active = selectedNotes.includes(note);
            return (
              <button
                type="button"
                key={note}
                className={`chip ${active ? 'chip-active' : ''}`}
                onClick={() => toggleNote(note)}
                aria-pressed={active}
              >
                {note}
              </button>
            );
          })}
        </div>
        <div className="fingerings-actions">
          <Button variant="secondary" size="sm" onClick={() => setSelectedNotes(DEFAULT_NOTES)}>
            Select all
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setSelectedNotes([])}>
            Clear
          </Button>
        </div>
      </Card>
      <Card title="Input impedance">
        <p>
          Peaks in this chart show where the instrument naturally resonates. Higher peaks generally
          mean easier note production.
        </p>
        <ChartImpedance data={impedanceData} />
      </Card>
      <Card title="Intonation offsets">
        <p>
          Each bar displays how far a note is from your chosen concert pitch. Positive values are
          sharp, negative values are flat.
        </p>
        <ChartIntonation data={intonationData} />
      </Card>
      <Card title="Intonation table">
        <p>
          Prefer raw numbers? This table mirrors the chart above and includes the resonance frequency
          for each fingering.
        </p>
        <Table columns={notesColumns} data={simulationResult?.intonation ?? []} />
      </Card>
    </div>
  );
}
