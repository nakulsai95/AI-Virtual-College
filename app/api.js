/* AULA frontend — backend API client + curriculum adapter.
 *
 * The static app talks to the FastAPI backend for two things:
 *   1. LLM connectors (which provider + key powers the agents)
 *   2. Onboarding (the Principal designs a real curriculum)
 *
 * Everything degrades gracefully: if the backend is down, the app keeps
 * running on its built-in demo data.
 */
(function () {
  // Backend base URL. Override with: localStorage.setItem('aula_api_base', 'http://host:port')
  const BASE =
    (typeof localStorage !== 'undefined' && localStorage.getItem('aula_api_base')) ||
    window.AULA_API_BASE ||
    'http://localhost:8000';

  const TOKEN_KEY = 'aula_token';
  const getToken = () => { try { return localStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; } };
  const setToken = (t) => { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch (e) {} };

  async function req(method, path, body) {
    const headers = { 'Content-Type': 'application/json' };
    const tok = getToken();
    if (tok) headers.Authorization = 'Bearer ' + tok;
    const opts = { method, headers };
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
    // Professor authors a lesson; Examiner grades (rewarding the professor);
    // sandbox runs code; faculty returns live grades + the reward feed.
    lesson: (subject, topic, professor, sandbox) =>
      req('POST', '/api/lesson', { subject, topic, professor: professor || '', sandbox: sandbox || 'python' }),
    grade: (payload) => req('POST', '/api/grade', payload),
    faculty: () => req('GET', '/api/faculty'),
    runCode: (sandbox, code) => req('POST', '/api/sandbox/run', { sandbox, code }),
    progress: () => req('GET', '/api/progress'),
    enrollment: () => req('GET', '/api/enrollment'),
    // Exams: the Examiner sets, then grades, a multi-question exam.
    examStart: (subject, bar) => req('POST', '/api/exam/start', { subject, bar: bar || 65 }),
    examSubmit: (payload) => req('POST', '/api/exam/submit', payload),
    examResults: () => req('GET', '/api/exam/results'),
    // Faculty room (live agent conversation) + notifications
    channel: () => req('GET', '/api/channel'),
    advanceChannel: () => req('POST', '/api/channel/advance'),
    notifications: () => req('GET', '/api/notifications'),
    markSeen: () => req('POST', '/api/notifications/seen'),
    // Library / content knowledge base + grounded retrieval
    library: () => req('GET', '/api/library'),
    materialsSearch: (query, n) => req('POST', '/api/materials/search', { query, n: n || 8 }),
    // Search (retrieval) connector
    searchProviders: () => req('GET', '/api/connectors/search/providers'),
    getSearchConnector: () => req('GET', '/api/connectors/search'),
    saveSearchConnector: (provider, api_key) => req('PUT', '/api/connectors/search', { provider, api_key }),
    clearSearchConnector: () => req('DELETE', '/api/connectors/search'),
    // Auth
    token: getToken,
    isAuthed: () => !!getToken(),
    me: () => req('GET', '/api/auth/me'),
    register: (email, password, name) =>
      req('POST', '/api/auth/register', { email, password, name }).then(u => { setToken(u.token); return u; }),
    login: (email, password) =>
      req('POST', '/api/auth/login', { email, password }).then(u => { setToken(u.token); return u; }),
    logout: () => req('POST', '/api/auth/logout').catch(() => {}).then(() => setToken('')),
  };

  // Hue palette so generated subjects/faculty look at home in the design.
  const HUES = ['#f5a623', '#3b82f6', '#9b6cff', '#2dd4bf', '#f0846b', '#46d6ad'];

  /* Map a backend Curriculum onto the shapes the existing screens read,
   * then replace the live AULA_DATA so the whole app reflects the real plan. */
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
        objectives: m.objectives || [],
        assignment: m.assignment || null,
        reading: m.reading || [],
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
      budget: { used: 0, cap: 30 },
    }));

    if (subjects.length) D.SUBJECTS = subjects;
    if (faculty.length) D.FACULTY = faculty;
    D.MILESTONES = curriculum.milestones || [];
    D.GROUNDED = !!curriculum.grounded;
    if (window.AULA_DATA.STUDENT) {
      D.STUDENT.mission = curriculum.mission || D.STUDENT.mission;
      D.STUDENT.weeks = curriculum.weeks || D.STUDENT.weeks;
      D.STUDENT.level = curriculum.level || D.STUDENT.level;
    }
    window.AULA_CURRICULUM = curriculum;
  }

  /* Map the backend student model onto the live data the screens read. */
  function applyStudent(s) {
    if (!s || !window.AULA_DATA) return;
    const D = window.AULA_DATA;
    const S = D.STUDENT || {};
    ['xp', 'streak', 'momentum', 'attendance', 'week', 'weeks', 'rankTier', 'nextTierXp', 'mission', 'level']
      .forEach((k) => { if (s[k] !== undefined && s[k] !== null) S[k] = s[k]; });
    D.STUDENT = S;
    if (s.mastery && s.mastery.length) D.MASTERY = s.mastery;
    window.AULA_STUDENT = s;
  }

  window.AULA_API = AULA_API;
  window.applyCurriculum = applyCurriculum;
  window.applyStudent = applyStudent;
})();
