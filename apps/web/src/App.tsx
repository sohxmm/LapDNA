import { useEffect, useState } from 'react';
import { fetchCatalog } from './api';

type LoadState =
  | { status: 'loading' }
  | { status: 'ready'; count: number }
  | { status: 'error'; message: string };

const surfaces = [
  ['01', 'Find the difference', 'A track map will show where either lap gained time, with a shared distance cursor.'],
  ['02', 'Follow the evidence', 'Speed, throttle, gear and brake state will line up beneath a single delta trace.'],
  ['03', 'Tell the story', 'Up to three supported observations will connect local gains to measured patterns.'],
];

export function App() {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: 'loading' });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: 'loading' });
    fetchCatalog(controller.signal)
      .then((catalog) => setState({ status: 'ready', count: catalog.comparisons.length }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setState({ status: 'error', message: error instanceof Error ? error.message : 'Unable to reach the API.' });
        }
      });
    return () => controller.abort();
  }, [attempt]);

  return (
    <>
      <a className="skip-link" href="#workspace">Skip to workspace</a>
      <header className="site-header">
        <a className="wordmark" href="/" aria-label="LapDNA home">LAP<span>DNA</span><i aria-hidden="true" /></a>
        <span className="build-label">PROJECT FOUNDATION <span>v0.1</span></span>
      </header>
      <main id="workspace">
        <section className="intro" aria-labelledby="title">
          <p className="eyebrow"><span aria-hidden="true" /> QUALIFYING, UNDER THE MICROSCOPE</p>
          <h1>Where did the<br /><em>lap time</em> go?</h1>
          <p className="lede">Two laps. One distance axis. A clearer view of where the difference developed.</p>
          <div className="legend" aria-label="Planned comparison convention">
            <span><i className="dot a" /> Driver A</span>
            <span><i className="dot b" /> Driver B</span>
            <span className="legend-note">Positive delta = A ahead</span>
          </div>
        </section>

        <section className="workspace-panel" aria-labelledby="workspace-title">
          <div className="panel-heading">
            <div><p className="eyebrow">COMPARISON WORKSPACE</p><h2 id="workspace-title">The foundation is ready.</h2></div>
            <span className="status-pill">Scaffold</span>
          </div>
          <div className="data-state" aria-live="polite" aria-busy={state.status === 'loading'}>
            <div className="state-icon" aria-hidden="true">{state.status === 'error' ? '!' : '↗'}</div>
            <div>
              <h3>{state.status === 'loading' ? 'Checking the data catalogue…' : state.status === 'error' ? 'The data service is unavailable.' : state.count ? `${state.count} prepared comparisons found.` : 'No laps imported yet.'}</h3>
              <p>{state.status === 'error' ? state.message : state.status === 'ready' && state.count ? 'The API is serving data. Interactive comparison views are the next implementation milestone.' : 'The next milestone imports and validates the first qualifying session. Real telemetry will appear here once it passes the quality checks.'}</p>
              {state.status === 'error' && <p className="hint">For local development, start the Python API on port 8000.</p>}
              {state.status !== 'loading' && <button className="secondary-button" onClick={() => setAttempt((value) => value + 1)}>{state.status === 'error' ? 'Retry connection' : 'Refresh catalogue'} <span aria-hidden="true">↻</span></button>}
            </div>
          </div>
          <div className="circuit-strip"><span>PLANNED CIRCUITS</span><strong>Monza</strong><strong>Silverstone</strong><strong>Suzuka</strong><small>Availability pending validation</small></div>
        </section>

        <section className="surface-grid" aria-label="Planned analysis views">
          {surfaces.map(([number, title, description]) => <article className="surface" key={number}><span className="surface-number">{number} / PLANNED</span><h2>{title}</h2><p>{description}</p></article>)}
        </section>

        <aside className="method-note"><span>MEASURED, WITH LIMITS</span><p>Official timing will check the comparison. Public telemetry supports approximate local analysis; it cannot establish precisely why time was lost. Brake means on/off, not pressure.</p></aside>
      </main>
      <footer><span>LAPDNA / DISTANCE REVEALS THE DIFFERENCE</span><a href="https://github.com/sohxmm/LapDNA">Project &amp; methodology <span aria-hidden="true">↗</span></a></footer>
    </>
  );
}
