"use strict";
// The house furnished - the window's side (v32.3): two more rooms in the house's window - the furnishings to buy (and
// those bought), and the trophies to mount on the wall and take down, with what each gives. Rules: 69zc-furnish.js.
{ const oh0 = CM.UI.prototype.openHome;
  CM.UI.prototype.openHome = function (...a) {
    const out = oh0.apply(this, a), g = this.game, box = this.$("#home-rooms"); if (!box || !g.furnished || g.homeLevel() < 1) return out;
    const note = this.$("#home-note"), say = (t) => { note.textContent = t || "Done."; this.openHome(true); this.refresh(); }, FN = CM.FURNISH, F = g.furnished();
    const d = document.createElement("div"); d.innerHTML = `<div class="list-title">Furnishings (${Object.keys(F).length} of ${Object.keys(FN).length})</div>`;
    for (const [id, f] of Object.entries(FN)) { const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      row.innerHTML = `<div><b>${this.esc(f.name)}</b> <small>${this.esc(f.what)}</small></div>`; const b = document.createElement("button"); const why = g.furnishWhy(id);
      b.textContent = F[id] ? "In the house" : `${f.gold} gold`; b.disabled = Boolean(why); if (why && !F[id]) b.title = why; b.addEventListener("click", () => say(g.buyFurnish(id))); row.appendChild(b); d.appendChild(row); }
    box.appendChild(d);
    if (g.homeLevel() >= 2) { const w = document.createElement("div"), M = g.mounted(), won = Object.keys(g.trophies || {}).filter((id) => CM.TROPHY_GIFT[id]);
      w.innerHTML = `<div class="list-title">Mounted on the wall (${M.length} of ${g.mountRoom()})</div><div class="small">Each trophy mounted gives every hero who sets out +1 to its guardian's own: the Rat King's luck, the Knight's constitution...</div>`;
      if (!won.length) w.innerHTML += `<div class="small">No guardian's trophy yet: they are won on the floors they keep.</div>`;
      for (const id of won) { const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto"; const on = M.includes(id);
        row.innerHTML = `<div><b>${this.esc(CM.GUARDIANS[id].name)}</b> <small>+1 ${this.esc(CM.STAT_NAMES[CM.TROPHY_GIFT[id]])}</small></div>`; const b = document.createElement("button"); const why = on ? "" : g.mountWhy(id);
        b.textContent = on ? "Take down" : "Mount"; b.disabled = Boolean(why); if (why) b.title = why; b.addEventListener("click", () => say(on ? g.unmountTrophy(id) : g.mountTrophy(id))); row.appendChild(b); w.appendChild(row); }
      box.appendChild(w); }
    return out; };
}
