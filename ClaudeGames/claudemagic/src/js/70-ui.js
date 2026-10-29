"use strict";
// The window around the dungeon: the title (what you set out with, the Hall of Fame, settings), the party and the
// log under the view, the automap, the bag and the merchant, and the little dialogs. It listens to the Game and
// redraws; it never decides the rules.
CM.UI = class {
  constructor(game, root) {
    this.game = game;
    this.root = root;
    this.bagRow = -1; this.shopRow = -1;
    this.portraits = {};
    root.innerHTML = `
<div id="title" class="screen">
  <div class="backdrop-slot"></div><div class="shade"></div>
  <div class="sheet">
    <h1>Claude and Magic</h1>
    <div class="tagline">Twenty floors down, the Lich King waits. Four go in together.</div>
    <div class="note" id="title-note"></div>
    <div class="card" id="expedition">
      <h2>Expedition</h2>
      <div class="row"><button id="btn-continue" class="primary">Continue</button><span id="continue-note" class="small"></span></div>
      <div class="row"><button id="btn-new" class="primary">New Expedition</button><label for="seed">Seed</label><input id="seed" type="text" maxlength="40" spellcheck="false"><button id="btn-dice" title="Another seed">&#x2684;</button></div>
      <p>The same seed lays out the same twenty floors, so a dungeon can be tried again - or handed to a friend. What
      the monsters do in a fight is up to the dice. The run saves as you go; when the whole party falls, it ends, and
      the deepest runs go in the Hall of Fame.</p>
      <h2>Your party</h2>
      <div id="heroes"></div>
      <p id="start-with"></p>
    </div>
    <div class="card" id="fame"><h2>Hall of Fame</h2><table></table></div>
    <div class="foot"><button id="btn-settings">Settings</button><button id="btn-keys">Keys</button><button id="btn-transfer">Export / Import</button></div>
    <div class="version"></div>
  </div>
</div>
<div id="play" class="screen">
  <div class="top">
    <div id="view"><div class="canvas-slot"></div><canvas id="hud"></canvas><div class="vignette"></div><div class="compass"></div><div class="fps"></div><div class="hurt"></div><div id="floats"></div><div class="hint"></div></div>
    <div id="side"><canvas id="automap" width="290" height="290"></canvas><div class="where"></div><div class="purse"></div></div>
  </div>
  <div id="party"></div>
  <div id="log"></div>
  <div id="actions"></div>
</div>
<div id="bag" class="screen">
  <h2 id="bag-title"></h2>
  <div class="lists"><div class="list" id="bag-list"></div><div class="list" id="shop-list"></div></div>
  <div class="note" id="bag-note"></div>
  <div class="give" id="bag-give"></div>
  <div class="act"><button id="btn-buy">Buy</button><button id="btn-sell">Sell</button><button id="btn-bag-done" class="primary">Done</button></div>
</div>
<div class="dialog" id="dlg-settings"><div class="box"><h2>Settings</h2>
  <div class="row"><label for="set-sound">Sound</label><input type="checkbox" id="set-sound"></div>
  <div class="row"><label for="set-volume">Volume</label><input type="range" id="set-volume" min="0" max="100"></div>
  <div class="row"><label for="set-smooth">Smooth steps and turns (off: snap, the classic way)</label><input type="checkbox" id="set-smooth"></div>
  <div class="row"><label for="set-fps">Show frames per second (F3)</label><input type="checkbox" id="set-fps"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-keys"><div class="box"><h2>Keys</h2><table class="keys"></table><div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-transfer"><div class="box"><h2>Export / Import</h2>
  <p class="small">Your run, the Hall of Fame and your settings, as text. Copy it to keep it or to carry it to another
  browser; paste a copy here and Import to bring it back.</p>
  <textarea id="transfer-text" spellcheck="false"></textarea>
  <div class="small" id="transfer-note"></div>
  <div class="end"><button id="btn-copy">Copy</button><button id="btn-import">Import</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-pause"><div class="box"><h2>Paused</h2>
  <p class="small">The run is saved as you go.</p>
  <div class="end"><button id="btn-pause-settings">Settings</button><button id="btn-pause-title">Back to the title</button><button class="close primary">Carry on</button></div></div></div>
<div class="dialog" id="bigmap"><canvas id="bigmap-canvas" width="600" height="600"></canvas></div>`;
    this.$ = (sel) => root.querySelector(sel);
    this.canvas = document.createElement("canvas");                        // the one WebGL canvas, moved between screens
    this.canvas.id = "gl";
    this.attachCanvas("title");
    for (const b of root.querySelectorAll(".dialog .close")) b.addEventListener("click", () => this.closeDialogs());
    for (const d of root.querySelectorAll(".dialog")) d.addEventListener("click", (e) => { if (e.target === d) this.closeDialogs(); });
    this._title();
    this._bag();
    this._settings();
    this.$("#btn-pause-settings").addEventListener("click", () => { this.closeDialogs(); this.openDialog("#dlg-settings"); });
    this.$("#btn-pause-title").addEventListener("click", () => { this.closeDialogs(); game.saveRun(); game.setMode("title"); });
    const keys = this.$("#dlg-keys table");
    keys.innerHTML = CM.KEYS_HELP.map(([k, what]) => `<tr><td><kbd>${k}</kbd></td><td>${what}</td></tr>`).join("");
    this.$("#title .version").textContent = `Claude and Magic v${CM.version}`;
    game.on("change", () => this.refresh());
    game.on("mode", (mode) => this.show(mode === "title" ? "title" : "play"));
    game.on("bag", (open) => (open ? this.openBag() : this.show("play")));
    game.on("fx", (fx) => this.fx(fx));
    this.show("title");
  }

  attachCanvas(where) {
    const slot = where === "title" ? this.$("#title .backdrop-slot") : this.$("#view .canvas-slot");
    if (this.canvas.parentNode !== slot) slot.appendChild(this.canvas);
    this.canvas.className = where === "title" ? "backdrop" : "";
  }

  show(screen) {
    for (const s of this.root.querySelectorAll(".screen")) s.classList.toggle("on", s.id === screen);
    this.screen = screen;
    if (screen === "title") { this.attachCanvas("title"); this.refreshTitle(); }
    if (screen === "play") this.attachCanvas("play");
    this.refresh();
  }

  dialogOpen() { return Boolean(this.root.querySelector(".dialog.on")); }
  openDialog(sel) { this.closeDialogs(); this.$(sel).classList.add("on"); }
  closeDialogs() { for (const d of this.root.querySelectorAll(".dialog.on")) d.classList.remove("on"); }

  portrait(cls, size) {
    const key = `${cls}:${size}`;
    if (!this.portraits[key]) this.portraits[key] = CM.art.portrait(cls, size);
    const c = document.createElement("canvas");
    c.width = c.height = size;
    c.getContext("2d").drawImage(this.portraits[key], 0, 0);
    return c;
  }

  // ---- the title ----
  _title() {
    const g = this.game;
    this.$("#seed").value = CM.randomSeed();
    this.$("#btn-dice").addEventListener("click", () => { this.$("#seed").value = CM.randomSeed(); });
    this.$("#btn-new").addEventListener("click", () => this.startNew());
    this.$("#btn-continue").addEventListener("click", () => g.continueRun());
    this.$("#btn-settings").addEventListener("click", () => this.openDialog("#dlg-settings"));
    this.$("#btn-keys").addEventListener("click", () => this.openDialog("#dlg-keys"));
    this.$("#btn-transfer").addEventListener("click", () => {
      this.$("#transfer-text").value = g.exportText();
      this.$("#transfer-note").textContent = "";
      this.openDialog("#dlg-transfer");
    });
    this.$("#btn-copy").addEventListener("click", () => {
      const t = this.$("#transfer-text");
      t.select();
      const done = navigator.clipboard ? navigator.clipboard.writeText(t.value).then(() => true, () => false) : Promise.resolve(document.execCommand("copy"));
      done.then((ok) => { this.$("#transfer-note").textContent = ok ? "Copied." : "Select the text and copy it yourself."; });
    });
    this.$("#btn-import").addEventListener("click", () => {
      const err = g.importText(this.$("#transfer-text").value);
      this.$("#transfer-note").textContent = err || "Imported.";
      this.refreshTitle();
    });
    const heroes = this.$("#heroes");
    for (const hero of CM.newParty()) {
      const div = document.createElement("div");
      div.className = "hero";
      div.appendChild(this.portrait(hero.cls, 48));
      const s = CM.CLASSES[hero.cls];
      const text = document.createElement("div");
      text.innerHTML = `<b>${hero.cls}</b> <small>${s.role} - ${s.hp} HP${s.mp ? `, ${s.mp} MP` : ""}, attack ${s.atk}, defence ${s.df}</small>
        <small>${s.blurb}</small><span class="gear">${hero.weapon.name}, ${hero.armor.name}</span>`;
      div.appendChild(text);
      heroes.appendChild(div);
    }
  }

  startNew() {
    const g = this.game;
    if (g.canContinue() && !window.confirm("A run is waiting to be continued. Start a new expedition and let it go?")) return;
    g.newGame(this.$("#seed").value);
  }

  refreshTitle() {
    const g = this.game;
    this.$("#title-note").textContent = g.titleNote;
    const can = g.canContinue();
    this.$("#btn-continue").disabled = !can;
    this.$("#continue-note").textContent = can
      ? `Floor ${g.lastRun.floor.number}, ${g.lastRun.gold.toLocaleString()} gold${g.lastRun.saved ? ", saved " + new Date(g.lastRun.saved).toLocaleString() : ""}`
      : "No expedition is under way.";
    const bag = CM.startingBag(this.$("#seed").value || "x");
    this.$("#start-with").textContent = `You set out with 30 gold and two potions (${bag.map((i) => i.name).join(", ")} - the seed decides which). `
      + "Chests and fallen monsters give better gear; a merchant's camp waits below floors 5, 10 and 15.";
    const table = this.$("#fame table");
    if (!g.fame.length) table.innerHTML = `<tr><td class="empty">No party has gone down yet.</td></tr>`;
    else table.innerHTML = g.fame.map((e, i) => `<tr><td>${i + 1}.</td><td>${this.esc(e.name).slice(0, 14)}</td>`
      + `<td class="${e.won ? "won" : ""}">${e.won ? "SLEW THE LICH KING" : "floor " + e.floor}</td><td>${e.gold.toLocaleString()} gold</td><td>${this.esc(e.date)}</td></tr>`).join("");
  }

  esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

  // ---- settings ----
  _settings() {
    const g = this.game, s = g.settings;
    const sound = this.$("#set-sound"), vol = this.$("#set-volume"), smooth = this.$("#set-smooth"), fps = this.$("#set-fps");
    sound.checked = s.sound; vol.value = Math.round(s.volume * 100); smooth.checked = s.smooth; fps.checked = s.fps;
    const apply = () => {
      s.sound = sound.checked; s.volume = vol.value / 100; s.smooth = smooth.checked; s.fps = fps.checked;
      g.saveSettings();
      g.emit("settings", s);
    };
    for (const el of [sound, vol, smooth, fps]) el.addEventListener("input", apply);
  }

  toggleFps() {
    this.game.settings.fps = !this.game.settings.fps;
    this.$("#set-fps").checked = this.game.settings.fps;
    this.game.saveSettings();
    this.game.emit("settings", this.game.settings);
  }

  // ---- the dungeon screen ----
  refresh() {
    const g = this.game;
    if (this.screen === "title") { this.refreshTitle(); return; }
    if (this.screen !== "play") return;
    const fl = g.floor;
    if (fl) {
      this.$("#view .compass").textContent = `${CM.DIR_NAMES[fl.facing]}   -   Floor ${fl.number}`;
      this.$("#side .where").textContent = `${CM.themeFor(fl.number).name} - floor ${fl.number}`;
    }
    this.$("#side .purse").textContent = `Gold: ${g.gold.toLocaleString()}   Potions: ${g.potionCount()}`;
    const hint = this.$("#view .hint");
    if (g.mode === "camp") hint.textContent = "A merchant's camp. Rest, trade, see to the fallen - then go deeper.";
    else if (g.mode === "combat") hint.textContent = "";
    else {
      const thing = fl && fl.things[`${fl.pos[0]},${fl.pos[1]}`];
      hint.textContent = thing ? (thing.type === "chest" ? "A chest. Space opens it." : "A ladder down. Space climbs it.") : "";
    }
    this.renderParty();
    this.renderLog();
    this.renderActions();
    this.drawAutomap(this.$("#automap"));
    if (this.$("#bigmap").classList.contains("on")) this.drawAutomap(this.$("#bigmap-canvas"));
  }

  renderParty() {
    const box = this.$("#party");
    if (box.children.length !== this.game.party.length) {
      box.innerHTML = "";
      for (const m of this.game.party) {
        const div = document.createElement("div");
        div.className = "member";
        div.appendChild(this.portrait(m.cls, 44));
        const text = document.createElement("div");
        text.innerHTML = `<div class="name"></div><div class="gear"></div><div class="bar hp"><i></i><span></span></div><div class="bar mp"><i></i><span></span></div>`;
        div.appendChild(text);
        box.appendChild(div);
      }
    }
    this.game.party.forEach((m, i) => {
      const div = box.children[i], dead = m.hp <= 0;
      div.classList.toggle("fallen", dead);
      div.querySelector(".name").textContent = `${m.cls}  Lv ${m.level}` + (dead ? "  (fallen)" : "");
      div.querySelector(".gear").textContent = `${m.weapon.name} / ${m.armor.name}`;
      const hp = div.querySelector(".bar.hp");
      hp.querySelector("i").style.width = `${100 * Math.max(0, m.hp) / Math.max(1, m.max)}%`;
      hp.querySelector("span").textContent = `HP ${Math.max(0, m.hp)}/${m.max}`;
      const mp = div.querySelector(".bar.mp");
      mp.style.display = m.maxmp ? "" : "none";
      mp.querySelector("i").style.width = `${100 * Math.max(0, m.mp) / Math.max(1, m.maxmp)}%`;
      mp.querySelector("span").textContent = `MP ${m.mp}/${m.maxmp}`;
    });
  }

  renderLog() {
    const log = this.$("#log");
    const lines = this.game.messages.slice(-7);
    log.innerHTML = lines.map((l) => `<div>${this.esc(l)}</div>`).join("");
  }

  renderActions() {
    const g = this.game, box = this.$("#actions");
    const sets = {
      explore: [["◄ Turn", () => g.turn(-1)], ["▲ Forward", () => g.move(0)], ["▼ Back", () => g.move(2)], ["Turn ►", () => g.turn(1)],
        ["Use (Space)", () => g.use()], ["Inventory (I)", () => g.openBag()], ["Map (Tab)", () => this.toggleBigMap()], ["Menu (Esc)", () => this.openDialog("#dlg-pause")]],
      combat: [["Fight (F)", () => g.combatRound("fight")], ["Cast (C)", () => g.combatRound("cast")],
        ["Potion (P)", () => g.combatRound("potion")], ["Run (R)", () => g.combatRound("run")]],
      camp: [["Merchant", () => g.openBag(true)], ["Rest (20 gold)", () => g.rest()], ["Raise the fallen", () => g.raiseDead()],
        ["Inventory", () => g.openBag()], ["Go deeper", () => g.leaveCamp()], ["Menu (Esc)", () => this.openDialog("#dlg-pause")]],
    };
    const wanted = sets[g.mode] || [];
    if (box.dataset.mode !== g.mode) {
      box.innerHTML = "";
      box.dataset.mode = g.mode;
      for (const [text, slot] of wanted) {
        const b = document.createElement("button");
        b.textContent = text;
        b.addEventListener("click", () => { slot(); });
        box.appendChild(b);
      }
    }
  }

  toggleBigMap() {
    const d = this.$("#bigmap");
    if (d.classList.contains("on")) this.closeDialogs();
    else { this.openDialog("#bigmap"); this.drawAutomap(this.$("#bigmap-canvas")); }
  }

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
    const colours = { chest: "#C08030", ladder: "#3060C0", monsters: "#C03030", boss: "#8030C0" };
    for (const [x, y] of fl.seen) {
      p.fillStyle = fl.grid[y][x] ? "#3A3028" : "#F8F0DC";
      p.fillRect(x * cell, y * cell, cell, cell);
      const thing = fl.things[`${x},${y}`];
      if (thing && !fl.grid[y][x]) {
        p.fillStyle = colours[thing.type];
        p.beginPath(); p.arc((x + 0.5) * cell, (y + 0.5) * cell, cell * 0.3, 0, Math.PI * 2); p.fill();
      }
    }
    const [x, y] = fl.pos, [dx, dy] = CM.DIRS[fl.facing], cx = (x + 0.5) * cell, cy = (y + 0.5) * cell;
    p.fillStyle = "#20A040";
    p.beginPath();
    p.moveTo(cx + dx * cell * 0.45, cy + dy * cell * 0.45);
    p.lineTo(cx - dy * cell * 0.35 - dx * cell * 0.3, cy + dx * cell * 0.35 - dy * cell * 0.3);
    p.lineTo(cx + dy * cell * 0.35 - dx * cell * 0.3, cy - dx * cell * 0.35 - dy * cell * 0.3);
    p.fill();
  }

  // the names and health of the foes, over the view, where they stand
  drawHud(foes, project) {
    const hud = this.$("#hud"), view = this.$("#view");
    const dpr = Math.min(2, window.devicePixelRatio || 1), w = view.clientWidth, h = view.clientHeight;
    if (hud.width !== Math.round(w * dpr) || hud.height !== Math.round(h * dpr)) { hud.width = Math.round(w * dpr); hud.height = Math.round(h * dpr); }
    const p = hud.getContext("2d");
    p.setTransform(dpr, 0, 0, dpr, 0, 0);
    p.clearRect(0, 0, w, h);
    for (const f of foes) {
      const at = project(f.wx, f.wh, f.wz);
      if (!at) continue;
      const [sx, sy, depth] = at, bw = CM.clamp(120 / depth, 40, 110);
      p.fillStyle = "#401010"; p.fillRect(sx - bw / 2, sy - 8, bw, 6);
      p.fillStyle = "#E03030"; p.fillRect(sx - bw / 2, sy - 8, bw * Math.max(0, f.m.hp) / f.m.max, 6);
      p.font = `bold ${CM.clamp(26 / depth, 10, 14)}px Georgia`; p.textAlign = "center";
      p.fillStyle = "#000"; p.fillText(f.m.name, sx + 1, sy - 12);
      p.fillStyle = "#fff"; p.fillText(f.m.name, sx, sy - 13);
    }
  }

  fx(fx) {
    if (fx.kind === "hurt") {
      const flash = this.$("#view .hurt");
      flash.classList.add("on");
      setTimeout(() => flash.classList.remove("on"), 60);
    }
  }

  floatText(x, y, text, cls = "") {
    const el = document.createElement("div");
    el.className = "float " + cls;
    el.textContent = text;
    el.style.left = `${x}px`; el.style.top = `${y}px`;
    this.$("#floats").appendChild(el);
    setTimeout(() => el.remove(), 950);
  }

  // ---- the bag and the merchant ----
  _bag() {
    const g = this.game;
    const give = this.$("#bag-give");
    for (let i = 0; i < 4; i++) {
      const b = document.createElement("button");
      b.addEventListener("click", () => { this.note(g.give(this.bagRow, i)); this.fillBag(); });
      give.appendChild(b);
    }
    this.$("#btn-buy").addEventListener("click", () => { this.note(g.buy(this.shopRow)); this.fillBag(); });
    this.$("#btn-sell").addEventListener("click", () => { this.note(g.sell(this.bagRow)); this.fillBag(); });
    this.$("#btn-bag-done").addEventListener("click", () => g.closeBag());
  }

  note(text) { this.$("#bag-note").textContent = text || this.$("#bag-note").dataset.base; }

  openBag() {
    this.bagRow = this.shopRow = -1;
    this.show("bag");
    this.fillBag();
  }

  fillBag() {
    const g = this.game, shop = g.shopping;
    this.$("#bag-title").textContent = `${shop ? "The Merchant" : "Inventory"}   -   Gold: ${g.gold.toLocaleString()}`;
    this.$("#shop-list").style.display = shop ? "" : "none";
    this.$("#btn-buy").style.display = shop ? "" : "none";
    this.$("#btn-sell").style.display = shop ? "" : "none";
    const list = (el, head, items, selected, describe, onPick) => {
      el.innerHTML = `<div class="head">${head}</div>` + (items.length ? "" : `<div class="empty">Nothing here.</div>`);
      items.forEach((item, i) => {
        const row = document.createElement("div");
        row.className = "item" + (i === selected ? " sel" : "");
        row.innerHTML = `${this.esc(item.name)} <span class="what">${describe(item)}</span>`;
        row.addEventListener("click", () => { onPick(i); this.fillBag(); });
        el.appendChild(row);
      });
    };
    list(this.$("#bag-list"), "Your pack", g.bag, this.bagRow, (i) => `(${g.describe(i)}, worth ${Math.floor(i.value / 2)} gold)`, (i) => { this.bagRow = i; });
    if (shop) list(this.$("#shop-list"), "The merchant's wares", g.stock || [], this.shopRow,
      (i) => (i.kind === "weapon" || i.kind === "armor" ? `(+${i.power})  -  ${i.value} gold` : `-  ${i.value} gold`), (i) => { this.shopRow = i; });
    this.$("#bag-give").querySelectorAll("button").forEach((b, i) => {
      const m = g.party[i];
      b.textContent = `Give to ${m.cls}` + (m.hp <= 0 ? " (fallen)" : "");
    });
    const base = "Pick something from your pack, then who should equip or use it." + (shop ? "  Pick from the merchant's wares (right) to Buy." : "");
    this.$("#bag-note").dataset.base = base;
    if (!this.$("#bag-note").textContent) this.$("#bag-note").textContent = base;
  }
};
