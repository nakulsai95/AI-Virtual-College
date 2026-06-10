/* AULA product — assess/faculty/admin screens */
const { useState: useStateAd } = React;

/* ---------- Exams & Results ---------- */
function TakeExam({ terms, data }){
  const { useState } = React;
  const [exam,setExam] = useState(null);
  const [answers,setAnswers] = useState([]);
  const [busy,setBusy] = useState(false);
  const [result,setResult] = useState(null);
  const next = data.NEXT_EXAM;
  if(!window.AULA_LIVE || !next) return null;

  function generate(){
    setBusy(true);
    window.AULA_API.examGenerate(next.module_id)
      .then(r=>{ setExam(r.exam); setAnswers(r.exam.questions.map(()=>'')); })
      .catch(()=>{})
      .finally(()=>setBusy(false));
  }
  function submit(){
    setBusy(true);
    window.AULA_API.examSubmit(exam.id, answers)
      .then(r=>{ setResult(r); window.AULA_API.hydrate(); })
      .catch(()=>{})
      .finally(()=>setBusy(false));
  }

  if(result){
    return (
      <div className={"card "+(result.passed?'mint-note':'coral-note')} style={{marginBottom:18}}>
        <div className="row" style={{gap:10,flexWrap:'wrap',marginBottom:8}}>
          <b style={{fontFamily:'var(--font-d)',fontSize:15}}>{exam.title} — graded</b>
          <span className={"badge "+(result.passed?'mint':'coral')}>{result.score}% · {result.passed?'passed':'below bar'}</span>
          {result.reward && <span className={"badge "+(result.reward.delta>=0?'mint':'coral')+" mono"}>{result.reward.delta>=0?'+':''}{result.reward.delta} to {result.reward.professor && result.reward.professor.name}</span>}
          {result.methodology_changed && <span className="badge accent mono">Provost rewrote methodology</span>}
        </div>
        <p className="muted" style={{fontSize:13.5}}>{result.feedback}</p>
        <p className="faint mono" style={{fontSize:11,marginTop:8}}>{result.passed?'Module complete — the next one is unlocked.':'No penalty to you — your teacher took the hit. Revise and retake when ready.'}</p>
        <button className="btn ghost" style={{marginTop:12}} onClick={()=>{setResult(null);setExam(null);}}>Done</button>
      </div>
    );
  }
  if(exam){
    return (
      <div className="card accent-note" style={{marginBottom:18}}>
        <div className="row" style={{justifyContent:'space-between',marginBottom:12,flexWrap:'wrap',gap:8}}>
          <b style={{fontFamily:'var(--font-d)',fontSize:15}}>{exam.title} · {exam.type}</b>
          <span className="badge accent mono">bar {exam.bar} · graded blind</span>
        </div>
        {exam.questions.map((q,i)=>(
          <div key={i} style={{marginBottom:14}}>
            <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:14,marginBottom:6}}>{i+1}. {q.q}</div>
            <textarea className="probe-input" rows={2} value={answers[i]||''}
                      onChange={e=>setAnswers(a=>a.map((v,j)=>j===i?e.target.value:v))}
                      placeholder="Type your answer…" />
            {q.hint && <div className="faint mono" style={{fontSize:11,marginTop:4}}>Hint: {q.hint}</div>}
          </div>
        ))}
        <button className="btn primary" onClick={submit} disabled={busy || answers.every(a=>!a.trim())}>
          {busy?'The Examiner is grading…':'Submit '+terms.exam.toLowerCase()}
        </button>
      </div>
    );
  }
  return (
    <div className="card accent-note" style={{marginBottom:18}}>
      <div className="row" style={{gap:14,alignItems:'center',flexWrap:'wrap'}}>
        <div style={{flex:1,minWidth:220}}>
          <div className="eyebrow" style={{marginBottom:6}}>Next {terms.exam.toLowerCase()}</div>
          <b style={{fontFamily:'var(--font-d)',fontSize:15.5}}>{next.title}</b>
          <div className="faint mono" style={{fontSize:11,marginTop:4}}>{next.subject} · the Examiner writes it fresh for you</div>
        </div>
        <button className="btn primary" onClick={generate} disabled={busy}>{busy?'Writing questions…':'Take it now →'}</button>
      </div>
    </div>
  );
}

