"use strict";
// The tray (v25.3, UPGRADE_PLAN_20.md): what matters and passes comes up as a small toast in the corner of the view as
// well as in the log - a hero gaining a level, a town request ready to hand in (and its reward), seeds found, a rare
// find, a card for the deck, the party's renown level rising. Each has its own mark and colour; they stack (four at
// most), fade after a few seconds (a pointer over them holds them), and a click opens the page they belong to. Off
// while a film plays or the game is played back.
{ const KINDS = { level: ["★", "#E8C870"], request: ["✓", "#7CDA6A"], seed: ["❦", "#9AD07A"], rare: ["♦", "#C890FF"], card: ["♠", "#E0E0F0"], renown: ["▲", "#F0B060"] };
  const MOST = 4, STAY = 5200;
  CM.UI.prototype.toast = function (kind, text, open) {
    const g = this.game; if (!g || g.replaying || (g.film && g.film.playing) || g.mode === "title") return;
    const view = this.$("#view"); if (!view) return; let tray = view.querySelector(".tray"); if (!tray) { tray = document.createElement("div"); tray.className = "tray"; view.appendChild(tray); }
    const [mark, col] = KINDS[kind] || ["•", "#CFC3A0"], el = document.createElement("div"); el.className = "toast";
    el.style.setProperty("--tc", col); el.innerHTML = `<b>${mark}</b><span></span>`; el.querySelector("span").textContent = text; if (open) { el.classList.add("link"); el.title = "Open"; }
    tray.appendChild(el); while (tray.children.length > MOST) tray.firstChild.remove();
    let left = STAY, last = performance.now(), held = false; const tick = () => { const now = performance.now(); if (!held) left -= now - last; last = now; if (left <= 0) { el.classList.add("out"); setTimeout(() => el.remove(), 300); } else requestAnimationFrame(tick); };
    el.addEventListener("pointerenter", () => { held = true; }); el.addEventListener("pointerleave", () => { held = false; last = performance.now(); });
    el.addEventListener("click", () => { el.remove(); if (open) try { open(); } catch (e) { /* (the page isn't there just now) */ } });
    requestAnimationFrame(tick);
  };
  const ui = () => CM.ui;
  // a level gained (the fight's level-up, and any other)
  // a rare find, and seeds
  const RARE = ["rare", "relic", "unique", "set"];
  const gain0 = CM.Game.prototype.gain;
  CM.Game.prototype.gain = function (items, how) { const out = gain0.call(this, items, how), U = ui(); if (U && U.game === this && out && out.length && how !== "shop" && how !== "buy") {
      const seeds = out.filter((it) => it.kind === "seed"); if (seeds.length) U.toast("seed", seeds.length === 1 ? `Seeds found: ${seeds[0].name}` : `Seeds found: ${seeds.length} packets`, () => this.openBag && this.openBag(false));
      for (const it of out.filter((x) => !x.unknown && RARE.includes(CM.rarityOf(x))).slice(0, 2)) U.toast("rare", `A ${CM.rarityOf(it)} find: ${it.name}`, () => this.openBag && this.openBag(false)); }
    return out; };
  // a card for the deck
  if (CM.Game.prototype.addCard) { const ac0 = CM.Game.prototype.addCard; CM.Game.prototype.addCard = function (name, why) { const out = ac0.call(this, name, why), U = ui(); if (U && U.game === this && name) U.toast("card", `A card for the deck: ${name}`); return out; }; }
  // what is watched as it changes: a request ready, the renown level
  const rf0 = CM.UI.prototype.refresh;
  CM.UI.prototype.refresh = function (...a) {
    const out = rf0.apply(this, a), g = this.game;
    if (g && !this.trayBound && g.on) { this.trayBound = true; g.on("fx", (e) => { if (e && e.kind === "levelup" && e.hero && e.real !== false) { const i = g.party.indexOf(e.hero); this.toast("level", `${e.hero.name} reaches level ${e.level}`, i >= 0 ? () => this.openSheet(i) : null); } }); }
    if (g && g.mode !== "title" && !g.replaying) {
      try { if (g.rqList && g.rqProgress) { const L = g.rqList(), ready = this.trayReady = this.trayReady || new Set();
          for (const q of L) { const id = `${q.kind}:${q.n}:${q.giver || ""}`; if (!q.done && g.rqProgress(q) >= q.n && !ready.has(id)) { ready.add(id); if (this.trayPrimed) this.toast("request", `A request is ready: ${g.rqWords(q)}`, () => this.openRequests && this.openRequests()); } } } } catch (e) { /* (no requests yet) */ }
      try { if (g.rlInfo) { const L = g.rlInfo().level; if (this.trayRenown !== undefined && L > this.trayRenown) this.toast("renown", `Renown level ${L}`, () => this.openVillage && this.openVillage()); this.trayRenown = L; } } catch (e) { /* (no renown yet) */ }
      this.trayPrimed = true;
    }
    return out;
  };
  // a request handed in: its reward
  if (CM.Game.prototype.rqDone) { const rd0 = CM.Game.prototype.rqDone; CM.Game.prototype.rqDone = function (i) { const out = rd0.call(this, i), U = ui(); if (U && U.game === this && out && !out.error) U.toast("request", `Request done: ${out.gold ? out.gold + " gold, " : ""}${out.renown || 0} renown`); return out; }; }
}
