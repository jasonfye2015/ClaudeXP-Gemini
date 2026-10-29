"use strict";
// The window around the dungeon: the title (what you set out with, the Hall of Fame and its details, settings), the
// party and the log under the view, the automap, the bag and the merchant, the little dialogs, and the end of a run.
// It listens to the Game and redraws; it never decides the rules.
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
    <h1><span class="emblem-slot"></span>Claude and Magic</h1>
    <div class="tagline">Twenty floors down, the Lich King waits - and below him, the Deep. Four go in together.</div>
    <div class="note" id="title-note"></div>
    <div class="honours" id="honours"></div>
    <div class="card" id="expedition">
      <h2>Expedition</h2>
      <div class="row slots" id="slots-row"><span class="small">Expedition</span><button data-slot="1">1</button><button data-slot="2">2</button><button data-slot="3">3</button></div>
      <div class="row"><button id="btn-continue" class="primary">Continue</button><span id="continue-note" class="small"></span></div>
      <div class="row"><button id="btn-new" class="primary">New Expedition</button><label for="seed">Seed</label><input id="seed" type="text" maxlength="40" spellcheck="false"><button id="btn-dice" title="Another seed">&#x2684;</button><button id="btn-daily" title="Today's dungeon: the same one for everyone, today">Today's</button></div>
      <p>The same seed lays out the same fifty floors, so a dungeon can be tried again - or handed to a friend. What
      the monsters do in a fight is up to the dice. The run saves as you go; when the whole party falls, it ends, and
      the deepest runs go in the Hall of Fame.</p>
      <h2>The eight callings</h2>
      <div id="classes"></div>
      <p id="start-with"></p>
    </div>
    <div class="card" id="fame"><h2>Hall of Fame <span class="boards"><button data-board="dungeon" class="on" title="Runs down the dungeon: to the Lich King, and to the bottom">The dungeon</button><button data-board="endless" title="Endless expeditions: how deep they went">Endless</button></span></h2><table></table><h2 class="later">Unlocks</h2><div id="unlocks"></div><h2 class="later">Trophies</h2><div id="trophies"></div><h2 class="later">Achievements</h2><div id="achievements"></div></div>
    <div class="foot"><label for="look">Theme</label><select id="look" title="The look of the dungeon - change it any time, here or in Settings"></select><button id="btn-settings">Settings</button><button id="btn-keys">Keys</button><button id="btn-transfer">Export / Import</button><button id="btn-credits">Credits</button></div>
    <div class="version"></div>
  </div>
</div>
<div id="create" class="screen">
  <div class="sheet">
    <h1>Who goes down?</h1>
    <div class="tagline">Four of them. Name them, choose their callings, roll their stats, and set them in their rows. The advice is only advice.</div>
    <div id="slots"></div>
    <div class="card" id="advice"><h2>Advice</h2><ul></ul></div>
    <div class="foot"><button id="btn-suggest">Suggest a party</button><button id="btn-reroll-all">Reroll everyone</button>
      <label for="create-seed">Seed</label><input id="create-seed" type="text" maxlength="40" spellcheck="false">
      <label for="kit">Kit</label><select id="kit" title="What the deepest run so far has earned"></select>
      <label for="difficulty">Difficulty</label><select id="difficulty" title="How hard the dungeon is"></select>
      <label for="mode">Expedition</label><select id="mode" title="The dungeon has a bottom; an Endless expedition does not"><option value="dungeon">The dungeon</option><option value="endless">Endless</option></select>
      <button id="btn-setout" class="primary">Set out</button><button id="btn-create-back">Back</button></div>
    <div class="small" id="create-note"></div>
  </div>
</div>
<div id="play" class="screen">
  <div class="top">
    <div id="view"><div class="canvas-slot"></div><canvas id="hud"></canvas><div class="vignette"></div><div class="compass"></div><div class="fps"></div><div class="hurt"></div><div class="blink"></div><div class="fall"></div><div class="tint"></div><div id="floats"></div><div class="hint"></div></div>
    <div id="side"><canvas id="automap" width="290" height="290"></canvas><div class="where"></div><div class="purse"></div><div class="light"></div></div>
  </div>
  <div id="party"></div>
  <div id="log" role="log" aria-live="polite"></div>
  <div id="actions"></div>
</div>
<div id="bag" class="screen">
  <h2 id="bag-title"></h2>
  <div class="lists"><div class="list" id="bag-list"></div><div class="list" id="shop-list"></div></div>
  <div class="note" id="bag-note"></div>
  <div class="give" id="bag-give"></div>
  <div class="act"><button id="btn-buy">Buy</button><button id="btn-sell">Sell</button><button id="btn-sort" title="Weapons, then armour, shields, helms, rings, amulets, then the rest - the best first">Sort the pack</button><button id="btn-bag-done" class="primary">Done</button></div>
</div>
<div class="dialog" id="dlg-settings"><div class="box"><h2>Settings</h2>
  <div class="row"><label for="set-sound">Sound</label><input type="checkbox" id="set-sound"></div>
  <div class="row"><label for="set-volume">Volume</label><input type="range" id="set-volume" min="0" max="100"></div>
  <div class="row"><label for="set-music">Music (a tune for each depth, the fight, the camp)</label><input type="checkbox" id="set-music"></div>
  <div class="row"><label for="set-music-volume">Music volume</label><input type="range" id="set-music-volume" min="0" max="100"></div>
  <div class="row"><label for="set-look">Theme - the look of the dungeon</label><select id="set-look"></select></div>
  <div class="small" id="set-look-note"></div>
  <div class="row"><label for="set-smooth">Smooth steps and turns (off: snap, the classic way)</label><input type="checkbox" id="set-smooth"></div>
  <div class="row"><label for="set-fps">Show frames per second (F3)</label><input type="checkbox" id="set-fps"></div>
  <div class="row"><label for="set-tap">Tap or click the view to move (the sides turn, the top walks, the bottom steps back)</label><input type="checkbox" id="set-tap"></div>
  <div class="row"><label for="set-speed">Combat speed - how long bolts fly and sparks hang</label><select id="set-speed"><option value="normal">Normal</option><option value="fast">Fast</option><option value="instant">As good as instant</option></select></div>
  <div class="row"><label for="set-text">Text size</label><select id="set-text"><option value="normal">Normal</option><option value="large">Large</option><option value="larger">Larger</option></select></div>
  <div class="row"><label for="set-motion">Reduce motion - no shaking, no flashes, no washes of colour over the view</label><input type="checkbox" id="set-motion"></div>
  <div class="row"><label for="set-contrast">High contrast - brighter text and sharper edges</label><input type="checkbox" id="set-contrast"></div>
  <div class="row"><label for="set-swapab">Gamepad: swap A and B (confirm with B, back with A)</label><input type="checkbox" id="set-swapab"></div>
  <div class="small" id="set-storage"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-keys"><div class="box"><h2>Keys</h2><p class="small">Change sets a key: press the one you want. Esc and the arrows stay as they are.</p><table class="keys"></table><div class="end"><button id="btn-keys-reset">Reset</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-credits"><div class="box"><h2>Credits</h2><div id="credits"></div><div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-transfer"><div class="box"><h2>Export / Import</h2>
  <p class="small">Your run, the Hall of Fame and your settings, as text. Copy it to keep it or to carry it to another
  browser; paste a copy here and Import to bring it back.</p>
  <textarea id="transfer-text" spellcheck="false"></textarea>
  <div class="small" id="transfer-note"></div>
  <div class="end"><button id="btn-copy">Copy</button><button id="btn-import">Import</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-pause"><div class="box"><h2>Paused</h2>
  <p class="small">The run is saved as you go.</p>
  <div class="end"><button id="btn-pause-settings">Settings</button><button id="btn-pause-title">Back to the title</button><button class="close primary">Carry on</button></div></div></div>
<div class="dialog" id="dlg-sheet"><div class="box sheetbox">
  <h2 id="sheet-title"></h2>
  <div class="sheet-grid"><div id="sheet-left"></div><div id="sheet-right"></div></div>
  <div id="sheet-boon"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-temple"><div class="box"><h2>The Temple</h2>
  <p class="small">An old priest keeps a shrine by the camp fire, and asks for the upkeep of his candles.</p>
  <div class="row"><label>Cure the small ailments - poison, sleep, paralysis, blindness - for everyone</label><button data-service="cure">30 gold</button></div>
  <div class="row"><label>Lift a curse</label><button data-service="uncurse">60 gold</button></div>
  <div class="row"><label>Stone to flesh</label><button data-service="unstone">150 gold</button></div>
  <div class="row"><label>Raise the fallen (100 gold a level)</label><button id="btn-temple-raise">Raise</button></div>
  <div class="row"><label>The priest's scribe names everything unknown you carry</label><button id="btn-scribe">25 gold</button></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-tavern"><div class="box"><h2>The Tavern</h2>
  <p class="small">Three who'd come along, for a price - to take the place of a hero who has fallen or turned to stone. What the fallen wore besides weapon and armour stays with the party.</p>
  <div id="recruits"></div>
  <div class="small" id="tavern-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-smith"><div class="box journalbox"><h2>The Smith</h2>
  <p class="small">A dwarf of the deep halls, who came up and stayed, works a forge by the camp. A diamond and his fee put +1 on a piece of gear (three times at most);
  a ruby, a sapphire or a sunstone goes into a weapon for fire, frost or holiness.</p>
  <div class="small" id="smith-gems"></div><div id="smith-list"></div><div class="small" id="smith-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-vault"><div class="box journalbox"><h2>The Vault</h2>
  <p class="small">The merchant keeps one thing in an iron box for whoever comes after: leave an heirloom here, and the next party to reach a camp may take it up.</p>
  <div class="list-title">In the vault</div><div class="recruit" id="vault-held"></div>
  <div class="list-title">Leave something</div><div id="vault-list"></div><div class="small" id="vault-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-waystone"><div class="box"><h2>The Waystones</h2>
  <p class="small">A mark chalked by every camp fire the party has reached. From one camp, the old road leads to another: the floors between stay as you left them.</p>
  <div id="waystone-list"></div><div class="small" id="waystone-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-lore"><div class="box"><h2>Carved into the stone</h2><p id="lore-text" class="lore"></p>
  <div class="end"><button class="close primary">Walk on</button></div></div></div>
