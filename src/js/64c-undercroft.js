"use strict";
// The Undercroft (the eleventh update, phase 6): the lower town that "went under", three floors below the Wood's
// deepest cave - floors -2, -3 and -4 in the save, "the Undercroft, first vault" and so on in words. A stair of old
// stone in the third cave is found only with a light (it lies hidden until a lit party stands near it). Its floors are
// carved by generator 2 from a key of their own (no floor of the shaft moves), then made the Undercroft's: its own five
// kinds, a carving a floor that tells what the town forgot, standing water; on the third, the tenth guardian - the
// Bell-Founder's Boy, grown old and dead and still ringing a bell nobody hears; his bell wakes every lair on the floor -
// and past him a door into the Flooded Vaults. Through that door (once he has fallen, and once a party has been down to
// floor six) the Undercroft is a way to floor six that skips the Catacombs, and a way up from the Vaults into the Wood.
CM.UNDERCROFT_FLOORS = [-2, -3, -4];
CM.isUndercroft = (n) => n <= -2 && n >= -4 && n % 1 === 0;
CM.isDeep = (n) => n >= 1 || CM.isUndercroft(n);                          // (a dungeon floor: lairs, a light to shade, noise)
CM.UNDERCROFT_LEVEL = (n) => 7 + (-n - 2);                                // the monsters' level: seven, eight, nine
CM.UNDERCROFT_DOOR_FROM = 6;                                              // the floor a party must have reached for the door to open
CM.UNDERCROFT_THEME = Object.assign({}, CM.THEMES[4], {
  name: "The Undercroft", floors: [-4, -2], stone: [80, 86, 80], mortar: [32, 36, 34], floor: [56, 62, 58], ceiling: [40, 46, 44], moss: [70, 120, 90],
  fog: [0.022, 0.032, 0.03], torch: [0.98, 0.86, 0.66], reach: 5.0, bones: 0.25, photos: "t1", pixel: "t4", undercroft: true, grade: [0.96, 1.0, 0.98],
});
CM.UNDERCROFT_NAMES = ["the Undercroft, first vault", "the Undercroft, the drowned street", "the Undercroft, the bell-yard"];
// the Undercroft's own kinds: never among the shaft's bands (they carry `undercroft`, as the Wood's carry `wood`)
CM.UNDERCROFT_KINDS = [
  { name: "Drowned Townsfolk", colour: "#5A6A64", body: "biped", head: "pale", eyes: "#C0E0D0", extras: ["torn"], skin: "rot", speed: 6, undead: true, touch: { status: "sleep", chance: 0.1 }, undercroft: true, shape: [1.1, 0.9, 0.8] },
  { name: "Eel", colour: "#2E4A40", body: "beast", head: "snout", eyes: "#E0F060", extras: ["tail"], speed: 15, ability: "ranged", touch: { status: "paralysis", chance: 0.2 }, undercroft: true, shape: [0.8, 1.1, 0.5] },
  { name: "Marsh Light", colour: "#B8E8A0", body: "ghost", head: "pale", eyes: "#FFFFE0", extras: [], speed: 16, ability: "coward", undercroft: true, shape: [0.6, 0.8, 0.3], flees: true },
  { name: "Cellar Spider", colour: "#3A3028", body: "beast", head: "round", eyes: "#FF4040", extras: ["claws"], speed: 13, ability: "web", touch: { status: "poison", chance: 0.25 }, undercroft: true, shape: [0.9, 1.0, 0.7] },
  { name: "Bell-Ringer", colour: "#4A4440", body: "tall", head: "hood", eyes: "#E8D080", extras: ["torn"], speed: 9, undead: true, ability: "howl", undercroft: true, shape: [1.4, 1.2, 1.0] },
];
for (const k of CM.UNDERCROFT_KINDS) if (!CM.MONSTERS.some((m) => m.name === k.name)) CM.MONSTERS.push(k);
// the tenth guardian
CM.GUARDIANS.bell = {
  floor: -4, name: "The Bell-Founder's Boy", colour: "#6A6458", body: "tall", head: "hood", eyes: "#F0E0A0", extras: ["torn", "crown"], speed: 9, size: 1.0,
  hp: 360, atk: 24, df: 10, xp: 1800, gold: 900, touch: { status: "sleep", chance: 0.2 }, weak: "holy", resist: "frost", undead: true,
  escorts: ["Drowned Townsfolk", "Drowned Townsfolk"], tint: "rgba(200,190,140,0.35)", warn: "The Bell-Founder's Boy lifts the bell, and every face in the room turns to it.",
  moves: [{ kind: "summon", what: "Drowned Townsfolk", n: 2, max: 4, word: "townsfolk", text: "The bell swings, and {n} of the drowned townsfolk come up out of the water to it!" }], passives: ["bell"],
  abilities: [["The bell", "it rings: every lair on the floor wakes, and the party's heart sinks a little"], ["The drowned", "the townsfolk come to the bell, two at a time"]],
  intro: "In the bell-yard, under the water's sound, something old stands holding a bell with no tongue in it, and swings it, and swings it. The Bell-Founder's Boy, grown old down here, and dead, and still ringing.",
  fall: "The bell drops, and for the first time in a hundred years the Undercroft is quiet.",
  take: "The bell is cracked through. But its tongue was in his other hand all along: iron, heavy, and still humming.",
  lore: "The founder cast the last bell of the lower town, and sent his boy down to hang it the night the water came.",
  relic: { name: "The Bell's Tongue", kind: "weapon", slot: "weapon", power: 10, value: 1000, props: { relic: true, shriek: true, element: "holy" } },
  lair: { name: "The Bell-yard", lore: "g:bell", rows: ["#########", "#.......#", "#...B...#", "#.......#", "####D####"] },
};
CM.UNDERCROFT_LORE = [
  "Carved low on a cellar wall, under the waterline: THE LOWER TOWN DID NOT FALL. IT WAS LET GO. THE HILL CLOSED ITS GATE.",
  "Scratched into a door, by many hands: they rang the bells for us to come up. then they stopped ringing. we heard them stop.",
  "Round the base of the bell-yard's cross: TO THOSE ABOVE - KEEP THE NIGHT OF BELLS. WE WILL LISTEN FOR IT.",
];
for (let i = 0; i < 3; i++) CM.LORE_TEXT[`undercroft.${i + 1}`] = { key: `undercroft.${i + 1}`, chapter: "undercroft", order: i + 1, text: CM.UNDERCROFT_LORE[i], tellings: [CM.UNDERCROFT_LORE[i]], floor: -2 - i };
CM.CHAPTERS.undercroft = { name: "The lower town", epigraph: "What the hill forgot, and what was written down where no one would read it." };

