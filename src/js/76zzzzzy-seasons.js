"use strict";
// Seasons of the year - the window's side (v33.1): the Calendar (K) tells this season's trial, how far this run has
// come at it, and the trials done in other seasons; the side panel's date line marks a trial still open. Rules:
// 69ze-seasons.js.
{ const oc0 = CM.UI.prototype.openCalendar;
  CM.UI.prototype.openCalendar = function (...a) { const out = oc0.apply(this, a), g = this.game, body = this.$("#calendar-body"); if (!body || !g.trialKey) return out;
    const s = CM.season(g), T = CM.SEASON_TRIALS[s], V = g.vext("seasons"), done = V[g.trialKey()], it = T.reward();
    const past = Object.entries(V).filter(([k]) => k !== g.trialKey()).map(([k, v]) => `${k.split("-")[1]} ${k.split("-")[0]}: ${v.item}`);
    const d = document.createElement("div"); d.className = "trialbox";
    d.innerHTML = `<div class="list-title">This ${s}'s trial: ${this.esc(T.name)}</div><p class="small">To ${this.esc(T.what)}. ${done ? `<b>Done</b> (${this.esc(done.date || "")}): ${this.esc(done.item)}.` : `Once a season; it gives <b>${this.esc(it.name)}</b> (${this.esc(CM.itemLabel ? CM.itemLabel(it) : "")}). This run: ${this.esc(g.trialProgress())}.`}</p>`
      + `<p class="small">The year's four: ${Object.entries(CM.SEASON_TRIALS).map(([k, t]) => `${k} - ${this.esc(t.name)}`).join("; ")}.${past.length ? ` Done before: ${this.esc(past.join("; "))}.` : ""}</p>`;
    body.prepend(d); return out; };
}
