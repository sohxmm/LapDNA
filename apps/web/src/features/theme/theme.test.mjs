import test from 'node:test';
import assert from 'node:assert/strict';
import { persistTheme, storedTheme, THEME_STORAGE_KEY,traceContrast,chartPalette } from './theme.ts';

test('pale source colours require an outline in light mode while keeping their original hue',()=>{
  const light=chartPalette('light'),dark=chartPalette('dark');
  assert.ok(traceContrast('#FFFFFF',light.background)<3);
  assert.ok(traceContrast('#FFF500',light.background)<3);
  assert.ok(traceContrast('#FFFFFF',dark.background)>3);
  assert.ok(traceContrast('#DC0000',light.background)>3);
});

test('a saved light preference survives a new page and invalid preferences default to dark', () => {
  const data = new Map();
  const storage = { getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, value) };
  assert.equal(storedTheme(storage), 'dark');
  persistTheme(storage, 'light');
  assert.equal(data.get(THEME_STORAGE_KEY), 'light');
  assert.equal(storedTheme(storage), 'light');
  data.set(THEME_STORAGE_KEY, 'unknown');
  assert.equal(storedTheme(storage), 'dark');
});

test('blocked or full browser storage cannot break theme selection', () => {
  const blocked = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('full'); } };
  assert.equal(storedTheme(blocked), 'dark');
  assert.doesNotThrow(() => persistTheme(blocked, 'light'));
  assert.equal(storedTheme(null), 'dark');
  assert.doesNotThrow(() => persistTheme(null, 'dark'));
});
