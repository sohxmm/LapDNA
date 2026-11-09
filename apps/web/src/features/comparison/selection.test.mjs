import test from 'node:test';
import assert from 'node:assert/strict';
import { initialDraft, changeMode, changePhase, changeDriver } from './selection.ts';
import { traceView } from './resultView.ts';
import { availableSignals, supportedSample, signed, groupTurnMarkers } from '../telemetry/view.ts';

test('local display precision does not imply a negative zero gain',()=>{
  assert.equal(signed(-4,2),'+0.00');assert.equal(signed(-6,2),'−0.01');
});
test('dense turn labels group without changing their source positions and resolve after zoom',()=>{
  const turns=[100,120,180,700].map((at,i)=>({label:'T'+(i+1),at,start:80,end:220,speedClass:'low'}));
  const before=JSON.stringify(turns);
  assert.deepEqual(groupTurnMarkers(turns,0,1000,250).map(group=>group.map(turn=>turn.label)),[['T1','T2','T3'],['T4']]);
  assert.deepEqual(groupTurnMarkers(turns,80,220,600).map(group=>group.map(turn=>turn.label)),[['T1'],['T2'],['T3']]);
  assert.equal(JSON.stringify(turns),before);
});

const drivers = ['1', '2', '3'].map(n => ({ driver_number: n, driver_code: 'D' + n, driver_name: 'Test ' + n }));
const lap = (driver_number, phase, lap_number, lap_time_ms, capability = 'telemetry') => ({
  driver_number, phase, lap_number, lap_time_ms, capability,
  lap_id: [driver_number, phase, lap_number].join('_'),
});
const index = { drivers, laps: [
  lap('1','Q1',1,80000), lap('1','Q2',2,79000), lap('1','Q2',3,79000),
  lap('1','Q2',4,78000,'unavailable'), lap('1','Q3',5,77000),
  lap('2','Q1',1,81000), lap('2','Q2',2,80000), lap('3','Q1',1,82000),
] };
test('default selects fastest eligible laps in highest common phase with lower lap as tie-break', () => {
  const draft = initialDraft(index);
  assert.deepEqual([draft.a.lapId, draft.b.lapId], ['1_Q2_2','2_Q2_2']);
});
test('changing an independent phase preserves the other slot, relinking finds the highest common phase', () => {
  const draft = changeMode(index, initialDraft(index), true);
  draft.a.lapId = '1_Q2_3';
  const changed = changePhase(index, draft, 'b', 'Q1');
  assert.deepEqual([changed.a.lapId, changed.b.lapId], ['1_Q2_3','2_Q1_1']);
  assert.equal(changeMode(index, changed, false).b.lapId, '2_Q2_2');
  assert.equal(changeDriver(index, changed, 'b', '3').a.lapId, '1_Q2_3');
});
test('a reversed result exchanges channel roles and negates delta and minisectors, preserving unsupported samples', () => {
  const channels = speed => ({ speed_kph: speed, brake: [], throttle_pct: [], gear: [] });
  const provenance = {speed_kph:{status:'measured',source_channel:'Speed',reason:null},
    ...Object.fromEntries(['throttle_pct','gear','brake'].map(name=>[name,{status:'missing',source_channel:null,reason:'No native field'}]))};
  const fixture = { segments: [{ segment_id:'t1', start_m:0,end_m:100 }], corners:[
    {segment_id:'t1',label:'T1',distance_m:40,speed_class:'low'}], lap_a:{driver_code:'XA',team_colour:'#FF8000'},lap_b:{driver_code:'XB',team_colour:'#27F4D2'},
    channels_a:channels([50]),channels_b:channels([45]),delta_ms:[null,123],distance_m:[0,100],
    channel_provenance_a:provenance,channel_provenance_b:provenance,
    sector_boundaries_m:[30,65],estimated_minisectors:[{start_m:0,end_m:100,gain_ms:123}] };
  const view = traceView(fixture,true);
  assert.deepEqual([view.nameA,view.nameB,view.a.speed,view.delta,view.bins[0].gain], ['XB','XA',[45],[null,-123],-123]);
  assert.equal(view.turns[0].at,40);
  assert.deepEqual([view.colorA,view.colorB],['#27F4D2','#FF8000']);
});

test('measured brake state stays binary, missing channels do not become inferred traces', () => {
  const missing={status:'missing',sourceChannel:null,reason:'Native source did not return this field'};
  const provenance={speed:{status:'measured',sourceChannel:'Speed',reason:null},
    throttle:missing,gear:missing,brake:{status:'measured',sourceChannel:'Brake',reason:null}};
  const samples={speed:[100,90,80],throttle:[null,null,null],gear:[null,null,null],brake:[true,false,null]};
  const view={a:samples,b:samples,provenanceA:provenance,provenanceB:provenance};
  assert.deepEqual(availableSignals(view),['speed','brake']);
  assert.deepEqual([0,1,2].map(index=>supportedSample(view,'a','brake',index)),[true,false,null]);
  view.provenanceA={...provenance,brake:missing};
  assert.equal(supportedSample(view,'a','brake',1),null);
  assert.deepEqual(availableSignals(view),['speed','brake']); // B still has actual brake samples.
  view.provenanceB={...provenance,brake:missing};
  assert.deepEqual(availableSignals(view),['speed']);
});
