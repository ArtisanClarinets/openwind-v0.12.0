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
import { DEFAULT_NOTES } from '../lib/constants.js';

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
        <div className="grid-two">
          <NumberField
            label="Temperature"
            value={simulationOptions.temp_C}
            unit="°C"
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, temp_C: value }))}
          />
          <NumberField
            label="Freq. min"
            value={simulationOptions.freq_min_hz}
            unit="Hz"
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, freq_min_hz: value }))}
          />
          <NumberField
            label="Freq. max"
            value={simulationOptions.freq_max_hz}
            unit="Hz"
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, freq_max_hz: value }))}
          />
          <NumberField
            label="Points"
            value={simulationOptions.n_points}
            onChange={(value) => setSimulationOptions((prev) => ({ ...prev, n_points: value }))}
          />
        </div>
        <Switch
          id="simulation-autosim"
          label="Auto-run"
          description="Debounced runs when geometry or parameters change"
          checked={autosimulate}
          onChange={setAutosimulate}
        />
        {loading && <p aria-live="polite">Simulating…</p>}
      </Card>
      <Card title="Fingerings">
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
        <ChartImpedance data={impedanceData} />
      </Card>
      <Card title="Intonation offsets">
        <ChartIntonation data={intonationData} />
      </Card>
      <Card title="Intonation table">
        <Table columns={notesColumns} data={simulationResult?.intonation ?? []} />
      </Card>
    </div>
  );
}
