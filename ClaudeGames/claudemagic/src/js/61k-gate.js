"use strict";
// The Neather Gate (the eighteenth update): in the Keep-yard with the other portals, a gate of dark basalt with violet
// runes cut in it and a shimmer of violet light inside. The party steps through into Claudecraft (64n-claudecraft.js),
// for now a tech demo: walk the island, break blocks and trees, place blocks. The island and every change made to it
// are kept with the village; the same gate stands on the island, and its light is the way home.
CM.PORTAL_YARD.gate = [37, 20];                                            // the Neather Gate, on the yard's east side
CM.CRAFT_EDITS_MAX = 20000;
Object.assign(CM.Game.prototype, {
  craftStore() { this.village = this.village || {}; const K = this.village.craft = this.village.craft || {}; K.seed = K.seed || (CM.hashSeed(`${this.seed}:claudecraft`) % 2147483000) + 1; K.edits = K.edits || {}; K.visits = K.visits || 0; return K; },
  // through the gate: the island made from its seed and its edits, the party where they last stood (or by the gate)
  enterCraft() {
    if (this.mode !== "explore" || !this.floor || this.floor.number !== 0) return "The Neather Gate is in the Keep-yard.";
    const K = this.craftStore(), world = new CM.CC.World(K.seed, K.edits).generate();
    const g = world.gate, pos = K.pos && world.inside(Math.floor(K.pos[0]), 1, Math.floor(K.pos[2])) ? K.pos : [g.x + 1.5, g.y, g.z + 2.5];
    const walker = new CM.CC.Walker(world, pos, K.pos ? K.yaw : 180, K.pos ? K.pitch : -8);
    K.visits += 1; this.logAct && this.logAct("enterCraft");
    this.craft = { world, walker, target: [null, null], broken: 0, placed: 0, says: [[performance.now ? performance.now() : 0, "The gate lets you out onto a green island under a blue sky."]], since: 0 };
    this.say("The party steps into the Neather Gate's violet light, and the Keep-yard folds away.");
    this.setMode("craft"); this.emit("craft", this.craft);
    return "";
  },
  craftKeep() { const cr = this.craft; if (!cr) return; const K = this.craftStore(), w = cr.walker; K.edits = cr.world.edits; K.pos = w.pos.slice(); K.yaw = w.yaw; K.pitch = w.pitch; this.saveVillage && this.saveVillage(); },
  // a block broken (not bedrock, not the gate) or placed (not where the party stands)
  craftBreak() {
    const cr = this.craft, hit = cr && cr.target[0]; if (!hit) return false;
    const b = cr.world.get(...hit); if (CM.CC.UNBREAKABLE.has(b)) { cr.says.push([performance.now(), b === CM.CC.B.BEDROCK ? "Bedrock: nothing breaks it." : "The gate's stone will not break."]); return false; }
    if (Object.keys(cr.world.edits).length >= CM.CRAFT_EDITS_MAX) { cr.says.push([performance.now(), "The island has had enough changes for now."]); return false; }
    cr.world.set(...hit, CM.CC.B.AIR); cr.broken += 1; return b;
  },
  craftPlace() {
    const cr = this.craft, prev = cr && cr.target[1], w = cr && cr.walker; if (!prev) return false;
    const [x, y, z] = prev, p = w.pos; if (x + 1 > p[0] - 0.3 && x < p[0] + 0.3 && z + 1 > p[2] - 0.3 && z < p[2] + 0.3 && y + 1 > p[1] && y < p[1] + 1.8) return false;   // (not inside the walker)
    if (cr.world.get(x, y, z) === CM.CC.B.GATE) return false;
    cr.world.set(x, y, z, CM.CC.HOTBAR[w.slot]); cr.placed += 1; return true;
  },
  // home through the gate's light (or from the menu): the island kept, the party back in the Keep-yard
  leaveCraft() {
    const cr = this.craft; if (!cr) return null;
    this.craftKeep(); const K = this.craftStore(), g = cr.world.gate; if (cr.walker.inGate()) { K.pos = [g.x + 1.5, g.y, g.z + 2.5]; K.yaw = 180; K.pitch = -8; this.saveVillage && this.saveVillage(); }   // (out through the gate: next time, in front of it)
    this.tally.craftBroken = (this.tally.craftBroken || 0) + cr.broken; this.tally.craftPlaced = (this.tally.craftPlaced || 0) + cr.placed;
    this.say(`The party steps back out of the Neather Gate into the Keep-yard${cr.broken || cr.placed ? ` (${cr.broken} blocks broken, ${cr.placed} placed - the island keeps them)` : ""}.`);
    const out = { broken: cr.broken, placed: cr.placed };
    this.craft = null; if (typeof document !== "undefined" && document.pointerLockElement && document.exitPointerLock) document.exitPointerLock();
    this.setMode("explore"); this.floor.pos = [CM.PORTAL_YARD.gate[0] - 1, CM.PORTAL_YARD.gate[1]]; this.floor.facing = 1;
    this.saveRun(); this.emit("floor", this.floor);
    return out;
  },
});
