"use strict";
// The daily challenge, scored - the window's side (v33.3): Today's dungeon on the new party's screen shows the day's
// party, as the week's does, and says the day's rules; the title screen gains a page of the days played - each day's
// best score, its deepest floor and how many tries. Rules: 69zg-daily.js.
{ const oc0 = CM.UI.prototype.openCreate;
  CM.UI.prototype.openCreate = function (...a) { const seed = this.$("#seed").value, daily = String(seed).startsWith("daily-");
    if (daily) this.slots = CM.weeklyParty(seed); const out = oc0.apply(this, a);
    if (daily) { this.slots = CM.weeklyParty(seed); this.renderCreate && this.renderCreate(); const n = this.$("#create-note"); if (n) n.textContent += ` Today's rules: ${CM.DAILY_RULES}.`;
      for (const id of ["#kit", "#difficulty", "#ascension", "#again"]) { const el = this.$(id); if (el) el.disabled = true; } }
    else for (const id of ["#kit", "#difficulty", "#ascension"]) { const el = this.$(id); if (el) el.disabled = false; }
    return out; };
  const rt0 = CM.UI.prototype.refreshTitle;
  CM.UI.prototype.refreshTitle = function (...a) { const out = rt0.apply(this, a), g = this.game, ach = this.$("#achievements"); if (!ach || !g.dailyBoard) return out;
    let box = this.$("#daily-board"); if (!box) { box = document.createElement("div"); box.id = "daily-board"; ach.before(box); }
    const B = g.dailyBoard(), days = Object.keys(B).sort().reverse().slice(0, 10), today = CM.dailySeed().slice(6);
    box.innerHTML = days.length ? `<div class="list-title">Today's dungeon, day by day</div><table class="small" style="width:100%">${days.map((d) => `<tr${d === today ? ' style="color:#F0D080"' : ""}><td>${d}${d === today ? " (today)" : ""}</td><td>best <b>${B[d].best.toLocaleString("en")}</b></td><td>floor ${B[d].floor}${B[d].won ? ", crowned" : ""}</td><td>${B[d].tries} ${B[d].tries === 1 ? "try" : "tries"}</td></tr>`).join("")}</table>` : "";
    return out; };
}
