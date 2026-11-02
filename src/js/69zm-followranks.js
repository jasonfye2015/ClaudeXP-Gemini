"use strict";
// Followers who level (v35.0, UPGRADE_PLAN_30.md): a follower who comes through five new floors is seasoned, through
// ten a veteran - four more health a rank, and better at their trade: the porter carries ten more a rank; the
// torchbearer, seasoned, cups the flame so a gust doesn't take it, and as a veteran spots a trap a square off; the
// hedge-wizard, seasoned, mends twice a floor, and as a veteran her light lasts half again; the farm's dog goes five
// floors deeper a rank. The rescued adventurer keeps her own way. The rank is in the follower's name.
//   CM.FOLLOWER_RANKS; game.followerRank()
{ CM.FOLLOWER_RANKS = [{ floors: 5, name: "seasoned" }, { floors: 10, name: "veteran" }];
  const G = CM.Game.prototype, rank = (f) => (f ? CM.FOLLOWER_RANKS.filter((r) => (f.deep || 0) >= r.floors).length : 0);
  G.followerRank = function () { return rank(this.follower); };
  const fn0 = G.followerName; G.followerName = function () { const out = fn0.call(this), r = rank(this.follower); return r ? `${out} (${CM.FOLLOWER_RANKS[r - 1].name})` : out; };
  const of0 = G.followerOnFloor; G.followerOnFloor = function (number, fresh) {
    const f = this.follower, D = CM.FOLLOWERS.dog, deep0 = D.deepest; if (f && f.id === "dog") D.deepest = deep0 + 5 * rank(f);
    try { of0.call(this, number, fresh); } finally { D.deepest = deep0; }
    if (!f || this.follower !== f || f.away || f.id === "adventurer" || !(fresh && number >= 1 && number < 1000)) return;
    const before = rank(f); f.deep = (f.deep || 0) + 1; const after = rank(f);
    if (after > before) { f.max += 4; f.hp = f.max; const R = CM.FOLLOWER_RANKS[after - 1];
      const gift = { porter: "carries ten more", torchbearer: after === 1 ? "cups the flame against a gust" : "has learnt to see a trap a square off", wizard: after === 1 ? "can mend twice a floor" : "keeps her light half again as long", dog: "will go five floors deeper" }[f.id] || "is steadier";
      this.say(`${f.name} has come through ${f.deep} floors with you: ${R.name} now - and ${gift}.`); }
    if (f.id === "wizard" && after >= 2 && this.spellLight === 60) this.spellLight = 90; };
  const fc0 = G.followerCarry; G.followerCarry = function () { const out = fc0.call(this); return out + (this.followerIs("porter") ? 10 * rank(this.follower) : 0); };
  const burn0 = G.burn; G.burn = function (...a) { const was = this.gutter || 0, out = burn0.apply(this, a);
    if ((this.gutter || 0) > was && this.followerIs("torchbearer") && rank(this.follower) >= 1) { this.gutter = 0; this.say(`${this.follower.name} cups a hand round the flame: the gust doesn't take it.`); }
    return out; };
  const look0 = G.look; G.look = function (...a) { const out = look0.apply(this, a), f = this.follower, fl = this.floor;
    if (f && fl && this.followerIs("torchbearer") && rank(f) >= 2 && CM.isDeep(fl.number)) { const [x, y] = fl.pos;
      for (const [k, ft] of Object.entries(fl.features || {})) { const [tx, ty] = k.split(",").map(Number); if (Math.abs(tx - x) + Math.abs(ty - y) !== 1) continue;
        if ((ft.type === "trapdoor" && !ft.known) || (ft.type === "plate" && ft.trap && !ft.known && !ft.spent)) { ft.known = true; this.say(`${f.name} holds the torch low: "Mind the floor there."`); } } }
    return out; };
  const af0 = G.followerAfterFight; G.followerAfterFight = function (...a) { const f = this.follower, out = af0.apply(this, a);
    if (f && this.followerIs("wizard") && rank(f) >= 1 && f.mended === this.floor.number && f.mended2 !== this.floor.number) { f.mended2 = this.floor.number; f.mended = null; af0.apply(this, a); f.mended = this.floor.number; }
    return out; };
}
