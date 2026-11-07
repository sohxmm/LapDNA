import {useState} from 'react';
import {useTheme} from '../theme/ThemeProvider';
import {chartPalette} from '../theme/theme';
import {lapTime} from './selection';
import {orient} from './resultView';
import {signed} from '../telemetry/view';
import type {PairResponse} from './resultView';
import type {Theme} from '../theme/theme';

type Artifact=PairResponse['artifact'];
export function comparisonLink(result:PairResponse,origin:string) {
  const {artifact,swapped}=result;
  const a=swapped?artifact.lap_b:artifact.lap_a,b=swapped?artifact.lap_a:artifact.lap_b;
  const query=new URLSearchParams({year:String(artifact.session.year),race:artifact.session.year+'-'+artifact.session.round,view:'studio',analysis:'telemetry',lapSession:artifact.session.session_id,lapA:a.lap_id,lapB:b.lap_id,dataset:artifact.provenance.source_snapshot_sha256,detail:artifact.detail_level,comparison:artifact.comparison_id});
  if(a.phase!==b.phase)query.set('cross','1');
  return origin+'/?'+query.toString();
}

export function sourceName(artifact:Artifact) {
  return artifact.provenance.source==='fastf1'?'FastF1':artifact.provenance.source==='openf1'?'OpenF1':'OpenF1 + TracingInsights / FastF1';
}

function download(blob:Blob,name:string) {
  const url=URL.createObjectURL(blob),anchor=document.createElement('a');
  anchor.href=url;anchor.download=name;document.body.append(anchor);anchor.click();anchor.remove();
  window.setTimeout(()=>URL.revokeObjectURL(url),1000);
}

