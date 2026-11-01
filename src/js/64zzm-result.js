"use strict";
// One way of telling a result (v16.6): whatever a table pays - gold, tickets, a card - is gathered here as it is paid,
// and the window shows it the same way at every table when the play is done (76zzp-controls.js). Tickets that come
// with laying a stake are not a win and aren't gathered; nor are chips cashed out at the residents' table.
{ const st0 = CM.Game.prototype.cgStake, pay0 = CM.Game.prototype.cgPay, tk0 = CM.Game.prototype.tkAdd, card0 = CM.Game.prototype.cgCard, tier0 = CM.Game.prototype.cgTierCard, CASH = ["holdem"];
  const res = (g) => (g.cgRes = g.cgRes || { gold: 0, tickets: 0, cards: [] });
  Object.assign(CM.Game.prototype, {
    cgStake(game, bet) { this.cgStaking = true; try { return st0.call(this, game, bet); } finally { this.cgStaking = false; } },
    cgPay(game, amount) { const n = pay0.call(this, game, amount); if (n > 0 && !CASH.includes(game)) { const R = res(this); R.gold += n; R.game = game; } return n; },
    tkAdd(n, why) { const k = tk0.call(this, n, why); if (k > 0 && !this.cgStaking) res(this).tickets += k; return k; },
    cgCard(rare, why, rnd) { const c = card0.call(this, rare, why, rnd); if (c && !this.cgTiering) res(this).cards.push(c); return c; },
    cgTierCard(tier, why, R) { this.cgTiering = true; let c; try { c = tier0.call(this, tier, why, R); } finally { this.cgTiering = false; } if (c) res(this).cards.push(c); return c; },
    // what has been won since last asked
    cgTakeResult() { const R = this.cgRes; this.cgRes = null; return R && (R.gold || R.tickets || R.cards.length) ? R : null; },
  });
}
