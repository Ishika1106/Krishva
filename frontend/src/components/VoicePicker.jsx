// One voice engine: the Krishva server. A Test button confirms sound works
// before a photo is uploaded, which is the quickest way to tell whether
// audio is the problem or something else.
export default function VoicePicker({ onTest, t, testing }) {
  return (
    <div className="voice-picker">
      <div className="d-flex align-items-center justify-content-between gap-2">
        <div>
          <div className="small fw-semibold text-secondary">{t('voice_choice')}</div>
          <div className="small text-muted">{t('server_voice_note')}</div>
        </div>
        <button
          type="button"
          className="btn btn-sm btn-outline-success text-nowrap"
          onClick={onTest}
          disabled={testing}
        >
          {testing ? t('voice_testing') : t('voice_test')}
        </button>
      </div>
    </div>
  );
}
