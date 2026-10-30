"use strict";
// The title: what you set out with, the Hall of Fame and its boards, unlocks, trophies, the memorial, the summary card.
Object.assign(CM.UI.prototype, {
  // ---- the title ----
  _title() {
    const g = this.game;
    this.$("#seed").value = CM.randomSeed();
    this.$("#btn-dice").addEventListener("click", () => { this.$("#seed").value = CM.randomSeed(); });
    this.$("#btn-new").addEventListener("click", () => this.openCreate());
    this.$("#btn-continue").addEventListener("click", () => g.continueRun());
    this.$("#btn-settings").addEventListener("click", () => this.openDialog("#dlg-settings"));
    this.$("#btn-village").addEventListener("click", () => this.openVillage());
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
    this.$("#btn-link").addEventListener("click", () => this.makeLink("save", g.exportText(), this.$("#transfer-text"), this.$("#transfer-note")));
    this.$("#btn-film-link").addEventListener("click", () => { const t = this.$("#film-text"); if (!CM.parseFilm(t.value)) { this.$("#film-note").textContent = "That isn't a film code (CM2:...)."; return; } this.makeLink("film", t.value.trim(), t, this.$("#film-note")); });
    this.$("#btn-stats").addEventListener("click", () => this.openStats());
    for (const b of this.root.querySelectorAll("#dlg-journal .boards button")) b.addEventListener("click", () => { this.journalPage = b.dataset.page; this.openJournal(); });
    this.$("#btn-install").addEventListener("click", () => { const p = this.installPrompt; if (!p) return; this.installPrompt = null; this.showInstall(false); p.prompt(); });
    this.$("#btn-import").addEventListener("click", () => {
      const err = g.importText(this.$("#transfer-text").value);
      this.$("#transfer-note").textContent = err || "Imported.";
      this.refreshTitle();
    });
    this.$("#fame table").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-seed]");
      if (b) { this.$("#seed").value = b.dataset.seed; this.refreshTitle(); return; }
      const fb = e.target.closest("button[data-film]");
      if (fb) { const f = (CM.store.get("films", []) || []).find((x) => x.key === fb.dataset.film); if (f) this.watch(Object.assign({}, f.spec, { log: CM.unpackLog(f.spec.log) })); return; }
      const c = e.target.closest("button[data-card]");
      if (c) { const b = this.fameBoard === "weekly" ? g.fame.concat(g.fameEndless || []).filter((x) => x.seed === CM.weeklySeed()) : this.fameBoard === "endless" ? g.fameEndless : g.fame; this.openCard(b[Number(c.dataset.card)]); return; }
      const tr = e.target.closest("tr.row");
      if (!tr) return;
      const i = Number(tr.dataset.i);
      this.fameOpen = this.fameOpen === i ? -1 : i;
      this.refreshTitle();
    });
    this.renderClasses();
  },

  renderClasses() {
    const classes = this.$("#classes"), g = this.game;
    classes.innerHTML = "";
    for (const cls of CM.ALL_CLASSES) {
      const c = CM.CLASSES[cls], div = document.createElement("div"), locked = !g.classUnlocked(cls);
      div.className = "calling" + (locked ? " locked" : "");
      div.appendChild(this.portrait(cls, 30));
      const text = document.createElement("div");
      text.innerHTML = `<b>${cls}</b> <small>${c.role}${c.cast ? `, casts ${CM.CASTS[c.cast]}` : ""}.</small> <small>${locked ? `<i>Earned: ${this.esc(CM.CLASS_UNLOCK[cls].what)}.</i> ` : ""}${c.blurb}</small>`;
      div.appendChild(text);
      classes.appendChild(div);
    }
  },

  // the theme changed (or its pack arrived): every portrait and icon is drawn again
  restyle() {
    this.portraits = {};
    this.renderClasses();
    if (this.screen === "create") this.renderCreate();
    this.$("#party").dataset.signature = "";
    if (this.screen === "bag") this.fillBag();
    if (this.$("#dlg-tavern").classList.contains("on")) this.renderTavern();
    this.refresh();
  },

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
    const table = this.$("#fame table"), weeklyBoard = this.fameBoard === "weekly", endlessBoard = this.fameBoard === "endless";
    const board = weeklyBoard ? g.fame.concat(g.fameEndless || []).filter((e) => e.seed === CM.weeklySeed()).sort((a, b) => (b.bottom ? 1 : 0) - (a.bottom ? 1 : 0) || (b.won ? 1 : 0) - (a.won ? 1 : 0) || b.floor - a.floor || b.gold - a.gold) : endlessBoard ? (g.fameEndless || []) : g.fame;
    for (const b of this.root.querySelectorAll("#fame .boards button")) b.classList.toggle("on", b.dataset.board === (this.fameBoard || "dungeon"));
    if (!board.length) table.innerHTML = `<tr><td class="empty">${weeklyBoard ? `No run on this week's seed yet (${CM.weeklySeed()}): This week's, on the left, sets it.` : endlessBoard ? "No Endless expedition yet: choose Endless when the party sets out." : "No party has gone down yet."}</td></tr>`;
    else table.innerHTML = board.map((e, i) => {
      const open = this.fameOpen === i, t = e.tally;
      let rows = `<tr class="row${open ? " open" : ""}" data-i="${i}" title="${open ? "" : "Click for the details"}"><td>${i + 1}.</td><td>${this.esc(e.name).slice(0, 14)}</td>`
        + `<td class="${e.won ? "won" : ""}">${endlessBoard ? `floor ${e.floor}${e.won ? " - crowned" : ""}` : e.bottom ? "TO THE BOTTOM" : e.won ? (e.floor > CM.LAST_FLOOR ? `SLEW THE LICH KING, floor ${e.floor}` : "SLEW THE LICH KING") : "floor " + e.floor}</td><td>${e.gold.toLocaleString()} gold${e.difficulty && e.difficulty !== "fair" && CM.DIFFICULTIES[e.difficulty] ? ` <i class="diff">${CM.DIFFICULTIES[e.difficulty].name}</i>` : ""}${e.ascension ? ` <i class="diff">A${e.ascension}</i>` : ""}${e.iron ? ` <i class="diff">Iron</i>` : ""}${e.awakened ? ` <i class="diff">Awakened</i>` : ""}</td><td>${this.esc(e.date)}${e.daily ? " ☀" : ""}</td></tr>`;
      if (open) {
        rows += `<tr class="details"><td colspan="5"><div>${(e.party || []).length ? this.esc(e.party.join(", ")) : "An old entry: who went wasn't written down."}</div>`
          + (e.seed ? `<div>Seed <b>${this.esc(e.seed)}</b>${e.daily ? " (today's dungeon)" : e.weekly ? " (a week's challenge)" : ""}${e.kit && e.kit !== "pauper" && CM.KITS[e.kit] ? `, ${CM.KITS[e.kit].name}` : ""} <button data-seed="${this.esc(e.seed)}">Play this seed</button>${e.code ? ` <button data-seed="${this.esc(e.code)}" title="The seed, the party, the difficulty and the kit, as they set out">Play this run</button>` : ""}</div>` : "")
          + (t ? `<div>${CM.plural(t.kills || 0, "monster")} slain, ${CM.plural(t.chests || 0, "chest")} opened, ${CM.plural(t.steps || 0, "step")}, ${CM.plural(t.fights || 0, "fight")}${t.fled ? ` (${t.fled} fled)` : ""}.</div>` : "")
          + (t && t.guardians && t.guardians.length ? `<div>Guardians slain: ${this.esc(this.guardianNames(t.guardians))}.</div>` : "")
          + (e.mutators && e.mutators.length ? `<div>${e.endless ? "The dark deepened" : "Today's dungeon"}: ${this.esc(e.mutators.map((m) => (CM.MUTATORS[m] || { name: m }).name).join(", "))}.</div>` : "")
          + (e.titles && e.titles.length ? `<div>Earned: ${this.esc(e.titles.map((id) => (CM.ACHIEVEMENTS[id] || { name: id }).name).join(", "))}.</div>` : "")
          + `<div><button data-card="${i}">Summary card</button>${e.film && (CM.store.get("films", []) || []).some((f) => f.key === e.film) ? ` <button data-film="${this.esc(e.film)}">Watch the film</button>` : ""}${e.trail && e.trail.length > 1 ? ` <small>a ghost to race: Play this seed</small>` : ""}</div>`
          + "</td></tr>";
      }
      return rows;
    }).join("");
    const have = CM.unlocked(g.allFame), deep = CM.deepest(g.allFame);
    this.$("#unlocks").innerHTML = Object.entries(CM.KITS).map(([id, k]) => {
      const got = have.includes(id), need = k.need === 21 ? "slay the Lich King" : `reach floor ${k.need}`;
      return `<div class="unlock ${got ? "got" : ""}"><b>${got ? "✓" : "○"} ${k.name}</b> <small>${got ? k.what : `${k.what} <i>(${need}${deep.floor ? `; deepest so far: floor ${deep.floor}` : ""})</i>`}</small></div>`;
    }).join("");
    const mem = g.memorial || [];
    this.$("#memorial").innerHTML = mem.length ? mem.slice(0, 8).map((m) => `<div class="unlock got"><b>${this.esc(m.name)}</b> <small>${this.esc(m.cls)}, level ${m.level}, laid to rest on floor ${m.floor} - ${this.esc(m.date)}${m.seed ? `, seed ${this.esc(m.seed)}` : ""}</small></div>`).join("") + (mem.length > 8 ? `<div class="small">...and ${mem.length - 8} more.</div>` : "") : `<div class="unlock"><small>No hero has been laid to rest at a camp fire yet.</small></div>`;
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
  },

  openCard(entry) {
    const g = this.game, e = entry || g.fame[0];
    if (!e) return;
    this.cardEntry = e;
    const slot = this.$("#card-slot");
    slot.innerHTML = "";
    slot.appendChild(CM.art.summaryCard(e, CM.titleFor(g.achievements)));
    const film = e.film && (CM.store.get("films", []) || []).find((f) => f.key === e.film);
    this.$("#card-text").value = CM.summaryText(e) + (e.code ? `\nRun code (paste it in the seed box): ${e.code}` : "") + (film ? `\nFilm code (Films, on the title, plays it): ${CM.filmCode(Object.assign({}, film.spec, { log: CM.unpackLog(film.spec.log) }))}` : "");
    this.$("#card-note").textContent = "";
    this.openDialog("#dlg-card");
  },
  copyText(text, noteEl) {
    const done = navigator.clipboard ? navigator.clipboard.writeText(text).then(() => true, () => false) : Promise.resolve(false);
    done.then((ok) => { if (noteEl) noteEl.textContent = ok ? "Copied." : "Select the text and copy it yourself."; });
    return done;
  },
});
