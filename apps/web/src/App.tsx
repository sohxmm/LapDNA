import CalendarWorkspace from './features/navigation/CalendarWorkspace';
import {isWorkspaceRoute} from './features/navigation/routing';
import LandingPage from './features/landing/LandingPage';
import {ThemeProvider} from './features/theme/ThemeProvider';
import {ThemeToggle} from './features/theme/ThemeToggle';
import './features/telemetry/trace.css';

function RoutedApp() {
  if (!isWorkspaceRoute(window.location.search)) return <LandingPage/>;
  return <div className="app-shell"><a className="skip-link" href="#workspace">Skip to workspace</a>
    <header className="site-header"><a className="wordmark" href="/" aria-label="LapDNA home">LAP<span>DNA</span><i aria-hidden="true"/></a><nav aria-label="Main"><span className="header-studio-label">QUALIFYING STUDIO</span><ThemeToggle/></nav></header>
    <main id="workspace"><CalendarWorkspace/></main>
    <footer><span>LAPDNA / EVERY TENTH HAS A STORY</span><a href="https://github.com/sohxmm/LapDNA/blob/main/docs/18-data-availability-by-year.md">Data coverage ↗</a><a href="https://github.com/sohxmm/LapDNA">Sources &amp; methodology ↗</a></footer></div>;
}

export function App() {
  return <ThemeProvider><RoutedApp/></ThemeProvider>;
}
