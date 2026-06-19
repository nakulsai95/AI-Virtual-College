/* AULA product — Onboarding flow: Intake -> Hiring -> Review */
const { useState: useStateO, useEffect: useEffectO, useRef: useRefO } = React;

function roleLabel(roleKey, terms){
  return ({ principal:terms.principal, provost:'Provost', professor:terms.professor,
    examiner:'Examiner', registrar:'Registrar', guide:terms.guide, counselor:'Counselor' })[roleKey] || roleKey;
}

function Onboarding({ terms, mark, onEnroll, themeSwitch }){
  const D = window.AULA_DATA;
  const [phase, setPhase] = useStateO('intake');
  const [goal, setGoal] = useStateO('');
  const [level, setLevel] = useStateO('intermediate');

  // Kick off the real Principal (backend) when the learner hits "Build".
  // The Hiring screen shows the TRUE order of work: the Principal scrapes
  // university curricula, studies them, designs the plan — and only THEN do
  // hiring cards appear, with the faculty the model actually chose.
  // window.AULA_ONBOARD signals the Hiring screen that the real plan landed.
  function build(){
    const g = goal.trim() || 'Become job-ready in backend Python';
    window.AULA_ONBOARD = null;
    setPhase('hiring');
    if(window.AULA_API){
      window.AULA_API.onboard(g, level)
        .then(out=>{
          window.applyCurriculum && window.applyCurriculum(out.curriculum);
          window.AULA_ONBOARD = out;
        })
        .catch(err=>{
          if(err instanceof TypeError){ window.AULA_ONBOARD = { offline:true }; return; }
          alert('The Principal hit a problem:\n\n' + (err.message || err) +
                '\n\nCheck your key/credits in Connections, then try again.');
          setPhase('intake');
        });
    } else {
      window.AULA_ONBOARD = { offline:true };
    }
  }

  const stepNum = phase==='intake'?1:phase==='hiring'?2:3;
  return (
    <div className="onb">
      <div className="onb-top">
        <div className="onb-brand"><span className="sb-mark">{mark}</span>{terms.college}</div>
        <div className="row" style={{gap:18}}>
          <div className="onb-step">step <b>{stepNum}</b> / 3 · {phase}</div>
          {themeSwitch}
        </div>
      </div>
      {phase==='intake' && <Intake {...{goal,setGoal,level,setLevel,terms,onBuild:build}} />}
      {phase==='hiring' && <Hiring {...{terms,goal,onDone:()=>setPhase('review')}} />}
      {phase==='review' && <Review {...{terms,goal,level,onEnroll,onRevise:()=>{
        if(window.AULA_API) window.AULA_API.resetCollege().catch(()=>{});
        setPhase('intake');
      }}} />}
    </div>
  );
}

function Intake({ goal, setGoal, level, setLevel, terms, onBuild }){
  const examples = ['Become job-ready in backend Python','Learn quantum computing basics','Master React & TypeScript','Understand machine learning end to end'];
  const g = goal.trim() || 'Become job-ready in backend Python';
  return (
    <div className="intake">
      <div className="eyebrow">Enrolment · tell the {terms.principal.toLowerCase()} your goal</div>
      <h1>What do you want to <span className="g">learn?</span></h1>
      <p className="lede">Describe it in your words. The {terms.principal} will hire a faculty, design your {terms.semester.toLowerCase()}, and run the whole {terms.college.replace(/^The /,'').toLowerCase()} — you review before you enrol.</p>
      <div className="intake-box">
        <textarea rows={2} value={goal} onChange={e=>setGoal(e.target.value)} placeholder="e.g. Become job-ready in backend Python — I know basic programming but no web frameworks yet." />
        <div className="intake-row">
          <div className="seg">
            {['beginner','intermediate','advanced'].map(l=>
              <button key={l} className={level===l?'on':''} onClick={()=>setLevel(l)}>{l}</button>)}
          </div>
          <div className="grow" />
          <button className="btn primary" onClick={onBuild}>Build my {terms.college.replace(/^The /,'')} →</button>
        </div>
      </div>
      <div className="examples">
        {examples.map(ex=><button key={ex} className="ex-chip" onClick={()=>setGoal(ex)}>{ex}</button>)}
      </div>
    </div>
  );
}

