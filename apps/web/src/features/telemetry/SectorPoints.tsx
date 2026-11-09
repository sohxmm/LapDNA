import {seconds, signed} from './view';

export function SectorPoints({nameA,nameB,a,b}:{nameA:string;nameB:string;a:readonly number[];b:readonly number[]}) {
  const each=a.map((t,i)=>b[i]-t);
  const cumulative=[0,...each.map((_,i)=>each.slice(0,i+1).reduce((n,k)=>n+k,0))];
  const limit=Math.max(1,...cumulative.map(Math.abs));
  return <section className="sector-points"><p className="eyebrow">RECORDED SPLITS</p><h2>Gap at sector crossings</h2>
    <p>Points show the cumulative gap at each crossing. Timing alone cannot locate a loss between crossings.</p>
    <svg viewBox="0 0 640 138" role="img" aria-label="Four separate points: start and the three sector crossings; no intermediate estimates">
      <line x1="38" y1="68" x2="605" y2="68" stroke="#44535e" strokeDasharray="3 4"/>
      {cumulative.map((v,i)=>{const x=50+180*i,y=68-v/limit*33;return <g key={i}><circle cx={x} cy={y} r="4.5" fill={i===0?'#abb9c4':v>=0?'var(--a)':'var(--b)'}/><text x={x} y={y-10} textAnchor="middle">{signed(v)} s</text><text className="sector-name" x={x} y="128" textAnchor="middle">{['Start','S1 end','S2 end','Finish'][i]}</text></g>;})}
    </svg>
    <table className="readout"><caption>Recorded sector durations, seconds</caption><thead><tr><th>Sector</th><th>{nameA}</th><th>{nameB}</th><th>B − A</th></tr></thead>
    <tbody>{each.map((v,i)=><tr key={i}><th>S{i+1}</th><td>{seconds(a[i])}</td><td>{seconds(b[i])}</td><td>{signed(v)}</td></tr>)}</tbody></table>
  </section>;
}
