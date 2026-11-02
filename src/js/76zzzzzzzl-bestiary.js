"use strict";
// An illustrated bestiary (v42.0, UPGRADE_PLAN_37.md): a page of the Journal ("Plates") with every kind the party has
// met painted large on its own parchment plate - the picture the game draws it with, framed and named in a fair hand -
// and the margins written up from what has been learned of it: where it lives, how many met and slain, what it fears
// and shrugs off, what it does, and its way once known; a kind met but never slain is only sketched in outline.
{ const css = `.cm-plates { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 14px; padding: 6px 2px; }
.cm-plate { position: relative; background: #EADCB8; color: #3A2A18; border: 1px solid #8A6A40; box-shadow: inset 0 0 22px rgba(120, 80, 30, 0.35), 0 2px 6px rgba(0,0,0,0.4); padding: 10px 10px 8px; min-height: 300px; }
.cm-plate canvas { display: block; margin: 18px auto 4px; width: 150px; height: 150px; border: 2px solid #6A4A28; background: radial-gradient(#F4EAD0, #D8C49A); }
.cm-plate h4 { margin: 2px 0 0; text-align: center; font-family: Georgia, serif; font-variant: small-caps; font-size: 17px; color: #4A2A10; }
.cm-plate .where { text-align: center; font-size: 11px; font-style: italic; color: #6A5030; }
.cm-plate .note { position: absolute; font-family: "Segoe Print", "Bradley Hand", "Comic Sans MS", cursive; font-size: 11px; line-height: 1.15; color: #5A2E10; max-width: 92px; }
.cm-plate .note.n0 { left: 6px; top: 6px; transform: rotate(-6deg); } .cm-plate .note.n1 { right: 6px; top: 8px; transform: rotate(5deg); text-align: right; }
.cm-plate .note.n2 { left: 4px; top: 120px; transform: rotate(-3deg); } .cm-plate .note.n3 { right: 4px; top: 128px; transform: rotate(4deg); text-align: right; }
.cm-plate .foot { font-family: "Segoe Print", "Bradley Hand", cursive; font-size: 11px; color: #5A2E10; margin-top: 6px; text-align: center; }
.cm-plate.sketch canvas { filter: grayscale(1) contrast(0.6) brightness(1.25) sepia(0.5); opacity: 0.6; }`;
  const ensureCss = () => { if (document.getElementById("cm-plates-css")) return; const s = document.createElement("style"); s.id = "cm-plates-css"; s.textContent = css; document.head.appendChild(s); };
  const portraits = new Map(), portrait = (m) => { let c = portraits.get(m.name); if (c) return c; try { c = CM.art.monster(m, false, "idle"); } catch (e) { c = null; } portraits.set(m.name, c); return c; };
  const boxes = new WeakMap(), boxOf = (pic) => { let b = boxes.get(pic); if (b) return b; b = [0, 0, pic.width, pic.height]; try { const d = pic.getContext("2d").getImageData(0, 0, pic.width, pic.height).data; let x0 = pic.width, y0 = pic.height, x1 = 0, y1 = 0;   /* (the figure's own box: drawn large) */
      for (let y = 0; y < pic.height; y++) for (let x = 0; x < pic.width; x++) if (d[(y * pic.width + x) * 4 + 3] > 40) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } if (x1 > x0) b = [x0, y0, x1 - x0 + 1, y1 - y0 + 1]; } catch (e) { /* (as it is) */ } boxes.set(pic, b); return b; };
  const shapeWords = (m) => { const [hp, atk, df] = m.shape || [1, 1, 1], w = []; if (hp >= 1.4) w.push("tough"); else if (hp <= 0.7) w.push("frail"); if (atk >= 1.2) w.push("hits hard"); if (df >= 1.3) w.push("armoured"); else if (df <= 0.7) w.push("thin-skinned"); return w; };
  CM.journalPage("plates", "Plates", "The bestiary illustrated: every kind met, painted large, with what has been learned of it", (ui, box) => { ensureCss(); const g = ui.game, b = g.bestiary || {}, kinds = CM.MONSTERS.filter((m) => b[m.name] && b[m.name].seen);
    const head = document.createElement("div"); head.className = "list-title"; head.textContent = `Plates - ${kinds.length} of ${CM.MONSTERS.length} kinds drawn`; box.appendChild(head);
    if (!kinds.length) { const p = document.createElement("p"); p.textContent = "Nothing met yet. The plates wait, blank, for the first thing in the dark."; box.appendChild(p); return; }
    const grid = document.createElement("div"); grid.className = "cm-plates"; box.appendChild(grid);
    for (const m of kinds) { const e = b[m.name], el = document.createElement("div"); el.className = `cm-plate${e.slain ? "" : " sketch"}`;
      const notes = []; const sw = shapeWords(m); if (sw.length) notes.push(sw.join(", ") + "!");
      if (e.weak && e.weak.length) notes.push(`fears ${e.weak.map((x) => (CM.ELEMENT_NAMES[x] || x).toLowerCase()).join(" & ")}`); if (e.resist && e.resist.length) notes.push(`shrugs off ${e.resist.map((x) => (CM.ELEMENT_NAMES[x] || x).toLowerCase()).join(" & ")}`);
      if (m.ability && CM.ABILITY_WORDS && CM.ABILITY_WORDS[m.ability]) notes.push(CM.ABILITY_WORDS[m.ability]); if (m.touch && CM.STATUSES[m.touch.status]) notes.push(`its touch: ${CM.STATUSES[m.touch.status].name.toLowerCase()}`);
      if (m.undead) notes.push("dead, and walking"); if (m.row === "back") notes.push("keeps behind the others");
      const habit = g.habitRead && CM.habitOf && (g.habitRead(m.name) || (g.habitKnown && g.habitKnown(m.name))) ? CM.habitOf(m.name) : null;
      el.innerHTML = notes.slice(0, 4).map((n, i) => `<div class="note n${i}">${ui.esc(n)}</div>`).join("") + `<h4>${ui.esc(m.name)}</h4><div class="where">${ui.esc(m.deep ? CM.THEMES[m.deep].name : "the first twenty floors")}</div>`
        + `<div class="foot">met ${e.seen}, slain ${e.slain}${habit ? ` - its way: ${ui.esc(habit)}` : e.slain ? "" : " - never yet brought down"}</div>`;
      const pic = portrait(m), c = document.createElement("canvas"); c.width = 150; c.height = 150; if (pic) { const p = c.getContext("2d"), [x0, y0, w, h] = boxOf(pic), k = Math.min(130 / w, 136 / h); p.imageSmoothingEnabled = true; p.drawImage(pic, x0, y0, w, h, 75 - w * k / 2, 144 - h * k, w * k, h * k); }
      el.insertBefore(c, el.querySelector("h4")); grid.appendChild(el); } });
}
