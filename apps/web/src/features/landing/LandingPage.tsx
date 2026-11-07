import './landing.css';
import {ThemeToggle} from '../theme/ThemeToggle';

function CircuitArtwork() {
  return <div className="landing-circuit" aria-label="Decorative circuit illustration; schematic, not a measured track map" role="img">
    <svg viewBox="0 0 640 650" aria-hidden="true">
      <defs><pattern id="circuit-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="currentColor" strokeWidth=".5" opacity=".15"/></pattern></defs>
      <rect width="640" height="650" fill="url(#circuit-grid)"/>
      <circle cx="320" cy="325" r="245" className="circuit-orbit"/>
      <circle cx="320" cy="325" r="190" className="circuit-orbit"/>
      <path className="circuit-guide" d="M40 325H600M320 35V615"/>
      <g transform="rotate(-15 320 325)">
        <path className="circuit-shadow" d="M132 450L142 210Q144 170 182 170H300Q326 170 333 194L355 273Q361 293 382 279L471 213Q490 198 505 218L543 269Q556 287 539 308L465 402Q451 420 432 406L397 381Q381 370 368 388L314 468Q300 489 278 473L239 444Q222 432 208 450L185 480Q172 497 151 481L143 475Q132 466 132 450Z"/>
        <path className="circuit-line" d="M132 450L142 210Q144 170 182 170H300Q326 170 333 194L355 273Q361 293 382 279L471 213Q490 198 505 218L543 269Q556 287 539 308L465 402Q451 420 432 406L397 381Q381 370 368 388L314 468Q300 489 278 473L239 444Q222 432 208 450L185 480Q172 497 151 481L143 475Q132 466 132 450Z"/>
        <path className="circuit-highlight" d="M142 210Q144 170 182 170H300Q326 170 333 194L355 273Q361 293 382 279"/>
        <path d="M124 358L145 359" stroke="#f1f0e8" strokeWidth="8"/>
        <circle cx="139" cy="359" r="6" fill="#151612"/>
      </g>
      <g className="circuit-annotations"><path d="M196 128L218 99H285"/><text x="218" y="88">THE ENTRY</text><path d="M522 327L567 351V386"/><text x="492" y="407">THE EXIT</text><path d="M218 489L174 530H91"/><text x="92" y="550">THE DIFFERENCE</text></g>
      <text className="circuit-index" x="34" y="54">L / DNA — 001</text>
      <text className="circuit-index" x="432" y="613">SCHEMATIC / NOT TO SCALE</text>
    </svg>
    <div className="circuit-caption"><span className="landing-dot"/> ONE LAP. A THOUSAND DETAILS.</div>
  </div>;
}

export default function LandingPage() {
  return <div className="landing-page">
    <a className="skip-link" href="#landing-main">Skip to content</a>
    <header className="landing-header"><a href="/" className="landing-wordmark" aria-label="LapDNA home">LAP<span>DNA</span><i aria-hidden="true"/></a><span>FORMULA 1 / LAP COMPARISON</span><div className="landing-header-actions"><a className="landing-demo" href="?preview=1">Explore the demo <span aria-hidden="true">↗</span></a><ThemeToggle/></div></header>
    <main id="landing-main" className="landing-main">
      <div className="landing-kicker"><span>THE TIME IS ONLY THE BEGINNING.</span><span>EST. 2026</span></div>
      <section className="landing-hero" aria-labelledby="landing-title">
        <div className="landing-copy"><h1 id="landing-title">WHERE DID<br/>THE LAP<br/><span>TIME GO?</span></h1><div className="landing-intro"><p>Two drivers. One circuit.<br/>Find the difference.</p><a className="landing-cta" href="?view=calendar">Open Studio <span aria-hidden="true">↗</span></a></div></div>
        <CircuitArtwork/>
      </section>
      <div className="landing-bottom"><p><span>01</span> CHOOSE A SEASON <i aria-hidden="true">/</i> <span>02</span> PICK A RACE <i aria-hidden="true">/</i> <span>03</span> COMPARE DRIVERS</p><span>BUILT AROUND THE DATA.</span></div>
      <section className="landing-preview" aria-labelledby="preview-title"><div><p className="eyebrow">INSIDE THE STUDIO</p><h2 id="preview-title">A closer look<br/>at every tenth.</h2><p>Recorded qualifying times. Synchronized telemetry, when verified.</p><a href="?preview=1">View the synthetic telemetry demo ↗</a></div><div className="landing-traces" aria-hidden="true"><div><span>ILLUSTRATIVE TRACES</span><span>A / B</span></div><svg viewBox="0 0 650 240" preserveAspectRatio="none"><path className="preview-grid" d="M0 50H650M0 115H650M0 180H650M140 0V240M330 0V240M510 0V240"/><path className="preview-a" d="M0 74Q35 30 80 28H120L156 142Q174 167 196 136L217 76Q240 43 285 45H310L345 133Q360 166 385 122L411 83Q440 68 478 66L520 163Q535 186 555 151L585 96Q610 61 650 44"/><path className="preview-b" d="M0 81Q35 37 80 33H123L158 148Q180 174 201 138L220 81Q240 49 285 49H314L349 142Q365 172 391 130L415 89Q440 76 480 74L524 175Q540 192 560 159L588 103Q615 68 650 52"/><path className="preview-delta" d="M0 215L100 215Q140 211 174 205T240 211T330 204T390 214T470 200T540 209T650 195"/></svg><span>SHARED DISTANCE →</span></div></section>
    </main>
    <footer className="landing-footer"><span>LAPDNA / EVERY TENTH HAS A STORY</span><a href="https://github.com/sohxmm/LapDNA">Sources &amp; methodology ↗</a></footer>
  </div>;
}
