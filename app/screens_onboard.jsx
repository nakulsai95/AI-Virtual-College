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
  // The hiring animation plays while the curriculum is generated; if the
  // backend is unavailable, the app keeps its built-in demo plan.
  function build(){
    const g = goal.trim() || 'Become job-ready in backend Python';
    setPhase('hiring');
    if(window.AULA_API){
      window.AULA_API.onboard(g, level)
        .then(out=>{ window.AULA_ONBOARD = out; window.applyCurriculum && window.applyCurriculum(out.curriculum); })
        .catch(()=>{ /* offline / no backend — demo data stays */ });
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
      {phase==='review' && <Review {...{terms,goal,level,onEnroll,onBack:()=>setPhase('hiring')}} />}
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

function Hiring({ terms, goal, onDone }){
  const D = window.AULA_DATA;
  const seq = D.HIRING;
  const [n, setN] = useStateO(0);     // agents revealed
  const [lines, setLines] = useStateO([]);
  const done = n >= seq.length;

  useEffectO(()=>{
    if(done) return;
    const a = seq[n];
    const t = setTimeout(()=>{
      setLines(ls=>[...ls, n===0
        ? { tk:'init', text:<span><b>{a.name}</b> · {a.line}</span>, ok:false }
        : { tk:'hire', text:<span>Hired <b>{a.name}</b> · {roleLabel(a.roleKey,terms)} — {a.line}</span>, ok:true }]);
      setN(n+1);
    }, n===0?500:680);
    return ()=>clearTimeout(t);
  },[n,done]);

  return (
    <div className="hiring">
      <div className="hiring-head">
        <div className="eyebrow" style={{justifyContent:'center',marginBottom:12}}>Building · watch it happen</div>
        <h2>Hiring your faculty</h2>
        <p>For “{goal.trim()||'Become job-ready in backend Python'}”</p>
      </div>
      <div className="hiring-grid">
        <div className="console">
          {lines.map((l,i)=>
            <div key={i} className={"cl"+(l.ok?' ok':'')}><span className="tk">{l.ok?'✓ hire':'›'}</span>{l.text}</div>)}
          {!done && <div className="cl"><span className="tk">…</span>working</div>}
        </div>
        <div className="roster">
          {seq.slice(0,n).map((a,i)=>{
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
        <Bar value={n} max={seq.length} />
      </div>
      <div className="hiring-cta">
        {done
          ? <button className="btn primary" onClick={onDone}>Review the plan →</button>
          : <span className="mono faint" style={{fontSize:13}}>{n} / {seq.length} hired…</span>}
      </div>
    </div>
  );
}

function Review({ terms, goal, level, onEnroll, onBack }){
  const D = window.AULA_DATA;
  const [changed, setChanged] = useStateO(false);
  const totalBudget = D.FACULTY.reduce((a,f)=>a+f.budget.cap,0);
  return (
    <div className="review">
      <div className="review-head">
        <div>
          <div className="eyebrow" style={{marginBottom:10}}>Proposed {terms.semester.toLowerCase()} · review before you enrol</div>
          <h2>Your {terms.college.replace(/^The /,'')}, staffed.</h2>
          <p className="muted" style={{marginTop:8,maxWidth:'52ch'}}>For “{goal.trim()||'Become job-ready in backend Python'}” · {level}. {changed && <span style={{color:'var(--accent)'}}>Change requested — the {terms.principal} will revise.</span>}</p>
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
          <span className="badge gold mono">budget ${totalBudget}/mo cap</span>
        </div>
        <div className="faculty-strip">
          {D.FACULTY.filter(f=>f.role!=='professor').map(f=>
            <div key={f.id} className="fac-mini"><Avatar name={f.name} hue={f.hue} size={26}/>{f.name}<span className="fm-r">{roleLabel(f.role,terms)}</span></div>)}
        </div>
      </div>

      <div className="review-foot">
        <button className="btn ghost" onClick={()=>setChanged(true)}>Request changes</button>
        <button className="btn primary" onClick={onEnroll}>Enrol — start learning →</button>
      </div>
    </div>
  );
}

Object.assign(window, { Onboarding });
