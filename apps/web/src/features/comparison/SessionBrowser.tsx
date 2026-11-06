import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { compareLaps, loadLaps, loadSessions } from './api';
import ComparisonResult from './ComparisonResult';
import type { PairResponse } from './resultView';
import { available, changeDriver, changeMode, changePhase, initialDraft, lapTime, phases } from './selection';
import type { Draft, Index, Phase, SlotName } from './selection';
import { sessionsForRace } from '../navigation/routing';
import './comparison.css';

type Resource<T> = { state: 'loading' } | { state: 'error'; message: string } | { state: 'ready'; data: T };
function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Unable to reach the data service.';
}
function useLoad<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [resource, setResource] = useState<Resource<T>>({ state:'loading' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setResource({ state:'loading' });
    load(controller.signal).then(data => {
      if (!controller.signal.aborted) setResource({ state:'ready', data });
    }).catch((error: unknown) => {
      if (!controller.signal.aborted) setResource({ state:'error', message:errorMessage(error) });
    });
    return () => controller.abort();
  }, [load, attempt]);
  return { resource, retry: () => setAttempt(n => n + 1) };
}

function SlotPicker({ index, draft, name, update }: {
  index: Index; draft: Draft; name: SlotName; update: (draft: Draft) => void;
}) {
  const slot = draft[name];
  const other = draft[name === 'a' ? 'b' : 'a'];
  const laps = slot.phase ? available(index, slot.driver, slot.phase) : [];
  const reasons = index.laps.filter(lap => lap.driver_number === slot.driver && lap.capability === 'unavailable');
  const driver = index.drivers.find(d => d.driver_number === slot.driver);
  return <fieldset className={'sc-slot sc-slot-' + name}><legend>Driver {name.toUpperCase()}</legend>
    <label>Driver<select aria-label={'Driver ' + name.toUpperCase()} value={slot.driver} onChange={e => update(changeDriver(index, draft, name, e.target.value))}>
      {!slot.driver && <option value="">Choose driver</option>}
      {index.drivers.map(d => {
        const missing = !available(index, d.driver_number).length;
        return <option key={d.driver_number} value={d.driver_number} disabled={d.driver_number === other.driver || missing}>
          {d.driver_code} · {d.driver_name}{missing ? ' · No eligible lap' : ''}
        </option>;
      })}
    </select></label>
    <label>Qualifying phase<select aria-label={'Phase ' + name.toUpperCase()} value={slot.phase}
      onChange={e => update(changePhase(index, draft, name, e.target.value as Phase))}>
      {!slot.phase && <option value="">No shared eligible phase</option>}
      {phases.map(phase => {
        const own = available(index, slot.driver, phase).length > 0;
        const shared = draft.independent || available(index, other.driver, phase).length > 0;
        return <option key={phase} value={phase} disabled={!own || !shared}>
          {phase}{!own ? ' · No eligible lap' : !shared ? ' · Unavailable for other driver' : ''}
        </option>;
      })}
    </select></label>
    <label>Lap<select aria-label={'Lap ' + name.toUpperCase()} value={slot.lapId} disabled={!laps.length}
      onChange={e => update({ ...draft, [name]: { ...slot, lapId:e.target.value } })}>
      {!laps.length && <option value="">No eligible lap</option>}
      {laps.map((lap, i) => <option key={lap.lap_id} value={lap.lap_id}>Lap {lap.lap_number} · {lapTime(lap.lap_time_ms)}{i === 0 ? ' · Fastest eligible' : ''}{lap.capability === 'sector_only' ? ' · Sector timing only' : ''}</option>)}
    </select></label>
    {reasons.length > 0 && <details><summary>Excluded laps for {driver?.driver_code}</summary><ul>{reasons.map(lap =>
      <li key={lap.lap_id}>{lap.phase} lap {lap.lap_number} · {lap.reasons.join(', ')}</li>)}</ul></details>}
  </fieldset>;
}

