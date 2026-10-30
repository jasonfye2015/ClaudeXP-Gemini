"use strict";
// The fight: turn by turn in order of speed, the heroes' blows, spells and skills, the monsters' ways, the Lich King
// and the guardians, ailments, and what a won fight brings.
{
const keyOf = CM.keyOf;
Object.assign(CM.Game.prototype, {
  // ---- fighting: turn by turn, in order of speed ----
  // this.combat: { round, order [{hero | foe, init}], index, waiting (the hero whose turn it is), surprise (the party's
  // free round), taunter / tauntUntil, bless, protect, reached (foes that have come at the party this round) }
  startCombat(key, thing, theyCame = false) {
    // the fight's dice come from the seed and where and when it begins: the same fight, fought the same way, goes the same way
    this.rnd = new CM.Random(CM.hashSeed(`${this.seed}:fight:${this.floor ? this.floor.number : 0}:${(this.tally || {}).fights || 0}:${this.steps || 0}:${key}`));
    this.foes = thing.group.map(CM.upgradeMonster);
    if (thing.terms && !thing.termsDone) {                               // spoken to first: on better terms its company goes and it is shaken; on worse it is enraged
      thing.termsDone = true;
      if (thing.terms === "good") { this.foes = this.foes.filter((m) => m.guardian || m.boss || this.foes.length === 1); for (const m of this.foes) if (m.guardian) { m.hp = Math.max(1, Math.round(m.hp * 0.85)); m.shaken = true; } }
      else if (thing.terms === "bad") for (const m of this.foes) if (m.guardian) { m.atk = Math.round(m.atk * 1.15); m.enraged = true; }
      thing.group = this.foes;
    }
    if (this.has("hordes") && !thing.horded && this.foes.length && !this.foes[0].boss && !this.foes[0].guardian) {   // one more, of the first kind
      thing.horded = true;
      const kind = CM.monsterKind(this.foes[0].kind || this.foes[0].name);
      if (kind) this.foes.push(CM.makeMonster(kind, CM.monsterLevel(this.floor ? this.floor.number : 1), this.rnd));
    }
    if (this.asc("leaders") && this.floor && this.floor.number >= 3 && !thing.ascended && this.foes.length && !this.foes.some((m) => m.elite || m.boss || m.guardian)) { thing.ascended = true; CM.makeElite(this.foes, this.rnd, this.gen); }   // (Leaders)
    for (const m of this.foes) this.tune(m);
    if (this.villageLevel("library") >= 4) for (const m of this.foes) for (const el of Object.keys(CM.ELEMENT_NAMES)) this.learnResist(m, el, CM.resistance(m, el));   // (the library knows)
    thing.group = this.foes;
    this.fightFell = false;
    this.foeKey = key;
    delete thing.anim;
    if (!(this.song && this.songEpic === this.floor.number)) this.song = 0;   // the Bard's song lasts the fight (an Epic one, the floor)
    for (const h of this.party) { h.cried = false; h.winded = false; h.defending = false; h.guardedBy = null; h.guarding = null; h.used = {}; h.struck = false; h.undied = false; h.avenged = false;
      if (CM.trait(h, "manawell") && h.hp > 0) h.mp = Math.min(h.maxmp, h.mp + Math.ceil(h.maxmp / 3)); }
    for (const m of this.foes) { m.held = 0; m.asleep = 0; m.blind = 0; m.marked = false; m.charged = false; m.fled = false; m.dead = m.hp <= 0; m.chilled = 0; m.warded = 0; m.intent = null; if (!m.row) m.row = (CM.monsterKind(m.kind || m.name) || {}).row || "front"; this.noteFoe(m, "seen"); }
    this.target = 0;
    this.combat = { foes: this.foes, round: 0, order: [], index: 0, waiting: null, surprise: false, taunter: null, tauntUntil: 0, bless: Boolean(this.blessedNext), protect: false, reached: 0 };
    if (this.blessedNext) { this.blessedNext = false; this.say("The saint's blessing is on the party for this fight."); }
    if (this.floor && this.floor.tide) for (const m of this.foes) m.speed = (m.speed || 10) + 3;   // (high tide: the Drowned are quick)
    this.foes.forEach((m, i) => { if (m.ability === "breath") m.breath = i % 2; });   // (a pack of demons breathes in halves, not all at once)
    this.setMode("combat");
    this.count("fights");
    this.sound(CM.roarFor((this.foes[0] || {}).kind || (this.foes[0] || {}).name));
    const names = {};
    for (const m of this.foes) names[m.name] = (names[m.name] || 0) + 1;
    const who = Object.entries(names).map(([k, n]) => CM.plural(n, k)).join(", ");
    const guardian = this.foes.find((m) => m.guardian);
    if (guardian || this.foes.some((m) => m.boss)) this.emit("fx", { kind: "intro", foe: guardian || this.foes.find((m) => m.boss) });   // (a title card, a push of the camera)
    else if (this.foes.some((m) => m.elite)) this.sound("elite");          // (a leader among them: a stinger)
    if (this.foes.some((m) => m.boss)) this.say(`The Lich King rises from his throne. "You took your time," he says.${this.phylactery ? "" : " Somewhere, his heart beats."}`);
    else if (guardian) this.say(CM.GUARDIANS[guardian.guardian].intro + (guardian.echo ? " It is not the thing itself: it is what the dark remembers of it, and the dark remembers it stronger." : "")
      + (guardian.hp < guardian.max ? " The wounds you left are still there." : ""));
    else this.say(theyCame ? `${who} come at you out of the dark!` : `Monsters! ${who} attack!`);
    const sneaky = this.alive().some((h) => ["Rogue", "Ranger"].includes(h.cls) && this.canAct(h));
    const wary = this.alive().some((h) => CM.trait(h, "slippery") || h.quirk === "quiet" || (h.boots && h.boots.props && h.boots.props.silence && !h.boots.unknown) || (this.inDark() && h.cloak && h.cloak.props && h.cloak.props.hood && !h.cloak.unknown));
    if ((theyCame || this.inDark()) && !wary && this.rnd.chance(0.5)) {   // surprise: they're on you before you can draw... (not past silent boots, a hood, a quiet one)
      this.say("They're on you before you can draw!");
      for (const m of this.living()) this.monsterAct(m);
      this.afterBlows();
      if (this.mode !== "combat") return;
    } else if (!theyCame && !this.asc("watchful") && (this.rnd.chance(sneaky ? 0.35 : 0.2) || this.alive().some((h) => CM.trait(h, "foresight")))) {     // ...or you have the drop on them (never, past the tenth rung)
      this.say("You have the drop on them: a free round!");
      this.combat.surprise = true;
    }
    if (this.asc("kingsguard") && this.foes.some((m) => m.boss)) this.summonSkeletons(2);   // (the king's guard)
    this.beginRound();
  },

  // a fight begun some other way (the tests set the mode by hand) still gets its turns
  ensureCombat() {
    if (this.combat && this.combat.order && this.combat.foes === this.foes) return;
    for (const h of this.party) { h.cried = false; h.winded = false; h.defending = false; h.guardedBy = null; h.guarding = null; h.used = h.used || {}; }
    for (const m of this.foes) { CM.upgradeMonster(m); m.held = m.held || 0; m.asleep = m.asleep || 0; m.blind = m.blind || 0; }
    this.target = 0;
    this.combat = { foes: this.foes, round: 0, order: [], index: 0, waiting: null, surprise: false, taunter: null, tauntUntil: 0, bless: false, protect: false, reached: 0 };
    this.beginRound();
  },

  alive() { return this.party.filter((m) => m.hp > 0); },
  living() { return this.foes.filter((m) => m.hp > 0 && !m.fled); },
  attackable() { return this.living().filter((m) => !m.hidden); },        // (a king hidden in its swarm can't be struck)
  // the ground the fight stands on (CM.TERRAIN ids): water, a vent, pillars, the dark
  terrain() {
    const fl = this.floor, c = this.combat || {}, out = [];
    if (!fl) return out;
    const k = CM.keyOf(fl.pos[0], fl.pos[1]), f = fl.features[k];
    if (fl.tide || fl.special === "wading" || c.flooded || (fl.decor || []).some((d) => d.kind === "water" && d.x === fl.pos[0] && d.y === fl.pos[1])) out.push("water");
    if (f && f.type === "vents") out.push("vent");
    if ((fl.rooms || []).some((r) => r.name && CM.PILLARED.includes(r.name) && fl.pos[0] >= r.x0 && fl.pos[0] <= r.x1 && fl.pos[1] >= r.y0 && fl.pos[1] <= r.y1)) out.push("pillars");
    if (this.inDark() && !(this.spellLight > 0)) out.push("dark");
    return out;
  },
  terrainNote() { return this.terrain().map((id) => `${CM.TERRAIN[id].name}: ${CM.TERRAIN[id].what}`).join(". "); },
  setFormation(id) {
    if (!CM.FORMATIONS[id] || this.mode === "combat") return false;
    this.logAct("setFormation", id);
    this.formation = id; this.dirty = true;
    this.say(`The party takes up a ${CM.FORMATIONS[id].name.toLowerCase()}: ${CM.FORMATIONS[id].what}.`);
    this.emit("change");
    return true;
  },
  point() { return this.formation === "wedge" ? this.alive().find((h) => h.row === "front" && !(h.status || {}).stone) || null : null; },
  canAct(h) { const s = h.status || {}; return h.hp > 0 && !s.paralysis && !s.sleep && !s.stone; },   // standing, and not held by an ailment
  targets() { return this.alive().filter((h) => !(h.status || {}).stone); },                           // what a monster can reach: stone isn't worth hitting

  // the party's square: in a corridor, only two foes can come at them at once
  reachLimit() {
    const fl = this.floor;
    return (fl && CM.openNeighbours(fl, fl.pos[0], fl.pos[1]).length <= 2) || this.terrain().includes("pillars") ? 2 : 99;
  },

  // a round: everyone standing, in order of speed (the dice have a say); heroes win ties
  beginRound() {
    const c = this.combat;
    c.round += 1;
    c.reached = 0;
    const order = [];
    for (const h of this.party) if (h.hp > 0) order.push({ hero: h, init: this.stat(h, "dex") + (["Rogue", "Ranger", "Monk"].includes(h.cls) ? 2 : 0) + (c.oiled ? 3 : 0) + (h.boots && !h.boots.unknown ? h.boots.power : 0) + this.rnd.int(1, 6) + 0.5 });
    if (!c.surprise) for (const m of this.living()) order.push({ foe: m, init: (m.speed || 10) + this.rnd.int(1, 6) });
    order.sort((a, b) => b.init - a.init);
    for (const h of this.alive()) if (h.familiar === "skull" && c.round > 0) { const foe = this.attackable()[0]; if (foe) this.spellHit(foe, Math.max(1, 2 + Math.floor(h.level / 2)), `${h.name}'s skull bites:`); }
    c.order = order;
    c.index = 0;
    c.waiting = null;
    this.emit("round", c.round);
    this.advance();
  },

  // on through the order until a hero needs telling what to do, or the round is over
  advance() {
    const c = this.combat;
    while (this.mode === "combat" && c) {
      if (c.index >= c.order.length) {
        this.endRound();
        if (this.mode === "combat") this.beginRound();
        return;
      }
      const slot = c.order[c.index++];
      if (slot.hero) {
        const h = slot.hero;
        if (h.hp <= 0) continue;
        h.defending = false;                                               // (a guard raised lasts until now)
        if (h.guarding) { h.guarding.guardedBy = null; h.guarding = null; }
        const st = h.status || {};
        if (!this.canAct(h)) { if (!st.stone) this.say(`${h.name} is ${st.sleep ? "asleep" : "paralysed"} and can't act.`); continue; }
        if (!this.living().length) continue;
        const m = this.morale === undefined ? CM.MORALE.start : this.morale;
        if (m <= 30 && this.rnd.chance(m <= 10 ? 0.3 : 0.15)) { this.say(`${h.name} freezes: the party is ${this.moraleWord().toLowerCase()}.`); continue; }
        c.waiting = h;
        this.emit("turn", h);
        this.emit("change");
        return;
      }
      const m = slot.foe;
      if (m.hp <= 0 || m.fled) continue;
      this.monsterAct(m);
      this.afterBlows();
    }
  },

  // the round's end: poison bites, ailments run their course, trolls knit
  endRound() {
    const c = this.combat;
    for (const h of this.alive()) {
      const st = h.status || {};
      if (st.poison) {
        const bite = Math.max(1, Math.floor(h.max * ((h.boons || []).includes("thickblood") ? 0.025 : 0.05) * (this.asc("deeperhurts") ? 2 : 1)));
        h.hp = Math.max(1, h.hp - bite);
        this.say(`${h.name} suffers from the poison (-${bite}).`);
      }
      for (const s of Object.keys(st)) {
        if (st[s] >= 900) continue;
        st[s]--;
        if (st[s] <= 0) { delete st[s]; this.say(`${h.name} is no longer ${CM.STATUSES[s].name.toLowerCase()}.`); }
      }
    }
    for (const m of this.living()) {
      if (m.ability === "regen" && m.hp < m.max) {
        const back = Math.max(1, Math.floor(m.max * 0.05));
        m.hp = Math.min(m.max, m.hp + back);
        this.say(`The ${m.name}'s wounds knit (+${back}).`);
      }
      if (CM.guardianHas(m, "regrow") && m.hp < m.max) {                 // (the Mind's flesh, the Root's sap)
        const back = Math.max(1, Math.floor(m.max * 0.05));
        m.hp = Math.min(m.max, m.hp + back);
        this.say(`${CM.The(m)} regrows (+${back}).`);
      }
      if (m.burning > 0) {                                               // (an Inferno's fire)
        m.burning -= 1;
        this.spellHit(m, m.burnDmg || 5, `${CM.The(m)} burns:`, "fire");
      }
      if (m.chilled > 0) m.chilled -= 1;
      if (m.warded > 0) m.warded -= 1;
      if (m.marked && m.hp > 0 && this.alive().some((h) => CM.trait(h, "bleed"))) this.spellHit(m, 3, `${CM.The(m)} bleeds:`);
    }
    for (const h of this.alive()) if (CM.trait(h, "wellspring") && h.mp < h.maxmp) h.mp = Math.min(h.maxmp, h.mp + 2);
    this.enginesAct();
    if (this.terrain().includes("vent")) { const burn = 2 + Math.floor(this.floor.number / 5); let any = false; for (const h of this.alive().filter((p) => p.row === "back")) { h.hp = Math.max(1, h.hp - burn); any = true; } if (any) this.say(`The vent breathes: the back row is scorched (-${burn}).`); }
    for (const m of this.living()) if (m.elite === "shielded") m.warded = Math.max(m.warded || 0, 1);
    for (const h of this.alive()) {                                      // gear that mends (of Mending, a unique, three relics worn)
      const mend = CM.gearProp(h, "regen") + (CM.relicsWorn(h) >= 3 ? CM.RELIC_SET.three.regen : 0);
      if (mend > 0 && h.hp < h.max) h.hp = Math.min(h.max, h.hp + mend);
    }
    if (this.alive().some((h) => CM.trait(h, "evergreen"))) for (const h of this.alive()) h.hp = Math.min(h.max, h.hp + 3);
    c.surprise = false;
    this.afterBlows();
    this.emit("change");
  },

  // after blows are struck: the fallen, the Lich King's rising, victory or the end
  afterBlows() {
    for (const m of this.foes) if (m.hp <= 0 && !m.dead && !m.fled) { m.dead = true; this.emit("fx", { kind: "die", foe: m }); }
    for (const h of this.party) h.hp = Math.max(0, h.hp);
    if (this.mode !== "combat") return;
    const lich = this.foes.find((m) => m.boss);
    if (lich && lich.hp <= 0 && !this.phylactery) {
      lich.hp = Math.floor(lich.max * CM.LICH.riseTo);
      lich.dead = false;
      lich.risen = (lich.risen || 0) + 1;
      this.sound("lich");
      this.say("The Lich King crumbles... and the bones knit again. Somewhere, his heart still beats.");
      this.summonSkeletons(2);
      this.emit("fx", { kind: "rise", foe: lich });
    }
    for (const m of this.foes) {                                         // a second form, at a third of its strength (the shallow guardians)
      const G = m.guardian ? CM.GUARDIANS[m.guardian] : null;
      if (!G || !G.form2 || m.form2 || m.hp <= 0 || m.hp > m.max * (this.asc("nomercy") ? 1.01 : 0.34) || m.echo) continue;
      m.form2 = true;
      this.say(G.form2.text);
      this.emit("fx", { kind: "rise", foe: m, form2: true });
      if (G.form2.kind === "hide") { m.hidden = true; this.summonFor(m, G.moves[0], 2); }
      else if (G.form2.kind === "flood") { this.combat.flooded = true; m.quick = true; }
      else if (G.form2.kind === "heat") { m.broken = true; m.atk = Math.round(m.atk * 1.3); }
    }
    const hidden = this.foes.find((m) => m.hidden && m.hp > 0);
    if (hidden && !this.living().some((m) => m !== hidden && !m.hidden)) { hidden.hidden = false; this.say(CM.GUARDIANS[hidden.guardian].form2.found); }
    for (const m of this.foes) {
      if (!CM.guardianHas(m, "rise") || m.hp > 0 || m.risen) continue;
      m.hp = Math.floor(m.max / 3); m.dead = false; m.risen = 1;
      this.sound("lich");
      this.say(CM.GUARDIANS[m.guardian].riseText || `${CM.The(m)} rises again.`);
      this.emit("fx", { kind: "rise", foe: m });
    }
    if (!this.living().length) { this.wonFight(); return; }
    if (!this.alive().length || this.alive().every((h) => (h.status || {}).stone)) {
      this.say(this.alive().length ? "The last of the party stands as stone, and the dark closes in..." : "The last of the party falls...");
      this.endRun(false);
    }
  },

  // the hero whose turn it is does something: fight (the chosen foe), cast {id, target}, item {row, who}, defend, run
  act(action, arg) {
    const c = this.combat, h = c && c.waiting;
    if (!h || this.mode !== "combat") return false;
    if (!this.inAuto) this.logAct("act", action, arg && typeof arg === "object" ? (arg.hp !== undefined ? { foe: this.living().indexOf(arg) } : arg) : arg === undefined ? null : arg);
    if (arg && typeof arg === "object" && arg.foe !== undefined && arg.hp === undefined) arg = this.living()[arg.foe] || null;   // (a foe, by its place among the living: how the log keeps it)
    if (action === "fight") {
      const t = this.foeAt(arg);
      if (!t) return false;
      this.strike(h, t);
      if (CM.trait(h, "flurry") && t.hp > 0 && !t.fled) this.strike(h, t, " again", { mult: 0.5 });
    } else if (action === "cast") {
      const id = arg && arg.id !== undefined ? arg.id : this.defaultAbility(h);
      if (!this.useAbility(h, id, arg && arg.target !== undefined ? arg.target : null, arg && arg.power, arg && arg.reagent)) return false;
    } else if (action === "item") {
      if (!this.useItemInBattle(h, arg)) return false;
    } else if (action === "defend") {
      h.defending = true;
      this.say(`${h.name} raises a guard.`);
    } else if (action === "run") {
      if (this.flee(false)) return true;
      this.say("You can't get away!");
    } else {
      return false;
    }
    if (this.mode !== "combat" || !this.combat) return true;
    c.waiting = null;
    this.afterBlows();
    if (this.mode === "combat") this.advance();
    return true;
  },

  // the chosen foe: an index among the living, a foe itself, or the one picked already (Tab, or a click)
  foeAt(arg) {
    const foes = this.attackable();
    if (!foes.length) return null;
    if (arg && typeof arg === "object") return foes.includes(arg) ? arg : foes[0];
    const i = typeof arg === "number" ? arg : (this.target || 0);
    return foes[Math.min(Math.max(0, i), foes.length - 1)];
  },

  setTarget(i) {
    const n = this.attackable().length;
    if (!n) return;
    this.target = ((i % n) + n) % n;
    this.emit("change");
  },

  // one of the party to cast on: an index, the hero itself, or the one who needs it most
  allyAt(target, fallen) {
    const pool = this.party.filter((p) => (fallen ? p.hp <= 0 : p.hp > 0));
    if (!pool.length) return null;
    if (target && typeof target === "object") return pool.includes(target) ? target : null;
    if (typeof target === "number") return pool.includes(this.party[target]) ? this.party[target] : null;
    return fallen ? pool[0] : pool.reduce((a, b) => (a.hp / a.max <= b.hp / b.max ? a : b));
  },

  // every hero does the one thing, with the foe and friend that need it most: the old game's round, kept for the tests
  combatRound(action) {
    if (this.mode !== "combat") return;
    this.ensureCombat();
    const round = this.combat.round;
    let guard = 0;
    while (this.mode === "combat" && this.combat && this.combat.round === round && this.combat.waiting && guard++ < 20) {
      const ok = action === "potion" ? this.act("item", null) : this.act(action, null);
      if (!ok && this.mode === "combat" && this.combat && this.combat.waiting) this.act("defend");
    }
  },

  // running: more than half the time (a Rogue helps), and never from the Lich King; the party steps back a square
  flee(sure) {
    if (this.foes.some((m) => m.boss && m.hp > 0) && !sure) { this.say("There's no running from the Lich King."); return false; }
    if (!sure && !this.alive().some((h) => CM.trait(h, "slippery")) && !this.rnd.chance(0.55 + (this.alive().some((h) => h.cls === "Rogue") ? 0.1 : 0))) return false;
    const fl = this.floor;
    for (let i = 0; i < (sure ? 2 : 1); i++) {                          // back the way you came, while the way is clear
      const [dx, dy] = CM.DIRS[(fl.facing + 2) % 4], nx = fl.pos[0] + dx, ny = fl.pos[1] + dy, k = keyOf(nx, ny);
      const f = fl.features[k];
      if (!CM.passable(fl, nx, ny) || fl.things[k] || (f && ["pit", "trapdoor", "teleporter", "spinner"].includes(f.type))) break;
      fl.pos = [nx, ny];
      this.emit("moved", nx, ny);
    }
    const guardian = this.foes.find((m) => m.guardian && m.hp > 0);
    if (guardian) {                                                      // it keeps its lair: it mends a little, and the swarm goes back into the walls
      guardian.hp = Math.min(guardian.max, guardian.hp + Math.floor(guardian.max / 4));
      const lairThing = this.floor.things[this.foeKey];
      if (lairThing) lairThing.group = this.foes.filter((m) => !m.summoned);
      this.say(`Behind you, ${CM.the(guardian)} settles back over the shaft to lick its wounds.`);
    }
    this.say(sure ? "The world folds, and the party is elsewhere." : "The party flees back the way it came!");
    this.count("fled");
    if (!sure) this.cheer(-10, "a flight");
    this.combat = null;
    this.setMode("explore");
    this.look();
    this.saveRun();
    return true;
  },

  damage(atk, power, df) {
    return Math.max(1, atk + power + this.rnd.int(0, Math.max(1, Math.floor((atk + power) / 2))) - Math.floor(df / 2));
  },

  // a hero's numbers as they stand right now: a curse takes from them, the song and a blessing give
  effective(h) {
    const cursed = (h.status || {}).curse ? 2 : 0, bless = this.combat && this.combat.bless, point = this.point() === h ? 2 : 0;
    return { atk: Math.max(1, h.atk - cursed + (this.song === 2 ? 4 : this.song ? 2 : 0) + (bless ? 2 : 0)), df: Math.max(0, h.df - cursed + (bless ? 1 : 0) + point) };
  },
  stat(h, s) { return CM.heroStat(h, s); },
  hitChance(h) {
    return CM.clamp(0.8 + (this.stat(h, "dex") - 10) * 0.01 + ((h.boons || []).includes("keeneye") ? 0.1 : 0) - ((h.status || {}).blind ? 0.4 : 0) + ((this.morale === undefined ? CM.MORALE.start : this.morale) >= 80 ? 0.05 : 0), 0.25, 0.97);
  },
  critChance(h) { return CM.clamp((h.cls === "Rogue" ? 0.25 : 0.05) + (this.stat(h, "luck") - 10) * 0.01 + CM.gearProp(h, "crit"), 0.02, 0.7); },
  resistChance(h) {
    return CM.clamp((this.stat(h, "luck") - 10) * 0.02 + (this.stat(h, "wis") - 10) * 0.01 + ((h.boons || []).includes("thickblood") ? 0.2 : 0), 0, 0.6);
  },
  spellMod(h) { return this.stat(h, (CM.CLASSES[h.cls] || CM.CLASSES.Knight).key) - 10; },

  // an ailment settles on a hero, unless they shrug it off; it lasts this many rounds (curses and stone, until lifted)
  afflict(h, status, by) {
    if (!CM.STATUSES[status] || (h.status || {})[status]) return false;
    if (h.thrall) return false;
    if ((status === "paralysis" && (CM.trait(h, "immovable") || h.quirk === "stubborn")) || ((status === "poison" || status === "paralysis") && CM.trait(h, "diamondbody"))) { this.say(`${h.name} does not so much as flinch.`); return false; }
    if (status === "curse") this.cheer(-5, "a curse");
    const charm = CM.equipped(h).find((it) => it.props && it.props.resist === status && !it.unknown);
    if (charm) { this.say(`${h.name}'s ${CM.baseName(charm)} grows warm: the ${status === "stone" ? "gaze" : "touch"} finds no purchase.`); return false; }
    if (this.rnd.chance(this.resistChance(h))) { this.say(`${h.name} shrugs off ${CM.the(by)}'s ${status === "stone" ? "gaze" : "touch"}.`); return false; }
    h.status = h.status || {};
    let turns = { poison: 8, paralysis: 2, sleep: 3, blind: 4, curse: 999, stone: 999 }[status];
    if (status === "poison" && by === CM.GUARDIANS.rat.name) turns = 12;
    if (turns < 900 && (h.boons || []).includes("thickblood")) turns = Math.ceil(turns / 2);
    h.status[status] = turns;
    this.sound("ailment");
    this.say(`${h.name} is ${CM.STATUSES[status].name.toLowerCase()}!`);
    this.emit("fx", { kind: "ailment", hero: h, status });
    return true;
  },

  cure(h, which) {                                                       // which: a list of ailments, or "all"
    const cured = [];
    for (const s of Object.keys(h.status || {})) if (which === "all" || which.includes(s)) { delete h.status[s]; cured.push(s); }
    return cured;
  },

  // who a monster goes for: the Knight's taunt, else the front row (the Knight most of all) - unless it shoots
  pickTarget(m) {
    const pool = this.targets(), c = this.combat || {};
    if (!pool.length) return null;
    if (c.taunter && pool.includes(c.taunter) && c.round <= c.tauntUntil) return c.taunter;
    if (c.thrall && c.thrall.hp > 0 && (!m || m.ability !== "ranged") && this.rnd.chance(0.75)) return c.thrall;   // (the thrall takes the blows meant for the party)
    const point = this.point();
    if (point && (!m || m.ability !== "ranged") && pool.includes(point)) return point;                       // (the wedge: the point takes every blow that isn't a shot)
    const shadows = pool.filter((h) => !(CM.trait(h, "shadowstep") && h.row === "back"));
    if (shadows.length) pool.splice(0, pool.length, ...shadows);
    if (m && m.ability === "ranged") return this.rnd.pick(pool);
    const front = pool.some((h) => h.row === "front");
    const weights = pool.map((h) => (front ? (h.row === "front" ? (h.cls === "Knight" ? 5 : 3) : 1) : 1));
    let r = this.rnd.next() * weights.reduce((a, b) => a + b, 0);
    for (let i = 0; i < pool.length; i++) { r -= weights[i]; if (r < 0) return pool[i]; }
    return pool[pool.length - 1];
  },

  // a blow lands on a hero: a guard steps in, a raised guard halves it, the song and a prayer soften it
  hurt(h, dmg, by, opts = {}) {
    const c = this.combat || {};
    if (h && h.thrall) {                                                  // the Necromancer's thrall, between the party and the blow
      h.hp -= dmg;
      this.say(`${CM.The(by)} hits the thrall for ${dmg}.` + (h.hp <= 0 ? " The thrall comes apart." : ""));
      this.emit("fx", { kind: "hurt", hero: null, amount: dmg, foe: by });
      return dmg;
    }
    if (h.guardedBy && h.guardedBy !== h && h.guardedBy.hp > 0 && this.canAct(h.guardedBy)) {
      this.say(`${h.guardedBy.name} steps in front of ${h.name}!`);
      if (CM.trait(h.guardedBy, "aegis")) dmg = Math.ceil(dmg / 2);
      h = h.guardedBy;
    }
    if (h.defending) dmg = Math.ceil(dmg / 2);
    if (this.song) dmg -= this.song;
    if (c.protect) dmg -= 3 + (c.protectMore || 0);
    if (this.has("glass")) dmg *= 2;
    if (opts.aoe && this.formation === "loose") dmg = Math.ceil(dmg / 2);
    dmg = Math.max(1, dmg);
    h.hp -= dmg;
    if (h.hp <= 0 && CM.trait(h, "undying") && !h.undied) { h.undied = true; h.hp = 1; this.say(`${h.name} does not fall. Not this once.`); }
    if ((h.status || {}).sleep) delete h.status.sleep;                   // (a blow wakes)
    const thorns = CM.gearProp(h, "thorns");
    if (thorns > 0 && by && by.hp > 0 && !opts.noTouch && by.ability !== "ranged") { by.hp -= thorns; this.say(`${CM.The(by)} is torn on ${h.name}'s spikes (-${thorns}).`); this.emit("fx", { kind: "hit", foe: by, amount: thorns }); }
    this.sound(h.hp <= 0 ? "fallen" : "hurt");
    this.emit("fx", { kind: "hurt", hero: h, amount: dmg, foe: by });
    this.say(`${CM.The(by)} hits ${h.name} for ${dmg}${opts.how || ""}.` + (h.hp <= 0 ? `  ${h.name} falls!` : ""));
    if (h.hp <= 0) { this.fightFell = true; this.everFell = true; this.cheer(-15, `${h.name} fell`); }
    if (h.hp > 0) {
      if (!opts.noTouch && by.touch && this.rnd.chance(by.touch.chance)) this.afflict(h, by.touch.status, by.name);
      if ((h.boons || []).includes("secondwind") && !h.winded && h.hp < h.max / 4) {
        h.winded = true;
        const back = Math.floor(h.max / 3);
        h.hp = Math.min(h.max, h.hp + back);
        this.say(`${h.name} finds a second wind (+${back}).`);
      }
    }
    return dmg;
  },

  // a monster's turn: what its kind does
  monsterAct(m) {
    const c = this.combat || {}, rnd = this.rnd;
    if (m.asleep > 0) { m.asleep--; if (m.asleep === 0) this.say(`The ${m.name} stirs.`); return; }
    if (m.held > 0) { m.held--; this.say(`The ${m.name} is held fast.`); return; }
    if (m.boss) { this.lichAct(m); return; }
    if (m.guardian) { this.guardianAct(m); return; }
    if (m.ability !== "ranged" && m.ability !== "breath") {
      c.reached = (c.reached || 0) + 1;
      const limit = this.reachLimit();
      if (c.reached > limit) { if (c.reached === limit + 1) this.say("The rest crowd behind, unable to reach you in the narrow way."); return; }
    }
    if (m.ability === "healer") {                                         // it mends the most hurt of its fellows, when one is hurt enough
      const hurt = this.living().filter((f) => f !== m && f.hp < f.max * 0.6).sort((a, b) => a.hp / a.max - b.hp / b.max)[0];
      if (hurt) { const back = Math.max(2, Math.floor(hurt.max * 0.2)); hurt.hp = Math.min(hurt.max, hurt.hp + back); this.say(`${CM.The(m)} mutters over ${CM.the(hurt)}: its wounds close (+${back}).`); this.emit("fx", { kind: "mend", foe: hurt }); return; }
    }
    if (m.ability === "warder") {                                         // it wards a fellow (or itself) against the next blows
      const ward = this.living().filter((f) => !f.warded).sort((a, b) => a.hp / a.max - b.hp / b.max)[0];
      if (ward && rnd.chance(0.6)) { ward.warded = 2; this.say(`${CM.The(m)} hums, and a sheen of crystal closes over ${ward === m ? "it" : CM.the(ward)}: the next blows do half.`); this.emit("fx", { kind: "ward", foe: ward }); return; }
    }
    if (m.ability === "thief" && !m.stole) {                              // it snatches something from the pack, and bolts with it
      const row = this.bag.findIndex((i) => ["heal", "mana", "scroll", "wand", "antidote", "gem"].includes(i.kind));
      if (row >= 0 && rnd.chance(0.5)) {
        const item = this.bag.splice(row, 1)[0];
        m.stole = true; m.fled = true;
        this.say(`${CM.The(m)} darts in, snatches the ${item.name} from the pack, and is gone up the flue with it!`);
        this.emit("fx", { kind: "die", foe: m });
        return;
      }
    }
    if (m.ability === "coward" && m.hp < m.max * 0.3) {
      const purse = Math.floor(this.gold * 0.05);
      this.gold -= purse;
      m.fled = true;
      this.say(`The ${m.name} snatches a purse (${purse} gold) and bolts!`);
      this.emit("fx", { kind: "die", foe: m });
      return;
    }
    if (m.ability === "breath") {
      m.breath = (m.breath || 0) + 1;
      if (m.breath % 2 === 0) {
        this.emit("fx", { kind: "attack", foe: m, breath: true });
        this.say(`The ${m.name} breathes fire over the whole party!`);
        for (const h of this.targets()) this.hurt(h, Math.max(1, Math.floor(m.atk / 3) + 2), m, { noTouch: true, aoe: true });
        return;
      }
    }
    this.emit("fx", { kind: "attack", foe: m, ranged: m.ability === "ranged" });
    const blows = m.ability === "buffet" ? 2 : 1;
    for (let i = 0; i < blows; i++) {
      const target = this.pickTarget(m);
      if (!target) break;
      if (m.marked && !target.thrall && rnd.chance(0.3) && this.alive().some((h) => CM.trait(h, "lastlaugh"))) { const own = Math.max(1, Math.floor(m.atk / 3)); m.hp -= own; this.say(`${CM.The(m)}, mocked past bearing, strikes at nothing and catches itself (-${own}).`); continue; }
      if (!rnd.chance(0.8 * (m.blind > 0 ? 0.5 : 1) * this.dodgeOf(target) * (this.terrain().includes("dark") ? 0.85 : 1))) { this.say(`${CM.The(m)} misses ${target.name}.`); if (!target.thrall && CM.trait(target, "counter") && this.canAct(target)) { this.say(`${target.name} answers.`); this.strike(target, m, " in answer"); } continue; }
      let dmg = this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + CM.gearDefence(target)), how = "";
      if (m.ability === "savage" && rnd.chance(0.2)) { dmg *= 2; how = " - a savage blow"; }
      if (m.ability === "charge" && !m.charged) { m.charged = true; dmg *= 2; how = " - it charges"; }
      const dealt = this.hurt(target, dmg, m, { how });
      if (target.hp > 0) {
        if (m.ability === "stun" && rnd.chance(0.25) && !target.thrall && !(target.status || {}).paralysis && !CM.trait(target, "immovable") && target.quirk !== "stubborn") { target.status.paralysis = 1; this.say(`${target.name} is knocked flat!`); }
        if (m.ability === "drain" && target.xp > 0) {
          const lost = Math.min(target.xp, Math.max(5, Math.floor(CM.xpForLevel(target.level + 1) * 0.15)));
          target.xp -= lost;
          this.say(`${target.name} feels the ${m.name} draw out ${lost} experience.`);
        }
      }
      if (m.ability === "lifesteal") { const back = Math.ceil(dealt / 2); m.hp = Math.min(m.max, m.hp + back); this.say(`The ${m.name} feeds: +${back}.`); }
    }
    if (m.blind > 0) m.blind--;
  },

  // the Lich King: a grave-cold touch; hurt, he calls skeletons up out of the floor; near his end, a deathly cold on everyone
  lichAct(m) {
    const c = this.combat || {}, share = m.hp / m.max;
    if (share <= CM.LICH.summonFrom) {
      c.summonTick = (c.summonTick || 0) + 1;
      const up = this.foes.filter((f) => f.summoned && f.hp > 0).length;
      if (c.summonTick % CM.LICH.summonEvery === 1 && up < CM.LICH.summonMax) { this.summonSkeletons(Math.min(2, CM.LICH.summonMax - up)); return; }
    }
    if (share <= CM.LICH.coldFrom) {
      c.cold = (c.cold || 0) + 1;
      if (c.cold % (this.difficulty === "grim" ? 3 : 2) === 0) {              // (on Grim the cold comes every third turn: a wall with a door)
        this.emit("fx", { kind: "cold", foe: m });
        this.say("The Lich King raises his hand, and a deathly cold fills the hall!");
        for (const h of this.targets()) this.hurt(h, 10 + Math.floor(this.floor.number / 2), m, { noTouch: true, aoe: true });
        return;
      }
    }
    const target = this.pickTarget(m);
    if (!target) return;
    this.emit("fx", { kind: "attack", foe: m });
    if (!this.rnd.chance(0.85 * this.dodgeOf(target))) { this.say(`The Lich King's hand closes on nothing: ${target.name} is too quick.`); return; }
    this.hurt(target, this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + CM.gearDefence(target)), m, { how: " - a touch of grave-cold" });
  },

  summonSkeletons(n) {
    for (let i = 0; i < n; i++) {
      const s = CM.skeleton(CM.LAST_FLOOR, this.rnd);
      Object.assign(s, { summoned: true, held: 0, asleep: 0, blind: 0, marked: false, charged: false, fled: false, dead: false });
      this.foes.push(this.tune(s));
    }
    this.sound("roar_undead");
    this.say(`The Lich King calls, and ${CM.plural(n, "skeleton")} claw up out of the floor!`);
    this.emit("fx", { kind: "summon" });
  },

  // a guardian's turn (CM.GUARDIANS): every third turn one of its moves, in turn - a swarm called, a grasp, a slam on
  // the front line or on everyone, a breath of fire, an ailment on the party; otherwise a blow like any other
  guardianAct(m) {
    const rnd = this.rnd, G = CM.GUARDIANS[m.guardian], moves = G.moves || [];
    m.turns = (m.turns || 0) + 1;
    m.intent = null;
    const every = m.quick ? 2 : 3;                                        // (the flooded Knight comes faster)
    if (m.hidden) { const up = this.foes.filter((f) => f.summoned && f.hp > 0 && !f.fled).length; if (up < 4) this.summonFor(m, moves[0], Math.min(2, 4 - up)); else this.say("The heap seethes."); return; }
    const telegraph = () => {                                             // next turn is one of its moves: it shows, so the party can brace
      if ((m.turns + 1) % every === 0 && moves.length && !m.broken) { const next = moves[(Math.floor((m.turns + 1) / every) - 1) % moves.length]; m.intent = next; this.say(next.warn || G.warn || `${CM.The(m)} gathers itself for something terrible.`); this.emit("fx", { kind: "intent", foe: m }); }
    };
    if (m.turns % every === 0 && moves.length && !m.broken) {
      const mv = moves[(Math.floor(m.turns / every) - 1) % moves.length];
      if (this.guardianMove(m, mv)) { telegraph(); return; }
    }
    const target = this.pickTarget(m);
    if (!target) return;
    this.emit("fx", { kind: "attack", foe: m });
    if (!rnd.chance(0.85 * this.dodgeOf(target))) { this.say(`${CM.The(m)} misses ${target.name}.`); telegraph(); return; }
    let dmg = this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + CM.gearDefence(target)), how = "";
    if (CM.guardianHas(m, "plague") && (target.status || {}).poison) { dmg = Math.ceil(dmg * 1.5); how = " - the plague bites deep"; }
    this.hurt(target, dmg, m, { how });
    if (CM.guardianHas(m, "drain") && target.hp > 0 && target.xp > 0) {   // (the Patriarch's old hunger)
      const lost = Math.min(target.xp, Math.max(5, Math.floor(CM.xpForLevel(target.level + 1) * 0.15)));
      target.xp -= lost;
      this.say(`${target.name} feels ${CM.the(m)} draw out ${lost} experience.`);
    }
    telegraph();
  },

  guardianMove(m, mv) {
    const rnd = this.rnd, who = (t) => (mv.text || "").replace("{who}", t ? t.name : "");
    if (mv.kind === "summon") {
      const up = this.foes.filter((f) => f.summoned && f.hp > 0 && !f.fled).length;
      if (up >= mv.max) return false;
      this.summonFor(m, mv, Math.min(mv.n, mv.max - up));
      return true;
    }
    if (mv.kind === "grasp") {
      const target = this.pickTarget(m);
      if (!target) return false;
      this.emit("fx", { kind: "grasp", hero: target, foe: m });
      this.say(who(target));
      this.hurt(target, Math.ceil(this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + CM.gearDefence(target)) * (mv.mult || 1.5)), m, { how: mv.how || "", noTouch: true });
      if (target.hp > 0 && mv.status && this.afflict(target, mv.status, m.name) && mv.status === "paralysis") target.status.paralysis = 1;
      return true;
    }
    if (mv.kind === "slam") {
      const pool = this.targets(), front = pool.filter((h) => h.row === "front"), struck = mv.front && front.length ? front : pool;
      if (!struck.length) return false;
      this.emit("fx", { kind: "slam", foe: m });
      this.sound("slam");
      this.say(who());
      for (const h of struck) {
        this.hurt(h, this.damage(Math.floor(m.atk / (mv.frac || 2.5)), 0, this.effective(h).df + CM.gearDefence(h)), m, { how: mv.how || "", noTouch: true, aoe: true });
        if (h.hp > 0 && mv.status && rnd.chance(mv.chance || 0.3) && !(h.status || {})[mv.status]) {
          h.status[mv.status] = mv.status === "paralysis" ? 1 : mv.status === "blind" ? 2 : 2;
          this.say((mv.flat || "{who} reels.").replace("{who}", h.name));
        }
      }
      return true;
    }
    if (mv.kind === "breath") {
      const pool = this.targets();
      if (!pool.length) return false;
      this.emit("fx", { kind: "attack", foe: m, breath: true });
      this.say(who());
      for (const h of pool) this.hurt(h, Math.max(1, Math.floor(m.atk / (mv.frac || 2)) + 2), m, { noTouch: true, aoe: true });
      return true;
    }
    if (mv.kind === "ailment") {
      const pool = this.targets();
      if (!pool.length) return false;
      this.emit("fx", { kind: "cold", foe: m });
      this.say(who());
      let took = 0;
      for (const h of pool) if (rnd.chance(mv.chance === undefined ? 0.6 : mv.chance) && this.afflict(h, mv.status, m.name)) took++;
      if (!took) this.say("The party shakes it off.");
      return true;
    }
    return false;
  },

  // what a guardian calls up: its own kind of company, at the Deep's level where it says so
  summonFor(m, mv, n) {
    const kind = CM.monsterKind(mv.what);
    if (!kind) return;
    const level = mv.level === "deep" ? CM.monsterLevel(this.floor ? this.floor.number : CM.LAST_FLOOR) : (this.floor ? this.floor.number : 5);
    for (let i = 0; i < n; i++) {
      const r = CM.makeMonster(kind, level, this.rnd);
      Object.assign(r, { summoned: true, held: 0, asleep: 0, blind: 0, marked: false, charged: false, fled: false, dead: false });
      this.foes.push(this.tune(r));
    }
    this.sound(CM.roarFor(kind.name));
    this.say((mv.text || "{n} come.").replace("{n}", mv.plural ? mv.plural.replace("{n}", String(n)) : CM.plural(n, mv.word || kind.name.toLowerCase())));
    this.emit("fx", { kind: "summon", layer: kind.undead ? "fx:shard" : "fx:spark" });
  },

  summonRats(n) { this.summonFor(this.foes.find((f) => f.guardian === "rat") || { name: "The Rat King" }, CM.GUARDIANS.rat.moves[0], n); },

  // the Lich King falls: the crown is the party's, and the choice - into the daylight, or down the shaft the throne hid
  crown() {
    this.crowned = true;
    this.trophy("lich");
    const steps = (this.tally || {}).steps || 0;
    this.achieve("crown");
    if (!this.everFell) this.achieve("ironman");
    if (steps < 1500) this.achieve("swift");
    if (this.difficulty === "grim") this.achieve("grim");
    this.achieve("delver"); this.achieve("deep"); this.achieve("deeper");
    if (this.foeKey) this.floor.things[this.foeKey] = { type: "ladder" };
    this.sound("victory");
    this.say(this.reminded ? "The crown is set down, not struck off. Behind the throne the floor has split all the same: a shaft goes down, into a dark that was never his. The Deep."
      : "The crown rolls from the throne, and the cold goes out of the stone. Behind the throne the floor has split: a shaft goes down, into a dark that was never his. The Deep.");
    this.setMode("explore");
    this.saveRun();
    this.emit("crowned");
  },

  // a guardian falls: its relic into the pack, a trophy kept between runs, and the shaft it stood over is open
  slayGuardian(m) {
    const id = m.guardian, G = CM.GUARDIANS[id], relic = G.relic && !m.echo ? CM.relic(id) : null;
    this.tally.guardians = (this.tally.guardians || []).concat(id);
    if (!m.echo) this.trophy(id);
    if (relic) this.bag.push(relic);
    this.sound("toll");
    this.say(G.fall);
    { const P = CM.PARLEY[id], fought = this.floor && this.floor.things[this.foeKey]; if (P && !m.echo) this.say(fought && fought.spoke ? P.deathSpoken : P.death); }
    this.lairAfter(id);
    this.say(m.echo ? "The echo fades, and leaves nothing but the shaft it stood over." : relic ? `${G.take} (${relic.name}: ${CM.itemLabel(relic)}.)` : G.take);
    this.emit("fx", { kind: "relic", item: relic });
  },

  trophy(id) {                                                           // a guardian slain, remembered between runs
    if (this.trophies[id]) return;
    this.trophies[id] = { date: CM.today(), name: CM.playerName || "Adventurer", seed: this.seed };
    CM.store.set("trophies", this.trophies);
  },

  // one hero's blow on one foe (Fight, and the Ranger's arrows): the damage done, 0 for a miss
  strike(hero, target, note = "", opts = {}) {
    const rnd = this.rnd;
    this.emit("fx", { kind: "swing", hero, foe: target });
    const bow = Boolean(hero.weapon && hero.weapon.props && hero.weapon.props.bow), ambush = CM.trait(hero, "ambush") && !hero.struck;
    const dark = this.terrain().includes("dark");
    if (!opts.sure && !ambush && !(bow && CM.trait(hero, "truearrow")) && !rnd.chance(this.hitChance(hero) * (dark ? 0.85 : 1))) {
      this.say(`${hero.name} misses${note ? " with" + note : ""}.`);
      this.sound("miss");
      this.emit("fx", { kind: "miss", foe: target });
      return 0;
    }
    let dmg = this.damage(this.effective(hero).atk, hero.weapon.power, bow && CM.trait(hero, "piercing") ? Math.floor(target.df / 2) : target.df), how = "";
    const back = hero.row === "back", reaches = hero.cls === "Rogue" || hero.cls === "Ranger";
    const critMult = CM.trait(hero, "deadly") ? 3 : 2;
    if (target.elite === "spectral" && rnd.chance(0.5)) { this.say(`${hero.name}'s blow passes through ${CM.the(target)}.`); this.emit("fx", { kind: "miss", foe: target }); return 0; }
    if (hero.cls === "Rogue" && back) { dmg *= 2; how = " - a knife from behind"; }
    else if (ambush || rnd.chance(this.critChance(hero))) { dmg *= critMult; how = " - a weak spot"; }
    else if (back && !reaches && !(this.formation === "wedge" && this.point() !== hero)) { dmg = Math.max(1, Math.ceil(dmg / 2)); how = ", reaching from the back row"; }
    if (this.formation === "loose") dmg = Math.max(1, Math.ceil(dmg * 0.85));
    if ((this.fed || 0) >= CM.HUNGER.weary) dmg = Math.max(1, Math.ceil(dmg * 0.85));
    if (target.row === "back" && !bow && this.living().some((f) => f !== target && f.row !== "back")) { dmg = Math.max(1, Math.ceil(dmg / 2)); how += ", reaching past the front"; }   // (their back row, as yours)
    if ((hero.boons || []).includes("warcry") && !hero.cried) { hero.cried = true; dmg *= 2; how += " - a war cry"; }
    const props = (hero.weapon && hero.weapon.props) || {}, el = (props.element && !hero.weapon.unknown ? props.element : null) || (hero.oil && hero.oil.fights > 0 ? hero.oil.element : null);
    const G = target.guardian ? CM.GUARDIANS[target.guardian] : null;   // (its heat, its shards: below)
    if (el) {                                                            // a flaming, frost or blessed blade
      const r = CM.resistance(target, el);
      this.learnResist(target, el, r);
      if (r > 1) { dmg = Math.ceil(dmg * r); how += ` - the ${el === "holy" ? "blessing" : el} bites deep`; }
      else if (r < 1) { dmg = Math.max(1, Math.ceil(dmg * r)); how += ` - the ${el} does little to it`; }
      else dmg += 2;
    }
    else if (target.undead && CM.trait(hero, "holyblade")) { dmg = Math.ceil(dmg * 1.5); how += " - the blessing in the blade bites deep"; }
    hero.struck = true;
    if (opts.mult) dmg = Math.ceil(dmg * opts.mult);
    if (target.marked) dmg = Math.ceil(dmg * 1.25);
    if (CM.trait(hero, "executioner") && target.hp < target.max / 4) { dmg *= 2; how += " - the end of it"; }
    const friend = this.bondOf(hero);
    if (friend && friend.hp <= 0 && !hero.avenged) { hero.avenged = true; dmg *= 2; how += ` - for ${friend.name}`; }
    if (opts.bash && target.chilled > 0) { dmg *= 2; how += " - the ice shatters"; this.combo("shatter"); target.chilled = 0; }
    if (hero.cls === "Rogue" && target.marked) { dmg = Math.ceil(dmg * 1.5); how += " - the knife finds the mark"; this.combo("knife"); }
    if (target.warded > 0) { dmg = Math.max(1, Math.ceil(dmg / 2)); how += " - the ward takes half"; target.warded -= 1; }
    if (this.has("glass")) dmg *= 2;
    dmg = Math.ceil(dmg * this.scholarship(target));
    target.hp -= dmg;
    this.splitIfHurt(target);
    if (target.asleep > 0) { target.asleep = 0; how += " - it wakes"; }
    this.say(`${hero.name} hits ${CM.the(target)}${note} for ${dmg}${how}.`);
    this.emit("fx", { kind: "hit", foe: target, amount: dmg });
    this.sound("hit");
    if (props.stun && target.hp > 0 && !CM.unmoved(target) && rnd.chance(props.stun)) { target.held = Math.max(target.held || 0, 1); this.say(`${CM.The(target)} reels from the blow.`); }
    if (props.sleep && !hero.weapon.unknown && target.hp > 0 && !CM.unmoved(target) && rnd.chance(props.sleep)) { target.asleep = 2; this.say(`${CM.The(target)} hears the tide in the blade, and sleeps.`); }
    if (props.lifesteal && !hero.weapon.unknown && hero.hp > 0 && hero.hp < hero.max) { const back = Math.max(1, Math.ceil(dmg / 4)); hero.hp = Math.min(hero.max, hero.hp + back); this.say(`${hero.name}'s blade drinks: +${back}.`); }
    if ((CM.guardianHas(target, "heat") || CM.guardianHas(target, "glass")) && !props.bow && hero.hp > 0) {   // its heat, or its shards: whoever strikes it pays
      const burn = (2 + Math.floor((this.floor ? this.floor.number : 15) / 5)) * (target.broken ? 2 : 1);
      hero.hp = Math.max(1, hero.hp - burn);
      this.say((G.sear || "The heat of " + CM.the(target) + " sears {who} (-{n}).").replace("{who}", hero.name).replace("{n}", burn));
      this.emit("fx", { kind: "sear", hero, amount: burn, foe: target });
    }
    return dmg;
  },

  // a spell's blow: it doesn't miss
  spellHit(foe, dmg, what, element) {
    let how = "";
    if (element === "fire" && this.casting && CM.trait(this.casting, "firebrand")) dmg = Math.ceil(dmg * 1.5);
    const r = CM.resistance(foe, element);                              // (what it fears, and what it shrugs off)
    if (element) this.learnResist(foe, element, r);
    if (r > 1) { dmg = Math.ceil(dmg * r); how = ` - the ${CM.ELEMENT_NAMES[element] || element} bites deep`; }
    else if (r < 1) { dmg = Math.max(1, Math.ceil(dmg * r)); how = ` - the ${CM.ELEMENT_NAMES[element] || element} does little to it`; }
    if (foe.marked) dmg = Math.ceil(dmg * 1.25);
    if (element === "fire" && this.terrain().includes("water")) { dmg = Math.max(1, Math.ceil(dmg / 2)); how += " - the fire sputters on the water"; }
    if ((this.fed || 0) >= CM.HUNGER.weary) dmg = Math.max(1, Math.ceil(dmg * 0.9));
    if (foe.elite === "mirrored") { dmg = Math.max(1, Math.ceil(dmg / 2)); const back = Math.max(1, Math.ceil(dmg / 2)); if (this.casting && this.casting.hp > 0) { this.casting.hp = Math.max(1, this.casting.hp - back); this.say(`The spell comes back off ${CM.the(foe)}'s mirror onto ${this.casting.name} (-${back}).`); } }
    if (element === "fire" && foe.held > 0) { dmg = Math.ceil(dmg * 1.5); how += " - the vines burn"; this.combo("kindling"); }
    if (element === "storm" && foe.chilled > 0) { dmg *= 2; how += " - the ice carries it"; this.combo("thunderclap"); foe.chilled = 0; }
    if (foe.warded > 0) { dmg = Math.max(1, Math.ceil(dmg / 2)); how += " - the ward takes half"; foe.warded -= 1; }
    if (this.has("glass")) dmg *= 2;
    dmg = Math.ceil(dmg * this.scholarship(foe));
    foe.hp -= dmg;
    if (foe.asleep > 0) foe.asleep = 0;
    this.emit("fx", { kind: "hit", foe, amount: dmg, spell: true });
    if (what) this.say(`${what} ${foe.name} takes ${dmg}${how}.`);
    this.splitIfHurt(foe);
    return dmg;
  },

  // the Crystal Caverns' mirror walls: a bolt at one foe rebounds onto another, for half
  rebound(foe, dmg, element) {
    if (!this.floor || this.floor.hazard !== "mirror") return;
    const other = this.living().find((m) => m !== foe);
    if (!other) return;
    this.spellHit(other, Math.max(1, Math.ceil(dmg / 2)), "The bolt rebounds off the crystal:", element);
  },

  // a Spore Beast badly hurt tears in two: the other half takes its place beside it, once
  splitIfHurt(m) {
    if (m.ability !== "splitter" || m.split || m.hp <= 0 || m.hp > m.max / 2 || this.mode !== "combat") return;
    m.split = true;
    const twin = Object.assign({}, m, { hp: m.hp, max: m.max, held: 0, asleep: 0, blind: 0, marked: false, charged: false, fled: false, dead: false, chilled: 0, warded: 0, summoned: true, xp: Math.floor(m.xp / 2), gold: 0 });
    delete twin.anim;
    this.foes.push(twin);
    this.say(`${CM.The(m)} tears in two, and both halves come on!`);
    this.emit("fx", { kind: "summon", layer: "fx:leaf" });
  },

  // a combo done: named once in the log, and remembered (the journal keeps every one found)
  combo(id) {
    const c = CM.COMBOS[id];
    if (!c) return;
    this.combos = this.combos || {};
    const first = !this.combos[id];
    this.combos[id] = (this.combos[id] || 0) + 1;
    if (first) { CM.store.set("combos", this.combos); this.say(`Combo - ${c.name}! ${c.what}`); this.emit("fx", { kind: "combo", id }); }
  },

  // the bestiary: every kind met, slain, and what it has been seen to fear or shrug off (kept between runs)
  noteFoe(m, what) {
    if (!m || m.boss || m.guardian) return;
    const kind = m.kind || m.name;
    this.bestiary = this.bestiary || {};
    const e = this.bestiary[kind] = this.bestiary[kind] || { seen: 0, slain: 0, weak: [], resist: [] };
    e[what] = (e[what] || 0) + 1;
    this.bestiaryDirty = true;
  },
  learnResist(m, element, r) {
    if (r === 1 || !m || m.boss || m.guardian) return;
    const kind = m.kind || m.name;
    this.bestiary = this.bestiary || {};
    const e = this.bestiary[kind] = this.bestiary[kind] || { seen: 0, slain: 0, weak: [], resist: [] };
    const list = r > 1 ? e.weak : e.resist;
    if (!list.includes(element)) { list.push(element); this.bestiaryDirty = true; }
  },

  // a familiar chosen at level 6 (the Mage's: a cat, an owl, a toad; the Necromancer's skull comes by itself)
  chooseFamiliar(hero, id) {
    const F = CM.FAMILIARS[id];
    if (!F || !F.cls.includes(hero.cls) || hero.familiar || hero.level < CM.FAMILIAR_AT || hero.hp <= 0) return false;
    this.logAct("chooseFamiliar", this.party.indexOf(hero), id);
    hero.familiar = id;
    this.sound("level");
    this.say(`${hero.name} is joined by ${F.name}: ${F.what}.`);
    this.saveRun(); this.emit("change");
    return true;
  },
  needsFamiliar(h) { return Boolean(h && h.hp > 0 && !h.familiar && h.level >= CM.FAMILIAR_AT && Object.values(CM.FAMILIARS).some((F) => F.cls.includes(h.cls))); },

  // what a hero reaches for when told only "cast": their calling's own thing, if they can afford it
  defaultAbility(h) {
    const can = CM.abilitiesFor(h).filter((id) => CM.ABILITIES[id].mp <= h.mp && !(CM.ABILITIES[id].once && h.used && h.used[id]));
    const prefer = { Mage: ["fireball", "frost", "firebolt", "missile"], Cleric: ["heal"], Paladin: ["lay"], Druid: ["thorns"], Bard: ["song"],
      Ranger: ["volley"], Knight: ["guard"], Rogue: ["trick"] }[h.cls] || [];
    return prefer.find((id) => can.includes(id)) || null;
  },

  // the old game's Cast, kept for the tests: the calling's own thing, at whoever needs it most
  cast(hero) {
    if (!this.useAbility(hero, this.defaultAbility(hero), null)) {
      const t = this.foeAt(null);
      if (t) this.strike(hero, t);
    }
  },

  // a spell or skill, if the hero knows it, can afford it and has someone to aim it at
  // the cost of a spell for this hero: its level (a tome read twice), the path, the formation
  spellCost(h, a, power = 1) {
    if (!a.mp) return 0;
    const lvl = (h.spellLevels || {})[a.id] || 1;
    let cost = Math.max(1, a.mp - (lvl - 1));
    if (CM.trait(h, "thrifty")) cost = Math.max(1, cost - 1);
    if (this.formation === "loose") cost += 1;
    return cost * (CM.OVERCAST[power] || CM.OVERCAST[1]).cost;
  },
  // what a spell's numbers are multiplied by right now: its level, the overcast, a reagent
  spellMult(h, id) {
    const lvl = (h && h.spellLevels || {})[id] || 1;
    return (1 + 0.25 * (lvl - 1)) * (this.castMult || 1);
  },
  pow(n) { return Math.max(1, Math.ceil(n * (this.castScale || 1))); },
  // the reagent in the pack that goes with a spell, if any: {row, id}
  reagentFor(id) {
    for (let row = 0; row < this.bag.length; row++) { const it = this.bag[row]; if (it.kind === "ingredient" && CM.REAGENTS[it.ingredient] && CM.REAGENTS[it.ingredient].spells.includes(id)) return { row, id: it.ingredient }; }
    return null;
  },
  useAbility(h, id, target, power, reagentRow) {
    this.tally.abilities = this.tally.abilities || {};
    if (id) this.tally.abilities[id] = (this.tally.abilities[id] || 0) + 1;
    if (!id) {
      const t = this.foeAt(target);
      if (!t) return false;
      if (CM.CLASSES[h.cls] && CM.CLASSES[h.cls].cast) this.say(`${h.name} is out of magic, and swings instead.`);
      this.strike(h, t);
      return true;
    }
    const a = CM.ABILITIES[id];
    if (!a || !CM.abilitiesFor(h).includes(id)) { this.say(`${h.name} doesn't know that.`); return false; }
    if (a.once && h.used && h.used[id]) { this.say(`${h.name} has used ${a.name} this fight.`); return false; }
    power = a.mp && CM.OVERCAST[power] ? power : 1;
    const cost = this.spellCost(h, Object.assign({ id }, a), power);
    if (h.mp < cost) { this.say(`${h.name} hasn't the magic for ${a.name}${power > 1 ? " at that strength" : ""}.`); return false; }
    let reagent = null;
    if (reagentRow !== undefined && reagentRow !== null && this.bag[reagentRow] && this.bag[reagentRow].kind === "ingredient" && (CM.REAGENTS[this.bag[reagentRow].ingredient] || {}).spells.includes(id)) reagent = this.bag[reagentRow].ingredient;
    if (this.mode !== "combat" && !a.outside) { this.say(`${a.name} is for a fight.`); return false; }
    const foes = this.attackable();
    let foe = null, ally = null;
    if (a.target === "foe") { foe = this.foeAt(target); if (!foe) return false; }
    if (a.target === "foes" && !foes.length) return false;
    if (a.target === "ally") {
      ally = this.allyAt(target, false);
      if (id === "lay" && CM.trait(h, "lastrites") && !(h.used && h.used.lastrites)) {   // (Last Rites: a fallen hero may be the one)
        const fallen = this.allyAt(target, true);
        if (fallen && (typeof target === "number" ? this.party[target] === fallen : !ally)) ally = fallen;
      }
      if (!ally) { this.say("No one to cast that on."); return false; }
    }
    if (a.target === "fallen") { ally = this.allyAt(target, true); if (!ally) { this.say("No one has fallen."); return false; } }
    h.mp -= cost;
    if (a.once) { h.used = h.used || {}; h.used[id] = true; }
    if (reagent) { this.bag.splice(reagentRow, 1); this.say(`${h.name} crumbles ${CM.INGREDIENTS[reagent].name.toLowerCase()} into the casting: ${CM.REAGENTS[reagent].what}.`); }
    if (power > 1) this.say(`${h.name} pours more into it: ${a.name} at ${power === 2 ? "half again" : "double"} the strength.`);
    this.sound(a.mp ? "spell" : "hit");
    this.emit("fx", { kind: "cast", id, hero: h, foe, ally, foes, power });
    this.casting = h; this.castMult = (CM.OVERCAST[power] || CM.OVERCAST[1]).mult; this.castScale = this.spellMult(h, id); this.reagent = reagent;
    this.doAbility(h, id, a, foe, ally, foes);
    this.weave(h, id, foes);
    this.casting = null; this.castMult = 1; this.castScale = 1; this.reagent = null;
    if (power === 3 && CM.OVERCAST[3].backlash && this.rnd.chance(CM.OVERCAST[3].backlash) && h.hp > 1) { const burn = Math.max(1, Math.floor(h.max / 10)); h.hp = Math.max(1, h.hp - burn); this.say(`The magic bites back: ${h.name} burns for ${burn}.`); this.emit("fx", { kind: "sear", hero: h, amount: burn, foe: { name: "The spell" } }); }
    this.emit("change");
    return true;
  },

  // two casters in one round: the first holds, the second matches, and the weave is more than both (CM.WEAVES)
  weave(h, id, foes) {
    const c = this.combat;
    if (!c || this.mode !== "combat" || !CM.ABILITIES[id].mp) return;
    const held = c.held;
    c.held = { id, hero: h, round: c.round };
    if (!held || held.round !== c.round || held.hero === h) return;
    const key = [held.id, id].sort().join("+"), W = CM.WEAVES[key];
    if (!W) return;
    const L = Math.max(h.level, held.hero.level), mod = Math.max(this.spellMod(h), this.spellMod(held.hero)), living = this.attackable();
    this.weaves = this.weaves || {};
    const first = !this.weaves[key];
    this.weaves[key] = (this.weaves[key] || 0) + 1;
    CM.store.set("weaves", this.weaves);
    this.say(`Weave - ${W.name}! ${held.hero.name} and ${h.name} make one spell of two.`);
    this.emit("fx", { kind: "combo", id: key });
    switch (W.name) {
      case "Steam": for (const m of living) { m.blind = Math.max(m.blind || 0, 2); this.spellHit(m, Math.max(1, 6 + 2 * L + mod), "The steam scalds:"); } break;
      case "Firestorm": for (const m of living) { this.spellHit(m, Math.max(1, 8 + 4 * L + mod), "The firestorm:", "fire"); if (m.hp > 0) { m.burning = Math.max(m.burning || 0, 2); m.burnDmg = Math.max(m.burnDmg || 0, 5 + L); } } break;
      case "Sanctuary": for (const m of living) if (!CM.unmoved(m)) m.held = Math.max(m.held || 0, 1); for (const p of this.alive()) p.hp = Math.min(p.max, p.hp + 6 + L); this.sound("heal"); break;
      case "Nightmare": for (const m of living) if (m.asleep > 0) this.spellHit(m, Math.max(1, 15 + 3 * L + mod), "Its dream tears at it:"); break;
      case "Barrage": for (let i = 0; i < 2; i++) { const m = living[i % living.length]; if (m) this.spellHit(m, Math.max(1, 6 + 2 * L + mod), "The barrage:"); } break;
      case "Bramble": for (const m of living) if (!CM.unmoved(m)) m.held = Math.max(m.held || 0, 2); break;
      default: break;
    }
    if (first) this.achieve("weaver");
    c.held = null;
  },

  doAbility(h, id, a, foe, ally, foes) {
    const rnd = this.rnd, L = h.level, mod = this.spellMod(h), c = this.combat || {};
    const healAll = (n, text) => { for (const p of this.alive()) p.hp = Math.min(p.max, p.hp + n); this.say(text); this.sound("heal"); };
    switch (id) {
      case "missile": { const d = this.pow(6 + 2 * L + mod); this.spellHit(foe, d, `${h.name}'s bolt of force strikes:`); this.rebound(foe, d, null); if (this.reagent === "crystaldust") { const other = this.attackable().find((m) => m !== foe); if (other) this.spellHit(other, d, "The bolt splits:"); } break; }
      case "firebolt": { const d = this.pow((10 + 3 * L + mod) * (["forgesoot", "slag"].includes(this.reagent) ? 1.5 : 1)); this.spellHit(foe, d, `${h.name}'s fire bolt:`, "fire"); this.rebound(foe, d, "fire"); break; }
      case "lightning": this.spellHit(foe, this.pow(20 + 5 * L + mod), `${h.name} calls down lightning!`, "storm"); this.rebound(foe, this.pow(20 + 5 * L + mod), "storm"); if (CM.trait(h, "tempest") && foe.hp > 0 && !CM.unmoved(foe) && rnd.chance(0.5)) { foe.held = Math.max(foe.held || 0, 1); this.say(`${CM.The(foe)} reels, smoking.`); } break;
      case "calllightning": {
        const dmg = this.pow(18 + 4 * L + mod), struck = CM.trait(h, "stormcall") ? foes : [foe];
        for (const m of struck) { this.spellHit(m, m === foe ? dmg : Math.ceil(dmg * 0.6), m === foe ? `${h.name} calls down lightning!` : "The storm reaches on:", "storm"); if (CM.trait(h, "tempest") && m.hp > 0 && !CM.unmoved(m) && (CM.trait(h, "hurricane") || rnd.chance(0.5))) { m.held = Math.max(m.held || 0, 1); this.say(`${CM.The(m)} reels, smoking.`); } }
        break;
      }
      case "smite": {
        let dmg = this.pow((12 + 3 * L + Math.floor(mod / 2)) * (this.reagent === "bonedust" ? 2 : 1));
        if (c.bless) { dmg = Math.ceil(dmg * 1.5); this.combo("consecrated"); }
        if (CM.trait(h, "radiance") && foes.some((m) => m.undead)) { for (const m of foes) if (m.undead) this.spellHit(m, dmg * 2, `${h.name}'s radiance falls on the unholy:`, "holy"); }
        else this.spellHit(foe, dmg * (foe.undead ? 2 : 1), `${h.name} smites${foe.undead ? " the unholy thing" : ""}:`, "holy");
        break;
      }
      case "fireball": {
        const dmg = this.pow((8 + 4 * L + mod) * (["forgesoot", "slag"].includes(this.reagent) ? 1.5 : 1));
        for (const m of foes) { this.spellHit(m, dmg, "", "fire"); if (CM.trait(h, "inferno") && m.hp > 0) { m.burning = CM.trait(h, "immolation") ? 4 : 2; m.burnDmg = (5 + L) * (CM.trait(h, "immolation") ? 2 : 1); } }
        this.say(`${h.name} hurls a fireball! ${dmg} damage to every foe${CM.trait(h, "inferno") ? ", and they burn" : ""}.`);
        break;
      }
      case "frost": {
        const dmg = this.pow(6 + 2 * L + mod), weed = ["drownedweed", "saltweed"].includes(this.reagent);
        let held = 0;
        for (const m of foes) { this.spellHit(m, dmg, "", "frost"); if (m.hp > 0) m.chilled = 2; if (m.hp > 0 && !CM.unmoved(m) && (weed || this.terrain().includes("water") || rnd.chance(0.3))) { m.held = Math.max(m.held || 0, 1); held++; } }
        this.say(`${h.name} breathes frost over every foe: ${dmg} each${held ? `, ${CM.plural(held, "foe")} frozen fast` : ""}. The ice clings.`);
        break;
      }
      case "sleep": case "lullaby": {
        let asleep = 0;
        for (const m of foes) if (!CM.unmoved(m) && ((id === "lullaby" && CM.trait(h, "lull")) || rnd.chance(0.5 + mod * 0.03))) { m.asleep = this.reagent === "sporecap" ? 99 : 3; asleep++; }
        this.say(id === "sleep" ? `${h.name} weaves a sleep: ${asleep ? CM.plural(asleep, "foe") + " slump where they stand" : "none of them so much as yawns"}.`
          : `${h.name} sings a lullaby: ${asleep ? CM.plural(asleep, "foe") + " nod off" : "none of them so much as yawns"}.`);
        break;
      }
      case "blink": this.flee(true); break;
      case "light": this.spellLight = CM.LIGHT_STEPS; this.say(`${h.name} calls up a light. It will last ${CM.LIGHT_STEPS} steps.`); break;
      case "heal": case "mend": {
        let n = this.pow(((id === "heal" ? 12 + 4 * L : 10 + 3 * L) + mod) * (this.reagent === "gravemoss" ? 1.5 : 1));
        if (id === "heal" && CM.trait(h, "blessedhands")) n = Math.ceil(n * 1.5);
        if (this.bondOf(h) === ally) n = Math.ceil(n * 1.25);
        ally.hp = Math.min(ally.max, ally.hp + n);
        this.sound("heal");
        this.say(`${h.name} ${id === "heal" ? "prays" : "lays on herbs and words"}: ${ally.name} is healed by ${n}.`);
        if (id === "heal" && CM.trait(h, "benediction")) { const rest = Math.ceil(n / 4); for (const p of this.alive()) if (p !== ally) p.hp = Math.min(p.max, p.hp + rest); this.say(`The benediction spreads: everyone else mends ${rest}.`); }
        break;
      }
      case "blows": { this.strike(h, foe, "", { mult: 0.6 }); if (foe.hp > 0 && !foe.fled) this.strike(h, foe, " again", { mult: 0.6 }); break; }
      case "palm": { if (this.strike(h, foe, " with the iron palm") > 0 && foe.hp > 0 && !CM.unmoved(foe) && rnd.chance(0.4)) { foe.held = Math.max(foe.held || 0, 1); this.say(`${CM.The(foe)} reels.`); } break; }
      case "meditate": { const back = Math.ceil(h.max / 4); h.hp = Math.min(h.max, h.hp + back); const cured = this.cure(h, CM.CURABLE); this.sound("heal"); this.say(`${h.name} breathes once, slowly: +${back}${cured.length ? ", and the ailments pass" : ""}.`); break; }
      case "drain": { const dmg = this.pow(8 + 2 * L + mod), dealt = this.spellHit(foe, dmg, `${h.name} pulls the life out of ${CM.the(foe)}:`); const back = CM.trait(h, "deepdrain") ? dealt : Math.ceil(dealt / 2); h.hp = Math.min(h.max, h.hp + back); this.say(`${h.name} keeps ${back} of it.`); break; }
      case "hex": { const struck = CM.trait(h, "contagion") ? foes : [foe]; for (const m of struck) { m.marked = true; m.blind = Math.max(m.blind || 0, 2); if (CM.trait(h, "hexhold") && !CM.unmoved(m)) m.held = Math.max(m.held || 0, 1); } this.say(`${h.name} speaks a hex over ${struck.length > 1 ? "every foe" : CM.the(foe)}: marked, and half-blind${CM.trait(h, "hexhold") ? ", and held" : ""}.`); break; }
      case "thrall": { const dead = this.foes.filter((m) => m.hp <= 0 && !m.fled).pop(); if (!dead) { this.say("Nothing has died here yet to raise."); h.mp += CM.ABILITIES.thrall.mp; delete h.used.thrall; break; } c.thrall = { thrall: true, name: `the ${dead.name} thrall`, hp: Math.max(10, Math.floor(dead.max * 0.6)), max: Math.max(10, Math.floor(dead.max * 0.6)), atk: Math.max(2, Math.floor(dead.atk / 2)), by: h }; this.sound("roar_undead"); this.say(`${h.name} speaks, and ${dead.name} stands up again with empty eyes, between the party and the foes.`); this.emit("fx", { kind: "summon", layer: "fx:shard" }); break; }
      case "deathpact": { const dmg = this.pow(10 + 3 * L + mod), own = Math.max(1, Math.floor(h.max / 10)); for (const m of foes) this.spellHit(m, dmg, ""); h.hp = Math.max(1, h.hp - own); this.say(`${h.name} opens a vein and speaks the pact: every foe withers for ${dmg}; the Necromancer bleeds ${own}.`); break; }
      case "turret": { c.turret = { by: h, dmg: Math.max(1, 5 + 2 * L + Math.floor(mod / 2)) * (CM.trait(h, "twinturret") ? 2 : 1) }; this.sound("lever"); this.say(`${h.name} winds the brass turret and sets it ticking. It will shoot every round.`); break; }
      case "wardengine": { c.protect = true; c.protectMore = CM.trait(h, "bulwarkengine") ? 2 : 0; this.say(`${h.name}'s ward engine hums: every blow on the party does less, this fight.`); break; }
      case "oilgears": { c.oiled = true; this.say(`${h.name} oils the gears: the party moves first from here on.`); break; }
      case "firework": { const dmg = this.pow((7 + 3 * L + mod) * (["forgesoot", "slag"].includes(this.reagent) ? 1.5 : 1)); for (const m of foes) this.spellHit(m, dmg, "", "fire"); this.say(`${h.name}'s firework bursts over every foe: ${dmg} each.`); break; }
      case "lay": {
        if (ally.hp <= 0) {                                              // (Last Rites)
          h.used = h.used || {}; h.used.lastrites = true;
          ally.hp = Math.max(1, Math.floor(ally.max / 3));
          this.sound("heal");
          this.say(`${h.name} lays hands on ${ally.name}, and says the last rites backwards. ${ally.name} breathes.`);
          break;
        }
        let n = this.pow((8 + 3 * L + Math.floor(mod / 2)) * (this.reagent === "gravemoss" ? 1.5 : 1));
        const gentle = CM.trait(h, "gentlehands");
        if (gentle) n = Math.ceil(n * 1.5);
        if (this.bondOf(h) === ally) n = Math.ceil(n * 1.25);
        if (CM.trait(h, "sanctified")) c.protect = true;
        ally.hp = Math.min(ally.max, ally.hp + n);
        const cured = this.cure(ally, gentle ? CM.CURABLE : ["poison"]);
        this.sound("heal");
        this.say(`${h.name} lays on hands: ${ally.name} mends by ${n}${cured.length ? `, and the ${cured.length > 1 ? "ailments leave" : CM.STATUSES[cured[0]].name.toLowerCase() + " leaves"} them` : ""}.`);
        break;
      }
      case "cure": {
        const cured = this.cure(ally, CM.CURABLE);
        this.sound("heal");
        this.say(cured.length ? `${h.name} prays over ${ally.name}: no longer ${cured.map((s) => CM.STATUSES[s].name.toLowerCase()).join(" or ")}.` : `${h.name} prays over ${ally.name}, who had nothing to cure.`);
        break;
      }
      case "lift": {
        let n = 0;
        for (const p of this.alive()) n += this.cure(p, ["curse", "blind", "sleep"]).length;
        this.sound("heal");
        this.say(n ? `${h.name} lifts what lay on the party: ${CM.plural(n, "ailment")} gone.` : `${h.name} prays, but nothing lay on the party.`);
        break;
      }
      case "rally": {
        let n = 0;
        for (const p of this.alive()) { p.hp = Math.min(p.max, p.hp + 6); n += this.cure(p, CM.CURABLE).length; }
        this.sound("heal");
        this.say(`${h.name} rallies the party: a little mended${n ? `, and ${CM.plural(n, "ailment")} shaken off` : ""}.`);
        break;
      }
      case "regrowth": healAll(this.pow((6 + 2 * L + Math.floor(mod / 2)) * (this.reagent === "rootsap" ? 2 : 1)), `${h.name} calls green growth through the party: everyone mends.`); break;
      case "bless": c.bless = true; if (CM.trait(h, "consecrate")) c.protect = true; this.say(`${h.name} blesses the party: blows land harder and glance off, this fight${CM.trait(h, "consecrate") ? ", and every blow on the party does less" : ""}.`); break;
      case "protection": c.protect = true; this.say(`${h.name} prays for protection: every blow on the party does less, this fight.`); break;
      case "song": {
        this.song = CM.trait(h, "warsong") ? 2 : 1;
        this.songEpic = CM.trait(h, "epic") ? this.floor.number : 0;
        if (CM.trait(h, "anthem")) c.bless = true;
        for (const p of this.alive()) { p.hp = Math.min(p.max, p.hp + 4); if ((p.status || {}).sleep) delete p.status.sleep; }
        this.sound("heal");
        this.say(`${h.name} sings. Hearts lift: the party hits harder this fight, and hurts a little less.`);
        this.cheer(5);
        break;
      }
      case "turn": {
        const dmg = this.pow(10 + 4 * L + mod);
        let burned = 0, fled = 0;
        for (const m of foes) if (m.undead) { burned++; this.spellHit(m, CM.trait(h, "holyfire") ? dmg * 2 : dmg, "", "holy"); if (m.hp > 0 && !CM.unmoved(m) && (this.reagent === "gravesalt" || rnd.chance(0.4))) { m.fled = true; fled++; this.emit("fx", { kind: "die", foe: m }); } }
        if (CM.trait(h, "purifier")) for (const m of foes) if (!m.undead && m.hp > 0) this.spellHit(m, Math.ceil(dmg / 2), "The light scorches:", "holy");
        this.say(burned ? `${h.name} raises the holy symbol: the undead burn (${dmg})${fled ? `, and ${CM.plural(fled, "one")} flee` : ""}.` : `${h.name} raises the holy symbol, but nothing here is undead.`);
        break;
      }
      case "sanctuary": {
        let held = 0;
        for (const m of foes) if (!CM.unmoved(m) && rnd.chance(0.5)) { m.held = Math.max(m.held || 0, 1); held++; }
        this.say(`${h.name} prays for sanctuary: ${held ? CM.plural(held, "foe") + " can't bring themselves to strike" : "the foes press on regardless"}.`);
        break;
      }
      case "raise": {
        if (this.asc("ironbound")) { this.say("Ironbound: the fallen rise only at the temple. The prayer goes unanswered."); break; }
        ally.hp = CM.trait(h, "miracle") ? ally.max : Math.max(1, Math.floor(ally.max / 3));
        this.sound("heal");
        this.say(`${h.name} calls ${ally.name} back from the dark!`);
        break;
      }
      case "thorns": {
        const dmg = this.pow(6 + 3 * L + Math.floor(mod / 2));
        let held = 0;
        for (const m of foes) { this.spellHit(m, dmg); if (m.hp > 0 && !CM.unmoved(m) && rnd.chance(0.3 + mod * 0.02)) { m.held = Math.max(m.held || 0, 1); held++; } }
        for (const p of this.alive()) { p.hp = Math.min(p.max, p.hp + this.pow((3 + Math.floor(L / 2)) * (CM.trait(h, "deeproots") ? 3 : 1) * (this.reagent === "rootsap" ? 2 : 1))); if (CM.trait(h, "oldgrowth")) this.cure(p, ["poison"]); }
        this.say(`${h.name} calls thorns up through the stone: ${dmg} to every foe${held ? `, ${CM.plural(held, "foe")} held fast` : ""}; the party mends a little.`);
        break;
      }
      case "entangle": if (CM.unmoved(foe)) { this.say(`${h.name} calls roots up round ${CM.the(foe)}, and they snap.`); break; } foe.held = Math.max(foe.held || 0, 2); this.say(`${h.name} calls roots round the ${foe.name}: held fast for two rounds.`); break;
      case "mockery": foe.marked = true; if (CM.trait(h, "jeer")) foe.blind = Math.max(foe.blind || 0, 2); this.say(`${h.name} mocks the ${foe.name}, who takes it badly: a quarter more from every blow${CM.trait(h, "jeer") ? ", and it can't see straight for rage" : ""}.`); break;
      case "mark": foe.marked = true; this.say(`${h.name} marks the ${foe.name}: a quarter more from every blow.`); break;
      case "volley": {
        const first = this.foeAt(foe || null);
        this.strike(h, first, " with an arrow");
        const rest = this.living().filter((m) => m !== first);
        if (rest.length) this.strike(h, rnd.pick(rest), " with a second arrow");
        else if (first.hp > 0) this.strike(h, first, " with a second arrow");
        if (CM.trait(h, "rainofarrows")) { const third = this.living()[0]; if (third) this.strike(h, third, " with a third arrow"); }
        break;
      }
      case "aimed": this.strike(h, foe, " with an aimed arrow", { sure: true, mult: 1.5 }); break;
      case "guard": h.guarding = ally; ally.guardedBy = h; this.say(`${h.name} stands guard over ${ally.name}.`); break;
      case "taunt": c.taunter = h; c.tauntUntil = c.round + 1; this.say(`${h.name} roars a challenge: every foe turns their way!`); break;
      case "bash": if (this.strike(h, foe, " with the shield", { bash: true }) > 0 && foe.hp > 0 && !CM.unmoved(foe) && rnd.chance(0.5)) { foe.held = Math.max(foe.held || 0, 1); this.say(`${CM.The(foe)} reels.`); } break;
      case "trick": foe.blind = 3; if (CM.trait(h, "sand") && !CM.unmoved(foe)) foe.held = Math.max(foe.held || 0, 1); this.say(`${h.name} flings sand in the ${foe.name}'s eyes!${CM.trait(h, "sand") && !CM.unmoved(foe) ? " It stands there clawing at them." : ""}`); break;
      default: break;
    }
  },

  // a potion, an antidote, a feather, in the thick of it: {row, who}, or the first healing potion for whoever needs it most
  useItemInBattle(h, arg) {
    if (arg && typeof arg === "object" && arg.row !== undefined) {
      const item = this.bag[arg.row];
      if (item && (item.kind === "scroll" || item.kind === "wand")) return this.useMagicInBattle(h, arg.row, arg.who);
      if (item && item.kind === "bomb") {                                 // a firepot: fire on every foe
        const foes = this.living(), dmg = 25 + 3 * (this.floor ? this.floor.number : 1);
        this.bag.splice(arg.row, 1);
        this.sound("spell");
        this.emit("fx", { kind: "cast", id: "fire", hero: h, item: "bomb", foes });
        this.casting = h;
        for (const m of foes) this.spellHit(m, dmg, "", "fire");
        this.casting = null;
        this.say(`${h.name} hurls the firepot: it bursts over every foe, ${dmg} each.`);
        return true;
      }
      if (!item || !["heal", "mana", "antidote", "revive", "greaterheal"].includes(item.kind)) { this.say("Not now."); return false; }
      const who = arg.who !== undefined ? arg.who : this.party.indexOf(this.allyAt(null, item.kind === "revive"));
      if (who < 0) return false;
      const note = this.give(arg.row, who);
      if (note) { this.say(note); return false; }
      this.emit("fx", { kind: "potion", who, item: item.kind });
      return true;
    }
    return this.potionInBattle();
  },

  potionInBattle() {
    const potion = this.bag.find((i) => i.kind === "heal") || this.bag.find((i) => i.kind === "greaterheal");
    if (!potion) { this.say("No healing potions left!"); return false; }
    const target = this.alive().reduce((a, b) => (a.hp / a.max <= b.hp / b.max ? a : b));
    this.bag.splice(this.bag.indexOf(potion), 1);
    target.hp = Math.min(target.max, target.hp + Math.ceil(potion.power * (this.alive().some((h) => CM.trait(h, "overclock")) ? 1.5 : 1)));
    this.sound("heal");
    this.emit("fx", { kind: "potion", who: this.party.indexOf(target), item: "heal" });
    this.say(`${target.name} drinks a ${potion.name} (+${potion.power}).`);
    return true;
  },

  // between fights: a healing spell, a cure, Light - from whoever knows it
  castOutside(heroIndex, id, target) {
    this.logAct("castOutside", heroIndex, id, target === undefined ? null : target);
    const h = this.party[heroIndex];
    if (!h || h.hp <= 0 || !this.canAct(h) || this.mode === "combat") return false;
    const ok = this.useAbility(h, id, target);
    if (ok) this.saveRun();
    return ok;
  },

  wonFight() {
    const rnd = this.rnd;
    const slain = this.foes.filter((m) => !m.fled);
    this.count("kills", slain.length);
    for (const m of slain) this.noteFoe(m, "slain");
    if (this.bestiaryDirty) { CM.store.set("bestiary", this.bestiary); this.bestiaryDirty = false; }
    const xp = this.has("pilgrim") ? 0 : slain.reduce((s, m) => s + m.xp, 0);
    let gold = slain.reduce((s, m) => s + m.gold, 0);
    if (this.alive().some((h) => (h.boons || []).includes("scavenger"))) gold = Math.floor(gold * 1.25);
    if (this.alive().some((h) => CM.trait(h, "pickpocket"))) gold = Math.floor(gold * 1.1);
    if (this.asc("poorveins")) gold = Math.floor(gold * 0.8);
    if (this.alive().some((h) => CM.trait(h, "avenger")) && slain.some((m) => m.undead)) { const n = slain.filter((m) => m.undead).length * 5; for (const h of this.alive()) h.hp = Math.min(h.max, h.hp + n); this.say(`The unholy are laid low, and the party mends ${n}.`); }
    this.foughtTogether();
    gold = Math.floor(gold * (CM.DIFFICULTIES[this.difficulty] || CM.DIFFICULTIES.fair).gold);
    this.gold += gold;
    if (this.gold >= 2000) this.achieve("hoarder");
    if (slain.some((m) => m.name === "Minotaur of the Labyrinth")) this.achieve("labyrinth");
    const fought0 = this.floor.things[this.foeKey];
    if (fought0 && fought0.rivalsFight) {                                 // the rivals' best thing, and their purse, on top
      const rnd0 = new CM.Random(CM.hashSeed(`${this.seed}:rivals:${this.floor.number}`)), best = CM.affix(CM.makeItem(this.floor.number + 3, rnd0, rnd0.pick(["weapon", "armor", "helm"])), 99, rnd0);
      best.unknown = false; this.bag.push(best); gold += 30 * this.floor.number;
      this.achieve("rivals");
      this.say(`The rivals are beaten, and the one in front yields: their purse, and ${best.name} (${CM.itemLabel(best)}).`);
    }
    const loot = rnd.chance(0.45) ? [CM.affix(CM.makeItem(this.floor.number, rnd), this.floor.number, rnd)] : [];
    const band = CM.themeIndex(this.floor.number), ing = Object.keys(CM.INGREDIENTS).find((id) => CM.INGREDIENTS[id].band === band);
    if (ing && rnd.chance(0.3)) loot.push(CM.ingredient(ing));           // (what the alchemist wants: the band's own stuff)
    this.bag.push(...loot);
    for (const h of this.party) if (h.oil && h.oil.fights > 0) { h.oil.fights -= 1; if (!h.oil.fights) { this.say(`The oil on ${h.name}'s weapon has worn off.`); h.oil = null; } }
    const boss = this.foes.some((m) => m.boss), guardian = this.foes.find((m) => m.guardian), fought = this.floor.things[this.foeKey];
    if (fought && fought.vengeance) { this.floor.avenged = (this.floor.avenged || []).concat(fought.vengeance); this.say("Somewhere on this floor, something lets out a long breath it has held a long time."); }
    delete this.floor.things[this.foeKey];
    if (guardian) this.floor.things[this.foeKey] = { type: "ladder" };   // (the shaft it stood over)
    this.combat = null;
    this.sound("coin");
    this.cheer(guardian ? 10 : 3);
    this.say(`Victory! ${xp} experience and ${gold} gold` + (loot.length ? `, and ${loot.map((i) => (i.kind === "ingredient" ? "some " : "a ") + (i.unknown ? CM.baseName(i) + " (unknown)" : i.name)).join(" and ")}.` : "."));
    for (const hero of this.alive()) {
      hero.xp += Math.floor(xp / 2);                                      // everyone standing learns from the fight
      while (hero.xp >= CM.xpForLevel(hero.level + 1)) {
        hero.level += 1;
        CM.upgradeHero(hero);
        CM.recompute(hero);
        hero.hp = hero.max;
        hero.mp = hero.maxmp;
        hero.pending += 1;
        this.sound("level");
        this.emit("fx", { kind: "levelup", hero });
        this.say(`${hero.name} reaches level ${hero.level}! A boon is theirs to choose (press ${this.party.indexOf(hero) + 1}).`);
      }
    }
    if (guardian) {
      this.slayGuardian(guardian);
      if (!this.fightFell) this.achieve("untouched");
      if (CM.GUARDIANS[guardian.guardian].final && !this.endless && !guardian.echo) { this.bottom = true; this.endRun(true); return; }
    }
    if (boss) { this.crown(); return; }
    this.setMode("explore");
    this.saveRun();
  },
});
}

