import test from 'node:test';
import assert from 'node:assert/strict';
import {initialDraft,lapSelectionSearch,restoreLapSelection,telemetryAlternative} from './selection.ts';

const index={session:{session_id:'session_q',year:2024,round:16},source_snapshot_sha256:'a'.repeat(64),drivers:[{driver_number:'4'},{driver_number:'81'}],laps:[
  {lap_id:'n_q2',driver_number:'4',phase:'Q2',lap_number:7,lap_time_ms:80000,capability:'telemetry'},
  {lap_id:'n_q3',driver_number:'4',phase:'Q3',lap_number:11,lap_time_ms:79327,capability:'telemetry'},
  {lap_id:'p_q3',driver_number:'81',phase:'Q3',lap_number:15,lap_time_ms:79436,capability:'sector_only'},
  {lap_id:'p_rejected',driver_number:'81',phase:'Q2',lap_number:8,lap_time_ms:78000,capability:'unavailable'},
]};

test('exact lap links restore selected drivers, phases and dataset revision without timing substitution',()=>{
  const draft=initialDraft(index),search=lapSelectionSearch(index,draft,'?session=classification&phase=Q1&a=old&b=old&comparison=old');
  const restored=restoreLapSelection(index,search);
  assert.deepEqual(restored.draft,draft);assert.equal(restored.warning,null);assert.equal(restored.requested,true);
  const query=new URLSearchParams(search);assert.equal(query.get('analysis'),'telemetry');assert.equal(query.get('phase'),null);assert.equal(query.get('comparison'),null);
  assert.equal(restored.draft.b.lapId,'p_q3');
});
test('unavailable revisions, foreign sessions, rejected laps and duplicate drivers never silently auto-restore',()=>{
  const search=lapSelectionSearch(index,initialDraft(index));
  for(const [key,value] of [['dataset','b'.repeat(64)],['lapSession','foreign'],['lapA','missing'],['lapB','p_rejected'],['lapB','n_q2']]) {
    const query=new URLSearchParams(search);query.set(key,value);
    assert.ok(restoreLapSelection(index,'?'+query).warning,key);
  }
});
test('cross-phase share links require explicit context and retain exact original laps',()=>{
  const draft={a:{driver:'4',phase:'Q2',lapId:'n_q2'},b:{driver:'81',phase:'Q3',lapId:'p_q3'},independent:true};
  const search=lapSelectionSearch(index,draft);assert.deepEqual(restoreLapSelection(index,search).draft,draft);
  const query=new URLSearchParams(search);query.delete('cross');assert.ok(restoreLapSelection(index,'?'+query).warning);
});
test('a telemetry alternative is explicit and never replaces the phase-best default silently',()=>{
  const extended={...index,laps:[...index.laps,{lap_id:'p_later',driver_number:'81',phase:'Q3',lap_number:18,lap_time_ms:79661,capability:'telemetry'}]};
  const original=initialDraft(extended);assert.equal(original.b.lapId,'p_q3');
  const alternative=telemetryAlternative(extended,original);assert.equal(alternative.b.lapId,'p_later');
  assert.equal(original.b.lapId,'p_q3');assert.equal(telemetryAlternative(index,original),null);
});