// the relic's base, as 14-items.js makes the others' (it was read before this file)
{ const R = CM.GUARDIANS.bell.relic, like = CM.BASES["Rat King's Crown"] || {}; CM.BASES[R.name] = Object.assign({}, like, { id: R.name, kind: R.kind, slot: R.slot, tier: 9, group: "relic" }); }
// the three floors, by generator 2 from keys of their own, made the Undercroft's
CM.makeUndercroft = function (number, seed) {
  const i = -number - 2, level = CM.UNDERCROFT_LEVEL(number), fl = CM.makeFloor(level, `${seed}:undercroft:${i}`, 2);
  fl.number = number; fl.special = "undercroft"; fl.hazard = null; delete fl.wing;
  for (const [k, t] of Object.entries(fl.things)) {
    if (t.type === "stairs_up") fl.things[k] = { type: "ucup" };
    else if (t.type === "ladder" || t.type === "boss" || t.type === "guardian") fl.things[k] = { type: i < 2 ? "ucdown" : "ucdoor" };
    else if (!["chest", "monsters", "key"].includes(t.type)) delete fl.things[k];
  }
  for (const [k, f] of Object.entries(fl.features)) { if (["teleporter", "spinner", "trapdoor"].includes(f.type)) delete fl.features[k]; else if (f.type === "carving") f.text = `u:${i}`; }
  if (!Object.values(fl.things).some((t) => t.type === "ucup")) fl.things[CM.keyOf(fl.pos[0], fl.pos[1])] = { type: "ucup" };
  // its own kinds, by a hash of the floor; a Bell-Ringer leads one pack a floor (a champion that shrieks)
  const rnd = new CM.Random(CM.hashSeed(`${seed}:ucgroups:${i}`)), kinds = CM.UNDERCROFT_KINDS.filter((k) => k.name !== "Bell-Ringer");
  let ringer = false;
  for (const k of Object.keys(fl.things).sort()) {
    const t = fl.things[k];
    if (t.type !== "monsters") continue;
    const kind = rnd.pick(kinds), n = kind.name === "Marsh Light" ? 1 : rnd.int(2, 3), group = [];
    for (let j = 0; j < n; j++) group.push(CM.makeMonster(kind, level, rnd));
    const keep = { asleep: t.asleep };
    fl.things[k] = Object.assign({ type: "monsters", group }, keep, kind.flees ? { flees: true, asleep: false } : {});
    if (!ringer && !kind.flees) { ringer = true; fl.things[k].group.unshift(CM.makeMonster(CM.monsterKind("Bell-Ringer"), level, rnd)); CM.makeChampion(fl.things[k], "shrieking"); fl.things[k].asleep = true; }
  }
  if (i === 2) {                                                         // the bell-yard: the guardian between the stair and the door
    const door = Object.keys(fl.things).find((k) => fl.things[k].type === "ucdoor"), [dx, dy] = door.split(",").map(Number);
    const near = CM.distances(fl.grid, [dx, dy], (x, y) => CM.isOpen(fl, x, y)), spot = [...near.entries()].filter(([k, d]) => d >= 1 && d <= 3 && !fl.things[k] && !fl.features[k]).sort((a, b) => a[1] - b[1] || (a[0] < b[0] ? -1 : 1))[0];
    if (spot) fl.things[spot[0]] = { type: "guardian", group: CM.guardianGroup("bell", 9, new CM.Random(CM.hashSeed(`${seed}:bell`))) };
  }
  return fl;
};
// the way down from the third cave: a stair of old stone, somewhere far from the way out, hidden until a light finds it
CM.undercroftStairOf = function (fl, seed) {
  const exit = Object.keys(fl.things).find((k) => fl.things[k].type === "caveexit"), from = exit ? exit.split(",").map(Number) : fl.pos;
  const d = CM.distances(fl.grid, from, (x, y) => CM.isOpen(fl, x, y)), far = [...d.entries()].filter(([k]) => !fl.things[k] && !fl.features[k]).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
  return far.length ? far[CM.hashSeed(`${seed}:ucstair`) % Math.min(4, far.length)][0] : null;
};
CM.undercroftDoorOpen = (game) => Boolean(game && game.village && game.village.undercroftDoor);

