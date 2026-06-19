/* AULA product — learn screens: Dashboard, Board, Lesson, Guide, Channel, Library */
const { useState: useStateL, useEffect: useEffectL, useRef: useRefL } = React;

/* ---------- Dashboard ---------- */
function BuildBanner({ data }){
  const b = data.BUILD;
  if(!window.AULA_LIVE || !b || b.finished) return null;
  const paused = b.stage === 'paused';
  function resume(){
    if(window.AULA_API) window.AULA_API.buildContinue().then(()=>window.AULA_API.hydrate()).catch(()=>{});
  }
  return (
    <div className={"card "+(paused?'coral-note':'accent-note')} style={{marginBottom:16}}>
      <div className="row" style={{justifyContent:'space-between',flexWrap:'wrap',gap:10,marginBottom:10}}>
        <b style={{fontFamily:'var(--font-d)',fontSize:14.5}}>{paused?'⏸ University build paused':'⚙ Your university is being built'}</b>
        <span className={"badge mono "+(paused?'coral':'accent')}>{b.done}/{b.total} classes</span>
      </div>
      <Bar value={b.done} max={Math.max(1,b.total)} />
      <p className="muted" style={{fontSize:13,marginTop:10}}>{b.message}</p>
      {paused
        ? <button className="btn primary" style={{marginTop:10}} onClick={resume}>Resume the build →</button>
        : <p className="faint mono" style={{fontSize:11,marginTop:6}}>Syllabi, textbooks, full 101 classes and exams — authored live by your faculty. This page updates as they work.</p>}
    </div>
  );
}
function Dashboard({ terms, nav, data }){
  const S = data.STUDENT;
  const ranks = terms.ranks;
  const L = data.LESSON;
  return (
    <div className="screen-pad">
      <BuildBanner data={data} />
      <div className="dash-hero">
        <div>
          <div className="eyebrow" style={{marginBottom:10}}>{terms.semester} · week {S.week} of {S.weeks}</div>
          <h1 style={{fontSize:30}}>Welcome back, {S.name}.</h1>
          <p className="muted" style={{marginTop:8,fontSize:16,maxWidth:'52ch'}}>{S.mission}</p>
        </div>
        {L
          ? <button className="btn primary" onClick={()=>nav('lesson')}>Continue · {L.title} →</button>
          : <button className="btn primary" onClick={()=>nav('guide')}>Ask your {terms.guide} →</button>}
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
            {L ? (
              <React.Fragment>
                <div className="row" style={{gap:12}}>
                  <Avatar name={L.author} hue="#f5a623" size={40} sq />
                  <div><b style={{fontFamily:'var(--font-d)',fontSize:15}}>{L.title}</b><div className="faint" style={{fontSize:12,fontFamily:'var(--font-m)'}}>{terms.professor} {L.author} · {L.read}</div></div>
                </div>
                <p className="muted" style={{fontSize:13,margin:'13px 0 16px'}}>{(L.intro||'').slice(0,110)}…</p>
                <button className="btn primary" style={{width:'100%',justifyContent:'center'}} onClick={()=>nav('lesson')}>Read the lesson →</button>
              </React.Fragment>
            ) : (
              <React.Fragment>
                <p className="muted" style={{fontSize:13.5,margin:'4px 0 14px'}}>
                  {data.BUILD && !data.BUILD.finished
                    ? 'Your professors are writing your first lessons right now — they’ll appear here.'
                    : 'No lesson yet — ask your '+terms.guide+' anything and a professor will write one for you.'}
                </p>
                <button className="btn primary" style={{width:'100%',justifyContent:'center'}} onClick={()=>nav('guide')}>Ask the {terms.guide} →</button>
              </React.Fragment>
            )}
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
                  <span className="cm-title">
                    {m.title}
                    {m.topics && m.topics.length>0 &&
                      <span className="faint" style={{display:'block',fontSize:11,marginTop:3,lineHeight:1.5}}>{m.topics.join('  ·  ')}</span>}
                  </span>
                  <span className={"badge "+eb[0]} style={{marginLeft:'auto',flexShrink:0}}>{terms.exam}: {eb[1]}</span>
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
  const { useState } = React;
  const cols = [
    { key:'lessons', label:'Lessons' }, { key:'doing', label:'Doing' },
    { key:'submitted', label:'Submitted' }, { key:'graded', label:'Graded' }
  ];
  // Stable color per subject (from the curriculum hue, with a fallback palette).
  const PAL = ['#f5a623','#3b82f6','#9b6cff','#2dd4bf','#f0846b','#46d6ad','#e6c06a','#6e8efb'];
  const hueFor = {};
  (data.SUBJECTS||[]).forEach((s,i)=>{ hueFor[s.title] = s.hue || PAL[i%PAL.length]; });
  const subjectHue = (name)=> hueFor[name] || PAL[(Math.abs((name||'').split('').reduce((a,ch)=>a+ch.charCodeAt(0),0)))%PAL.length];

  const allSubjects = Array.from(new Set(
    cols.flatMap(c=>(data.KANBAN[c.key]||[]).map(t=>t.subject)).filter(Boolean)));
  const [filter,setFilter] = useState('all');
  const match = (t)=> filter==='all' || t.subject===filter;

  return (
    <div className="screen-pad wide">
      <div className="row" style={{justifyContent:'space-between',marginBottom:12,flexWrap:'wrap',gap:10}}>
        <div><h1 style={{fontSize:26}}>My Board</h1><p className="muted" style={{fontSize:14,marginTop:4}}>Tasks across your {terms.semester.toLowerCase()} · color-coded by subject</p></div>
        <span className="badge accent mono">⛁ kanban-mcp · live</span>
      </div>

      {/* Subject filter + legend */}
      <div className="row" style={{gap:8,marginBottom:16,flexWrap:'wrap'}}>
        <button className={"ex-chip"+(filter==='all'?' on-chip':'')} onClick={()=>setFilter('all')}
          style={filter==='all'?{color:'var(--accent)',borderColor:'var(--accent-line)',background:'var(--accent-soft)'}:{}}>All subjects</button>
        {allSubjects.map(s=>(
          <button key={s} className={"ex-chip"+(filter===s?' on-chip':'')} onClick={()=>setFilter(s)}
            style={{display:'inline-flex',alignItems:'center',gap:7,
              ...(filter===s?{borderColor:subjectHue(s),background:'rgba(255,255,255,.04)'}:{})}}>
            <span style={{width:9,height:9,borderRadius:3,background:subjectHue(s),display:'inline-block'}}/>{s}
          </button>
        ))}
      </div>

      <div className="kanban">
        {cols.map(c=>{
          const cards = (data.KANBAN[c.key]||[]).filter(match);
          return (
            <div key={c.key} className="kan-col">
              <div className="kan-head"><span>{c.label}</span><span className="kan-n">{cards.length}</span></div>
              <div className="kan-cards">
                {cards.map(t=>{
                  const hue = subjectHue(t.subject);
                  return (
                    <div key={t.id} className={"kan-card"+(t.type==='lesson'?' lesson':'')}
                      onClick={()=>openTask(t,nav)}
                      style={{borderLeft:'3px solid '+hue, paddingLeft:11}}>
                      <div className="row" style={{justifyContent:'space-between',marginBottom:8}}>
                        <span className="badge" style={{color:hue,borderColor:hue,background:'transparent'}}>{t.subject||t.type}</span>
                        {t.tool && <span className="badge gold mono">tool</span>}
                        {t.good===true && <span className="badge mint">passed</span>}
                        {t.good===false && <span className="badge coral">retry</span>}
                      </div>
                      <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:13.5,lineHeight:1.3}}>{t.title}</div>
                      <div className="faint mono" style={{fontSize:11,marginTop:9}}>{t.type} · {t.meta}</div>
                    </div>
                  );
                })}
                {!cards.length && <div className="faint mono" style={{fontSize:11,padding:'10px 4px'}}>nothing here</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---------- Lesson (blog reader) ---------- */
function LessonScreen({ terms, nav, data, lessonOpen }){
  const L = (lessonOpen && typeof lessonOpen==='object' && lessonOpen.title) ? lessonOpen : data.LESSON;
  if(!L){
    return (
      <div className="screen-pad">
        <div className="card" style={{textAlign:'center',padding:'60px 20px'}}>
          <h2 style={{fontSize:22}}>No lesson here yet</h2>
          <p className="muted" style={{marginTop:8}}>Ask your {terms.guide} anything — the right {terms.professor.toLowerCase()} will write one for you.</p>
          <button className="btn primary" style={{marginTop:16}} onClick={()=>nav('guide')}>Ask the {terms.guide} →</button>
        </div>
      </div>
    );
  }
  return <LessonBody key={L.id||L.title} terms={terms} nav={nav} L={L} />;
}
/* Mermaid architecture diagrams — bad LLM syntax must never break the page. */
function MermaidBlock({ code, idx }){
  const ref = useRefL(null);
  const [failed,setFailed] = useStateL(false);
  useEffectL(()=>{
    if(!window.mermaid || !ref.current){ setFailed(true); return; }
    try{
      window.mermaid.initialize({ startOnLoad:false, theme:'dark', securityLevel:'loose' });
      window.mermaid.render('aula-mmd-'+idx+'-'+Math.floor(Math.random()*1e6), code)
        .then(r=>{ if(ref.current) ref.current.innerHTML = r.svg; })
        .catch(()=>setFailed(true));
    }catch(e){ setFailed(true); }
  },[code]);
  if(failed) return null;
  return <div ref={ref} style={{margin:'14px 0',padding:'14px',background:'rgba(255,255,255,.025)',border:'1px solid var(--line)',borderRadius:12,overflowX:'auto'}} />;
}

/* ---------- Narrated lecture mode: watch + listen (browser TTS, $0) ---------- */
function buildSlides(L, terms){
  const slides = [];
  slides.push({ title:L.title, kind:'title',
    bullets:(L.objectives||[]).slice(0,5),
    script:`${L.title}. ${L.intro||''} ${ (L.objectives||[]).length?('In this class you will: '+L.objectives.join('; ')+'.'):''}` });
  (L.sections||[]).forEach(s=>{
    const paras = s.paras || (s.p?[s.p]:[]);
    slides.push({ title:s.h, kind:'section',
      bullets: paras.map(p=> p.length>160 ? p.slice(0,157)+'…' : p),
      code:s.code, diagram:s.diagram,
      script:`${s.h}. ${paras.join(' ')}` });
  });
  if((L.takeaways||[]).length) slides.push({ title:'Key takeaways', kind:'end',
    bullets:L.takeaways, script:'To recap. '+L.takeaways.join('. ') });
  return slides;
}
function LecturePlayer({ L, terms, onClose }){
  const slides = buildSlides(L, terms);
  const [i,setI] = useStateL(0);
  const [playing,setPlaying] = useStateL(true);
  const hasTTS = typeof window!=='undefined' && 'speechSynthesis' in window;
  const s = slides[i];
  const go = (n)=>{ setI(Math.max(0,Math.min(slides.length-1,n))); };
  function speak(idx, autoadvance){
    if(!hasTTS) return;
    try{
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(slides[idx].script||slides[idx].title);
      u.rate = 1.0;
      u.onend = ()=>{ if(autoadvance && idx < slides.length-1) setI(idx+1); else if(idx>=slides.length-1) setPlaying(false); };
      window.speechSynthesis.speak(u);
    }catch(e){}
  }
  useEffectL(()=>{ if(playing) speak(i, true); else if(hasTTS){ try{window.speechSynthesis.cancel();}catch(e){} } },[i,playing]);
  useEffectL(()=>()=>{ if(hasTTS){ try{window.speechSynthesis.cancel();}catch(e){} } },[]);
  useEffectL(()=>{
    const k=(e)=>{ if(e.key==='ArrowRight') go(i+1); if(e.key==='ArrowLeft') go(i-1); if(e.key==='Escape') onClose(); };
    window.addEventListener('keydown',k); return ()=>window.removeEventListener('keydown',k);
  },[i]);
  return (
    <div style={{position:'fixed',inset:0,zIndex:200,background:'var(--bg)',display:'flex',flexDirection:'column'}}>
      <div className="row" style={{justifyContent:'space-between',padding:'14px 22px',borderBottom:'1px solid var(--line)'}}>
        <div className="row" style={{gap:10}}><span className="badge accent mono">▶ Lecture · {terms.professor} {L.author}</span><span className="faint mono" style={{fontSize:11}}>slide {i+1}/{slides.length}</span></div>
        <button className="btn ghost" onClick={onClose}>✕ Exit lecture</button>
      </div>
      <div style={{flex:1,overflow:'auto',display:'flex',flexDirection:'column',justifyContent:'center',alignItems:'center',padding:'30px 24px'}}>
        <div style={{maxWidth:820,width:'100%'}}>
          <div className="eyebrow" style={{marginBottom:14}}>{s.kind==='title'?'Lecture begins':s.kind==='end'?'Wrap up':L.subject}</div>
          <h1 style={{fontSize:38,lineHeight:1.1,marginBottom:22}}>{s.title}</h1>
          {(s.bullets||[]).map((b,j)=>(
            <div key={j} className="row" style={{gap:12,marginBottom:14,alignItems:'flex-start'}}>
              <span className="dot" style={{background:'var(--accent)',marginTop:10,flexShrink:0}}/>
              <span style={{fontSize:18,lineHeight:1.5}}>{b}</span>
            </div>
          ))}
          {s.code && s.code.snippet && <pre className="cc-code" style={{borderRadius:10,padding:'12px 14px',margin:'14px 0',whiteSpace:'pre-wrap'}}>{s.code.snippet}</pre>}
          {s.diagram && <MermaidBlock code={s.diagram} idx={'lec'+i} />}
        </div>
      </div>
      <div className="row" style={{justifyContent:'center',gap:12,padding:'16px 22px',borderTop:'1px solid var(--line)'}}>
        <button className="btn ghost" onClick={()=>go(i-1)} disabled={i===0}>← Prev</button>
        {hasTTS && <button className="btn ghost" onClick={()=>setPlaying(p=>!p)}>{playing?'⏸ Pause':'▶ Play'}</button>}
        {i < slides.length-1
          ? <button className="btn primary" onClick={()=>go(i+1)}>Next →</button>
          : <button className="btn primary" onClick={onClose}>Finish</button>}
      </div>
      {!hasTTS && <div className="faint mono" style={{textAlign:'center',fontSize:11,paddingBottom:10}}>Narration unavailable in this browser — use Next/Prev to advance.</div>}
    </div>
  );
}

function LessonBody({ terms, nav, L }){
  const [ans,setAns] = useStateL('');
  const [sent,setSent] = useStateL(false);
  const [lecture,setLecture] = useStateL(false);
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
  if(lecture) return <LecturePlayer L={L} terms={terms} onClose={()=>setLecture(false)} />;
  return (
    <div className="screen-pad">
      <button className="btn ghost" style={{marginBottom:18,padding:'8px 14px',fontSize:13}} onClick={()=>nav('board')}>← Board</button>
      <div className="lesson">
        <div className="eyebrow" style={{marginBottom:14}}>{L.subject} · authored lesson</div>
        <h1 style={{fontSize:34,lineHeight:1.1}}>{L.title}</h1>
        <div className="row" style={{gap:11,margin:'16px 0 18px'}}>
          <Avatar name={L.author} hue="#f5a623" size={34} />
          <div><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{terms.professor} {L.author}</b><div className="faint mono" style={{fontSize:11}}>{L.read} read · wrote this for you</div></div>
        </div>

        {/* This class — the parts a real course bundles together */}
        <div className="row" style={{gap:8,marginBottom:24,flexWrap:'wrap'}}>
          <button className="btn primary" style={{fontSize:13}} onClick={()=>setLecture(true)}>▶ Lecture mode</button>
          <button className="btn ghost" style={{fontSize:13}} onClick={()=>nav('lab',{subject:L.subject,topic:L.title})}>🎮 Play the game</button>
          <button className="btn ghost" style={{fontSize:13}} onClick={()=>nav('lab',{subject:L.subject,topic:L.title,mode:'lab'})}>🧩 Quick lab</button>
          {L.refs && L.refs.length>0 && <span className="badge mono">📖 {L.refs.length} readings</span>}
          <span className="badge mono">✓ probe below</span>
        </div>

        <p className="lesson-intro">{L.intro}</p>

        {L.objectives && L.objectives.length>0 && (
          <div className="card" style={{margin:'4px 0 22px',padding:'14px 18px'}}>
            <div className="eyebrow" style={{marginBottom:8}}>What you'll learn in this class</div>
            {L.objectives.map((o,i)=>(
              <div key={i} className="row" style={{gap:9,marginBottom:6,alignItems:'flex-start'}}>
                <span className="dot" style={{background:'var(--accent)',marginTop:7,flexShrink:0}}/>
                <span style={{fontSize:13.5}}>{o}</span>
              </div>
            ))}
          </div>
        )}

        {L.sections.map((s,i)=>(
          <div key={i} className="lesson-sec">
            <h3>{s.h}</h3>
            {(s.paras || (s.p?[s.p]:[])).map((p,j)=><p key={j}>{p}</p>)}
            {s.code && s.code.snippet && (
              <pre className="cc-code" style={{borderRadius:10,padding:'12px 14px',margin:'10px 0',overflowX:'auto',whiteSpace:'pre-wrap'}}>{s.code.snippet}</pre>
            )}
            {s.diagram && <MermaidBlock code={s.diagram} idx={i} />}
          </div>
        ))}

        {L.takeaways && L.takeaways.length>0 && (
          <div className="card mint-note" style={{margin:'8px 0 18px',padding:'14px 18px'}}>
            <div className="eyebrow" style={{marginBottom:8}}>Key takeaways</div>
            {L.takeaways.map((t,i)=>(
              <div key={i} className="row" style={{gap:9,marginBottom:6,alignItems:'flex-start'}}>
                <span style={{color:'var(--mint)',fontSize:13,flexShrink:0}}>✓</span>
                <span style={{fontSize:13.5}}>{t}</span>
              </div>
            ))}
          </div>
        )}

        {L.refs && L.refs.length > 0 && (
          <div className="card" style={{margin:'18px 0',padding:'14px 16px'}}>
            <div className="eyebrow" style={{marginBottom:8}}>Taught from these sources · gathered by {terms.professor} {L.author}</div>
            <div className="col" style={{gap:6}}>
              {L.refs.slice(0,6).map((r,i)=>(
                <a key={i} href={r.url||'#'} target="_blank" rel="noreferrer" className="row" style={{gap:8,textDecoration:'none',color:'inherit'}}>
                  <span className="badge mono" style={{minWidth:64,justifyContent:'center'}}>{r.kind}</span>
                  <span style={{fontSize:12.5}} className="muted">{r.title}</span>
                </a>
              ))}
            </div>
          </div>
        )}

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

/* ---------- Library (lessons + scraped materials) ---------- */
const MAT_ICON = { textbook:'📕', book:'📚', paper:'📄', article:'📖', link:'🔗', curriculum:'🏛' };
function LibraryScreen({ terms, nav, data }){
  const [q,setQ] = useStateL('');
  const [subj,setSubj] = useStateL('all');
  const [tab,setTab] = useStateL('lessons');
  const [genId,setGenId] = useStateL(null);   // catalog id being written on demand
  const materials = data.MATERIALS || [];
  const source = tab==='lessons' ? data.LIBRARY : materials;
  const subjects = ['all', ...new Set(source.map(l=>l.subject))];
  const ql = q.toLowerCase();
  const items = source.filter(l=>
    (subj==='all'||l.subject===subj) &&
    ((l.title||'').toLowerCase().includes(ql)||(l.author||l.authors||'').toLowerCase().includes(ql)));
  const readyCount = data.LIBRARY.filter(l=>l.state==='ready'||l.state==='new'||l.state==='read'||l.state==='unread').length;

  function openOrWrite(l){
    const isReady = l.state==='ready'||l.state==='new'||l.state==='read'||l.state==='unread';
    if(isReady){
      openTask({type:'lesson',lesson_id:(window.AULA_LIVE?(l.lesson_id||l.id):null)},nav);
      return;
    }
    // planned/writing: have the professor write this class right now
    if(l.catalog_id && window.AULA_LIVE && genId===null){
      setGenId(l.catalog_id);
      window.AULA_API.catalogGenerate(l.catalog_id)
        .then(r=>{ nav('lesson', r.lesson); window.AULA_API.hydrate(); })
        .catch(()=>{})
        .finally(()=>setGenId(null));
    }
  }

  return (
    <div className="screen-pad wide">
      <div className="row" style={{justifyContent:'space-between',marginBottom:16,flexWrap:'wrap',gap:12}}>
        <div><h1 style={{fontSize:26}}>Library</h1><p className="muted" style={{fontSize:14,marginTop:4}}>{readyCount} of {data.LIBRARY.length} classes ready · {materials.length} materials your faculty gathered</p></div>
        <input className="lib-search" value={q} onChange={e=>setQ(e.target.value)} placeholder="Search…" />
      </div>
      <div className="row" style={{gap:8,marginBottom:14}}>
        <div className="seg">
          <button className={tab==='lessons'?'on':''} onClick={()=>{setTab('lessons');setSubj('all');}}>Classes · {readyCount}/{data.LIBRARY.length}</button>
          <button className={tab==='materials'?'on':''} onClick={()=>{setTab('materials');setSubj('all');}}>Materials · {materials.length}</button>
        </div>
      </div>
      <div className="row" style={{gap:8,marginBottom:18,flexWrap:'wrap'}}>
        {subjects.map(s=><button key={s} className={"ex-chip"+(subj===s?' on-chip':'')} onClick={()=>setSubj(s)} style={subj===s?{color:'var(--accent)',borderColor:'var(--accent-line)',background:'var(--accent-soft)'}:{}}>{s==='all'?'All subjects':s}</button>)}
      </div>
      {tab==='lessons' ? (
        <div className="lib-grid">
          {items.map(l=>{
            const isReady = l.state==='ready'||l.state==='new'||l.state==='read'||l.state==='unread';
            const isWriting = l.state==='writing' || genId===l.catalog_id;
            const isPlanned = l.state==='planned' && !isWriting;
            return (
              <div key={(l.catalog_id||'')+'-'+l.id} className={"lib-card"+(l.state==='locked'?' locked':'')}
                   style={isPlanned?{opacity:.75}:{}}
                   onClick={()=>l.state!=='locked'&&openOrWrite(l)}>
                <div className="row" style={{justifyContent:'space-between',marginBottom:12}}>
                  <span className="badge mono">{l.tag}</span>
                  {l.state==='new' && <span className="badge accent">new</span>}
                  {isWriting && <span className="badge accent mono">✍ writing…</span>}
                  {isPlanned && <span className="badge gold mono">✍ write it now</span>}
                  {l.state==='locked' && <span className="badge">🔒</span>}
                </div>
                <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:15,lineHeight:1.25,marginBottom:10}}>{l.title}</div>
                <div className="row" style={{gap:8}}><Avatar name={l.author} hue={l.author==='Mei'?'#f5a623':'#3b82f6'} size={22}/><span className="faint mono" style={{fontSize:11}}>{l.author} · {l.module||l.read}</span></div>
              </div>
            );
          })}
          {!items.length && <div className="muted" style={{padding:20,fontSize:13.5}}>No classes yet — ask your {terms.guide} and a {terms.professor.toLowerCase()} will write one.</div>}
        </div>
      ) : (
        <div className="lib-grid">
          {items.map(m=>(
            <a key={m.id} className="lib-card" href={m.url||'#'} target="_blank" rel="noreferrer" style={{textDecoration:'none',color:'inherit',display:'block'}}>
              <div className="row" style={{justifyContent:'space-between',marginBottom:12}}>
                <span className="badge mono">{MAT_ICON[m.kind]||'🔗'} {m.kind}</span>
                {(m.tools||[]).map(t=><span key={t} className="badge gold mono">{t}</span>)}
              </div>
              <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:14.5,lineHeight:1.25,marginBottom:8}}>{m.title}</div>
              {m.summary && <p className="muted" style={{fontSize:12,marginBottom:8,maxHeight:54,overflow:'hidden'}}>{m.summary}</p>}
              <div className="faint mono" style={{fontSize:11}}>{m.authors||'—'} · added by {m.addedBy||'faculty'}</div>
            </a>
          ))}
          {!items.length && <div className="muted" style={{padding:20,fontSize:13.5}}>No materials yet — your professors gather books, papers and articles during the college build.</div>}
        </div>
      )}
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

/* ---------- Schedule (week-by-week university timetable) ---------- */
function ScheduleScreen({ terms, nav, data }){
  const S = data.STUDENT;
  const weeks = S.weeks || 12;
  const now = S.week || 1;
  const PAL = ['#f5a623','#3b82f6','#9b6cff','#2dd4bf','#f0846b','#46d6ad','#e6c06a','#6e8efb'];
  // Spread each subject's modules evenly across the semester → a real timetable.
  const byWeek = {};
  (data.SUBJECTS||[]).forEach((s,si)=>{
    const hue = s.hue || PAL[si%PAL.length];
    const mods = s.modules||[];
    mods.forEach((m,mi)=>{
      const wk = Math.max(1, Math.min(weeks, Math.round((mi+1)/Math.max(1,mods.length)*weeks)));
      (byWeek[wk] = byWeek[wk]||[]).push({ subject:s.title, hue, module:m.title, status:m.status, idx:mi+1 });
    });
  });
  const list = Array.from({length:weeks},(_,i)=>i+1);
  return (
    <div className="screen-pad">
      <div className="row" style={{justifyContent:'space-between',alignItems:'flex-end',marginBottom:18,flexWrap:'wrap',gap:12}}>
        <div>
          <div className="eyebrow" style={{marginBottom:8}}>{terms.semester} schedule · designed by {terms.principal}</div>
          <h1 style={{fontSize:26}}>When to study what</h1>
          <p className="muted" style={{fontSize:14,marginTop:6}}>Your {weeks}-week plan. Each week tells you which class to start — you're in <b style={{color:'var(--accent)'}}>week {now}</b>.</p>
        </div>
      </div>
      <div className="col" style={{gap:10}}>
        {list.map(wk=>{
          const items = byWeek[wk]||[];
          const isNow = wk===now, past = wk<now;
          return (
            <div key={wk} className="card" style={{padding:'12px 16px',opacity:past?0.6:1,
              borderColor:isNow?'var(--accent-line)':'var(--line)',
              background:isNow?'var(--accent-soft)':undefined}}>
              <div className="row" style={{gap:14,alignItems:'flex-start'}}>
                <div style={{textAlign:'center',minWidth:52}}>
                  <div className="faint mono" style={{fontSize:10}}>WEEK</div>
                  <div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:22,color:isNow?'var(--accent)':'inherit'}}>{wk}</div>
                  {isNow && <div className="badge accent mono" style={{fontSize:9,marginTop:2}}>now</div>}
                </div>
                <div style={{flex:1}}>
                  {items.length? items.map((it,j)=>(
                    <div key={j} className="row" style={{gap:9,marginBottom:j<items.length-1?8:0,alignItems:'center'}}>
                      <span style={{width:9,height:9,borderRadius:3,background:it.hue,flexShrink:0}}/>
                      <span className="faint mono" style={{fontSize:11,minWidth:90}}>{it.subject}</span>
                      <span style={{flex:1,fontSize:13.5,fontFamily:'var(--font-d)'}}>{terms.module} {it.idx}: {it.module}</span>
                      {it.status==='done' && <span className="badge mint">done</span>}
                      {it.status==='active' && <span className="badge accent">in progress</span>}
                      {isNow && it.status!=='done' && <button className="btn primary" style={{fontSize:12,padding:'5px 12px'}} onClick={()=>nav('library')}>Start →</button>}
                    </div>
                  )) : <span className="faint" style={{fontSize:12.5}}>Catch-up / review week</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---------- Lab / game (learn by playing) ---------- */
function shuffle(a){ const r=a.slice(); for(let i=r.length-1;i>0;i--){ const j=Math.floor((i+1)* (Math.sin(i*99.7)*0.5+0.5)); const t=r[i]; r[i]=r[j]; r[j]=t; } return r; }
function LabScreen({ terms, nav, data, payload }){
  const { useState, useEffect } = React;
  const subject = (payload && payload.subject) || (data.SUBJECTS[0]||{}).title || '';
  const topic = (payload && payload.topic) || subject;
  const gameMode = !(payload && payload.mode==='lab');   // default: an actual game
  const [lab,setLab] = useState(null);
  const [err,setErr] = useState('');
  const [done,setDone] = useState(null);   // {score}

  function load(){
    setLab(null); setErr(''); setDone(null);
    if(!window.AULA_API || !window.AULA_LIVE){ setErr('Connect the backend to play.'); return; }
    const gen = gameMode ? window.AULA_API.gameGenerate(subject, topic) : window.AULA_API.labGenerate(subject, topic);
    gen.then(r=>setLab(r.lab)).catch(e=>setErr(String(e.message||e)));
  }
  useEffect(()=>{ load(); },[subject,topic,gameMode]);

  function finish(score){
    setDone({score});
    if(window.AULA_API && window.AULA_LIVE) window.AULA_API.labComplete(subject, score, topic).then(()=>window.AULA_API.hydrate()).catch(()=>{});
  }
  const isGame = lab && lab.kind==='arcade';

  return (
    <div className={"screen-pad"+(isGame?' wide':'')}>
      <button className="btn ghost" style={{marginBottom:18,padding:'8px 14px',fontSize:13}} onClick={()=>nav('library')}>← Library</button>
      <div className="eyebrow" style={{marginBottom:8}}>{subject} · {isGame?'play to learn':'interactive lab'}</div>
      <h1 style={{fontSize:28,marginBottom:6}}>{lab?lab.title:topic}</h1>
      {err && <div className="card coral-note" style={{marginTop:14}}><p className="muted" style={{fontSize:13.5}}>{err}</p></div>}
      {!lab && !err && <div className="card" style={{marginTop:14,padding:30,textAlign:'center'}}><p className="muted">{gameMode?'Your professor is building a game for this chapter…':'The professor is designing your lab…'}</p></div>}
      {done ? (
        <div className={"card "+(done.score>=60?'mint-note':'coral-note')} style={{marginTop:16}}>
          <b style={{fontFamily:'var(--font-d)',fontSize:16}}>{done.score>=60?'Chapter cleared — you’ve got it.':'Good run — play again to master it.'}</b>
          <div className="row" style={{gap:10,margin:'10px 0'}}>
            <span className={"badge "+(done.score>=60?'mint':'coral')}>{done.score}%</span>
            <span className="badge accent mono">+{20+Math.floor(done.score/5)} XP</span>
          </div>
          <button className="btn primary" onClick={load}>Play again</button>
          <button className="btn ghost" style={{marginLeft:8}} onClick={()=>nav('library')}>Back to library</button>
        </div>
      ) : lab && (isGame ? <ArcadeGame lab={lab} onFinish={finish} /> : <LabRunner lab={lab} onFinish={finish} terms={terms} />)}
    </div>
  );
}
/* arcade — a real, playable LLM-authored game, run in a sandboxed iframe */
function ArcadeGame({ lab, onFinish }){
  const { useEffect, useRef, useState } = React;
  const frame = useRef(null);
  const [ended,setEnded] = useState(false);
  useEffect(()=>{
    function onMsg(e){
      const d = e.data;
      if(d && d.aula==='score'){ setEnded(true); onFinish(Math.max(0,Math.min(100, parseInt(d.value)||0))); }
    }
    window.addEventListener('message', onMsg);
    return ()=>window.removeEventListener('message', onMsg);
  },[]);
  return (
    <div className="card" style={{marginTop:16,padding:14}}>
      <div className="row" style={{gap:10,flexWrap:'wrap',marginBottom:10}}>
        {lab.controls && <span className="badge accent mono">🎮 {lab.controls}</span>}
        {lab.goal && <span className="faint" style={{fontSize:12.5}}>{lab.goal}</span>}
      </div>
      <iframe ref={frame} title="game" sandbox="allow-scripts"
        srcDoc={lab.html}
        style={{width:'100%',height:460,border:'1px solid var(--line)',borderRadius:12,background:'#000',display:'block'}}
        tabIndex={0} onLoad={e=>{ try{ e.target.contentWindow.focus(); }catch(_){} }} />
      <div className="row" style={{justifyContent:'space-between',marginTop:10}}>
        <span className="faint mono" style={{fontSize:11}}>Click the game, then use the keys. Finishing reports your score automatically.</span>
        {!ended && <button className="btn ghost" onClick={()=>onFinish(60)}>I'm done</button>}
      </div>
    </div>
  );
}
function LabRunner({ lab, onFinish, terms }){
  if(lab.kind==='sort') return <SortGame lab={lab} onFinish={onFinish} />;
  if(lab.kind==='steps') return <StepsGame lab={lab} onFinish={onFinish} />;
  if(lab.kind==='scenario') return <ScenarioGame lab={lab} onFinish={onFinish} />;
  if(lab.kind==='quiz') return <QuizGame lab={lab} onFinish={onFinish} />;
  if(lab.kind==='match') return <MatchGame lab={lab} onFinish={onFinish} />;
  if(lab.kind==='order') return <OrderGame lab={lab} onFinish={onFinish} />;
  if(lab.kind==='bugfix') return <BugfixGame lab={lab} onFinish={onFinish} />;
  return <div className="card" style={{marginTop:16,padding:20}}><p className="muted">This lab type isn’t supported yet.</p></div>;
}
/* sort — arcade flash game: drop each item into the right bucket, beat the clock */
function SortGame({ lab, onFinish }){
  const { useState, useEffect, useRef } = React;
  const items = lab.items||[];
  const TOTAL_T = Math.max(30, items.length*7);
  const [idx,setIdx] = useState(0);
  const [score,setScore] = useState(0);
  const [combo,setCombo] = useState(0);
  const [correct,setCorrect] = useState(0);
  const [fb,setFb] = useState(null);          // {ok, why}
  const [t,setT] = useState(TOTAL_T);
  const [over,setOver] = useState(false);
  const lockRef = useRef(false);
  const finishedRef = useRef(false);

  useEffect(()=>{
    if(over) return;
    const id = setInterval(()=>setT(x=>{ if(x<=1){ clearInterval(id); end(correct); return 0; } return x-1; }),1000);
    return ()=>clearInterval(id);
  },[over]);

  function end(c){ if(finishedRef.current) return; finishedRef.current=true; setOver(true); onFinish(Math.round(c/items.length*100)); }
  function pick(cat){
    if(lockRef.current || over || idx>=items.length) return;
    const it = items[idx];
    const ok = cat===it.category;
    lockRef.current = true;
    if(ok){ const pts=10*(1+Math.floor(combo*0.5)); setScore(s=>s+pts); setCombo(c=>c+1); setCorrect(c=>c+1); }
    else { setCombo(0); }
    setFb({ ok, why: it.why || (ok?'Correct.':'Not quite — '+it.text+' belongs in '+it.category+'.') });
    setTimeout(()=>{
      setFb(null); lockRef.current=false;
      const n = idx+1; setIdx(n);
      if(n>=items.length) end(ok?correct+1:correct);
    }, 1100);
  }
  const it = items[idx];
  const pct = Math.round(t/TOTAL_T*100);
  return (
    <div className="card" style={{marginTop:16}}>
      <div className="row" style={{justifyContent:'space-between',marginBottom:6}}>
        <span className="faint mono" style={{fontSize:11}}>{lab.intro} · drop it in the right bucket</span>
        <div className="row" style={{gap:12}}>
          {combo>1 && <span className="badge accent mono">🔥 {combo}× combo</span>}
          <span className="badge mono">★ {score}</span>
          <span className="badge mono">{idx}/{items.length}</span>
        </div>
      </div>
      <div className="bar" style={{height:6,marginBottom:18}}><i style={{width:pct+'%',background:pct<25?'var(--coral)':'var(--accent)'}}/></div>

      <div style={{textAlign:'center',minHeight:84,display:'flex',flexDirection:'column',justifyContent:'center',marginBottom:18}}>
        {it && !over ? (
          <div className="card" style={{display:'inline-block',padding:'18px 26px',fontFamily:'var(--font-d)',fontWeight:700,fontSize:20,border:'1px solid var(--accent-line)'}}>{it.text}</div>
        ) : <div className="muted">{over?'Time! Tallying…':'Done'}</div>}
        {fb && <p className="muted" style={{fontSize:13,marginTop:10,color:fb.ok?'var(--mint)':'var(--coral)'}}>{fb.ok?'✓ ':'✗ '}{fb.why}</p>}
      </div>

      <div className="row" style={{gap:10,flexWrap:'wrap',justifyContent:'center'}}>
        {lab.categories.map(c=>(
          <button key={c} className="btn ghost" style={{minWidth:120,justifyContent:'center',fontFamily:'var(--font-d)',fontWeight:600}} onClick={()=>pick(c)} disabled={!!fb||over}>{c}</button>
        ))}
      </div>
    </div>
  );
}

/* steps — predict → reveal → learn the why, one stage at a time */
function StepsGame({ lab, onFinish }){
  const { useState } = React;
  const steps = lab.steps||[];
  const [i,setI] = useState(0); const [picked,setPicked] = useState(null); const [correct,setCorrect] = useState(0);
  const s = steps[i];
  const hasPredict = s && s.predict;
  const revealed = !hasPredict || picked!==null;
  const withPredict = steps.filter(x=>x.predict).length;
  function choose(idx){ if(picked!==null) return; setPicked(idx); if(idx===s.predict.answer) setCorrect(c=>c+1); }
  function next(){
    if(i<steps.length-1){ setI(i+1); setPicked(null); }
    else onFinish(withPredict? Math.round(correct/withPredict*100) : 100);
  }
  return (
    <div className="card" style={{marginTop:16}}>
      <div className="row" style={{justifyContent:'space-between',marginBottom:12}}><span className="faint mono" style={{fontSize:11}}>{lab.intro}</span><span className="badge mono">stage {i+1}/{steps.length}</span></div>
      <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:17,marginBottom:14}}>{s.stage}</div>
      {hasPredict && (
        <div style={{marginBottom:12}}>
          <div className="eyebrow" style={{marginBottom:8}}>{s.predict.q}</div>
          <div className="col" style={{gap:8}}>
            {s.predict.options.map((o,idx)=>{
              const isAns = idx===s.predict.answer;
              return <button key={idx} className="btn ghost" style={{justifyContent:'flex-start',textAlign:'left',borderColor:revealed&&isAns?'var(--mint)':revealed&&idx===picked?'var(--coral)':'var(--line)'}} onClick={()=>choose(idx)}>{o}</button>;
            })}
          </div>
        </div>
      )}
      {revealed && (
        <div className="card mint-note" style={{padding:'12px 16px',marginTop:6}}>
          <p style={{fontSize:13.5,lineHeight:1.5}}>{s.reveal}</p>
        </div>
      )}
      {revealed && <button className="btn primary" style={{marginTop:14}} onClick={next}>{i<steps.length-1?'Next stage →':'Finish →'}</button>}
    </div>
  );
}
/* scenario — decide, then learn the consequence and the reasoning */
function ScenarioGame({ lab, onFinish }){
  const { useState } = React;
  const rounds = lab.rounds||[];
  const [i,setI] = useState(0); const [picked,setPicked] = useState(null); const [correct,setCorrect] = useState(0);
  const r = rounds[i];
  function choose(idx){ if(picked!==null) return; setPicked(idx); if(r.choices[idx].correct) setCorrect(c=>c+1); }
  function next(){ if(i<rounds.length-1){ setI(i+1); setPicked(null); } else onFinish(Math.round(correct/rounds.length*100)); }
  return (
    <div className="card" style={{marginTop:16}}>
      <div className="row" style={{justifyContent:'space-between',marginBottom:12}}><span className="faint mono" style={{fontSize:11}}>{lab.intro}</span><span className="badge mono">{i+1}/{rounds.length}</span></div>
      <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:16,marginBottom:14,lineHeight:1.4}}>{r.situation}</div>
      <div className="col" style={{gap:8}}>
        {r.choices.map((c,idx)=>{
          const reveal = picked!==null;
          return (
            <div key={idx}>
              <button className="btn ghost" style={{width:'100%',justifyContent:'flex-start',textAlign:'left',borderColor:reveal?(c.correct?'var(--mint)':(idx===picked?'var(--coral)':'var(--line)')):'var(--line)'}} onClick={()=>choose(idx)}>
                {reveal && (c.correct?'✓ ':(idx===picked?'✗ ':''))}{c.text}
              </button>
              {reveal && (idx===picked || c.correct) && c.why && <p className="muted" style={{fontSize:12.5,margin:'6px 0 4px 12px'}}>{c.why}</p>}
            </div>
          );
        })}
      </div>
      {picked!==null && <button className="btn primary" style={{marginTop:14}} onClick={next}>{i<rounds.length-1?'Next situation →':'See result →'}</button>}
    </div>
  );
}
function QuizGame({ lab, onFinish }){
  const { useState } = React;
  const qs = lab.questions||[];
  const [i,setI] = useState(0); const [picked,setPicked] = useState(null); const [correct,setCorrect] = useState(0);
  const q = qs[i];
  function choose(idx){ if(picked!==null) return; setPicked(idx); if(idx===q.answer) setCorrect(c=>c+1); }
  function next(){ if(i<qs.length-1){ setI(i+1); setPicked(null); } else { onFinish(Math.round((correct + (picked===q.answer?0:0))/qs.length*100)); } }
  return (
    <div className="card" style={{marginTop:16}}>
      <div className="row" style={{justifyContent:'space-between',marginBottom:10}}><span className="faint mono" style={{fontSize:11}}>{lab.intro}</span><span className="badge mono">{i+1}/{qs.length}</span></div>
      <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:17,marginBottom:14}}>{q.q}</div>
      <div className="col" style={{gap:8}}>
        {q.options.map((o,idx)=>{
          const reveal = picked!==null;
          const isAns = idx===q.answer;
          const cls = reveal ? (isAns?'mint':(idx===picked?'coral':'')) : '';
          return <button key={idx} className={"btn ghost "+cls} style={{justifyContent:'flex-start',textAlign:'left',borderColor:reveal&&isAns?'var(--mint)':reveal&&idx===picked?'var(--coral)':'var(--line)'}} onClick={()=>choose(idx)}>{o}</button>;
        })}
      </div>
      {picked!==null && (
        <div style={{marginTop:14}}>
          <p className="muted" style={{fontSize:13}}>{q.explain}</p>
          <button className="btn primary" style={{marginTop:10}} onClick={next}>{i<qs.length-1?'Next →':'See result →'}</button>
        </div>
      )}
    </div>
  );
}
function MatchGame({ lab, onFinish }){
  const { useState } = React;
  const pairs = lab.pairs||[];
  const [rights] = useState(()=>shuffle(pairs.map((p,i)=>({...p,i}))));
  const [selLeft,setSelLeft] = useState(null);
  const [matched,setMatched] = useState({}); const [wrong,setWrong] = useState(0);
  function clickRight(r){
    if(selLeft===null) return;
    if(pairs[selLeft].right===r.right){ const m={...matched,[selLeft]:true}; setMatched(m); setSelLeft(null);
      if(Object.keys(m).length===pairs.length) onFinish(Math.max(20,Math.round(100 - wrong*10))); }
    else { setWrong(w=>w+1); setSelLeft(null); }
  }
  return (
    <div className="card" style={{marginTop:16}}>
      <div className="faint mono" style={{fontSize:11,marginBottom:12}}>{lab.intro} · click a term, then its match</div>
      <div className="grid" style={{gridTemplateColumns:'1fr 1fr',gap:10}}>
        <div className="col" style={{gap:8}}>
          {pairs.map((p,idx)=>(
            <button key={idx} className={"btn ghost"+(selLeft===idx?' on':'')} disabled={matched[idx]} style={{opacity:matched[idx]?.4:1,justifyContent:'flex-start',borderColor:selLeft===idx?'var(--accent)':'var(--line)'}} onClick={()=>setSelLeft(idx)}>{p.left}</button>
          ))}
        </div>
        <div className="col" style={{gap:8}}>
          {rights.map((r)=>{
            const used = Object.keys(matched).some(k=>pairs[k].right===r.right);
            return <button key={r.i} className="btn ghost" disabled={used} style={{opacity:used?.4:1,justifyContent:'flex-start'}} onClick={()=>clickRight(r)}>{r.right}</button>;
          })}
        </div>
      </div>
      <div className="faint mono" style={{fontSize:11,marginTop:12}}>{Object.keys(matched).length}/{pairs.length} matched{wrong?` · ${wrong} misses`:''}</div>
    </div>
  );
}
function OrderGame({ lab, onFinish }){
  const { useState } = React;
  const correct = lab.steps||[];
  const [order,setOrder] = useState(()=>shuffle(correct.map((s,i)=>({s,i}))));
  const [checked,setChecked] = useState(false);
  function move(idx,dir){ const j=idx+dir; if(j<0||j>=order.length) return; const o=order.slice(); const t=o[idx]; o[idx]=o[j]; o[j]=t; setOrder(o); setChecked(false); }
  const [score,setScore] = useState(null);
  function check(){ setChecked(true); const sc=Math.round(order.filter((o,idx)=>o.i===idx).length/correct.length*100); setScore(sc); onFinish(sc); }
  return (
    <div className="card" style={{marginTop:16}}>
      <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:15,marginBottom:12}}>{lab.prompt}</div>
      <div className="col" style={{gap:8}}>
        {order.map((o,idx)=>(
          <div key={o.i} className="row" style={{gap:8,alignItems:'center',padding:'10px 12px',background:'rgba(255,255,255,.03)',border:'1px solid '+(checked?(o.i===idx?'var(--mint)':'var(--coral)'):'var(--line)'),borderRadius:10}}>
            <span className="mono faint" style={{fontSize:12,minWidth:20}}>{idx+1}</span>
            <span style={{flex:1,fontSize:13.5}}>{o.s}</span>
            <button className="mini-btn" onClick={()=>move(idx,-1)} disabled={idx===0}>↑</button>
            <button className="mini-btn" onClick={()=>move(idx,1)} disabled={idx===order.length-1}>↓</button>
          </div>
        ))}
      </div>
      <button className="btn primary" style={{marginTop:14}} onClick={check}>Check order →</button>
      {checked && lab.explain && <div className="card mint-note" style={{padding:'12px 16px',marginTop:12}}><p style={{fontSize:13.5,lineHeight:1.5}}>{lab.explain}</p></div>}
    </div>
  );
}
function BugfixGame({ lab, onFinish }){
  const { useState } = React;
  const [code,setCode] = useState(lab.broken_code||'');
  const [out,setOut] = useState(null); const [running,setRunning] = useState(false); const [passed,setPassed] = useState(false);
  function run(){
    setRunning(true); setOut(null);
    window.AULA_API.runCode(lab.language||'python', code)
      .then(r=>{ setRunning(false); const txt=[(r.stdout||'').trim(), r.stderr?('— '+r.stderr.trim()):''].filter(Boolean).join('\n'); setOut(txt||'(no output)');
        const ok = r.ok && (!lab.check || (r.stdout||'').includes(lab.check)); setPassed(ok); if(ok) onFinish(100); })
      .catch(()=>{ setRunning(false); setOut('Sandbox offline.'); });
  }
  return (
    <div className="card" style={{marginTop:16}}>
      <div className="faint mono" style={{fontSize:11,marginBottom:6}}>🐞 {lab.task||'Fix the bug so it runs correctly.'}</div>
      <textarea className="cc-code" spellCheck={false} value={code} onChange={e=>setCode(e.target.value)} rows={10} style={{width:'100%',borderRadius:10,padding:'12px 14px'}} />
      <div className="row" style={{justifyContent:'space-between',marginTop:10}}>
        <span className="faint mono" style={{fontSize:11}}>{passed?'✓ fixed!':lab.check?('target output contains: '+lab.check):'make it run'}</span>
        <button className="btn primary" onClick={run} disabled={running}>{running?'Running…':'▶ Run & check'}</button>
      </div>
      {out && <pre className="cc-out">{out}</pre>}
    </div>
  );
}

/* ---------- Review (spaced repetition) ---------- */
function ReviewScreen({ terms, nav, data }){
  const { useState, useEffect } = React;
  const [cards,setCards] = useState(null);
  const [i,setI] = useState(0); const [flipped,setFlipped] = useState(false); const [reviewed,setReviewed] = useState(0);
  useEffect(()=>{
    if(!window.AULA_API || !window.AULA_LIVE){ setCards([]); return; }
    window.AULA_API.reviewDue().then(r=>setCards(r.cards)).catch(()=>setCards([]));
  },[]);
  if(cards===null) return <div className="screen-pad"><div className="card" style={{padding:30,textAlign:'center'}}><p className="muted">Loading your review…</p></div></div>;
  if(!cards.length || i>=cards.length){
    return (
      <div className="screen-pad">
        <h1 style={{fontSize:26}}>Review</h1>
        <div className="card mint-note" style={{marginTop:16}}>
          <b style={{fontFamily:'var(--font-d)',fontSize:15}}>{reviewed?`Done — ${reviewed} cards reviewed.`:'Nothing due right now.'}</b>
          <p className="muted" style={{fontSize:13.5,marginTop:6}}>Flashcards are written into every class. They come back on a spaced schedule so what you learn actually sticks. Read more classes to grow your review deck.</p>
          <button className="btn primary" style={{marginTop:12}} onClick={()=>nav('library')}>Go to the library →</button>
        </div>
      </div>
    );
  }
  const card = cards[i];
  function rate(grade){
    if(window.AULA_API) window.AULA_API.reviewCard(card.id, grade).then(()=>window.AULA_API.hydrate()).catch(()=>{});
    setReviewed(r=>r+1); setFlipped(false); setI(i+1);
  }
  return (
    <div className="screen-pad">
      <div className="row" style={{justifyContent:'space-between',marginBottom:16}}>
        <div><h1 style={{fontSize:26}}>Review</h1><p className="muted" style={{fontSize:14,marginTop:4}}>Spaced repetition · {cards.length-i} due</p></div>
        <span className="badge accent mono">{i+1}/{cards.length}</span>
      </div>
      <div className="card" style={{minHeight:220,display:'flex',flexDirection:'column',justifyContent:'center',alignItems:'center',textAlign:'center',padding:40,cursor:'pointer'}} onClick={()=>setFlipped(f=>!f)}>
        <div className="faint mono" style={{fontSize:11,marginBottom:12}}>{card.subject||''} · {flipped?'answer':'question — click to flip'}</div>
        <div style={{fontFamily:'var(--font-d)',fontWeight:600,fontSize:flipped?18:20,lineHeight:1.4}}>{flipped?card.back:card.front}</div>
      </div>
      {flipped ? (
        <div className="row" style={{gap:10,marginTop:16,justifyContent:'center'}}>
          <button className="btn ghost" style={{borderColor:'var(--coral)'}} onClick={()=>rate('again')}>Again</button>
          <button className="btn ghost" onClick={()=>rate('good')}>Good</button>
          <button className="btn primary" onClick={()=>rate('easy')}>Easy</button>
        </div>
      ) : (
        <div className="row" style={{justifyContent:'center',marginTop:16}}>
          <button className="btn primary" onClick={()=>setFlipped(true)}>Show answer</button>
        </div>
      )}
    </div>
  );
}

/* ---------- Transcript (GPA + degree) ---------- */
function TranscriptScreen({ terms, nav, data }){
  const exams = (data.EXAMS||[]).filter(e=>e.status==='passed'||e.status==='failed');
  const scored = exams.filter(e=>typeof e.score==='number');
  const gpa = scored.length ? (scored.reduce((a,e)=>a+e.score,0)/scored.length) : 0;
  const letter = gpa>=90?'A':gpa>=80?'A−':gpa>=70?'B':gpa>=60?'C':'—';
  const subjects = data.SUBJECTS||[];
  const allDone = subjects.length>0 && subjects.every(s=>s.modules.every(m=>m.status==='done'));
  const passedAll = exams.length>0 && exams.every(e=>e.status==='passed');
  const conferred = allDone && passedAll;
  return (
    <div className="screen-pad">
      <div className="row" style={{justifyContent:'space-between',alignItems:'flex-end',marginBottom:18,flexWrap:'wrap',gap:12}}>
        <div><div className="eyebrow" style={{marginBottom:8}}>Official transcript · {data.STUDENT.name}</div><h1 style={{fontSize:26}}>{data.STUDENT.mission}</h1></div>
        <div style={{textAlign:'right'}}><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:28,color:gpa>=80?'var(--mint)':'var(--accent)'}}>{gpa?gpa.toFixed(0):'—'}<span className="faint" style={{fontSize:14}}>/100</span></div><div className="faint mono" style={{fontSize:10}}>GPA · {letter}</div></div>
      </div>

      {conferred && (
        <div className="card mint-note" style={{marginBottom:18,textAlign:'center',padding:28}}>
          <div style={{fontSize:34,marginBottom:8}}>🎓</div>
          <b style={{fontFamily:'var(--font-d)',fontSize:18}}>Degree conferred</b>
          <p className="muted" style={{fontSize:13.5,marginTop:6}}>You completed every module and passed every exam. {terms.principal} {(data.FACULTY.find(f=>f.role==='principal')||{}).name||''} signs off on “{data.STUDENT.mission}”.</p>
        </div>
      )}

      {subjects.map(s=>{
        const done = s.modules.filter(m=>m.status==='done').length;
        const subjExams = exams.filter(e=>e.subject===s.title);
        return (
          <div key={s.id} className="card" style={{marginBottom:12}}>
            <div className="row" style={{justifyContent:'space-between',marginBottom:8}}>
              <div className="row" style={{gap:10}}><Avatar name={s.profName} hue={s.hue} size={30} sq/><div><b style={{fontFamily:'var(--font-d)',fontSize:14.5}}>{s.title}</b><div className="faint mono" style={{fontSize:11}}>{terms.professor} {s.profName} · {done}/{s.modules.length} modules</div></div></div>
              <div style={{width:120}}><Bar value={done} max={Math.max(1,s.modules.length)} /></div>
            </div>
            {subjExams.length>0 && (
              <div className="row" style={{gap:8,flexWrap:'wrap',marginTop:8}}>
                {subjExams.map(e=><span key={e.id} className={"badge "+(e.status==='passed'?'mint':'coral')+" mono"}>{e.title}: {e.score}%</span>)}
              </div>
            )}
          </div>
        );
      })}
      {!subjects.length && <div className="muted" style={{padding:20}}>No subjects yet — onboard to start your degree.</div>}
    </div>
  );
}

Object.assign(window, {
  SCR_home:Dashboard, SCR_board:MyBoard, SCR_lesson:LessonScreen,
  SCR_guide:GuideScreen, SCR_channel:ChannelScreen, SCR_library:LibraryScreen,
  SCR_progress:ProgressScreen, SCR_curriculum:CurriculumScreen,
  SCR_lab:LabScreen, SCR_review:ReviewScreen, SCR_transcript:TranscriptScreen,
  SCR_schedule:ScheduleScreen
});
