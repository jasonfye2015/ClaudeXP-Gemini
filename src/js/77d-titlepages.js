"use strict";
// The title screen on one page (UPGRADE_PLAN_69.md): the screen after the title card no longer scrolls. Its parts -
// every element and id the code already fills - are set once into a fixed frame: a one-line header, five pages behind
// tabs (Play, Callings, Hall of Fame, Progress, Memorial), and the toolbar always at the foot. Each list pages by
// measure: it shows what fits its panel and pages the rest with arrows, so a tall window shows more and a short one
// fewer, and nothing scrolls. Keys 1-5 (and Q/E, Tab) switch pages, the arrows page the open list; Enter and Space
// still continue the run. The page last open is remembered in this browser.
{ const PAGES = [["play", "Play"], ["callings", "Callings"], ["fame", "Hall of Fame"], ["progress", "Progress"], ["memorial", "Memorial"]];
  const SUBS = [["unlocks", "Unlocks"], ["trophies", "Trophies"], ["achievements", "Achievements"]];
  const KEY = "claudemagic.titlePage";
  const remember = (v) => { try { localStorage.setItem(KEY, v); } catch (e) { /* (a private window) */ } }, recall = () => { try { return localStorage.getItem(KEY); } catch (e) { return null; } };
  const CSS = `
#title .sheet.tp { display: flex; flex-direction: column; gap: 8px; width: min(1100px, 97vw); height: 100vh; max-height: 100vh; padding: 10px 0 8px; box-sizing: border-box; grid-template-columns: none; }
#title .sheet.tp > * { grid-column: auto; }
#title .tp-head { display: flex; align-items: center; justify-content: center; gap: 14px; flex-wrap: wrap; flex: 0 0 auto; }
#title .tp-head h1 { margin: 0; font-size: 34px; display: flex; align-items: center; gap: 10px; }
#title .tp-head h1 .emblem-slot canvas { width: 48px; height: 48px; }
#title .tp-head .honours, #title .tp-head .note { margin: 0; min-height: 0; }
#title .tp-head .tagline { display: none; }
#title .tp-tabs { display: flex; gap: 6px; justify-content: center; flex: 0 0 auto; flex-wrap: wrap; }
#title .tp-tabs button { min-width: 110px; padding: 6px 14px; font-size: 14px; }
#title .tp-tabs button.on, #title .tp-subs button.on, #title .tp-filter button.on { border-color: var(--gold); color: var(--gold); background: #4A321A; }
#title .tp-tabs button kbd { font: 10px var(--mono); color: var(--faint); margin-left: 6px; }
#title .tp-pages { flex: 1 1 auto; min-height: 0; position: relative; }
#title .tp-page { position: absolute; inset: 0; display: none; }
#title .tp-page.on { display: flex; flex-direction: column; }
#title .tp-page > .card { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; margin: 0; overflow: hidden; }
#title .tp-list { flex: 1 1 auto; min-height: 0; overflow: hidden; position: relative; }
#title .tp-pager { flex: 0 0 auto; display: flex; gap: 10px; align-items: center; justify-content: center; padding-top: 6px; color: var(--dim); font-size: 13px; }
#title .tp-pager[hidden] { display: none; }
#title .tp-pager button { padding: 2px 12px; }
#title .tp-hide { display: none !important; }
/* Play */
#title #expedition > h2 { margin-bottom: 4px; }
#title #slots-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 6px 0 10px; }
#title #slots-row > span { display: none; }
#title #slots-row button { display: flex; flex-direction: column; align-items: flex-start; gap: 3px; padding: 10px 12px; min-height: 108px; text-align: left; font-weight: normal; }
#title #slots-row button .sl-n { font: 700 12px var(--serif); color: var(--dim); letter-spacing: 1px; text-transform: uppercase; }
#title #slots-row button .sl-where { font: 700 17px var(--serif); color: var(--ink); }
#title #slots-row button.on .sl-where { color: var(--gold); }
#title #slots-row button .sl-info { font-size: 11px; color: var(--dim); }
#title #slots-row button .sl-party { display: flex; gap: 3px; margin-top: auto; }
#title #slots-row button .sl-party canvas { width: 28px; height: 28px; image-rendering: pixelated; border-radius: 3px; }
#title #expedition .row { margin: 8px 0; }
#title #btn-continue { font-size: 18px; padding: 8px 26px; }
#title .tp-help { position: relative; }
#title .tp-help .pop { position: absolute; z-index: 5; left: 0; top: calc(100% + 6px); width: min(520px, 80vw); background: #1E160E; border: 1px solid var(--gold); border-radius: 4px; padding: 10px 12px; box-shadow: 0 8px 20px #000a; }
#title .tp-help .pop p { margin: 0 0 6px; font-size: 13px; }
#title .tp-play-foot { margin-top: auto; color: var(--dim); font-size: 13px; font-style: italic; text-align: center; }
/* Callings */
#title .tp-cwrap { flex: 1 1 auto; min-height: 0; display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 16px; }
#title .tp-callings #classes { display: grid; grid-template-columns: repeat(auto-fill, minmax(84px, 1fr)); gap: 8px; align-content: start; }
#title .tp-callings .calling { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 4px; border: 1px solid var(--edge); border-radius: 4px; cursor: pointer; background: rgba(30,22,14,0.6); }
#title .tp-callings .calling:hover, #title .tp-callings .calling.on { border-color: var(--gold); }
#title .tp-callings .calling canvas { width: 52px; height: 52px; image-rendering: pixelated; }
#title .tp-callings .calling > div small { display: none; }
#title .tp-callings .calling > div b { font-size: 13px; }
#title .tp-callings .calling.locked { opacity: 0.55; }
#title .tp-cdetail { border-left: 1px solid var(--edge); padding-left: 16px; overflow: hidden; }
#title .tp-cdetail canvas { width: 96px; height: 96px; image-rendering: pixelated; float: left; margin: 0 12px 6px 0; border-radius: 4px; }
#title .tp-cdetail h3 { margin: 4px 0; color: var(--gold); font: 700 22px var(--serif); }
#title .tp-cdetail .role { color: var(--ink); font-size: 14px; }
#title .tp-cdetail .blurb { clear: both; color: var(--dim); font-size: 14px; line-height: 1.5; }
#title .tp-cdetail .stats { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 13px; color: var(--dim); margin: 4px 0 10px; }
#title .tp-cdetail .stats b { color: var(--ink); }
#title .tp-cdetail .ph { color: var(--gold); font: 700 12px var(--serif); letter-spacing: 1px; text-transform: uppercase; margin: 6px 0 4px; }
#title .tp-cdetail .path { font-size: 13px; color: var(--ink); margin-bottom: 8px; line-height: 1.45; }
#title .tp-cdetail .path i { color: var(--dim); }
#title .tp-cdetail .path small { color: var(--dim); }
#title .tp-glance { margin-top: 14px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; flex: 1 1 auto; min-height: 0; align-content: start; }
#title .tp-glance > div { border: 1px solid var(--edge); border-radius: 4px; padding: 10px 12px; background: rgba(30,22,14,0.55); overflow: hidden; }
#title .tp-glance h3 { margin: 0 0 6px; color: var(--gold); font: 700 12px var(--serif); letter-spacing: 1px; text-transform: uppercase; }
#title .tp-glance .big { font: 700 22px var(--serif); color: var(--ink); }
#title .tp-glance p { margin: 3px 0; font-size: 13px; color: var(--dim); }
#title .tp-glance ol { margin: 0; padding-left: 20px; font: 13px var(--serif); color: var(--ink); }
@media (max-width: 900px) { #title .tp-glance { grid-template-columns: 1fr; } }
#title .tp-callings #start-with { flex: 0 0 auto; margin: 8px 0 0; font-size: 12px; color: var(--dim); }
/* the badge grids */
#title .tp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 6px 12px; align-content: start; }
#title .tp-grid .unlock { margin: 0; padding: 6px 8px; border: 1px solid var(--edge); border-radius: 4px; background: rgba(30,22,14,0.55); }
#title .tp-grid .unlock.got { border-color: #5A4A28; }
#title .tp-grid .unlock small { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
#title #achievements.f-done .unlock:not(.got), #title #achievements.f-todo .unlock.got { display: none; }
#title .tp-subs, #title .tp-filter { display: flex; gap: 6px; flex: 0 0 auto; margin-bottom: 8px; flex-wrap: wrap; }
#title .tp-subs button, #title .tp-filter button { padding: 3px 12px; font-size: 13px; }
#title .tp-filter { margin-left: auto; }
#title .tp-subbar { display: flex; align-items: center; flex: 0 0 auto; }
#title .tp-sub { display: none; flex: 1 1 auto; min-height: 0; flex-direction: column; }
#title .tp-sub.on { display: flex; }
#title #daily-board { flex: 0 0 auto; margin-bottom: 6px; }
/* the toolbar */
#title .sheet.tp > .foot { flex: 0 0 auto; margin: 0; padding-top: 6px; border-top: 1px solid var(--edge); }
#title .sheet.tp > .version { flex: 0 0 auto; margin: 0; }
@media (max-width: 900px) {
  #title .tp-tabs button { min-width: 0; padding: 5px 9px; font-size: 13px; }
  #title .tp-tabs button kbd { display: none; }
  #title #slots-row { grid-template-columns: repeat(2, 1fr); }
  #title .tp-callings #classes { grid-template-columns: repeat(auto-fill, minmax(70px, 1fr)); gap: 6px; }
  #title .tp-callings .calling canvas { width: 40px; height: 40px; }
  #title .tp-head h1 { font-size: 26px; }
}
@media (max-height: 700px) {
  #title .tp-head h1 { font-size: 24px; } #title .tp-head h1 .emblem-slot canvas { width: 34px; height: 34px; }
  #title #slots-row button { min-height: 0; padding: 7px 10px; }
  #title .tp-glance > div:nth-child(3) { display: none; } #title .tp-glance { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 8px; }
  #title .tp-glance ol li:nth-child(n+3) { display: none; }
  #title .tp-glance > div { padding: 6px 10px; } #title .tp-glance .big { font-size: 17px; } #title .tp-glance p { margin: 1px 0; font-size: 12px; } #title .tp-glance h3 { margin-bottom: 3px; }
  #title .tp-cdetail .path small, #title .tp-cdetail .ph { display: none; } #title .tp-cdetail canvas { width: 64px; height: 64px; }
  #title .tp-callings #start-with { display: none; }
}
@media (prefers-reduced-motion: no-preference) { #title .tp-page.on { animation: tpIn 0.18s ease-out; } }
@keyframes tpIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }`;
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html !== undefined) e.innerHTML = html; return e; };
  // a list that pages by measure: items stay where they are, only what fits the panel is shown
  const Pager = function (ui, key, listEl, items) { this.ui = ui; this.key = key; this.list = listEl; this.items = items; this.bar = el("div", "tp-pager"); this.bar.hidden = true;
    this.prevB = el("button", "", "&#9664;"); this.label = el("span"); this.nextB = el("button", "", "&#9654;"); this.prevB.title = "The page before (the left arrow)"; this.nextB.title = "The next page (the right arrow)"; this.bar.append(this.prevB, this.label, this.nextB);
    this.prevB.addEventListener("click", (e) => { e.stopPropagation(); this.go(-1); }); this.nextB.addEventListener("click", (e) => { e.stopPropagation(); this.go(1); }); };
  Pager.prototype.go = function (d) { const st = this.ui.tpPage; st[this.key] = Math.max(0, Math.min((this.pages || 1) - 1, (st[this.key] || 0) + d)); this.show(); };
  Pager.prototype.measure = function () { const items = this.items().filter((e) => getComputedStyle(e).display !== "none" || e.classList.contains("tp-hide"));
    for (const e of items) e.classList.remove("tp-hide");
    if (!this.list.clientHeight) { this.pages = 1; this.starts = [0]; this.vis = items; return; }
    const vis = items.filter((e) => getComputedStyle(e).display !== "none"), starts = [0], bottom = this.list.getBoundingClientRect().bottom, first = vis.length ? vis[0].getBoundingClientRect().top : bottom, H = bottom - first; let pageTop = first;   /* (the room below the first item: a table above the items is not theirs) */
    vis.forEach((e, i) => { const r = e.getBoundingClientRect(); if (r.bottom - pageTop > H + 0.5 && i > starts[starts.length - 1]) { starts.push(i); pageTop = r.top; } });
    this.vis = vis; this.starts = starts; this.pages = starts.length; this.show(); };
  Pager.prototype.show = function () { const st = this.ui.tpPage, n = this.pages || 1; st[this.key] = Math.max(0, Math.min(n - 1, st[this.key] || 0)); const p = st[this.key], a = (this.starts || [0])[p], b = p + 1 < n ? this.starts[p + 1] : (this.vis || []).length;
    (this.vis || []).forEach((e, i) => e.classList.toggle("tp-hide", i < a || i >= b)); this.bar.hidden = n <= 1; this.label.textContent = `${p + 1} / ${n}`; this.prevB.disabled = p === 0; this.nextB.disabled = p >= n - 1; };
  const P = CM.UI.prototype;
  P.tpBuild = function () { if (this.tpBuilt) return; const sheet = this.$("#title .sheet"); if (!sheet) return; this.tpBuilt = true; this.tpPage = {};
    if (!document.getElementById("tp-css")) { const st = el("style"); st.id = "tp-css"; st.textContent = CSS; document.head.appendChild(st); }
    sheet.classList.add("tp");
    const h1 = sheet.querySelector("h1"), tag = sheet.querySelector(".tagline"), note = this.$("#title-note"), hon = this.$("#honours"), exp = this.$("#expedition"), fame = this.$("#fame"), foot = sheet.querySelector(".foot"), ver = sheet.querySelector(".version");
    const head = el("div", "tp-head"); head.append(h1, hon, note, tag);
    const tabs = el("div", "tp-tabs"), pages = el("div", "tp-pages"), page = {};
    PAGES.forEach(([id, name], i) => { const b = el("button", "", `${name}<kbd>${i + 1}</kbd>`); b.dataset.tp = id; b.title = `${name} (${i + 1})`; b.addEventListener("click", () => this.tpShow(id)); tabs.appendChild(b); page[id] = el("div", `tp-page tp-${id}`); page[id].dataset.tp = id; pages.appendChild(page[id]); });
    sheet.prepend(head, tabs, pages); if (foot) sheet.appendChild(foot); if (ver) sheet.appendChild(ver);
    // Play: the expedition card, without the callings; the two explanations behind a "?"
    page.play.appendChild(exp);
    const callH = [...exp.querySelectorAll("h2")].find((h) => /callings/i.test(h.textContent)), classes = this.$("#classes"), start = this.$("#start-with");
    const paras = [...exp.querySelectorAll(":scope > p")].filter((p) => p !== start);
    const help = el("span", "tp-help"), q = el("button", "", "?"), pop = el("div", "pop"); q.title = "About seeds and run codes"; pop.hidden = true; for (const p of paras) pop.appendChild(p); help.append(q, pop);
    q.addEventListener("click", (e) => { e.stopPropagation(); pop.hidden = !pop.hidden; }); document.addEventListener("click", (e) => { if (!help.contains(e.target)) pop.hidden = true; });
    const seedRow = this.$("#seed").closest(".row"); seedRow.appendChild(help);
    const glance = el("div", "tp-glance"); exp.appendChild(glance); this.tpGlance = glance;
    exp.appendChild(el("div", "tp-play-foot", "")); this.tpPlayFoot = exp.querySelector(".tp-play-foot");
    // Callings: the portraits in a grid, the chosen one told beside it
    const cCard = el("div", "card tp-callings"); if (callH) cCard.appendChild(callH); const cwrap = el("div", "tp-cwrap"), detail = el("div", "tp-cdetail"); cwrap.append(classes, detail); cCard.append(cwrap, start); page.callings.appendChild(cCard); this.tpDetail = detail;
    // Hall of Fame: the boards and the table, ten a page or what fits
    page.fame.appendChild(fame); const table = fame.querySelector("table"), fList = el("div", "tp-list"); table.before(fList); fList.appendChild(table);
    // Progress: unlocks, trophies, achievements as sub-tabs; Memorial its own page
    const pCard = el("div", "card"), subbar = el("div", "tp-subbar"), subs = el("div", "tp-subs"), filt = el("div", "tp-filter"); pCard.appendChild(el("h2", "", "Progress")); subbar.append(subs, filt); pCard.appendChild(subbar);
    const subPanel = {}; SUBS.forEach(([id, name]) => { const b = el("button", "", name); b.dataset.sub = id; b.addEventListener("click", () => this.tpSub(id)); subs.appendChild(b); const sp = el("div", "tp-sub"); sp.dataset.sub = id; const list = el("div", "tp-list"), node = this.$(`#${id}`); node.classList.add("tp-grid"); list.appendChild(node); sp.appendChild(list); subPanel[id] = sp; pCard.appendChild(sp); });
    [["all", "All"], ["done", "Done"], ["todo", "To do"]].forEach(([f, name]) => { const b = el("button", "", name); b.dataset.f = f; b.addEventListener("click", () => { this.tpFilter = f; this.tpLayout(); }); filt.appendChild(b); });
    page.progress.appendChild(pCard); this.tpSubPanel = subPanel; this.tpFilterBar = filt;
    const mCard = el("div", "card"), mList = el("div", "tp-list"), mem = this.$("#memorial"); mCard.appendChild(el("h2", "", "In memoriam")); mem.classList.add("tp-grid"); mList.appendChild(mem); mCard.appendChild(mList); page.memorial.appendChild(mCard);
    for (const h of [...fame.querySelectorAll("h2")]) if (!h.querySelector(".boards")) h.remove();   /* (the old headings of the moved lists) */
    // the pagers
    const kids = (sel) => () => [...this.root.querySelectorAll(sel)];
    this.tpPagers = { fame: new Pager(this, "fame", fList, () => { const out = []; for (const tr of table.rows) { if (tr.classList.contains("details") && out.length) { out[out.length - 1].glue = tr; continue; } out.push(tr); } return out; }),
      unlocks: new Pager(this, "unlocks", subPanel.unlocks.querySelector(".tp-list"), kids("#unlocks > .unlock")), trophies: new Pager(this, "trophies", subPanel.trophies.querySelector(".tp-list"), kids("#trophies > .unlock")),
      achievements: new Pager(this, "achievements", subPanel.achievements.querySelector(".tp-list"), kids("#achievements > .unlock")), memorial: new Pager(this, "memorial", mList, kids("#memorial > .unlock")) };
    fList.after(this.tpPagers.fame.bar); for (const id of ["unlocks", "trophies", "achievements"]) subPanel[id].appendChild(this.tpPagers[id].bar); mList.after(this.tpPagers.memorial.bar);
    // a fame row's details travel with it
    const show0 = Pager.prototype.show; this.tpPagers.fame.show = function () { show0.call(this); for (const tr of this.vis || []) if (tr.glue) tr.glue.classList.toggle("tp-hide", tr.classList.contains("tp-hide")); };
    this.tpCur = PAGES.some(([id]) => id === recall()) ? recall() : "play"; this.tpSubCur = "unlocks"; this.tpFilter = "all";
    window.addEventListener("resize", () => { if (this.screen === "title") this.tpLayout(); });
    window.addEventListener("keydown", (e) => this.tpKey(e), true);
  };
  P.tpShow = function (id) { this.tpCur = id; remember(id); this.tpLayout(); };
  P.tpSub = function (id) { this.tpSubCur = id; this.tpLayout(); };
  P.tpActivePager = function () { const P0 = this.tpPagers; if (!P0) return null; return this.tpCur === "fame" ? P0.fame : this.tpCur === "memorial" ? P0.memorial : this.tpCur === "progress" ? P0[this.tpSubCur] : null; };
  P.tpLayout = function () { if (!this.tpBuilt) return;
    for (const b of this.root.querySelectorAll("#title .tp-tabs button")) b.classList.toggle("on", b.dataset.tp === this.tpCur);
    for (const pg of this.root.querySelectorAll("#title .tp-page")) pg.classList.toggle("on", pg.dataset.tp === this.tpCur);
    for (const b of this.root.querySelectorAll("#title .tp-subs button")) b.classList.toggle("on", b.dataset.sub === this.tpSubCur);
    for (const [id, sp] of Object.entries(this.tpSubPanel)) sp.classList.toggle("on", id === this.tpSubCur);
    this.tpFilterBar.style.visibility = this.tpSubCur === "achievements" ? "visible" : "hidden";
    for (const b of this.tpFilterBar.querySelectorAll("button")) b.classList.toggle("on", b.dataset.f === this.tpFilter);
    const ach = this.$("#achievements"); ach.classList.toggle("f-done", this.tpFilter === "done"); ach.classList.toggle("f-todo", this.tpFilter === "todo");
    const pg = this.tpActivePager(); if (pg) pg.measure(); };
  // the slots as cards: the place, the gold and the day, and the party's four faces
  P.tpSlots = function () { const g = this.game;
    for (const b of this.root.querySelectorAll("#slots-row button[data-slot]")) { const n = Number(b.dataset.slot), r = (g.runs || [])[n - 1], floor = r ? CM.runFloor(r) : null, live = r && floor !== null;
      b.innerHTML = `<span class="sl-n">Slot ${n}</span><span class="sl-where">${live ? (floor === 0 ? "The town" : `Floor ${floor}`) : "Empty"}</span><span class="sl-info">${live ? `${(r.gold || 0).toLocaleString()} gold${r.saved ? ` - ${new Date(r.saved).toLocaleDateString()}` : ""}${r.endless ? " - Endless" : ""}` : "A new expedition"}</span><span class="sl-party"></span>`;
      if (live && Array.isArray(r.party)) { const box = b.querySelector(".sl-party"); for (const h of r.party.slice(0, 4)) { try { box.appendChild(this.portrait(h.cls, 28)); } catch (e) { /* (an odd old save) */ } } } } };
  P.tpGlanceFill = function () { const g = this.game, box = this.tpGlance; if (!box) return; const fame = (g.fame || []).slice(0, 3), all = g.allFame || g.fame || [], deep = CM.deepest(all), have = CM.unlocked(all);
    const next = Object.entries(CM.KITS).filter(([id, k]) => !have.includes(id) && k.need > 0).sort((a, b) => a[1].need - b[1].need)[0], mem = (g.memorial || [])[0], nem = CM.store && CM.store.get ? CM.store.get("nemesis", null) : null;
    const best = fame.length ? `<ol>${fame.map((e) => `<li>${this.esc(e.name)} - ${e.won ? "slew the Lich King" : `floor ${e.floor}`}</li>`).join("")}</ol>` : "<p>No party has gone down yet.</p>";
    const depth = deep.floor ? `<div class="big">Floor ${deep.floor}</div><p>${this.esc((CM.themeFor(deep.floor) || {}).name || "")}${deep.won ? " - and the Lich King slain" : ""}</p>` : "<p>The shaft waits in the Keep-yard.</p>";
    const nextLine = next ? `<p>Next: <b>${this.esc(next[1].name)}</b> at floor ${next[1].need}.</p>` : "<p>Every kit is open.</p>";
    const lost = (mem ? `<p><b>${this.esc(mem.name)}</b> the ${this.esc(mem.cls)}, fell on floor ${mem.floor}.</p>` : "<p>No one lost yet.</p>") + (nem ? `<p><i>${this.esc(CM.nemesisLine(nem))}.</i></p>` : "");
    box.innerHTML = `<div><h3>Best runs</h3>${best}</div><div><h3>Deepest</h3>${depth}${nextLine}</div><div><h3>Lately</h3>${lost}</div>`; };
  // the callings: click one to read it
  P.tpCallings = function () { const g = this.game, all = [...this.root.querySelectorAll("#classes .calling")]; if (!all.length || !this.tpDetail) return;
    const names = CM.ALL_CLASSES; if (!this.tpCalling || !names.includes(this.tpCalling)) this.tpCalling = names[0];
    all.forEach((div, i) => { const cls = names[i]; div.dataset.cls = cls; div.classList.toggle("on", cls === this.tpCalling); div.onclick = () => { this.tpCalling = cls; this.tpCallings(); }; div.title = cls; });
    const cls = this.tpCalling, c = CM.CLASSES[cls], locked = g.classUnlocked && !g.classUnlocked(cls), d = this.tpDetail; d.innerHTML = "";
    d.appendChild(this.portrait(cls, 96)); d.appendChild(el("h3", "", cls)); d.appendChild(el("div", "role", `${c.role}${c.cast ? `, casts ${CM.CASTS[c.cast]}` : ""}.`));
    d.appendChild(el("p", "blurb", `${locked ? `<i>Earned: ${this.esc(CM.CLASS_UNLOCK[cls].what)}.</i> ` : ""}${c.blurb}`));
    d.appendChild(el("div", "stats", `<span>Health <b>${c.hp}</b></span><span>Magic <b>${c.mp}</b></span><span>Attack <b>${c.atk}</b></span><span>Defence <b>${c.df}</b></span><span>${c.row === "back" ? "Back" : "Front"} row</span><span>Starts with ${this.esc(c.weapon)} and ${this.esc(c.armor)}</span>`));
    const paths = CM.PATHS && CM.PATHS[cls]; if (paths) { const box = el("div", "paths"); box.appendChild(el("div", "ph", "Two paths, chosen at level 5")); for (const P1 of Object.values(paths)) box.appendChild(el("div", "path", `<b>${this.esc(P1.name)}</b> <i>${this.esc(P1.blurb || "")}</i><br><small>${[P1.t1, P1.t2, P1.t3].filter(Boolean).map((t) => `${this.esc(t.name)}: ${this.esc(t.what)}`).join(" &middot; ")}</small>`)); d.appendChild(box); } };
  // the start-with line, brought up to the hundred-floor shaft
  P.tpStartWith = function () { const s = this.$("#start-with"); if (!s) return; const bag = CM.startingBag(this.$("#seed").value || "x").filter((i) => i.kind !== "torch");
    s.textContent = `Four set out with 30 gold, two torches and two potions (${bag.map((i) => i.name).join(" and ")} - the seed decides which). Below floors ${CM.CAMP_FLOORS.slice(0, 3).join(", ")} and every guardian's floor of the Deep a merchant's camp waits; Claude, the Lich King, is on floor ${CM.LAST_FLOOR}, and below him the Deep goes down to the Root of the World on floor ${CM.BOTTOM} - or, in an Endless expedition, to no bottom at all.`; };
  { const rt0 = P.refreshTitle; P.refreshTitle = function (...a) { this.tpBuild(); const out = rt0.apply(this, a); try { this.tpSlots(); this.tpStartWith(); this.tpCallings(); this.tpGlanceFill(); const g = this.game, bits = []; if (g.festival && CM.FESTIVALS[g.festival]) bits.push(`${CM.FESTIVALS[g.festival].name} is on: ${CM.FESTIVALS[g.festival].what}.`); if (this.tpPlayFoot) this.tpPlayFoot.textContent = bits.join(" ");
      requestAnimationFrame(() => this.tpLayout()); } catch (e) { /* (the old screen still works) */ } return out; }; }
  { const rc0 = P.renderClasses; P.renderClasses = function (...a) { const out = rc0.apply(this, a); try { this.tpCallings(); } catch (e) { /* quiet */ } return out; }; }
  // the keys: 1-5, Q/E and Tab switch pages, the arrows page the list
  P.tpKey = function (e) { if (this.screen !== "title" || !this.tpBuilt || this.splashOn || (this.dialogOpen && this.dialogOpen())) return; const t = e.target, typing = t && (t.tagName === "INPUT" || t.tagName === "SELECT" || t.tagName === "TEXTAREA"); if (typing) return;
    const ids = PAGES.map(([id]) => id), i = ids.indexOf(this.tpCur), m = /^Digit([1-5])$/.exec(e.code);
    if (m) { e.preventDefault(); e.stopPropagation(); this.tpShow(ids[Number(m[1]) - 1]); return; }
    if (e.code === "KeyE" || (e.code === "Tab" && !e.shiftKey)) { e.preventDefault(); e.stopPropagation(); this.tpShow(ids[(i + 1) % ids.length]); return; }
    if (e.code === "KeyQ" || (e.code === "Tab" && e.shiftKey)) { e.preventDefault(); e.stopPropagation(); this.tpShow(ids[(i + ids.length - 1) % ids.length]); return; }
    if (e.code === "ArrowLeft" || e.code === "ArrowRight") { const pg = this.tpActivePager(); if (pg && pg.pages > 1) { e.preventDefault(); e.stopPropagation(); pg.go(e.code === "ArrowLeft" ? -1 : 1); } } };
}