// ---- Auto (A): the party fights on by itself with a sensible hand - heal under a third, a crowd gets the fireball,
// the weakest foe gets the blows - until the fight ends or someone is badly hurt; and the numbers a player would want
// before choosing: how likely a blow is to land, what a spell is likely to do ----
{
Object.assign(CM.Game.prototype, {
  autoFight(on = true) {
    if (!this.combat || this.mode !== "combat") return false;
    this.logAct("autoFight", on ? 1 : 0);
    this.combat.auto = on;
    if (on) this.say("The party fights on by itself. (Any key takes the reins back.)");
    this.emit("change");
    return true;
  },
  // the waiting hero's turn, by the simple hand; false when there is no turn to take (or Auto has stopped itself)
  autoTurn() {
    const c = this.combat, h = c && c.waiting;
    if (!h || this.mode !== "combat") return false;
    this.logAct("autoTurn");
    this.inAuto = true;
    try { return this.autoTurn2(); } finally { this.inAuto = false; }
  },
  autoTurn2() {
    const c = this.combat, h = c && c.waiting;
    if (c.auto && this.alive().some((p) => p.hp < p.max * 0.5)) { c.auto = false; this.say("Someone is badly hurt: Auto stops, and waits for orders."); this.emit("change"); return false; }
    const hurt = this.alive().filter((p) => p.hp < p.max / 3), foes = this.attackable();
    const can = CM.abilitiesFor(h).filter((id) => CM.ABILITIES[id].mp <= h.mp && !(CM.ABILITIES[id].once && h.used && h.used[id]));
    let done = false;
    if (hurt.length && can.includes("heal")) done = this.act("cast", { id: "heal", target: this.party.indexOf(hurt[0]) });
    else if (hurt.length && can.includes("lay")) done = this.act("cast", { id: "lay", target: this.party.indexOf(hurt[0]) });
    else if (hurt.length && hurt.includes(h) && this.bag.some((i) => i.kind === "heal")) done = this.act("item", null);
    else if (foes.length >= 3 && can.includes("fireball")) done = this.act("cast", { id: "fireball" });
    else if (foes.length >= 2 && can.includes("thorns")) done = this.act("cast", { id: "thorns" });
    else if (can.includes("song") && !this.song) done = this.act("cast", { id: "song" });
    else if (can.includes("volley") && foes.length >= 2) done = this.act("cast", { id: "volley" });
    if (!done && foes.length) {
      const bow = Boolean(h.weapon && h.weapon.props && h.weapon.props.bow), front = foes.filter((m) => m.row !== "back" && !m.hidden);
      const pool = !bow && front.length ? front : foes;                   // (a blow from the front reaches past the front for half: the front first)
      const weakest = pool.reduce((a, b) => (a.hp <= b.hp ? a : b), pool[0]);
      done = this.act("fight", weakest);
    }
    if (!done) done = this.act("defend");
    return done;
  },
  // what a hero's blow on a foe is likely to come to: {hit, low, high}
  strikeEstimate(h, foe) {
    if (!h || !foe) return null;
    const atk = this.effective(h).atk + (h.weapon ? h.weapon.power : 0), base = atk - Math.floor(foe.df / 2);
    let mult = 1;
    if (h.cls === "Rogue" && h.row === "back") mult = 2;
    else if (h.row === "back" && h.cls !== "Ranger") mult = 0.5;
    const bow = Boolean(h.weapon && h.weapon.props && h.weapon.props.bow), sure = (bow && CM.trait(h, "truearrow")) || (CM.trait(h, "ambush") && !h.struck);
    return { hit: sure ? 1 : this.hitChance(h), low: Math.max(1, Math.ceil(base * mult)), high: Math.max(1, Math.ceil((base + Math.max(1, Math.floor(atk / 2))) * mult)) };
  },
  // what a spell is likely to do, in a few words (the formulas of doAbility, read the other way)
  spellEstimate(h, id) {
    const L = h.level, mod = this.spellMod(h), m = (n) => Math.max(1, n);
    const dmg = { missile: 6 + 2 * L + mod, firebolt: 10 + 3 * L + mod, lightning: 20 + 5 * L + mod, calllightning: 18 + 4 * L + mod, smite: 12 + 3 * L + Math.floor(mod / 2),
      fireball: 8 + 4 * L + mod, frost: 6 + 2 * L + mod, turn: 10 + 4 * L + mod, thorns: 6 + 3 * L + Math.floor(mod / 2) }[id];
    const heal = { heal: 12 + 4 * L + mod, mend: 10 + 3 * L + mod, lay: 8 + 3 * L + Math.floor(mod / 2), regrowth: 6 + 2 * L + Math.floor(mod / 2) }[id];
    if (dmg !== undefined) {
      let n = m(dmg);
      if (id === "firebolt" || id === "fireball") { if (CM.trait(h, "firebrand")) n = Math.ceil(n * 1.5); }
      if (id === "smite") return `${n} (${n * 2} to the undead)`;
      if (id === "turn") return `${n} to each undead foe`;
      if (["fireball", "frost", "thorns"].includes(id)) return `${n} to every foe`;
      if (id === "calllightning") return CM.trait(h, "stormcall") ? `${n}, and ${Math.ceil(n * 0.6)} to the rest` : `${n}`;
      return `${n}`;
    }
    if (heal !== undefined) {
      let n = m(heal);
      if (id === "heal" && CM.trait(h, "blessedhands")) n = Math.ceil(n * 1.5);
      if (id === "lay" && CM.trait(h, "gentlehands")) n = Math.ceil(n * 1.5);
      return id === "regrowth" ? `mends everyone ${n}` : `mends ${n}`;
    }
    return "";
  },
});
}