async function renderCard(result:PairResponse,theme:Theme) {
  await document.fonts.ready;
  const canvas=document.createElement('canvas');canvas.width=1080;canvas.height=1350;
  const ctx=canvas.getContext('2d');if(!ctx)throw new Error('Image export is unavailable in this browser.');
  const colors=chartPalette(theme),dark=theme==='dark',bg=dark?'#0b131c':'#f0efe7',text=dark?'#eef3f8':'#182734',muted=dark?'#a4b5c3':'#506270',surface=dark?'#142332':'#e5e7df';
  const {artifact,swapped}=result,a=swapped?artifact.lap_b:artifact.lap_a,b=swapped?artifact.lap_a:artifact.lap_b;
  ctx.fillStyle=bg;ctx.fillRect(0,0,1080,1350);
  function write(value:string,x:number,y:number,size=20,color=text,weight=400) {ctx!.font=weight+' '+size+'px system-ui, sans-serif';ctx!.fillStyle=color;ctx!.fillText(value,x,y);}
  function wrap(value:string,x:number,y:number,width:number,size=20,lineHeight=29,maxLines=3,color=text) {
    ctx!.font='400 '+size+'px system-ui, sans-serif';
    const words=value.split(/\s+/);let line='',row=0;
    for(let i=0;i<words.length;i++) {
      const next=(line?' ':'')+words[i];
      if(ctx!.measureText(line+next).width>width&&line) {
        write(line,x,y+row*lineHeight,size,color);row++;line=words[i];
        if(row===maxLines-1) {
          let rest=[line,...words.slice(i+1)].join(' ');let truncated=false;
          while(ctx!.measureText(rest+(truncated?'…':'')).width>width&&rest.length>1){rest=rest.slice(0,-2);truncated=true;}
          write(rest+(truncated?'…':''),x,y+row*lineHeight,size,color);return;
        }
      } else line+=next;
    }
    if(line)write(line,x,y+row*lineHeight,size,color);
  }
  write('LAPDNA / QUALIFYING',52,60,22,text,800);
  write(artifact.session.year+' · '+artifact.session.event_name,52,111,31,text,700);
  write(artifact.detail_level==='telemetry'?'DISTANCE REVEALS THE DIFFERENCE':'RECORDED SECTOR TIMING',52,150,15,muted,600);
  [a,b].forEach((lap,i)=>{
    const x=52+i*496;ctx!.fillStyle=surface;ctx!.fillRect(x,182,480,155);
    ctx!.fillStyle=i===0?colors.a:colors.b;ctx!.fillRect(x,182,480,4);
    write((i===0?'A':'B')+' / '+lap.driver_name,x+19,220,23,text,650);
    write(lap.phase+' · Lap '+lap.lap_number+' · '+lap.compound,x+19,253,17,muted);
    write(lapTime(lap.lap_time_ms),x+19,304,36,i===0?colors.a:colors.b,650);
  });
  const gap=b.lap_time_ms-a.lap_time_ms;
  write('Recorded gap: '+signed(gap)+' s · '+(gap===0?'equal times':(gap>0?a.driver_code:b.driver_code)+' ahead'),52,381,25,text,650);
  write('B − A · Positive favours '+a.driver_code,52,410,16,muted);
  if(artifact.detail_level==='telemetry') {
    const points=artifact.geometry.x.flatMap((x,i)=>x===null||artifact.geometry.y[i]===null?[]:[{x,y:-artifact.geometry.y[i]!,i}]);
    if(points.length>2) {
      const minX=Math.min(...points.map(p=>p.x)),maxX=Math.max(...points.map(p=>p.x)),minY=Math.min(...points.map(p=>p.y)),maxY=Math.max(...points.map(p=>p.y));
      const scale=Math.min(420/Math.max(1,maxX-minX),255/Math.max(1,maxY-minY));
      const ox=62+(420-(maxX-minX)*scale)/2,oy=462+(255-(maxY-minY)*scale)/2;
      artifact.segments.forEach(segment=>{
        const gain=orient(segment.gain_ms,swapped);ctx!.strokeStyle=gain===null?muted:Math.abs(gain)<10?colors.axis:gain>0?colors.a:colors.b;ctx!.lineWidth=5;ctx!.lineCap='round';ctx!.beginPath();let previous=-2;
        points.filter(p=>artifact.distance_m[p.i]>=segment.start_m&&artifact.distance_m[p.i]<=segment.end_m).forEach(p=>{
          const x=ox+(p.x-minX)*scale,y=oy+(p.y-minY)*scale;
          if(p.i!==previous+1)ctx!.moveTo(x,y);else ctx!.lineTo(x,y);previous=p.i;
        });ctx!.stroke();
      });
    }
    const left=558,top=488,width=455,height=204,last=artifact.distance_m.at(-1)!;
    const delta=artifact.delta_ms.map(value=>orient(value,swapped));
    const extent=Math.max(20,...delta.filter((v):v is number=>v!==null).map(Math.abs))*1.12;
    ctx.strokeStyle=colors.axis;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(left,top+height/2);ctx.lineTo(left+width,top+height/2);ctx.stroke();
    ctx.strokeStyle=colors.delta;ctx.lineWidth=3;ctx.beginPath();let active=false;
    delta.forEach((value,i)=>{if(value===null){active=false;return;}const x=left+artifact.distance_m[i]/last*width,y=top+height/2-value/extent*height/2;if(active)ctx!.lineTo(x,y);else ctx!.moveTo(x,y);active=true;});ctx.stroke();
    write('Estimated cumulative delta (s)',left,454,17,muted);write('0',left-20,top+height/2+5,14,muted);
    write('+'+(extent/1000).toFixed(2),left-20,top-9,13,muted);write('−'+(extent/1000).toFixed(2),left-20,top+height+4,13,muted);
    artifact.corners.forEach((corner,i)=>write(corner.label,left+corner.distance_m/last*width-6,top+height+21+(i%2)*13,10,muted));
    write('0 m',left,top+height+53,14,muted);write(Math.round(last)+' m',left+width-60,top+height+53,14,muted);
    write('LOCAL GAIN / CORNER SPEED',52,785,16,muted,650);
    artifact.analysis.categories.forEach((category,i)=>{
      const net=orient(category.net_gain_ms,swapped);
      write(category.speed_class.toUpperCase(),52+i*330,827,16,muted,650);
      write(net===null?'Insufficient':signed(net,2)+' s',52+i*330,864,28,net===null||Math.abs(net)<5?muted:net>=0?colors.a:colors.b,650);
      write(category.independent_units+' supported · '+Math.round(category.distance_coverage*100)+'% coverage',52+i*330,892,14,muted);
      const assessment=category.assessment==='a_advantage'?artifact.lap_a.driver_code+' advantage':category.assessment==='b_advantage'?artifact.lap_b.driver_code+' advantage':category.assessment;
      write(assessment,52+i*330,915,14,muted);
    });
    artifact.observations.forEach((observation,i)=>wrap((i+1)+'. '+observation.text,52,955+i*77,970,19,26,2));
    if(artifact.observations.length<3) wrap(artifact.insufficient_evidence_reason??'Fewer than three supported findings.',52,955+artifact.observations.length*77,970,18,25,2,muted);
  } else {
    write('Sector',60,483,21,muted);write(a.driver_code,360,483,21,colors.a);write(b.driver_code,595,483,21,colors.b);write('B − A',830,483,21,muted);
    a.sector_times_ms.forEach((value,i)=>{const y=546+i*70;write('S'+(i+1),60,y,25);write((value/1000).toFixed(3)+' s',360,y,25,colors.a);write((b.sector_times_ms[i]/1000).toFixed(3)+' s',595,y,25,colors.b);write(signed(b.sector_times_ms[i]-value)+' s',830,y,25);});
    wrap(artifact.fallback_reason,52,814,970,22,32,4,muted);
  }
  const warnings=[...artifact.pairing.warnings,...artifact.quality.warnings.filter(value=>!['Approximate local timing','Timing clocks/eligibility','Start/finish values'].some(prefix=>value.startsWith(prefix)))];
  wrap('Quality: '+artifact.quality.status+'. '+warnings.join(' '),52,1190,970,16,22,3,muted);
  wrap(sourceName(artifact)+' · Local gains are estimates · Brake is on/off',52,1270,970,15,21,2,muted);
  write(artifact.comparison_id+' · '+artifact.provenance.methodology_version,52,1323,13,muted);
  return new Promise<Blob>((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error('Unable to create the image.')),'image/png'));
}

