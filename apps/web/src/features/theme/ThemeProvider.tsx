import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { persistTheme, resolveTheme, storedTheme, THEME_EVENT, THEME_STORAGE_KEY } from './theme';
import type { Theme } from './theme';
import './theme.css';

type ThemeContextValue = { theme: Theme; setTheme: (theme: Theme) => void };
const ThemeContext = createContext<ThemeContextValue>({ theme: 'dark', setTheme: () => undefined });

function browserStorage() {
  try { return window.localStorage; } catch { return null; }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() =>
    typeof document === 'undefined'
      ? 'dark'
      : document.documentElement.dataset.theme
        ? resolveTheme(document.documentElement.dataset.theme)
        : storedTheme(browserStorage()),
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#0b131c' : '#f0efe7');
    persistTheme(browserStorage(), theme);
    window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: theme }));
  }, [theme]);

  useEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key === THEME_STORAGE_KEY || event.key === null) setTheme(resolveTheme(event.newValue));
    };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}
