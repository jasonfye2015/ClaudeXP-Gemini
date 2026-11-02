"use strict";
// Eyes in the dark (v41.2, UPGRADE_PLAN_36.md): a waking pack out past the torch's reach is a darkness with eyes in it -
// a pair for each that stands, at its head's height, in its kind's colour (cold blue for the dead, amber for beasts, red
// for the fiery and the demonic, green for the rest), blinking now and then. The sleeping keep theirs shut; one that has
// turned its back shows none. As the party comes nearer the torch finds the rest of it.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const COL = { blue: ["#A8D8FF", "#FFFFFF"], amber: ["#FFB020", "#FFF0A0"], red: ["#FF3020", "#FFC0A0"], green: ["#80FF60", "#E8FFD0"] };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, [c, hot]] of Object.entries(COL)) { const k = cv(), p = k.getContext("2d");
      for (const x of [26, 102]) { p.fillStyle = c; p.beginPath(); p.ellipse(x, 64, 24, 15, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = hot; p.beginPath(); p.ellipse(x, 64, 9, 9, 0, 0, Math.PI * 2); p.fill(); }
      set.index[`ey:${n}`] = set.layers.length; set.layers.push(k); } return set; }; }
  const colourOf = (m) => { const k = CM.monsterKind(m.kind || m.name) || {}, n = `${m.kind || m.name}`; return k.undead || m.undead ? "blue" : /Demon|Imp|Fire|Ember|Salamander|Hell|Wyvern|Drake|Dragon/.test(n) ? "red" : k.body === "beast" || /Wolf|Rat|Bat|Bear|Spider|Hound|Boar|Cat/.test(n) ? "amber" : "green"; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || game.mode !== "explore" || !(fl.number >= 1) || !CM.renderer || CM.renderer.index["ey:red"] === undefined) return out;
      const eye = CM.renderer.eye || [fl.pos[0] + 0.5, 0.5, fl.pos[1] + 0.5], reach = Math.max(3, ((CM.themeFor(fl.number) || {}).reach || 5) * 0.7);
      for (const [k, t] of Object.entries(fl.things)) { if (!["monsters", "boss", "guardian"].includes(t.type) || t.asleep || t.anim || !t.group) continue; const [x, y] = k.split(",").map(Number), cx = x + 0.5, cz = y + 0.5, d = Math.hypot(cx - eye[0], cz - eye[2]); if (d < reach || d > 11) continue;
        const view = CM.monsterView ? CM.monsterView(t, x, y, eye) : null; if (view && view.view === "back") continue;
        const up = t.group.filter((m) => m.hp > 0 && !m.fled).slice(0, 3), toEye = [(eye[0] - cx) / d, (eye[2] - cz) / d], across = [-toEye[1], toEye[0]], fade = Math.min(1, (d - reach) / 1.5);
        up.forEach((m, i) => { const sh = (i - (up.length - 1) / 2) * 0.28, big = m.boss ? 1.15 : m.guardian ? 1.1 : 1, blink = !CM.reducedMotion && (now / 1000 + x * 1.3 + y * 0.7 + i * 1.9) % 4.3 < 0.14; if (blink) return;
          const H = (m.boss ? 0.98 : m.guardian ? 0.92 : 0.85) * 0.72 + (i % 2) * 0.04, wob = CM.reducedMotion ? 0 : Math.sin(now / 900 + i + x) * 0.01;
          out.push({ x, y, dx: toEye[0] * 0.12 + across[0] * sh + wob, dz: toEye[1] * 0.12 + across[1] * sh, layer: `ey:${colourOf(m)}`, w: 0.11 * big, h: 0.11 * big, lift: H, glow: 2, alpha: fade }); }); }
      return out; }; }
}
