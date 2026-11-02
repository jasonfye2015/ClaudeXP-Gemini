"use strict";
// Townsfolk who remember - the window's side (v36.2): when the party steps beside one of the residents walking the town
// (where 76zzzzy-townsfolk.js has them this hour), the resident greets it - once a day each. Rules: 69zt-remember.js.
{ const em0 = CM.Game.prototype.emit;
  CM.Game.prototype.emit = function (ev, ...a) { const out = em0.call(this, ev, ...a);
    if (ev === "moved" && this.floor && this.floor.number === 0 && this.greet && CM.townsfolkNow && !this.replaying && !this.film && !(this.autoOn && this.autoOn())) { const [x, y] = this.floor.pos;
      for (const [who, at] of CM.townsfolkNow(this, this.floor)) if (at && Math.abs(at[0] - x) + Math.abs(at[1] - y) <= 1) { this.greet(who); break; } }
    return out; };
}
