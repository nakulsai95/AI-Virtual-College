/* AULA product — learn screens: Dashboard, Board, Lesson, Guide, Channel, Library */
const { useState: useStateL, useEffect: useEffectL, useRef: useRefL } = React;

/* ---------- Dashboard ---------- */
function Dashboard({ terms, nav, data }){
  const S = data.STUDENT;
  const ranks = terms.ranks;
  return (
    <div className="screen-pad">
      <div className="dash-hero">
        <div>
          <div className="eyebrow" style={{marginBottom:10}}>{terms.semester} · week {S.week} of {S.weeks}</div>
          <h1 style={{fontSize:30}}>Welcome back, {S.name}.</h1>
          <p className="muted" style={{marginTop:8,fontSize:16,maxWidth:'52ch'}}>{S.mission}</p>
        </div>
        <button className="btn primary" onClick={()=>nav('lesson')}>Continue · {data.LESSON.title} →</button>
      </div>

      <div className="stat-row">
        <div className="card pad-sm stat-card">
          <RankRing tier={S.rankTier} ranks={ranks} size={46} />
          <div><div className="sc-k">{terms.rankWord}</div><div className="sc-v">{ranks[S.rankTier]}</div><div className="sc-s">{S.nextTierXp-S.xp} XP to {ranks[S.rankTier+1]}</div></div>
        </div>
        <div className="card pad-sm stat-card">
          <div className="sc-big" style={{color:'var(--accent)'}}>{S.xp}</div>
          <div><div className="sc-k">XP</div><div style={{width:120,marginTop:6}}><Bar value={S.xp} max={S.nextTierXp} /></div></div>
        </div>
        <div className="card pad-sm stat-card">
          <div className="sc-big" style={{color:'var(--mint)'}}>{S.streak}🔥</div>
          <div><div className="sc-k">Day streak</div><div className="sc-s">momentum {S.momentum}%</div></div>
        </div>
        <div className="card pad-sm stat-card">
          <div className="sc-big">{S.attendance}%</div>
          <div><div className="sc-k">Attendance</div><div className="sc-s">on track</div></div>
        </div>
      </div>

      <div className="dash-grid">
        <div className="col" style={{gap:16}}>
          <div className="card">
            <div className="row" style={{justifyContent:'space-between',marginBottom:14}}>
              <h3>Your subjects</h3><span className="badge mono">{data.SUBJECTS.length} active</span>
            </div>
            {data.SUBJECTS.map(s=>(
              <div key={s.id} className="subj-row" onClick={()=>nav('board')}>
                <Avatar name={s.profName} hue={s.hue} size={36} sq />
                <div style={{flex:1,minWidth:0}}>
                  <div className="row" style={{justifyContent:'space-between'}}><b style={{fontFamily:'var(--font-d)',fontSize:14.5}}>{s.title}</b><span className="mono faint" style={{fontSize:12}}>{s.progress}%</span></div>
                  <div style={{marginTop:7}}><Bar value={s.progress} /></div>
                  <div className="faint" style={{fontSize:12,marginTop:6,fontFamily:'var(--font-m)'}}>{terms.professor} {s.profName}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="card">
            <h3 style={{marginBottom:12}}>Recent activity</h3>
            {data.FEED.slice(0,4).map((f,i)=>(
              <div key={i} className="feed-row">
                <span className={"dot"} style={{background:f.kind==='pos'?'var(--mint)':f.kind==='neg'?'var(--coral)':f.kind==='update'?'var(--accent)':'var(--faint)'}} />
                <span style={{flex:1,fontSize:13}}>{f.text}</span>
                <span className="faint mono" style={{fontSize:11}}>{f.t}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="col" style={{gap:16}}>
          <div className="card next-card">
            <div className="eyebrow" style={{marginBottom:12}}>Up next</div>
            <div className="row" style={{gap:12}}>
              <Avatar name={data.LESSON.author} hue="#f5a623" size={40} sq />
              <div><b style={{fontFamily:'var(--font-d)',fontSize:15}}>{data.LESSON.title}</b><div className="faint" style={{fontSize:12,fontFamily:'var(--font-m)'}}>{terms.professor} {data.LESSON.author} · {data.LESSON.read}</div></div>
            </div>
            <p className="muted" style={{fontSize:13,margin:'13px 0 16px'}}>{data.LESSON.intro.slice(0,110)}…</p>
            <button className="btn primary" style={{width:'100%',justifyContent:'center'}} onClick={()=>nav('lesson')}>Read the lesson →</button>
          </div>
          <div className="card">
            <h3 style={{marginBottom:12}}>Your faculty</h3>
            <div className="col" style={{gap:9}}>
              {data.FACULTY.filter(f=>f.role==='professor'||f.role==='guide').map(f=>(
                <div key={f.id} className="row"><Avatar name={f.name} hue={f.hue} size={30} /><div style={{flex:1}}><b style={{fontFamily:'var(--font-d)',fontSize:13}}>{f.name}</b> <span className="faint" style={{fontSize:11.5}}>{f.subject||terms.guide}</span></div>{f.grade && <span className="badge mint">{f.grade.letter}</span>}</div>
              ))}
            </div>
            <button className="btn ghost" style={{width:'100%',justifyContent:'center',marginTop:14}} onClick={()=>nav('channel')}>Message a {terms.professor.toLowerCase()} →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Curriculum / Semester plan ---------- */
function CurriculumScreen({ terms, nav, data }){
  const S = data.STUDENT;
  const weeks = Array.from({length:S.weeks},(_,i)=>i+1);
  const examWeeks = {};
  data.EXAMS.forEach(e=>{ const n=parseInt((e.when||'').replace(/\D/g,'')); if(n) examWeeks[n]=e.status; });
  const statusIcon = { done:'✓', active:'●', locked:'🔒' };
  const examBadge = { passed:['mint','passed'], failed:['coral','failed'], pending:['','pending'] };
  return (
    <div className="screen-pad">
      <div className="row" style={{justifyContent:'space-between',alignItems:'flex-end',marginBottom:18,flexWrap:'wrap',gap:14}}>
        <div>
          <div className="eyebrow" style={{marginBottom:10}}>{terms.semester} plan · designed by {terms.principal} Iroha</div>
          <h1 style={{fontSize:28}}>Your {terms.semester.toLowerCase()}</h1>
          <p className="muted" style={{fontSize:15,marginTop:8}}>{S.mission} · {data.SUBJECTS.length} subjects · {S.weeks} weeks</p>
        </div>
        <div style={{textAlign:'right'}}><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:24}}>Week {S.week}</div><div className="faint mono" style={{fontSize:11}}>of {S.weeks}</div></div>
      </div>

      <div className="curr-timeline">
        {weeks.map(w=>(
          <div key={w} className={"week"+(w===S.week?' now':'')+(w<S.week?' past':'')} title={'Week '+w}>
            <div className="wk-bar">{examWeeks[w] && <span className={"wk-exam "+(examWeeks[w]==='failed'?'fail':'pass')} title={terms.exam} />}</div>
            <span className="wk-n">{w}</span>
          </div>
        ))}
      </div>
      <div className="row" style={{gap:16,margin:'12px 2px 26px',flexWrap:'wrap'}}>
        <span className="faint mono" style={{fontSize:11}}><span className="dot" style={{background:'var(--accent)',display:'inline-block',marginRight:6}} />current week</span>
        <span className="faint mono" style={{fontSize:11}}><span className="dot" style={{background:'var(--mint)',display:'inline-block',marginRight:6}} />{terms.exam} passed</span>
        <span className="faint mono" style={{fontSize:11}}><span className="dot" style={{background:'var(--coral)',display:'inline-block',marginRight:6}} />re-enrol</span>
      </div>

      {data.SUBJECTS.map(s=>(
        <div key={s.id} className="subj-card">
          <div className="sc-top">
            <Avatar name={s.profName} hue={s.hue} size={40} sq />
            <div style={{flex:1}}><div className="scn">{s.title}</div><div className="scp">{terms.professor} {s.profName} · {s.progress}% complete</div></div>
            <div style={{width:140}}><Bar value={s.progress} /></div>
          </div>
          <div className="col" style={{gap:0}}>
            {s.modules.map((m,i)=>{
              const eb=examBadge[m.exam]||['','pending'];
              return (
                <div key={m.id} className={"curr-mod "+m.status}>
                  <span className={"cm-ico "+m.status}>{statusIcon[m.status]}</span>
                  <span className="cm-n mono">{terms.module} {i+1}</span>
                  <span className="cm-title">{m.title}</span>
                  <span className={"badge "+eb[0]} style={{marginLeft:'auto'}}>{terms.exam}: {eb[1]}</span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ---------- My Board (kanban) ---------- */
/* Open a task's lesson — fetched live by id when the backend authored it. */
function openTask(t, nav){
  if(t.type!=='lesson') return;
  if(t.lesson_id && window.AULA_API && window.AULA_LIVE){
    window.AULA_API.getLesson(t.lesson_id)
      .then(r=>nav('lesson', r.lesson))
      .catch(()=>nav('lesson'));
    return;
  }
  nav('lesson');
}
function MyBoard({ terms, nav, data }){
  const cols = [
    { key:'lessons', label:'Lessons' }, { key:'doing', label:'Doing' },
    { key:'submitted', label:'Submitted' }, { key:'graded', label:'Graded' }
  ];
  return (
    <div className="screen-pad wide">
      <div className="row" style={{justifyContent:'space-between',marginBottom:6}}>
        <div><h1 style={{fontSize:26}}>My Board</h1><p className="muted" style={{fontSize:14,marginTop:4}}>Tasks across your {terms.semester.toLowerCase()} · synced via Kanban MCP</p></div>
        <span className="badge accent mono">⛁ kanban-mcp · live</span>
      </div>
      <div className="kanban">
        {cols.map(c=>(
          <div key={c.key} className="kan-col">
            <div className="kan-head"><span>{c.label}</span><span className="kan-n">{data.KANBAN[c.key].length}</span></div>
            <div className="kan-cards">
              {data.KANBAN[c.key].map(t=>(
                <div key={t.id} className={"kan-card"+(t.type==='lesson'?' lesson':'')} onClick={()=>openTask(t,nav)}>
                  <div className="row" style={{justifyContent:'space-between',marginBottom:8}}>
                    <span className={"badge "+(t.good===true?'mint':t.good===false?'coral':'')}>{t.type}</span>
                    {t.tool && <span className="badge gold mono">tool</span>}
                  </div>
                  <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:13.5,lineHeight:1.3}}>{t.title}</div>
                  <div className="faint mono" style={{fontSize:11,marginTop:9}}>{t.subject} · {t.meta}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- Lesson (blog reader) ---------- */
function LessonScreen({ terms, nav, data, lessonOpen }){
  const L = (lessonOpen && typeof lessonOpen==='object' && lessonOpen.title) ? lessonOpen : data.LESSON;
  const [ans,setAns] = useStateL('');
  const [sent,setSent] = useStateL(false);
  const [grade,setGrade] = useStateL(null);   // real Examiner result
  const [grading,setGrading] = useStateL(false);
  // Self-contained default so "Run" works for real against the Python sandbox.
  const STARTER = "import base64, json\n\npayload = {\"sub\": 1024, \"name\": \"Alex\", \"exp\": 1735689600}\nencoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip(\"=\")\nprint(\"encoded:\", encoded)\n\nbody = encoded + \"=\" * (-len(encoded) % 4)\nprint(\"decoded:\", json.loads(base64.urlsafe_b64decode(body)))\n";
  const sandbox = L.sandbox || 'python';
  const [code,setCode] = useStateL(L.code_starter || STARTER);
  const [out,setOut] = useStateL(null);
  const [running,setRunning] = useStateL(false);
  function runCode(){
    setRunning(true); setOut(null);
    if(window.AULA_API){
      window.AULA_API.runCode(sandbox, code)
        .then(r=>{ setRunning(false);
          const txt = [(r.stdout||'').replace(/\s+$/,''), r.stderr?('\u2014 '+r.stderr.replace(/\s+$/,'')):''].filter(Boolean).join('\n');
          setOut(txt || (r.ok?'(ran \u2014 no output)':'(error)')); })
        .catch(()=>{ setRunning(false); setOut('Sandbox offline \u2014 start the backend (backend\\run.bat) to run code for real.'); });
      return;
    }
    setTimeout(()=>{ setRunning(false); setOut("{'sub': 1024, 'name': 'Alex', 'exp': 1735689600}\n\n\u2713 demo output \u2014 connect the backend to run for real."); }, 600);
  }
  function submitProbe(){
    if(window.AULA_API){
      setGrading(true);
      window.AULA_API.grade({ kind:'probe', question:L.probe.q, answer:ans, bar:70, subject:L.subject, professor:L.author })
        .then(r=>{ setGrade(r); setGrading(false); setSent(true); window.AULA_API.hydrate(); })
        .catch(()=>{ setGrading(false); setSent(true); });
      return;
    }
    setSent(true);
  }
  return (
    <div className="screen-pad">
      <button className="btn ghost" style={{marginBottom:18,padding:'8px 14px',fontSize:13}} onClick={()=>nav('board')}>← Board</button>
      <div className="lesson">
        <div className="eyebrow" style={{marginBottom:14}}>{L.subject} · authored lesson</div>
        <h1 style={{fontSize:34,lineHeight:1.1}}>{L.title}</h1>
        <div className="row" style={{gap:11,margin:'16px 0 26px'}}>
          <Avatar name={L.author} hue="#f5a623" size={34} />
          <div><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{terms.professor} {L.author}</b><div className="faint mono" style={{fontSize:11}}>{L.read} read · wrote this for you</div></div>
        </div>
        <p className="lesson-intro">{L.intro}</p>
        {L.sections.map((s,i)=>(
          <div key={i} className="lesson-sec">
            <h3>{s.h}</h3><p>{s.p}</p>
          </div>
        ))}

        <div className="codecell">
          <div className="cc-head">
            <span className="mono" style={{fontSize:12,color:'var(--muted)'}}>▶ Try it · test your understanding</span>
            <span className="badge accent mono">{sandbox} · sandbox</span>
          </div>
          <textarea className="cc-code" spellCheck={false} value={code} onChange={e=>setCode(e.target.value)} rows={7} />
          <div className="cc-actions">
            <span className="faint mono" style={{fontSize:11}}>Runs in a real {sandbox} sandbox on your backend.</span>
            <button className="btn primary" onClick={runCode} disabled={running}>{running?'Running…':'▶ Run'}</button>
          </div>
          {out && <pre className="cc-out">{out}</pre>}
        </div>

        <div className="probe">
          <div className="eyebrow" style={{marginBottom:10}}>{terms.professor} {L.author} asks · this affects their grade, not yours</div>
          <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:16,marginBottom:14}}>{L.probe.q}</div>
          {!sent ? (
            <React.Fragment>
              <textarea className="probe-input" rows={2} value={ans} onChange={e=>setAns(e.target.value)} placeholder="Type your answer…" />
              <div className="row" style={{justifyContent:'space-between',marginTop:10}}>
                <span className="faint mono" style={{fontSize:11}}>Hint: {L.probe.hint}</span>
                <button className="btn primary" onClick={submitProbe} disabled={!ans.trim()||grading}>{grading?'Grading…':'Submit answer'}</button>
              </div>
            </React.Fragment>
          ) : (
            <div className="probe-fb">
              {grade ? (
                <React.Fragment>
                  <div className="row" style={{gap:10,marginBottom:8,flexWrap:'wrap'}}>
                    <Avatar name={L.author} hue="#f5a623" size={28}/><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{L.author}</b>
                    <span className={"badge "+(grade.passed?'mint':'coral')}>{grade.score}% · {grade.passed?'passed':'below bar'}</span>
                    {grade.reward && <span className={"badge "+(grade.reward.delta>=0?'mint':'coral')+" mono"}>{grade.reward.delta>=0?'+':''}{grade.reward.delta} to {L.author}</span>}
                    {grade.reward && grade.reward.methodology_changed && <span className="badge accent mono">Provost rewrote methodology · v{grade.reward.professor.version}</span>}
                  </div>
                  <p className="muted" style={{fontSize:13.5}}>{grade.feedback}</p>
                  <p className="faint mono" style={{fontSize:11,marginTop:8}}>Remember: the reward landed on your teacher, never on you — that’s what keeps the faculty accountable.</p>
                  <button className="btn primary" style={{marginTop:14}} onClick={()=>nav('board')}>Next · {L.next||'continue'} →</button>
                </React.Fragment>
              ) : (
                <React.Fragment>
                  <div className="row" style={{gap:10,marginBottom:8}}><Avatar name={L.author} hue="#f5a623" size={28}/><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{L.author}</b><span className="badge mint">answer received</span></div>
                  <p className="muted" style={{fontSize:13.5}}>Submitted. Connect a model in Connections to have the Examiner grade this for real.</p>
                  <button className="btn primary" style={{marginTop:14}} onClick={()=>nav('board')}>Next · {L.next||'continue'} →</button>
                </React.Fragment>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------- Personal Guide (chat) ---------- */
function GuideScreen({ terms, nav, data }){
  const [msgs,setMsgs] = useStateL(()=> window.AULA_LIVE
    ? [{who:'guide',name:terms.guide,text:'Stuck on anything? Ask me and I’ll bring the right teacher in.'}]
    : data.GUIDE_THREAD);
  const [val,setVal] = useStateL('');
  const [busy,setBusy] = useStateL(false);
  const endRef = useRefL(null);
  useEffectL(()=>{ endRef.current && endRef.current.scrollTo(0, endRef.current.scrollHeight); },[msgs]);
  function send(){
    if(!val.trim() || busy) return;
    const q = val.trim(); setVal('');
    setMsgs(m=>[...m,{who:'user',text:q}]);

    // Live: the real Guide agent routes the question; the routed Professor
    // actually authors a lesson and drops it on your board + library.
    if(window.AULA_API && window.AULA_LIVE){
      setBusy(true);
      setMsgs(m=>[...m,{who:'system',text:'Guide is thinking…'}]);
      window.AULA_API.guideAsk(q)
        .then(out=>{
          data.LESSON = out.lesson;  // dashboard "Continue" + board card open it
          setMsgs(m=>[...m.filter(x=>x.text!=='Guide is thinking…'),
            {who:'guide',name:terms.guide,text:out.reply},
            {who:'route',text:'Routed · '+out.route.professor+' · '+out.route.subject},
            {who:'prof',name:out.lesson.author,hue:'#f5a623',text:'Done — I wrote “'+out.lesson.title+'”. Open it from your board or dashboard.'},
            {who:'system',text:'New lesson added · '+out.lesson.title}
          ]);
          window.AULA_API.hydrate();
        })
        .catch(()=>{
          setMsgs(m=>[...m.filter(x=>x.text!=='Guide is thinking…'),
            {who:'guide',name:terms.guide,text:'I hit a snag reaching the faculty — try again in a moment.'}]);
        })
        .finally(()=>setBusy(false));
      return;
    }

    // Demo fallback (no backend).
    const subj = (data.SUBJECTS && data.SUBJECTS[0]) || {};
    const subject = subj.title || 'your subject';
    const prof = subj.profName || terms.professor;
    setTimeout(()=>setMsgs(m=>[...m,{who:'guide',name:terms.guide,text:'Good one — bringing in '+prof+' for '+subject+'. They’ll write you a lesson.'}]),400);
    setTimeout(()=>setMsgs(m=>[...m,{who:'route',text:'Routed · '+terms.professor+' · '+subject}]),900);
    if(window.AULA_API){
      window.AULA_API.lesson(subject, q, prof, (subj.sandboxes && subj.sandboxes[0]) || 'python')
        .then(out=>{
          data.LESSON = out.lesson;
          setMsgs(m=>[...m,
            {who:'prof',name:out.lesson.author,hue:'#f5a623',text:'Done — I wrote “'+out.lesson.title+'”. Open it from your board or dashboard.'},
            {who:'system',text:'New lesson added · '+out.lesson.title}
          ]);
        })
        .catch(()=>{});
    }
  }
  return (
    <div className="chat-wrap">
      <div className="chat-head">
        <Avatar name="Y" hue="#9b6cff" size={34} sq glyph="✦" />
        <div><b style={{fontFamily:'var(--font-d)',fontSize:15}}>{terms.guide}</b><div className="mono" style={{fontSize:11,color:'var(--mint)'}}>● always on · routes any doubt</div></div>
      </div>
      <div className="chat-body" ref={endRef}>
        {msgs.map((m,i)=><Bubble key={i} m={m} terms={terms} />)}
      </div>
      <div className="chat-input">
        <input value={val} onChange={e=>setVal(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send()} placeholder={"Ask anything — I’ll bring the right "+terms.professor.toLowerCase()+" in…"} />
        <button className="btn primary" onClick={send}>Ask</button>
      </div>
    </div>
  );
}
function Bubble({ m, terms }){
  if(m.who==='route') return <div className="b-route">→ {m.text}</div>;
  if(m.who==='system') return <div className="b-system">✓ {m.text}</div>;
  const me = m.who==='user';
  const hue = m.hue || (m.who==='guide'?'#9b6cff':'#f5a623');
  return (
    <div className={"bubble-row"+(me?' me':'')}>
      {!me && <Avatar name={m.name||'?'} hue={hue} size={28} />}
      <div className={"bubble"+(me?' me':'')}>
        {!me && m.name && <div className="b-name">{m.name}</div>}
        {m.text}
      </div>
    </div>
  );
}

/* ---------- Channel (Slack-style) ---------- */
function ChannelScreen({ terms, data }){
  const [active,setActive] = useStateL(data.CHANNELS[0].id);
  const [draft,setDraft] = useStateL('');
  const [busy,setBusy] = useStateL(false);
  const bodyRef = useRefL(null);
  const ch = data.CHANNELS.find(c=>c.id===active) || data.CHANNELS[0];
  useEffectL(()=>{ bodyRef.current && bodyRef.current.scrollTo(0, bodyRef.current.scrollHeight); },[ch && ch.messages.length, active]);
  function pick(c){
    setActive(c.id);
    if(window.AULA_LIVE && c.unread){ c.unread = 0; window.AULA_API.channelRead(c.id).catch(()=>{}); }
  }
  function send(){
    const t = draft.trim();
    if(!t || busy || !(window.AULA_API && window.AULA_LIVE)) return;
    setBusy(true); setDraft('');
    ch.messages.push({who:data.STUDENT.name,role:'me',text:t,t:'now'});
    window.AULA_API.channelSend(ch.id, t)
      .then(()=>window.AULA_API.hydrate())
      .catch(()=>{ ch.messages.push({who:'system',role:'system',text:'Could not send — backend unreachable.',t:'now'}); })
      .finally(()=>setBusy(false));
  }
  return (
    <div className="channel">
      <div className="ch-list">
        <div className="ch-list-h mono">Channels</div>
        {data.CHANNELS.map(c=>(
          <button key={c.id} className={"ch-item"+(c.id===active?' on':'')} onClick={()=>pick(c)}>
            {c.kind==='room'
              ? <span className="ch-hash">#</span>
              : <Avatar name={c.name} hue={c.hue||'#9b6cff'} size={26} />}
            <div style={{flex:1,minWidth:0}}><b style={{fontFamily:'var(--font-d)',fontSize:13}}>{c.name}</b><div className="faint" style={{fontSize:11}}>{c.sub}</div></div>
            {c.unread>0 && <span className="badge-n" style={{marginLeft:'auto'}}>{c.unread}</span>}
          </button>
        ))}
      </div>
      <div className="ch-main">
        <div className="ch-head">
          {ch.kind==='room'?<span className="ch-hash big">#</span>:<Avatar name={ch.name} hue={ch.hue} size={30}/>}
          <div><b style={{fontFamily:'var(--font-d)',fontSize:15}}>{ch.name}</b><div className="faint mono" style={{fontSize:11}}>{ch.sub}</div></div>
          <div style={{flex:1}}/>
          <span className="badge accent mono">⌁ slack-mcp</span>
        </div>
        <div className="ch-body" ref={bodyRef}>
          {ch.kind==='room' && <div className="b-system" style={{marginBottom:10}}>Your faculty coordinate here. You can read along.</div>}
          {ch.messages.map((m,i)=>(
            <div key={i} className={"ch-msg"+(m.role==='me'?' me':'')}>
              {m.role!=='me' && <Avatar name={m.who} hue={m.hue||'#6e8efb'} size={30} />}
              <div className="ch-msg-body">
                <div className="ch-msg-top"><b>{m.who}</b> <span className="badge" style={{fontSize:9}}>{roleTermFor(m.role,terms)}</span> <span className="faint mono" style={{fontSize:10}}>{m.t}</span></div>
                <div className="ch-msg-text">{m.text}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="chat-input">
          <input value={draft} onChange={e=>setDraft(e.target.value)}
                 onKeyDown={e=>e.key==='Enter'&&send()}
                 placeholder={window.AULA_LIVE
                   ? (ch.kind==='room'?'Reply in '+ch.name+'…':'Message '+ch.name+'…')
                   : 'Connect the backend to message your faculty…'} />
          <button className="btn primary" onClick={send} disabled={busy||!window.AULA_LIVE}>{busy?'…':'Send'}</button>
        </div>
      </div>
    </div>
  );
}
function roleTermFor(role, terms){
  return ({ professor:terms.professor, principal:terms.principal, provost:'Provost', examiner:'Examiner', guide:terms.guide, me:'you' })[role] || role;
}

/* ---------- Library ---------- */
function LibraryScreen({ terms, nav, data }){
  const [q,setQ] = useStateL('');
  const [subj,setSubj] = useStateL('all');
  const subjects = ['all', ...new Set(data.LIBRARY.map(l=>l.subject))];
  const items = data.LIBRARY.filter(l=>
    (subj==='all'||l.subject===subj) &&
    (l.title.toLowerCase().includes(q.toLowerCase())||l.author.toLowerCase().includes(q.toLowerCase())));
  return (
    <div className="screen-pad wide">
      <div className="row" style={{justifyContent:'space-between',marginBottom:16,flexWrap:'wrap',gap:12}}>
        <div><h1 style={{fontSize:26}}>Library</h1><p className="muted" style={{fontSize:14,marginTop:4}}>Every lesson your faculty has authored · {data.LIBRARY.length} entries</p></div>
        <input className="lib-search" value={q} onChange={e=>setQ(e.target.value)} placeholder="Search lessons…" />
      </div>
      <div className="row" style={{gap:8,marginBottom:18,flexWrap:'wrap'}}>
        {subjects.map(s=><button key={s} className={"ex-chip"+(subj===s?' on-chip':'')} onClick={()=>setSubj(s)} style={subj===s?{color:'var(--accent)',borderColor:'var(--accent-line)',background:'var(--accent-soft)'}:{}}>{s==='all'?'All subjects':s}</button>)}
      </div>
      <div className="lib-grid">
        {items.map(l=>(
          <div key={l.id} className={"lib-card"+(l.state==='locked'?' locked':'')}
               onClick={()=>l.state!=='locked'&&openTask({type:'lesson',lesson_id:(window.AULA_LIVE?l.id:null)},nav)}>
            <div className="row" style={{justifyContent:'space-between',marginBottom:12}}>
              <span className="badge mono">{l.tag}</span>
              {l.state==='new' && <span className="badge accent">new</span>}
              {l.state==='unread' && <span className="dot" style={{background:'var(--accent)'}} />}
              {l.state==='locked' && <span className="badge">🔒</span>}
            </div>
            <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:15,lineHeight:1.25,marginBottom:10}}>{l.title}</div>
            <div className="row" style={{gap:8}}><Avatar name={l.author} hue={l.author==='Mei'?'#f5a623':'#3b82f6'} size={22}/><span className="faint mono" style={{fontSize:11}}>{l.author} · {l.read}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- My Progress (student diagnostic) ---------- */
function levelMeta(l){
  if(l>=0.8) return { label:'Strong', cls:'mint', color:'var(--mint)' };
  if(l>=0.55) return { label:'Solid', cls:'accent', color:'var(--accent)' };
  if(l>=0.3) return { label:'Developing', cls:'gold', color:'var(--gold)' };
  return { label:'Needs work', cls:'coral', color:'var(--coral)' };
}
function ProgressScreen({ terms, nav, data }){
  const flat = data.MASTERY.flatMap(s=>s.concepts.map(c=>({...c, subject:s.subject, hue:s.hue})));
  const overall = flat.length ? Math.round(flat.reduce((a,c)=>a+c.level,0)/flat.length*100) : 0;
  const strengths = flat.filter(c=>c.level>=0.8).sort((a,b)=>b.level-a.level).slice(0,3);
  const engaged = flat.filter(c=>c.seen!=='not yet'&&c.seen!=='locked');
  const focus = engaged.sort((a,b)=>a.level-b.level).slice(0,3);
  const lag = focus[0];
  return (
    <div className="screen-pad">
      <div className="report-head">
        <div>
          <div className="eyebrow" style={{marginBottom:10}}>Your diagnostic · this is for you, not a grade</div>
          <h1 style={{fontSize:28}}>Where you stand</h1>
          <p className="muted" style={{fontSize:15,marginTop:8,maxWidth:'54ch'}}>Your teachers carry the grades — this is your own map of what’s landed and what to focus on next. Nothing here counts against you.</p>
        </div>
        <div className="overall">
          <RankRing tier={Math.min(3,Math.floor(overall/25))} ranks={terms.ranks} size={68} />
          <div><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:30,lineHeight:1}}>{overall}%</div><div className="faint mono" style={{fontSize:10,marginTop:3}}>OVERALL MASTERY</div></div>
        </div>
      </div>

      <div className="sw-grid">
        <div className="card sw-card mint">
          <div className="row" style={{justifyContent:'space-between',marginBottom:12}}><h3 style={{fontSize:15}}>Your strengths</h3><span className="badge mint">going well</span></div>
          {strengths.map(c=>(
            <div key={c.name} className="sw-item">
              <span className="dot" style={{background:'var(--mint)'}}/>
              <div style={{flex:1}}><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{c.name}</b><div className="faint mono" style={{fontSize:11}}>{c.subject}</div></div>
              <span className="mono" style={{fontSize:12,color:'var(--mint)'}}>{Math.round(c.level*100)}%</span>
            </div>
          ))}
        </div>
        <div className="card sw-card coral">
          <div className="row" style={{justifyContent:'space-between',marginBottom:12}}><h3 style={{fontSize:15}}>Where you lag</h3><span className="badge coral">focus here</span></div>
          {focus.map(c=>(
            <div key={c.name} className="sw-item">
              <span className="dot" style={{background:levelMeta(c.level).color}}/>
              <div style={{flex:1}}><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{c.name}</b><div className="faint mono" style={{fontSize:11}}>{c.subject} · seen {c.seen}</div></div>
              <span className="mono" style={{fontSize:12,color:levelMeta(c.level).color}}>{Math.round(c.level*100)}%</span>
            </div>
          ))}
        </div>
      </div>

      {lag && (
        <div className="card next-move">
          <div className="row" style={{gap:14,alignItems:'flex-start'}}>
            <span className="dot" style={{background:'var(--accent)',marginTop:7}}/>
            <div style={{flex:1}}>
              <div className="eyebrow" style={{marginBottom:6}}>Your next best move</div>
              <b style={{fontFamily:'var(--font-d)',fontSize:15.5}}>Revise “{lag.name}” — your weakest active concept.</b>
              <p className="muted" style={{fontSize:13.5,marginTop:6}}>It’s the one thing most likely to lift your {lag.subject} mastery. Your teacher already reworked this with worked examples — it’s waiting in the library.</p>
            </div>
            <button className="btn primary" onClick={()=>nav('library')}>Go revise →</button>
          </div>
        </div>
      )}

      <h3 style={{fontSize:16,margin:'28px 0 14px'}}>Concept-by-concept</h3>
      <div className="grid" style={{gridTemplateColumns:'1fr 1fr'}}>
        {data.MASTERY.map(s=>(
          <div key={s.subject} className="card concept-block">
            <div className="row" style={{gap:11,marginBottom:14}}><Avatar name={s.subject} hue={s.hue} size={28} sq glyph={s.subject[0]} /><b style={{fontFamily:'var(--font-d)',fontSize:14.5}}>{s.subject}</b></div>
            {s.concepts.map(c=>{
              const m=levelMeta(c.level);
              return (
                <div key={c.name} className="concept-row">
                  <div className="cr-name">{c.name}</div>
                  <div className="m-bar"><i style={{width:Math.max(4,c.level*100)+'%',background:m.color}}/></div>
                  <span className={"badge "+m.cls} style={{minWidth:92,justifyContent:'center'}}>{m.label}</span>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, {
  SCR_home:Dashboard, SCR_board:MyBoard, SCR_lesson:LessonScreen,
  SCR_guide:GuideScreen, SCR_channel:ChannelScreen, SCR_library:LibraryScreen,
  SCR_progress:ProgressScreen, SCR_curriculum:CurriculumScreen
});
