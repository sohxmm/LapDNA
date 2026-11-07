export type Theme = 'dark' | 'light';

export const THEME_STORAGE_KEY = 'lapdna.theme';
export const THEME_EVENT = 'lapdna:themechange';

export function resolveTheme(value: string | null | undefined): Theme {
  return value === 'light' ? 'light' : 'dark';
}

export function storedTheme(storage: Pick<Storage, 'getItem'> | null): Theme {
  try {
    return resolveTheme(storage?.getItem(THEME_STORAGE_KEY));
  } catch {
    return 'dark';
  }
}

export function persistTheme(storage: Pick<Storage, 'setItem'> | null, theme: Theme): void {
  try {
    storage?.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // A blocked/full browser store must not prevent switching this page.
  }
}

export function chartPalette(theme: Theme) {
  return theme === 'light'
    ? { a: '#087f8c', b: '#b45819', ink: '#586979', grid: '#d5dce0', axis: '#a6b3bc', pointer: '#253b4a', marker: '#96a6b1', delta: '#7053a6' }
    : { a: '#56dce8', b: '#ffb06b', ink: '#96a5ae', grid: '#233039', axis: '#3b4953', pointer: '#c8d2d8', marker: '#64727d', delta: '#d6c5fb' };
}