function ComparisonForm({ index }: { index: Index }) {
  const [draft, setDraft] = useState(() => initialDraft(index));
  const [result, setResult] = useState<PairResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);
  function update(next: Draft) {
    pending.current?.abort();
    setBusy(false);
    setError('');
    setDraft(next);
    setResult(null);
  }
  const selectedA = index.laps.find(lap => lap.lap_id === draft.a.lapId);
  const selectedB = index.laps.find(lap => lap.lap_id === draft.b.lapId);
  const across = !!selectedA && !!selectedB && selectedA.phase !== selectedB.phase;
  const valid = !!selectedA && !!selectedB && selectedA.driver_number !== selectedB.driver_number
    && selectedA.capability !== 'unavailable' && selectedB.capability !== 'unavailable' && (!across || draft.independent);
  const sectorOnly = selectedA?.capability === 'sector_only' || selectedB?.capability === 'sector_only';
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!valid || busy) return;
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true);
    setError('');
    try {
      const response = await compareLaps({ session_id:index.session.session_id, lap_a_id:draft.a.lapId,
        lap_b_id:draft.b.lapId, allow_cross_phase:across && draft.independent, detail_level:'auto' }, controller.signal);
      if (!controller.signal.aborted) setResult(response);
    } catch (failure) {
      if (!controller.signal.aborted) setError(errorMessage(failure));
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  const withoutLaps = index.drivers.filter(d => !available(index, d.driver_number).length);
  return <>
    <form onSubmit={submit}>
      <label className="sc-switch"><input type="checkbox" checked={draft.independent}
        onChange={e => update(changeMode(index, draft, e.target.checked))}/> Allow different qualifying phases</label>
      <div className="sc-slots">{(['a','b'] as const).map(name =>
        <SlotPicker key={name} index={index} draft={draft} name={name} update={update}/>)}</div>
      {withoutLaps.length > 0 && <details><summary>Drivers without an eligible lap ({withoutLaps.length})</summary><ul>{withoutLaps.map(driver => {
        const reasons = [...new Set(index.laps.filter(lap => lap.driver_number === driver.driver_number).flatMap(lap => lap.reasons))];
        return <li key={driver.driver_number}>{driver.driver_name} · {reasons.join(', ') || 'No recorded laps in this import.'}</li>;
      })}</ul></details>}
      {!valid && <p className="sc-muted">{draft.a.driver && draft.b.driver && !draft.independent
        ? 'No common eligible phase. Enable different qualifying phases or choose another driver.'
        : 'Select two different drivers with eligible laps.'}</p>}
      {across && <p className="sc-warning">Cross-phase comparison: {selectedA?.phase} vs {selectedB?.phase}. Track conditions, tyres and session timing can differ.</p>}
      {sectorOnly && <p className="sc-muted">Sector timing only. {[...new Set([selectedA,selectedB].flatMap(lap => lap?.capability === 'sector_only' ? lap.reasons : []))].join(' · ')}</p>}
      <div className="sc-actions"><button type="submit" className="sc-compare" disabled={!valid || busy}>{busy ? 'Comparing…' : 'Compare laps'}</button>
        <button type="button" className="secondary-button" disabled={!valid || busy}
          onClick={() => update({ ...draft, a:draft.b, b:draft.a })}>Swap selections</button>
      </div>
      {error && <p className="sc-warning" role="alert">{error}</p>}
    </form>
    {result && <ComparisonResult result={result}/>}
  </>;
}

function SessionLaps({ sessionId }: { sessionId: string }) {
  const load = useCallback((signal: AbortSignal) => loadLaps(sessionId, signal), [sessionId]);
  const { resource, retry } = useLoad(load);
  if (resource.state === 'loading') return <p role="status">Loading driver and lap inventory…</p>;
  if (resource.state === 'error') return <div role="alert"><p>{resource.message}</p><button type="button" className="secondary-button" onClick={retry}>Retry lap inventory</button></div>;
  return <ComparisonForm index={resource.data}/>;
}

export default function SessionBrowser({year,round,eventName}: {year?:number;round?:number;eventName?:string} = {}) {
  const { resource, retry } = useLoad(loadSessions);
  const [sessionId, setSessionId] = useState('');
  if (resource.state === 'loading') return <section className="session-browser"><p role="status">Loading qualifying sessions…</p></section>;
  if (resource.state === 'error') return <section className="session-browser"><h2>Session inventory unavailable</h2><p role="alert">{resource.message}</p><button type="button" className="secondary-button" onClick={retry}>Retry connection</button></section>;
  const sessions = sessionsForRace(resource.data.sessions,year,round);
  if (!sessions.length) return <section className="session-browser"><h2>{eventName?'No qualifying data imported for this race':'No qualifying sessions imported yet'}</h2><p>{eventName?`${year} ${eventName}: `:''}Imported sessions will list each driver's available Q1, Q2 and Q3 laps here. Calendar selection does not start a telemetry download.</p><button type="button" className="secondary-button" onClick={retry}>Refresh sessions</button></section>;
  const selected = sessions.find(entry => entry.session.session_id === sessionId) ?? sessions[0];
  return <section className="session-browser"><h2>Compare qualifying laps</h2>
    <label className="sc-session">Qualifying session<select aria-label="Qualifying session" value={selected.session.session_id}
      onChange={e => setSessionId(e.target.value)}>{sessions.map(({session}) => <option key={session.session_id} value={session.session_id}>{session.year} · {session.event_name}</option>)}</select></label>
    <p className="sc-muted">{selected.driver_count} drivers · {selected.selectable_lap_count} eligible laps</p>
    <SessionLaps key={selected.session.session_id} sessionId={selected.session.session_id}/>
  </section>;
}
