"use strict";
// The gate towers, their lookout, and the east postern (the eleventh update, phase 4). The ring wall steps round the
// hill in diagonals and runs into hedges and the Temple, so it is not a walk a party can take square by square; the
// plan's own fallback is taken: the two towers that flank the West Gate are climbed by a stair at their foot, and the
// party stands on the top among the merlons, with the town below and the watchman's word on tomorrow's weather. The
// postern is a small door in the Keep-yard's north-east corner, opening (once the party has been down to the fifth
// floor, in this run or any) onto a path cut along the foot of the cliffs to the fields: the short way from the shaft to
// the land.
CM.TOWER = { h: 2.3, r: 0.62, merlon: 0.32, climbMinutes: 6 };
CM.TOWN_TOWERS = [[3, 18], [2, 20]];                                     // flanking the West Gate
CM.TOWER_STAIRS = { "4,18": [3, 18], "3,20": [2, 20] };                  // the stair at each tower's foot, inside the wall -> its tower
CM.TOWN_POSTERN = [37, 18];                                              // the Keep-yard's north-east corner
CM.POSTERN_LAND = [57, 13];                                              // the door in the cliff, on the land
CM.POSTERN_PATH = [57, 13, 57, 19];                                      // the cliff path, down to the fields
CM.POSTERN_FROM = 5;                                                     // the floor a party must have reached
CM.TOMORROW_WORDS = { clear: "Fair, and the same after.", rain: "Rain, out of the west. Bring a hood.", mist: "Mist on the low ground in the morning.", wind: "Wind. The beasts won't smell you coming.", snow: "Snow. Look at that sky." };
CM.posternOpen = (game) => Boolean(game && ((game.village && game.village.posternOpen) || Math.max(0, ...(game.trail || []).map((t) => t[0] || 0)) >= CM.POSTERN_FROM));

Object.assign(CM.Game.prototype, {
  // up the tower stair: the party stands on the top (this.perch, never saved: a run loads at the stair's foot)
  climbTower(k) {
    const tower = CM.TOWER_STAIRS[k];
    if (!tower || this.perch || !this.floor || this.floor.number !== 0) return false;
    this.perch = { tower: tower.slice(), from: k };
    this.clock = (this.clock || 0) + CM.TOWER.climbMinutes;
    const ahead = CM.comingWeather(this, 2)[1], D = CM.dialOf(this);
    this.sound("step");
    this.say(`Up the tower stair, round and round, and out among the merlons: the town below, the wall running off round the hill, the trees beyond it. The watchman nods. "Tomorrow? ${CM.TOMORROW_WORDS[ahead.weather] || CM.TOMORROW_WORDS.clear}"`);
    if (!D.night && D.dusk - D.hour <= 1.5) { this.say("The sun goes down over the Wood, and the whole town is gold for a moment."); this.achieve("tower"); }
    this.emit("change");
    return true;
  },
  climbDown() {
    if (!this.perch) return false;
    this.perch = null;
    this.clock = (this.clock || 0) + CM.TOWER.climbMinutes;
    this.say("Down the tower stair to the street.");
    this.emit("change");
    return true;
  },
  // the postern: from the Keep-yard to the cliff path, and back; shut until the party has been down to the fifth floor
  postern() {
    const fl = this.floor;
    if (!CM.posternOpen(this)) { this.sound("bump"); this.say(`A small iron door in the yard's wall, the postern. The guild keeps it shut for those who haven't been down past the ${CM.ordinal ? CM.ordinal(CM.POSTERN_FROM) : "fifth"} floor.`); return false; }
    if (this.village && !this.village.posternOpen) { this.village.posternOpen = true; if (this.saveVillage) this.saveVillage(); this.say("The guild's man unbars the postern for you: \"You've been down far enough to be trusted with it.\""); }
    this.sound("door");
    if (fl.number === 0) { this.enterFloor(-1, "rope", CM.POSTERN_LAND.slice()); this.say("Through the postern and down the cliff path, the hill's side on your right, the fields below."); }
    else { this.enterFloor(0, "rope", CM.TOWN_POSTERN.slice()); this.say("Up the cliff path and in at the postern: the Keep-yard, and the shaft."); }
    return true;
  },
});
