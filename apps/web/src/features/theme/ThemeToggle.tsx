import { useTheme } from './ThemeProvider';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const dark = theme === 'dark';
  return <button
    type="button"
    role="switch"
    aria-label="Dark mode"
    aria-checked={dark}
    title={'Switch to ' + (dark ? 'light' : 'dark') + ' mode'}
    className="theme-toggle"
    onClick={() => setTheme(dark ? 'light' : 'dark')}
  >
    <svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5">
      {dark
        ? <path d="M16.5 12A7 7 0 0 1 8 3.5 7 7 0 1 0 16.5 12Z"/>
        : <><circle cx="10" cy="10" r="3.25"/><path d="M10 1v2m0 14v2M1 10h2m14 0h2M3.6 3.6 5 5m10 10 1.4 1.4M3.6 16.4 5 15M15 5l1.4-1.4"/></>}
    </svg>
    <span>{dark ? 'Dark' : 'Light'}</span>
  </button>;
}
