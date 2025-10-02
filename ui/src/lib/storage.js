const KEY = 'openwind-bb-clarinet-settings';

export function loadSettings() {
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (error) {
    console.warn('Unable to read settings', error);
    return {};
  }
}

export function saveSettings(patch) {
  try {
    const current = loadSettings();
    const next = { ...current, ...patch };
    window.localStorage.setItem(KEY, JSON.stringify(next));
    return next;
  } catch (error) {
    console.warn('Unable to save settings', error);
    return patch;
  }
}
