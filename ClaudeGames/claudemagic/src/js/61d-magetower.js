"use strict";
// The Mage Tower (the twelfth update): its portal yard in the town, the tower itself in the Wood, and who may go in.
// Phase 0 (v10.1): the portal yard in the Keep-yard beside the shaft - one lit portal, to the tower's front, and two
// dark plinths for the challenges to come - and the tower in a clearing north of the fields: a great octagon of black
// and grey stone many stories tall, two dark-brown doors on its front, dark shrubs and fog about its foot, and a portal
// back to the town by its door. The tower and its clearing are laid on the land last (nothing the seed placed moves).
CM.MAGE_TOWER = { at: [47, 12], r: 1.45, h: 10.5, stories: 7, roof: 3.6, clearing: [43, 9, 51, 16] };   // its middle cell, its size in squares
CM.MAGE_DOOR = [47, 14];                                                   // the square before its doors (the party stands here)
CM.MAGE_PORTAL_LAND = [45, 15];                                            // the portal home, by the door
CM.MAGE_PATH = [47, 16, 47, 19];                                           // the path down to the fields
CM.PORTAL_YARD = { tower: [33, 18], plinths: [[33, 22], [37, 22]] };       // in the Keep-yard: the lit portal and the dark plinths
CM.TOWER_CASTERS = ["Mage", "Necromancer", "Druid", "Cleric", "Bard", "Artificer"];
CM.isMageTowerCell = (x, y) => Math.abs(x - CM.MAGE_TOWER.at[0]) <= 1 && Math.abs(y - CM.MAGE_TOWER.at[1]) <= 1;
// who may go into the tower: a caster, or anyone with a bow or a crossbow in hand; "" if they may, else why not
CM.towerWhyNot = (h) => {
  if (!h) return "No one.";
  if (h.hp <= 0) return `${h.name} has fallen.`;
  if (CM.TOWER_CASTERS.includes(h.cls)) return "";
  const w = h.weapon, bow = w && w.props && w.props.bow;
  if (bow) return "";
  return `${h.name} the ${h.cls} has nothing that reaches across a room: the tower is for casters, and for a bow or a crossbow.`;
};

// the tower's clearing, laid on the land after everything else: the tower's nine squares, the ground round it, the door,
// the portal home, the path to the fields, the dark shrubs
CM.layMageTower = function (fl) {
  const T = CM.MAGE_TOWER, [x0, y0, x1, y1] = T.clearing, key = (x, y) => `${x},${y}`;
  const open = (x, y, g) => { fl.grid[y][x] = 0; if (fl.kinds) delete fl.kinds[key(x, y)]; (fl.ground = fl.ground || {})[key(x, y)] = g; };
  const cx = T.at[0], cy = T.at[1];
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
    const d = ((x - cx) / 4.6) ** 2 + ((y - cy - 0.5) / 4.2) ** 2;
    if (d <= 1 && !CM.isMageTowerCell(x, y)) open(x, y, (x + y) % 3 ? "moss" : "dirt");
  }
  for (let y = cy - 1; y <= cy + 1; y++) for (let x = cx - 1; x <= cx + 1; x++) { fl.grid[y][x] = 1; (fl.kinds = fl.kinds || {})[key(x, y)] = "magetower"; if (fl.ground) delete fl.ground[key(x, y)]; }
  const [px, py0, , py1] = CM.MAGE_PATH; for (let y = py0; y <= py1; y++) open(px, y, "dirt");
  fl.things[key(...CM.MAGE_DOOR)] = { type: "magedoor" };
  fl.things[key(...CM.MAGE_PORTAL_LAND)] = { type: "portal", to: "town" };
  fl.decor = (fl.decor || []).filter((d) => !(d.x >= x0 && d.x <= x1 && d.y >= y0 && d.y <= y1));
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {               // dark shrubs crowding the clearing's edge
    if (fl.grid[y][x] !== 0 || fl.things[key(x, y)] || CM.isMageTowerCell(x, y)) continue;
    const edge = CM.DIRS.some(([dx, dy]) => fl.grid[y + dy] && fl.grid[y + dy][x + dx] === 1 && !CM.isMageTowerCell(x + dx, y + dy));
    if (edge && x !== px && CM.hashSeed(`magetower:shrub:${x},${y}`) % 3 !== 0) fl.decor.push({ kind: "darkshrub", x, y });
  }
  fl.rooms = (fl.rooms || []).concat({ x0, y0, x1, y1, name: "the Mage Tower" });
  for (let y = y0; y <= y1 + 3; y++) for (let x = x0; x <= x1; x++) if (!(fl.seen || []).some(([sx, sy]) => sx === x && sy === y)) (fl.seen = fl.seen || []).push([x, y]);   // (in sight from the fields)
  return fl;
};
// the portal yard, laid in the town's Keep-yard
CM.layPortalYard = function (fl) {
  const P = CM.PORTAL_YARD, key = (x, y) => `${x},${y}`;
  if (!fl.things[key(...P.tower)]) fl.things[key(...P.tower)] = { type: "portal", to: "magetower" };
  if (P.gate && (!fl.things[key(...P.gate)] || fl.things[key(...P.gate)].to !== "claudecraft")) fl.things[key(...P.gate)] = { type: "portal", to: "claudecraft" };   // (the Neather Gate: 61k-gate.js)
  if (P.ablo && (!fl.things[key(...P.ablo)] || fl.things[key(...P.ablo)].to !== "claudeablo")) fl.things[key(...P.ablo)] = { type: "portal", to: "claudeablo" };   // (the red portal: 61i-redportal.js)
  if (P.fortress && (!fl.things[key(...P.fortress)] || fl.things[key(...P.fortress)].type !== "portal")) fl.things[key(...P.fortress)] = { type: "portal", to: "fortress" };   // (the Fortress: 61h-fortress.js)
  for (const p of P.plinths) { const was = fl.things[key(...p)], lit = P.cabin && p === P.cabin ? "cabin" : P.claudeita && p === P.claudeita ? "claudeita" : null; if (!was || (lit && was.type === "plinth")) fl.things[key(...p)] = lit ? { type: "portal", to: lit } : { type: "plinth" }; }   // (the plinths lit: Leshy's cabin, Claudeita's cave)   // (the first plinth lit: to Leshy's cabin)
  return fl;
};