export function ComparisonExport({result}:{result:PairResponse}) {
  const {theme}=useTheme();const [busy,setBusy]=useState(false),[status,setStatus]=useState(''),[showLink,setShowLink]=useState(false);
  const link=comparisonLink(result,window.location.origin),base='LapDNA-'+result.artifact.comparison_id;
  async function png() {setBusy(true);setStatus('');try{download(await renderCard(result,theme),base+'.png');setStatus('Analysis card downloaded.');}catch(error){setStatus(error instanceof Error?error.message:'Export failed.');}finally{setBusy(false);}}
  async function share() {try{await navigator.clipboard.writeText(link);setStatus('Comparison link copied.');}catch{setShowLink(true);setStatus('Copy the comparison link below.');}}
  return <section className="comparison-export" aria-label="Export comparison"><div className="export-actions">
    <button type="button" className="secondary-button" onClick={png} disabled={busy}>{busy?'Preparing card…':'Download analysis card'}</button>
    <button type="button" className="secondary-button" onClick={()=>download(new Blob([JSON.stringify({artifact:result.artifact,view:{swapped:result.swapped,theme},share_url:link},null,2)],{type:'application/json'}),base+'.json')}>Download evidence JSON</button>
    <button type="button" className="secondary-button" onClick={share}>Copy comparison link</button></div>
    {status&&<p role="status">{status}</p>}{showLink&&<label>Comparison link<input readOnly value={link} onFocus={e=>e.currentTarget.select()}/></label>}
  </section>;
}
