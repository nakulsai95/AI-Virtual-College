/* AULA product — theme system (10 genre-inspired skins, original naming) */
(function(){
  const THEMES = {
    standard:{ name:'Standard', wm:'AULA', mark:'A', vibe:'calm · scholarly', accent:'#6e8efb', accent2:'#46d6ad', bg:'#0e1014',
      terms:{ college:'AULA', principal:'Principal', professor:'Professor', guide:'Personal Guide', semester:'Semester', module:'Module', exam:'Exam', rankWord:'Rank', ranks:['Bronze','Silver','Gold','Platinum'] } },
    ninja:{ name:'Ninja Path', wm:'The Academy', mark:'道', vibe:'shonen · missions', accent:'#f5a623', accent2:'#3b82f6', bg:'#100f0d',
      terms:{ college:'The Academy', principal:'Headmaster', professor:'Sensei', guide:'Path Guide', semester:'Arc', module:'Mission', exam:'Rank Trial', rankWord:'Rank', ranks:['Novice','Adept','Elite','Master'] } },
    blade:{ name:'Blade Corps', wm:'Blade Corps', mark:'刃', vibe:'dark · slayer', accent:'#e0566b', accent2:'#2dd4bf', bg:'#0f0d10',
      terms:{ college:'The Corps', principal:'Commander', professor:'Master', guide:'Attendant', semester:'Season', module:'Selection', exam:'The Trial', rankWord:'Rank', ranks:['Initiate','Bladesman','Veteran','Pillar'] } },
    spirit:{ name:'Spirit Order', wm:'The Order', mark:'呪', vibe:'cursed · sorcery', accent:'#9b6cff', accent2:'#38bdf8', bg:'#0c0b13',
      terms:{ college:'The Order', principal:'Headmaster', professor:'Mentor', guide:'Familiar', semester:'Term', module:'Ordeal', exam:'The Ordeal', rankWord:'Grade', ranks:['Fourth','Third','Second','Special'] } },
    hero:{ name:'Hero Course', wm:'Hero Course', mark:'英', vibe:'bright · heroes', accent:'#4ade80', accent2:'#f43f5e', bg:'#0b0f0d',
      terms:{ college:'Hero Course', principal:'Principal', professor:'Pro-Hero', guide:'Support', semester:'Term', module:'Mission', exam:'Provisional Exam', rankWord:'Rank', ranks:['Sidekick','Rookie','Pro','Top Hero'] } },
    voyage:{ name:'Grand Voyage', wm:'The Crew', mark:'海', vibe:'adventure · sea', accent:'#f6c453', accent2:'#22b8c4', bg:'#0a0e11',
      terms:{ college:'The Crew', principal:'Captain', professor:'Navigator', guide:'Lookout', semester:'Voyage', module:'Island', exam:'Port Trial', rankWord:'Rank', ranks:['Deckhand','Mate','Officer','Captain'] } },
    arcane:{ name:'Arcane Academy', wm:'The Academy', mark:'魔', vibe:'mystic · spellcraft', accent:'#c084fc', accent2:'#f5c542', bg:'#0e0b14',
      terms:{ college:'The Academy', principal:'Archmage', professor:'Mentor', guide:'Familiar', semester:'Term', module:'Rite', exam:'Examination', rankWord:'Rank', ranks:['Apprentice','Adept','Mage','Archmage'] } },
    mecha:{ name:'Mecha Program', wm:'The Program', mark:'機', vibe:'sci-fi · pilots', accent:'#34d3e6', accent2:'#f25f4c', bg:'#0a0d10',
      terms:{ college:'The Program', principal:'Commander', professor:'Instructor', guide:'Operator', semester:'Deployment', module:'Sortie', exam:'Eval Sortie', rankWord:'Rank', ranks:['Cadet','Pilot','Ace','Commander'] } },
    cyber:{ name:'Neo Net', wm:'The Net', mark:'電', vibe:'cyberpunk · neon', accent:'#ff4d9d', accent2:'#2dd4ff', bg:'#0b0a0f',
      terms:{ college:'The Net', principal:'Sysop', professor:'Operator', guide:'Daemon', semester:'Cycle', module:'Run', exam:'Benchmark', rankWord:'Tier', ranks:['User','Runner','Hacker','Sysop'] } },
    dream:{ name:'Dream Studio', wm:'The Studio', mark:'夢', vibe:'cozy · slice-of-life', accent:'#f4a6c0', accent2:'#9bd1c6', bg:'#12100f',
      terms:{ college:'The Studio', principal:'Director', professor:'Guide', guide:'Buddy', semester:'Season', module:'Episode', exam:'Review', rankWord:'Level', ranks:['Newcomer','Regular','Senior','Lead'] } }
  };
  const ORDER = ['standard','ninja','blade','spirit','hero','voyage','arcane','mecha','cyber','dream'];

  function hexRgba(hex,a){const h=hex.replace('#','');return `rgba(${parseInt(h.substr(0,2),16)},${parseInt(h.substr(2,2),16)},${parseInt(h.substr(4,2),16)},${a})`;}

  function applyThemeVars(key){
    const t = THEMES[key] || THEMES.ninja;
    const r = document.documentElement.style;
    r.setProperty('--accent', t.accent);
    r.setProperty('--accent2', t.accent2);
    r.setProperty('--accent-soft', hexRgba(t.accent,.14));
    r.setProperty('--accent-line', hexRgba(t.accent,.30));
    r.setProperty('--glow', hexRgba(t.accent,.18));
    r.setProperty('--bg', t.bg);
    document.body && document.body.setAttribute('data-theme', key);
  }

  window.AULA_THEMES = THEMES;
  window.AULA_THEME_ORDER = ORDER;
  window.AULA_hexRgba = hexRgba;
  window.applyThemeVars = applyThemeVars;
})();