<div class="dialog" id="dlg-talk"><div class="box"><h2 id="talk-title"></h2><p id="talk-text" class="lore"></p>
  <div class="end"><button class="close primary">Walk on</button></div></div></div>
<div class="dialog" id="dlg-riddle"><div class="box"><h2>Runes on the door</h2><p id="riddle-q" class="lore"></p><div id="riddle-answers" class="answers"></div>
  <p class="small">The answer is carved somewhere above. A wrong one burns.</p><div class="end"><button class="close">Step back</button></div></div></div>
<div class="dialog" id="dlg-journal"><div class="box journalbox"><h2>Journal</h2><div id="journal-list"></div>
  <div class="end"><button class="close primary">Close</button></div></div></div>
<div class="dialog" id="dlg-over"><div class="box overbox"><div class="emblem-slot"></div><h2 id="over-title"></h2><p id="over-text" class="lore"></p>
  <div class="roll" id="over-party"></div><div class="tally" id="over-tally"></div>
  <div class="end"><button id="btn-over-card" class="ended">Summary card</button><button class="close primary ended">To the title</button>
    <button id="btn-over-daylight" class="crown">Into the daylight</button><button id="btn-over-deep" class="crown primary">Into the Deep</button></div></div></div>
<div class="dialog" id="dlg-card"><div class="box cardbox"><h2>The expedition, in a card</h2><div id="card-slot"></div>
  <textarea id="card-text" spellcheck="false" readonly></textarea><div class="small" id="card-note"></div>
  <div class="end"><button id="btn-card-copy">Copy the text</button><button id="btn-card-save">Save the card (PNG)</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="bigmap"><canvas id="bigmap-canvas" width="600" height="600"></canvas></div>`;
    this.$ = (sel) => root.querySelector(sel);
    this.canvas = document.createElement("canvas");                        // the one WebGL canvas, moved between screens
    this.canvas.id = "gl";
    this.attachCanvas("title");
    for (const b of root.querySelectorAll(".dialog .close")) b.addEventListener("click", () => this.closeDialogs());
    for (const d of root.querySelectorAll(".dialog")) d.addEventListener("click", (e) => { if (e.target === d) this.closeDialogs(); });
    this._title();
    this._create();
    this._bag();
    this._settings();
    for (const b of root.querySelectorAll("#dlg-temple button[data-service]")) {
      b.addEventListener("click", () => { game.temple(b.dataset.service); this.refresh(); });
    }
    this.$("#btn-temple-raise").addEventListener("click", () => { game.raiseDead(); this.refresh(); });
    this.$("#btn-scribe").addEventListener("click", () => { game.scribe(); this.refresh(); });
    this.$("#btn-daily").addEventListener("click", () => { this.$("#seed").value = CM.dailySeed(); this.refreshTitle(); });
    this.$("#btn-pause-settings").addEventListener("click", () => { this.closeDialogs(); this.openDialog("#dlg-settings"); });
    this.$("#btn-pause-title").addEventListener("click", () => { this.closeDialogs(); game.saveRun(); game.setMode("title"); });
    this.renderKeys();
    this.$("#btn-keys-reset").addEventListener("click", () => this.resetKeys());
    this.$("#btn-over-card").addEventListener("click", () => this.openCard(this.overEntry));
    this.$("#btn-over-daylight").addEventListener("click", () => { this.closeDialogs(); game.endRun(true); });
    this.$("#btn-over-deep").addEventListener("click", () => { this.closeDialogs(); game.say("You leave the crown where it fell, and go down."); this.refresh(); });
    this.$("#btn-card-copy").addEventListener("click", () => this.copyText(this.$("#card-text").value, this.$("#card-note")));
    this.$("#btn-card-save").addEventListener("click", () => {
      const c = this.$("#card-slot canvas");
      if (!c) return;
      const a = document.createElement("a");
      a.href = c.toDataURL("image/png"); a.download = `Claude and Magic - ${(this.cardEntry && this.cardEntry.seed) || "expedition"}.png`;
      document.body.appendChild(a); a.click(); a.remove();
      this.$("#card-note").textContent = "Saved, where the browser puts downloads.";
    });
    for (const b of this.root.querySelectorAll("#slots-row button[data-slot]")) b.addEventListener("click", () => { game.setSlot(Number(b.dataset.slot)); this.refreshTitle(); });
    for (const c of [this.$("#automap"), this.$("#bigmap-canvas")]) {
      const cellAt = (e) => { const fl = game.floor; if (!fl) return null; const r = c.getBoundingClientRect(), size = fl.grid.length; return [Math.floor((e.clientX - r.left) / r.width * size), Math.floor((e.clientY - r.top) / r.height * size)]; };
      c.addEventListener("click", (e) => { const at = cellAt(e); if (!at) return; if (game.travel) { game.stopTravel(); return; } if (game.travelTo(at[0], at[1]) && c.id === "bigmap-canvas") this.closeDialogs(); });
      c.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        const at = cellAt(e), fl = game.floor;
        if (!at || !fl || !fl.seen.some(([x, y]) => x === at[0] && y === at[1])) return;
        const was = (fl.notes || {})[`${at[0]},${at[1]}`] || "";
        const text = window.prompt("A note for this square (a word or two; empty takes it off):", was);
        if (text !== null) game.setNote(at[0], at[1], text);
      });
    }
    this.$("#title .version").textContent = `Claude and Magic v${CM.version}`;
    this.$("#title .emblem-slot").appendChild(CM.art.emblem(120));
    this.fameOpen = -1;
    this.ending = null;                                                  // "victory" or "lament" while the ending is up (the music follows)
    game.on("over", (won, entry) => this.showEnding(won, entry));
    game.on("crowned", () => this.showCrowning());
    game.on("change", () => this.refresh());
    game.on("mode", (mode) => this.show(mode === "title" ? "title" : "play"));
    game.on("bag", (open) => (open ? this.openBag() : this.show("play")));
    game.on("fx", (fx) => this.fx(fx));
    game.on("turn", () => { this.cmenu = { kind: "main" }; });
    game.on("mode", (mode) => { if (mode !== "combat") this.cmenu = { kind: "main" }; this.xmenu = null; });
    game.on("lore", (text) => { this.$("#lore-text").textContent = text; this.openDialog("#dlg-lore"); });
    game.on("talk", ({ title, text }) => { this.$("#talk-title").textContent = title; this.$("#talk-text").textContent = text; this.openDialog("#dlg-talk"); });
    game.on("riddle", (k) => this.askRiddle(k));
    game.on("teleported", () => this.flash(".blink", 60));
    game.on("fell", () => this.flash(".fall", 350));
    this.show("title");
  }

  flash(sel, ms) {
    if (CM.reducedMotion && sel !== ".fall") return;
    const el = this.$("#view " + sel);
    el.classList.add("on");
    setTimeout(() => el.classList.remove("on"), ms);
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

  // ---- a hero's sheet ----
  openSheet(i) {
    const g = this.game, h = g.party[i];
    if (!h) return;
    this.sheetOf = i;
    this.renderSheet();
    this.openDialog("#dlg-sheet");
  }

  renderSheet() {
    const g = this.game, h = g.party[this.sheetOf];
    if (!h || !this.$("#dlg-sheet").classList.contains("on") && this.sheetOf === undefined) return;
    const c = CM.CLASSES[h.cls] || CM.CLASSES.Knight, st = h.status || {}, fallen = h.hp <= 0;
    this.$("#sheet-title").textContent = `${h.name} - ${h.cls}, level ${h.level}${fallen ? " (fallen)" : ""}`;
    const next = CM.xpForLevel(h.level + 1);
    const eff = g.effective(h);
    const left = this.$("#sheet-left");
    left.innerHTML = "";
    left.appendChild(this.portrait(h.cls, 96));
    const facts = document.createElement("div");
    facts.className = "facts";
    facts.innerHTML = `<div>${c.role}${c.cast ? `, casts <b>${CM.CASTS[c.cast]}</b>` : ""}</div>
      <div>Experience ${h.xp} / ${next} for level ${h.level + 1}</div>
      <div>Health ${Math.max(0, h.hp)} / ${h.max}${h.maxmp ? ` &nbsp; Magic ${h.mp} / ${h.maxmp}` : ""}</div>
      <div>Attack ${eff.atk}${eff.atk !== h.atk ? ` (${h.atk})` : ""} &nbsp; Defence ${eff.df}${eff.df !== h.df ? ` (${h.df})` : ""} + gear ${CM.gearDefence(h)} &nbsp; Hits ${Math.round(g.hitChance(h) * 100)}%</div>
      <div class="rowpick"><span>Row:</span><button data-row="front" class="${h.row === "front" ? "on" : ""}">Front</button><button data-row="back" class="${h.row === "back" ? "on" : ""}">Back</button>
        <small>${g.mode === "combat" ? "not in a fight" : h.row === "front" ? "takes the blows" : h.cls === "Rogue" || h.cls === "Ranger" ? "strikes from safety" : "safer, hits for half"}</small></div>
      <div class="list-title">Gear</div>
      <div class="gear-list">${CM.SLOTS.map((slot) => { const it = h[slot]; return `<div><span class="slot">${CM.SLOT_NAMES[slot]}</span><span class="icon-slot" data-slot="${slot}"></span> ${it ? `<b>${this.esc(it.unknown ? CM.baseName(it) : it.name)}</b> <small>${this.esc(CM.itemLabel(it))}</small>` : "<small>-</small>"}${it && !["weapon", "armor"].includes(slot) && g.mode !== "combat" ? ` <button data-off="${slot}">Take off</button>` : ""}</div>`; }).join("")}</div>`;
    for (const span of facts.querySelectorAll(".icon-slot")) { const it = h[span.dataset.slot]; if (it) span.appendChild(this.icon(it, 20)); }
    for (const b of facts.querySelectorAll("button[data-row]")) b.addEventListener("click", () => { if (g.setRow(h, b.dataset.row)) this.renderSheet(); });
    for (const b of facts.querySelectorAll("button[data-off]")) b.addEventListener("click", () => { const note = g.takeOff(this.sheetOf, b.dataset.off); if (note) g.say(note); this.renderSheet(); });
    left.appendChild(facts);
    const right = this.$("#sheet-right");
    right.innerHTML = `<table class="stats">${CM.STATS.map((s) => `<tr class="${s === c.key ? "key" : ""}"><td>${CM.STAT_NAMES[s]}</td><td class="v">${g.stat(h, s)}</td><td class="hint">${s === c.key ? "their calling's stat" : CM.STAT_HINTS[s]}</td></tr>`).join("")}</table>
      <div class="list-title">Boons</div><div class="boons">${(h.boons || []).length ? h.boons.map((id) => `<div><b>${CM.BOONS[id].name}</b> - ${CM.BOONS[id].what}</div>`).join("") : "<div class='small'>None yet. Each level earned offers one.</div>"}</div>
      <div class="list-title">Path</div><div class="boons">${h.path && CM.PATHS[h.cls] && CM.PATHS[h.cls][h.path] ? (() => { const P = CM.PATHS[h.cls][h.path]; return `<div><b>${P.name}</b> - ${P.blurb}</div><div><b>${P.t1.name}</b> - ${P.t1.what}</div><div><b>${P.t2.name}</b> - ${h.level >= CM.PATH_AT[1] ? P.t2.what : `at level ${CM.PATH_AT[1]}: ${P.t2.what.charAt(0).toLowerCase() + P.t2.what.slice(1)}`}</div>`; })() : `<div class='small'>${CM.needsPath(h) ? "A path waits to be chosen, below." : `Chosen at level ${CM.PATH_AT[0]}: two ways for a ${h.cls} to grow.`}</div>`}</div>
      ${(h.learned || []).length ? `<div class="list-title">Learned from tomes</div><div class="boons">${h.learned.map((id) => `<div><b>${CM.ABILITIES[id].name}</b> - ${CM.ABILITIES[id].what}</div>`).join("")}</div>` : ""}
      <div class="list-title">Ailments</div><div class="ails">${Object.keys(st).length ? Object.keys(st).map((s) => `<div><b>${CM.STATUSES[s].mark} ${CM.STATUSES[s].name}</b> - ${CM.STATUSES[s].hint}${st[s] < 900 ? ` (${st[s]} more rounds)` : ""}</div>`).join("") : "<div class='small'>None.</div>"}</div>`;
    const boon = this.$("#sheet-boon");
    boon.innerHTML = "";
    if (h.pending > 0) {
      const offer = g.offerBoons(h);
      boon.innerHTML = `<div class="list-title gold">Level ${h.level}: choose a boon${h.pending > 1 ? ` (${h.pending} to choose)` : ""}</div>`;
      const row = document.createElement("div");
      row.className = "offer";
      for (const id of offer) {
        const b = document.createElement("button");
        b.innerHTML = `<b>${CM.BOONS[id].name}</b><small>${CM.BOONS[id].what}</small>`;
        b.addEventListener("click", () => { g.chooseBoon(h, id); this.renderSheet(); });
        row.appendChild(b);
      }
      boon.appendChild(row);
    }
    if (CM.needsPath(h)) {
      const title = document.createElement("div");
      title.className = "list-title gold";
      title.textContent = `Level ${CM.PATH_AT[0]}: choose ${h.name}'s path`;
      boon.appendChild(title);
      const row = document.createElement("div");
      row.className = "offer";
      for (const [id, P] of Object.entries(CM.PATHS[h.cls])) {
        const b = document.createElement("button");
        b.innerHTML = `<b>${P.name}</b><small>${P.blurb} Now: ${P.t1.what}. At level ${CM.PATH_AT[1]}: ${P.t2.what.charAt(0).toLowerCase() + P.t2.what.slice(1)}.</small>`;
        b.addEventListener("click", () => { g.choosePath(h, id); this.renderSheet(); });
        row.appendChild(b);
      }
      boon.appendChild(row);
    }
  }

  dialogOpen() { return Boolean(this.root.querySelector(".dialog.on")); }
  // ---- the waystones ----
  openWaystone() { this.renderWaystone(); this.openDialog("#dlg-waystone"); }
  renderWaystone() {
    const g = this.game, box = this.$("#waystone-list"), camps = g.camps || [];
    box.innerHTML = "";
    for (const n of camps) {
      const row = document.createElement("div");
      row.className = "recruit";
      row.style.gridTemplateColumns = "1fr auto";
      row.innerHTML = `<div><b>The camp below floor ${n}</b><small>${this.esc(CM.themeFor(n).name)}${g.floor && g.floor.number === n ? " - you are here" : ""}</small></div>`;
      const b = document.createElement("button");
      b.textContent = "Walk the old road";
      b.disabled = Boolean(g.floor && g.floor.number === n);
      b.addEventListener("click", () => { const note = g.waystone(n); if (note) this.$("#waystone-note").textContent = note; else this.closeDialogs(); this.refresh(); });
      row.appendChild(b);
      box.appendChild(row);
    }
    if (!camps.length) box.innerHTML = `<div class="small">No mark yet.</div>`;
    this.$("#waystone-note").textContent = "";
  }
  openDialog(sel) { this.closeDialogs(); this.$(sel).classList.add("on"); if (sel === "#dlg-settings") this.showStorage(); }
  closeDialogs() {
    const ending = this.$("#dlg-over").classList.contains("on");
    for (const d of this.root.querySelectorAll(".dialog.on")) d.classList.remove("on");
    if (ending) { this.ending = null; if (this.onEnding) this.onEnding(); }
  }

  // ---- the end of a run: how it went, who came back, what it came to ----
  showEnding(won, entry) {
    const g = this.game, t = entry.tally || {}, board = entry.endless ? g.fameEndless : g.fame, rank = board.indexOf(entry) + 1;
    this.overEntry = entry;
    this.fameBoard = entry.endless ? "endless" : "dungeon";
    this.fameOpen = -1;                                                  // (the Hall of Fame has been re-sorted: an open row would be another's)
    const slot = this.$("#dlg-over .emblem-slot");
    slot.innerHTML = "";
    slot.appendChild(CM.art.emblem(120));
    this.$("#dlg-over").classList.toggle("won", won);
    this.$("#dlg-over").classList.remove("crowning");
    this.$("#over-title").textContent = CM.endlessFall(entry) ? `Floor ${entry.floor} of the endless dark` : entry.bottom ? "To the bottom of the world" : won && entry.floor > CM.LAST_FLOOR ? `With the crown, into the Deep - and down on floor ${entry.floor}` : won ? "The Lich King is no more" : `The party fell on floor ${entry.floor}`;
    const standing = g.party.filter((h) => h.hp > 0), fallen = g.party.filter((h) => h.hp <= 0);
    const names = (list) => (list.length ? list.map((h) => h.name).join(", ").replace(/, ([^,]*)$/, " and $1") : "The party");
    let text;
    if (CM.endlessFall(entry)) {
      text = `${entry.floor} floors down into a dark with no bottom${won ? ", with the Lich King's crown" : ""}, the last of them fell, in ${CM.themeFor(entry.floor).name} come round again, with ${entry.gold.toLocaleString()} gold. ${names(g.party)} are counted among the deepest.`
        + (t.kills ? ` ${CM.plural(t.kills, "monster")} went down before them.` : "") + " The dark goes on without them. It always did.";
    } else if (entry.bottom) {
      text = `The Root of the World is still, and the dark below it is only dark. ${names(standing)} climb fifty floors into the daylight with the Lich King's crown and ${entry.gold.toLocaleString()} gold`
        + (fallen.length ? `; ${names(fallen)} ${fallen.length > 1 ? "do" : "does"} not come back up.` : ", all four of them.") + " Nothing is dreaming the king now. The story is over, all the way down.";
    } else if (won && entry.floor > CM.LAST_FLOOR) {
      text = `They took the Lich King's crown and went down into the Deep, where the carvings never went. The last of them fell on floor ${entry.floor}, in ${CM.themeFor(entry.floor).name}, with ${entry.gold.toLocaleString()} gold. The crown lies there with ${names(g.party)}.`
        + (t.kills ? ` ${CM.plural(t.kills, "monster")} went down before them.` : "") + " Somewhere above, another four are sharpening their blades - and they know the way now.";
    } else if (won) {
      text = `The crown rolls from the throne, and the cold goes out of the stone. ${names(standing)} climb twenty floors into the daylight with the Lich King's crown and ${entry.gold.toLocaleString()} gold`
        + (fallen.length ? `; ${names(fallen)} ${fallen.length > 1 ? "do" : "does"} not come back up, and ${fallen.length > 1 ? "their names are" : "that name is"} carved on the last floor beside his.` : ", all four of them.")
        + " The carvings told his story. This one is yours.";
    } else {
      text = `The last of them fell on floor ${entry.floor}, in ${CM.themeFor(entry.floor).name}, with ${entry.gold.toLocaleString()} gold they'll never spend. The dark closes over ${names(g.party)}.`
        + (t.kills ? ` ${CM.plural(t.kills, "monster")} went down before them.` : "") + " Somewhere above, another four are sharpening their blades.";
    }
    this.$("#over-text").textContent = text;
    const roll = this.$("#over-party");
    roll.innerHTML = "";
    for (const h of g.party) {
      const div = document.createElement("div");
      div.className = h.hp > 0 ? "standing" : "fallen";
      div.appendChild(this.portrait(h.cls, 56));
      const who = document.createElement("div");
      who.innerHTML = `<b>${this.esc(h.name)}</b><small>${h.cls}, level ${h.level}</small><small class="fate">${h.hp > 0 ? (won ? "comes home" : "stood to the last") : "fell"}</small>`;
      div.appendChild(who);
      roll.appendChild(div);
    }
    const facts = [["Floors", CM.endlessFall(entry) ? `${entry.floor}, Endless` : `${entry.floor} of ${entry.won || entry.floor > CM.LAST_FLOOR ? CM.BOTTOM : CM.LAST_FLOOR}`], ["Gold", entry.gold.toLocaleString()], ["Monsters slain", t.kills || 0],
      ["Chests opened", t.chests || 0], ["Steps walked", (t.steps || 0).toLocaleString()], ["Fights", `${t.fights || 0}${t.fled ? ` (${t.fled} fled)` : ""}`],
      ["Kit", (CM.KITS[entry.kit] || CM.KITS.pauper).name], ["Difficulty", (CM.DIFFICULTIES[entry.difficulty] || CM.DIFFICULTIES.fair).name], ["Seed", `${entry.seed}${entry.daily ? " (today's)" : ""}`],
      [entry.endless ? "Endless board" : "Hall of Fame", rank ? `${CM.ordinal(rank)} of ${board.length}` : "not among the ten"]];
    if (t.guardians && t.guardians.length) facts.splice(6, 0, ["Guardians slain", this.guardianNames(t.guardians)]);
    if (g.vault) facts.push(["In the vault", `${g.vault.name}, for the next party`]);
    if (entry.titles && entry.titles.length) facts.push(["Earned", entry.titles.map((id) => (CM.ACHIEVEMENTS[id] || { name: id }).name).join(", ")]);
    this.$("#over-tally").innerHTML = facts.map(([k, v]) => `<div><span>${k}</span><b>${this.esc(v)}</b></div>`).join("");
    this.openDialog("#dlg-over");                                      // (opening closes whatever was open - an ending too - so the kind is set after)
    this.ending = won ? "victory" : "lament";
    if (this.onEnding) this.onEnding();
  }

  portrait(cls, size) {
    const look = this.game.settings.look, key = `${look}:${cls}:${size}`;
    if (!this.portraits[key]) this.portraits[key] = CM.art.portrait(cls, size, look);
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
    this.$("#btn-new").addEventListener("click", () => this.openCreate());
    this.$("#btn-continue").addEventListener("click", () => g.continueRun());
    this.$("#btn-settings").addEventListener("click", () => this.openDialog("#dlg-settings"));
    this.$("#btn-keys").addEventListener("click", () => this.openDialog("#dlg-keys"));
    this.$("#btn-credits").addEventListener("click", () => {
      this.$("#credits").innerHTML = CM.art.credits().map(([who, what]) => `<div class="credit"><b>${this.esc(who)}</b><div>${this.esc(what)}</div></div>`).join("")
        + `<p class="small">A Claude Timeline game. The tile set and the textures are public domain (CC0); the whole sets are kept with the Timeline's media for the updates to come.</p>`;
      this.openDialog("#dlg-credits");
    });
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
    this.$("#fame table").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-seed]");
      if (b) { this.$("#seed").value = b.dataset.seed; this.refreshTitle(); return; }
      const c = e.target.closest("button[data-card]");
      if (c) { this.openCard((this.fameBoard === "endless" ? g.fameEndless : g.fame)[Number(c.dataset.card)]); return; }
      const tr = e.target.closest("tr.row");
      if (!tr) return;
      const i = Number(tr.dataset.i);
      this.fameOpen = this.fameOpen === i ? -1 : i;
      this.refreshTitle();
    });
    this.renderClasses();
  }

  renderClasses() {
    const classes = this.$("#classes");
    classes.innerHTML = "";
    for (const cls of CM.CLASS_ORDER) {
      const c = CM.CLASSES[cls], div = document.createElement("div");
      div.className = "calling";
      div.appendChild(this.portrait(cls, 30));
      const text = document.createElement("div");
      text.innerHTML = `<b>${cls}</b> <small>${c.role}${c.cast ? `, casts ${CM.CASTS[c.cast]}` : ""}.</small> <small>${c.blurb}</small>`;
      div.appendChild(text);
      classes.appendChild(div);
    }
  }

  // the theme changed (or its pack arrived): every portrait and icon is drawn again
  restyle() {
    this.portraits = {};
    this.renderClasses();
    if (this.screen === "create") this.renderCreate();
    this.$("#party").dataset.signature = "";
    if (this.screen === "bag") this.fillBag();
    if (this.$("#dlg-tavern").classList.contains("on")) this.renderTavern();
    this.refresh();
  }

  // ---- who goes down: the creation screen ----
  _create() {
    const g = this.game;
    this.slots = [];
    this.$("#btn-suggest").addEventListener("click", () => { this.fillSlots(CM.CLASSIC); this.renderCreate(); });
    this.$("#btn-reroll-all").addEventListener("click", () => { for (const s of this.slots) s.stats = CM.rollStats(s.cls); this.renderCreate(); });
    this.$("#btn-create-back").addEventListener("click", () => this.show("title"));
    this.$("#btn-setout").addEventListener("click", () => this.setOut());
    this.$("#create-seed").addEventListener("input", () => { this.$("#seed").value = this.$("#create-seed").value; this.renderCreateNote(); });
    this.$("#difficulty").innerHTML = Object.entries(CM.DIFFICULTIES).map(([id, d]) => `<option value="${id}">${d.name}</option>`).join("");
    this.$("#difficulty").value = "fair";
    this.$("#difficulty").addEventListener("change", () => this.renderCreateNote());
    this.$("#mode").addEventListener("change", () => this.renderCreateNote());
    for (const b of this.root.querySelectorAll("#fame .boards button")) b.addEventListener("click", () => { this.fameBoard = b.dataset.board; this.fameOpen = -1; this.refreshTitle(); });
    const slots = this.$("#slots");
    for (let i = 0; i < 4; i++) {
      const div = document.createElement("div");
      div.className = "slot";
      div.innerHTML = `<div class="top"><div class="portrait-slot"></div><div class="who"><input class="name" type="text" maxlength="14" spellcheck="false" title="Their name"><button class="dice" title="Another name">&#x2684;</button>
        <select class="cls" title="Their calling">${CM.CLASS_ORDER.map((c) => `<option value="${c}">${c}</option>`).join("")}</select></div></div>
        <div class="role"></div>
        <table class="stats"></table>
        <div class="derived"></div>
        <div class="rowpick"><span>Row:</span><button data-row="front">Front</button><button data-row="back">Back</button><button class="reroll">Reroll</button></div>`;
      div.querySelector(".name").addEventListener("input", (e) => { this.slots[i].name = e.target.value; this.renderAdvice(); });
      div.querySelector(".dice").addEventListener("click", () => { this.slots[i].name = CM.randomName(); this.renderCreate(); });
      div.querySelector(".cls").addEventListener("change", (e) => {
        const s = this.slots[i];
        s.cls = e.target.value; s.stats = CM.rollStats(s.cls); s.row = CM.CLASSES[s.cls].row;
        this.renderCreate();
      });
      div.querySelector(".reroll").addEventListener("click", () => { this.slots[i].stats = CM.rollStats(this.slots[i].cls); this.renderCreate(); });
      for (const b of div.querySelectorAll("button[data-row]")) b.addEventListener("click", () => { this.slots[i].row = b.dataset.row; this.renderCreate(); });
      slots.appendChild(div);
    }
    g.on("mode", (mode) => { if (mode !== "title") this.closeDialogs(); });
  }

  fillSlots(classes) {
    const rnd = new CM.Random(Math.floor(Math.random() * 4294967296));
    this.slots = classes.map((cls) => ({ cls, name: CM.randomName(rnd), stats: CM.rollStats(cls, rnd), row: CM.CLASSES[cls].row }));
  }

  openCreate() {
    const g = this.game;
    if (g.canContinue() && !window.confirm(`A run is waiting in expedition slot ${g.slot}. Start a new expedition there and let it go? (The other slots keep theirs.)`)) return;
    if (!this.slots.length) this.fillSlots(CM.CLASSIC);
    this.$("#create-seed").value = this.$("#seed").value;
    this.renderCreateNote();
    this.refreshTitle();                                                 // (the kits on offer)
    this.show("create");
    this.renderCreate();
  }

  renderCreate() {
    const cards = this.$("#slots").children;
    this.slots.forEach((s, i) => {
      const div = cards[i], c = CM.CLASSES[s.cls];
      const slot = div.querySelector(".portrait-slot");
      slot.innerHTML = "";
      slot.appendChild(this.portrait(s.cls, 56));
      if (div.querySelector(".name").value !== s.name) div.querySelector(".name").value = s.name;
      div.querySelector(".cls").value = s.cls;
      div.querySelector(".role").textContent = `${c.role}${c.cast ? `, casts ${CM.CASTS[c.cast]}` : ""}. ${c.blurb}`;
      div.querySelector(".stats").innerHTML = CM.STATS.map((st) => {
        const v = s.stats[st], key = st === c.key;
        return `<tr class="${key ? "key" : ""}"><td>${CM.STAT_NAMES[st]}</td><td class="v">${v}</td><td class="hint">${key ? "their calling's stat" : CM.STAT_HINTS[st]}</td></tr>`;
      }).join("");
      const h = CM.makeHero(s.cls, s.name, s.stats, s.row);
      div.querySelector(".derived").textContent = `${h.max} health${h.maxmp ? `, ${h.maxmp} magic` : ""}, attack ${h.atk}, defence ${h.df} - ${h.weapon.name} and ${h.armor.name}`;
      for (const b of div.querySelectorAll("button[data-row]")) b.classList.toggle("on", b.dataset.row === s.row);
    });
    this.renderAdvice();
  }

  renderAdvice() {
    const advice = CM.partyAdvice(this.slots), ul = this.$("#advice ul");
    ul.innerHTML = advice.notes.map((n) => `<li class="${advice.sound && advice.notes.length === 1 ? "good" : ""}">${this.esc(n)}</li>`).join("");
    this.$("#advice").classList.toggle("sound", advice.sound);
  }

  setOut() {
    const g = this.game, seed = this.$("#create-seed").value;
    this.$("#seed").value = seed;
    this.chosenKit = this.$("#kit").value || "pauper";
    g.newGame(seed, this.slots.map((s) => ({ cls: s.cls, name: s.name, stats: s.stats, row: s.row })), this.chosenKit, this.$("#difficulty").value, undefined, this.$("#mode").value);
  }

  startNew() { this.openCreate(); }

  renderCreateNote() {
    const seed = this.$("#create-seed").value, muts = CM.mutatorsFor(seed), d = CM.DIFFICULTIES[this.$("#difficulty").value] || CM.DIFFICULTIES.fair;
    this.$("#create-note").textContent = `${d.name}: ${d.what}.` + (muts.length ? ` Today's dungeon comes with ${muts.map((m) => `${CM.MUTATORS[m].name} (${CM.MUTATORS[m].what})`).join(" and ")}.` : "")
      + (this.$("#mode").value === "endless" ? " Endless: the fifty floors and the Lich King as ever, and then no bottom - the bands come round again, the guardians return as echoes every ten floors, and the dark deepens. The run goes on the Endless board, by depth." : "");
  }

  refreshTitle() {
    const g = this.game;
    this.$("#title-note").textContent = g.titleNote;
    const can = g.canContinue();
    this.$("#btn-continue").disabled = !can;
    this.$("#continue-note").textContent = can
      ? `Slot ${g.slot}: floor ${CM.runFloor(g.lastRun)}, ${g.lastRun.gold.toLocaleString()} gold${g.lastRun.saved ? ", saved " + new Date(g.lastRun.saved).toLocaleString() : ""}${g.lastRun.difficulty && g.lastRun.difficulty !== "fair" ? ", " + CM.DIFFICULTIES[g.lastRun.difficulty].name : ""}${g.lastRun.endless ? ", Endless" : ""}`
      : `Slot ${g.slot} is empty: no expedition is under way there.`;
    for (const b of this.root.querySelectorAll("#slots-row button[data-slot]")) {
      const n = Number(b.dataset.slot), r = (g.runs || [])[n - 1];
      b.classList.toggle("on", n === g.slot);
      b.textContent = `${n}: ${r && r.floor ? `floor ${CM.runFloor(r)}` : "empty"}`;
      b.title = r && r.floor ? `${r.gold.toLocaleString()} gold${r.saved ? ", saved " + new Date(r.saved).toLocaleString() : ""}` : "An empty slot for a new expedition";
    }
    const title = CM.titleFor(g.achievements), got = Object.keys(CM.ACHIEVEMENTS).filter((id) => g.achievements[id]);
    this.$("#honours").textContent = got.length ? `${CM.playerName || "Adventurer"} ${title} - ${got.length} of ${Object.keys(CM.ACHIEVEMENTS).length} achievements` : "";
    this.$("#achievements").innerHTML = Object.entries(CM.ACHIEVEMENTS).map(([id, a]) => { const t = g.achievements[id];
      return `<div class="unlock ${t ? "got" : ""}"><b>${t ? "✓" : "○"} ${a.name}</b> <small>${a.what}${t ? ` - ${this.esc(t.date)}; the title "${a.title}"` : ""}</small></div>`; }).join("");
    const bag = CM.startingBag(this.$("#seed").value || "x").filter((i) => i.kind !== "torch");
    this.$("#start-with").textContent = `Four set out with 30 gold, two torches and two potions (${bag.map((i) => i.name).join(" and ")} - the seed decides which). `
      + "New Expedition lets you name them, choose their callings and roll their stats; chests and fallen monsters give better gear; "
      + "a merchant's camp with a temple waits below floors 5, 10 and 15 (and every fifth floor of the Deep) - each shaft guarded by something that has made its lair over it, and leaves a relic when it falls. "
      + "The Lich King waits on floor 20; below him, thirty floors of the Deep go down to the Root of the World - or, in an Endless expedition, to no bottom at all.";
    const table = this.$("#fame table"), endlessBoard = this.fameBoard === "endless", board = endlessBoard ? (g.fameEndless || []) : g.fame;
    for (const b of this.root.querySelectorAll("#fame .boards button")) b.classList.toggle("on", (b.dataset.board === "endless") === endlessBoard);
    if (!board.length) table.innerHTML = `<tr><td class="empty">${endlessBoard ? "No Endless expedition yet: choose Endless when the party sets out." : "No party has gone down yet."}</td></tr>`;
    else table.innerHTML = board.map((e, i) => {
      const open = this.fameOpen === i, t = e.tally;
      let rows = `<tr class="row${open ? " open" : ""}" data-i="${i}" title="${open ? "" : "Click for the details"}"><td>${i + 1}.</td><td>${this.esc(e.name).slice(0, 14)}</td>`
        + `<td class="${e.won ? "won" : ""}">${endlessBoard ? `floor ${e.floor}${e.won ? " - crowned" : ""}` : e.bottom ? "TO THE BOTTOM" : e.won ? (e.floor > CM.LAST_FLOOR ? `SLEW THE LICH KING, floor ${e.floor}` : "SLEW THE LICH KING") : "floor " + e.floor}</td><td>${e.gold.toLocaleString()} gold${e.difficulty && e.difficulty !== "fair" && CM.DIFFICULTIES[e.difficulty] ? ` <i class="diff">${CM.DIFFICULTIES[e.difficulty].name}</i>` : ""}</td><td>${this.esc(e.date)}${e.daily ? " ☀" : ""}</td></tr>`;
      if (open) {
        rows += `<tr class="details"><td colspan="5"><div>${(e.party || []).length ? this.esc(e.party.join(", ")) : "An old entry: who went wasn't written down."}</div>`
          + (e.seed ? `<div>Seed <b>${this.esc(e.seed)}</b>${e.daily ? " (today's dungeon)" : ""}${e.kit && e.kit !== "pauper" && CM.KITS[e.kit] ? `, ${CM.KITS[e.kit].name}` : ""} <button data-seed="${this.esc(e.seed)}">Play this seed</button></div>` : "")
          + (t ? `<div>${CM.plural(t.kills || 0, "monster")} slain, ${CM.plural(t.chests || 0, "chest")} opened, ${CM.plural(t.steps || 0, "step")}, ${CM.plural(t.fights || 0, "fight")}${t.fled ? ` (${t.fled} fled)` : ""}.</div>` : "")
          + (t && t.guardians && t.guardians.length ? `<div>Guardians slain: ${this.esc(this.guardianNames(t.guardians))}.</div>` : "")
          + (e.mutators && e.mutators.length ? `<div>${e.endless ? "The dark deepened" : "Today's dungeon"}: ${this.esc(e.mutators.map((m) => (CM.MUTATORS[m] || { name: m }).name).join(", "))}.</div>` : "")
          + (e.titles && e.titles.length ? `<div>Earned: ${this.esc(e.titles.map((id) => (CM.ACHIEVEMENTS[id] || { name: id }).name).join(", "))}.</div>` : "")
          + `<div><button data-card="${i}">Summary card</button></div>`
          + "</td></tr>";
      }
      return rows;
    }).join("");
    const have = CM.unlocked(g.allFame), deep = CM.deepest(g.allFame);
    this.$("#unlocks").innerHTML = Object.entries(CM.KITS).map(([id, k]) => {
      const got = have.includes(id), need = k.need === 21 ? "slay the Lich King" : `reach floor ${k.need}`;
      return `<div class="unlock ${got ? "got" : ""}"><b>${got ? "✓" : "○"} ${k.name}</b> <small>${got ? k.what : `${k.what} <i>(${need}${deep.floor ? `; deepest so far: floor ${deep.floor}` : ""})</i>`}</small></div>`;
    }).join("");
    const trophies = g.trophies || {};
    this.$("#trophies").innerHTML = [...Object.entries(CM.GUARDIANS).filter(([, G]) => G.floor < CM.LAST_FLOOR).map(([id, G]) => [id, G.name, G.floor, G.lair.name]), ["lich", CM.BOSS.name, CM.LAST_FLOOR, "his palace"],
      ...Object.entries(CM.GUARDIANS).filter(([, G]) => G.floor > CM.LAST_FLOOR).map(([id, G]) => [id, G.name, G.floor, G.lair.name])].map(([id, name, floor, where]) => {
      const t = trophies[id];
      return `<div class="unlock ${t ? "got" : ""}"><b>${t ? "✓" : "○"} ${name}</b> <small>${t ? `slain ${this.esc(t.date)} by ${this.esc(t.name)}'s party` : `<i>floor ${floor}: ${where}</i>`}</small></div>`;
    }).join("");
    const kit = this.$("#kit");
    kit.innerHTML = have.map((id) => `<option value="${id}">${CM.KITS[id].name}</option>`).join("");
    if (this.chosenKit && have.includes(this.chosenKit)) kit.value = this.chosenKit;
    const todays = this.$("#seed").value === CM.dailySeed();
    this.$("#btn-daily").classList.toggle("on", todays);
  }

  icon(item, size = 22) {                                               // a thing's picture, by the theme
    const c = CM.art.itemIcon(item, size, this.game.settings.look);
    c.className = "icon";
    return c;
  }

  esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

  // ---- settings ----
  // how much of the browser's keeping the game uses: the runs are small now, but a browser gives a site about 5 MB in all
  showStorage() {
    const used = CM.store.used(), kb = Math.round(used / 1024);
    this.$("#set-storage").textContent = `Saved in this browser: ${kb < 1 ? "under 1" : kb.toLocaleString()} KB (runs, the Hall of Fame, settings).${used > 3.5 * 1024 * 1024 ? " That is close to what a browser allows: Export your runs to keep them safe." : ""}  Claude and Magic v${CM.version}, built ${CM.built}.`;
  }
  _settings() {
    const g = this.game, s = g.settings;
    const sound = this.$("#set-sound"), vol = this.$("#set-volume"), music = this.$("#set-music"), mvol = this.$("#set-music-volume");
    const smooth = this.$("#set-smooth"), fps = this.$("#set-fps"), look = this.$("#set-look"), titleLook = this.$("#look"), tap = this.$("#set-tap");
    const speed = this.$("#set-speed"), text = this.$("#set-text"), motion = this.$("#set-motion"), contrast = this.$("#set-contrast"), swapab = this.$("#set-swapab");
    speed.value = s.speed || "normal"; text.value = s.text || "normal"; motion.checked = Boolean(s.motion); contrast.checked = Boolean(s.contrast); swapab.checked = Boolean(s.swapAB);
    for (const sel of [look, titleLook]) sel.innerHTML = Object.entries(CM.LOOKS).map(([id, l]) => `<option value="${id}">${l.name}</option>`).join("");
    sound.checked = s.sound; vol.value = Math.round(s.volume * 100); music.checked = s.music !== false; mvol.value = Math.round((s.musicVolume === undefined ? 0.5 : s.musicVolume) * 100);
    smooth.checked = s.smooth; fps.checked = s.fps; look.value = titleLook.value = s.look || "drawn"; tap.checked = s.tapMove !== false;
    const note = () => { this.$("#set-look-note").textContent = CM.LOOKS[s.look] ? CM.LOOKS[s.look].what + "." : ""; };
    note();
    const apply = () => {
      s.sound = sound.checked; s.volume = vol.value / 100; s.music = music.checked; s.musicVolume = mvol.value / 100; s.smooth = smooth.checked; s.fps = fps.checked; s.tapMove = tap.checked;
      s.speed = speed.value; s.text = text.value; s.motion = motion.checked; s.contrast = contrast.checked; s.swapAB = swapab.checked;
      g.saveSettings();
      g.emit("settings", s);
    };
    for (const el of [sound, vol, music, mvol, smooth, fps, tap, motion, contrast, swapab]) el.addEventListener("input", apply);
    for (const el of [speed, text]) el.addEventListener("change", apply);
    for (const sel of [look, titleLook]) sel.addEventListener("change", () => { s.look = sel.value; look.value = titleLook.value = s.look; note(); apply(); });
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
    const light = this.$("#side .light"), l = g.light || {};
    let lit = l.kind === "lantern" ? "Lantern lit" : l.kind === "torch" ? (l.left > 40 ? `Torch: ${l.left} steps left` : `Torch burning low: ${l.left}`) : "No light!";
    if (g.spellLight > 0) lit += ` - conjured light: ${g.spellLight} steps`;
    if (fl && g.inDark()) lit += " - a magical dark";
    light.textContent = lit;
    light.classList.toggle("dark", !g.hasLight() || g.inDark());
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
        adventurer: "Someone bound. Space cuts them loose.", rope: "A rope from above. Space climbs it." }[thing.type] || "";
      else if (f && f.type === "plate" && (f.gate || f.known)) text = f.gate ? (f.pressed ? "A pressure plate, sunk." : "A pressure plate.") : "A plate that was a trap.";
      else if (f && f.type === "fountain") text = f.used ? "A dry fountain." : "A fountain. Space drinks.";
      else if (f && f.type === "altar") text = f.used ? "A quiet altar." : "An altar. Space kneels.";
      else if (ahead && ahead.type === "door" && !ahead.open) text = ahead.riddle !== undefined ? "A door written over with runes. Walk into it, and answer." : ahead.locked ? "A locked door. Walk into it with a key." : "A door. Walk into it to open it.";
      else if (ahead && ahead.type === "gate" && !ahead.open) text = "A portcullis. Find its lever.";
      hint.textContent = text;
    }
    this.renderParty();
    this.renderLog();
    this.renderActions();
    if (this.$("#dlg-sheet").classList.contains("on")) this.renderSheet();
    this.drawAutomap(this.$("#automap"));
    if (this.$("#bigmap").classList.contains("on")) this.drawAutomap(this.$("#bigmap-canvas"));
  }

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
  }

  renderLog() {
    const log = this.$("#log");
    const lines = this.game.messages.slice(-7);
    log.innerHTML = lines.map((l) => `<div>${this.esc(l)}</div>`).join("");
  }

  renderActions() {
    const g = this.game, box = this.$("#actions");
    if (g.mode === "combat") { this.renderCombat(); return; }
    box.classList.remove("combat");
    const sets = {
      explore: [["◄ Turn", () => g.turn(-1)], ["▲ Forward", () => g.move(0)], ["▼ Back", () => g.move(2)], ["Turn ►", () => g.turn(1)],
        ["Use (Space)", () => g.use()], ["Explore (X)", () => (g.travel ? g.stopTravel() : g.explore())], ["Cast (C)", () => this.outsideCast()], ["Inventory (I)", () => g.openBag()], ["Journal (J)", () => this.openJournal()], ["Map (Tab)", () => this.toggleBigMap()],
        ["Menu (Esc)", () => this.openDialog("#dlg-pause")]],
      camp: [["Merchant", () => g.openBag(true)], ["Rest (20 gold)", () => g.rest()], ["Temple", () => this.openDialog("#dlg-temple")],
        ["Tavern", () => this.openTavern()], ["Smith", () => this.openSmith()], ["Vault", () => this.openVault()], ["Waystone", () => this.openWaystone()], ["Cast (C)", () => this.outsideCast()], ["Inventory", () => g.openBag()], ["Journal (J)", () => this.openJournal()],
        ["Back up the shaft", () => g.backUp()], ["Go deeper", () => g.leaveCamp()], ["Menu (Esc)", () => this.openDialog("#dlg-pause")]],
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
  }

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
  }
  outsideCast() { this.xmenu = { kind: "list" }; this.refresh(); }
  outsidePick(ch) {
    const a = CM.ABILITIES[ch.id];
    if (a.target === "ally" || a.target === "fallen") { this.xmenu = { kind: "ally", id: ch.id, hero: ch.hi, fallen: a.target === "fallen" }; this.refresh(); return; }
    this.game.castOutside(ch.hi, ch.id, null);
    this.closeMenu();
  }
  outsideAlly(i) { const m = this.xmenu; this.game.castOutside(m.hero, m.id, i); this.closeMenu(); }
  closeMenu() { this.xmenu = null; this.refresh(); }
  pickOutside(n) {
    const buttons = [...this.$("#actions").querySelectorAll("button.pick")], b = buttons[n - 1];
    if (b && !b.disabled) { b.click(); return true; }
    return false;
  }

  // ---- the fight: whose turn it is, what they'll do, at whom ----
  renderCombat() {
    const g = this.game, box = this.$("#actions"), c = g.combat || {}, h = c.waiting;
    box.classList.add("combat");
    box.dataset.mode = "combat";
    box.innerHTML = "";
    const turn = document.createElement("div");
    turn.className = "turn";
    turn.innerHTML = h ? `Round ${c.round || 1} <small>-</small> ${this.esc(h.name)}'s turn` : `Round ${c.round || 1} <small>- the foes move</small>`;
    box.appendChild(turn);
    const menu = document.createElement("div");
    menu.className = "menu";
    const btn = (html, fn, disabled, cls) => {
      const b = document.createElement("button");
      b.innerHTML = html;
      b.disabled = Boolean(disabled);
      if (cls) b.className = cls;
      b.addEventListener("click", fn);
      menu.appendChild(b);
      return b;
    };
    const cm = this.cmenu || { kind: "main" };
    if (h && cm.kind === "main") {
      btn("<kbd>F</kbd>Fight", () => g.act("fight", g.target));
      btn("<kbd>C</kbd>Cast / Skill", () => this.combatMenu("cast"), !CM.abilitiesFor(h).length);
      btn("<kbd>P</kbd>Item", () => this.combatMenu("item"));
      btn("<kbd>D</kbd>Defend", () => g.act("defend"));
      btn("<kbd>R</kbd>Run", () => g.act("run"));
      btn(`<kbd>A</kbd>${c.auto ? "Stop auto" : "Auto"}`, () => g.autoFight(!c.auto), false, c.auto ? "on" : "");
    } else if (h && cm.kind === "cast") {
      CM.abilitiesFor(h).forEach((id, i) => {
        const a = CM.ABILITIES[id], used = a.once && h.used && h.used[id], poor = h.mp < a.mp, est = g.spellEstimate(h, id);
        const b = btn(`<kbd>${i + 1}</kbd>${a.name}<small>${a.mp ? a.mp + " MP - " : ""}${used ? "used this fight" : a.what}${est ? ` <i>(${est})</i>` : ""}</small>`, () => this.castPick(id), used || poor, "pick");
        const ic = CM.art.spellIcon(id, 18, g.settings.look);
        if (ic) { ic.className = "icon"; b.insertBefore(ic, b.firstChild.nextSibling); }
      });
      btn("<kbd>Esc</kbd>Back", () => this.combatMenu("main"));
    } else if (h && cm.kind === "item") {
      const rows = this.usableRows();
      rows.forEach((row, i) => btn(`<kbd>${i + 1}</kbd>${this.esc(g.bag[row].name)}<small>${g.describe(g.bag[row])}</small>`, () => this.itemPick(row), false, "pick"));
      if (!rows.length) { const none = document.createElement("span"); none.className = "small"; none.textContent = "Nothing in the pack for a fight."; menu.appendChild(none); }
      btn("<kbd>Esc</kbd>Back", () => this.combatMenu("main"));
    } else if (h && cm.kind === "ally") {
      g.party.forEach((p, i) => btn(`<kbd>${i + 1}</kbd>${this.esc(p.name)}<small>${p.hp <= 0 ? "fallen" : `${p.hp}/${p.max}`}</small>`,
        () => this.allyPick(i), cm.fallen ? p.hp > 0 : p.hp <= 0, "pick"));
      btn("<kbd>Esc</kbd>Back", () => this.combatMenu("main"));
    }
    box.appendChild(menu);
    const targets = document.createElement("div");
    targets.className = "targets";
    g.living().forEach((m, i) => {
      const b = document.createElement("button");
      b.className = i === (g.target || 0) ? "chosen" : "";
      const est = h ? g.strikeEstimate(h, m) : null;
      b.innerHTML = `${this.esc(m.name)} <small>${Math.max(0, m.hp)}/${m.max}${m.asleep > 0 ? " - asleep" : ""}${m.held > 0 ? " - held" : ""}${m.marked ? " - marked" : ""}${m.blind > 0 ? " - blinded" : ""}${m.burning > 0 ? " - burning" : ""}</small>${est ? `<i class="odds">${Math.round(est.hit * 100)}% to hit, ${est.low}-${est.high}</i>` : ""}`;
      b.addEventListener("click", () => g.setTarget(i));
      targets.appendChild(b);
    });
    box.appendChild(targets);
  }

  // ---- the tavern ----
  openTavern() {
    this.renderTavern();
    this.openDialog("#dlg-tavern");
  }

  renderTavern() {
    const g = this.game, box = this.$("#recruits");
    const fallen = g.party.map((h, i) => i).filter((i) => g.party[i].hp <= 0 || (g.party[i].status || {}).stone);
    box.innerHTML = "";
    g.tavern().forEach((r, i) => {
      const div = document.createElement("div");
      div.className = "recruit";
      div.appendChild(this.portrait(r.cls, 40));
      const text = document.createElement("div");
      text.innerHTML = `<b>${this.esc(r.name)}</b> the ${r.cls}, level ${r.level} <small>${r.max} health${r.maxmp ? `, ${r.maxmp} magic` : ""}, attack ${r.atk}, defence ${r.df} - ${CM.STATS.map((s) => `${CM.STAT_NAMES[s].slice(0, 3)} ${r.stats[s]}`).join(" ")}</small>`;
      div.appendChild(text);
      const hire = document.createElement("div");
      hire.className = "hire";
      if (fallen.length <= 1) {
        const b = document.createElement("button");
        b.textContent = r.price ? `Hire, ${r.price} gold` : "Hire - owes you their life";
        b.disabled = !fallen.length;
        b.addEventListener("click", () => { const note = g.hire(i); this.$("#tavern-note").textContent = note || `${r.name} comes along.`; this.renderTavern(); this.refresh(); });
        hire.appendChild(b);
      } else {
        for (const idx of fallen) {
          const b = document.createElement("button");
          b.textContent = r.price ? `For ${g.party[idx].name}, ${r.price} gold` : `For ${g.party[idx].name} - owes you their life`;
          b.addEventListener("click", () => { const note = g.hire(i, idx); this.$("#tavern-note").textContent = note || `${r.name} comes along.`; this.renderTavern(); this.refresh(); });
          hire.appendChild(b);
        }
      }
      div.appendChild(hire);
      box.appendChild(div);
    });
    if (!box.children.length) box.innerHTML = "<div class='small'>The benches are empty tonight.</div>";
    this.$("#tavern-note").textContent = fallen.length ? "" : "The party is whole; the recruits drink to that.";
  }

  combatMenu(kind, data) { this.cmenu = Object.assign({ kind }, data || {}); this.renderCombat(); }
  usableRows() { return this.game.bag.map((it, i) => (["heal", "mana", "antidote", "revive"].includes(it.kind) ? i : -1)).filter((i) => i >= 0); }

  castPick(id) {
    const g = this.game, a = CM.ABILITIES[id];
    if (a.target === "ally" || a.target === "fallen") { this.combatMenu("ally", { id, fallen: a.target === "fallen" }); return; }
    g.act("cast", a.target === "foe" ? { id, target: g.target } : { id });
    this.refresh();
  }

  itemPick(row) { this.combatMenu("ally", { row, fallen: this.game.bag[row].kind === "revive" }); }

  allyPick(i) {
    const cm = this.cmenu || {};
    if (cm.row !== undefined) this.game.act("item", { row: cm.row, who: i });
    else this.game.act("cast", { id: cm.id, target: i });
    this.refresh();
  }

  // a number key in a fight: the chosen foe, or a pick from the open list
  pick(n) {
    const g = this.game, cm = this.cmenu || { kind: "main" };
    if (cm.kind === "main") { g.setTarget(n - 1); return true; }
    const buttons = [...this.$("#actions .menu").querySelectorAll("button.pick")], b = buttons[n - 1];
    if (b && !b.disabled) { b.click(); return true; }
    return false;
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
    const colours = { chest: "#C08030", ladder: "#3060C0", monsters: "#C03030", boss: "#8030C0", guardian: "#A02050", key: "#D8B040",
      ghost: "#A0C8E8", hermit: "#C8A060", adventurer: "#E8C890", bones: "#D8D0B8", rope: "#B08040" };
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
        else if (thing.type === "ladder") p.fillRect(cx - cell * 0.3, cy - cell * 0.3, cell * 0.6, cell * 0.6);
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
  }

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
  }

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
  }

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
  }

  guardianNames(ids) { return ids.map((id) => (CM.GUARDIANS[id] || { name: id }).name.replace(/^The /, "the ")).join(", "); }




  // ---- ways to play: the keys as set, the summary card, the gamepad's focus, a tap on the view ----
  renderKeys() {
    const g = this.game, keys = this.$("#dlg-keys table"), k = g.settings.keys || CM.DEFAULT_KEYS;
    keys.innerHTML = CM.KEY_ACTIONS.map(([id, what]) => `<tr data-action="${id}"><td><kbd>${this.esc(CM.keyName(k[id]))}</kbd>${this.rebinding === id ? " <i>press a key...</i>" : ""}</td><td>${what}</td><td><button data-rebind="${id}">Change</button></td></tr>`).join("")
      + `<tr><td><kbd>Arrows</kbd></td><td>move and turn as well, always</td><td></td></tr><tr><td><kbd>1 - 4</kbd></td><td>a hero's sheet; in a list, the pick</td><td></td></tr>`
      + `<tr><td><kbd>Esc</kbd></td><td>close a screen / pause</td><td></td></tr><tr><td><kbd>F3</kbd></td><td>frames per second</td><td></td></tr>`
      + `<tr><td colspan="3" class="small" style="white-space: normal; max-width: 560px; padding-top: 8px">A gamepad works too: the stick or pad moves, A uses or picks, B steps back, X the pack, Y casts, the shoulders sidestep or pick targets, Start pauses, Select the map. On a touch screen, tap the view: the sides turn, the top walks, the bottom steps back.</td></tr>`;
    for (const b of keys.querySelectorAll("button[data-rebind]")) b.addEventListener("click", () => { this.rebinding = this.rebinding === b.dataset.rebind ? null : b.dataset.rebind; this.renderKeys(); });
  }
  rebind(action, code) {
    const g = this.game, k = g.settings.keys || (g.settings.keys = Object.assign({}, CM.DEFAULT_KEYS));
    if (!CM.DEFAULT_KEYS[action] || !code || code === "Escape" || /^F\d+$/.test(code)) { this.rebinding = null; this.renderKeys(); return false; }
    for (const other of Object.keys(k)) if (k[other] === code && other !== action) k[other] = CM.DEFAULT_KEYS[other] === code ? "" : CM.DEFAULT_KEYS[other];   // (one key, one action)
    k[action] = code;
    this.rebinding = null;
    g.saveSettings();
    g.emit("settings", g.settings);
    this.renderKeys();
    return true;
  }
  resetKeys() { this.game.settings.keys = Object.assign({}, CM.DEFAULT_KEYS); this.rebinding = null; this.game.saveSettings(); this.game.emit("settings", this.game.settings); this.renderKeys(); }

  openCard(entry) {
    const g = this.game, e = entry || g.fame[0];
    if (!e) return;
    this.cardEntry = e;
    const slot = this.$("#card-slot");
    slot.innerHTML = "";
    slot.appendChild(CM.art.summaryCard(e, CM.titleFor(g.achievements)));
    this.$("#card-text").value = CM.summaryText(e);
    this.$("#card-note").textContent = "";
    this.openDialog("#dlg-card");
  }
  copyText(text, noteEl) {
    const done = navigator.clipboard ? navigator.clipboard.writeText(text).then(() => true, () => false) : Promise.resolve(false);
    done.then((ok) => { if (noteEl) noteEl.textContent = ok ? "Copied." : "Select the text and copy it yourself."; });
    return done;
  }

  // a gamepad's way through buttons: the focus moves along the visible ones, A presses
  padTargets() {
    const open = this.root.querySelector(".dialog.on .box");
    const scope = open || (this.xmenu || (this.game.mode === "combat" && this.cmenu && this.cmenu.kind !== "main") ? this.$("#actions") : null);
    if (!scope) return [];
    return [...scope.querySelectorAll("button")].filter((b) => !b.disabled && b.offsetParent !== null);
  }
  padFocus(delta) {
    const list = this.padTargets();
    for (const b of this.root.querySelectorAll(".padfocus")) b.classList.remove("padfocus");
    if (!list.length) { this.padIndex = -1; return null; }
    this.padIndex = ((this.padIndex === undefined || this.padIndex < 0 ? (delta > 0 ? -1 : 0) : this.padIndex) + delta + list.length) % list.length;
    const b = list[this.padIndex];
    b.classList.add("padfocus");
    if (b.scrollIntoView) b.scrollIntoView({ block: "nearest" });
    return b;
  }
  padPress() {
    const list = this.padTargets();
    if (!list.length) return false;
    const b = list[this.padIndex >= 0 && this.padIndex < list.length ? this.padIndex : 0];
    b.click();
    this.padIndex = -1;
    return true;
  }
  // a tap (or a click) on the view, out of a fight: the sides turn, the top walks, the bottom steps back
  tapView(fx, fy) {
    const g = this.game;
    if (g.mode !== "explore" || !g.settings.tapMove || this.dialogOpen()) return false;
    if (fx < 0.3) g.turn(-1); else if (fx > 0.7) g.turn(1); else if (fy < 0.65) g.move(0); else g.move(2);
    return true;
  }


  // the Lich King is slain: the victory, and the choice - into the daylight, or down into the Deep
  showCrowning() {
    const g = this.game, dlg = this.$("#dlg-over");
    this.overEntry = null;
    const slot = this.$("#dlg-over .emblem-slot");
    slot.innerHTML = "";
    slot.appendChild(CM.art.emblem(120));
    dlg.classList.add("won"); dlg.classList.add("crowning");
    this.$("#over-title").textContent = "The Lich King is no more";
    const standing = g.party.filter((h) => h.hp > 0), names = (list) => (list.length ? list.map((h) => h.name).join(", ").replace(/, ([^,]*)$/, " and $1") : "The party");
    this.$("#over-text").textContent = `The crown rolls from the throne, and the cold goes out of the stone. ${names(standing)} stand in the throne room with the Lich King's crown and ${g.gold.toLocaleString()} gold. `
      + "Behind the throne the floor has split: a shaft goes down into a dark that was never his. The carvings never spoke of it. Climb into the daylight as legends - or go down, and see what the king was listening to.";
    const roll = this.$("#over-party");
    roll.innerHTML = "";
    for (const h of g.party) {
      const div = document.createElement("div");
      div.className = h.hp > 0 ? "standing" : "fallen";
      div.appendChild(this.portrait(h.cls, 56));
      const who = document.createElement("div");
      who.innerHTML = `<b>${this.esc(h.name)}</b><small>${h.cls}, level ${h.level}</small><small class="fate">${h.hp > 0 ? "stands" : "fell"}</small>`;
      div.appendChild(who);
      roll.appendChild(div);
    }
    const t = g.tally || {};
    this.$("#over-tally").innerHTML = [["Floors", `${CM.LAST_FLOOR} of ${CM.LAST_FLOOR} - and ${g.endless ? "no bottom" : (CM.BOTTOM - CM.LAST_FLOOR) + " more"} below`], ["Gold", g.gold.toLocaleString()], ["Monsters slain", t.kills || 0],
      ["Steps walked", (t.steps || 0).toLocaleString()], ["Guardians slain", (t.guardians || []).length ? this.guardianNames(t.guardians) : "none"]].map(([k, v]) => `<div><span>${k}</span><b>${this.esc(v)}</b></div>`).join("");
    this.openDialog("#dlg-over");
    this.ending = "victory";
    if (this.onEnding) this.onEnding();
  }

  // ---- the camp's smith and vault ----
  openSmith() { this.renderSmith(); this.openDialog("#dlg-smith"); }
  renderSmith() {
    const g = this.game, box = this.$("#smith-list");
    const diamonds = g.bag.filter((i) => i.kind === "gem" && i.gem === "diamond").length;
    const gems = g.bag.filter((i) => i.kind === "gem" && CM.GEMS[i.gem].element).map((i) => i.name);
    this.$("#smith-gems").textContent = `In the pack: ${diamonds ? CM.plural(diamonds, "diamond") : "no diamond"}${gems.length ? ", " + gems.join(", ") : ""}. Gold: ${g.gold.toLocaleString()}.`;
    box.innerHTML = "";
    g.party.forEach((h, hi) => {
      for (const slot of ["weapon", "armor", "offhand", "helm"]) {
        const it = h[slot];
        if (!it) continue;
        const row = document.createElement("div");
        row.className = "recruit";
        row.appendChild(this.icon(it, 22));
        const text = document.createElement("div");
        const n = (it.props || {}).enchant || 0;
        text.innerHTML = `<b>${this.esc(it.unknown ? CM.baseName(it) : it.name)}</b> <small>${this.esc(h.name)}'s ${CM.SLOT_NAMES[slot].toLowerCase()} - ${this.esc(CM.itemLabel(it))}${n ? ` - the smith's work: +${n}` : ""}</small>`;
        row.appendChild(text);
        const act = document.createElement("div");
        act.className = "hire";
        const b = document.createElement("button");
        b.textContent = n >= CM.SMITH.most ? "Worked to the limit" : `+1 for ${CM.SMITH.enchant * (n + 1)} gold and a diamond`;
        b.disabled = n >= CM.SMITH.most || !diamonds || g.gold < CM.SMITH.enchant * (n + 1) || it.unknown;
        b.addEventListener("click", () => { this.$("#smith-note").textContent = g.smith("enchant", hi, slot) || "Done."; this.renderSmith(); this.refresh(); });
        act.appendChild(b);
        if (slot === "weapon") {
          const s = document.createElement("button");
          s.textContent = `Set a gem for ${CM.SMITH.gem} gold`;
          s.disabled = !gems.length || g.gold < CM.SMITH.gem || it.unknown;
          s.title = "The first ruby, sapphire or sunstone in the pack goes in: fire, frost or holiness";
          s.addEventListener("click", () => { this.$("#smith-note").textContent = g.smith("gem", hi, slot) || "Done."; this.renderSmith(); this.refresh(); });
          act.appendChild(s);
        }
        row.appendChild(act);
        box.appendChild(row);
      }
    });
  }
  openVault() { this.renderVault(); this.openDialog("#dlg-vault"); }
  renderVault() {
    const g = this.game, held = this.$("#vault-held"), list = this.$("#vault-list");
    held.innerHTML = "";
    if (g.vault) {
      held.appendChild(this.icon(g.vault, 22));
      const text = document.createElement("span");
      text.innerHTML = `<b>${this.esc(g.vault.name)}</b> <small>${this.esc(CM.itemLabel(g.vault))}</small> `;
      held.appendChild(text);
      const b = document.createElement("button");
      b.textContent = "Take it";
      b.addEventListener("click", () => { this.$("#vault-note").textContent = g.takeHeirloom() || "Taken."; this.renderVault(); this.refresh(); });
      held.appendChild(b);
    } else held.innerHTML = `<span class="small">The vault is empty. Leave something here, and the next party to come this way will find it.</span>`;
    list.innerHTML = "";
    g.bag.forEach((it, i) => {
      if (["key", "bones", "rope", "torch"].includes(it.kind)) return;
      const row = document.createElement("div");
      row.className = "recruit";
      row.appendChild(this.icon(it, 22));
      const text = document.createElement("div");
      text.innerHTML = `<b>${this.esc(it.unknown ? CM.baseName(it) : it.name)}</b> <small>${this.esc(CM.itemLabel(it))}</small>`;
      row.appendChild(text);
      const act = document.createElement("div");
      act.className = "hire";
      const b = document.createElement("button");
      b.textContent = g.vault ? "Leave it (swap)" : "Leave it";
      b.addEventListener("click", () => { this.$("#vault-note").textContent = g.leaveHeirloom(i) || "Left for those who come after."; this.renderVault(); this.refresh(); });
      act.appendChild(b);
      row.appendChild(act);
      list.appendChild(row);
    });
    if (!list.children.length) list.innerHTML = `<div class="small">Nothing in the pack worth the keeping.</div>`;
  }

  // ---- the dungeon's people and puzzles: a word with someone, a riddle at a door, the journal ----
  askRiddle(k) {
    const g = this.game, f = g.floor.features[k], r = f && CM.RIDDLES[f.riddle];
    if (!r) return;
    const rnd = new CM.Random(CM.hashSeed(`${g.seed}:riddle:${k}:${f.tries || 0}`));
    this.riddle = { k, answers: rnd.shuffle([r.a, ...r.wrong]) };
    this.$("#riddle-q").textContent = r.q;
    const box = this.$("#riddle-answers");
    box.innerHTML = "";
    this.riddle.answers.forEach((a, i) => {
      const b = document.createElement("button");
      b.innerHTML = `<kbd>${i + 1}</kbd>${this.esc(a)}`;
      b.addEventListener("click", () => this.pickRiddle(i + 1));
      box.appendChild(b);
    });
    this.openDialog("#dlg-riddle");
  }
  pickRiddle(n) {
    const r = this.riddle;
    if (!r || !r.answers[n - 1]) return;
    this.closeDialogs();
    this.game.answerRiddle(r.k, r.answers[n - 1]);
    this.riddle = null;
    this.refresh();
  }
  openJournal() {
    const g = this.game, box = this.$("#journal-list"), entries = g.journal || [];
    const part = (title, kind, order) => {
      const list = entries.filter((e) => e.kind === kind).sort(order || ((a, b) => a.floor - b.floor));
      if (!list.length) return "";
      return `<div class="list-title">${title}</div>` + list.map((e) => `<div class="entry"><small>${e.floor ? `Floor ${e.floor}` : ""}${e.who ? ` - ${this.esc(e.who)}` : ""}</small><p>${this.esc(e.text)}</p></div>`).join("");
    };
    const html = part("Carved into the stone", "carving") + part("What the dead said", "ghost") + part("Riddles answered", "riddle");
    box.innerHTML = html || `<div class="small">Nothing yet. Read the walls (Space before a carving), and listen to whoever you meet; the hermit pays for stories.</div>`;
    this.openDialog("#dlg-journal");
  }

  // a wash of colour over the view that fades (a spell's light, a trap's gas)
  tint(colour, ms = 260) {
    if (CM.reducedMotion) return;
    const el = this.$("#view .tint");
    clearTimeout(this.tintTimer);
    el.style.transition = "none"; el.style.background = colour; el.style.opacity = "1";
    this.tintTimer = setTimeout(() => { el.style.transition = `opacity ${ms}ms ease-out`; el.style.opacity = "0"; }, 40);
  }

  // a hero's card jolts or glows for a moment
  cardFx(i, cls, ms = 700) {
    const card = this.$("#party").children[i];
    if (!card || (CM.reducedMotion && cls === "jolt")) return;
    card.classList.remove(cls);
    void card.offsetWidth;                                               // (so the animation starts again)
    card.classList.add(cls);
    setTimeout(() => card.classList.remove(cls), ms);
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
    this.$("#btn-sort").addEventListener("click", () => { g.sortBag(); this.bagRow = -1; this.fillBag(); });
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
        row.appendChild(this.icon(item));
        const text = document.createElement("span");
        text.innerHTML = `${this.esc(item.unknown ? CM.baseName(item) : item.name)} <span class="what">${describe(item)}</span>`;
        row.appendChild(text);
        row.addEventListener("click", () => { onPick(i); this.fillBag(); });
        el.appendChild(row);
      });
    };
    list(this.$("#bag-list"), g.identifying ? "Your pack - pick the unknown thing to identify" : "Your pack", g.bag, this.bagRow,
      (i) => `(${g.describe(i)}, worth ${i.unknown ? 10 : Math.floor(i.value / 2)} gold)`,
      (i) => { if (g.identifying) this.note(g.identify(i)); else this.bagRow = i; });
    if (shop) list(this.$("#shop-list"), "The merchant's wares", g.stock || [], this.shopRow,
      (i) => (i.kind === "weapon" || i.kind === "armor" ? `(+${i.power})  -  ${i.value} gold` : `-  ${i.value} gold`), (i) => { this.shopRow = i; });
    const picked = this.bagRow >= 0 ? g.bag[this.bagRow] : null;
    const verb = !picked ? "Give to" : ["weapon", "armor", "shield", "helm", "ring", "amulet"].includes(picked.kind) ? "Equip on" : picked.kind === "scroll" || picked.kind === "tome" ? "Read" : picked.kind === "wand" ? "Use on" : "Give to";
    this.$("#bag-give").querySelectorAll("button").forEach((b, i) => {
      const m = g.party[i], cmp = picked ? g.compare(m, picked) : null;
      b.innerHTML = `${verb} ${this.esc(m.name)}` + (m.hp <= 0 ? " (fallen)" : "") + (cmp ? ` <i class="cmp ${cmp.cls}">${this.esc(cmp.text)}</i>` : "");
      b.title = cmp && cmp.why ? cmp.why : "";
    });
    const base = "Pick something from your pack, then who should equip or use it. A hero's sheet (1-4) takes things off." + (shop ? "  Pick from the merchant's wares (right) to Buy." : "");
    this.$("#bag-note").dataset.base = base;
    if (!this.$("#bag-note").textContent) this.$("#bag-note").textContent = base;
  }
};
