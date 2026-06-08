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
    // Professor authors a lesson; Examiner grades (rewarding the professor);
    // sandbox runs code; faculty returns live grades + the reward feed.
    lesson: (subject, topic, professor, sandbox) =>
      req('POST', '/api/lesson', { subject, topic, professor: professor || '', sandbox: sandbox || 'python' }),
    grade: (payload) => req('POST', '/api/grade', payload),
    faculty: () => req('GET', '/api/faculty'),
    runCode: (sandbox, code) => req('POST', '/api/sandbox/run', { sandbox, code }),
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
    if (window.AULA_DATA.STUDENT) {
      D.STUDENT.mission = curriculum.mission || D.STUDENT.mission;
      D.STUDENT.weeks = curriculum.weeks || D.STUDENT.weeks;
      D.STUDENT.level = curriculum.level || D.STUDENT.level;
    }
    window.AULA_CURRICULUM = curriculum;
  }

  window.AULA_API = AULA_API;
  window.applyCurriculum = applyCurriculum;
})();
