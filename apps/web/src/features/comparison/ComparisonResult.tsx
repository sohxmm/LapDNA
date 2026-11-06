import { lazy, Suspense, useMemo } from 'react';
import { SectorPoints } from '../telemetry/SectorPoints';
import { signed } from '../telemetry/view';
import { traceView, orient } from './resultView';
import type { PairResponse, Telemetry } from './resultView';
import { lapTime } from './selection';

const TraceBoard = lazy(async () => ({ default: (await import('../telemetry/TraceBoard')).TraceBoard }));
const estimated = (value: number | null, showSign = false) =>
  value === null ? 'Unavailable' : '≈ ' + (showSign ? signed(value, 2) : (value / 1000).toFixed(2)) + ' s';

function TelemetryAnalysis({ artifact, swapped }: { artifact: Telemetry; swapped: boolean }) {
  const view = useMemo(() => traceView(artifact, swapped), [artifact, swapped]);
  const labels = new Map(artifact.segments.map(segment => [segment.segment_id, segment.label]));
  const evidence = new Map(artifact.evidence.map(item => [item.evidence_id, item]));
  const driverA = artifact.lap_a.driver_code;
  const driverB = artifact.lap_b.driver_code;
  return <>
    <Suspense fallback={<p role="status">Loading telemetry chart…</p>}>
      <TraceBoard view={view}/>
    </Suspense>
    <section className="sc-analysis" aria-label="Corner-speed analysis">
      <h3>Where each lap gained by corner speed</h3>
      <p>{artifact.analysis.text}</p>
      <details className="sc-muted"><summary>How this analysis is generated</summary><p>This is the saved evidence summary for these selected laps. The app renders its recorded metrics and observations; it does not currently call an LLM. Optional AI wording can be added after the numerical evidence is validated.</p></details>
      <p className="sc-muted">Reference speed bands · Low below {artifact.analysis.medium_from_kph} km/h · Medium below {artifact.analysis.high_from_kph} km/h · High from {artifact.analysis.high_from_kph} km/h</p>
      {artifact.analysis.categories.map(category => {
        const assessment = category.assessment === 'a_advantage' ? driverA + ' advantage'
          : category.assessment === 'b_advantage' ? driverB + ' advantage' : category.assessment;
        const members = category.included_segment_ids.map(id => labels.get(id) ?? id);
        return <details key={category.speed_class} className="sc-category">
          <summary><strong>{category.speed_class}-speed corners</strong> · {assessment} · net {estimated(orient(category.net_gain_ms, swapped), true)}</summary>
          <p>{category.independent_units} supported units · {Math.round(category.distance_coverage * 100)}% distance coverage</p>
          <p>{view.nameA} gained {estimated(swapped ? category.gains_b_ms : category.gains_a_ms)} · {view.nameB} gained {estimated(swapped ? category.gains_a_ms : category.gains_b_ms)}</p>
          <p>Included: {members.join(', ') || 'None'}. Excluded: {category.excluded_segment_ids.map(id => labels.get(id) ?? id).join(', ') || 'None'}.</p>
        </details>;
      })}
      {artifact.analysis.limitations.length > 0 && <ul>{artifact.analysis.limitations.map((text, i) => <li key={i}>{text}</li>)}</ul>}
    </section>
    <section className="sc-analysis"><h3>Regional observations</h3>
      {artifact.observations.map(observation => <details key={observation.observation_id} className="sc-category">
        <summary>{labels.get(observation.segment_id) ?? observation.segment_id} · {observation.text}</summary>
        <ul>{observation.evidence_ids.map(id => {
          const item = evidence.get(id);
          if (!item) return null;
          const a = swapped ? item.value_b : item.value_a;
          const b = swapped ? item.value_a : item.value_b;
          return <li key={id}>{item.metric.replaceAll('_', ' ')} · {Math.round(item.start_m)}–{Math.round(item.end_m)} m · {view.nameA} {a ?? '—'} {item.unit} · {view.nameB} {b ?? '—'} {item.unit}</li>;
        })}</ul>
      </details>)}
      {artifact.insufficient_evidence_reason && <p>{artifact.insufficient_evidence_reason}</p>}
    </section>
  </>;
}

export default function ComparisonResult({ result }: { result: PairResponse }) {
  const { artifact, swapped } = result;
  const a = swapped ? artifact.lap_b : artifact.lap_a;
  const b = swapped ? artifact.lap_a : artifact.lap_b;
  return <section className="sc-result" aria-label="Loaded comparison">
    <p className="eyebrow">{artifact.session.year} · {artifact.session.event_name} · {artifact.detail_level === 'telemetry' ? 'Telemetry comparison' : 'Sector timing only'}</p>
    <h2>{a.driver_code} {a.phase} vs {b.driver_code} {b.phase}</h2>
    <div className="sc-lap-cards">{[a, b].map((lap, i) => <div key={lap.lap_id}>
      <strong>{i === 0 ? 'A' : 'B'} · {lap.driver_name}</strong>
      <p>{lap.phase} · Lap {lap.lap_number} · {lapTime(lap.lap_time_ms)}</p>
      <small>{lap.compound} · Tyre life {lap.tyre_life_laps ?? 'unknown'} laps</small>
    </div>)}</div>
    <p><strong>Official gap {signed(b.lap_time_ms - a.lap_time_ms)} s</strong> · B − A, positive favors {a.driver_code}.</p>
    <p>Quality: {artifact.quality.status}. Source: {artifact.provenance.source}, {artifact.provenance.source_session} · Method {artifact.provenance.methodology_version}.</p>
    {artifact.pairing.mode === 'cross_phase' && <p className="sc-warning">Different qualifying phases · {a.phase} and {b.phase}. Conditions may have changed between these laps.</p>}
    {[...new Set([...artifact.pairing.warnings, ...artifact.quality.warnings])].map(text => <p className="sc-warning" key={text}>{text}</p>)}
    {artifact.detail_level === 'sector_only'
      ? <p className="sc-muted">{artifact.fallback_reason}</p>
      : <TelemetryAnalysis key={artifact.comparison_id + String(swapped)} artifact={artifact} swapped={swapped}/>}
    <SectorPoints nameA={a.driver_code} nameB={b.driver_code} a={a.sector_times_ms} b={b.sector_times_ms}/>
  </section>;
}
