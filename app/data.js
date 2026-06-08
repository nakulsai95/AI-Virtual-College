/* AULA product — mock data (one coherent scenario: learning Backend Python) */
(function(){
  const FACULTY = [
    { id:'principal', role:'principal', name:'Iroha', hue:'#6e8efb', model:'Claude · reasoner', budget:{used:24,cap:60}, status:'active' },
    { id:'provost',   role:'provost',   name:'Daichi', hue:'#46d6ad', model:'Claude · reasoner', budget:{used:9,cap:30}, status:'active' },
    { id:'prof-api',  role:'professor', name:'Mei',    hue:'#f5a623', subject:'APIs & Services', grade:{letter:'A−',score:88,trend:'up'},  model:'GPT · balanced', budget:{used:31,cap:50}, status:'teaching' },
    { id:'prof-db',   role:'professor', name:'Kenji',  hue:'#3b82f6', subject:'Databases',       grade:{letter:'B+',score:78,trend:'flat'}, model:'GPT · balanced', budget:{used:24,cap:50}, status:'teaching' },
    { id:'examiner',  role:'examiner',  name:'Rei',    hue:'#f0846b', model:'Claude · reasoner', budget:{used:12,cap:40}, status:'active' },
    { id:'registrar', role:'registrar', name:'Sora',   hue:'#e6c06a', model:'Llama · fast', budget:{used:4,cap:15}, status:'active' },
    { id:'guide',     role:'guide',     name:'Yuki',   hue:'#9b6cff', model:'Llama · fast', budget:{used:11,cap:20}, status:'online' },
    { id:'counselor', role:'counselor', name:'Haru',   hue:'#2dd4bf', model:'GPT · balanced', budget:{used:6,cap:20}, status:'active' }
  ];

  const SUBJECTS = [
    { id:'apis', title:'APIs & Services', prof:'prof-api', profName:'Mei', progress:62, hue:'#f5a623',
      modules:[
        { id:'m1', title:'HTTP & REST foundations', status:'done', exam:'passed' },
        { id:'m2', title:'Auth: sessions & JWT',     status:'done', exam:'passed' },
        { id:'m3', title:'Build a REST service',     status:'active', exam:'pending' },
        { id:'m4', title:'Testing & deployment',     status:'locked', exam:'pending' }
      ]},
    { id:'db', title:'Databases', prof:'prof-db', profName:'Kenji', progress:40, hue:'#3b82f6',
      modules:[
        { id:'d1', title:'Relational modelling', status:'done', exam:'passed' },
        { id:'d2', title:'SQL & queries',        status:'active', exam:'failed' },
        { id:'d3', title:'Indexing & perf',      status:'locked', exam:'pending' },
        { id:'d4', title:'Transactions',         status:'locked', exam:'pending' }
      ]}
  ];

  const KANBAN = {
    lessons:[
      { id:'t1', title:'Read: JWTs, end to end', subject:'APIs & Services', type:'lesson', meta:'8 min · Mei' },
      { id:'t2', title:'Read: Query planning basics', subject:'Databases', type:'lesson', meta:'6 min · Kenji' }
    ],
    doing:[
      { id:'t3', title:'Build the /users endpoint', subject:'APIs & Services', type:'project', meta:'Python sandbox', tool:true },
      { id:'t4', title:'Write 5 JOIN queries', subject:'Databases', type:'task', meta:'SQL tool', tool:true }
    ],
    submitted:[
      { id:'t5', title:'REST routing exercise', subject:'APIs & Services', type:'task', meta:'awaiting grade' }
    ],
    graded:[
      { id:'t6', title:'Auth flow diagram', subject:'APIs & Services', type:'task', meta:'92% · passed', good:true },
      { id:'t7', title:'Normalize a schema', subject:'Databases', type:'task', meta:'58% · retry', good:false }
    ]
  };

  const LESSON = {
    title:'JWTs, end to end',
    author:'Mei', authorRole:'professor', subject:'APIs & Services', read:'8 min',
    intro:'You asked the Guide how token auth actually works. Here is the whole picture — what a JWT is, how it is signed, and why the server can trust it without storing a session.',
    sections:[
      { h:'What problem it solves', p:'HTTP is stateless: every request arrives with no memory of the last. Sessions solve this by storing state on the server and handing the client a lookup key. JWTs flip that — the proof of identity travels with the request, signed so it cannot be forged.' },
      { h:'Anatomy of a token', p:'A JWT is three base64 parts joined by dots: a header (the algorithm), a payload (claims like the user id and an expiry), and a signature. The signature is the header and payload, hashed with a secret only the server knows.' },
      { h:'Why the server can trust it', p:'On each request the server recomputes the signature from the header and payload it received. If it matches the signature attached, the token is authentic and untampered — no database lookup required. Change one byte of the payload and the signatures diverge.' }
    ],
    probe:{ q:'If a JWT needs no server-side storage, how do you revoke one before it expires?', hint:'Think about what the server still controls.' },
    next:'Build the /users endpoint'
  };

  const GUIDE_THREAD = [
    { who:'user', text:'I don’t get how JWT auth actually works.' },
    { who:'guide', name:'Yuki', text:'Good question — that lives with your APIs & Services professor. Bringing Mei in; she’ll write you a short lesson on it.' },
    { who:'route', text:'Routed to Mei · APIs & Services' },
    { who:'prof', name:'Mei', hue:'#f5a623', text:'On it. I’ve drafted “JWTs, end to end” and added it to your board — read it, then I’ll ask you one question to check it landed.' },
    { who:'system', text:'New lesson added to your kanban · JWTs, end to end' }
  ];

  const EXAMS = [
    { id:'e1', title:'HTTP & REST foundations', subject:'APIs & Services', type:'Unit exam', score:91, bar:70, status:'passed', when:'Wk 2' },
    { id:'e2', title:'Auth: sessions & JWT', subject:'APIs & Services', type:'Unit exam', score:84, bar:70, status:'passed', when:'Wk 4' },
    { id:'e3', title:'Relational modelling', subject:'Databases', type:'Unit exam', score:76, bar:70, status:'passed', when:'Wk 3' },
    { id:'e4', title:'SQL & queries', subject:'Databases', type:'Mid-term', score:58, bar:65, status:'failed', when:'Wk 5' },
    { id:'e5', title:'Build a REST service', subject:'APIs & Services', type:'Unit exam', score:null, bar:70, status:'upcoming', when:'Wk 6' }
  ];

  // faculty grade detail (reward history = last 10 signals)
  const GRADES = [
    { id:'prof-api', name:'Mei', subject:'APIs & Services', letter:'A−', score:88, trend:'up', version:3,
      history:[72,74,71,78,80,79,83,85,86,88], note:'Strong. Worked-example-first method is landing.' },
    { id:'prof-db', name:'Kenji', subject:'Databases', letter:'B+', score:78, trend:'down', version:4,
      history:[82,83,80,79,77,74,70,76,77,78], note:'Recovered after a mid-term fail triggered a methodology rewrite (v3→v4).' }
  ];

  // command-center reward feed
  const FEED = [
    { t:'2m', who:'Rei', icon:'examiner', text:'Graded “REST routing” · 92% · +reward to Mei', kind:'pos' },
    { t:'14m', who:'Mei', icon:'professor', text:'Published lesson · “JWTs, end to end”', kind:'neutral' },
    { t:'1h', who:'Rei', icon:'examiner', text:'Mid-term failed · SQL & queries · −10 to Kenji', kind:'neg' },
    { t:'1h', who:'Daichi', icon:'provost', text:'Rewrote Kenji’s methodology · v3 → v4', kind:'update' },
    { t:'2h', who:'Sora', icon:'registrar', text:'Attendance logged · 6-day streak', kind:'neutral' },
    { t:'3h', who:'Haru', icon:'counselor', text:'Nudge sent · “One more JOIN and you’ve got it”', kind:'neutral' }
  ];

  // connections
  const MODELS = [
    { id:'claude', name:'Claude', tier:'strong reasoner', dot:'#d79a72' },
    { id:'gpt', name:'GPT', tier:'balanced', dot:'#74aa9c' },
    { id:'gemini', name:'Gemini', tier:'long-context', dot:'#5fb0e8' },
    { id:'llama', name:'Llama', tier:'fast & cheap', dot:'#8b86f0' },
    { id:'mistral', name:'Mistral', tier:'fast', dot:'#e6c06a' }
  ];
  const MCP = [
    { id:'py', name:'Python sandbox', cap:'run code · tests', domain:'coding', status:'mounted' },
    { id:'sql', name:'SQL / database', cap:'query · schema', domain:'databases', status:'mounted' },
    { id:'git', name:'Git / filesystem', cap:'repos · review', domain:'projects', status:'mounted' },
    { id:'search', name:'Web search', cap:'retrieve · cite', domain:'theory', status:'available' },
    { id:'jupyter', name:'Jupyter', cap:'data · plots', domain:'data sci', status:'available' },
    { id:'slack', name:'Slack / comms', cap:'DM teachers · faculty room', domain:'communication', status:'mounted' },
    { id:'kanban', name:'Kanban board', cap:'flow · status sync', domain:'tracking', status:'mounted' }
  ];

  // hiring sequence (for the build animation)
  const HIRING = [
    { id:'principal', name:'Iroha', roleKey:'principal', line:'Reading your goal & drafting the college…' },
    { id:'provost', name:'Daichi', roleKey:'provost', line:'Hired — owns teaching methodology.' },
    { id:'prof-api', name:'Mei', roleKey:'professor', line:'Hired for APIs & Services.' },
    { id:'prof-db', name:'Kenji', roleKey:'professor', line:'Hired for Databases.' },
    { id:'examiner', name:'Rei', roleKey:'examiner', line:'Hired — sets & grades your exams.' },
    { id:'registrar', name:'Sora', roleKey:'registrar', line:'Hired — attendance & records.' },
    { id:'guide', name:'Yuki', roleKey:'guide', line:'Hired — your personal guide.' },
    { id:'counselor', name:'Haru', roleKey:'counselor', line:'Hired — pacing & wellbeing.' }
  ];

  const STUDENT = {
    name:'Alex', handle:'@alex', mission:'Become job-ready in backend Python',
    level:'intermediate', audience:'switcher', careerMode:true,
    xp:1240, rankTier:1, nextTierXp:1500, streak:6, momentum:78, attendance:86, week:5, weeks:12
  };

  // Slack-style comms (user <-> teacher DMs, + the faculty room where agents talk)
  const CHANNELS = [
    { id:'faculty-room', kind:'room', name:'Faculty Room', sub:'where your teachers talk about your progress', unread:2,
      messages:[
        { who:'Mei', role:'professor', hue:'#f5a623', text:'Alex passed the JWT probe — auth is solid. Moving them onto the REST build.', t:'1h' },
        { who:'Kenji', role:'professor', hue:'#3b82f6', text:'Heads up: Alex failed the SQL mid-term. My theory-first order isn’t landing.', t:'1h' },
        { who:'Daichi', role:'provost', hue:'#46d6ad', text:'On it — shipping you a methodology update, Kenji. Worked queries before theory, slower ramp.', t:'58m' },
        { who:'Kenji', role:'professor', hue:'#3b82f6', text:'Applied (v4). Re-teaching JOINs with examples first.', t:'52m' },
        { who:'Iroha', role:'principal', hue:'#6e8efb', text:'Good. The REST service is the capstone signal — keep me posted, Mei.', t:'40m' },
        { who:'Rei', role:'examiner', hue:'#f0846b', text:'REST unit exam scheduled for Wk 6. Bar is 70.', t:'30m' }
      ]},
    { id:'dm-mei', kind:'dm', name:'Mei', sub:'APIs & Services · Professor', hue:'#f5a623', unread:0,
      messages:[
        { who:'Alex', role:'me', text:'Can you give me a hint on the /users endpoint?', t:'10m' },
        { who:'Mei', role:'professor', hue:'#f5a623', text:'Start with the GET. What shape should a user object be? Send me your struct and I’ll review it in the sandbox.', t:'8m' }
      ]},
    { id:'dm-yuki', kind:'dm', name:'Yuki', sub:'Personal Guide · always on', hue:'#9b6cff', unread:0,
      messages:[
        { who:'Yuki', role:'guide', hue:'#9b6cff', text:'Stuck on anything? Ask me and I’ll bring the right teacher in.', t:'2h' }
      ]}
  ];

  // Campus library — every lesson the faculty has authored
  const LIBRARY = [
    { id:'l1', title:'JWTs, end to end', author:'Mei', subject:'APIs & Services', read:'8 min', tag:'auth', state:'new' },
    { id:'l2', title:'REST verbs & status codes', author:'Mei', subject:'APIs & Services', read:'6 min', tag:'rest', state:'read' },
    { id:'l3', title:'Designing a resource', author:'Mei', subject:'APIs & Services', read:'7 min', tag:'rest', state:'read' },
    { id:'l4', title:'Normalization, plainly', author:'Kenji', subject:'Databases', read:'9 min', tag:'modelling', state:'read' },
    { id:'l5', title:'JOINs with worked examples', author:'Kenji', subject:'Databases', read:'10 min', tag:'sql', state:'new' },
    { id:'l6', title:'Query planning basics', author:'Kenji', subject:'Databases', read:'6 min', tag:'sql', state:'unread' },
    { id:'l7', title:'Idempotency & retries', author:'Mei', subject:'APIs & Services', read:'5 min', tag:'rest', state:'unread' },
    { id:'l8', title:'Transactions & ACID', author:'Kenji', subject:'Databases', read:'8 min', tag:'modelling', state:'locked' }
  ];

  // Per-concept mastery — the STUDENT's own diagnostic (strengths & gaps, never punitive)
  const MASTERY = [
    { subject:'APIs & Services', hue:'#f5a623', concepts:[
      { name:'HTTP & REST basics', level:0.92, seen:'2d ago' },
      { name:'Resource design',    level:0.86, seen:'3d ago' },
      { name:'JWT & auth',         level:0.80, seen:'today' },
      { name:'Error handling',     level:0.56, seen:'5d ago' },
      { name:'Testing',            level:0.34, seen:'not yet' },
      { name:'Deployment',         level:0.18, seen:'not yet' }
    ]},
    { subject:'Databases', hue:'#3b82f6', concepts:[
      { name:'Relational modelling', level:0.82, seen:'4d ago' },
      { name:'Normalization',        level:0.70, seen:'4d ago' },
      { name:'SQL basics',           level:0.55, seen:'2d ago' },
      { name:'JOINs',                level:0.36, seen:'1d ago' },
      { name:'Indexing & perf',      level:0.16, seen:'not yet' },
      { name:'Transactions',         level:0.08, seen:'locked' }
    ]}
  ];

  window.AULA_DATA = { FACULTY, SUBJECTS, KANBAN, LESSON, GUIDE_THREAD, EXAMS, GRADES, FEED, MODELS, MCP, HIRING, STUDENT, CHANNELS, LIBRARY, MASTERY };
})();
