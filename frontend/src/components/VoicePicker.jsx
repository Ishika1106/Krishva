// One engine only, so Test voice is the quickest way to check audio before uploading a photo.
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
