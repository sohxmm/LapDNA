import {useEffect, useMemo, useRef, useState} from 'react';
import {init, use} from 'echarts/core';
import type {EChartsCoreOption, EChartsType} from 'echarts/core';
import {LineChart} from 'echarts/charts';
import {GridComponent, TooltipComponent, MarkLineComponent, AxisPointerComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';
import {availableSignals, groupTurnMarkers, hasSupportedSignal, nearest, signalLabels, signalOrder, signed, supportedSample} from './view';
import type {SignalName, TraceView} from './view';
import {useTheme} from '../theme/ThemeProvider';
import {chartPalette} from '../theme/theme';

use([LineChart, GridComponent, TooltipComponent, MarkLineComponent, AxisPointerComponent, CanvasRenderer]);
export type TraceWindow = {label:string; start:number; end:number} | null;
const layout = [[24,160],[218,48],[300,40],[374,46],[454,86]];
const axisNames = ['SPEED  ·  KM/H','THROTTLE  ·  %','GEAR','BRAKE  ·  BINARY STATES','CUMULATIVE Δ  ·  S'];
const labels = (v:number|null|undefined) => v == null ? '—' : String(Math.round(v));

export function chartRows(view:TraceView) {
  const shown=availableSignals(view);
  const indices=[...signalOrder.flatMap((name,i)=>shown.includes(name)?[i]:[]),4];
  let top=24;
  return indices.map(original=>{
    const height=layout[original][1];
    const row={original,top:indices.length===5?layout[original][0]:top,height};
    top+=height+38;
    return row;
  });
}

function options(v:TraceView, start:number, end:number, colors:ReturnType<typeof chartPalette>):EChartsCoreOption {
  const {a:A,b:B,ink:INK}=colors;
  const series:Record<string,unknown>[]=[];
  const deltaExtent=Math.max(.02,...v.delta.flatMap((value,i)=>value!==null&&v.distance[i]>=start&&v.distance[i]<=end?[Math.abs(value/1000)]:[]))*1.12;
  const rows=chartRows(v), marked=new Set<number>();
  const divisions = v.boundaries.filter(d=>d>=start && d<=end).map(d=>({xAxis:d}));
  const add=(index:number, vals:(number|null)[], name:string, color:string, dashed=false, step=false, extraLine=false)=>{
    const actual=rows.findIndex(row=>row.original===index);
    if(actual<0) return;
    if(index<4 && !hasSupportedSignal(dashed?v.b:v.a,dashed?v.provenanceB:v.provenanceA,signalOrder[index])) return;
    const markers:Record<string,number>[] = [...divisions];
    if (extraLine) markers.push({yAxis:0});
    const first=!marked.has(actual); marked.add(actual);
    series.push({name,type:'line',xAxisIndex:actual,yAxisIndex:actual,
      data:v.distance.map((d,i)=>[d,vals[i]]), showSymbol:false, animation:false, clip:true,
      step:step?'end':false, connectNulls:false, smooth:false,
      emphasis:{disabled:true},lineStyle:{color,width:index===0?2.3:1.8,type:dashed?'dashed':'solid'},
      itemStyle:{color},...(!first?{}:{markLine:{silent:true,animation:false,symbol:'none',
        label:{show:false},lineStyle:{color:colors.marker,type:'dashed',width:1},data:markers}})});
  };
  add(0,v.a.speed,v.nameA,A); add(0,v.b.speed,v.nameB,B,true);
  add(1,v.a.throttle,v.nameA,A); add(1,v.b.throttle,v.nameB,B,true);
  add(2,v.a.gear,v.nameA,A,false,true); add(2,v.b.gear,v.nameB,B,true,true);
  const binary=(b:(boolean|null)[],offset=0)=>b.map(k=>k===null?null:Number(k)+offset);
  add(3,binary(v.a.brake),v.nameA,A,false,true); add(3,binary(v.b.brake,2),v.nameB,B,true,true);
  add(4,v.delta.map(x=>x===null?null:x/1000),'B − A',colors.delta,false,false,true);
  return {animation:false,backgroundColor:'transparent',textStyle:{fontFamily:'system-ui, sans-serif',color:INK},
    grid:rows.map(({top,height})=>({top,height,left:55,right:25,outerBoundsMode:'none'})),
    tooltip:{trigger:'axis',showContent:false,axisPointer:{type:'line',snap:true}},
    axisPointer:{link:[{xAxisIndex:'all'}],label:{show:false},lineStyle:{color:colors.pointer,width:1}},
    xAxis:rows.map((_,i)=>({type:'value',gridIndex:i,min:start,max:end,boundaryGap:false,
      splitNumber:4,axisLabel:{show:i===rows.length-1,color:INK,fontSize:10,hideOverlap:true,formatter:(n:number)=>Math.round(n)+' m'},
      axisTick:{show:false},axisLine:{show:i===rows.length-1,lineStyle:{color:colors.axis}},splitLine:{show:false}})),
    yAxis:rows.map(({original},i)=>({type:'value',gridIndex:i,name:axisNames[original],nameGap:8,nameLocation:'end',
      nameTextStyle:{align:'left',fontSize:9,color:INK,fontWeight:600},scale:original===0 || original===4,
      ...(original===1?{min:0,max:100,interval:50}:original===2?{min:0,max:8,interval:4}:original===3?{min:0,max:3,interval:1}:original===4?{min:-deltaExtent,max:deltaExtent}:{}),
      splitNumber:2,axisLabel:{color:INK,fontSize:9,formatter:original===3?(n:number)=>['A off','A on','B off','B on'][n]:undefined},
      axisLine:{show:false},axisTick:{show:false},splitLine:{lineStyle:{color:colors.grid,width:0.65}}})),
    series};
}

export function TraceBoard({view,cursor:externalCursor,onCursorChange,selection:externalSelection,onSelectionChange}:{
  view:TraceView; cursor?:number; onCursorChange?:(distance:number)=>void;
  selection?:TraceWindow; onSelectionChange?:(selection:TraceWindow)=>void;
}) {
  const {theme}=useTheme();
  const host=useRef<HTMLDivElement>(null), chart=useRef<EChartsType|null>(null);
  const [localSelection,setLocalSelection]=useState<TraceWindow>(null), [localCursor,setLocalCursor]=useState(0);
  const [pinned,setPinned]=useState(false), pinnedRef=useRef(false);
  const [railWidth,setRailWidth]=useState(800);
  const cursorChange=useRef(onCursorChange); cursorChange.current=onCursorChange;
  pinnedRef.current=pinned;
  const selection=externalSelection===undefined?localSelection:externalSelection;
  const cursor=externalCursor??localCursor;
  const turn=view.turns.find(t=>t.label===selection?.label);
  const start=selection?.start??0, end=selection?.end??view.distance[view.distance.length-1];
  const firstIndex=Math.max(0,view.distance.findIndex(distance=>distance>=start));
  let lastIndex=view.distance.length-1;while(lastIndex>firstIndex&&view.distance[lastIndex]>end)lastIndex--;
  const index=Math.max(firstIndex,Math.min(lastIndex,nearest(view.distance,Math.max(start,Math.min(end,cursor)))));
  const d=view.distance[index];
  const option=useMemo(()=>options(view,start,end,chartPalette(theme)),[view,start,end,theme]);
  const signals=availableSignals(view), rows=chartRows(view);
  const plotHeight=rows.at(-1)!.top+rows.at(-1)!.height+34;
  useEffect(()=>{
    if(!host.current) return;
    const c=init(host.current,null,{renderer:'canvas'}); chart.current=c;
    c.on('updateAxisPointer',(raw: unknown)=>{
      const evt=raw as {axesInfo?:{value?:number}[]};
      const value=evt.axesInfo?.[0]?.value;
      if(!pinnedRef.current&&typeof value==='number'&&Number.isFinite(value)) {
        setLocalCursor(value); cursorChange.current?.(value);
      }
    });
    c.on('click',()=>setPinned(true));
    const observer=new ResizeObserver(()=>{c.resize();setRailWidth(Math.max(1,(host.current?.clientWidth??880)-80));}); observer.observe(host.current);
    return ()=>{observer.disconnect();c.dispose();chart.current=null;};
  },[]);
  useEffect(()=>{chart.current?.setOption(option,{notMerge:true});},[option]);
  useEffect(()=>{
    if(externalCursor!==undefined) chart.current?.dispatchAction({type:'showTip',seriesIndex:0,dataIndex:nearest(view.distance,externalCursor)});
  },[externalCursor,view.distance]);
  function setCursor(value:number) {setLocalCursor(value);onCursorChange?.(value);}
  function setSelection(value:TraceWindow) {setLocalSelection(value);onSelectionChange?.(value);}
  function select(label:string) {
    const selected=view.turns.find(t=>t.label===label);
    setSelection(selected?{label:selected.label,start:selected.start,end:selected.end}:null);
    setCursor(selected?.at??0);
  }
  function inspect(value:number) {
    setCursor(value); chart.current?.dispatchAction({type:'showTip',seriesIndex:0,dataIndex:nearest(view.distance,value)});
  }
  const pos=(x:number)=>100*(x-start)/(end-start);
  const last=view.distance.at(-1)!;
  const edge=[0,...view.boundaries,last];
  function cell(slot:'a'|'b',name:SignalName) {
    const value=supportedSample(view,slot,name,index);
    if(value===null) return '—';
    return name==='brake'?(value?'On':'Off'):labels(value as number)+(name==='speed'?' km/h':name==='throttle'?'%':'');
  }
  function source(slot:'a'|'b',name:SignalName) {
    const provenance=(slot==='a'?view.provenanceA:view.provenanceB)[name];
    return provenance.status==='measured'?'Source '+provenance.sourceChannel+' · aligned display samples'
      : provenance.status==='synthetic'?'Synthetic preview fixture':provenance.reason??'No source measurement';
  }
  return <section className="trace-board" aria-label="Distance-aligned telemetry">
    <div className="trace-tools"><div><p className="eyebrow">TELEMETRY / DISTANCE</p><h2>The lap, side by side.</h2></div>
      <label>Inspect turn <select value={selection?.label??''} onChange={e=>select(e.target.value)}><option value="">Full lap</option>{selection&&!turn&&<option value={selection.label}>{selection.label}</option>}{view.turns.map(t=><option key={t.label} value={t.label}>{t.label} · {t.speedClass} speed</option>)}</select></label></div>
    <div className="trace-legend"><span className="key-a">{view.nameA} · solid</span><span className="key-b">{view.nameB} · dashed</span><span>Positive Δ: {view.nameA} ahead</span></div>
    <div className="strip-label">Estimated minisector gain <span>100 m · grey: within 0.01 s · striped: unavailable</span></div>
    <div className="trace-rail bins">{view.bins.map(b=>{
      const a=Math.max(start,b.start), z=Math.min(end,b.end);if(a>=z)return null;
      const tone=b.gain===null?'unknown':Math.abs(b.gain)<10?'tie':b.gain>0?'a':'b';
      return <span key={b.start} className={'bin '+tone} style={{left:pos(a)+'%',width:(pos(z)-pos(a))+'%'}}
        title={b.start+'–'+b.end+' m: '+(b.gain===null?'unsupported':signed(b.gain)+' s')}/>;
    })}</div>
    <div className="trace-rail sectors">{edge.slice(0,-1).map((n,i)=>{
      const a=Math.max(start,n), b=Math.min(end,edge[i+1]);if(a>=b)return null;
      return <span key={i} style={{left:pos(a)+'%',width:(pos(b)-pos(a))+'%'}}>S{i+1}</span>;
    })}</div>
    <div className="trace-rail turn-rail" aria-label="Turn positions">{view.turns.filter(t=>t.at>=start&&t.at<=end).map(t=><i aria-hidden="true" key={'tick'+t.label} style={{position:'absolute',left:pos(t.at)+'%',height:10,borderLeft:'1px solid var(--muted)'}}/>)}
      {groupTurnMarkers(view.turns,start,end,railWidth).map(group=>{
        const first=group[0],last=group.at(-1)!,label=group.length===1?first.label:first.label+'–'+last.label;
        return <button key={label} onClick={()=>{
          if(group.length===1)select(first.label);
          else {setSelection({label,start:first.start,end:last.end});setCursor(first.at);}
        }} style={{left:pos((first.at+last.at)/2)+'%',top:12}} aria-label={'Inspect '+label+(group.length>1?' turn group':'')}>{label}</button>;
      })}</div>
    <div className="plot-canvas" ref={host} style={{height:plotHeight}} role="img" aria-label={signals.map(name=>signalLabels[name]).join(', ')+', and cumulative elapsed-time difference by distance. Use the cursor control for numeric values.'}/>
    <div className="cursor-control"><label>Distance cursor <output>{Math.round(d)} m</output><input type="range" min={view.distance[firstIndex]} max={view.distance[lastIndex]} step={5} value={d}
      onChange={e=>inspect(Number(e.target.value))} onKeyDown={e=>{if(e.shiftKey&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){e.preventDefault();inspect(Math.max(start,Math.min(end,d+(e.key==='ArrowRight'?50:-50))));}}} aria-label="Distance cursor in metres"/></label>
      <p>{selection?.label??'Full lap'} · Δ {view.delta[index]===null?'—':signed(view.delta[index]!)} s</p>
      <button type="button" className="secondary-button" aria-pressed={pinned} onClick={()=>setPinned(!pinned)}>{pinned?'Unpin cursor':'Pin cursor'}</button>
      {selection&&<button type="button" className="secondary-button" onClick={()=>{setSelection(null);setCursor(d);}}>Full lap</button>}</div>
    <table className="readout"><caption>Source-supported channels at the cursor</caption><thead><tr><th>Driver</th>{signals.map(name=><th key={name}>{signalLabels[name]}</th>)}</tr></thead>
    <tbody>{([['a',view.nameA],['b',view.nameB]] as const).map(([slot,name])=><tr key={slot}><th>{name}</th>{signals.map(channel=><td key={channel} title={source(slot,channel)}>{cell(slot,channel)}</td>)}</tr>)}</tbody></table>
    <details className="trace-data-details"><summary>Data details</summary><p>Brake displays on/off states in separate A and B lanes. This channel does not measure brake pressure.</p><ul>{signalOrder.map(name=><li key={name}>{signalLabels[name]} · {view.nameA}: {source('a',name)} · {view.nameB}: {source('b',name)}{!signals.includes(name)?' · Trace hidden because neither lap has a measured signal.':''}</li>)}</ul></details>
  </section>;
}
