// Rendering input. The scientific contract lives in Python; this adapter only needs display values.
export type Samples = {
  speed: (number | null)[]; throttle: (number | null)[]; gear: (number | null)[]; brake: (boolean | null)[];
};
export type SignalName = keyof Samples;
export type SignalProvenance = {
  status: 'measured' | 'missing' | 'synthetic';
  sourceChannel: string | null;
  reason: string | null;
};
export type SignalProvenanceSet = Record<SignalName, SignalProvenance>;
export const signalOrder: SignalName[] = ['speed','throttle','gear','brake'];
export const signalLabels: Record<SignalName,string> = {speed:'Speed',throttle:'Throttle',gear:'Gear',brake:'Brake'};
export type TraceTurn = { label: string; at: number; start: number; end: number; speedClass: string };
export type TraceView = {
  distance: number[]; a: Samples; b: Samples; delta: (number | null)[];
  turns: TraceTurn[]; bins: {start:number; end:number; gain:number | null}[];
  boundaries: number[]; nameA: string; nameB: string;
  provenanceA: SignalProvenanceSet; provenanceB: SignalProvenanceSet;
};
export function hasSupportedSignal(samples:Samples, provenance:SignalProvenanceSet, name:SignalName) {
  return (provenance[name].status==='measured' || provenance[name].status==='synthetic')
    && samples[name].some(value=>value!==null);
}
export function availableSignals(view:TraceView):SignalName[] {
  return signalOrder.filter(name=>hasSupportedSignal(view.a,view.provenanceA,name)
    || hasSupportedSignal(view.b,view.provenanceB,name));
}
export function supportedSample(view:TraceView, slot:'a'|'b', name:SignalName, index:number) {
  const provenance=slot==='a'?view.provenanceA:view.provenanceB;
  return hasSupportedSignal(view[slot],provenance,name)?view[slot][name][index]??null:null;
}
export function nearest(grid: number[], value: number) {
  let lo=0, hi=grid.length-1;
  while (lo<hi) { const mid=(lo+hi)>>>1; if (grid[mid]<value) lo=mid+1; else hi=mid; }
  return lo>0 && value-grid[lo-1]<grid[lo]-value ? lo-1 : lo;
}
export const seconds = (ms: number, decimals=3) => (ms/1000).toFixed(decimals);
export const signed = (ms: number, decimals=3) => (ms<0?'−':'+') + seconds(Math.abs(ms),decimals);
