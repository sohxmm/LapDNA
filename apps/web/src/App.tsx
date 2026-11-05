import {lazy, Suspense} from 'react';
import './features/telemetry/trace.css';

const DesignPreview=lazy(()=>import('./features/telemetry/DesignPreview'));
const SessionBrowser=lazy(()=>import('./features/comparison/SessionBrowser'));
const planned=[
  ['01','Follow the turn','Synchronized speed, throttle, gear, brake state and time delta, with turn numbers on the distance axis.'],
  ['02','Compare any eligible laps','Choose two drivers, their qualifying phases, and their laps from an imported session.'],
  ['03','Understand the pattern','Inspect gains by low-, medium- and high-speed corner windows, with coverage and evidence.'],
];

export function App() {
  if(new URLSearchParams(window.location.search).get('preview')==='1')
    return <Suspense fallback={<p className="loading-page" role="status">Loading the synthetic design preview…</p>}><DesignPreview/></Suspense>;
  return <><a className="skip-link" href="#workspace">Skip to workspace</a>
    <header className="site-header"><a className="wordmark" href="/" aria-label="LapDNA home">LAP<span>DNA</span><i aria-hidden="true"/></a><span className="build-label">PROJECT FOUNDATION <span>v0.2</span></span></header>
    <main id="workspace"><section className="intro"><p className="eyebrow"><span aria-hidden="true"/> QUALIFYING, UNDER THE MICROSCOPE</p><h1>Where did the<br/><em>lap time</em> go?</h1>
      <p className="lede">Two laps. One distance axis. See the gap develop, turn by turn.</p>
      <a className="preview-link" href="?preview=1">Open telemetry design preview ↗ <span className="preview-tag">Synthetic data</span></a>
    </section>
    <Suspense fallback={<p role="status">Loading session workspace…</p>}><SessionBrowser/></Suspense>
    <section className="surface-grid" aria-label="Analysis capabilities">{planned.map(([n,title,text])=><article className="surface" key={n}><span className="surface-number">{n} / ANALYSIS PLAN</span><h2>{title}</h2><p>{text}</p></article>)}</section>
    <aside className="method-note"><span>MEASURED, WITH LIMITS</span><p>Recorded sector times check the comparison. Local gains and 100 m mini-sectors are telemetry estimates. Public data supports speed, throttle, gear and brake state; steering angle and brake pressure are unavailable.</p></aside>
    </main><footer><span>LAPDNA / DISTANCE REVEALS THE DIFFERENCE</span><a href="https://github.com/sohxmm/LapDNA">Project &amp; methodology ↗</a></footer></>;
}