function ExamsScreen({ terms, data }){
  const passed = data.EXAMS.filter(e=>e.status==='passed').length;
  const total = data.EXAMS.filter(e=>e.status!=='upcoming').length;
  const lastFail = [...data.EXAMS].reverse().find(e=>e.status==='failed');
  const failProf = lastFail && (data.SUBJECTS.find(s=>s.title===lastFail.subject)||{}).profName;
  return (
    <div className="screen-pad">
      <div className="row" style={{justifyContent:'space-between',marginBottom:18,flexWrap:'wrap',gap:12}}>
        <div><h1 style={{fontSize:26}}>{terms.exam}s & Results</h1><p className="muted" style={{fontSize:14,marginTop:4}}>Graded blind by the Examiner · pass the bar to advance</p></div>
        <div className="row" style={{gap:18}}>
          <div style={{textAlign:'right'}}><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:22}}>{passed}/{total}</div><div className="faint mono" style={{fontSize:11}}>PASSED</div></div>
        </div>
      </div>
      <TakeExam terms={terms} data={data} />
      <div className="col" style={{gap:10}}>
        {data.EXAMS.map(e=>(
          <div key={e.id} className={"exam-row"+(e.status==='failed'?' failed':'')}>
            <div className="ex-when mono">{e.when}</div>
            <div style={{flex:1,minWidth:0}}>
              <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:14.5}}>{e.title}</div>
              <div className="faint mono" style={{fontSize:11,marginTop:2}}>{e.subject} · {e.type}</div>
            </div>
            {e.status==='upcoming' ? (
              <span className="badge mono">upcoming</span>
            ) : (
              <React.Fragment>
                <div className="ex-score">
                  <div className="row" style={{gap:8,justifyContent:'flex-end'}}>
                    <span style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:18,color:e.status==='passed'?'var(--mint)':'var(--coral)'}}>{e.score}%</span>
                    <span className="faint mono" style={{fontSize:11}}>bar {e.bar}</span>
                  </div>
                  <div className="ex-bar"><i style={{width:e.score+'%',background:e.status==='passed'?'var(--mint)':'var(--coral)'}}/><span className="ex-bar-mark" style={{left:e.bar+'%'}}/></div>
                </div>
                <span className={"badge "+(e.status==='passed'?'mint':'coral')}>{e.status==='passed'?'passed':'failed'}</span>
              </React.Fragment>
            )}
          </div>
        ))}
      </div>
      {lastFail && (
        <div className="card coral-note" style={{marginTop:18}}>
          <div className="row" style={{gap:12,alignItems:'flex-start'}}>
            <span className="dot" style={{background:'var(--coral)',marginTop:6}}/>
            <div>
              <b style={{fontFamily:'var(--font-d)',fontSize:14.5}}>{lastFail.title} — failed at {lastFail.score}% (bar {lastFail.bar})</b>
              <p className="muted" style={{fontSize:13.5,marginTop:6}}>You re-enrol this unit — <b style={{color:'var(--ink)'}}>no penalty to you</b>. {failProf?terms.professor+' '+failProf+' took the negative reward':'Your teacher took the negative reward'}; if their grade slipped, the Provost rewrote how they teach. Try again from "Take it now" above when ready.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Teacher Board + methodology ---------- */
function TeacherBoard({ terms, data }){
  const profs = data.FACULTY.filter(f=>f.role==='professor');
  const [pid,setPid] = useStateAd(profs[0].id);
  const prof = profs.find(p=>p.id===pid) || profs[0];
  const grade = data.GRADES.find(g=>g.id===prof.id) || data.GRADES[0]
    || { letter:'—', score:78, trend:'flat', history:[78], note:'No signals yet.', version:1 };
  const subjLessons = (data.LIBRARY||[]).filter(l=>l.subject===prof.subject).map(l=>l.title);
  const cols = [
    { k:'Prep', cards:['Plan next module','Refresh examples'] },
    { k:'Teaching', cards: subjLessons.length?subjLessons.slice(0,3):['First lesson on request'] },
    { k:'Assessing', cards:['Grade probes as they land'] },
    { k:'Reviewing', cards:['Watch '+(data.STUDENT?data.STUDENT.name:'the learner')+'’s mastery'] },
  ];
  // Live methodology straight from the backend (the Provost rewrites it for real).
  const gm = grade.methodology || {};
  const methodology = {
    v: grade.version || 1,
    pacing: gm.pacing || 'normal',
    seq: gm.sequence || 'concept → practice',
    modality: gm.modality || 'blog + diagrams',
    example: gm.examples || 'medium',
    probe: gm.probe || 'after-read',
    changed: (grade.version || 1) > 1,
  };
  return (
    <div className="screen-pad wide">
      <div className="row" style={{justifyContent:'space-between',marginBottom:16,flexWrap:'wrap',gap:12}}>
        <div className="row" style={{gap:12}}>
          <Avatar name={prof.name} hue={prof.hue} size={42} sq />
          <div><h1 style={{fontSize:22}}>{prof.name}</h1><div className="faint mono" style={{fontSize:12}}>{terms.professor} · {prof.subject}</div></div>
        </div>
        <div className="seg">
          {profs.map(p=><button key={p.id} className={pid===p.id?'on':''} onClick={()=>setPid(p.id)}>{p.name}</button>)}
        </div>
      </div>

      <div className="teacher-grid">
        <div className="kanban" style={{marginTop:0}}>
          {cols.map(c=>(
            <div key={c.k} className="kan-col">
              <div className="kan-head"><span>{c.k}</span><span className="kan-n">{c.cards.length}</span></div>
              <div className="kan-cards">
                {c.cards.map((t,i)=><div key={i} className="kan-card"><div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:13}}>{t}</div></div>)}
              </div>
            </div>
          ))}
        </div>
        <div className="col" style={{gap:14}}>
          <div className="card">
            <div className="row" style={{justifyContent:'space-between',marginBottom:6}}><h3>Grade</h3><span className={"badge "+(grade.score>=80?'mint':grade.score>=60?'gold':'coral')}>{grade.letter}</span></div>
            <div className="row" style={{gap:12,marginTop:6}}><Spark data={grade.history} hue={grade.score>=80?'var(--mint)':'var(--accent)'} w={150}/><span className="faint mono" style={{fontSize:11}}>{grade.trend}</span></div>
            <p className="muted" style={{fontSize:12.5,marginTop:10}}>{grade.note}</p>
          </div>
          <div className={"card"+(methodology.changed?' accent-note':'')}>
            <div className="row" style={{justifyContent:'space-between',marginBottom:12}}><h3>Teaching plan</h3><span className="badge accent mono">v{methodology.v}{methodology.changed?' · updated':''}</span></div>
            <div className="meth">
              <div className="meth-row"><span>pacing</span><b>{methodology.pacing}</b></div>
              <div className="meth-row"><span>sequence</span><b>{methodology.seq}</b></div>
              <div className="meth-row"><span>modality</span><b>{methodology.modality}</b></div>
              <div className="meth-row"><span>examples</span><b>{methodology.example}</b></div>
              <div className="meth-row"><span>probe timing</span><b>{methodology.probe}</b></div>
            </div>
            {methodology.changed && <p className="muted" style={{fontSize:12,marginTop:12}}>↳ {grade.note || 'Provost rewrote this after a struggle.'}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Faculty Grades ---------- */
function FacultyGrades({ terms, data }){
  const { useState, useEffect } = React;
  const [live,setLive] = useState(null);
  useEffect(()=>{ if(window.AULA_API && !window.AULA_LIVE) window.AULA_API.faculty().then(setLive).catch(()=>{}); },[]);
  const grades = window.AULA_LIVE ? data.GRADES
    : (live && live.professors && live.professors.length) ? live.professors : data.GRADES;
  return (
    <div className="screen-pad">
      <h1 style={{fontSize:26}}>Faculty Grades</h1>
      <p className="muted" style={{fontSize:14,marginTop:4,marginBottom:20}}>Teachers are graded on whether <b style={{color:'var(--ink)'}}>you</b> learn. Reward history, last 10 signals.</p>
      <div className="grid" style={{gridTemplateColumns:'1fr 1fr'}}>
        {grades.map(g=>{
          const hue = g.hue || (g.id==='prof-api'?'#f5a623':'#3b82f6');
          return (
            <div key={g.id} className="card grade-card">
              <div className="row" style={{gap:12,marginBottom:14}}>
                <Avatar name={g.name} hue={hue} size={40} sq />
                <div style={{flex:1}}><b style={{fontFamily:'var(--font-d)',fontSize:15}}>{g.name}</b><div className="faint mono" style={{fontSize:11}}>{terms.professor} · {g.subject}</div></div>
                <div style={{textAlign:'right'}}><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:26,color:g.score>=80?'var(--mint)':'var(--gold)'}}>{g.letter}</div><div className="faint mono" style={{fontSize:10}}>{g.score}/100</div></div>
              </div>
              <Spark data={g.history} hue={g.score>=80?'var(--mint)':'var(--accent)'} w={260} h={48}/>
              <div className="row" style={{justifyContent:'space-between',marginTop:12}}>
                <span className={"badge "+(g.trend==='up'?'mint':g.trend==='down'?'coral':'')}>{g.trend==='up'?'▲ rising':g.trend==='down'?'▼ recovering':'– steady'}</span>
                <span className="badge accent mono">methodology v{g.version}</span>
              </div>
              <p className="muted" style={{fontSize:12.5,marginTop:12}}>{g.note}</p>
            </div>
          );
        })}
      </div>
      <div className="card mint-note" style={{marginTop:16}}>
        <b style={{fontFamily:'var(--font-d)',fontSize:14}}>The asymmetry</b>
        <p className="muted" style={{fontSize:13,marginTop:6}}>Every penalty here came from <i>your</i> struggle — and landed only on the teacher. Your own score never goes down. That’s what keeps the faculty accountable to you.</p>
      </div>
    </div>
  );
}

/* ---------- Command Center ---------- */
function CommandCenter({ terms, data }){
  const { useState, useEffect } = React;
  const [live,setLive] = useState(null);
  useEffect(()=>{ if(window.AULA_API && !window.AULA_LIVE) window.AULA_API.faculty().then(setLive).catch(()=>{}); },[]);
  const feed = window.AULA_LIVE ? data.FEED
    : (live && live.feed && live.feed.length) ? live.feed : data.FEED;
  const gradeFor = (f)=>{
    if(live && live.professors){ const p=live.professors.find(p=>p.name===f.name||p.id===f.id); if(p) return {letter:p.letter,score:p.score}; }
    return f.grade;
  };
  const fmt$ = (v)=> window.AULA_LIVE ? '$'+(+v).toFixed(2) : '$'+v;
  const totalUsed = data.USAGE ? data.USAGE.used : data.FACULTY.reduce((a,f)=>a+(f.budget?f.budget.used:0),0);
  const totalCap = data.USAGE ? data.USAGE.cap : data.FACULTY.reduce((a,f)=>a+(f.budget?f.budget.cap:0),0);
  return (
    <div className="screen-pad wide">
      <div className="row" style={{justifyContent:'space-between',marginBottom:18,flexWrap:'wrap',gap:12}}>
        <div><div className="eyebrow" style={{marginBottom:8}}>{terms.principal}’s command center · you are the board</div><h1 style={{fontSize:26}}>All agents at a glance</h1></div>
        <div className="row" style={{gap:18}}>
          <div style={{textAlign:'right'}}><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:20}}>{fmt$(totalUsed)}<span className="faint" style={{fontSize:13}}>/{fmt$(totalCap)}</span></div><div className="faint mono" style={{fontSize:10}}>CREDITS USED</div></div>
          <div style={{textAlign:'right'}}><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:20}}>{data.FACULTY.length}</div><div className="faint mono" style={{fontSize:10}}>AGENTS</div></div>
        </div>
      </div>
      <div className="cmd-grid">
        <div className="panel" style={{overflow:'hidden'}}>
          <div className="cmd-th mono">Agent · role · model · grade · budget</div>
          {data.FACULTY.map(f=>(
            <div key={f.id} className="cmd-row">
              <Avatar name={f.name} hue={f.hue} size={32} sq />
              <div style={{flex:1,minWidth:0}}><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{f.name}</b> <span className="faint mono" style={{fontSize:11}}>{roleTermFor(f.role,terms)}{f.subject?' · '+f.subject:''}</span></div>
              <span className="faint mono cmd-model" style={{fontSize:11}}>{f.model}</span>
              {(()=>{ const g=gradeFor(f); return g ? <span className={"badge "+(g.score>=80?'mint':'gold')}>{g.letter}</span> : <span className="badge" style={{opacity:.5}}>—</span>; })()}
              <div className="cmd-budget"><div className="bar" style={{width:70}}><i style={{width:Math.min(100,(f.budget&&f.budget.cap?f.budget.used/f.budget.cap:0)*100)+'%'}}/></div><span className="faint mono" style={{fontSize:10}}>{fmt$(f.budget?f.budget.used:0)}/{fmt$(f.budget?f.budget.cap:0)}</span></div>
              <div className="cmd-actions"><button className="mini-btn">pause</button></div>
            </div>
          ))}
        </div>
        <div className="panel" style={{padding:16}}>
          <div className="row" style={{justifyContent:'space-between',marginBottom:12}}><h3 style={{fontSize:15}}>Reward feed</h3><span className="badge accent mono">{live?'live':'demo'}</span></div>
          <div className="col" style={{gap:2}}>
            {feed.map((f,i)=>(
              <div key={i} className="cmd-feed">
                <span className="dot" style={{background:f.kind==='pos'?'var(--mint)':f.kind==='neg'?'var(--coral)':f.kind==='update'?'var(--accent)':'var(--faint)',marginTop:6}}/>
                <div style={{flex:1}}><span style={{fontSize:12.5}}>{f.text}</span><div className="faint mono" style={{fontSize:10,marginTop:2}}>{f.who} · {f.t}</div></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Connections (LLM connectors + MCP) ---------- */
function Connections({ terms, data }){
  const { useState, useEffect } = React;
  const [providers, setProviders] = useState([]);
  const [active, setActive] = useState(null);
  const [offline, setOffline] = useState(false);
  const [sel, setSel] = useState('');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [test, setTest] = useState(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const [usage, setUsage] = useState(null);
  const [capDraft, setCapDraft] = useState('');

  useEffect(()=>{
    if(!window.AULA_API){ setOffline(true); return; }
    Promise.all([window.AULA_API.providers(), window.AULA_API.getConnector()])
      .then(([p, a])=>{
        setProviders(p.providers); setActive(a);
        const start = a.connected ? a.provider : p.providers[0].id;
        pick(p.providers, start, a.connected ? a.model : '');
      })
      .catch(()=> setOffline(true));
    window.AULA_API.usage().then(u=>{ setUsage(u); setCapDraft(String(u.cap)); }).catch(()=>{});
  },[]);

  function saveCap(){
    const cap = parseFloat(capDraft);
    if(isNaN(cap) || cap < 0) return;
    window.AULA_API.setBudget(cap).then(u=>{ setUsage(u); setCapDraft(String(u.cap)); window.AULA_API.hydrate(); }).catch(()=>{});
  }

  function pick(list, id, withModel){
    const spec = (list||providers).find(p=>p.id===id);
    setSel(id); setTest(null); setMsg('');
    setModel(withModel || (spec && spec.default_model) || '');
    if(spec && spec.id!=='ollama') setBaseUrl('');
  }

  const spec = providers.find(p=>p.id===sel);
  const cfg = ()=>({ provider: sel, api_key: apiKey, model, base_url: baseUrl });
  const needsKey = spec && spec.requires_key;
  const canConnect = spec && (!needsKey || apiKey.trim());

  function runTest(){
    setBusy(true); setTest(null);
    window.AULA_API.testConnector(cfg())
      .then(r=> setTest(r))
      .catch(e=> setTest({ ok:false, detail:String(e.message||e) }))
      .finally(()=> setBusy(false));
  }
  function connect(){
    setBusy(true); setMsg('');
    window.AULA_API.saveConnector(cfg())
      .then(a=>{ setActive(a); setApiKey(''); setMsg('Connected. Your agents now run on '+a.name+' · '+a.model+'.'); })
      .catch(e=> setMsg('Could not connect: '+String(e.message||e)))
      .finally(()=> setBusy(false));
  }
  function disconnect(){
    setBusy(true);
    window.AULA_API.clearConnector()
      .then(a=>{ setActive(a); setMsg('Disconnected — back to demo mode.'); })
      .finally(()=> setBusy(false));
  }

  return (
    <div className="screen-pad">
      <h1 style={{fontSize:26}}>Connections</h1>
      <p className="muted" style={{fontSize:14,marginTop:4,marginBottom:20}}>Bring your own model · pick a provider, add your key — tools auto-mount by subject</p>

      {offline ? (
        <div className="card coral-note" style={{marginBottom:24}}>
          <b style={{fontFamily:'var(--font-d)',fontSize:14.5}}>Backend not reachable</b>
          <p className="muted" style={{fontSize:13.5,marginTop:6}}>Start it with <span className="mono">backend\run.bat</span> (Windows) or <span className="mono">backend/run.sh</span>, then open <span className="mono">http://localhost:8000</span>. The app runs in demo mode until then.</p>
        </div>
      ) : (
        <React.Fragment>
          {/* Active connector status */}
          <div className={"card "+(active && active.connected ? 'mint-note':'')} style={{marginBottom:18}}>
            <div className="row" style={{justifyContent:'space-between',alignItems:'center',gap:12,flexWrap:'wrap'}}>
              <div>
                <div className="eyebrow" style={{marginBottom:6}}>Active connector</div>
                {active && active.connected
                  ? <b style={{fontFamily:'var(--font-d)',fontSize:15}}>{active.name} · <span className="mono" style={{color:'var(--accent)'}}>{active.model}</span></b>
                  : <b style={{fontFamily:'var(--font-d)',fontSize:15}}>Demo mode <span className="faint" style={{fontWeight:400}}>— no key connected, agents use scripted responses</span></b>}
              </div>
              {active && active.connected && <button className="btn ghost" onClick={disconnect} disabled={busy}>Disconnect</button>}
            </div>
          </div>

          {/* Credits & budget */}
          {usage && (
            <div className="card" style={{marginBottom:18}}>
              <div className="row" style={{justifyContent:'space-between',flexWrap:'wrap',gap:12,alignItems:'center'}}>
                <div style={{flex:1,minWidth:220}}>
                  <div className="eyebrow" style={{marginBottom:6}}>Credits & budget</div>
                  <b style={{fontFamily:'var(--font-d)',fontSize:15}}>${usage.used.toFixed(2)} <span className="faint" style={{fontWeight:400}}>of</span> ${usage.cap.toFixed(2)} <span className="faint" style={{fontWeight:400}}>spent</span></b>
                  <div style={{marginTop:8,maxWidth:280}}><Bar value={usage.used} max={Math.max(usage.cap,0.01)} /></div>
                  <p className="faint" style={{fontSize:11.5,marginTop:8}}>Every agent call is metered at the provider's token price. Low credits auto-downshift agents to the cheapest model; at $0 they fall back to demo mode.</p>
                </div>
                <div className="row" style={{gap:8,alignItems:'center'}}>
                  <span className="faint mono" style={{fontSize:11}}>cap $</span>
                  <input className="conn-input mono" style={{width:90}} value={capDraft} onChange={e=>setCapDraft(e.target.value)} />
                  <button className="btn ghost" onClick={saveCap}>Set</button>
                </div>
              </div>
            </div>
          )}

          {/* Provider picker */}
          <div className="eyebrow" style={{marginBottom:12}}>Choose a provider</div>
          <div className="grid" style={{gridTemplateColumns:'repeat(auto-fill,minmax(190px,1fr))',marginBottom:18}}>
            {providers.map(p=>(
              <button key={p.id} className={"mcp-card"+(sel===p.id?' on':'')} style={{textAlign:'left',cursor:'pointer'}} onClick={()=>pick(providers,p.id,'')}>
                <div className="row" style={{justifyContent:'space-between',marginBottom:8}}>
                  <b style={{fontFamily:'var(--font-d)',fontSize:14}}>{p.name}</b>
                  {active && active.connected && active.provider===p.id && <span className="badge mint">on</span>}
                </div>
                <div className="faint mono" style={{fontSize:11}}>{p.tier}</div>
                <div className="faint" style={{fontSize:11,marginTop:8}}>{p.requires_key?'needs API key':'no key · local'}</div>
              </button>
            ))}
          </div>

          {/* Configure selected provider */}
          {spec && (
            <div className="card" style={{marginBottom:26}}>
              <div className="row" style={{justifyContent:'space-between',marginBottom:14}}>
                <b style={{fontFamily:'var(--font-d)',fontSize:15}}>Configure {spec.name}</b>
                <a href={spec.key_url} target="_blank" rel="noreferrer" className="faint mono" style={{fontSize:11}}>{spec.requires_key?'get a key ↗':'install ↗'}</a>
              </div>

              <label className="conn-label">Model</label>
              <select className="conn-input" value={model} onChange={e=>setModel(e.target.value)}>
                {spec.models.map(m=><option key={m} value={m}>{m}</option>)}
              </select>

              {needsKey && (
                <React.Fragment>
                  <label className="conn-label" style={{marginTop:12}}>API key <span className="faint mono" style={{fontSize:10}}>· {spec.key_label}</span></label>
                  <input className="conn-input mono" type="password" value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="paste your key — stored on your backend, never committed" />
                </React.Fragment>
              )}
              {spec.id==='ollama' && (
                <React.Fragment>
                  <label className="conn-label" style={{marginTop:12}}>Endpoint</label>
                  <input className="conn-input mono" value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="http://localhost:11434/v1" />
                </React.Fragment>
              )}

              <div className="row" style={{gap:10,marginTop:16,alignItems:'center',flexWrap:'wrap'}}>
                <button className="btn ghost" onClick={runTest} disabled={busy || (needsKey && !apiKey.trim())}>{busy?'…':'Test'}</button>
                <button className="btn primary" onClick={connect} disabled={busy || !canConnect}>Connect</button>
                {test && <span className="badge mono" style={{color:test.ok?'var(--mint)':'var(--coral)',borderColor:'currentColor'}}>{test.ok?'✓ reachable':'✕ failed'} · {String(test.detail||'').slice(0,60)}</span>}
              </div>
              {msg && <p className="muted" style={{fontSize:12.5,marginTop:12}}>{msg}</p>}
            </div>
          )}
        </React.Fragment>
      )}

      <div className="eyebrow" style={{marginBottom:12}}>Faculty · model per agent</div>
      <div className="panel" style={{overflow:'hidden',marginBottom:26}}>
        {data.FACULTY.map(f=>(
          <div key={f.id} className="conn-row">
            <Avatar name={f.name} hue={f.hue} size={30} sq />
            <div style={{flex:1}}><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{f.name}</b> <span className="faint mono" style={{fontSize:11}}>{roleTermFor(f.role,terms)}</span></div>
            <div className="model-pick">
              {(active && active.connected) ? active.model : f.model}
              <span className="faint" style={{fontSize:11,marginLeft:8}}>▾</span>
            </div>
          </div>
        ))}
      </div>

      <div className="eyebrow" style={{marginBottom:12}}>MCP registry · {data.MCP.filter(m=>m.status==='mounted').length} mounted</div>
      <div className="grid" style={{gridTemplateColumns:'repeat(auto-fill,minmax(230px,1fr))'}}>
        {data.MCP.map(m=>(
          <div key={m.id} className={"mcp-card"+(m.status==='mounted'?' on':'')}>
            <div className="row" style={{justifyContent:'space-between',marginBottom:10}}>
              <span className="mcp-ico mono">{m.id==='slack'?'⌁':m.id==='kanban'?'⛁':'{}'}</span>
              <span className={"badge "+(m.status==='mounted'?'mint':'')}>{m.status}</span>
            </div>
            <b style={{fontFamily:'var(--font-d)',fontSize:14}}>{m.name}</b>
            <div className="faint mono" style={{fontSize:11,marginTop:4}}>{m.cap}</div>
            <div className="faint" style={{fontSize:11,marginTop:8}}>auto-mounts · {m.domain}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, {
  SCR_exams:ExamsScreen, SCR_teacherboard:TeacherBoard, SCR_grades:FacultyGrades,
  SCR_command:CommandCenter, SCR_connections:Connections
});
