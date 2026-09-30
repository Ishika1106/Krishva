import { useEffect, useMemo, useRef, useState } from 'react';
import SegmentedToggle from './components/SegmentedToggle.jsx';
import ResultTable from './components/ResultTable.jsx';
import VoicePicker from './components/VoicePicker.jsx';
import { API_URL, fetchUi, isLocalDev, predict } from './lib/api.js';
import { translator } from './lib/i18n.js';
import { useSpeech } from './lib/useSpeech.js';

export default function App() {
  const [lang, setLang] = useState('en');
  const [voice, setVoice] = useState('off');
  const [apiUi, setApiUi] = useState(null);
  const [apiUp, setApiUp] = useState(null);
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState('');
  const inputRef = useRef(null);

  const t = useMemo(() => translator(apiUi, lang), [apiUi, lang]);
  const { speak, stop, speaking, note, setNote } = useSpeech();
  const [testing, setTesting] = useState(false);

  // Lets the user confirm audio works before uploading anything.
  const testVoice = async () => {
    setTesting(true);
    await speak(t('voice_sample'), lang, t);
    setTesting(false);
  };

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    let alive = true;
    fetchUi()
      .then((d) => {
        if (!alive) return;
        setApiUp(true);
        if (d.ui) setApiUi(d.ui);
      })
      .catch(() => alive && setApiUp(false));
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => () => stop(), [stop]);

  const topResult = results && results[0];
  const localised = (r) => (lang === 'hi' ? { name: r.name_hi, remedy: r.remedy_hi } : { name: r.name_en, remedy: r.remedy_en });

  const speakTop = () => {
    if (!topResult) return;
    const L = localised(topResult);
    speak(`${L.name}. ${L.remedy}`, lang, t);
  };

  const handleLanguage = (next) => {
    if (next === lang) return;
    stop();
    setLang(next);
    // Re-read in the new language without re-uploading.
    if (voice === 'on' && topResult) {
      const r = topResult;
      const L = next === 'hi' ? { name: r.name_hi, remedy: r.remedy_hi } : { name: r.name_en, remedy: r.remedy_en };
      speak(`${L.name}. ${L.remedy}`, next, translator(apiUi, next));
    }
  };

  const handleVoice = (next) => {
    setVoice(next);
    if (next === 'on') speakTop();
    else stop();
  };

  const onPick = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(ev.target.result);
    reader.readAsDataURL(file);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    const file = inputRef.current.files && inputRef.current.files[0];
    if (!file) return;

    setBusy(true);
    setError('');
    setResults(null);
    setNote('');
    stop();

    try {
      const data = await predict(file);
      setApiUp(true);
      if (data.ui) setApiUi(data.ui);
      setResults(data.results);
      if (voice === 'on') {
        const r = data.results[0];
        const L = lang === 'hi' ? { name: r.name_hi, remedy: r.remedy_hi } : { name: r.name_en, remedy: r.remedy_en };
        speak(`${L.name}. ${L.remedy}`, lang, t);
      }
    } catch (err) {
      setApiUp(false);
      setError(err.message || t('api_down'));
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    stop();
    setResults(null);
    setPreview('');
    setError('');
    setNote('');
    if (inputRef.current) inputRef.current.value = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (inputRef.current) inputRef.current.focus();
  };

  // Only warn when the chosen path genuinely cannot work.
  const voiceHint = note || (voice !== 'on' ? '' : apiUp === false ? t('api_down') : '');

  return (
    <div className="container py-4" style={{ maxWidth: 700 }}>
      <header className="d-flex align-items-center gap-3 mb-1">
        <div className="brand-mark">Kr</div>
        <div>
          <h2 className="mb-0 text-success fw-bold">Krishva</h2>
          <div className="tagline">{t('tagline')}</div>
        </div>
      </header>

      <div className="setting-card p-3 my-3">
        <div className="row g-3">
          <div className="col-sm-6">
            <SegmentedToggle
              name="lang"
              label={t('language')}
              value={lang}
              onChange={handleLanguage}
              options={[
                { value: 'en', label: 'English' },
                { value: 'hi', label: 'हिन्दी' },
              ]}
            />
          </div>
          <div className="col-sm-6">
            <SegmentedToggle
              name="voice"
              label={t('voice')}
              value={voice}
              onChange={handleVoice}
              options={[
                { value: 'off', label: t('voice_off') },
                { value: 'on', label: t('voice_on') },
              ]}
            />
          </div>
        </div>
        {voice === 'on' && (
          <div className="row g-2 mt-1">
            <div className="col-12">
              <VoicePicker onTest={testVoice} testing={testing} t={t} />
            </div>
          </div>
        )}
        {(voiceHint || note) && <div className="small text-muted mt-2">{note || voiceHint}</div>}
      </div>

      <p className="text-muted">{t('intro')}</p>

      <form onSubmit={onSubmit}>
        <input
          ref={inputRef}
          type="file"
          className="form-control mb-2"
          accept="image/*"
          onChange={onPick}
          aria-label={t('disease')}
        />
        {preview && <img src={preview} className="preview rounded border" alt="preview" />}
        <button type="submit" className="btn btn-success w-100 fw-bold mb-3" disabled={busy}>
          {busy ? t('analyzing') : t('analyze')}
        </button>
      </form>

      {error && (
        <div className={`alert ${apiUp === false ? 'alert-danger' : 'alert-warning'}`}>
          {error}
          {apiUp === false && (
            <div className="small mt-1">
              {API_URL} &middot; {isLocalDev() ? t('api_down_local') : t('api_down_hosted')}
            </div>
          )}
        </div>
      )}

      {results && (
        <ResultTable
          results={results}
          t={t}
          lang={lang}
          speaking={speaking}
          onReplay={speakTop}
          onNewScan={reset}
        />
      )}

      <hr className="my-4" />
      <p className="text-muted small mb-0">{t('footer')}</p>
    </div>
  );
}
