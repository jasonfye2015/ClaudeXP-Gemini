"use strict";
// Surrender and parley - the window's side (v38.3): the choice's answer goes to the rules (the choice dialog sends a
// surrender's answer to game.answerSurrender); under Automatic the party gives quarter. Rules: 69zze-surrender.js.
{ const ac0 = CM.UI.prototype.askChoice;
  CM.UI.prototype.askChoice = function (c, ...a) { if (c && c.surrender) { const g = this.game; if ((g.autoOn && g.autoOn()) || g.film) { g.answerSurrender(0); this.refresh(); return; }
      const out = ac0.call(this, c, ...a), box = this.$("#choice-options"); if (box) for (const [i, b] of [...box.querySelectorAll("button")].entries()) { const nb = b.cloneNode(true); b.replaceWith(nb); nb.addEventListener("click", () => { this.closeDialogs(); g.answerSurrender(i); this.refresh(); }); } return out; }
    return ac0.call(this, c, ...a); };
}
