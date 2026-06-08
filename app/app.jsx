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

function AccountMenu({ account, onSignIn, onSignOut }){
  const { useState } = React;
  const [open,setOpen] = useState(false);
  if(!window.AULA_API) return null;
  const authed = account && !account.guest;
  if(!authed) return <button className="tb-btn" onClick={onSignIn}>Sign in</button>;
  return (
    <div style={{position:'relative'}}>
      <button className="tb-btn" onClick={()=>setOpen(o=>!o)}><Avatar name={account.name} size={20} hue="var(--accent)"/> {account.name} <span className="faint" style={{fontSize:11}}>▾</span></button>
      {open && (
        <React.Fragment>
          <div style={{position:'fixed',inset:0,zIndex:70}} onClick={()=>setOpen(false)}/>
          <div className="theme-pop" style={{minWidth:190}}>
            <div className="tp-sub" style={{marginBottom:10}}>{account.email}</div>
            <button className="btn ghost" style={{width:'100%',justifyContent:'center'}} onClick={()=>{setOpen(false);onSignOut();}}>Sign out</button>
          </div>
        </React.Fragment>
      )}
    </div>
  );
}

function AuthModal({ onClose, onAuthed }){
  const { useState } = React;
  const [mode,setMode] = useState('login');
  const [email,setEmail] = useState('');
  const [password,setPassword] = useState('');
  const [name,setName] = useState('');
  const [busy,setBusy] = useState(false);
  const [err,setErr] = useState('');
  function submit(){
    if(!email||!password) return;
    setBusy(true); setErr('');
    const p = mode==='login' ? window.AULA_API.login(email,password) : window.AULA_API.register(email,password,name);
    p.then(u=>{ setBusy(false); onAuthed({id:u.id,email:u.email,name:u.name,guest:false}); })
     .catch(e=>{ setBusy(false); setErr(String(e.message||e)); });
  }
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={e=>e.stopPropagation()}>
        <h3 style={{fontSize:18,marginBottom:14}}>Welcome to AULA</h3>
        <div className="seg" style={{marginBottom:16}}>
          <button className={mode==='login'?'on':''} onClick={()=>setMode('login')}>Sign in</button>
          <button className={mode==='register'?'on':''} onClick={()=>setMode('register')}>Create account</button>
        </div>
        {mode==='register' && <input className="conn-input" style={{marginBottom:10}} placeholder="Name" value={name} onChange={e=>setName(e.target.value)} />}
        <input className="conn-input" style={{marginBottom:10}} placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="conn-input" type="password" style={{marginBottom:14}} placeholder="Password (min 6 chars)" value={password} onChange={e=>setPassword(e.target.value)} onKeyDown={e=>e.key==='Enter'&&submit()} />
        {err && <p className="muted" style={{fontSize:12.5,color:'var(--coral)',marginBottom:10}}>{err}</p>}
        <button className="btn primary" style={{width:'100%',justifyContent:'center'}} onClick={submit} disabled={busy||!email||!password}>{busy?'…':(mode==='login'?'Sign in':'Create account')}</button>
        <button className="btn ghost" style={{width:'100%',justifyContent:'center',marginTop:10}} onClick={onClose}>Continue as guest</button>
        <p className="faint mono" style={{fontSize:10.5,marginTop:14,textAlign:'center'}}>Your progress saves to your account on your own backend.</p>
      </div>
    </div>
  );
}

function App(){
  const [themeKey, setThemeKey] = useStateA(localStorage.getItem('aula_app_theme') || 'ninja');
  const [enrolled, setEnrolled] = useStateA(localStorage.getItem('aula_enrolled')==='1');
  const [active, setActive] = useStateA('home');
  const [lessonOpen, setLessonOpen] = useStateA(null);
  const [account, setAccount] = useStateA(null);
  const [authOpen, setAuthOpen] = useStateA(false);
  const [, setTick] = useStateA(0);
  const bump = ()=>setTick(t=>t+1);

  useEffectA(()=>{ window.applyThemeVars(themeKey); localStorage.setItem('aula_app_theme',themeKey); },[themeKey]);

  // Restore a returning student from the backend: account + enrollment + progress.
  function loadSession(){
    if(!window.AULA_API) return;
    window.AULA_API.enrollment().then(r=>{
      if(r && r.enrolled){
        window.applyCurriculum(r.curriculum);
        window.AULA_API.progress()
          .then(p=>{ if(p&&p.student) window.applyStudent(p.student); })
          .finally(()=>{ setEnrolled(true); localStorage.setItem('aula_enrolled','1'); bump(); });
      } else { setEnrolled(false); localStorage.removeItem('aula_enrolled'); bump(); }
    }).catch(()=>{});
  }
  useEffectA(()=>{
    if(!window.AULA_API) return;
    window.AULA_API.me().then(setAccount).catch(()=>{});
    loadSession();
  },[]);

  const terms = window.AULA_THEMES[themeKey].terms;
  const mark = window.AULA_THEMES[themeKey].mark;
  const setTheme = (k)=>setThemeKey(k);
  const themeSwitch = <ThemeSwitch themeKey={themeKey} setTheme={setTheme} />;

  function onAuthed(acc){ setAccount(acc); setAuthOpen(false); loadSession(); }
  function signOut(){
    const done = ()=>{ setAccount(null); setEnrolled(false); localStorage.removeItem('aula_enrolled'); setActive('home'); bump(); };
    if(window.AULA_API) window.AULA_API.logout().finally(done); else done();
  }
  const accountMenu = <AccountMenu account={account} onSignIn={()=>setAuthOpen(true)} onSignOut={signOut} />;

  function enrol(){
    setEnrolled(true); localStorage.setItem('aula_enrolled','1'); setActive('home');
    if(window.AULA_API) window.AULA_API.progress().then(p=>{ if(p&&p.student){ window.applyStudent(p.student); bump(); } }).catch(()=>{});
  }
  function nav(key, payload){ if(key==='lesson'){ setLessonOpen(payload||true); } setActive(key); }

  if(!enrolled){
    return (
      <React.Fragment>
        <Onboarding terms={terms} mark={mark} onEnroll={enrol} themeSwitch={themeSwitch} accountMenu={accountMenu} />
        {authOpen && <AuthModal onClose={()=>setAuthOpen(false)} onAuthed={onAuthed} />}
      </React.Fragment>
    );
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
                const unread = it.key==='channel' ? 2 : 0;
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
          <Avatar name={(account&&account.name)||window.AULA_DATA.STUDENT.name} hue="var(--accent)" size={34} />
          <div className="who"><b>{(account&&account.name)||window.AULA_DATA.STUDENT.name}</b><span>{account&&!account.guest?account.email:window.AULA_DATA.STUDENT.handle}</span></div>
        </div>
      </aside>

      <div className="main">
        <div className="topbar">
          <div className="tb-title"><span className="crumb">{current.group}</span>{navLabel(current,terms)}</div>
          <div className="tb-spacer" />
          {accountMenu}
          {themeSwitch}
        </div>
        <div className="screen">
          {Comp ? <Comp {...screenProps} /> : <Placeholder label={navLabel(current,terms)} />}
        </div>
      </div>
      {authOpen && <AuthModal onClose={()=>setAuthOpen(false)} onAuthed={onAuthed} />}
    </div>
  );
}

function navLabel(it, terms){
  const map = { board:'My Board', guide:terms.guide, teacherboard:terms.professor+' Board', exams:terms.exam+'s & Results', command:terms.principal+'’s Center', grades:'Faculty Grades', curriculum:terms.semester+' Plan' };
  return map[it.key] || it.label;
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
