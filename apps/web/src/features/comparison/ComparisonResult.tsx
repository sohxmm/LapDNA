import { lazy, Suspense, useMemo, useRef, useState } from 'react';
import { SectorPoints } from '../telemetry/SectorPoints';
import { signed } from '../telemetry/view';
import { traceView, orient } from './resultView';
import type { PairResponse, Telemetry } from './resultView';
import { lapTime } from './selection';
import {PerformanceMap} from './PerformanceMap';
import {ComparisonExport, sourceName} from './ComparisonExport';
import type {TraceWindow} from '../telemetry/TraceBoard';

const TraceBoard = lazy(async () => ({ default: (await import('../telemetry/TraceBoard')).TraceBoard }));
const estimated = (value: number | null, showSign = false) =>
  value === null ? 'Unavailable' : '≈ ' + (showSign ? signed(value, 2) : (value / 1000).toFixed(2)) + ' s';

function TelemetryAnalysis({ artifact, swapped }: { artifact: Telemetry; swapped: boolean }) {
  const view = useMemo(() => traceView(artifact, swapped), [artifact, swapped]);
  const [cursor,setCursor]=useState(0),[selection,setSelection]=useState<TraceWindow>(null),[selectedRegion,setSelectedRegion]=useState<string|null>(null);
  const traceAnchor=useRef<HTMLDivElement>(null);
  const labels = new Map(artifact.segments.map(segment => [segment.segment_id, segment.label]));
  const evidence = new Map(artifact.evidence.map(item => [item.evidence_id, item]));
  const driverA = artifact.lap_a.driver_code;
  const driverB = artifact.lap_b.driver_code;
  function inspect(segment:Telemetry['segments'][number]) {
    const padding=(segment.end_m-segment.start_m)*.1;
    setSelection({label:segment.label,start:Math.max(0,segment.start_m-padding),end:Math.min(artifact.distance_m.at(-1)!,segment.end_m+padding)});
    setCursor((segment.start_m+segment.end_m)/2);setSelectedRegion(segment.segment_id);
    traceAnchor.current?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  }
  return <>
    <div ref={traceAnchor}><Suspense fallback={<p role="status">Loading telemetry chart…</p>}>
      <TraceBoard view={view} cursor={cursor} onCursorChange={setCursor} selection={selection} onSelectionChange={next=>{
        setSelection(next);const corner=artifact.corners.find(item=>item.label===next?.label);setSelectedRegion(corner?.segment_id??null);
      }}/>
    </Suspense></div>
    <PerformanceMap artifact={artifact} swapped={swapped} cursor={cursor} selected={selectedRegion} onCursor={setCursor} onRegion={inspect}/>
    <section className="sc-analysis" aria-label="Corner-speed analysis">
      <h3>Where each lap gained by corner speed</h3>
      <p>{artifact.analysis.text}</p>
      <details className="sc-muted"><summary>Class definitions and method</summary><p>Low below {artifact.analysis.medium_from_kph} km/h · Medium below {artifact.analysis.high_from_kph} km/h · High from {artifact.analysis.high_from_kph} km/h. Classes use supported native speeds from the frozen reference, independent of this driver selection. Text is generated from the numerical evidence for these selected laps; no LLM is called.</p></details>
      <div className="analysis-categories">{artifact.analysis.categories.map(category => {
        const assessment = category.assessment === 'a_advantage' ? driverA + ' advantage'
          : category.assessment === 'b_advantage' ? driverB + ' advantage' : category.assessment;
        const members = category.included_segment_ids.map(id => labels.get(id) ?? id);
        return <details key={category.speed_class} className="sc-category">
          <summary><strong>{category.speed_class}-speed corners</strong> · {assessment} · net {estimated(orient(category.net_gain_ms, swapped), true)}</summary>
          <p>{category.independent_units} supported units · {Math.round(category.distance_coverage * 100)}% distance coverage</p>
          <p>{view.nameA} gained {estimated(swapped ? category.gains_b_ms : category.gains_a_ms)} · {view.nameB} gained {estimated(swapped ? category.gains_a_ms : category.gains_b_ms)}</p>
          <p>Included: {members.join(', ') || 'None'}. Excluded: {category.excluded_segment_ids.map(id => labels.get(id) ?? id).join(', ') || 'None'}.</p>
          <div className="export-actions">{category.included_segment_ids.map(id=>{
            const segment=artifact.segments.find(item=>item.segment_id===id);return segment?<button type="button" key={id} onClick={()=>inspect(segment)}>Inspect {segment.label}</button>:null;
          })}</div>
        </details>;
      })}</div>
      {artifact.analysis.limitations.length > 0 && <ul>{artifact.analysis.limitations.map((text, i) => <li key={i}>{text}</li>)}</ul>}
    </section>
    <section className="sc-analysis"><h3>Regional observations</h3>
      <div className="observation-list">{artifact.observations.map(observation => <article key={observation.observation_id} className="observation-card">
        <h4>{labels.get(observation.segment_id) ?? observation.segment_id}</h4><p>{observation.text}</p>
        <button type="button" className="secondary-button" onClick={()=>{const segment=artifact.segments.find(item=>item.segment_id===observation.segment_id);if(segment)inspect(segment);}}>Inspect interval</button>
        <details><summary>Supporting measurements</summary>
        <ul>{observation.evidence_ids.map(id => {
          const item = evidence.get(id);
          if (!item) return null;
          const a = swapped ? item.value_b : item.value_a;
          const b = swapped ? item.value_a : item.value_b;
          const intervalA=swapped?item.interval_b:item.interval_a,intervalB=swapped?item.interval_a:item.interval_b;
          const value=(point:number|null,interval:readonly number[]|null|undefined)=>point!==null?Math.round(point*100)/100:interval?Math.floor(interval[0])+'–'+Math.ceil(interval[1]):'Unavailable';
          return <li key={id}>{item.metric.replaceAll('_', ' ')} · {Math.round(item.start_m)}–{Math.round(item.end_m)} m · {view.nameA} {value(a,intervalA)} {item.unit} · {view.nameB} {value(b,intervalB)} {item.unit} · native samples {swapped?item.native_samples_b:item.native_samples_a}/{swapped?item.native_samples_a:item.native_samples_b}</li>;
        })}</ul>
        </details>
      </article>)}</div>
      {artifact.insufficient_evidence_reason && <p>{artifact.insufficient_evidence_reason}</p>}
    </section>
  </>;
}

