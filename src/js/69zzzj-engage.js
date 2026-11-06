"use strict";
// Being engaged (UPGRADE_PLAN_67.md): when a fight begins with the foes on a square beside or behind the party, the
// party turns to face them first - before the fight's first blow, so the attacker is in view and a flight runs away
// from it. One group is one fight and one square, so the facing changes only at a fight's start: a second group that
// reaches the party mid-fight waits (as it always has) and is faced only when its own fight begins - no bouncing
// between attackers. Then the game says how the fight began, for the window's flourish:
//   game.on("engaged", { how, from, turned, facing })   how: ambush | met | drop;  from: ahead | right | behind | left
// The turn is part of the rules (the fight's dice don't read the facing, a flight does), so a replay turns the same.
{ CM.ENGAGE = { from: ["ahead", "right", "behind", "left"] };
  const P = CM.Game.prototype;
  const plainFloor = (game, fl) => fl && fl.pos && fl.grid && fl.number !== 0 && game.mode === "explore" && !(CM.isTowerFloor && CM.isTowerFloor(fl.number));   /* (the dungeon, the Wood, the Undercroft; not the town or the tower) */
  CM.engageFrom = (fl, key) => { if (!fl || !fl.pos || typeof key !== "string") return null; const [x, y] = key.split(",").map(Number), dx = x - fl.pos[0], dy = y - fl.pos[1]; if (Math.abs(dx) + Math.abs(dy) !== 1) return null; const d = CM.DIRS.findIndex(([ex, ey]) => ex === dx && ey === dy); return d < 0 ? null : d; };
  const sc0 = P.startCombat;
  P.startCombat = function (key, thing, theyCame = false) {
    const fl = this.floor; let turned = false, from = "ahead";
    if (plainFloor(this, fl)) { const d = CM.engageFrom(fl, key); if (d !== null && d !== fl.facing) { from = CM.ENGAGE.from[(d - fl.facing + 4) % 4]; fl.facing = d; turned = true; } }
    this.engagedHow = "met";
    const out = sc0.call(this, key, thing, theyCame);
    if (fl && this.floor === fl) this.emit("engaged", { how: this.engagedHow || "met", from, turned, facing: fl.facing, theyCame: Boolean(theyCame) });
    return out;
  };
}
