"""Mock connector — runs with no key so the app works before one is added.

It returns a deterministic, plausible curriculum derived from the goal text so
the onboarding flow is fully functional offline. Real providers replace it the
moment the user connects one in the UI.
"""
from __future__ import annotations

import json

from ..base import LLMProvider


class MockProvider(LLMProvider):
    id = "mock"
    name = "Demo (no key)"

    @property
    def default_model(self) -> str:
        return "aula-demo"

    def complete(self, system, messages, *, max_tokens=4000, json=False):
        if not json:
            return "pong"
        sys_l = (system or "").lower()
        user = " ".join(m["content"] for m in messages if m["role"] == "user")
        # Match the role's identity line, not stray mentions (the Principal's
        # prompt also contains the word "professor").
        if "design an exam" in sys_l:
            return _demo_exam_json(user)
        if "you are the game designer" in sys_l:
            return _demo_game_json(user)
        if "you are the lab designer" in sys_l:
            return _demo_lab_json(user)
        if "detailed academic" in sys_l and "syllabus" in sys_l:
            return _demo_syllabus_json(user)
        if "quality pass" in sys_l:
            return json.dumps({"aligned": True,
                               "note": "Demo validation — coverage looks consistent.",
                               "additions": []})
        if "planning the learner's kanban" in sys_l:
            return json.dumps({"cards": []})  # caller falls back to the deterministic plan
        if "you are the examiner" in sys_l:
            return _demo_grade_json(_answer_of(messages))
        if "you are a professor" in sys_l:
            return _demo_lesson_json(user)
        if "you are the personal guide" in sys_l:
            return _demo_guide_json(user)
        if "you are the provost" in sys_l:
            return _demo_provost_json()
        if "you are the counselor" in sys_l:
            return _demo_counselor_json(user)
        return _demo_curriculum_json(_clean_goal(user))


def _answer_of(messages) -> str:
    text = " ".join(m["content"] for m in messages if m["role"] == "user")
    import re
    m = re.search(r"answer:\s*(.+?)(?:\n\nPass bar:|\Z)", text, re.IGNORECASE | re.DOTALL)
    return (m.group(1) if m else text).strip()


def _demo_grade_json(answer: str) -> str:
    words = len(answer.split())
    score = max(0, min(95, 45 + words * 5))
    return json.dumps({
        "score": score,
        "feedback": "Demo grading rewards a clear, reasoned answer. Connect a "
                    "model in Connections for real, substantive feedback.",
    })


def _demo_lesson_json(prompt: str) -> str:
    import re
    m = re.search(r"the class to teach:\s*(.+)", prompt, re.IGNORECASE) \
        or re.search(r"^class:\s*(.+)", prompt, re.IGNORECASE | re.MULTILINE) \
        or re.search(r"topic the learner asked about:\s*(.+)", prompt, re.IGNORECASE)
    topic = (m.group(1).strip().splitlines()[0] if m else prompt.strip()) or "the topic"
    title = topic[:60].strip().title()
    return json.dumps({
        "title": title,
        "read": "8 min",
        "intro": f"A demo 101 class on {topic}. Connect a model in Connections "
                 "to have a real Professor write this in full depth.",
        "objectives": [f"Explain what {topic} is and why it exists",
                       f"Apply {topic} to a small real example",
                       "Spot the most common mistake"],
        "sections": [
            {"h": "Why this matters",
             "paras": [f"{title} is foundational to your goal — without it, the next "
                       "modules won't land.",
                       "We start with the problem it solves, then build the idea up "
                       "from first principles."]},
            {"h": "How it works",
             "paras": ["We break the concept into its moving parts and how they connect."],
             "diagram": "flowchart LR\n  A[Input] --> B[Core idea]\n  B --> C[Result]"},
            {"h": "Worked example",
             "paras": ["Walk through the runnable example below, predict the output, "
                       "then run it."],
             "code": {"language": "python", "snippet": "print('hello, " + title.replace("'", "") + "')"}},
            {"h": "Where it goes wrong",
             "paras": ["The classic mistake is skipping the fundamentals and "
                       "memorizing the recipe instead of the reason."]},
        ],
        "takeaways": [f"{title} solves a real problem — know which one",
                      "Worked examples beat definitions",
                      "Predict before you run"],
        "flashcards": [
            {"front": f"What is {topic}?", "back": f"A core idea in this subject — {title}."},
            {"front": f"Why does {topic} matter?", "back": "It unlocks the next module in your plan."},
            {"front": "Best way to learn it?", "back": "Work the example, then explain it back."},
        ],
        "probe": {"q": f"In your own words, what problem does {topic} solve?",
                  "hint": "Think about what would break without it."},
    })


