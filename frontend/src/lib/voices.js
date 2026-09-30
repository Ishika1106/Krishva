// Voice selection that works on every OS.
// Browser speechSynthesis is the only engine that is guaranteed present on
// Mac, Windows, Android and iOS, so it is the default. It uses whatever
// voices the device already has, which is why we list them for the user to
// pick from. The server gTTS path is the fallback when no local voice fits.
export function listVoices() {
  if (typeof window === 'undefined' || !window.speechSynthesis) return [];
  return window.speechSynthesis.getVoices() || [];
}

export const isSpeechSupported = () =>
  typeof window !== 'undefined' && !!window.speechSynthesis;

// Voices for a language, best match first, with a default when none match.
// Underscores are normalised because some Android builds report "en_US"
// and "hi_IN" rather than the hyphenated form.
const norm = (l) => (l || '').toLowerCase().replace(/_/g, '-');

export function voicesFor(lang, voices = listVoices()) {
  const tag = lang === 'hi' ? 'hi' : 'en';
  const seen = new Set();
  const exact = [];
  const base = [];
  const regional = [];
  for (const v of voices) {
    const l = norm(v.lang);
    if (!l.startsWith(tag) || seen.has(v.voiceURI)) continue;
    seen.add(v.voiceURI);
    if (l === `${tag}-in`) exact.push(v);
    else if (l === tag || l.startsWith(`${tag}-`)) regional.push(v);
    else base.push(v);
  }
  return [...exact, ...regional, ...base];
}

// Best automatic choice, used when the user has not picked one.
export function pickVoice(lang, voices = listVoices()) {
  const match = voicesFor(lang, voices);
  if (!match.length) return null;
  const local = match.find((v) => v.localService);
  return local || match[0];
}

// Label for the dropdown, with a readable name when the OS gives none.
export function voiceLabel(v) {
  const name = (v.name || '').trim();
  const lang = v.lang || '?';
  return name ? `${name} (${lang})` : lang;
}
