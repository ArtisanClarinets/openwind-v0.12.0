import { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { ChartImpedance } from '../components/ChartImpedance.jsx';
import { ChartIntonation } from '../components/ChartIntonation.jsx';
import { NumberField } from '../components/NumberField.jsx';
import { Button } from '../components/Button.jsx';
import { simulate } from '../lib/apiClient.js';
import { loadSettings } from '../lib/storage.js';
import { useDebounce } from '../hooks/useDebounce.js';
import { useToast } from '../components/Toast.jsx';

export function SimulationPage() {
  const [geometry, setGeometry] = useState(loadSettings().geometry ?? null);
  const [options, setOptions] = useState({ temp_C: 22, freq_min_hz: 100, freq_max_hz: 2200, n_points: 512, modes: 6 });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const debouncedOptions = useDebounce(options, 400);
  const { notify } = useToast();

  useEffect(() => {
    setGeometry(loadSettings().geometry ?? null);
  }, []);

  useEffect(() => {
    if (!geometry) return;
    runSimulation(geometry, debouncedOptions);
  }, [geometry, debouncedOptions]);

  const runSimulation = async (geom, simOptions) => {
    try {
      setLoading(true);
      const payload = { geometry: geom, options: simOptions };
      const response = await simulate(payload);
      setResult(response);
    } catch (error) {
      notify('Simulation failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const impedanceData = useMemo(() => {
    if (!result) return [];
    return result.freq_hz.map((freq, index) => ({ freq, abs: result.zin_abs[index], re: result.zin_re[index] }));
  }, [result]);

  const intonationData = result?.intonation?.map((item) => ({ note: item.note, cents: item.cents })) ?? [];

  if (!geometry) {
    return <p>Load a geometry in the builder to simulate.</p>;
  }

  return (
    <div className="page-grid">
      <Card title="Simulation options" action={<Button onClick={() => runSimulation(geometry, options)}>Simulate now</Button>}>
        <div className="grid-two">
          <NumberField label="Temperature" value={options.temp_C} unit="°C" onChange={(value) => setOptions((prev) => ({ ...prev, temp_C: value }))} />
          <NumberField label="Freq. min" value={options.freq_min_hz} unit="Hz" onChange={(value) => setOptions((prev) => ({ ...prev, freq_min_hz: value }))} />
          <NumberField label="Freq. max" value={options.freq_max_hz} unit="Hz" onChange={(value) => setOptions((prev) => ({ ...prev, freq_max_hz: value }))} />
          <NumberField label="Points" value={options.n_points} onChange={(value) => setOptions((prev) => ({ ...prev, n_points: value }))} />
        </div>
        {loading && <p>Simulating…</p>}
      </Card>
      <Card title="Input impedance">
        <ChartImpedance data={impedanceData} />
      </Card>
      <Card title="Intonation offsets">
        <ChartIntonation data={intonationData} />
      </Card>
    </div>
  );
}