Object.assign(CM.Game.prototype, {
  // a portal: the town's to the tower's front, the tower's back to the Keep-yard
  usePortal(t) {
    this.sound("spell");
    if (t.to === "magetower") { this.enterFloor(-1, "rope", CM.MAGE_DOOR.slice()); this.floor.facing = 0; this.say("The portal takes you in a breath of cold light: the Deep Wood, a clearing in fog, and over you the Mage Tower, black against the sky."); return true; }
    if (t.to === "cabin") { this.enterFloor(-1, "rope", CM.CABIN.front.slice()); this.floor.facing = 0; this.say("The portal sets you down in a clearing among the pines. A log cabin, smoke from its chimney, a light in its window."); return true; }
    if (t.to === "claudecraft") { const why = this.enterCraft(); if (why) this.say(why); return true; }   // (the whole party steps through)
    if (t.to === "claudeablo") { this.emit("claudeablo"); return true; }   // (who steps through: the window asks)
    if (t.to === "fortress") { this.enterFloor(-1, "rope", CM.FORTRESS.front.slice()); this.floor.facing = 0; this.say("The portal sets you down in a clearing of trampled earth. Over you the Fortress: black stone, four towers, and two great doors of dark wood."); return true; }
    if (t.to === "claudeita") { this.enterFloor(-1, "rope", CM.CLAUDEITA.front.slice()); this.floor.facing = 2; this.say("The portal leaves you among the trees south of the fields, before a crag of grey rock with a dark mouth in it. Warm air breathes out of the dark."); return true; }
    if (t.to === "town") { const near = (q) => this.floor && this.floor.number === -1 && Math.abs(this.floor.pos[0] - q[0]) + Math.abs(this.floor.pos[1] - q[1]) <= 1; this.enterFloor(0, "rope", (near(CM.CABIN.portal) ? CM.PORTAL_YARD.cabin : CM.CLAUDEITA && near(CM.CLAUDEITA.portal) ? CM.PORTAL_YARD.claudeita : CM.FORTRESS && near(CM.FORTRESS.portal) ? CM.PORTAL_YARD.fortress : CM.PORTAL_YARD.tower).slice()); this.say("Light, and the Keep-yard: the portal yard by the shaft."); return true; }
    return false;
  },
  // the tower's doors: the choice of who goes in (the dialog is the window's); the rules say who may
  towerChoices() { return this.party.map((h, i) => ({ i, name: h.name, cls: h.cls, why: CM.towerWhyNot(h) })); },
});
