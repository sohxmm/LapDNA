import {useMemo, useState} from 'react';
import {nearest, signed} from '../telemetry/view';
import {orient} from './resultView';
import type {Telemetry} from './resultView';

type Point = {x:number;y:number;index:number};
type Region = Telemetry['segments'][number];

export function PerformanceMap({artifact,swapped,cursor,selected,onCursor,onRegion}:{
  artifact:Telemetry;swapped:boolean;cursor:number;selected:string|null;
  onCursor:(distance:number)=>void;onRegion:(region:Region)=>void;
}) {
  const [layer,setLayer]=useState<'regions'|'minisectors'>('regions');
  const drawing=useMemo(()=>{
    const raw=artifact.geometry.x.flatMap((x,index)=>{
      const y=artifact.geometry.y[index];
      return x===null||y===null?[]:[{x,y:-y,index}];
    });
    if(raw.length<3) return null;
    const minX=Math.min(...raw.map(p=>p.x)),maxX=Math.max(...raw.map(p=>p.x));
    const minY=Math.min(...raw.map(p=>p.y)),maxY=Math.max(...raw.map(p=>p.y));
    const scale=Math.min(580/Math.max(1,maxX-minX),370/Math.max(1,maxY-minY));
    const offsetX=(680-(maxX-minX)*scale)/2,offsetY=(470-(maxY-minY)*scale)/2;
    const points=raw.map(p=>({x:(p.x-minX)*scale+offsetX,y:(p.y-minY)*scale+offsetY,index:p.index}));
    return {points,byIndex:new Map(points.map(p=>[p.index,p]))};
  },[artifact]);
  if(!drawing) return <section className="performance-map"><h3>Track map unavailable</h3><p>No supported reference geometry was published for these laps.</p></section>;
  const a=swapped?artifact.lap_b.driver_code:artifact.lap_a.driver_code;
  const b=swapped?artifact.lap_a.driver_code:artifact.lap_b.driver_code;
  const sameTeam=!!artifact.lap_a.team_colour&&artifact.lap_a.team_colour===artifact.lap_b.team_colour;
  const dash=(gain:number|null)=>gain===null?'2 8':sameTeam&&gain<-10?'12 6':undefined;
  const color=(gain:number|null)=>gain===null?'var(--muted)':Math.abs(gain)<10?'var(--border-strong)':gain>0?'var(--a)':'var(--b)';
  function path(start:number,end:number) {
    let previous=-2;
    return drawing!.points.filter(p=>artifact.distance_m[p.index]>=start&&artifact.distance_m[p.index]<=end)
      .map(p=>{const command=p.index===previous+1?'L':'M';previous=p.index;return command+p.x.toFixed(2)+','+p.y.toFixed(2);}).join(' ');
  }
  function pick(event:React.PointerEvent<SVGPathElement>,region?:Region) {
    const svg=event.currentTarget.ownerSVGElement;
    if(!svg) return;
    const rect=svg.getBoundingClientRect();
    const size=Math.min(rect.width/680,rect.height/470);
    const x=(event.clientX-rect.left-(rect.width-680*size)/2)/size;
    const y=(event.clientY-rect.top-(rect.height-470*size)/2)/size;
    const candidates=region?drawing!.points.filter(p=>artifact.distance_m[p.index]>=region.start_m&&artifact.distance_m[p.index]<=region.end_m):drawing!.points;
    const point=candidates.reduce<Point|null>((best,p)=>!best||Math.hypot(p.x-x,p.y-y)<Math.hypot(best.x-x,best.y-y)?p:best,null);
    if(point) onCursor(artifact.distance_m[point.index]);
  }
  const current=drawing.byIndex.get(nearest(artifact.distance_m,cursor));
  const finish=drawing.byIndex.get(0);
  const ranked=[...artifact.segments].sort((x,y)=>Math.abs(y.gain_ms??0)-Math.abs(x.gain_ms??0)||x.start_m-y.start_m);
  return <section className="performance-map" aria-labelledby="map-heading">
    <div className="trace-tools"><div><p className="eyebrow">TRACK / RELATIVE PERFORMANCE</p><h3 id="map-heading">Where the time moves.</h3></div>
      <label>Map layer<select aria-label="Map performance layer" value={layer} onChange={e=>setLayer(e.target.value as typeof layer)}><option value="regions">Corners and straights</option><option value="minisectors">Estimated 100 m minisectors</option></select></label></div>
    <div className="map-legend"><span className="key-a">{a} gains{sameTeam?' · solid':''}</span><span className="key-b">{b} gains{sameTeam?' · dashed':''}</span><span>Grey: within 0.01 s · dotted: unavailable</span></div>
    <div className="map-layout"><div>
      <svg viewBox="0 0 680 470" role="img" aria-label="Reference circuit coloured by estimated local gain. Use the adjacent region buttons for keyboard inspection.">
        {artifact.segments.map(region=><path key={'base'+region.segment_id} d={path(region.start_m,region.end_m)} fill="none" stroke="var(--border)" strokeWidth="13" strokeLinecap="round"/>)}
        {layer==='regions'?artifact.segments.map(region=>{
          const gain=orient(region.gain_ms,swapped);
          return <path key={region.segment_id} d={path(region.start_m,region.end_m)} fill="none" stroke={color(gain)} strokeWidth={selected===region.segment_id?10:6} strokeDasharray={dash(gain)} strokeLinecap="round" style={{cursor:'pointer'}} onPointerMove={event=>pick(event,region)} onClick={()=>onRegion(region)}>
            <title>{region.label}: {gain===null?'Unavailable':'estimated '+signed(gain,2)+' s'}</title></path>;
        }):artifact.estimated_minisectors.map(bin=>{
          const gain=orient(bin.gain_ms,swapped);
          return <path key={bin.start_m} d={path(bin.start_m,bin.end_m)} fill="none" stroke={color(gain)} strokeWidth="6" strokeDasharray={dash(gain)} onPointerMove={event=>pick(event)}><title>{Math.round(bin.start_m)}–{Math.round(bin.end_m)} m: {gain===null?'Unavailable':signed(gain,2)+' s estimated'}</title></path>;
        })}
        {artifact.corners.map(corner=>{
          const point=drawing.byIndex.get(nearest(artifact.distance_m,corner.distance_m));
          return point?<g key={corner.marker_id}><circle cx={point.x} cy={point.y} r="3" fill="var(--text)"/><text x={point.x+9} y={point.y-8} fontSize="12" fill="var(--text)" paintOrder="stroke" stroke="var(--surface)" strokeWidth="3" strokeLinejoin="round">{corner.label}</text></g>:null;
        })}
        {finish&&<g><rect x={finish.x-4} y={finish.y-4} width="8" height="8" fill="var(--text)"/><text x={finish.x+10} y={finish.y+18} fontSize="10" fill="var(--text-secondary)">S/F</text></g>}
        {current&&<circle cx={current.x} cy={current.y} r="7" fill="var(--surface)" stroke="var(--text)" strokeWidth="2"/>}
      </svg>
      <p className="sc-muted">Approximate reference path · cursor {Math.round(cursor)} m. {artifact.geometry.coordinate_note??'Position geometry is for orientation; local timing uses the shared integrated-speed distance axis.'}</p>
    </div><div className="map-region-list"><h4>Largest differences</h4>
      {ranked.map(region=>{
        const gain=orient(region.gain_ms,swapped);
        return <button type="button" key={region.segment_id} className={'map-region-button'+(selected===region.segment_id?' is-selected':'')} aria-pressed={selected===region.segment_id} onClick={()=>onRegion(region)}>
          <span>{region.label}<small>{region.kind} · {Math.round(region.start_m)}–{Math.round(region.end_m)} m</small></span>
          <strong className={gain===null||Math.abs(gain)<5?'':gain>=0?'key-a':'key-b'}>{gain===null?'Unavailable':signed(gain,2)+' s'}</strong>
        </button>;
      })}
    </div></div>
  </section>;
}
