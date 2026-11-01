"use strict";
// Who's next (v23.3, UPGRADE_PLAN_18.md): in a fight, a strip along the foot of the view shows this round's order -
// heroes and foes as the dice and their speed set them (62-combat.js beginRound: game.combat.order) - the one acting
// lit, those done dimmed, the fallen struck through, a foe numbered as its tag over its head. It moves on as each
// acts and is dealt again each round.
{ const short = (s, n = 11) => (s.length > n ? s.slice(0, n - 1) + "." : s);
  CM.UI.prototype.renderOrder = function () {
    const g = this.game, view = this.$("#view"); if (!view) return;
    let strip = view.querySelector(".turnstrip");
    const c = g.mode === "combat" ? g.combat : null;
    if (!c || !c.order || !c.order.length) { if (strip) { strip.classList.remove("on"); this.orderKey = ""; } return; }
    if (!strip) { strip = document.createElement("div"); strip.className = "turnstrip"; view.appendChild(strip); }
    const living = g.attackable ? g.attackable() : g.living(), now = c.waiting ? c.order.findIndex((s) => s.hero === c.waiting) : c.index - 1;
    const cells = c.order.map((s, i) => { const who = s.hero || s.foe, dead = who.hp <= 0 || who.fled, n = s.foe ? living.indexOf(s.foe) : -1;
      const cls = ["t", s.hero ? "hero" : "foe", i === now ? "now" : i < now ? "done" : "", dead ? "dead" : "", s.foe && s.foe.hidden ? "hid" : ""].filter(Boolean).join(" ");
      const name = s.hero ? who.name : s.foe.hidden ? "?" : (n >= 0 ? `[${n + 1}] ` : "") + short(who.name);
      return [cls, name, s.hero ? who.cls : ""]; });
    const key = `${c.round}|${now}|` + cells.map((x) => x[0] + x[1]).join(",");
    if (key === this.orderKey) return;
    this.orderKey = key;
    strip.innerHTML = `<span class="rd">Round ${c.round}</span>` + cells.map(([cls, name]) => `<span class="${cls}">${this.esc(name)}</span>`).join("");
    strip.classList.add("on");
  };
  const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a); try { this.renderOrder(); } catch (e) { /* (the strip is only a picture) */ } return out; };
  const bind = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { if (!this.orderBound && this.game && this.game.on) { this.orderBound = true; for (const ev of ["turn", "round", "change", "mode"]) this.game.on(ev, () => { try { this.renderOrder(); } catch (e) { /* */ } }); } return bind.apply(this, a); };
}