def _demo_exam_json(prompt: str) -> str:
    import re
    m = re.search(r"module:\s*(.+)", prompt, re.IGNORECASE)
    topic = (m.group(1).strip() if m else "this module").splitlines()[0]
    return json.dumps({"questions": [
        {"q": f"In your own words, what problem does “{topic}” solve?",
         "hint": "Think about what would break without it."},
        {"q": f"Walk through how you would apply {topic} to a small real project.",
         "hint": "Name the steps in order."},
        {"q": f"What is the most common mistake people make with {topic}, and how do you avoid it?",
         "hint": "Think about edge cases."},
        {"q": f"How would you explain {topic} to a beginner in two sentences?",
         "hint": "Plain words beat jargon."},
    ]})


def _demo_game_json(prompt: str) -> str:
    import re
    m = re.search(r"concept to turn into a game:\s*(.+)", prompt, re.IGNORECASE)
    topic = (m.group(1).strip().splitlines()[0] if m else "the concept")
    safe = topic.replace("<", "").replace(">", "").replace("&", "")
    # A real, self-contained catch game (demo). A connected model invents a
    # concept-specific mechanic; this proves the arcade renderer end to end.
    html = """<!doctype html><html><head><meta charset=utf-8><style>
html,body{margin:0;background:#0d0d12;color:#eee;font-family:system-ui;overflow:hidden}
#hud{position:fixed;top:8px;left:10px;font:600 14px system-ui}
#msg{position:fixed;top:8px;right:10px;font:600 13px system-ui;color:#46d6ad}
canvas{display:block;margin:0 auto;background:#16161e}</style></head><body>
<div id=hud>Catch the &#9733; · ← → to move</div><div id=msg></div>
<canvas id=c width=640 height=420></canvas><script>
var cv=document.getElementById('c'),x=cv.getContext('2d'),W=640,H=420;
var px=300,score=0,miss=0,t=30,items=[],keys={},over=false;
onkeydown=function(e){keys[e.key]=1;if([' ','ArrowLeft','ArrowRight'].indexOf(e.key)>=0)e.preventDefault();};
onkeyup=function(e){keys[e.key]=0;};
function spawn(){items.push({x:30+Math.random()*580,y:-20,good:Math.random()>0.4,v:2+Math.random()*2});}
var si=setInterval(spawn,800);
var ti=setInterval(function(){t--;if(t<=0)endGame();},1000);
function endGame(){if(over)return;over=true;clearInterval(si);clearInterval(ti);
var sc=Math.max(0,Math.min(100,Math.round(score*8-miss*5)));
document.getElementById('msg').textContent='Done! score '+sc;
parent.postMessage({aula:'score',value:sc},'*');}
function loop(){if(over){x.fillStyle='#46d6ad';x.font='28px system-ui';x.fillText('GAME OVER',240,210);return;}
x.clearRect(0,0,W,H);
if(keys['ArrowLeft'])px-=6;if(keys['ArrowRight'])px+=6;px=Math.max(0,Math.min(580,px));
for(var i=items.length-1;i>=0;i--){var it=items[i];it.y+=it.v;
x.fillStyle=it.good?'#f5a623':'#f0846b';x.beginPath();x.arc(it.x,it.y,11,0,7);x.fill();
if(it.y>380&&it.y<410&&Math.abs(it.x-(px+30))<40){if(it.good){score++;}else{miss++;}
document.getElementById('msg').textContent=it.good?'+ caught a good one':'- that one did not belong';items.splice(i,1);}
else if(it.y>H){if(it.good)miss++;items.splice(i,1);}}
x.fillStyle='#6e8efb';x.fillRect(px,388,60,16);
x.fillStyle='#eee';x.font='13px system-ui';x.fillText('score '+score+'   time '+t,12,H-10);
requestAnimationFrame(loop);}
loop();
</script></body></html>"""
    return json.dumps({
        "kind": "arcade",
        "title": f"Catch: {safe}",
        "goal": f"Catch the items that belong to {safe}, let the others fall — demo game; "
                "connect a model for a concept-specific mechanic.",
        "controls": "← → to move the paddle",
        "html": html,
    })


def _demo_lab_json(prompt: str) -> str:
    import re
    m = re.search(r"class topic:\s*(.+)", prompt, re.IGNORECASE)
    topic = (m.group(1).strip().splitlines()[0] if m else "this class")
    # A teach-through-play "steps" game: predict, then learn the why at each stage.
    return json.dumps({
        "kind": "steps", "title": f"{topic} — learn by playing",
        "intro": f"Walk through how {topic} works — predict each step, then see why.",
        "steps": [
            {"stage": f"We start with the problem {topic} addresses.",
             "predict": {"q": "What should come first?",
                         "options": ["Understand the problem", "Jump to the answer"],
                         "answer": 0},
             "reveal": f"Right — every idea like {topic} starts from a real problem. "
                       "Name the problem and the rest follows. (Demo lab — connect a "
                       "model for a richer, topic-specific game.)"},
            {"stage": "Now we apply the core idea to that problem.",
             "predict": {"q": "How do we make it stick?",
                         "options": ["Read once quickly", "Work a concrete example"],
                         "answer": 1},
             "reveal": "Working an example turns an abstract rule into something you "
                       "can actually do — that's where understanding forms."},
            {"stage": "Finally we check where it breaks.",
             "predict": {"q": "Why look at edge cases?",
                         "options": ["To memorize trivia", "Edge cases reveal the real boundaries"],
                         "answer": 1},
             "reveal": "Knowing where an idea stops working is how you know where it "
                       "DOES work — that's mastery, not memorization."},
        ],
    })


