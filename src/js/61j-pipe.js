"use strict";
// The pipe in the Square (the seventeenth update): a great bronze pipe, green with age, standing up out of the cobbles
// at the Square's east corner. One of the party climbs in, and comes out in Super Claude Bros (64m-claudebros.js):
// four levels from 1-1 to 1-4, run and jump to each banner pole. Coins are gold and every foe is experience, whatever
// happens: a death brings the hero back up the pipe with a tenth of their health and everything they collected. Nothing
// else comes back - there is no gear to find in there.
CM.TOWN_PIPE = [23, 22];
CM.BROS_LINES = {
  in: (n) => `${n} climbs into the pipe. There is a long, echoing slide, a pop, and blue sky.`,
  dead: (n) => `${n} shoots back up out of the pipe in a shower of coins, dizzy and bruised.`,
  won: (n) => `${n} comes back up the pipe with the Brass Warden beaten and the last banner flying. What a place.`,
  left: (n) => `${n} climbs back up the pipe.`,
};
Object.assign(CM.Game.prototype, {
  enterBros(i) {
    const h = this.party[i]; if (!h) return "No one.";
    if (h.hp <= 0) return `${h.name} has fallen.`;
    if (this.mode !== "explore" || !this.floor || this.floor.number !== 0) return "The pipe is in the Square.";
    this.logAct && this.logAct("enterBros", i);
    this.brosRun = new CM.BrosRun(this, i, 0);
    this.say(CM.BROS_LINES.in(h.name));
    this.setMode("bros"); this.emit("bros", this.brosRun);
    return "";
  },
  // a banner pole reached: on to the next level, carrying the coins and the experience; after 1-4, home
  brosNext() {
    const r = this.brosRun; if (!r || !r.cleared) return null;
    this.tally.brosBest = Math.max(this.tally.brosBest || 0, r.li + 1);
    if (r.li + 1 >= CM.BR_LEVELS.length) return this.leaveBros("won");
    const next = new CM.BrosRun(this, r.heroIndex, r.li + 1, { coins: r.coins, xp: r.xp, kills: r.kills });
    this.brosRun = next; this.emit("brosLevel", next);
    return next;
  },
  // out of the pipe: the coins as gold and the experience, whichever way it ends; a death leaves a tenth of the health
  leaveBros(how) {
    const r = this.brosRun; if (!r) return null;
    const h = r.hero, gold = r.coins * CM.BR.coinGold, xp = Math.round(r.xp * CM.BR.xpShare);
    if (xp) { h.xp += xp; this.checkLevels(); }
    this.gold += gold;
    if (how === "dead") h.hp = Math.max(1, Math.round(h.max * 0.1)); else h.hp = Math.max(1, h.hp);
    if (how === "won") { this.achieve && this.achieve("bros"); this.tally.brosWins = (this.tally.brosWins || 0) + 1; }
    this.say(CM.BROS_LINES[how] ? CM.BROS_LINES[how](h.name) : CM.BROS_LINES.left(h.name));
    this.say(`From the pipe: ${r.coins} coins (${gold} gold)${xp ? ` and ${xp} experience` : ""}.`);
    this.brosRun = null;
    this.setMode("explore"); this.floor.pos = [CM.TOWN_PIPE[0] - 1, CM.TOWN_PIPE[1]]; this.floor.facing = 1;
    this.saveRun(); this.emit("floor", this.floor);
    return { how, gold, xp, coins: r.coins };
  },
});
