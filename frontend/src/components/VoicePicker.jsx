// Choose between device voices and server audio, and test the choice.
//
// Chrome's speechSynthesis often reports success (onstart/onend fire) while
// producing no sound at all, so it cannot be trusted as the only path. The
// server generates a real audio file that always plays, so it is the default
// and the device voices are opt-in.
export default function VoicePicker({
  voices, value, onChange, engine, onEngineChange, onTest, t, testing,
}) {
  return (
    <div className="voice-picker">
      <label className="small fw-semibold text-secondary" htmlFor="engineSelect">
        {t('voice_choice')}
      </label>
      <div className="d-flex gap-2">
        <select
          id="engineSelect"
          className="form-select form-select-sm"
          value={engine}
          onChange={(e) => onEngineChange(e.target.value)}
        >
          <option value="server">{t('engine_server')}</option>
          <option value="device" disabled={voices.length === 0}>
            {t('engine_device')}
          </option>
        </select>
        <button
          type="button"
          className="btn btn-sm btn-outline-success text-nowrap"
          onClick={onTest}
          disabled={testing}
        >
          {testing ? t('voice_testing') : t('voice_test')}
        </button>
      </div>

      {engine === 'device' && voices.length > 0 && (
        <select
          className="form-select form-select-sm mt-2"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-label={t('voice_auto')}
        >
          <option value="">{t('voice_auto')}</option>
          {voices.map((v) => (
            <option key={v.voiceURI} value={v.voiceURI}>
              {v.name || v.lang} ({v.lang})
            </option>
          ))}
        </select>
      )}

      <div className="small text-muted mt-1">{engine === 'server' ? t('server_voice_note') : t('device_voice_note')}</div>
    </div>
  );
}