export default function ComparisonResult({ result }: { result: PairResponse }) {
  const { artifact, swapped } = result;
  const a = swapped ? artifact.lap_b : artifact.lap_a;
  const b = swapped ? artifact.lap_a : artifact.lap_b;
  const warnings=[...new Set([...artifact.pairing.warnings,...artifact.quality.warnings])];
  const methodWarning=(text:string)=>['Approximate local timing','Timing clocks/eligibility','Start/finish values'].some(prefix=>text.startsWith(prefix));
  return <section className="sc-result" aria-label="Loaded comparison">
    <p className="eyebrow">{artifact.session.year} · {artifact.session.event_name} · {artifact.detail_level === 'telemetry' ? 'Telemetry comparison' : 'Sector timing only'}</p>
    <h2>{a.driver_code} {a.phase} vs {b.driver_code} {b.phase}</h2>
    <div className="sc-lap-cards">{[a, b].map((lap, i) => <div key={lap.lap_id}>
      <strong>{i === 0 ? 'A' : 'B'} · {lap.driver_name}</strong>
      <p>{lap.phase} · Lap {lap.lap_number} · {lapTime(lap.lap_time_ms)}</p>
      <small>{lap.compound} · Tyre life {lap.tyre_life_laps ?? 'unknown'} laps</small>
    </div>)}</div>
    <p><strong>Official gap {signed(b.lap_time_ms - a.lap_time_ms)} s</strong> · B − A, positive favors {a.driver_code}.</p>
    <p className="lap-context">{artifact.detail_level==='telemetry'?'Estimated local timing · ':''}Data checks: {artifact.quality.status} · {sourceName(artifact)}</p>
    {artifact.pairing.mode === 'cross_phase' && <p className="sc-warning">Different qualifying phases · {a.phase} and {b.phase}. Conditions may have changed between these laps.</p>}
    {warnings.filter(text=>!methodWarning(text)).map(text => <p className="sc-warning" key={text}>{text}</p>)}
    {artifact.detail_level === 'sector_only'
      ? <p className="sc-muted">{artifact.fallback_reason}</p>
      : <TelemetryAnalysis key={artifact.comparison_id + String(swapped)} artifact={artifact} swapped={swapped}/>}
    <SectorPoints nameA={a.driver_code} nameB={b.driver_code} a={a.sector_times_ms} b={b.sector_times_ms}/>
    <details className="session-source-details"><summary>Data details and timing reconciliation</summary>
      <p>Method {artifact.provenance.methodology_version} · Dataset {artifact.provenance.source_snapshot_sha256} · Generated {new Date(artifact.provenance.generated_at).toUTCString()}.</p>
      <p>Timing constraints impose the lap edges; they do not independently validate interior corner timing. Raw residuals below are retained. Positions and local gains are approximate.</p>
      {(a.lap_start_utc||b.lap_start_utc)&&<p>Lap start UTC · {a.driver_code} {a.lap_start_utc??'unavailable'} · {b.driver_code} {b.lap_start_utc??'unavailable'}</p>}
      {warnings.filter(methodWarning).map(text=><p key={text}>{text}</p>)}
      {[...new Map(artifact.provenance.components?.map(component=>[component.source+'|'+component.license_url,component])).values()].map((component,i)=><p key={i}><a href={component.url} target="_blank" rel="noreferrer">{component.source}</a> · {component.version??'version not supplied'} · {component.license_url?<a href={component.license_url} target="_blank" rel="noreferrer">{component.license_name??'Source licence'}</a>:component.license_name??'Source terms not verified'}.</p>)}
      <p>Full per-file URLs, retrieval times and hashes are retained in the evidence JSON.</p>
      {artifact.detail_level==='telemetry'&&<p>Native car samples: {artifact.lap_a.driver_code} {artifact.quality.native_samples_a}, {artifact.lap_b.driver_code} {artifact.quality.native_samples_b}. Maximum gaps {artifact.quality.max_native_gap_ms_a.toFixed(0)} / {artifact.quality.max_native_gap_ms_b.toFixed(0)} ms. Distance scale factors {artifact.quality.distance_a.scale_factor.toFixed(5)} / {artifact.quality.distance_b.scale_factor.toFixed(5)}.</p>}
      <div className="quality-table-wrap"><table className="quality-table"><caption>Recorded timings and raw reconciliation residuals, milliseconds</caption><thead><tr><th>Driver</th><th>Check</th><th>Basis</th><th>Recorded</th><th>Observed</th><th>Residual</th><th>Status</th></tr></thead><tbody>{artifact.quality.checks.map(check=>{
        const orientation=check.driver==='pair'&&swapped?-1:1;
        return <tr key={check.driver+check.metric}><th>{check.driver==='A'?artifact.lap_a.driver_code:check.driver==='B'?artifact.lap_b.driver_code:'Pair'}</th><td>{check.metric.replaceAll('_',' ')}</td><td>{check.basis.replaceAll('_',' ')}</td><td>{(check.official_ms*orientation).toFixed(1)}</td><td>{check.observed_ms===null?'Unavailable':(check.observed_ms*orientation).toFixed(1)}</td><td>{check.residual_ms===null?'Unavailable':(check.residual_ms*orientation).toFixed(1)}</td><td>{check.status}</td></tr>;
      })}</tbody></table></div>
    </details>
    <ComparisonExport result={result}/>
  </section>;
}
