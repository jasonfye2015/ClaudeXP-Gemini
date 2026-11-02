"use strict";
// A follower's fear (v35.3, UPGRADE_PLAN_30.md): on coming to a new floor that is dark - from the Lich King's palace
// down, or with the party's light shaded - a follower may lose their nerve and bolt for the stair, gone for good, if the
// party's heart is below Steady: the lower it is the likelier, and the more seasoned they are the steadier (a half as
// likely seasoned, a quarter a veteran). Hired help only; the farm's dog never runs, nor the one you cut loose.
//   CM.FEAR; game.fearChance(number)
{ CM.FEAR = { below: 50, most: 0.35, darkBand: 3 };
  const G = CM.Game.prototype, F = CM.FEAR;
  G.fearChance = function (number) { const f = this.follower; if (!f || f.away || !["porter", "torchbearer", "wizard"].includes(f.id)) return 0;
    const dark = (number >= 1 && number < 1000 && CM.themeIndex(number) >= F.darkBand) || this.lightOut, morale = this.morale === undefined ? CM.MORALE.start : this.morale;
    if (!dark || morale >= F.below) return 0; const rank = this.followerRank ? this.followerRank() : 0; return F.most * ((F.below - morale) / F.below) * [1, 0.5, 0.25][rank]; };
  const of0 = G.followerOnFloor; G.followerOnFloor = function (number, fresh) { const chance = fresh ? this.fearChance(number) : 0, f = this.follower;
    of0.call(this, number, fresh);
    if (chance > 0 && f && this.follower === f && (CM.hashSeed(`${this.seed}:fear:${number}:${f.name}`) % 1000) / 1000 < chance) {
      this.say(`${f.name} looks down the dark of the stair, then back at you, and shakes their head. "Not this. Not for any money." They're gone up the stair before anyone can say a word.`);
      this.follower = null; this.tally.followersFled = (this.tally.followersFled || 0) + 1; this.emit && this.emit("change"); }
    else if (f && this.follower === f && chance > 0.12 && fresh) this.say(`${f.name} is very quiet on this floor, and keeps close to the light.`); };
}
