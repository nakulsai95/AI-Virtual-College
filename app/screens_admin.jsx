/* AULA product — assess/faculty/admin screens */
const { useState: useStateAd } = React;

/* ---------- Exams & Results ---------- */
function ExamsScreen({ terms, data }){
  const passed = data.EXAMS.filter(e=>e.status==='passed').length;
  const total = data.EXAMS.filter(e=>e.status!=='upcoming').length;
  return (
    <div className="screen-pad">
      <div className="row" style={{justifyContent:'space-between',marginBottom:18,flexWrap:'wrap',gap:12}}>
        <div><h1 style={{fontSize:26}}>{terms.exam}s & Results</h1><p className="muted" style={{fontSize:14,marginTop:4}}>Graded blind by Rei · pass the bar to advance</p></div>
        <div className="row" style={{gap:18}}>
          <div style={{textAlign:'right'}}><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:22}}>{passed}/{total}</div><div className="faint mono" style={{fontSize:11}}>PASSED</div></div>
        </div>
      </div>
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
      <div className="card coral-note" style={{marginTop:18}}>
        <div className="row" style={{gap:12,alignItems:'flex-start'}}>
          <span className="dot" style={{background:'var(--coral)',marginTop:6}}/>
          <div>
            <b style={{fontFamily:'var(--font-d)',fontSize:14.5}}>SQL & queries — failed at 58% (bar 65)</b>
            <p className="muted" style={{fontSize:13.5,marginTop:6}}>You re-enrol this unit — <b style={{color:'var(--ink)'}}>no penalty to you</b>. {terms.professor} Kenji took the −10 reward; the Provost rewrote his methodology (v3 → v4) to teach JOINs with worked examples first. Try again when ready.</p>
            <button className="btn primary" style={{marginTop:12}}>Re-enrol the unit →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Teacher Board + methodology ---------- */
function TeacherBoard({ terms, data }){
  const profs = data.FACULTY.filter(f=>f.role==='professor');
  const [pid,setPid] = useStateAd(profs[0].id);
  const prof = profs.find(p=>p.id===pid);
  const grade = data.GRADES.find(g=>g.id===pid);
  const cols = [
    { k:'Prep', cards:['Draft REST build brief','Outline testing unit'] },
    { k:'Teaching', cards:['JWTs, end to end','Designing a resource'] },
    { k:'Assessing', cards:['Grade REST routing'] },
    { k:'Reviewing', cards:['Check Alex’s endpoint'] },
  ];
  const methodology = pid==='prof-db'
    ? { v:4, pacing:'slow', seq:'examples → theory', modality:'blog + worked SQL', example:'high', probe:'after-practice', changed:true }
    : { v:3, pacing:'normal', seq:'concept → practice', modality:'blog + diagrams', example:'medium', probe:'after-read', changed:false };
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
            {methodology.changed && <p className="muted" style={{fontSize:12,marginTop:12}}>↳ Provost rewrote this after the mid-term fail — examples now come before theory.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Faculty Grades ---------- */
function FacultyGrades({ terms, data }){
  return (
    <div className="screen-pad">
      <h1 style={{fontSize:26}}>Faculty Grades</h1>
      <p className="muted" style={{fontSize:14,marginTop:4,marginBottom:20}}>Teachers are graded on whether <b style={{color:'var(--ink)'}}>you</b> learn. Reward history, last 10 signals.</p>
      <div className="grid" style={{gridTemplateColumns:'1fr 1fr'}}>
        {data.GRADES.map(g=>{
          const hue = g.id==='prof-api'?'#f5a623':'#3b82f6';
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
  const totalUsed = data.FACULTY.reduce((a,f)=>a+f.budget.used,0);
  const totalCap = data.FACULTY.reduce((a,f)=>a+f.budget.cap,0);
  return (
    <div className="screen-pad wide">
      <div className="row" style={{justifyContent:'space-between',marginBottom:18,flexWrap:'wrap',gap:12}}>
        <div><div className="eyebrow" style={{marginBottom:8}}>{terms.principal}’s command center · you are the board</div><h1 style={{fontSize:26}}>All agents at a glance</h1></div>
        <div className="row" style={{gap:18}}>
          <div style={{textAlign:'right'}}><div style={{fontFamily:'var(--font-d)',fontWeight:700,fontSize:20}}>${totalUsed}<span className="faint" style={{fontSize:13}}>/${totalCap}</span></div><div className="faint mono" style={{fontSize:10}}>BUDGET / MO</div></div>
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
              {f.grade ? <span className={"badge "+(f.grade.score>=80?'mint':'gold')}>{f.grade.letter}</span> : <span className="badge" style={{opacity:.5}}>—</span>}
              <div className="cmd-budget"><div className="bar" style={{width:70}}><i style={{width:(f.budget.used/f.budget.cap*100)+'%'}}/></div><span className="faint mono" style={{fontSize:10}}>${f.budget.used}/{f.budget.cap}</span></div>
              <div className="cmd-actions"><button className="mini-btn">pause</button></div>
            </div>
          ))}
        </div>
        <div className="panel" style={{padding:16}}>
          <div className="row" style={{justifyContent:'space-between',marginBottom:12}}><h3 style={{fontSize:15}}>Reward feed</h3><span className="badge accent mono">live</span></div>
          <div className="col" style={{gap:2}}>
            {data.FEED.map((f,i)=>(
              <div key={i} className="cmd-feed">
                <span className="dot" style={{background:f.kind==='pos'?'var(--mint)':f.kind==='neg'?'var(--coral)':f.kind==='update'?'var(--accent)':'var(--faint)',marginTop:6}}/>
                <div style={{flex:1}}><span style={{fontSize:12.5}}>{f.text}</span><div className="faint mono" style={{fontSize:10,marginTop:2}}>{f.who} · {f.t} ago</div></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Connections (LLM + MCP) ---------- */
function Connections({ terms, data }){
  return (
    <div className="screen-pad">
      <h1 style={{fontSize:26}}>Connections</h1>
      <p className="muted" style={{fontSize:14,marginTop:4,marginBottom:22}}>Any model behind any agent · tools auto-mounted by subject</p>

      <div className="eyebrow" style={{marginBottom:12}}>LLM router · model per agent</div>
      <div className="panel" style={{overflow:'hidden',marginBottom:26}}>
        {data.FACULTY.map(f=>(
          <div key={f.id} className="conn-row">
            <Avatar name={f.name} hue={f.hue} size={30} sq />
            <div style={{flex:1}}><b style={{fontFamily:'var(--font-d)',fontSize:13.5}}>{f.name}</b> <span className="faint mono" style={{fontSize:11}}>{roleTermFor(f.role,terms)}</span></div>
            <div className="model-pick">
              {f.model}
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
