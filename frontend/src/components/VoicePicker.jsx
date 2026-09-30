// Dropdown listing the voices the current device already has.
// Empty list means the OS has no voice for that language, and the parent
// falls back to the server, which is why the hint text explains that.
export default function VoicePicker({ voices, value, onChange, t, autoLabel, lang }) {
  return (
    <div className="voice-picker">
      <label className="small fw-semibold text-secondary" htmlFor="voiceSelect">
        {t('voice_choice')}
      </label>
      <select
        id="voiceSelect"
        className="form-select form-select-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">{autoLabel}</option>
        {voices.map((v) => (
          <option key={v.voiceURI} value={v.voiceURI}>
            {v.name || v.lang} ({v.lang})
          </option>
        ))}
      </select>
      {voices.length === 0 && (
        <div className="small text-muted mt-1">{t('no_local_voice')}</div>
      )}
    </div>
  );
}
