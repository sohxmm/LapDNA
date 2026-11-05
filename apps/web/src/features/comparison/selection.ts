import type { components } from '../../../../../packages/contracts/api';

type Schema = components['schemas'];
export type Index = Schema['SessionLapIndex'];
export type Lap = Schema['LapOption'];
export type Phase = Lap['phase'];
export type SlotName = 'a' | 'b';
export type Slot = { driver: string; phase: Phase | ''; lapId: string };
export type Draft = { a: Slot; b: Slot; independent: boolean };
export const phases: Phase[] = ['Q1', 'Q2', 'Q3'];

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
  return [...phases].reverse().find(phase => available(index, driver, phase).length > 0) ?? '';
}

export function synchronize(index: Index, draft: Draft, preferred: Phase | '' = ''): Draft {
  if (draft.independent) return draft;
  const common = phases.filter(phase => available(index, draft.a.driver, phase).length > 0
    && available(index, draft.b.driver, phase).length > 0);
  const phase = preferred && common.includes(preferred) ? preferred : common.at(-1) ?? '';
  return {
    independent: false,
    a: choose(index, draft.a.driver, phase, draft.a.lapId),
    b: choose(index, draft.b.driver, phase, draft.b.lapId),
  };
}

export function initialDraft(index: Index): Draft {
  const selectable = index.drivers.filter(d => available(index, d.driver_number).length);
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
