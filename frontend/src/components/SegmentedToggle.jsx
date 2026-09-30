export default function SegmentedToggle({ label, options, value, onChange, name }) {
  return (
    <div className="d-flex align-items-center justify-content-between gap-2 setting-row">
      <span className="small fw-semibold text-secondary">{label}</span>
      <div className="seg" role="group" aria-label={label}>
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            data-testid={`${name}-${o.value}`}
            className={value === o.value ? 'active' : ''}
            aria-pressed={value === o.value}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
