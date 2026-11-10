import type { components } from '../../../../../packages/contracts/api';

type Schema = components['schemas'];
export type Index = Schema['SessionLapIndex'];
export type Lap = Schema['LapOption'];
export type Phase = Lap['phase'];
export type SlotName = 'a' | 'b';
export type Slot = { driver: string; phase: Phase | ''; lapId: string };
export type Draft = { a: Slot; b: Slot; independent: boolean };
export const phases: Phase[] = ['Q1', 'Q2', 'Q3'];
export function sessionPhases(index:Index):Phase[] {
  return index.session?.session_type==='SQ'?['SQ1','SQ2','SQ3']:phases;
}

export function available(index: Index, driver: string, phase?: Phase | '') {
  return index.laps.filter(lap => lap.driver_number === driver && lap.capability !== 'unavailable'
    && (!phase || lap.phase === phase)).sort((a, b) =>
      (a.lap_time_ms ?? Infinity) - (b.lap_time_ms ?? Infinity) || a.lap_number - b.lap_number);
}

function choose(index: Index, driver: string, phase: Phase | '', current = ''): Slot {
  const laps = phase ? available(index, driver, phase) : [];
  return { driver, phase, lapId: laps.find(lap => lap.lap_id === current)?.lap_id ?? laps[0]?.lap_id ?? '' };
}

function highest(index: Index, driver: string): Phase | '' {
  return [...sessionPhases(index)].reverse().find(phase => available(index, driver, phase).length > 0) ?? '';
}

export function synchronize(index: Index, draft: Draft, preferred: Phase | '' = ''): Draft {
  if (draft.independent) return draft;
  const common = sessionPhases(index).filter(phase => available(index, draft.a.driver, phase).length > 0
    && available(index, draft.b.driver, phase).length > 0);
  const phase = preferred && common.includes(preferred) ? preferred : common.at(-1) ?? '';
  return {
    independent: false,
    a: choose(index, draft.a.driver, phase, draft.a.lapId),
    b: choose(index, draft.b.driver, phase, draft.b.lapId),
  };
}

export function initialDraft(index: Index): Draft {
  const highestShared = [...sessionPhases(index)].reverse().find(phase =>
    index.drivers.filter(driver => available(index,driver.driver_number,phase).length).length >= 2);
  const selectable = index.drivers.filter(d => available(index, d.driver_number,highestShared).length)
    .sort((a,b) => (available(index,a.driver_number,highestShared)[0]?.lap_time_ms ?? Infinity)
      - (available(index,b.driver_number,highestShared)[0]?.lap_time_ms ?? Infinity)
      || Number(a.driver_number)-Number(b.driver_number));
  const make = (i: number) => choose(index, selectable[i]?.driver_number ?? '', '');
  return synchronize(index, { a: make(0), b: make(1), independent: false });
}

export function changeMode(index: Index, draft: Draft, independent: boolean): Draft {
  if (!independent) return synchronize(index, { ...draft, independent: false }, draft.a.phase);
  const free = (slot: Slot) => choose(index, slot.driver, slot.phase || highest(index, slot.driver), slot.lapId);
  return { independent: true, a: free(draft.a), b: free(draft.b) };
}

export function changeDriver(index: Index, draft: Draft, name: SlotName, driver: string): Draft {
  const other = draft[name === 'a' ? 'b' : 'a'];
  const phase = highest(index, driver);
  return synchronize(index, { ...draft, [name]: choose(index, driver, phase) }, other.phase);
}

export function changePhase(index: Index, draft: Draft, name: SlotName, phase: Phase): Draft {
  const next = { ...draft, [name]: choose(index, draft[name].driver, phase) };
  return synchronize(index, next, phase);
}

export function lapTime(ms: number | null) {
  if (ms === null) return 'Unavailable';
  const value = Math.round(ms);
  const minutes = Math.floor(value / 60000);
  const remainder = value % 60000;
  return minutes + ':' + (remainder / 1000).toFixed(3).padStart(6, '0');
}

export function restoreLapSelection(index:Index,search:string):{draft:Draft;warning:string|null;requested:boolean} {
  const query=new URLSearchParams(search),first=query.get('lapA'),second=query.get('lapB');
  const fallback=initialDraft(index);
  if(!first&&!second)return {draft:fallback,warning:null,requested:false};
  const fail=(warning:string)=>({draft:fallback,warning,requested:true});
  if(query.get('lapSession')!==index.session.session_id)return fail('This link refers to a different qualifying session. Choose the laps below.');
  if(query.get('dataset')!==index.source_snapshot_sha256)return fail('This exact dataset revision is unavailable. Choose laps from the current publication below.');
  const a=index.laps.find(lap=>lap.lap_id===first),b=index.laps.find(lap=>lap.lap_id===second);
  if(!a||!b||a.driver_number===b.driver_number)return fail('This lap pair is absent or invalid. Choose two different drivers below.');
  if(a.capability==='unavailable'||b.capability==='unavailable')return fail('A linked lap is ineligible in this publication. Choose an available lap below.');
  const independent=query.get('cross')==='1';
  if(a.phase!==b.phase&&!independent)return fail('This link needs an explicit cross-phase choice. Select the phases and enable different phases below.');
  return {draft:{a:{driver:a.driver_number,phase:a.phase,lapId:a.lap_id},b:{driver:b.driver_number,phase:b.phase,lapId:b.lap_id},independent},warning:null,requested:true};
}

export function lapSelectionSearch(index:Index,draft:Draft,search='') {
  const query=new URLSearchParams(search);
  for(const key of ['session','phase','a','b','comparison'])query.delete(key);
  query.set('year',String(index.session.year));query.set('race',index.session.year+'-'+index.session.round);
  query.set('view','studio');query.set('analysis','telemetry');query.set('lapSession',index.session.session_id);
  query.set('lapA',draft.a.lapId);query.set('lapB',draft.b.lapId);query.set('dataset',index.source_snapshot_sha256);
  if(draft.a.phase!==draft.b.phase&&draft.independent)query.set('cross','1');else query.delete('cross');
  return '?'+query.toString();
}

export function telemetryAlternative(index:Index,draft:Draft):Draft|null {
  const a=available(index,draft.a.driver,draft.a.phase).find(lap=>lap.capability==='telemetry');
  const b=available(index,draft.b.driver,draft.b.phase).find(lap=>lap.capability==='telemetry');
  if(!a||!b||(a.lap_id===draft.a.lapId&&b.lap_id===draft.b.lapId))return null;
  return {...draft,a:{...draft.a,lapId:a.lap_id},b:{...draft.b,lapId:b.lap_id}};
}

/** Navigation choices only: the server still checks the selected pair. */
export function telemetryLapGroups(index:Index):{phase:Phase;laps:Lap[];draft:Draft|null}[] {
  return [...sessionPhases(index)].reverse().map(phase=>{
    const laps=index.drivers.flatMap(driver=>{
      const best=available(index,driver.driver_number,phase).find(lap=>lap.capability==='telemetry');
      return best?[best]:[];
    }).sort((a,b)=>(a.lap_time_ms??Infinity)-(b.lap_time_ms??Infinity)
      ||Number(a.driver_number)-Number(b.driver_number));
    const slot=(lap:Lap):Slot=>({driver:lap.driver_number,phase,lapId:lap.lap_id});
    return {phase,laps,draft:laps.length>=2?{a:slot(laps[0]),b:slot(laps[1]),independent:false}:null};
  });
}
