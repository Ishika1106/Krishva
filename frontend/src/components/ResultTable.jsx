// Top-3 table plus the remedy for rank 1 only.
export default function ResultTable({ results, t, lang, onReplay, onNewScan, speaking }) {
  const top = results[0];
  const topName = lang === 'hi' ? top.name_hi : top.name_en;
  const topRemedy = lang === 'hi' ? top.remedy_hi : top.remedy_en;

  const barClass = (c) => (c >= 70 ? '' : c >= 40 ? 'mid' : 'low');

  return (
    <div id="resultCard" className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-2 gap-2">
        <h5 className="fw-bold mb-0" id="resultsHeading">{t('results')}</h5>
        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={onNewScan}>
          &#8634; {t('new_scan')}
        </button>
      </div>

      <div className="card shadow-sm">
        <div className="table-responsive">
          <table className="table table-sm mb-0 align-middle">
            <thead className="table-light">
              <tr>
                <th scope="col" style={{ width: 52 }}>{t('rank')}</th>
                <th scope="col">{t('disease')}</th>
                <th scope="col" style={{ width: 190 }}>{t('confidence')}</th>
              </tr>
            </thead>
            <tbody id="resultRows">
              {results.map((r, i) => (
                <tr key={r.class} className={i === 0 ? 'top-result' : ''}>
                  <td>
                    <span className={`rank-pill r${i + 1}`}>{i + 1}</span>
                  </td>
                  <td>{lang === 'hi' ? r.name_hi : r.name_en}</td>
                  <td className="bar-cell">
                    <div className="d-flex align-items-center gap-2">
                      <div className={`conf-bar flex-grow-1 ${barClass(r.confidence)}`}>
                        <span style={{ width: `${Math.max(0, Math.min(100, r.confidence))}%` }} />
                      </div>
                      <span className="conf-num">{r.confidence}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={`alert alert-light border remedy-card mt-3${speaking ? ' speaking' : ''}`} id="remedyCard">
        <div className="d-flex justify-content-between align-items-start gap-2 mb-1">
          <div className="small fw-bold text-uppercase text-secondary" id="topDiseaseLabel">
            {t('remedy_for')} {topName}
          </div>
          <button type="button" className="btn btn-sm btn-outline-success" id="replayBtn" onClick={onReplay}>
            &#9835; {t('replay')}
          </button>
        </div>
        <div id="remedyText" style={{ fontSize: '.95rem' }}>{topRemedy}</div>
      </div>

      {top.confidence < 60 && (
        <div className="alert alert-warning mt-3 mb-0" id="lowConfWarn">{t('low_confidence')}</div>
      )}
    </div>
  );
}
