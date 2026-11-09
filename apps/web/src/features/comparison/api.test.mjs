import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSessions, loadLaps, compareLaps } from './api.ts';

test('native 1.4 inventories and sprint results pass the browser boundary', async () => {
  const original = globalThis.fetch;
  const session = { session_id:'2024-6-miami-SQ' };
  const artifact = {schema_version:'1.4.0',session,detail_level:'sector_only',lap_a:{lap_id:'a'},lap_b:{lap_id:'b'}};
  const responses = [{schema_version:'1.4.0',sessions:[]}, {schema_version:'1.4.0',session,drivers:[],laps:[]}, {swapped:false,artifact}];
  globalThis.fetch = async () => ({ok:true,json:async()=>responses.shift()});
  try {
    assert.deepEqual((await loadSessions(new AbortController().signal)).sessions,[]);
    assert.equal((await loadLaps(session.session_id,new AbortController().signal)).session.session_id,session.session_id);
    assert.equal((await compareLaps({session_id:session.session_id,lap_a_id:'a',lap_b_id:'b'},new AbortController().signal)).artifact,artifact);
  } finally { globalThis.fetch = original; }
});

test('a future unknown contract is refused rather than rendered unchecked', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => ({ok:true,json:async()=>({schema_version:'99.0.0',sessions:[]})});
  try { await assert.rejects(loadSessions(new AbortController().signal),/Unsupported/); }
  finally { globalThis.fetch=original; }
});
