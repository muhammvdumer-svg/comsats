(() => {
  const DATA = window.TIMETABLE;
  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const PROGRAMS = ["BBA", "BAF", "BBD", "BAT"];
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  };

  const todayIdx = new Date().getDay() - 1; // Monday = 0, Sunday = -1
  const state = {
    program: store.get("program") || "BBA",
    section: store.get("section") || null,
    day: DAYS[todayIdx] ? DAYS[todayIdx] : "Monday",
    q: "",
  };

  // Stable colour per course
  const colour = (name) => {
    const key = (name.match(/[A-Z]{3}\s?\d{3}/) || [name])[0];
    let h = 0;
    for (const ch of key) h = (h * 31 + ch.charCodeAt(0)) % 360;
    return `hsl(${h} 70% 55%)`;
  };
  const mins = (t) => { const [h, m] = (t || "0:0").split(":").map(Number); return h * 60 + m; };
  const fmt = (t) => {
    if (!t) return "";
    let [h, m] = t.split(":").map(Number);
    const ap = h >= 12 ? "pm" : "am";
    h = h % 12 || 12;
    return `${h}:${String(m).padStart(2, "0")} ${ap}`;
  };
  const sortByTime = (a, b) => mins(a.start) - mins(b.start);

  const sectionsOf = (p) => DATA.sections.filter((s) => s.program === p);
  const label = (s) => s.name.replace(/^[A-Z]{3}-/, "");

  function isNow(x) {
    const d = new Date();
    if (DAYS[d.getDay() - 1] !== x.day) return false;
    const n = d.getHours() * 60 + d.getMinutes();
    return n >= mins(x.start) && n < mins(x.end);
  }

  function card(x, showSection) {
    const live = isNow(x);
    return `<article class="card${live ? " now" : ""}" style="--c:${colour(x.course)}">
      <div class="time">${fmt(x.start)}<span>to ${fmt(x.end)}</span></div>
      <div>
        ${showSection ? `<div class="sectag">${esc(x._section)} · ${esc(x.day)}</div>` : ""}
        <p class="title">${esc(x.course)}${live ? '<span class="tag live">Now</span>' : ""}${x.note ? `<span class="tag">${esc(x.note)}</span>` : ""}${x.group ? `<span class="tag">${esc(x.group)}</span>` : ""}</p>
        <div class="facts">
          <span>Room <b>${esc(x.room || "—")}</b></span>
          <span>${esc(x.instructor)}</span>
        </div>
      </div>
    </article>`;
  }

  function renderPrograms() {
    $("#programs").innerHTML = PROGRAMS
      .filter((p) => sectionsOf(p).length)
      .map((p) => `<button class="chip" data-p="${p}" aria-pressed="${p === state.program}">${p}</button>`)
      .join("");
  }

  function renderSections() {
    const list = sectionsOf(state.program);
    if (!list.some((s) => s.name === state.section)) state.section = list[0]?.name;
    $("#sections").innerHTML = list
      .map((s) => `<button class="sec" data-s="${esc(s.name)}" aria-pressed="${s.name === state.section}">${esc(label(s))}<small>${esc(s.intake)}</small></button>`)
      .join("");
  }

  function renderSection() {
    const s = DATA.sections.find((x) => x.name === state.section);
    if (!s) { $("#view").innerHTML = ""; return; }
    const counts = Object.fromEntries(DAYS.map((d) => [d, s.sessions.filter((x) => x.day === d).length]));
    const items = s.sessions.filter((x) => x.day === state.day).sort(sortByTime);
    const isToday = DAYS[todayIdx] === state.day;

    $("#view").innerHTML = `
      <div class="head">
        <h2>${esc(s.name)}</h2>
        <span class="meta">${esc(s.program)} · ${esc(s.intake)} intake · ${s.sessions.length} classes a week</span>
      </div>
      <div class="days">${DAYS.map((d, i) => `<button class="day" data-d="${d}" aria-pressed="${d === state.day}">${d.slice(0, 3)}${i === todayIdx ? " · Today" : ""}${counts[d] ? `<span class="n">${counts[d]}</span>` : ""}</button>`).join("")}</div>
      <div class="list">
        ${items.length ? items.map((x) => card(x)).join("") : `<div class="panel empty"><div class="big">🎉</div>No classes on ${esc(state.day)}${isToday ? " — enjoy the day off" : ""}.</div>`}
      </div>
      ${s.courses.length ? `<div class="panel courses"><h3>Courses & instructors</h3>${s.courses.map((c) => `
        <div class="row"><div><div>${esc(c.title)}</div><div class="who">${esc(c.instructor)}${c.id && c.id !== s.name ? ` · ${esc(c.id)}` : ""}</div></div><div class="cr">${esc(c.credits)}</div></div>`).join("")}</div>` : ""}
    `;
  }

  function renderSearch() {
    const terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    const hits = [];
    for (const s of DATA.sections) {
      for (const x of s.sessions) {
        const hay = `${x.course} ${x.instructor} ${x.room} ${s.name}`.toLowerCase();
        if (terms.every((t) => hay.includes(t))) hits.push({ ...x, _section: s.name });
      }
    }
    hits.sort((a, b) => DAYS.indexOf(a.day) - DAYS.indexOf(b.day) || sortByTime(a, b));
    const byDay = DAYS.map((d) => [d, hits.filter((h) => h.day === d)]).filter(([, l]) => l.length);
    $("#view").innerHTML = `
      <div class="head"><h2>Results for “${esc(state.q)}”</h2><span class="meta">${hits.length} class${hits.length === 1 ? "" : "es"}</span></div>
      ${byDay.length ? byDay.map(([d, l]) => `<h3 class="sectag" style="margin:18px 0 8px">${d}</h3><div class="list">${l.map((x) => card(x, true)).join("")}</div>`).join("")
        : `<div class="panel empty"><div class="big">🔍</div>Nothing matches that. Try a course code like “MGT301”, a teacher’s name, or a room.</div>`}
    `;
  }

  function render() {
    renderPrograms();
    renderSections();
    state.q.trim() ? renderSearch() : renderSection();
  }

  document.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.p) { state.program = b.dataset.p; state.section = null; store.set("program", state.program); clearSearch(); }
    else if (b.dataset.s) { state.section = b.dataset.s; store.set("section", state.section); clearSearch(); }
    else if (b.dataset.d) { state.day = b.dataset.d; }
    else return;
    render();
    if (state.section) store.set("section", state.section);
  });

  function clearSearch() { state.q = ""; $("#q").value = ""; }
  $("#q").addEventListener("input", (e) => { state.q = e.target.value; render(); });

  render();
  setInterval(() => { if (!state.q) renderSection(); }, 60000); // keep the "Now" badge fresh
})();
