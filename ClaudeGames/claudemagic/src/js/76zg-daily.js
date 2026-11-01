"use strict";
// The Daily Challenge, the window's side (the fortieth big update): at the top of the gallery the board by the door -
// today's table (its picture and name), the three marks with a tick for each reached and a Collect for each waiting,
// the best so far today, the streak and what it adds, a Play button, anything carried over from before; a "Past
// days" view with the last fortnight. Inside today's table, the slim bar shows the challenge and how near it is. The
// rules are 64zp-daily.js.
{ const gal1 = CM.UI.prototype.cgGallery, nav1 = CM.UI.prototype.cgNav, r3 = CM.UI.prototype.renderCasino, DAILY = CM.DAILY, MED = ["#C88A50", "#C8D0D8", "#F0C040"], TIER = ["Bronze", "Silver", "Gold"];
  const nameOf = (id) => ((CM.CG_TABLES.find(([k]) => k === id) || [])[1]) || id;
  const what = (t, m) => (t === "pinball" ? `pass ${m} score marks` : t === "darts" || t === "skee" ? `score ${m * 100}` : t === "rings" ? `score ${m * 10} points` : `reach level ${m}`);
  Object.assign(CM.UI.prototype, {
    renderCasino() { if (this.cgView === "dailypast") { this.cgDailyPast(this.$("#casino-body")); this.cgToasts && this.cgToasts(); return; } return r3.call(this); },
    cgGallery(box) {
      gal1.call(this, box); const g = this.game, D = g.dlState(), mult = g.dlMult();
      const el = document.createElement("div"); el.className = "cgdaily";
      el.innerHTML = `<canvas width="132" height="72" data-dlthumb></canvas><div class="dlmain"><div class="dltitle"><b>Today's challenge</b><span>${D.day}${D.weekend ? " - weekend marks" : ""}</span></div>
        <div class="dlwhat">At <b>${nameOf(D.table)}</b>: ${what(D.table, D.marks[0])} for bronze, ${D.marks[1]} for silver, ${D.marks[2]} for gold. Best today: ${D.table === "pinball" ? `${D.best} marks` : `level ${D.best}`}.</div>
        <div class="dlmarks">${D.marks.map((m, i) => { const R = DAILY.REWARD[i]; return `<span class="dlmark ${D.got[i] ? "got" : ""}" style="--m:${MED[i]}"><i>${D.got[i] ? "✓" : m}</i>${TIER[i]}: ${Math.round(R.gold * mult)} gold${R.card ? ` + ${R.card === "better" ? "stronger" : R.card} card` : ""}${D.got[i] && !D.paid[i] ? ` <button class="primary" data-dlcollect="${i}">Collect</button>` : D.paid[i] ? " - collected" : ""}</span>`; }).join("")}</div>
        <div class="dlfoot">Streak: <b>${D.streak || 0} day${D.streak === 1 ? "" : "s"}</b>${(D.streak || 0) > 1 ? ` (+${Math.round((mult - 1) * 100)}% gold)` : ""} - every ${DAILY.streakCard}th day in a row brings a rare card.${D.streakUnpaid ? ` <button class="primary" data-dlcollect="streak">Collect the streak's card</button>` : ""}${(D.carry || []).length ? ` <button class="primary" data-dlcollect="carry">Collect ${D.carry.length} from before</button>` : ""}</div></div>
        <div class="dlside"><button class="primary" data-dlplay>Play</button><button data-dlpast>Past days</button></div>${this.dlOut || ""}`;
      box.querySelector(".cgclub").after(el); const c = el.querySelector("[data-dlthumb]"), f = CM.CG_THUMB[D.table]; if (f) f(c.getContext("2d"), c.width, c.height);
      el.querySelector("[data-dlplay]").addEventListener("click", () => { this.cgView = D.table; this.cgNote = `Today's challenge: ${what(D.table, D.marks[0])}.`; this.caSfx("cardplace", 0.35); this.renderCasino(); });
      el.querySelector("[data-dlpast]").addEventListener("click", () => { this.cgView = "dailypast"; this.renderCasino(); });
      el.querySelectorAll("[data-dlcollect]").forEach((b) => b.addEventListener("click", () => { const out = g.dlCollect(b.dataset.dlcollect); if (!out.gold && !out.cards.length) return; this.cgSfx("cardwin", 0.5); this.cgCoins(this.$("#casino-body"), 12); this.dlOut = `<div class="dlout">${out.gold ? `+${out.gold} gold ` : ""}${out.cards.map((x) => this.cgCardWon(x)).join("")}</div>`; this.renderCasino(); this.dlOut = ""; }));
      const strip = box.querySelector(".cgclub"); if (strip && g.dlUnpaid()) { const w = strip.querySelector(".cgwait"); const t = document.createElement("span"); t.className = "cgwait"; t.textContent = "Daily reward waiting"; if (w) w.after(t); else strip.appendChild(t); }
    },
    cgNav(box) {
      nav1.call(this, box); const D = this.game.dlState(); if (this.cgView !== D.table) return; const bar = box.querySelector(".cgbar"); if (!bar) return; const next = D.marks.findIndex((m, i) => !D.got[i]);
      const chip = document.createElement("span"); chip.className = "dlchip"; chip.textContent = next < 0 ? "Today's challenge: all three marks!" : `Today's challenge: ${what(D.table, D.marks[next])} for ${TIER[next].toLowerCase()} (best ${D.best})`; bar.querySelector(".cgname").after(chip);
    },
    cgDailyPast(box) {
      const D = this.game.dlState(), H = D.history || [];
      box.innerHTML = `<div class="cgdailypast"><p class="lore">The slate by the door, wiped each midnight - but the chalk-boy keeps a book.</p><table class="dlpast"><tr><th>Day</th><th>Table</th><th>Marks</th><th>Best</th><th>Reached</th></tr>${[{ day: D.day, table: D.table, marks: D.marks, best: D.best, got: D.got.filter(Boolean).length, today: true }, ...H].map((h) => `<tr class="${h.today ? "today" : ""}"><td>${h.day}${h.today ? " (today)" : ""}</td><td>${nameOf(h.table)}</td><td>${h.marks.join(" / ")}</td><td>${h.best}</td><td>${h.got ? TIER.slice(0, h.got).map((t, i) => `<span style="color:${MED[i]}">●</span>`).join("") + ` ${TIER[h.got - 1]}` : "-"}</td></tr>`).join("")}</table><div class="small">Streak: ${D.streak || 0}. Gold from daily challenges, all told: ${this.game.cgStore().dailyGold || 0}.</div></div>`;
      this.cgClubHead(box, "Daily challenges - the last fortnight");
    },
  });
}
