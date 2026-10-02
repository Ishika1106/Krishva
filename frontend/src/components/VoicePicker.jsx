export default function VoicePicker({ onTest, t, testing }) {
  return (
    <div className="voice-picker">
      <div className="d-flex align-items-center justify-content-between gap-2">
        <div>
          <div className="small fw-semibold label">{t('voice_choice')}</div>
          <div className="small muted">{t('server_voice_note')}</div>
        </div>
        <button
          type="button"
          className="btn btn-sm btn-glass text-nowrap"
          onClick={onTest}
          disabled={testing}
        >
          {testing ? t('voice_testing') : t('voice_test')}
        </button>
      </div>
    </div>
  );
}
