"use strict";
// A home on the island (the nineteenth update, phase 6 - v12.6). A bedroll (leaves and poles, at a workbench) laid in a
// room the hero has walled and roofed - a door (two high; the right button opens and shuts it) counts as wall when
// shut - makes a camp: sleeping there at night passes it to the dawn, mends the hero as a night's rest at home does,
// and the bed becomes where they wake from a fall. A camp with a chest, a workbench and a kiln within reach of the bed
// is a homestead: the town hears of it (renown, once), and its chest can be opened from the island's gate (the right
// button on the gate's stone). Signposts are placed and named; the compass shows them. It is all a help, never a need.
CM.CAMP = { room: 400, renown: 40 };
{ const B = CM.CC.B, P = CM.Game.prototype;
  Object.assign(P, {
    // walled and roofed: the air round the bed is bounded (a shut door is wall) and none of it is under the open sky
    craftEnclosed(x, y, z) {
      const W = this.craft.world, seen = new Set([`${x},${y},${z}`]), todo = [[x, y, z]];
      while (todo.length) {
        const [a, b, c] = todo.pop(); if (!W.inside(a, b, c) || W.roof[c * CM.CC.SIZE + a] <= b) return false;
        for (const [dx, dy, dz] of [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]) {
          const n = [a + dx, b + dy, c + dz], k = n.join(","); if (seen.has(k) || CM.CC.SOLID.has(W.get(...n))) continue;
          seen.add(k); if (seen.size > CM.CAMP.room) return false; todo.push(n);
        }
      }
      return true;
    },
    craftBedOk(key) { const cr = this.craft; if (!cr || !key) return false; const [x, y, z] = key.split(",").map(Number); return cr.world.get(x, y, z) === B.BEDROLL && this.craftEnclosed(x, y, z); },
    // a night's sleep in a camp: to the dawn, mended, and the bed is where the hero wakes now
    craftSleep(key) {
      const cr = this.craft; if (!cr) return ""; const K = this.craftStore(), h = cr.hero, L = this.craftLife();
      if (!this.craftBedOk(key)) return "Not safe to sleep here: a bedroll wants a room walled all round and roofed over (a shut door counts as wall).";
      if (CM.CL.daylight(this) > 0.6) return `${h.name} is not tired: the bedroll is for the night.`;
      if (L.mobs.some((o) => !o.wild && o.fellAt === null && Math.hypot(o.w.pos[0] - cr.walker.pos[0], o.w.pos[2] - cr.walker.pos[2]) < 10)) return "Not with monsters about.";
      const [dawn] = CM.daylightOf ? CM.daylightOf(this) : [5, 21], m = CM.minuteOf(this), wake = Math.round((dawn + 1) * 60), wait = (wake - m + CM.CLOCK.day) % CM.CLOCK.day || CM.CLOCK.day;
      this.clock = (this.clock || 0) + wait; L.night = false; L.mobs = L.mobs.filter((o) => o.wild); L.shots = [];
      h.hp = h.max; h.mp = h.maxmp; if (this.cure) this.cure(h, CM.CURABLE || []);
      K.beds = K.beds || {}; K.beds[CM.craftKey(h)] = key; this.tally.islandSleeps = (this.tally.islandSleeps || 0) + 1;
      this.craftSay(`${h.name} sleeps in the camp until the dawn, and wakes mended. This is where they will wake now.`);
      this.craftHomestead(key); this.saveVillage && this.saveVillage();
      return "slept";
    },
    // a homestead: the camp, and a chest, a workbench and a kiln within reach of the bed - the town hears, once
    craftHomestead(key) {
      const cr = this.craft, K = this.craftStore(), W = cr.world, [x, y, z] = key.split(",").map(Number), R = CM.CC.REACH; let chest = null, bench = false, kiln = false;
      for (let a = x - R; a <= x + R; a++) for (let b = y - 2; b <= y + 3; b++) for (let c = z - R; c <= z + R; c++) { const v = W.get(a, b, c); if (v === B.CHEST && !chest) chest = `${a},${b},${c}`; else if (v === B.WORKBENCH) bench = true; else if (v === B.KILN) kiln = true; }
      if (!chest || !bench || !kiln || !this.craftBedOk(key)) return false;
      const first = !K.homestead; K.homestead = { bed: key, chest };
      if (first) { this.village.renown = (this.village.renown || 0) + CM.CAMP.renown; this.craftSay(`A homestead on the island! Word of it reaches Caer Duin (+${CM.CAMP.renown} renown). Its chest can be opened from the island's gate.`); this.tally.homestead = true; }
      return true;
    },
    craftHomeChest() { const K = this.craftStore(), cr = this.craft; if (!K.homestead || !cr) return null; const [x, y, z] = K.homestead.chest.split(",").map(Number); return cr.world.get(x, y, z) === B.CHEST ? K.homestead.chest : null; },
    // a door: shut, it is wall; the right button opens and shuts both its halves
    craftToggleDoor(key) {
      const W = this.craft.world, [x, y, z] = key.split(",").map(Number), v = W.get(x, y, z); if (v !== B.DOOR && v !== B.DOOR_OPEN) return false;
      const to = v === B.DOOR ? B.DOOR_OPEN : B.DOOR, p = this.craft.walker.pos;
      if (to === B.DOOR && Math.floor(p[0]) === x && Math.floor(p[2]) === z && Math.abs(Math.floor(p[1]) - y) <= 1) return false;   // (not shut on the hero)
      for (const dy of [-1, 0, 1]) { const u = W.get(x, y + dy, z); if (u === B.DOOR || u === B.DOOR_OPEN) W.set(x, y + dy, z, to); }
      return to === B.DOOR_OPEN ? "open" : "shut";
    },
    craftNameSign(key, name) { const K = this.craftStore(), s = (K.signs || []).find((q) => `${q.x},${q.y},${q.z}` === key); if (!s) return false; s.name = String(name || "").trim().slice(0, 24) || s.name; this.saveVillage && this.saveVillage(); return true; },
  });
  // the right button: a door, a bed, a signpost, the gate's stone (the homestead's chest), after the chests and stations
  const use0 = P.craftUse;
  P.craftUse = function () {
    const u = use0.call(this); if (u) return u; const cr = this.craft, hit = cr && cr.target[0]; if (!hit) return null; const b = cr.world.get(...hit), key = hit.join(",");
    if (b === B.DOOR || b === B.DOOR_OPEN) return { kind: "door", key };
    if (b === B.BEDROLL) return { kind: "bed", key };
    if (b === B.SIGN) return { kind: "sign", key };
    if ((b === B.BASALT || b === B.GATE) && this.craftHomeChest()) return { kind: "homechest", key: this.craftHomeChest() };
    return null;
  };
  // placing: a door takes two blocks of room; a signpost is written down for the compass
  const place0 = P.craftPlace;
  P.craftPlace = function () {
    const cr = this.craft, prev = cr && cr.target[1], slot = cr && cr.satchel.slots[cr.walker.slot];
    if (prev && slot && slot.b === B.DOOR && cr.world.get(prev[0], prev[1] + 1, prev[2]) !== B.AIR) { this.craftSay("A door wants two blocks of room."); return false; }
    const b = place0.call(this); if (!b) return b; const [x, y, z] = prev;
    if (b === B.DOOR) cr.world.set(x, y + 1, z, B.DOOR);
    if (b === B.SIGN) { const K = this.craftStore(); K.signs = K.signs || []; K.signs.push({ x, y, z, name: `Signpost ${K.signs.length + 1}` }); this.emit("signname", `${x},${y},${z}`); }
    return b;
  };
  // breaking: a door's other half goes with it; a signpost leaves the compass; a bed is no longer slept in
  const break0 = P.craftBreak;
  P.craftBreak = function () {
    const cr = this.craft, hit = cr && cr.target[0], was = hit ? cr.world.get(...hit) : 0, b = break0.call(this); if (!b) return b;
    const [x, y, z] = hit, K = this.craftStore();
    if (was === B.DOOR || was === B.DOOR_OPEN) for (const dy of [-1, 1]) { const u = cr.world.get(x, y + dy, z); if (u === B.DOOR || u === B.DOOR_OPEN) cr.world.set(x, y + dy, z, B.AIR); }
    if (was === B.SIGN) K.signs = (K.signs || []).filter((q) => !(q.x === x && q.y === y && q.z === z));
    if (was === B.BEDROLL && K.beds) for (const k of Object.keys(K.beds)) if (K.beds[k] === hit.join(",")) delete K.beds[k];
    return b;
  };
  // a fall that kills: from a camp's bed, the hero wakes there rather than by the gate
  const hurt0 = P.craftHurt;
  P.craftHurt = function (dmg, why) {
    const cr = this.craft, K = this.craftStore(), bed = cr && K.beds && K.beds[CM.craftKey(cr.hero)], died = hurt0.call(this, dmg, why);
    if (died && bed && this.craftBedOk(bed)) { const [x, y, z] = bed.split(",").map(Number); cr.walker.pos = [x + 0.5, y + 0.01, z + 0.5]; this.craftSay("...in the camp, on the bedroll, not by the gate."); }
    return died;
  };
}
