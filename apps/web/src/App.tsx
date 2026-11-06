import {lazy, Suspense} from 'react';
import CalendarWorkspace from './features/navigation/CalendarWorkspace';
import './features/telemetry/trace.css';

const DesignPreview=lazy(()=>import('./features/telemetry/DesignPreview'));

export function App() {
  if(new URLSearchParams(window.location.search).get('preview')==='1')
    return <Suspense fallback={<p className="loading-page" role="status">Loading the synthetic design preview…</p>}><DesignPreview/></Suspense>;
  return <><a className="skip-link" href="#workspace">Skip to workspace</a>
    <header className="site-header"><a className="wordmark" href="/" aria-label="LapDNA home">LAP<span>DNA</span><i aria-hidden="true"/></a><a className="back-link" href="?preview=1">Fictional design preview ↗</a></header>
    <main id="workspace"><CalendarWorkspace/>
    <aside className="method-note"><span>SOURCE FIRST</span><p>Every telemetry panel depends on the selected source's actual channels. Missing measurements remain unavailable. Derived local timing and corner classes are identified as estimates with evidence.</p></aside>
    </main><footer><span>LAPDNA / DISTANCE REVEALS THE DIFFERENCE</span><a href="https://github.com/sohxmm/LapDNA">Project &amp; methodology ↗</a></footer></>;
}
