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
      <Card className="guidance-card" title="Tailor the workspace to your environment">
        <p>
          Settings synchronise the defaults used across geometry recommendations and simulations. If
          you rehearse in unusual conditions (cold halls, alternative pitch standards), dial those in
          here once and the rest of the app will follow.
        </p>
        <ul>
          <li>
            <strong>Concert A4:</strong> updates both the recommender and simulation reference pitch.
          </li>
          <li>
            <strong>Temperature and frequency range:</strong> ensure the model matches your playing
            environment.
          </li>
          <li>Toggle dark mode if you prefer a brighter interface for printouts or presentations.</li>
        </ul>
      </Card>
      <Card title="Environment">
        <p>
          These values are stored locally in your browser. Adjust them whenever your rehearsal space
          changes – OpenWInD will remember them next time you sign in.
        </p>
        <div className="grid-two">
          <NumberField
            label="Concert A4"
            value={settings.a4}
            unit="Hz"
            description="Standard orchestral tuning is 440 Hz; some ensembles use 442 Hz or higher."
            onChange={(value) => {
              setSettings((prev) => ({ ...prev, a4: value }));
              setRecommendationOptions((prev) => ({ ...prev, targetA4Hz: value }));
            }}
          />
          <NumberField
            label="Temperature"
            value={settings.temperature}
            unit="°C"
            description="Used as the starting point for new simulations."
            onChange={(value) => setSettings((prev) => ({ ...prev, temperature: value }))}
          />
          <NumberField
            label="Frequency min"
            value={settings.freq_min}
            unit="Hz"
            description="Default low end for impedance plots and exports."
            onChange={(value) => setSettings((prev) => ({ ...prev, freq_min: value }))}
          />
          <NumberField
            label="Frequency max"
            value={settings.freq_max}
            unit="Hz"
            description="Default high end for impedance plots and exports."
            onChange={(value) => setSettings((prev) => ({ ...prev, freq_max: value }))}
          />
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
