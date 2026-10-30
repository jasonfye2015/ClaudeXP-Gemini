"use strict";
// The dungeon screen: the party and the log, the actions, the automap, the HUD over the view, and what the window itself shows of an event.
Object.assign(CM.UI.prototype, {
  // ---- the dungeon screen ----
  refresh() {
    const g = this.game;
    if (this.screen === "title") { this.refreshTitle(); return; }
    if (this.screen !== "play") return;
    const fl = g.floor;
    if (fl) {
      this.$("#view .compass").textContent = `${CM.DIR_NAMES[fl.facing]}   -   ${fl.wing !== undefined ? fl.wingName.charAt(0).toUpperCase() + fl.wingName.slice(1) : fl.number === 0 ? "The town" : "Floor " + fl.number}`;
      this.$("#side .where").textContent = fl.wing !== undefined ? `${fl.wingName.charAt(0).toUpperCase() + fl.wingName.slice(1)} - beside floor ${Math.floor(fl.number)}` : fl.number === 0 ? `${CM.TOWN_THEME.name} - the town` : `${CM.themeFor(fl.number).name} - floor ${fl.number}`;
    }
    this.$("#side .purse").textContent = `Gold: ${g.gold.toLocaleString()}   Potions: ${g.potionCount()}`;
    const light = this.$("#side .light"), l = g.light || {};
    let lit = l.kind === "lantern" ? (l.left > 60 ? `Lantern: ${l.left} steps of oil` : `Lantern burning low: ${l.left}`) : l.kind === "glow" ? "Glow stone: a cold light that lasts" : l.kind === "torch" ? (l.left > 40 ? `Torch: ${l.left} steps left` : `Torch burning low: ${l.left}`) : "No light!";
    if (g.spellLight > 0) lit += ` - conjured light: ${g.spellLight} steps`;
    if (fl && g.inDark()) lit += " - a magical dark";
    light.textContent = lit;
    light.classList.toggle("dark", !g.hasLight() || g.inDark());
    this.renderBelt();
    const temper = this.$("#side .temper"), hungry = g.hungerWord();
    temper.textContent = `The party: ${g.moraleWord()}${hungry ? ", " + hungry.toLowerCase() : ""}${g.weightWord ? (g.weightWord() ? ", " + g.weightWord().toLowerCase() : "") : ""}${g.blessed && g.blessed() ? ", " + CM.t("hud.blessed") : ""}${g.autoOn() ? ", " + CM.t("hud.automatic") : ""}`;
    temper.title = CM.MORALE.what + " " + CM.HUNGER.what;
    temper.classList.toggle("low", (g.morale === undefined ? 70 : g.morale) <= 30 || hungry === "Weary");
    const hint = this.$("#view .hint");
    if (g.mode === "camp") hint.textContent = "A merchant's camp. Rest, trade, see to the fallen - then go deeper, or back up.";
    else if (g.mode === "combat") hint.textContent = "";
    else if (g.travel) hint.textContent = g.travel.explore ? "Exploring... (any key stops)" : "Walking... (any key stops)";
    else if (fl) {
      const k = `${fl.pos[0]},${fl.pos[1]}`, thing = fl.things[k], f = fl.features[k];
      const [dx, dy] = CM.DIRS[fl.facing], ahead = fl.features[`${fl.pos[0] + dx},${fl.pos[1] + dy}`];
      let text = "";
      if (f && f.type === "lever" && f.face === fl.facing) text = f.pulled ? "The lever, pulled." : "A lever on the wall. Space pulls it.";
      else if (f && f.type === "carving" && f.face === fl.facing) text = "Runes carved into the wall. Space reads them.";
      else if (thing) text = { chest: "A chest. Space opens it.", ladder: "A ladder down. Space climbs it.", stairs_up: "The stairs up. Space climbs them.",
        phylactery: "A cold box with a slow beat inside it. Space smashes it.", ghost: "A ghost. Space speaks to it.", hermit: "A hermit. Space speaks to him.",
        adventurer: "Someone bound. Space cuts them loose.", rope: "A rope from above. Space climbs it.", event: `${(CM.EVENTS[thing.event] || {}).title || "Something strange"}. Space looks closer.`,
        strongbox: thing.opened ? "An empty strongbox." : "A strongbox. Space tries the key.", peddler: "A peddler. Space sees his wares.", rivals: "A rival party. Space speaks to them.",
        wingstair: "A second stair, down into a wing. Space takes it.", wingexit: "A stair down to the main way. Space takes it.", wingstair_up: "The wing stair, up. Space climbs it." }[thing.type] || "";
      else if (f && f.type === "plate" && (f.gate || f.known)) text = f.gate ? (f.pressed ? "A pressure plate, sunk." : "A pressure plate.") : "A plate that was a trap.";
      else if (f && f.type === "spores" && f.known) text = "A hanging cloud of spores.";
      else if (f && f.type === "vents" && f.known) text = "A vent in the floor. It breathes fire on a beat.";
      else if (f && f.type === "bonepiles" && f.known) text = "A heap of bones, higher than a man.";
      else if (f && f.type === "fountain") text = f.used ? "A dry fountain." : "A fountain. Space drinks.";
      else if (f && f.type === "altar") text = f.used ? "A quiet altar." : "An altar. Space kneels.";
      else if (ahead && ahead.type === "door" && !ahead.open) text = ahead.riddle !== undefined ? "A door written over with runes. Walk into it, and answer." : ahead.barred ? "A door you barred. Walk into it to lift the bar." : ahead.locked ? `A locked door${ahead.grade ? ` (${CM.LOCKS[ahead.grade].name})` : ""}. Walk into it with a key, a Rogue, or a lockpick.` : "A door. Walk into it to open it.";
      else if (ahead && ahead.type === "gate" && !ahead.open) text = "A portcullis. Find its lever.";
      hint.textContent = text;
    }
    this.renderParty();
    this.renderLog();
    this.renderActions();
    if (this.$("#dlg-sheet").classList.contains("on")) this.renderSheet();
    this.drawAutomap(this.$("#automap"));
    if (this.$("#bigmap").classList.contains("on")) this.drawAutomap(this.$("#bigmap-canvas"));
  },

  renderParty() {
    const box = this.$("#party");
    const signature = this.game.party.map((m) => m.cls + m.name).join("|");
    if (box.dataset.signature !== signature) {
      box.innerHTML = "";
      box.dataset.signature = signature;
      this.game.party.forEach((m, i) => {
        const div = document.createElement("div");
        div.className = "member";
        div.title = `${m.name}'s sheet (${i + 1})`;
        div.appendChild(this.portrait(m.cls, 44));
        const text = document.createElement("div");
        text.innerHTML = `<div class="name"></div><div class="gear"></div><div class="bar hp"><i></i><span></span></div><div class="bar mp"><i></i><span></span></div><div class="ail"></div>`;
        div.appendChild(text);
        div.addEventListener("click", () => this.openSheet(i));
        box.appendChild(div);
      });
    }
    this.game.party.forEach((m, i) => {
      const div = box.children[i], dead = m.hp <= 0, st = m.status || {};
      div.classList.toggle("fallen", dead);
      div.classList.toggle("front", m.row === "front");
      div.querySelector(".name").innerHTML = `${this.esc(m.name)} <small>${m.cls} ${m.level}${m.row === "front" ? " ▴" : ""}</small>` + (dead ? " <i>(fallen)</i>" : "")
        + (m.pending ? ` <span class="boon-badge">Boon!</span>` : "") + (CM.needsPath(m) ? ` <span class="boon-badge">Path!</span>` : "");
      div.querySelector(".gear").textContent = `${m.weapon.name} / ${m.armor.name}`;
      const ail = div.querySelector(".ail");
      ail.textContent = Object.keys(st).map((s) => `${CM.STATUSES[s].mark} ${CM.STATUSES[s].name}`).join("  ");
      ail.style.display = Object.keys(st).length ? "" : "none";
      const hp = div.querySelector(".bar.hp");
      hp.querySelector("i").style.width = `${100 * Math.max(0, m.hp) / Math.max(1, m.max)}%`;
      hp.querySelector("span").textContent = `HP ${Math.max(0, m.hp)}/${m.max}`;
      const mp = div.querySelector(".bar.mp");
      mp.style.display = m.maxmp ? "" : "none";
      mp.querySelector("i").style.width = `${100 * Math.max(0, m.mp) / Math.max(1, m.maxmp)}%`;
      mp.querySelector("span").textContent = `MP ${m.mp}/${m.maxmp}`;
    });
  },

  renderLog() {
    const log = this.$("#log");
    const lines = this.game.messages.slice(-7);
    log.innerHTML = lines.map((l) => `<div>${this.esc(l)}</div>`).join("");
  },

  renderActions() {
    const g = this.game, box = this.$("#actions");
    if (g.mode === "combat") { this.renderCombat(); return; }
    box.classList.remove("combat");
    const sets = {
      explore: [["◄ Turn", () => g.turn(-1)], ["▲ Forward", () => g.move(0)], ["▼ Back", () => g.move(2)], ["Turn ►", () => g.turn(1)],
        ["Use (Space)", () => g.use()], ["Explore (X)", () => (g.travel ? g.stopTravel() : g.explore())], [g.autoOn() ? "Automatic: on (Z)" : "Automatic (Z)", () => g.autoPlay()], ["Cast (C)", () => this.outsideCast()], ["Inventory (I)", () => g.openBag()], ["Journal (J)", () => this.openJournal()], ["Map (Tab)", () => this.toggleBigMap()],
        ["Menu (Esc)", () => this.openDialog("#dlg-pause")]],
      camp: [["Merchant", () => g.openBag(true)], ["Rest (20 gold)", () => g.rest()], ["Temple", () => this.openDialog("#dlg-temple")], [CM.t("camp.bounty"), () => { const note = g.bounty ? (g.bountyDone() ? g.claimBounty() : g.takeBounty()) : g.takeBounty(); if (note) g.say(note); this.refresh(); }],
        ["Tavern", () => this.openTavern()], ["Smith", () => this.openSmith()], ["Alchemist", () => this.openAlchemist()], ["Vault", () => this.openVault()], ["Waystone", () => this.openWaystone()], ["Guild", () => this.openSecond()], ["Cast (C)", () => this.outsideCast()], ["Inventory", () => g.openBag()], ["Journal (J)", () => this.openJournal()],
        ["Back up the shaft", () => g.backUp()], ["Back to town", () => { const note = g.goHome(); if (note) g.say(note); }], ["Go deeper", () => g.leaveCamp()], [g.autoOn() ? "Automatic: on (Z)" : "Automatic (Z)", () => g.autoPlay()], ["Menu (Esc)", () => this.openDialog("#dlg-pause")]],
    };
    const key = g.mode + ":" + (this.xmenu ? this.xmenu.kind + ":" + (this.xmenu.id || "") + ":" + (this.xmenu.hero === undefined ? "" : this.xmenu.hero) : "");
    if (box.dataset.mode === key) return;
    box.innerHTML = "";
    box.dataset.mode = key;
    const btn = (html, fn, disabled, cls) => {
      const b = document.createElement("button");
      b.innerHTML = html;
      b.disabled = Boolean(disabled);
      if (cls) b.className = cls;
      b.addEventListener("click", fn);
      box.appendChild(b);
      return b;
    };
    if (this.xmenu && this.xmenu.kind === "list") {                       // between fights: who casts what
      const choices = this.outsideChoices();
      choices.forEach((ch, i) => {
        const b = btn(`<kbd>${i + 1}</kbd>${this.esc(ch.hero.name)}: ${CM.ABILITIES[ch.id].name}<small>${CM.ABILITIES[ch.id].mp} MP - ${CM.ABILITIES[ch.id].what}</small>`,
          () => this.outsidePick(ch), false, "pick");
        const ic = CM.art.spellIcon(ch.id, 18, g.settings.look);
        if (ic) { ic.className = "icon"; b.insertBefore(ic, b.firstChild.nextSibling); }
      });
      if (!choices.length) { const none = document.createElement("span"); none.className = "small"; none.textContent = "No one has a spell for outside a fight, or the magic for it."; box.appendChild(none); }
      btn("<kbd>Esc</kbd>Back", () => this.closeMenu());
      return;
    }
    if (this.xmenu && this.xmenu.kind === "ally") {
      g.party.forEach((p, i) => btn(`<kbd>${i + 1}</kbd>${this.esc(p.name)}<small>${p.hp <= 0 ? "fallen" : `${p.hp}/${p.max}`}</small>`,
        () => this.outsideAlly(i), this.xmenu.fallen ? p.hp > 0 : p.hp <= 0, "pick"));
      btn("<kbd>Esc</kbd>Back", () => this.closeMenu());
      return;
    }
    for (const [text, slot] of sets[g.mode] || []) btn(text, slot);
  },

  // ---- between fights: healing, cures and Light, from whoever knows them ----
  outsideChoices() {
    const out = [];
    this.game.party.forEach((hero, hi) => {
      if (hero.hp <= 0 || !this.game.canAct(hero)) return;
      for (const id of CM.abilitiesFor(hero)) {
        const a = CM.ABILITIES[id];
        if (a.outside && hero.mp >= a.mp) out.push({ hero, hi, id });
      }
    });
    return out;
  },
  outsideCast() { this.xmenu = { kind: "list" }; this.refresh(); },
  outsidePick(ch) {
    const a = CM.ABILITIES[ch.id];
    if (a.target === "ally" || a.target === "fallen") { this.xmenu = { kind: "ally", id: ch.id, hero: ch.hi, fallen: a.target === "fallen" }; this.refresh(); return; }
    this.game.castOutside(ch.hi, ch.id, null);
    this.closeMenu();
  },
  outsideAlly(i) { const m = this.xmenu; this.game.castOutside(m.hero, m.id, i); this.closeMenu(); },
  closeMenu() { this.xmenu = null; this.refresh(); },
  pickOutside(n) {
    const buttons = [...this.$("#actions").querySelectorAll("button.pick")], b = buttons[n - 1];
    if (b && !b.disabled) { b.click(); return true; }
    return false;
  },

  toggleBigMap() {
    const d = this.$("#bigmap");
    if (d.classList.contains("on")) this.closeDialogs();
    else { this.openDialog("#bigmap"); this.drawAutomap(this.$("#bigmap-canvas")); }
  },

  drawAutomap(canvas) {
    const fl = this.game.floor;
    if (!fl) return;
    const p = canvas.getContext("2d"), W = canvas.width, size = fl.grid.length, cell = W / size;
    p.fillStyle = "#E8DCC0";                                              // graph paper
    p.fillRect(0, 0, W, W);
    p.strokeStyle = "#C8B898"; p.lineWidth = 1;
    p.beginPath();
    for (let i = 0; i <= size; i++) { p.moveTo(i * cell, 0); p.lineTo(i * cell, W); p.moveTo(0, i * cell); p.lineTo(W, i * cell); }
    p.stroke();
    const colours = { chest: "#C08030", ladder: "#3060C0", monsters: "#C03030", boss: "#8030C0", guardian: "#A02050", key: "#D8B040",
      node: "#8FB06A", building: "#C09050", well: "#60A0E0", ghost: "#A0C8E8", hermit: "#C8A060", adventurer: "#E8C890", bones: "#D8D0B8", rope: "#B08040", event: "#D070E0", strongbox: "#806020", boxkey: "#E0A020", peddler: "#60B0A0", rivals: "#E06040", wingstair: "#2090A0", wingexit: "#3060C0", wingstair_up: "#2090A0" };
    const dark = new Set(fl.dark);
    for (const [x, y] of fl.seen) {
      const k = `${x},${y}`, f = fl.features[k], wall = fl.grid[y][x] && !(f && f.type === "secret" && f.found);
      p.fillStyle = wall ? "#3A3028" : dark.has(k) ? "#8A8070" : "#F8F0DC";
      p.fillRect(x * cell, y * cell, cell, cell);
      const cx = (x + 0.5) * cell, cy = (y + 0.5) * cell;
      if (f && !wall) this.drawFeature(p, f, x, y, cell, fl);
      const thing = fl.things[k];
      if (thing && !wall) {
        p.fillStyle = colours[thing.type] || (thing.type === "phylactery" ? "#60D0FF" : "#808080");
        if (thing.type === "stairs_up") { p.beginPath(); p.moveTo(cx, cy - cell * 0.35); p.lineTo(cx + cell * 0.35, cy + cell * 0.3); p.lineTo(cx - cell * 0.35, cy + cell * 0.3); p.fill(); }
        else if (thing.type === "ladder" || thing.type === "wingexit" || thing.type === "wingstair") p.fillRect(cx - cell * 0.3, cy - cell * 0.3, cell * 0.6, cell * 0.6);
        else { p.beginPath(); p.arc(cx, cy, cell * (thing.type === "key" ? 0.2 : 0.3), 0, Math.PI * 2); p.fill(); }
      }
    }
    for (const [k, text] of Object.entries(fl.notes || {})) {                   // the player's own marks
      const [nx, ny] = k.split(",").map(Number), ncx = (nx + 0.5) * cell, ncy = (ny + 0.5) * cell;
      p.fillStyle = "#C02060";
      p.beginPath(); p.moveTo(ncx - cell * 0.3, ncy + cell * 0.4); p.lineTo(ncx - cell * 0.3, ncy - cell * 0.4); p.lineTo(ncx + cell * 0.35, ncy - cell * 0.2); p.lineTo(ncx - cell * 0.3, ncy); p.fill();
      if (cell >= 16) {                                                             // (the words beside the flag - to its left near the right edge)
        const left = ncx < W * 0.7, tx = left ? ncx + cell * 0.45 : ncx - cell * 0.4;
        p.font = `bold ${Math.max(9, cell * 0.5)}px Georgia`; p.textAlign = left ? "left" : "right";
        p.fillStyle = "#000"; p.fillText(text, tx, ncy + cell * 0.2); p.fillStyle = "#C02060"; p.fillText(text, tx - 1, ncy + cell * 0.2 - 1);
      }
    }
    if (this.game.travel && this.game.travel.to) {                                  // where the party is walking to
      const [tx, ty] = this.game.travel.to;
      p.strokeStyle = "#20A040"; p.lineWidth = Math.max(1.5, cell * 0.12); p.strokeRect(tx * cell + 1, ty * cell + 1, cell - 2, cell - 2);
    }
    const [x, y] = fl.pos, [dx, dy] = CM.DIRS[fl.facing], cx = (x + 0.5) * cell, cy = (y + 0.5) * cell;
    p.fillStyle = "#20A040";
    p.beginPath();
    p.moveTo(cx + dx * cell * 0.45, cy + dy * cell * 0.45);
    p.lineTo(cx - dy * cell * 0.35 - dx * cell * 0.3, cy + dx * cell * 0.35 - dy * cell * 0.3);
    p.lineTo(cx + dy * cell * 0.35 - dx * cell * 0.3, cy - dx * cell * 0.35 - dy * cell * 0.3);
    p.fill();
  },

  // the dungeon's furniture on the automap, once seen (a trapdoor, a spinner or a teleporter only once it has had you)
  drawFeature(p, f, x, y, cell, fl) {
    const cx = (x + 0.5) * cell, cy = (y + 0.5) * cell, ns = fl.grid[y - 1] && fl.grid[y - 1][x] === 0 && fl.grid[y + 1] && fl.grid[y + 1][x] === 0;
    p.lineWidth = Math.max(1.5, cell * 0.16);
    if (f.type === "door" || f.type === "gate" || (f.type === "secret" && f.found)) {
      p.strokeStyle = f.type === "gate" ? "#607080" : f.locked ? "#D8B040" : f.type === "secret" ? "#A070C0" : f.riddle !== undefined && !f.open ? "#60C0E0" : "#8A5A2A";
      if (f.type === "gate" && !f.open) p.setLineDash([cell * 0.15, cell * 0.12]);
      if (f.type === "door" && f.open) p.setLineDash([cell * 0.25, cell * 0.25]);
      p.beginPath();
      if (ns) { p.moveTo(cx - cell * 0.42, cy); p.lineTo(cx + cell * 0.42, cy); } else { p.moveTo(cx, cy - cell * 0.42); p.lineTo(cx, cy + cell * 0.42); }
      p.stroke(); p.setLineDash([]);
    } else if (f.type === "pit" || (f.type === "trapdoor" && f.known)) {
      p.fillStyle = "#101010"; p.beginPath(); p.arc(cx, cy, cell * 0.32, 0, Math.PI * 2); p.fill();
    } else if (f.type === "plate" && (f.gate || f.known)) {
      p.strokeStyle = f.gate ? (f.pressed ? "#80A060" : "#E08030") : "#C03030"; p.lineWidth = Math.max(1.5, cell * 0.12); p.strokeRect(cx - cell * 0.26, cy - cell * 0.26, cell * 0.52, cell * 0.52);
    } else if (["spores", "vents", "bonepiles"].includes(f.type) && f.known) {
      p.fillStyle = f.type === "spores" ? "#A0C040" : f.type === "vents" ? "#E06020" : "#D8D0B8"; p.beginPath(); p.arc(cx, cy, cell * 0.22, 0, Math.PI * 2); p.fill();
    } else if (f.type === "teleporter" && f.known) {
      p.strokeStyle = "#8040E0"; p.lineWidth = Math.max(1.5, cell * 0.12); p.beginPath(); p.arc(cx, cy, cell * 0.3, 0, Math.PI * 2); p.stroke();
    } else if (f.type === "spinner" && f.known) {
      p.strokeStyle = "#606060"; p.lineWidth = Math.max(1.5, cell * 0.12); p.beginPath(); p.arc(cx, cy, cell * 0.28, 0.6, 5.4); p.stroke();
    } else if (f.type === "fountain") {
      p.fillStyle = f.used ? "#9098A0" : "#3090D0"; p.beginPath(); p.arc(cx, cy, cell * 0.26, 0, Math.PI * 2); p.fill();
    } else if (f.type === "altar") {
      p.fillStyle = "#E8E0C0"; p.fillRect(cx - cell * 0.08, cy - cell * 0.32, cell * 0.16, cell * 0.64); p.fillRect(cx - cell * 0.28, cy - cell * 0.12, cell * 0.56, cell * 0.16);
    } else if (f.type === "lever" || f.type === "carving") {
      const [dx, dy] = CM.DIRS[f.face];
      p.strokeStyle = f.type === "lever" ? (f.pulled ? "#80A060" : "#E08030") : "#8A6A3A";
      p.lineWidth = Math.max(2, cell * 0.2);
      p.beginPath();
      p.moveTo(cx + dx * cell * 0.4 - dy * cell * 0.3, cy + dy * cell * 0.4 - dx * cell * 0.3);
      p.lineTo(cx + dx * cell * 0.4 + dy * cell * 0.3, cy + dy * cell * 0.4 + dx * cell * 0.3);
      p.stroke();
    }
  },

  // the names and health of the foes, over the view, where they stand
  drawHud(foes, project) {
    const hud = this.$("#hud"), view = this.$("#view");
    const dpr = Math.min(2, window.devicePixelRatio || 1), w = view.clientWidth, h = view.clientHeight;
    if (hud.width !== Math.round(w * dpr) || hud.height !== Math.round(h * dpr)) { hud.width = Math.round(w * dpr); hud.height = Math.round(h * dpr); }
    const p = hud.getContext("2d");
    p.setTransform(dpr, 0, 0, dpr, 0, 0);
    p.clearRect(0, 0, w, h);
    this.lastHud = [];
    for (const f of foes) {
      const at = project(f.wx, f.wh, f.wz);
      if (!at) continue;
      const [sx, sy, depth] = at, bw = CM.clamp(120 / depth, 40, 110);
      this.lastHud.push({ sx, sy, index: f.index });
      p.fillStyle = "#401010"; p.fillRect(sx - bw / 2, sy - 8, bw, 6);
      p.fillStyle = "#E03030"; p.fillRect(sx - bw / 2, sy - 8, bw * Math.max(0, f.m.hp) / f.m.max, 6);
      const label = `${f.index !== undefined ? `[${f.index + 1}] ` : ""}${f.m.name}${f.m.asleep > 0 ? " z" : ""}`;
      p.font = `bold ${CM.clamp(26 / depth, 10, 14)}px Georgia`; p.textAlign = "center";
      p.fillStyle = "#000"; p.fillText(label, sx + 1, sy - 12);
      p.fillStyle = f.chosen ? "#F0C040" : "#fff"; p.fillText(label, sx, sy - 13);
      if (f.chosen) {                                                   // the one your blows are for
        p.strokeStyle = "#F0C040"; p.lineWidth = 2;
        p.beginPath(); p.moveTo(sx - bw / 2 - 6, sy - 30); p.lineTo(sx - bw / 2 - 6, sy + 4); p.moveTo(sx + bw / 2 + 6, sy - 30); p.lineTo(sx + bw / 2 + 6, sy + 4); p.stroke();
      }
    }
  },

  // what the window itself shows of an event: the red flash and a jolted card for a blow, a glow for a mending
  fx(fx) {
    const g = this.game, hold = CM.fx ? Math.max(0, CM.fx.holdUntil - performance.now()) : 0;
    const later = (fn) => (hold > 0 ? setTimeout(fn, hold) : fn());                   // (while a bolt is in flight, the blow waits for it)
    if (fx.kind === "hurt") later(() => { this.flash(".hurt", 60); this.cardFx(g.party.indexOf(fx.hero), "jolt", 500); });
    else if (fx.kind === "levelup") this.cardFx(g.party.indexOf(fx.hero), "glow-gold", 1200);
    else if (fx.kind === "sear") this.cardFx(g.party.indexOf(fx.hero), "jolt", 400);
    else if (fx.kind === "relic") g.party.forEach((h, i) => { if (h.hp > 0) this.cardFx(i, "glow-gold", 1400); });
    else if (fx.kind === "potion") this.cardFx(fx.who, fx.item === "mana" ? "glow-blue" : fx.item === "revive" ? "glow-gold" : "glow-green", 900);
    else if (fx.kind === "cast") {
      const heals = ["heal", "mend", "lay", "cure", "lift", "regrowth", "raise", "healing"], wards = ["bless", "protection", "sanctuary", "song", "rally", "guard", "taunt"];
      if (heals.includes(fx.id)) {
        if (fx.ally) this.cardFx(g.party.indexOf(fx.ally), "glow-green", 900);
        else g.party.forEach((h, i) => { if (h.hp > 0) this.cardFx(i, "glow-green", 900); });
      } else if (wards.includes(fx.id)) {
        const who = fx.ally ? [g.party.indexOf(fx.ally)] : fx.id === "taunt" ? [g.party.indexOf(fx.hero)] : g.party.map((h, i) => i);
        for (const i of who) this.cardFx(i, fx.id === "protection" || fx.id === "sanctuary" ? "glow-blue" : "glow-gold", 900);
      }
    }
  },

  // a guardian's name across the view, for a moment, as it rises
  // the belt: four slots under the automap; a click uses (the first hero standing), a right click puts it back in the pack
  renderBelt() {
    const g = this.game, box = this.$("#belt");
    if (!box) return;
    box.innerHTML = "";
    for (let i = 0; i < CM.BELT_SIZE; i++) {
      const it = (g.belt || [])[i], b = document.createElement("button");
      b.className = "slot" + (it ? "" : " empty");
      b.innerHTML = `<kbd>${i + 5}</kbd>${it ? this.esc(it.name) : "-"}`;
      b.title = it ? `${CM.itemCard(it)} Click to use; right-click to put back in the pack.` : "Empty: put something here from the pack (the Belt button beside each thing).";
      b.disabled = !it || g.mode === "title";
      b.addEventListener("click", () => { this.note && this.note(""); const note = g.useBelt(i); if (note) g.say(note); this.refresh(); });
      b.addEventListener("contextmenu", (e) => { e.preventDefault(); if (it) { g.fromBelt(i); this.refresh(); } });
      box.appendChild(b);
    }
  },
  titleCard(name, sub) {
    const el = this.$("#view .titlecard");
    el.querySelector("b").textContent = name;
    el.querySelector("small").textContent = sub || "";
    el.classList.remove("on");
    void el.offsetWidth;
    el.classList.add("on");
    clearTimeout(this.cardTimer);
    this.cardTimer = setTimeout(() => el.classList.remove("on"), 2600);
  },

  // a wash of colour over the view that fades (a spell's light, a trap's gas)
  tint(colour, ms = 260) {
    if (CM.reducedMotion) return;
    const el = this.$("#view .tint");
    clearTimeout(this.tintTimer);
    el.style.transition = "none"; el.style.background = colour; el.style.opacity = "1";
    this.tintTimer = setTimeout(() => { el.style.transition = `opacity ${ms}ms ease-out`; el.style.opacity = "0"; }, 40);
  },

  // a hero's card jolts or glows for a moment
  cardFx(i, cls, ms = 700) {
    const card = this.$("#party").children[i];
    if (!card || (CM.reducedMotion && cls === "jolt")) return;
    card.classList.remove(cls);
    void card.offsetWidth;                                               // (so the animation starts again)
    card.classList.add(cls);
    setTimeout(() => card.classList.remove(cls), ms);
  },

  floatText(x, y, text, cls = "") {
    const el = document.createElement("div");
    el.className = "float " + cls;
    el.textContent = text;
    el.style.left = `${x}px`; el.style.top = `${y}px`;
    this.$("#floats").appendChild(el);
    setTimeout(() => el.remove(), 950);
  },
});