// ---- the new callings' engines, the Monk's sway, and the bonds between heroes who have fought together ----
{
Object.assign(CM.Game.prototype, {
  // how much likelier a foe is to miss this hero: 1 for most, less for a Monk (and a Drunken Master)
  dodgeOf(h) {
    if (!h || h.thrall) return 1;
    if (h.cls !== "Monk") return 1;
    return CM.trait(h, "untouchable") ? 0.5 : CM.trait(h, "sway") ? 0.67 : 0.75;
  },
  // the round's end: the turret shoots, the thrall strikes
  enginesAct() {
    const c = this.combat;
    if (!c || this.mode !== "combat") return;
    const foes = this.living();
    if (c.turret && c.turret.by.hp > 0 && foes.length) {
      const t = c.turret, by = t.by, scatter = CM.trait(by, "scatter"), el = CM.trait(by, "bombard") ? "fire" : null;
      this.emit("fx", { kind: "cast", id: "firebolt", hero: by, foe: foes[0], foes });
      if (scatter) for (const m of foes) this.spellHit(m, Math.max(1, Math.ceil(t.dmg / 2)), "The turret's scattershot:", el);
      else this.spellHit(this.rnd.pick(foes), t.dmg, "The turret fires:", el);
      if (CM.trait(by, "medicengine")) { const hurt = this.alive().reduce((a, b) => (a.hp / a.max <= b.hp / b.max ? a : b)); const n = 5 + by.level; hurt.hp = Math.min(hurt.max, hurt.hp + n); this.say(`The turret's second arm binds ${hurt.name}'s wounds (+${n}).`); }
    }
    if (c.thrall && c.thrall.hp > 0 && this.living().length) {
      const blows = CM.trait(c.thrall.by, "twinthrall") ? 2 : 1;
      for (let i = 0; i < blows; i++) { const foe = this.living()[0]; if (!foe) break; this.spellHit(foe, Math.max(1, c.thrall.atk + this.rnd.int(0, 4)), "The thrall claws:"); }
    }
  },
  // the hero this one is bound to, if any (CM.BOND_FIGHTS fights together)
  bondOf(h) {
    for (const b of this.bonds || []) { if (b[0] === h.name) return this.party.find((p) => p.name === b[1]) || null; if (b[1] === h.name) return this.party.find((p) => p.name === b[0]) || null; }
    return null;
  },
  // a fight won together is counted for every pair standing; at CM.BOND_FIGHTS a bond forms, and stays
  foughtTogether() {
    const up = this.alive();
    this.pairFights = this.pairFights || {};
    for (let i = 0; i < up.length; i++) for (let j = i + 1; j < up.length; j++) {
      const k = [up[i].name, up[j].name].sort().join("|");
      this.pairFights[k] = (this.pairFights[k] || 0) + 1;
      if (this.pairFights[k] === CM.BOND_FIGHTS && !(this.bonds || []).some((b) => b.join("|") === k) && !this.bondOf(up[i]) && !this.bondOf(up[j])) {
        this.bonds = (this.bonds || []).concat([k.split("|")]);
        this.say(`${up[i].name} and ${up[j].name} have fought ${CM.BOND_FIGHTS} fights side by side: old friends now. Each is a little stronger for the other, mends the other better, and avenges the other's fall.`);
        this.sound("level");
        this.cheer(10);
        this.achieve("bonded");
      }
    }
    this.applyBonds();
  },
  applyBonds() {
    for (const h of this.party) { h.bondAtk = 0; h.bondDf = 0; }
    for (const [a, b] of this.bonds || []) for (const h of this.party) if (h.name === a || h.name === b) { h.bondAtk = 1; h.bondDf = 1; }
    for (const h of this.party) { const ratio = h.hp / Math.max(1, h.max); CM.recompute(h); h.hp = Math.max(0, Math.min(h.max, Math.round(h.max * ratio))); }
  },
});
}

