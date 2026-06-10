/* AULA product — app shell: nav, topbar, theme switch, routing */
const { useState: useStateA, useEffect: useEffectA } = React;

const NAV = [
  { group:'Learn', items:[
    { key:'home', label:'Dashboard', icon:'home' },
    { key:'curriculum', label:'Curriculum', icon:'book' },
    { key:'board', label:'My Board', icon:'board' },
    { key:'guide', label:'Personal Guide', icon:'guide' },
    { key:'channel', label:'Channel', icon:'chat' },
    { key:'library', label:'Library', icon:'library' },
    { key:'progress', label:'My Progress', icon:'spark' },
  ]},
  { group:'Assess', items:[
    { key:'exams', label:'Exams & Results', icon:'exam' },
  ]},
  { group:'Faculty & admin', items:[
    { key:'grades', label:'Faculty Grades', icon:'grades' },
    { key:'teacherboard', label:'Teacher Board', icon:'faculty' },
    { key:'command', label:'Command Center', icon:'command' },
    { key:'connections', label:'Connections', icon:'conn' },
  ]},
];

function ThemeSwitch({ themeKey, setTheme }){
  const [open,setOpen] = useStateA(false);
  const T = window.AULA_THEMES, ORDER = window.AULA_THEME_ORDER;
  return (
    <div style={{position:'relative'}}>
      <button className="tb-btn" onClick={()=>setOpen(o=>!o)}>
        <span className="sw" /> {T[themeKey].name} <span className="faint" style={{fontSize:11}}>▾</span>
      </button>
      {open && (
        <React.Fragment>
          <div style={{position:'fixed',inset:0,zIndex:70}} onClick={()=>setOpen(false)} />
          <div className="theme-pop">
            <h4>College theme</h4>
            <div className="tp-sub">the whole {T[themeKey].terms.college.replace(/^The /,'').toLowerCase()} reskins instantly</div>
            <div className="tp-grid">
              {ORDER.map(k=>(
                <button key={k} className={"tp-opt"+(k===themeKey?' on':'')} onClick={()=>{setTheme(k);setOpen(false);}}>
                  <span className="tg" style={{background:`linear-gradient(150deg,${T[k].accent},${T[k].accent2})`,fontFamily:'var(--font-jp)'}}>{T[k].mark}</span>
                  <span><span className="tn">{T[k].name}</span><br/><span className="tv">{T[k].vibe}</span></span>
                </button>
              ))}
            </div>
          </div>
        </React.Fragment>
      )}
    </div>
  );
}

function Placeholder({ label }){
  return (
    <div className="screen-pad">
      <div className="card" style={{textAlign:'center',padding:'60px 20px'}}>
        <div className="eyebrow" style={{justifyContent:'center',marginBottom:12}}>screen</div>
        <h2 style={{fontSize:24}}>{label}</h2>
        <p className="muted" style={{marginTop:8}}>Coming up in this prototype.</p>
      </div>
    </div>
  );
}

function App(){
  const [themeKey, setThemeKey] = useStateA(localStorage.getItem('aula_app_theme') || 'ninja');
  const [enrolled, setEnrolled] = useStateA(localStorage.getItem('aula_enrolled')==='1');
  const [active, setActive] = useStateA('home');
  const [lessonOpen, setLessonOpen] = useStateA(null);
  const [,setTick] = useStateA(0);

  useEffectA(()=>{ window.applyThemeVars(themeKey); localStorage.setItem('aula_app_theme',themeKey); },[themeKey]);

  // Re-render whenever the live backend state lands (hydration / after actions).
  // Enrolment follows the flag both ways — the backend is the source of truth.
  useEffectA(()=>{
    const onData = ()=>{ setTick(t=>t+1); setEnrolled(localStorage.getItem('aula_enrolled')==='1'); };
    window.addEventListener('aula:data', onData);
    return ()=>window.removeEventListener('aula:data', onData);
  },[]);

  const terms = window.AULA_THEMES[themeKey].terms;
  const mark = window.AULA_THEMES[themeKey].mark;
  const setTheme = (k)=>setThemeKey(k);
  const themeSwitch = <ThemeSwitch themeKey={themeKey} setTheme={setTheme} />;

  function enrol(){
    setEnrolled(true); localStorage.setItem('aula_enrolled','1'); setActive('home');
    if(window.AULA_API) window.AULA_API.hydrate();  // pull the persisted college
  }
  function nav(key, payload){ if(key==='lesson'){ setLessonOpen(payload||true); } setActive(key); }

  if(!enrolled){
    return <Onboarding terms={terms} mark={mark} onEnroll={enrol} themeSwitch={themeSwitch} />;
  }

  const screenProps = { terms, themeKey, mark, nav, data:window.AULA_DATA, lessonOpen };
  const Comp = window['SCR_'+active];
  const allItems = NAV.flatMap(g=>g.items);
  const current = allItems.find(i=>i.key===active) || { label:'Lesson', group:'Learn' };

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sb-brand">
          <span className="sb-mark">{mark}</span>
          <div><div className="wm">{terms.college.replace(/^The /,'')}</div><div className="sub">AI College</div></div>
        </div>
        <div className="sb-scroll">
          {NAV.map(g=>(
            <div key={g.group}>
              <div className="sb-group">{g.group}</div>
              {g.items.map(it=>{
                const unread = it.key==='channel'
                  ? (window.AULA_DATA.CHANNELS||[]).reduce((a,c)=>a+(c.unread||0),0) : 0;
                return (
                  <button key={it.key} className={"nav-item"+(active===it.key?' active':'')} onClick={()=>nav(it.key)}>
                    <span className="ico"><Icon name={it.icon} /></span>
                    <span className="lbl">{navLabel(it,terms)}</span>
                    {unread>0 && <span className="badge-n">{unread}</span>}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
        <div className="sb-foot">
          <Avatar name={window.AULA_DATA.STUDENT.name} hue="var(--accent)" size={34} />
          <div className="who"><b>{window.AULA_DATA.STUDENT.name}</b><span>{window.AULA_DATA.STUDENT.handle}</span></div>
        </div>
      </aside>

      <div className="main">
        <div className="topbar">
          <div className="tb-title"><span className="crumb">{current.group}</span>{navLabel(current,terms)}</div>
          <div className="tb-spacer" />
          {themeSwitch}
        </div>
        <div className="screen">
          {Comp ? <Comp {...screenProps} /> : <Placeholder label={navLabel(current,terms)} />}
        </div>
      </div>
    </div>
  );
}

function navLabel(it, terms){
  const map = { board:'My Board', guide:terms.guide, teacherboard:terms.professor+' Board', exams:terms.exam+'s & Results', command:terms.principal+'’s Center', grades:'Faculty Grades', curriculum:terms.semester+' Plan' };
  return map[it.key] || it.label;
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