// What the Principal is actually doing before any hiring decision is made.
const PREP_STAGES = [
  'Reading your goal & constraints…',
  'Scraping university syllabi — Stanford, MIT OCW, course pages…',
  'Studying the material: what real programs cover, and in what order…',
  'Designing your semester — subjects, modules, sandboxes per topic…',
  'Validating the plan against the syllabi — filling gaps…',
  'Making hiring calls — one professor per subject…',
];

function Hiring({ terms, goal, onDone }){
  const D = window.AULA_DATA;
  const [ready, setReady] = useStateO(!!window.AULA_ONBOARD);  // real plan landed
  const [prep, setPrep] = useStateO(1);   // prep stages revealed while the model works
  const [n, setN] = useStateO(0);         // faculty revealed (only after ready)
  const seq = D.HIRING;                   // real faculty once applyCurriculum ran
  const done = ready && n >= seq.length;

  // Wait for the Principal's real curriculum — no hiring before the decision.
  // Also ask the backend which stage it's truly in (research vs design).
  useEffectO(()=>{
    if(ready) return;
    const t = setInterval(()=>{ if(window.AULA_ONBOARD) setReady(true); }, 350);
    const s = setInterval(()=>{
      if(window.AULA_ONBOARD || !window.AULA_API) return;
      window.AULA_API.onboardStatus().then(r=>{
        if(r.stage==='research') setPrep(p=>Math.max(p,2));
        if(r.stage==='design') setPrep(p=>Math.max(p,4));
        if(r.stage==='validate') setPrep(p=>Math.max(p,5));
      }).catch(()=>{});
    }, 1200);
    return ()=>{ clearInterval(t); clearInterval(s); };
  },[ready]);

  // Research/design console lines advance while we wait (and stop when real).
  useEffectO(()=>{
    if(ready || prep >= PREP_STAGES.length) return;
    const t = setTimeout(()=>setPrep(p=>p+1), 2400);
    return ()=>clearTimeout(t);
  },[prep, ready]);

  // Hiring reveals — strictly after the model made its hiring calls.
  useEffectO(()=>{
    if(!ready || done) return;
    const t = setTimeout(()=>setN(x=>x+1), n===0?600:680);
    return ()=>clearTimeout(t);
  },[n, ready, done]);

  const progTotal = PREP_STAGES.length + (seq ? seq.length : 8);
  const progVal = ready ? PREP_STAGES.length + n : prep;

  return (
    <div className="hiring">
      <div className="hiring-head">
        <div className="eyebrow" style={{justifyContent:'center',marginBottom:12}}>Building · watch it happen</div>
        <h2>{ready ? 'Hiring your faculty' : 'Designing your '+terms.college.replace(/^The /,'')}</h2>
        <p>For “{goal.trim()||'Become job-ready in backend Python'}”</p>
      </div>
      <div className="hiring-grid">
        <div className="console">
          {PREP_STAGES.slice(0, ready ? PREP_STAGES.length : prep).map((s,i)=>
            <div key={'p'+i} className={"cl"+((ready||i<prep-1)?' ok':'')}>
              <span className="tk">{(ready||i<prep-1)?'✓':'›'}</span>
              <span>{i===0 ? <span><b>{terms.principal}</b> · {s}</span> : s}</span>
            </div>)}
          {ready && <div className="cl ok"><span className="tk">✓ plan</span><span>Curriculum designed — making the hires.</span></div>}
          {ready && seq.slice(0,n).map((a,i)=>
            <div key={'h'+i} className="cl ok"><span className="tk">✓ hire</span>
              <span>Hired <b>{a.name}</b> · {roleLabel(a.roleKey,terms)} — {a.line}</span></div>)}
          {!done && <div className="cl"><span className="tk">…</span>{ready?'hiring':'the '+terms.principal+' is working — scraping & deciding'}</div>}
        </div>
        <div className="roster">
          {!ready && (
            <div className="hire-card" style={{opacity:.65}}>
              <Avatar name="?" hue="var(--accent)" size={38} sq glyph="…" />
              <div className="hc-meta"><b>No hires yet</b><span>faculty appears once the {terms.principal.toLowerCase()} decides</span></div>
            </div>
          )}
          {ready && seq.slice(0,n).map((a,i)=>{
            const fac = D.FACULTY.find(f=>f.id===a.id) || {};
            return (
              <div key={a.id} className="hire-card" style={{animationDelay:'0s'}}>
                <Avatar name={a.name} hue={fac.hue||'var(--accent)'} size={38} sq />
                <div className="hc-meta"><b>{a.name}</b><span>{roleLabel(a.roleKey,terms)}{fac.subject?' · '+fac.subject:''}</span></div>
                <span className="hc-badge">hired</span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="hiring-prog">
        <Bar value={progVal} max={progTotal} />
      </div>
      <div className="hiring-cta">
        {done
          ? <button className="btn primary" onClick={onDone}>Review the plan →</button>
          : <span className="mono faint" style={{fontSize:13}}>
              {ready ? n+' / '+seq.length+' hired…' : 'researching & designing — hires come after the decision'}
            </span>}
      </div>
    </div>
  );
}

function Review({ terms, goal, level, onEnroll, onRevise }){
  const D = window.AULA_DATA;
  const [cap, setCap] = useStateO(null);
  useEffectO(()=>{ if(window.AULA_API) window.AULA_API.usage().then(u=>setCap(u.cap)).catch(()=>{}); },[]);
  const totalBudget = D.FACULTY.reduce((a,f)=>a+(f.budget?f.budget.cap:0),0);
  return (
    <div className="review">
      <div className="review-head">
        <div>
          <div className="eyebrow" style={{marginBottom:10}}>Proposed {terms.semester.toLowerCase()} · review before you enrol</div>
          <h2>Your {terms.college.replace(/^The /,'')}, staffed.</h2>
          <p className="muted" style={{marginTop:8,maxWidth:'52ch'}}>For “{goal.trim()||'Become job-ready in backend Python'}” · {level}.</p>
        </div>
        <div className="stat">
          <div className="s"><b>{D.STUDENT.weeks}</b><span>WEEKS</span></div>
          <div className="s"><b>{D.SUBJECTS.length}</b><span>SUBJECTS</span></div>
          <div className="s"><b>{D.FACULTY.length}</b><span>FACULTY</span></div>
        </div>
      </div>

      {D.SUBJECTS.map(s=>(
        <div key={s.id} className="subj-card">
          <div className="sc-top">
            <Avatar name={s.profName} hue={s.hue} size={40} sq />
            <div style={{flex:1}}>
              <div className="scn">{s.title}</div>
              <div className="scp">{terms.professor} {s.profName} · {s.modules.length} {terms.module.toLowerCase()}s</div>
            </div>
            <span className="badge accent">{s.modules.length} units</span>
          </div>
          <div className="mod-list">
            {s.modules.map((m,i)=>
              <div key={m.id} className="mod-pill"><span className="mp-n">{i+1}</span>{m.title}</div>)}
          </div>
        </div>
      ))}

      <div className="card" style={{marginTop:6}}>
        <div className="row" style={{justifyContent:'space-between'}}>
          <div><div className="eyebrow" style={{marginBottom:4}}>Support staff</div><div className="muted" style={{fontSize:13}}>Hired alongside your professors</div></div>
          <span className="badge gold mono">{cap!=null ? 'credits $'+cap.toFixed(2)+' cap' : 'budget $'+totalBudget+'/mo cap'}</span>
        </div>
        <div className="faculty-strip">
          {D.FACULTY.filter(f=>f.role!=='professor').map(f=>
            <div key={f.id} className="fac-mini"><Avatar name={f.name} hue={f.hue} size={26}/>{f.name}<span className="fm-r">{roleLabel(f.role,terms)}</span></div>)}
        </div>
      </div>

      <div className="review-foot">
        <button className="btn ghost" onClick={onRevise}>Request changes</button>
        <button className="btn primary" onClick={onEnroll}>Enrol — start learning →</button>
      </div>
    </div>
  );
}

/* ---------- Sign in (local Gmail profile — demo account, no setup) ---------- */
function SignIn({ terms, mark, onSignedIn, themeSwitch }){
  const [step,setStep] = useStateO('start');   // start | form
  const [name,setName] = useStateO('');
  const [email,setEmail] = useStateO('');
  const [busy,setBusy] = useStateO(false);
  const valid = /\S+@\S+\.\S+/.test(email.trim());
  function finish(){
    if(!valid || busy) return;
    setBusy(true);
    const account = { name: name.trim() || email.split('@')[0], email: email.trim() };
    localStorage.setItem('aula_account', JSON.stringify(account));
    const done = ()=>{ onSignedIn(account); };
    if(window.AULA_API) window.AULA_API.setProfile(account.name, account.email).then(done).catch(done);
    else done();
  }
  return (
    <div className="onb">
      <div className="onb-top">
        <div className="onb-brand"><span className="sb-mark">{mark}</span>{terms.college}</div>
        {themeSwitch}
      </div>
      <div className="intake" style={{maxWidth:460,textAlign:'center'}}>
        <div className="sb-mark" style={{width:64,height:64,fontSize:30,margin:'0 auto 22px',display:'flex',alignItems:'center',justifyContent:'center'}}>{mark}</div>
        <h1 style={{fontSize:30}}>Welcome to <span className="g">{terms.college.replace(/^The /,'')}</span></h1>
        <p className="lede" style={{margin:'10px auto 26px'}}>Your AI-run college. Sign in to enrol — your faculty, curriculum and progress are saved to your account.</p>

        {step==='start' ? (
          <button className="btn" style={{width:'100%',justifyContent:'center',gap:12,background:'#fff',color:'#222',fontWeight:600,padding:'13px',border:'1px solid #dadce0'}} onClick={()=>setStep('form')}>
            <span style={{fontFamily:'arial',fontWeight:700,fontSize:18}}><span style={{color:'#4285F4'}}>G</span><span style={{color:'#EA4335'}}>o</span><span style={{color:'#FBBC05'}}>o</span><span style={{color:'#4285F4'}}>g</span><span style={{color:'#34A853'}}>l</span><span style={{color:'#EA4335'}}>e</span></span>
            Continue with Google
          </button>
        ) : (
          <div className="intake-box" style={{textAlign:'left'}}>
            <label className="conn-label">Your name</label>
            <input className="conn-input" value={name} onChange={e=>setName(e.target.value)} placeholder="Alex Rivera" />
            <label className="conn-label" style={{marginTop:12}}>Gmail address</label>
            <input className="conn-input mono" value={email} onChange={e=>setEmail(e.target.value)} onKeyDown={e=>e.key==='Enter'&&finish()} placeholder="you@gmail.com" />
            <button className="btn primary" style={{width:'100%',justifyContent:'center',marginTop:16}} onClick={finish} disabled={!valid||busy}>{busy?'Signing in…':'Sign in →'}</button>
            <p className="faint mono" style={{fontSize:11,marginTop:12,textAlign:'center'}}>Demo profile — stored locally on your machine, no password.</p>
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { Onboarding, SignIn });
