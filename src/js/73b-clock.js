"use strict";
// The clock made visible (the tenth update, phase 9): a dial in the view's top-right corner - the sky's colour of the
// hour, the sun and the moon on their arc over a strip of ground, the hour in figures and words, the day, the season,
// the weather with the days ahead, a festival in its week, and the moon's face drawn large - and the Calendar (a click
// on the dial, or K): the moon's month, the seasons' daylight, the weather ahead and the year's festivals. The numbers
// are CM.dialOf, CM.nextMoon and CM.comingWeather (24b-calendar.js); this file only draws them.
CM.SKY_COLOURS = { day: ["#4F8FD0", "#A8D2F2"], dawn: ["#6A78B8", "#F0A060"], dusk: ["#5A5C9C", "#E88A58"], night: ["#0A0F28", "#1E2A58"] };
CM.MOON_NAMES = ["new moon", "waxing crescent", "first quarter", "waxing gibbous", "full moon", "waning gibbous", "last quarter", "waning crescent"];
CM.UI.prototype.weatherIcon = function (w, size = 14) {
  const ray = (a) => { const c = Math.cos((a * Math.PI) / 180), s = Math.sin((a * Math.PI) / 180); return `<line x1="${(8 + c * 5.2).toFixed(1)}" y1="${(8 + s * 5.2).toFixed(1)}" x2="${(8 + c * 7).toFixed(1)}" y2="${(8 + s * 7).toFixed(1)}"/>`; };
  const body = {
    clear: `<circle cx="8" cy="8" r="3.4" fill="#F6D060"/><g stroke="#F6D060" stroke-width="1.4" stroke-linecap="round">${[0, 45, 90, 135, 180, 225, 270, 315].map(ray).join("")}</g>`,
    rain: `<path d="M4 9a3 3 0 0 1 1-5.8A4 4 0 0 1 12.6 5 2.6 2.6 0 0 1 12 9.6H4.6z" fill="#C8D0DC"/><g stroke="#7FB4F0" stroke-width="1.3" stroke-linecap="round"><line x1="5" y1="11.5" x2="4" y2="14.5"/><line x1="8.5" y1="11.5" x2="7.5" y2="14.5"/><line x1="12" y1="11.5" x2="11" y2="14.5"/></g>`,
    mist: `<g stroke="#C8CCD4" stroke-width="1.5" stroke-linecap="round"><line x1="2" y1="5" x2="14" y2="5"/><line x1="4" y1="8.5" x2="13" y2="8.5"/><line x1="2" y1="12" x2="12" y2="12"/></g>`,
    wind: `<g fill="none" stroke="#D8DCE4" stroke-width="1.4" stroke-linecap="round"><path d="M2 6h8a2 2 0 1 0-2-2"/><path d="M2 9.5h11a2 2 0 1 1-2 2"/><path d="M2 13h5"/></g>`,
    snow: `<g stroke="#F4F8FF" stroke-width="1.4" stroke-linecap="round"><line x1="8" y1="2" x2="8" y2="14"/><line x1="2.8" y1="5" x2="13.2" y2="11"/><line x1="2.8" y1="11" x2="13.2" y2="5"/></g>`,
  }[w] || "";
  return `<svg class="wxi" width="${size}" height="${size}" viewBox="0 0 16 16" aria-hidden="true">${body}</svg>`;
};
CM.UI.prototype.moonFace = function (phase, r, cls = "") {
  return `<svg class="moonface ${cls}" width="${r * 2 + 2}" height="${r * 2 + 2}" viewBox="${-r - 1} ${-r - 1} ${r * 2 + 2} ${r * 2 + 2}" data-phase="${phase}" aria-hidden="true"><circle class="dark" r="${r}"/><path class="lit" d="${CM.moonPath(phase, r)}"/><circle class="edge" r="${r}"/></svg>`;
};
Object.assign(CM.UI.prototype, {
  // the dial, drawn from the game's clock on each refresh
  drawSky() {
    const g = this.game, el = this.$("#view .sky"); if (!el || !el.querySelector(".dial")) return;
    const below = Boolean(g.floor && g.floor.number >= 1), D = CM.dialOf(g), w = CM.weather(g), f = CM.festival(g), season = CM.season(g);
    el.classList.toggle("underground", below); el.classList.toggle("night", D.night);
    const [top, low] = CM.SKY_COLOURS[D.sky];
    el.querySelector(".skytop").setAttribute("stop-color", top); el.querySelector(".skylow").setAttribute("stop-color", low);
    el.querySelector(".stars").style.opacity = D.sky === "night" ? 1 : D.sky === "day" ? 0 : 0.35;
    const place = (sel, a) => { const node = el.querySelector(sel), r = (a * Math.PI) / 180; node.setAttribute("transform", `translate(${(Math.sin(r) * 25).toFixed(2)} ${(-Math.cos(r) * 25).toFixed(2)})`); node.style.display = Math.abs(a) <= 100 ? "" : "none"; };
    place(".sun", D.sun); place(".moon", D.moon);
    el.querySelector(".moon .lit").setAttribute("d", CM.moonPath(D.phase, 6));
    el.querySelector(".ground").classList.toggle("stone", below);
    el.querySelector(".time").textContent = CM.timeFigures(g);
    el.querySelector(".hourword").textContent = `${CM.hourWord(D.hour)}${below ? ", above" : ""}`;
    const date = el.querySelector(".date"); date.textContent = `Day ${D.day + 1} - ${season}`; date.className = `date ${season}`;
    const ahead = CM.comingWeather(g, 4).slice(1);
    el.querySelector(".wx").innerHTML = `${this.weatherIcon(w, 14)}<span>${w}</span><span class="ahead" title="${this.esc("The days ahead: " + ahead.map((d) => `day ${d.day + 1}, ${d.weather}`).join("; "))}">${ahead.map((d) => this.weatherIcon(d.weather, 11)).join("")}</span>`;
    const fest = el.querySelector(".fest"); fest.textContent = f ? CM.FESTIVALS[f].name.charAt(0).toUpperCase() + CM.FESTIVALS[f].name.slice(1) : ""; fest.title = f ? CM.FESTIVALS[f].what : ""; fest.style.display = f ? "" : "none";
    const slot = el.querySelector(".moonslot"); slot.innerHTML = this.moonFace(D.phase, 10, D.phase === 4 ? "full" : D.phase === 0 ? "new" : "");
    slot.title = `The moon: ${CM.MOON_NAMES[D.phase]}, day ${D.moonDay} of ${CM.CLOCK.moon}${CM.MOON_DOES[D.phase] ? ` - ${CM.MOON_DOES[D.phase]}` : ""}`;
    el.dataset.phase = D.phase; el.dataset.sky = D.sky;
  },
  // the Mage Tower's HUD, drawn each frame while inside
  drawTowerHud(run) {
    const el = this.$("#towerhud"); if (!el) return; const h = run.hero, A = run.arms;
    el.querySelector(".tname").textContent = `${CM.towerFloorName(run.n)} - ${h.name} the ${h.cls}`;
    const bar = (sel, v, m) => { const b = el.querySelector(sel); b.style.display = m ? "" : "none"; if (!m) return; b.querySelector("i").style.width = `${Math.max(0, Math.min(100, (v / m) * 100))}%`; b.querySelector("span").textContent = `${Math.max(0, Math.ceil(v))} / ${m}`; };
    bar(".thp", h.hp, h.max); bar(".tmp", h.mp || 0, A.arrows ? 0 : h.maxmp);
    el.querySelector(".tarrows").textContent = A.arrows ? `Arrows: ${run.arrows}` : `${A.word}: ${A.cost} magic`;
    const boss = run.bossInSight ? run.bossInSight() : null, bb = el.querySelector(".tboss"); bb.style.display = boss ? "" : "none";
    const tip = run.atLadder() ? (run.n < CM.TOWER_FLOORS ? `E: climb to floor ${run.n + 1} - L: leave, floor ${run.n} counted` : "") : ""; el.querySelector(".tname").textContent += tip ? `   |   ${tip}` : "";
    if (boss) { bb.querySelector("b").textContent = boss.name; bb.querySelector("i").style.width = `${Math.max(0, (boss.m.hp / boss.m.max) * 100)}%`; }
  },
  // the Mage Tower's doors: the heroes, who may go in and who may not (and why)
  openMageTower() {
    const g = this.game, box = this.$("#magetower-who"), note = this.$("#magetower-note");
    box.innerHTML = g.towerChoices().map((c) => `<div class="recruit" style="grid-template-columns: 1fr auto"><div><b>${this.esc(c.name)}</b> the ${this.esc(c.cls)}${c.why ? `<br><small>${this.esc(c.why)}</small>` : ""}</div><div class="hire"><button data-tower-hero="${c.i}" ${c.why ? "disabled" : ""}>Go in</button></div></div>`).join("");
    for (const b of box.querySelectorAll("[data-tower-hero]")) b.addEventListener("click", () => { const why = g.enterMageTower ? g.enterMageTower(Number(b.dataset.towerHero)) : "The doors stay shut. Inside, something is still being built."; note.textContent = why || ""; if (!why) { this.closeDialogs(); this.refresh(); } });
    note.textContent = "";
    this.openDialog("#dlg-magetower");
  },
  // the Calendar: the moon's month, the seasons, the weather ahead and the year's festivals
  openCalendar() {
    const g = this.game, D = CM.dialOf(g), season = CM.season(g), f = CM.festival(g), month = new Date().getMonth(), today = CM.weather(g);
    const inDays = (k) => (k === 0 ? "tonight" : k === 1 ? "tomorrow night" : `in ${k} nights`);
    const faces = CM.MOON_NAMES.map((name, p) => `<div class="mface${p === D.phase ? " on" : ""}">${this.moonFace(p, 13, p === 4 ? "full" : p === 0 ? "new" : "")}<small>${name}</small></div>`).join("");
    const full = CM.nextMoon(g, 4), fresh = CM.nextMoon(g, 0);
    const seasons = CM.SEASONS.map((s) => { const [a, b] = CM.DAYLIGHT[s]; return `<tr class="${s === season ? "on" : ""}"><td class="${s}">${s}</td><td>dawn at ${a}, dusk at ${b}</td><td>${b - a} hours of day</td></tr>`; }).join("");
    const ahead = CM.comingWeather(g, 7).map((d, i) => `<div class="wday${i === 0 ? " on" : ""}">${this.weatherIcon(d.weather, 22)}<small>${i === 0 ? "today" : `day ${d.day + 1}`}</small><span>${d.weather}</span></div>`).join("");
    const cap = (t) => t.charAt(0).toUpperCase() + t.slice(1);
    const fests = Object.entries(CM.FESTIVALS).sort((a, b) => a[1].month - b[1].month).map(([id, F]) => `<tr class="${id === f ? "on" : F.month === month ? "month" : ""}"><td>${CM.MONTH_NAMES[F.month]}</td><td><b>${this.esc(cap(F.name))}</b>${id === f ? " <em>- this week</em>" : ""}<br><small>${this.esc(F.what)}</small></td></tr>`).join("");
    this.$("#calendar-body").innerHTML = `
      <div class="calnow">${this.moonFace(D.phase, 22, D.phase === 4 ? "full" : D.phase === 0 ? "new" : "")}<div><b class="caltime">${CM.timeFigures(g)}</b>, ${CM.hourWord(D.hour)}${g.floor && g.floor.number >= 1 ? " above" : ""} - day ${D.day + 1} of the run, ${season}${f ? `, ${this.esc(CM.FESTIVALS[f].name)}` : ""}<br>
        <small>This ${season} the sun rises at ${D.dawn} and sets at ${D.dusk}. Today: ${this.esc(CM.WEATHER_WORDS[today] || today)}.</small></div></div>
      <div class="list-title">The moon - day ${D.moonDay} of its ${CM.CLOCK.moon}: ${CM.MOON_NAMES[D.phase]}</div><div class="mfaces">${faces}</div>
      <p class="small">The next full moon: ${inDays(full)} - ${CM.MOON_DOES[4]}.<br>The next new moon: ${inDays(fresh)} - ${CM.MOON_DOES[0]}.</p>
      <div class="list-title">The weather ahead</div><div class="wdays">${ahead}</div>
      <div class="list-title">The seasons' daylight</div><table class="caltable">${seasons}</table>
      <div class="list-title">The year's festivals <small>(the week around the fifteenth)</small></div><table class="caltable fests">${fests}</table>`;
    this.openDialog("#dlg-calendar");
  },
});
