"use strict";
// A music room (v44.4, UPGRADE_PLAN_39.md): the party's house has a music room (from its first level) - every tune ever
// heard, on any run, kept by name, and played there on asking: the bands' themes, the guardians' and the Lich King's,
// the fight, the camp, the town by the hour, the Joker's lounge, the title, the end; and the motifs, the party's and the
// Lich King's and the Joker's, the bell and the queen's song and the Root's note. What was playing comes back when the
// room is left. (Remembered on this computer: CM.store "tunesHeard".)
{ const M = CM.music; if (M) {
  const heard = () => { try { return new Set(CM.store.get("tunesHeard", [])); } catch (e) { return new Set(); } };
  { const s0 = M.start; M.start = function (kind, ...a) { const out = s0.call(this, kind, ...a); try { const k = this.playing, H = heard(); if (k && !H.has(k)) { H.add(k); CM.store.set("tunesHeard", [...H]); } } catch (e) { /* (not kept) */ } return out; }; }
  { const m0 = M.motif; M.motif = function (name, ...a) { const out = m0.call(this, name, ...a); try { const H = heard(), k = `motif:${name}`; if (out && !H.has(k)) { H.add(k); CM.store.set("tunesHeard", [...H]); } } catch (e) { /* (not kept) */ } return out; }; }
  const TOWN = { town_morning: "Caer Duin in the morning", town_midday: "Caer Duin at midday", town_evening: "The tavern's fiddle", town_night: "Caer Duin in the small hours" };
  const nameOf = (k) => { let m; if ((m = /^depth(\d)$/.exec(k))) return (CM.THEMES[Number(m[1])] || {}).name || k; if ((m = /^boss_(\w+?)(_2)?$/.exec(k))) { const who = m[1] === "lich" ? "The Lich King" : (CM.GUARDIANS[m[1]] || {}).name || m[1]; return `${who}${m[2] ? ", the turn" : ""}`; }
    if (TOWN[k]) return TOWN[k]; if ((m = /^motif:(\w+)$/.exec(k))) return { party: "The party's call", lich: "The Lich King's line", lich_end: "The Lich King's line, in the major", joker: "The Joker's waltz", bell: "The bell", queen: "The queen's song", root: "The Root's note" }[m[1]] || m[1];
    return { title: "The title", battle: "A fight", boss: "A guardian", camp: "The camp", victory: "Victory", lament: "The lament", casino: "The Joker's lounge" }[k] || k; };
  const ORDER = (k) => (k.startsWith("town_") ? 1 : /^depth/.test(k) ? 2 : k.startsWith("boss_") ? 3 : k.startsWith("motif:") ? 5 : 4);
  let before = null;
  CM.UI.prototype.openMusicRoom = function () { if (!this.$("#dlg-musicroom")) { const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-musicroom"; d.innerHTML = `<div class="box"><h2>The music room</h2><p class="lore">A spinet, a fiddle on a peg, a lute, a set of handbells - and whoever is home knows every tune the party has ever heard.</p><div id="mr-list"></div><div class="note" id="mr-note"></div><div class="row"><button data-mrstop>Stop</button><button data-mrclose>Close</button></div></div>`;
      (this.root || document.body).appendChild(d); d.querySelector("[data-mrclose]").addEventListener("click", () => this.closeDialogs()); d.querySelector("[data-mrstop]").addEventListener("click", () => { M.stop(); this.$("#mr-note").textContent = "Quiet."; }); }
    before = before || M.playing; const box = this.$("#mr-list"); box.innerHTML = ""; const H = [...heard()].sort((a, b) => ORDER(a) - ORDER(b) || nameOf(a).localeCompare(nameOf(b)));
    const title = (t) => { const e = document.createElement("div"); e.className = "list-title"; e.textContent = t; box.appendChild(e); }; let last = 0;
    for (const k of H) { const o = ORDER(k); if (o !== last) { title(["", "The town", "The bands", "The guardians", "Other times", "The motifs"][o]); last = o; } const b = document.createElement("button"); b.textContent = nameOf(k); b.style.margin = "2px";
      b.addEventListener("click", () => { if (k.startsWith("motif:")) M.motif(k.slice(6)); else { M.playing = null; M.start(k); } this.$("#mr-note").textContent = `Playing: ${nameOf(k)}.`; }); box.appendChild(b); }
    if (!H.length) box.textContent = "No tunes heard yet."; this.$("#mr-note").textContent = `${H.length} tune${H.length === 1 ? "" : "s"} known.`; this.openDialog("#dlg-musicroom"); };
  { const cd0 = CM.UI.prototype.closeDialogs; CM.UI.prototype.closeDialogs = function (...a) { const was = this.$ && this.$("#dlg-musicroom") && this.$("#dlg-musicroom").classList.contains("on"), out = cd0.apply(this, a);
      if (was && before !== undefined) { const k = before; before = null; M.playing = null; if (k) M.start(k); else M.stop(); } return out; }; }
  { const oh0 = CM.UI.prototype.openHome; if (oh0) CM.UI.prototype.openHome = function (...a) { const out = oh0.apply(this, a); try { const box = this.$("#home-rooms"); if (box && this.game.homeLevel() >= 1 && !box.querySelector("[data-musicroom]")) {
      const d = document.createElement("div"); d.innerHTML = `<div class="list-title">The music room</div>`; const b = document.createElement("button"); b.dataset.musicroom = "1"; b.textContent = `Play a tune (${heard().size} known)`; b.addEventListener("click", () => this.openMusicRoom()); d.appendChild(b); box.appendChild(d); } } catch (e) { /* (the house as it was) */ } return out; }; }
} }
