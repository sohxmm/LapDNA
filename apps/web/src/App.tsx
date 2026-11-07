import {lazy, Suspense} from 'react';
import CalendarWorkspace from './features/navigation/CalendarWorkspace';
import {isWorkspaceRoute} from './features/navigation/routing';
import LandingPage from './features/landing/LandingPage';
import './features/telemetry/trace.css';

const DesignPreview=lazy(()=>import('./features/telemetry/DesignPreview'));

export function App() {
  if(new URLSearchParams(window.location.search).get('preview')==='1')
    return <Suspense fallback={<p className="loading-page" role="status">Loading the synthetic design preview…</p>}><DesignPreview/></Suspense>;
  if (!isWorkspaceRoute(window.location.search)) return <LandingPage/>;
  return <div className="app-shell"><a className="skip-link" href="#workspace">Skip to workspace</a>
    <header className="site-header"><a className="wordmark" href="/" aria-label="LapDNA home">LAP<span>DNA</span><i aria-hidden="true"/></a><nav aria-label="Main"><span className="header-studio-label">QUALIFYING STUDIO</span><a className="back-link" href="?preview=1">Synthetic demo ↗</a></nav></header>
    <main id="workspace"><CalendarWorkspace/></main>
    <footer><span>LAPDNA / EVERY TENTH HAS A STORY</span><a href="https://github.com/sohxmm/LapDNA">Sources &amp; methodology ↗</a></footer></div>;
}
