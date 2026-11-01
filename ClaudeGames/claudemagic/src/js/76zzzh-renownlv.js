"use strict";
// One name across the world, the window's side: in the village's window, under the renown, the renown level - a bar to
// the next, what every part of the world has added, and the perks, got and to come; and a level gained goes up with
// the level-up jingle and a burst at the top of the view. The rules are 69h-renownlv.js.
{ const RL = CM.RENOWNLV, rv0 = CM.UI.prototype.renderVillage;
  const bind = (ui) => { if (ui.rlBound || !ui.game || !ui.game.on) return; ui.rlBound = true; ui.game.on("renownlevel", (n) => { try { CM.soloLevelFlourish ? CM.soloLevelFlourish("Renown", n) : null; } catch (e) { /* quiet */ } }); };
  Object.assign(CM.UI.prototype, {
    renderVillage() { const out = rv0.call(this); bind(this); const g = this.game; if (!g.rlInfo) return out; g.rlSync(); const I = g.rlInfo(), at = this.$("#village-renown"); if (!at) return out;
      let box = this.$("#village-rl"); if (!box) { box = document.createElement("div"); box.id = "village-rl"; box.className = "rlbox"; at.after(box); }
      const pc = I.next === null ? 100 : Math.round((100 * (I.earned - I.from)) / (I.next - I.from)), open = this.rlOpen;
      box.innerHTML = `<div class="rlhead"><b class="rllv">${I.level}</b><div><b>Renown level ${I.level}</b> <span class="small">${I.next === null ? "the highest" : `${I.earned.toLocaleString("en")} of ${I.next.toLocaleString("en")} renown earned to level ${I.level + 1}`}</span><div class="flbar"><i style="width:${pc}%"></i></div></div><button data-rlmore>${open ? "Less" : "Where it comes from"}</button></div>
        ${open ? `<div class="rlcols"><div><div class="list-title">Every part of the world adds</div>${I.areas.map((a) => `<div class="rlrow"><span>${this.esc(a.name)} <i>(${this.esc(a.how)})</i></span><b>${a.renown}</b></div>`).join("")}<div class="rlrow"><span>The dungeon's runs, the village's deeds and requests</span><b>${Math.max(0, I.earned - I.areas.reduce((n, a) => n + a.renown, 0))}</b></div></div>
          <div><div class="list-title">What the level gives, everywhere</div>${I.perks.map((p) => `<div class="rlrow${p.have ? " have" : ""}"><span>${p.have ? "&#10003;" : `at ${p.level}`}</span><span>${this.esc(p.words)}</span></div>`).join("")}</div></div>` : ""}`;
      box.querySelector("[data-rlmore]").addEventListener("click", () => { this.rlOpen = !this.rlOpen; this.renderVillage(); }); return out; },
  });
}