def _demo_syllabus_json(prompt: str) -> str:
    import re
    mods = re.findall(r'\{"id":\s*"([^"]+)",\s*"title":\s*"([^"]+)"\}', prompt)
    return json.dumps({"modules": [
        {"id": mid, "topics": [
            f"{title}: the core idea", f"{title}: key techniques",
            f"{title}: common pitfalls", f"{title}: hands-on practice",
        ]} for mid, title in mods
    ]})


def _demo_guide_json(prompt: str) -> str:
    import re
    m = re.search(r"question:\s*(.+)", prompt, re.IGNORECASE | re.DOTALL)
    q = (m.group(1).strip() if m else prompt.strip())[:80]
    return json.dumps({
        "reply": f"Good question — that belongs with one of your professors. "
                 f"Bringing them in to write you a short lesson on “{q}”.",
        "subject": "", "topic": q,
    })


def _demo_provost_json() -> str:
    return json.dumps({
        "methodology": {
            "pacing": "slow",
            "sequence": "examples → theory",
            "modality": "blog + worked examples",
            "examples": "high",
            "probe": "after-practice",
        },
        "note": "Demo rewrite — worked examples now come before theory.",
    })


def _demo_counselor_json(prompt: str) -> str:
    import re
    m = re.search(r"weakest concept:\s*(.+)", prompt, re.IGNORECASE)
    concept = (m.group(1).strip() if m else "your weakest concept").splitlines()[0]
    return json.dumps({"nudge": f"One more rep on {concept} and it sticks — try it today."})


def _clean_goal(text: str) -> str:
    """Pull just the goal out of the agent's 'My goal: ...\\nMy level: ...' prompt."""
    import re
    m = re.search(r"my goal:\s*(.+)", text, re.IGNORECASE)
    goal = m.group(1) if m else text
    return re.split(r"\bmy level:", goal, flags=re.IGNORECASE)[0].strip()


# --- naive topic inference, just enough to feel responsive ----------------
_TOPIC_MAP = [
    (("python", "backend", "api", "django", "flask", "fastapi"),
     [("APIs & Services", "py"), ("Databases", "sql")]),
    (("react", "frontend", "javascript", "typescript", "web"),
     [("React & Components", "git"), ("State & Data Fetching", "git")]),
    (("sql", "database", "data engineering", "data engineer"),
     [("Relational Modelling", "sql"), ("Querying & Performance", "sql")]),
    (("machine learning", "ml", "data science", "ai", "neural", "pandas"),
     [("Foundations of ML", "jupyter"), ("Models & Evaluation", "jupyter")]),
]


def _subjects_for(goal: str):
    for keys, subs in _TOPIC_MAP:
        if any(k in goal for k in keys):
            return subs
    return [("Core Concepts", "shell"), ("Applied Practice", "git")]


def _demo_curriculum_json(goal: str) -> str:
    subjects_seed = _subjects_for(goal.lower())
    subjects = []
    for i, (title, sandbox) in enumerate(subjects_seed):
        subjects.append({
            "id": f"s{i+1}",
            "title": title,
            "professor": ["Mei", "Kenji", "Aria", "Ravi"][i % 4],
            "sandboxes": [sandbox, "web-search"],
            "modules": [
                {"id": f"s{i+1}m1", "title": f"{title}: foundations"},
                {"id": f"s{i+1}m2", "title": f"{title}: core techniques"},
                {"id": f"s{i+1}m3", "title": f"{title}: building real things"},
                {"id": f"s{i+1}m4", "title": f"{title}: testing & mastery"},
            ],
        })
    data = {
        "mission": goal.strip()[:120] or "Reach your learning goal",
        "level": "intermediate",
        "weeks": 12,
        "summary": "A demo curriculum (no LLM key connected). Connect a provider "
                   "in Connections to have a real Principal design this for you.",
        "subjects": subjects,
        "faculty": [
            {"id": "principal", "role": "principal", "name": "Iroha", "model": "demo"},
            {"id": "provost", "role": "provost", "name": "Daichi", "model": "demo"},
        ] + [
            {"id": f"prof{i+1}", "role": "professor", "name": s["professor"],
             "subject": s["title"], "model": "demo"}
            for i, s in enumerate(subjects)
        ] + [
            {"id": "examiner", "role": "examiner", "name": "Rei", "model": "demo"},
            {"id": "guide", "role": "guide", "name": "Yuki", "model": "demo"},
        ],
    }
    return json.dumps(data)
