/* AULA frontend — backend API client + live-state hydration.
 *
 * The backend serves this app AND its API from http://localhost:8000.
 * On load (and after every meaningful action) the app hydrates AULA_DATA from
 * GET /api/state — the persistent college: curriculum, faculty grades, lessons,
 * board, exams, mastery, channels, feed, and the credit budget.
 *
 * Everything degrades gracefully: if the backend is down, the app keeps
 * running on its built-in demo data.
 */
(function () {
  // Backend base URL. Same-origin when served by the backend; override with:
  // localStorage.setItem('aula_api_base', 'http://host:port')
  const BASE =
    (typeof localStorage !== 'undefined' && localStorage.getItem('aula_api_base')) ||
    window.AULA_API_BASE ||
    (location.protocol.startsWith('http') ? location.origin : 'http://localhost:8000');

  async function req(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const res = await fetch(BASE + path, opts);
    const text = await res.text();
    const data = text ? JSON.parse(text) : null;
    if (!res.ok) {
      const msg = (data && (data.detail || data.message)) || res.statusText;
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return data;
  }

  const AULA_API = {
    base: BASE,
    health: () => req('GET', '/api/health'),
    providers: () => req('GET', '/api/connectors/providers'),
    sandboxes: () => req('GET', '/api/sandboxes'),
    getConnector: () => req('GET', '/api/connectors/active'),
    saveConnector: (cfg) => req('PUT', '/api/connectors/active', cfg),
    testConnector: (cfg) => req('POST', '/api/connectors/test', cfg),
    clearConnector: () => req('DELETE', '/api/connectors/active'),
    onboard: (goal, level) => req('POST', '/api/onboard', { goal, level }),
    onboardStatus: () => req('GET', '/api/onboard/status'),
    // Live college
    state: () => req('GET', '/api/state'),
    lesson: (subject, topic, professor, sandbox) =>
      req('POST', '/api/lesson', { subject, topic, professor: professor || '', sandbox: sandbox || 'python' }),
    getLesson: (id) => req('GET', '/api/lessons/' + id),
    grade: (payload) => req('POST', '/api/grade', payload),
    faculty: () => req('GET', '/api/faculty'),
    runCode: (sandbox, code) => req('POST', '/api/sandbox/run', { sandbox, code }),
    guideAsk: (message) => req('POST', '/api/guide', { message }),
    channelSend: (channel, text) => req('POST', '/api/channel/' + channel + '/messages', { text }),
    channelRead: (channel) => req('POST', '/api/channel/' + channel + '/read'),
    examGenerate: (module_id) => req('POST', '/api/exams/generate', { module_id }),
    examSubmit: (exam_id, answers) => req('POST', '/api/exams/' + exam_id + '/submit', { answers }),
    catalogGenerate: (catalog_id) => req('POST', '/api/catalog/' + catalog_id + '/generate'),
    buildContinue: () => req('POST', '/api/build/continue'),
    usage: () => req('GET', '/api/usage'),
    setBudget: (cap) => req('PUT', '/api/budget', { cap }),
    resetCollege: () => req('POST', '/api/reset'),
    /* Start fresh: wipe the college (keeps your connector key + budget),
     * return to onboarding. */
    startFresh: async () => {
      try { await req('POST', '/api/reset'); } catch (e) { /* offline is fine */ }
      localStorage.removeItem('aula_enrolled');
      location.reload();
    },
  };

  /* Pull the whole persistent college into AULA_DATA and re-render. */
  const LIVE_KEYS = ['STUDENT', 'SUBJECTS', 'FACULTY', 'KANBAN', 'EXAMS', 'GRADES',
                     'FEED', 'CHANNELS', 'LIBRARY', 'MASTERY', 'MATERIALS'];
  async function hydrate() {
    try {
      const s = await AULA_API.state();
      if (!s || !s.enrolled) {
        // Backend reachable but no college — it is the source of truth, so a
        // stale local "enrolled" flag (old demo session) gets cleared.
        window.AULA_LIVE = false;
        if (s && localStorage.getItem('aula_enrolled') === '1') {
          localStorage.removeItem('aula_enrolled');
          window.dispatchEvent(new CustomEvent('aula:data'));
        }
        return s;
      }
      const D = window.AULA_DATA;
      LIVE_KEYS.forEach((k) => { if (s[k]) D[k] = s[k]; });
      // Live college: the LESSON is whatever the faculty actually authored —
      // null until then (never the demo lesson).
      D.LESSON = s.LESSON || null;
      D.NEXT_EXAM = s.NEXT_EXAM || null;
      D.BUILD = s.BUILD || null;
      D.USAGE = s.USAGE || null;
      window.AULA_LIVE = true;
      localStorage.setItem('aula_enrolled', '1');
      window.dispatchEvent(new CustomEvent('aula:data'));
      return s;
    } catch (e) {
      window.AULA_LIVE = false;
      return null;
    }
  }
  AULA_API.hydrate = hydrate;

  // Hue palette so generated subjects/faculty look at home in the design.
  const HUES = ['#f5a623', '#3b82f6', '#9b6cff', '#2dd4bf', '#f0846b', '#46d6ad'];
  const HIRE_LINES = {
    principal: 'Reading your goal & drafting the college…',
    provost: 'Hired — owns teaching methodology.',
    examiner: 'Hired — sets & grades your exams.',
    registrar: 'Hired — attendance & records.',
    guide: 'Hired — your personal guide.',
    counselor: 'Hired — pacing & wellbeing.',
  };
  const ROLE_ORDER = ['principal', 'provost', 'professor', 'examiner', 'registrar', 'guide', 'counselor'];

  /* Map a backend Curriculum onto the shapes the existing screens read
   * (used during onboarding, before the full state hydration lands). */
  function applyCurriculum(curriculum) {
    if (!curriculum || !window.AULA_DATA) return;
    const D = window.AULA_DATA;

    const subjects = (curriculum.subjects || []).map((s, i) => ({
      id: s.id || 's' + (i + 1),
      title: s.title,
      profName: s.professor,
      prof: 'prof-' + (i + 1),
      progress: 0,
      hue: HUES[i % HUES.length],
      sandboxes: s.sandboxes || [],
      modules: (s.modules || []).map((m, j) => ({
        id: m.id || s.id + 'm' + (j + 1),
        title: m.title,
        status: j === 0 ? 'active' : 'locked',
        exam: 'pending',
      })),
    }));

    const faculty = (curriculum.faculty || []).map((f, i) => ({
      id: f.id || f.role + '-' + i,
      role: f.role,
      name: f.name,
      subject: f.subject || undefined,
      hue: HUES[i % HUES.length],
      model: f.model || '—',
      status: 'active',
      budget: { used: 0, cap: 1 },
    }));
    faculty.sort((a, b) => ROLE_ORDER.indexOf(a.role) - ROLE_ORDER.indexOf(b.role));

    if (subjects.length) D.SUBJECTS = subjects;
    if (faculty.length) {
      D.FACULTY = faculty;
      D.HIRING = faculty.map((f) => ({
        id: f.id, name: f.name, roleKey: f.role,
        line: f.role === 'professor'
          ? 'Hired for ' + (f.subject || 'your subject') + '.'
          : (HIRE_LINES[f.role] || 'Hired.'),
      }));
    }
    if (window.AULA_DATA.STUDENT) {
      D.STUDENT.mission = curriculum.mission || D.STUDENT.mission;
      D.STUDENT.weeks = curriculum.weeks || D.STUDENT.weeks;
      D.STUDENT.level = curriculum.level || D.STUDENT.level;
    }
    window.AULA_CURRICULUM = curriculum;
    window.dispatchEvent(new CustomEvent('aula:data'));
  }

  window.AULA_API = AULA_API;
  window.applyCurriculum = applyCurriculum;

  // Hydrate the persistent college on load (no-op when the backend is down).
  hydrate();
})();
