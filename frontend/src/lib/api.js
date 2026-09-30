// Empty backendUrl = auto-detect: localhost:8000 in dev, same origin once hosted.
export const CONFIG = { backendUrl: '' };

// A hosted page is already on the backend's origin, so only dev needs the fixed port.
function resolveApiBase() {
  if (CONFIG.backendUrl) return CONFIG.backendUrl.replace(/\/+$/, '');
  const { protocol, hostname, origin } = window.location;
  const local =
    protocol === 'file:' || /^(localhost|127\.0\.0\.1|\[::1\]|0\.0\.0\.0)$/i.test(hostname);
  return local ? 'http://localhost:8000' : origin;
}

export const API_URL = resolveApiBase();

export async function fetchUi() {
  const res = await fetch(`${API_URL}/`);
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}

export async function predict(file) {
  const body = new FormData();
  body.append('file', file);
  const res = await fetch(`${API_URL}/api/predict`, { method: 'POST', body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Server error ${res.status}`);
  return data;
}

export async function speakUrl(text, lang) {
  const res = await fetch(`${API_URL}/api/speak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, lang }),
  });
  if (!res.ok) throw new Error('speak failed');
  return URL.createObjectURL(await res.blob());
}

export const isLocalDev = () =>
  window.location.protocol === 'file:' ||
  /^(localhost|127\.0\.0\.1|\[::1\])$/i.test(window.location.hostname);
