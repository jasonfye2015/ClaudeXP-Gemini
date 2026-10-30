"use strict";
// The town above: floor 0, hand-laid (no generator, so the generators' fixtures do not move). A square with a well,
// four lanes, nine plots - the party's house at the west end of the main lane, the shaft's mouth at the east - and
// daylight: nothing wanders it, no torch burns on it, no one is hungry on it. A plot is a thing of type "building"
// with an id; what stands on it (a foundation, or a house of some level) is the village's business (CM.VILLAGE),
// read live, so the town is the same for a seed whatever has been built and a save of it never drifts.
CM.TOWN_THEME = { name: "Caer Duin, above", floors: [0, 0], stone: [168, 150, 122], mortar: [110, 96, 78], floor: [138, 124, 100], ceiling: [150, 172, 200],
  moss: [110, 140, 70], fog: [0.004, 0.004, 0.006], torch: [1.0, 0.96, 0.9], reach: 9.0, bones: 0, town: true };
CM.TOWN_PLOTS = {
  home: { name: "Your house", village: null, what: "The party's own door. A hearth, a stash and a trophy wall, as the house is raised." },
  tavern: { name: "The Hanged Lantern", village: null, what: "The tavern: recruits, the fence, rumours and the board." },
  merchant: { name: "The Merchant's House", village: "merchant", what: "The merchant at home: the full stock, orders and insurance." },
  smith: { name: "The Smith's forge", village: null, what: "The forge: everything the camps' smith does, and the work only a forge can." },
  garden: { name: "The Alchemist's Garden", village: null, what: "Beds for ingredients between runs, and the brewing bench." },
  library: { name: "The Library", village: "library", what: "The codex, the compendium and the bestiary at a desk; tomes to borrow." },
  temple: { name: "The Temple", village: "shrine", what: "The shrine of the fallen: candles, the Patriarch's history, the priest's services." },
  guildhall: { name: "The Guildhall", village: "guildhall", what: "The trainers, the second calling, the week's contracts." },
  chronicler: { name: "The Chronicler's House", village: null, what: "The films, the statistics, the ledger and the Hall of Fame, under a roof." },
};
// where each plot's door is on the 19 x 19 town (x, y); the square is 7..11 by 7..11, the main lane y = 9, the north and south lanes x = 9
CM.TOWN_AT = { home: [1, 9], shaft: [17, 9], well: [9, 8], tavern: [4, 8], merchant: [4, 10], smith: [14, 8], garden: [14, 10], library: [8, 4], temple: [10, 4], guildhall: [8, 14], chronicler: [10, 14] };
CM.TOWN_SIZE = 19;
CM.makeTown = function (seed) {
  const size = CM.TOWN_SIZE, grid = [];
  for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const open = (x, y) => { grid[y][x] = 0; };
  for (let x = 1; x <= 17; x++) open(x, 9);                              // the main lane, door to shaft
  for (let y = 7; y <= 11; y++) for (let x = 7; x <= 11; x++) open(x, y);   // the square
  for (let y = 3; y <= 7; y++) open(9, y);                                // the north lane
  for (let y = 11; y <= 15; y++) open(9, y);                              // the south lane
  const things = {}, features = {};
  for (const [id, [x, y]] of Object.entries(CM.TOWN_AT)) {
    open(x, y);
    if (id === "shaft") things[`${x},${y}`] = { type: "ladder" };
    else if (id === "well") things[`${x},${y}`] = { type: "well" };
    else things[`${x},${y}`] = { type: "building", id };
  }
  const seen = []; for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) seen.push([x, y]);   // (daylight: the whole town is on the map)
  return { number: 0, grid, pos: CM.TOWN_AT.home.slice(), facing: 1, things, features, dark: [], seen, rooms: [{ x0: 7, y0: 7, x1: 11, y1: 11, name: "The Square" }], decor: [], special: "town" };
};
// a plot's level: the village's, for the plots the village already raises; none yet for the rest (the next phases raise them)
CM.plotLevel = (game, id) => { const P = CM.TOWN_PLOTS[id]; return P && P.village && game ? game.villageLevel(P.village) : 0; };
CM.isTown = (fl) => Boolean(fl && fl.number === 0);
