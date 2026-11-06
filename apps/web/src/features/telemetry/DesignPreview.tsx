import {useState} from 'react';
import fixture from './design-fixture.json';
import {TraceBoard} from './TraceBoard';
import {SectorPoints} from './SectorPoints';
import {seconds, signed} from './view';
import type {SignalProvenanceSet, TraceView} from './view';
import './trace.css';

const previewProvenance:SignalProvenanceSet={
  speed:{status:'synthetic',sourceChannel:null,reason:'Constructed preview fixture; no source measurement'},
  throttle:{status:'synthetic',sourceChannel:null,reason:'Constructed preview fixture; no source measurement'},
  gear:{status:'synthetic',sourceChannel:null,reason:'Constructed preview fixture; no source measurement'},
  brake:{status:'synthetic',sourceChannel:null,reason:'Constructed preview fixture; no source measurement'},
};
const preview:TraceView={...fixture,nameA:'Sample A',nameB:'Sample B',provenanceA:previewProvenance,provenanceB:previewProvenance};

export default function DesignPreview() {
  const [mode,setMode]=useState<'trace'|'sector'>('trace');
  return <><header className="site-header"><a className="wordmark" href="/">LAP<span>DNA</span><i aria-hidden="true"/></a><a className="back-link" href="/">← Session workspace</a></header>
    <main className="studio"><p className="eyebrow">DESIGN PREVIEW / FICTIONAL TEST LOOP</p><h1>Telemetry studio</h1>
    <div className="synthetic-banner"><strong>Synthetic demonstration</strong> All drivers, turns, timings and findings on this page are constructed examples.</div>
    <div className="studio-toolbar"><div className="lap-id"><span className="key-a">A / Q3</span><strong>Sample A</strong><small>{seconds(fixture.elapsedAMs)} s</small></div><div className="lap-id"><span className="key-b">B / Q3</span><strong>Sample B</strong><small>{seconds(fixture.elapsedBMs)} s</small></div>
    <div className="mode-buttons" aria-label="Preview data mode"><button aria-pressed={mode==='trace'} onClick={()=>setMode('trace')}>Telemetry</button><button aria-pressed={mode==='sector'} onClick={()=>setMode('sector')}>Sectors only</button></div></div>
    {mode==='trace'?<><TraceBoard view={preview}/>
      <section className="class-review"><p className="eyebrow">COMPARISON ANALYSIS / SYNTHETIC</p><h2>Corner speed profile</h2>
      <p>In this example, Sample A gains through the medium- and high-speed windows, while Sample B gains through the low-speed windows. The totals describe these six windows on these two laps.</p>
      <div className="class-grid">{fixture.categories.map(c=><article key={c.category}><p>{c.category.toUpperCase()} SPEED</p><h3>{signed(c.netMs,2)} s</h3><span>{c.labels.join(' · ')} · {c.labels.length} windows</span><p>A gains {seconds(c.forAMs,2)} s / B gains {seconds(c.forBMs,2)} s</p></article>)}</div>
      <small>Reference minimum speed: low &lt;150 km/h; medium 150–&lt;250; high ≥250. These are versioned LapDNA thresholds. Straights are separate.</small></section></>
      : <><SectorPoints nameA={preview.nameA} nameB={preview.nameB} a={fixture.sectorAMs} b={fixture.sectorBMs}/><aside className="synthetic-banner">Sector-only example: no continuous delta, turn attribution or corner-speed findings are available from these splits alone.</aside></>}
    </main></>;
}
