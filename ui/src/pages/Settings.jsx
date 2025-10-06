import { useEffect, useState } from 'react';
import { Card } from '../components/Card.jsx';
import { NumberField } from '../components/NumberField.jsx';
import { Switch } from '../components/Switch.jsx';
import { loadSettings, saveSettings } from '../lib/storage.js';
import { useToast } from '../components/Toast.jsx';
import { useWorkspace } from '../lib/workspace.jsx';

export function SettingsPage() {
  const stored = loadSettings();
  const [settings, setSettings] = useState({
    a4: stored.a4 ?? 440,
    temperature: stored.temperature ?? 22,
    freq_min: stored.freq_min ?? 100,
    freq_max: stored.freq_max ?? 2200,
    darkMode: true
  });
  const { notify } = useToast();
  const { recommendationOptions, setRecommendationOptions } = useWorkspace();

  useEffect(() => {
    saveSettings(settings);
  }, [settings]);

  useEffect(() => {
    setSettings((prev) =>
      prev.a4 === recommendationOptions.targetA4Hz
        ? prev
        : { ...prev, a4: recommendationOptions.targetA4Hz }
    );
  }, [recommendationOptions.targetA4Hz]);

  return (
    <div className="page-grid">
      <Card title="Environment">
        <div className="grid-two">
          <NumberField
            label="Concert A4"
            value={settings.a4}
            unit="Hz"
            onChange={(value) => {
              setSettings((prev) => ({ ...prev, a4: value }));
              setRecommendationOptions((prev) => ({ ...prev, targetA4Hz: value }));
            }}
          />
          <NumberField label="Temperature" value={settings.temperature} unit="°C" onChange={(value) => setSettings((prev) => ({ ...prev, temperature: value }))} />
          <NumberField label="Frequency min" value={settings.freq_min} unit="Hz" onChange={(value) => setSettings((prev) => ({ ...prev, freq_min: value }))} />
          <NumberField label="Frequency max" value={settings.freq_max} unit="Hz" onChange={(value) => setSettings((prev) => ({ ...prev, freq_max: value }))} />
        </div>
        <Switch
          id="dark-mode"
          label="Dark mode"
          description="Use dark theme in the UI"
          checked={settings.darkMode}
          onChange={(checked) => {
            setSettings((prev) => ({ ...prev, darkMode: checked }));
            document.documentElement.dataset.theme = checked ? 'dark' : 'light';
            notify(`Theme switched to ${checked ? 'dark' : 'light'}`, 'info');
          }}
        />
      </Card>
    </div>
  );
}
