import {useEffect, useMemo, useRef, useState} from 'react';
import {init, use} from 'echarts/core';
import type {EChartsCoreOption, EChartsType} from 'echarts/core';
import {LineChart} from 'echarts/charts';
import {GridComponent, TooltipComponent, MarkLineComponent, AxisPointerComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';
import {nearest, signed} from './view';
import type {TraceView} from './view';

use([LineChart, GridComponent, TooltipComponent, MarkLineComponent, AxisPointerComponent, CanvasRenderer]);
const A='#56dce8', B='#ffb06b', INK='#96a5ae';
const layout = [[24,128],[186,48],[270,40],[350,23],[416,80]];
const axisNames = ['SPEED  ·  KM/H','THROTTLE  ·  %','GEAR','BRAKE  ·  ON/OFF','CUMULATIVE Δ  ·  S'];
const labels = (v:number|null|undefined) => v == null ? '—' : String(Math.round(v));

function options(v:TraceView, start:number, end:number):EChartsCoreOption {
  const series:Record<string,unknown>[]=[];
  const divisions = v.boundaries.filter(d=>d>=start && d<=end).map(d=>({xAxis:d}));
  const add=(index:number, vals:(number|null)[], name:string, color:string, dashed=false, step=false, extraLine=false)=>{
    const markers:Record<string,number>[] = [...divisions];
    if (extraLine) markers.push({yAxis:0});
    series.push({name,type:'line',xAxisIndex:index,yAxisIndex:index,
      data:v.distance.map((d,i)=>[d,vals[i]]), showSymbol:false, animation:false, clip:true,
      step:step?'end':false, connectNulls:false, smooth:false,
      emphasis:{disabled:true},lineStyle:{color,width:index===0?2.3:1.8,type:dashed?'dashed':'solid'},
      itemStyle:{color},...(dashed?{}:{markLine:{silent:true,animation:false,symbol:'none',
        label:{show:false},lineStyle:{color:'#64727d',type:'dashed',width:1},data:markers}})});
  };
  add(0,v.a.speed,v.nameA,A); add(0,v.b.speed,v.nameB,B,true);
  add(1,v.a.throttle,v.nameA,A); add(1,v.b.throttle,v.nameB,B,true);
  add(2,v.a.gear,v.nameA,A,false,true); add(2,v.b.gear,v.nameB,B,true,true);
  const binary=(b:(boolean|null)[])=>b.map(k=>k===null?null:Number(k));
  add(3,binary(v.a.brake),v.nameA,A,false,true); add(3,binary(v.b.brake),v.nameB,B,true,true);
  add(4,v.delta.map(x=>x===null?null:x/1000),'B − A','#d6c5fb',false,false,true);
  return {animation:false,backgroundColor:'transparent',textStyle:{fontFamily:'system-ui, sans-serif',color:INK},
    grid:layout.map(([top,height])=>({top,height,left:55,right:25,outerBoundsMode:'none'})),
    tooltip:{trigger:'axis',showContent:false,axisPointer:{type:'line',snap:true}},
    axisPointer:{link:[{xAxisIndex:'all'}],label:{show:false},lineStyle:{color:'#c8d2d8',width:1}},
    xAxis:layout.map((_,i)=>({type:'value',gridIndex:i,min:start,max:end,boundaryGap:false,
      splitNumber:4,axisLabel:{show:i===4,color:INK,fontSize:10,hideOverlap:true,formatter:(n:number)=>Math.round(n)+' m'},
      axisTick:{show:false},axisLine:{show:i===4,lineStyle:{color:'#3b4953'}},splitLine:{show:false}})),
    yAxis:layout.map((_,i)=>({type:'value',gridIndex:i,name:axisNames[i],nameGap:8,nameLocation:'end',
      nameTextStyle:{align:'left',fontSize:9,color:'#becbd3',fontWeight:600},scale:i===0 || i===4,
      ...(i===1?{min:0,max:100,interval:50}:i===2?{min:0,max:8,interval:4}:i===3?{min:0,max:1,interval:1}:{}),
      splitNumber:2,axisLabel:{color:INK,fontSize:9,formatter:i===3?(n:number)=>n?'On':'Off':undefined},
      axisLine:{show:false},axisTick:{show:false},splitLine:{lineStyle:{color:'#233039',width:0.65}}})),
    series};
}

export function TraceBoard({view}:{view:TraceView}) {
  const host=useRef<HTMLDivElement>(null), chart=useRef<EChartsType|null>(null);
  const [zoom,setZoom]=useState(''), [cursor,setCursor]=useState(0);
  const turn=view.turns.find(t=>t.label===zoom);
  const start=turn?.start??0, end=turn?.end??view.distance[view.distance.length-1];
  const index=nearest(view.distance,Math.max(start,Math.min(end,cursor)));
  const d=view.distance[index];
  const option=useMemo(()=>options(view,start,end),[view,start,end]);
  useEffect(()=>{
    if(!host.current) return;
    const c=init(host.current,null,{renderer:'canvas'}); chart.current=c;
    c.on('updateAxisPointer',(raw: unknown)=>{
      const evt=raw as {axesInfo?:{value?:number}[]};
      const value=evt.axesInfo?.[0]?.value; if(typeof value==='number' && Number.isFinite(value))setCursor(value);
    });
    const observer=new ResizeObserver(()=>c.resize()); observer.observe(host.current);
    return ()=>{observer.disconnect();c.dispose();chart.current=null;};
  },[]);
  useEffect(()=>{chart.current?.setOption(option,{notMerge:true});},[option]);
  function select(label:string) {
    setZoom(label); setCursor(view.turns.find(t=>t.label===label)?.at??0);
  }
  function inspect(value:number) {
    setCursor(value); chart.current?.dispatchAction({type:'showTip',seriesIndex:0,dataIndex:nearest(view.distance,value)});
  }
  const pos=(x:number)=>100*(x-start)/(end-start);
  const last=view.distance.at(-1)!;
  const edge=[0,...view.boundaries,last];
  return <section className="trace-board" aria-label="Distance-aligned telemetry">
    <div className="trace-tools"><div><p className="eyebrow">TELEMETRY / DISTANCE</p><h2>Where the gap develops</h2></div>
      <label>Inspect turn <select value={zoom} onChange={e=>select(e.target.value)}><option value="">Full lap</option>{view.turns.map(t=><option key={t.label} value={t.label}>{t.label} · {t.speedClass} speed</option>)}</select></label></div>
    <div className="trace-legend"><span className="key-a">{view.nameA} · solid</span><span className="key-b">{view.nameB} · dashed</span><span>Positive Δ: {view.nameA} ahead</span></div>
    <div className="strip-label">Estimated local gain <span>100 m bins · grey = within 0.01 s · striped = unsupported</span></div>
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
    <div className="trace-rail turn-rail" aria-label="Turn positions">{view.turns.filter(t=>t.at>=start && t.at<=end).map(t=>
      <button key={t.label} onClick={()=>select(t.label)} style={{left:pos(t.at)+'%'}} aria-label={'Inspect '+t.label}>{t.label}</button>)}</div>
    <div className="plot-canvas" ref={host} role="img" aria-label="Speed, throttle, gear, brake state and cumulative elapsed-time difference by distance. Use the cursor control for numeric values."/>
    <div className="cursor-control"><label>Distance cursor <output>{Math.round(d)} m</output><input type="range" min={start} max={end} step={5} value={d}
      onChange={e=>inspect(Number(e.target.value))} aria-label="Distance cursor in metres"/></label>
      <p>{turn?turn.label+' · '+turn.speedClass+' speed':'Full lap'} · Δ {view.delta[index]===null?'—':signed(view.delta[index]!)} s</p></div>
    <table className="readout"><caption>Channels at the cursor</caption><thead><tr>{['Driver','Speed','Throttle','Gear','Brake'].map(s=><th key={s}>{s}</th>)}</tr></thead>
    <tbody>{([['a',view.nameA],['b',view.nameB]] as const).map(([k,n])=><tr key={k}><th>{n}</th><td>{labels(view[k].speed[index])} km/h</td><td>{labels(view[k].throttle[index])}%</td><td>{labels(view[k].gear[index])}</td><td>{view[k].brake[index]===null?'—':view[k].brake[index]?'On':'Off'}</td></tr>)}</tbody></table>
  </section>;
}
