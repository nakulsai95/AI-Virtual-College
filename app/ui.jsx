/* AULA product — shared UI primitives (exported to window) */
const { useState, useEffect, useRef } = React;

function Avatar({ name='?', hue='#6e8efb', size=36, sq=false, glyph=null }){
  const st = { width:size, height:size, fontSize:size*0.42,
    background:`linear-gradient(150deg, ${hue}, ${shade(hue,-28)})` };
  return <div className={"avatar"+(sq?" sq":"")} style={st}>{glyph || (name[0]||'?').toUpperCase()}</div>;
}
function shade(hex,p){ const h=hex.replace('#',''); let r=parseInt(h.substr(0,2),16),g=parseInt(h.substr(2,2),16),b=parseInt(h.substr(4,2),16);
  r=Math.max(0,Math.min(255,r+p));g=Math.max(0,Math.min(255,g+p));b=Math.max(0,Math.min(255,b+p));
  return `#${[r,g,b].map(v=>v.toString(16).padStart(2,'0')).join('')}`; }

function Bar({ value, max=100 }){
  return <div className="bar"><i style={{ width: Math.max(0,Math.min(100, value/max*100))+'%' }} /></div>;
}

function Spark({ data=[], hue='var(--accent)', w=120, h=34 }){
  if(!data.length) return null;
  const min=Math.min(...data), max=Math.max(...data), rng=(max-min)||1;
  const pts=data.map((v,i)=>`${(i/(data.length-1))*w},${h - ((v-min)/rng)*(h-6) - 3}`).join(' ');
  const last=data[data.length-1], lx=w, ly=h-((last-min)/rng)*(h-6)-3;
  return (
    <svg width={w} height={h} style={{display:'block'}}>
      <polyline points={pts} fill="none" stroke={hue} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lx} cy={ly} r="3" fill={hue} />
    </svg>
  );
}

const ICONS = {
  home:'M3 11.5 12 4l9 7.5M5 10v10h14V10',
  board:'M4 5h4v14H4zM10 5h4v9h-4zM16 5h4v6h-4z',
  book:'M5 4h11a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2zM18 18H7',
  chat:'M5 5h14v10H9l-4 4z',
  guide:'M12 3v3M12 18v3M3 12h3M18 12h3M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  exam:'M9 4h6v2H9zM7 6h10v14H7zM10 12l1.5 1.5L15 10',
  faculty:'M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM16 11a3 3 0 1 0 0-6M3 19a5 5 0 0 1 10 0M14 19a5 5 0 0 1 7-4.6',
  grades:'M4 20V5M4 20h16M8 20v-6M12 20v-9M16 20v-4M20 20v-11',
  command:'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  conn:'M5 8h6M5 16h10M16 5v6M8 13v6M16 8a2 2 0 1 0 0-4M8 20a2 2 0 1 0 0-4M16 20a2 2 0 1 0 0-4',
  library:'M4 5h4v15H4zM10 5h4v15h-4zM16 6l4 1-3 13-4-1z',
  intake:'M12 4 2 9l10 5 10-5zM6 11v5c0 1 3 2.5 6 2.5s6-1.5 6-2.5v-5',
  spark:'M12 4l1.8 4.7L18 10l-4.2 1.3L12 16l-1.8-4.7L6 10l4.2-1.3zM18 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z'
};
function Icon({ name, size=18 }){
  const d = ICONS[name] || ICONS.home;
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{d.split('M').filter(Boolean).map((seg,i)=><path key={i} d={'M'+seg} />)}</svg>;
}

function RankRing({ tier=1, ranks=[], size=46 }){
  const pct=(tier+1)/4;
  const r=(size-6)/2, c=2*Math.PI*r;
  return (
    <div style={{position:'relative',width:size,height:size}}>
      <svg width={size} height={size} style={{transform:'rotate(-90deg)'}}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth="3"/>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c*(1-pct)}/>
      </svg>
      <div style={{position:'absolute',inset:0,display:'grid',placeItems:'center',fontFamily:'var(--font-d)',fontWeight:700,fontSize:size*0.32,color:'var(--accent)'}}>{tier+1}</div>
    </div>
  );
}

Object.assign(window, { Avatar, Bar, Spark, Icon, RankRing, shade });