Object.assign(CM.Game.prototype, {
  // the stair found: a lit party within two squares of it
  findUndercroft() {
    const fl = this.floor;
    if (!fl || fl.cave !== 2 || !this.hasLight() || this.lightOut) return false;
    for (const [k, t] of Object.entries(fl.things)) {
      if (t.type !== "ucstair" || !t.hidden) continue;
      const [x, y] = k.split(",").map(Number);
      if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 2) { t.hidden = false; this.dirty = true; this.say("Your light catches a stair of old cut stone going down, older than the cave: worn steps, and a cold breath off water."); return true; }
    }
    return false;
  },
  // the Undercroft's ways: down from the cave, down and up between its floors, out by the cave, the door to the Vaults
  undercroftWay(t, k) {
    const fl = this.floor;
    this.sound("stairs");
    if (t.type === "ucstair") { if (t.hidden) return false; this.enterFloor(-2, "down"); this.say("Down the old steps, and down: the Undercroft. Water stands in the streets of a town that was here before the hill shut its gate."); return true; }
    if (t.type === "ucdown") { this.enterFloor(fl.number - 1, "down"); this.say(`Down again: ${CM.UNDERCROFT_NAMES[-fl.number + 1 - 2] || "deeper"}.`); return true; }
    if (t.type === "ucup") {
      if (fl.number === -2) { const cave = CM.caveNumber(2), cf = this.floorAt(cave), at = Object.keys(cf.things).find((x) => cf.things[x].type === "ucstair"); this.enterFloor(cave, "rope", at ? at.split(",").map(Number) : null); this.say("Up the old steps into the cave."); return true; }
      const up = fl.number + 1, uf = this.floorAt(up), at = Object.keys(uf.things).find((x) => uf.things[x].type === "ucdown"); this.enterFloor(up, "rope", at ? at.split(",").map(Number) : null); this.say("Up, toward the cave."); return true;
    }
    if (t.type === "ucdoor") {
      const slain = (this.tally.guardians || []).includes("bell") || CM.undercroftDoorOpen(this), deepEnough = Math.max(0, ...(this.trail || []).map((x) => x[0] || 0)) >= CM.UNDERCROFT_DOOR_FROM || CM.undercroftDoorOpen(this);
      if (!slain) { this.sound("bump"); this.say("A door of black oak in the bell-yard's wall, swollen shut. Something in this yard is keeping it."); return false; }
      if (!deepEnough) { this.sound("bump"); this.say("The door gives an inch onto dark water and a stair going up - into the Flooded Vaults, by the smell. You'd want to know those halls first: come back when you've been down to the sixth floor."); return false; }
      if (this.village && !this.village.undercroftDoor) { this.village.undercroftDoor = true; if (this.saveVillage) this.saveVillage(); }
      this.enterFloor(CM.UNDERCROFT_DOOR_FROM, "down"); this.say("Through the black door and up a flooded stair: the Flooded Vaults, from below.");
      return true;
    }
    if (t.type === "ucback") { const df = this.floorAt(-4), at = Object.keys(df.things).find((x) => df.things[x].type === "ucdoor"); this.enterFloor(-4, "rope", at ? at.split(",").map(Number) : null); this.say("Down the flooded stair and through the black door: the bell-yard."); return true; }
    return false;
  },
  // on the sixth floor, once the door is open: the flooded stair down to the bell-yard
  layUndercroftBack(fl) {
    if (!fl || fl.number !== CM.UNDERCROFT_DOOR_FROM || !CM.undercroftDoorOpen(this) || Object.values(fl.things).some((t) => t.type === "ucback")) return;
    const top = Object.keys(fl.things).find((k) => fl.things[k].type === "stairs_up"), from = top ? top.split(",").map(Number) : fl.pos;
    const d = CM.distances(fl.grid, from, (x, y) => CM.isOpen(fl, x, y)), spot = [...d.entries()].filter(([k, n]) => n >= 2 && n <= 6 && !fl.things[k] && !fl.features[k]).sort((a, b) => a[1] - b[1] || (a[0] < b[0] ? -1 : 1))[0];
    if (spot) { fl.things[spot[0]] = { type: "ucback" }; this.dirty = true; }
  },
});
