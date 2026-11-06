"use strict";
// Presentation, first pass (UPGRADE_PLAN_74.md, release 1) - "the account" as the art direction: what Claude writes is
// parchment and ink, the world is stone and torchlight. Three things here:
//  1. The view, decluttered: the sky card is a compact dial and the hour by default (the date, the weather and the moon
//     open on hover, or always with Settings > Sky card: Full), and it steps out of the way in a fight; the view's
//     vignette is a touch deeper below ground.
//  2. Health and ailments at a glance: the health bar is a settled green when whole, amber when hurt, red and slowly
//     pulsing when low; ailments are coloured chips with their mark; a badly hurt hero's portrait dims, a fallen one
//     greys, and in a fight the hero whose turn it is has a lit frame.
//  3. Chapter cards: going down, the floor's number and its band in Claude's hand across the view for a moment; the
//     first floor of a band is a chapter, with his line under it. Settings > Chapter cards: On / Off. Not under
//     Automatic.
{ const css = `
#view .sky.compact { padding: 4px; gap: 6px; }
#view .sky.compact .dial { width: 50px; height: 50px; flex-basis: 50px; }
#view .sky.compact .clocktext > :not(.row1) { display: none; }
#view .sky.compact .clocktext { min-width: 0; }
#view .sky.compact .clocktext .time { font-size: 15px; }
#view .sky.compact:hover .clocktext > :not(.row1) { display: revert; }
#view .sky.compact:hover .clocktext { min-width: 112px; }
#view .sky { transition: opacity 0.35s, transform 0.35s; }
#view.in-combat .sky { opacity: 0; transform: translateY(-10px); pointer-events: none; }
#view.below .vignette { box-shadow: inset 0 0 110px 40px rgba(0,0,0,0.62); }
.bar.hp i { background: #6E9A4A; }
.bar.hp[data-band="hurt"] i { background: #C08A2E; }
.bar.hp[data-band="low"] i { background: #C83A2A; animation: lowPulse 1.6s ease-in-out infinite; }
@keyframes lowPulse { 50% { filter: brightness(1.35); } }
.member .ail { display: flex; flex-wrap: wrap; gap: 3px; white-space: normal; }
.member .ail .ailchip { display: inline-flex; align-items: center; gap: 3px; padding: 0 5px; border-radius: 8px; font: bold 9px Tahoma, Verdana, sans-serif; line-height: 14px; color: #111; background: #C8B898; box-shadow: 0 0 0 1px rgba(0,0,0,0.4); animation: chipPulse 2.4s ease-in-out infinite; }
.member .ail .ailchip b { font-size: 10px; }
@keyframes chipPulse { 50% { box-shadow: 0 0 0 1px rgba(0,0,0,0.4), 0 0 6px 1px rgba(255,255,255,0.25); } }
.member .ail .ailchip.a-poison { background: #7CC060; } .member .ail .ailchip.a-paralysis { background: #E8D050; } .member .ail .ailchip.a-sleep { background: #8AA8E8; }
.member .ail .ailchip.a-blind { background: #A8A8A8; } .member .ail .ailchip.a-curse { background: #B888D8; } .member .ail .ailchip.a-stone { background: #9A9488; } .member .ail .ailchip.a-burn { background: #F0905A; } .member .ail .ailchip.a-frozen, .member .ail .ailchip.a-chill { background: #A8E0F0; }
.member.low canvas, .member.low img { filter: saturate(0.6) brightness(0.8); } .member.fallen canvas, .member.fallen img { filter: grayscale(1) brightness(0.55); }
.member.acting { box-shadow: 0 0 0 2px #E8B860, 0 0 14px 2px rgba(232,184,96,0.45); }
#view .chapter-card { position: absolute; left: 50%; top: 38%; transform: translate(-50%, -50%); z-index: 6; pointer-events: none; text-align: center; padding: 14px 34px 16px; color: #2A1C10;
  background: radial-gradient(ellipse at center, rgba(240,228,200,0.94) 0%, rgba(232,216,180,0.9) 55%, rgba(220,200,160,0) 100%); font-family: Georgia, "Times New Roman", serif; opacity: 0; transition: opacity 0.7s; min-width: 280px; }
#view .chapter-card.on { opacity: 1; }
#view .chapter-card .floor { font: italic 15px Georgia, serif; letter-spacing: 0.08em; color: #6A4A28; }
#view .chapter-card .band { font: 600 28px Georgia, serif; letter-spacing: 0.02em; margin: 2px 0; }
#view .chapter-card .rule { width: 160px; height: 2px; margin: 6px auto; background: linear-gradient(90deg, rgba(90,60,30,0), #5A3C1E, rgba(90,60,30,0)); }
#view .chapter-card .line { font: italic 14px Georgia, serif; color: #4A3220; max-width: 460px; margin: 0 auto; }
#view .chapter-card.small { padding: 8px 26px 10px; min-width: 180px; } #view .chapter-card.small .band { font-size: 20px; }
body.reduce-motion .bar.hp i, body.reduce-motion .member .ail .ailchip { animation: none; }`;
  const style = () => { if (document.getElementById("presentation-css")) return; const st = document.createElement("style"); st.id = "presentation-css"; st.textContent = css; document.head.appendChild(st); };
  // 1. the view
  { const ds0 = CM.UI.prototype.drawSky; CM.UI.prototype.drawSky = function (...a) { const out = ds0.apply(this, a); style(); const el = this.$("#view .sky"), g = this.game; if (el) el.classList.toggle("compact", ((g.settings || {}).skycard || "compact") !== "full"); return out; }; }
  { const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), v = this.$("#view"), g = this.game; if (v && g) { v.classList.toggle("in-combat", g.mode === "combat"); v.classList.toggle("below", Boolean(g.floor && g.floor.number >= 1)); } return out; }; }
  // 2. health and ailments
  { const rp0 = CM.UI.prototype.renderParty; CM.UI.prototype.renderParty = function (...a) { const out = rp0.apply(this, a), box = this.$("#party"), g = this.game; if (!box || !g || !g.party) return out; style();
      const acting = g.mode === "combat" && g.combat ? g.combat.waiting : null;
      g.party.forEach((m, i) => { const div = box.children[i]; if (!div) return; const f = m.max ? Math.max(0, m.hp) / m.max : 0, band = f > 0.6 ? "whole" : f > 0.3 ? "hurt" : "low";
        const hp = div.querySelector(".bar.hp"); if (hp) hp.dataset.band = band; div.classList.toggle("low", m.hp > 0 && band === "low"); div.classList.toggle("acting", Boolean(acting) && acting === m);
        const ail = div.querySelector(".ail"), st = m.status || {}, ids = Object.keys(st).filter((s) => st[s]);
        if (ail) { { ail.innerHTML = ids.map((s) => { const S = (CM.STATUSES || {})[s] || { name: s, mark: "" }; return `<span class="ailchip a-${s}" title="${this.esc(S.name + (S.hint ? ": " + S.hint : ""))}"><b>${this.esc(S.mark || "")}</b>${this.esc(S.name)}</span>`; }).join(""); } ail.style.display = ids.length ? "" : "none"; } });
      return out; }; }
  // 3. chapter cards
  let timer = 0; const carded = new Set();   /* (the window's own memory: nothing of it goes into the run) */
  const card = (ui, big, floorText, band, line) => { const v = ui.$("#view"); if (!v) return; style(); let c = v.querySelector(".chapter-card"); if (!c) { c = document.createElement("div"); c.className = "chapter-card"; v.appendChild(c); }
    c.classList.toggle("small", !big); c.innerHTML = `<div class="floor">${ui.esc(floorText)}</div><div class="band">${ui.esc(band)}</div>${big && line ? `<div class="rule"></div><div class="line">${ui.esc(line)}</div>` : ""}`;
    clearTimeout(timer); requestAnimationFrame(() => c.classList.add("on")); timer = setTimeout(() => c.classList.remove("on"), big ? 2600 : 1300); };
  const words = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"];
  const bind = () => { const g = CM.game, ui = CM.ui; if (!g || !g.on || !ui) return false;
    g.on("floor", (fl) => { if (!fl || !(fl.number >= 1) || fl.number % 1 !== 0 || g.mode === "title" || (g.settings || {}).chapters === "off" || (g.autoOn && g.autoOn()) || g.replaying || g.film) return;
      const T = CM.themeFor(fl.number), N = g.ext ? g.ext("narr") : {}, b = CM.themeIndex(fl.number), id = `${g.seed}:${g.startedAt || ""}:${b}`, fresh = (N.bands || []).includes(b) && !carded.has(id);
      if (fresh) { carded.add(id); const pen = (g.messages || []).slice().reverse().find((m) => CM.PEN && m.startsWith(CM.PEN) && /Chapter \d+:/.test(m)); const line = pen ? pen.replace(CM.PEN, "").replace(/^Chapter \d+: [^.]*\.\s*/, "") : "";
        card(ui, true, `Chapter ${words[N.bands.length] || N.bands.length} - floor ${fl.number}`, T.name, line); }
      else card(ui, false, `Floor ${fl.number}`, T.name, ""); });
    return true; };
  if (!bind()) { const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); }
  if (CM.settingLater && CM.addSetting) CM.settingLater((ui) => {
    CM.addSetting("set-skycard", "Sky card - the dial and the hour (the date, weather and moon on hover), or everything always", [["compact", "Compact"], ["full", "Full"]], "skycard", "compact", ui);
    CM.addSetting("set-chapters", "Chapter cards - the floor and its band across the view as you go down", [["on", "On"], ["off", "Off"]], "chapters", "on", ui); });
  { const g0 = () => { const g = CM.game; if (g && g.on) { g.on("settings", () => { if (CM.ui) { CM.ui.drawSky && CM.ui.drawSky(); } }); return true; } return false; }; if (!g0()) { const t = setInterval(() => { if (g0()) clearInterval(t); }, 300); } }
}
