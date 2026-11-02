"use strict";
// Tooltips that compare (v25.2, UPGRADE_PLAN_20.md): hovering a thing anywhere it is shown with its card - the pack, a
// shop, a chest, the belt, the stash - brings up a tooltip of its own instead of the plain line: its name in its
// rarity's colour, what it is, and for gear, the hero it suits best with every number that would move (green up,
// red down; 69u-compare.js tries it on), and a line for each of the others. Things are known by their card's words
// (CM.itemCard is noted as it is written), so every list that uses the card gets it without being changed.
{ const seen = new Map(), MAX = 600;
  const card0 = CM.itemCard;
  CM.itemCard = function (item) { const s = card0.call(this, item); if (item && typeof item === "object") { seen.delete(s); seen.set(s, item); if (seen.size > MAX) seen.delete(seen.keys().next().value); } return s; };
  const lookup = (text) => { if (!text) return null; if (seen.has(text)) return seen.get(text); for (const [k, it] of seen) if (text.startsWith(k)) return it; return null; };
  let tip = null, host = null;
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const body = (item) => {
    const g = CM.game, name = item.unknown ? CM.baseName(item) : item.name, r = item.unknown ? "unknown" : CM.rarityOf(item);
    let h = `<div class="tt-name rarity-${r}">${esc(name)}</div><div class="tt-what">${esc(CM.itemLabel(item))}</div>`;
    if (item.found && item.found.how && item.found.how !== "unknown") h += `<div class="tt-found">Found ${item.found.floor ? `on floor ${item.found.floor}, ` : ""}${esc(CM.HOW_FOUND[item.found.how] || item.found.how)}</div>`;
    const B = g && g.party && CM.gearBest ? CM.gearBest(g, item) : null;
    if (B && B.best) { const { h: hero, c } = B.best;
      if (c && c.why) h += `<div class="tt-why">${esc(c.why)}</div>`;
      else if (c) { h += `<div class="tt-head">On ${esc(hero.name)}${c.was ? ` (for ${esc(c.was.unknown ? CM.baseName(c.was) : c.was.name)})` : ""}${c.two ? ", and the shield off" : ""}</div>`;
        h += c.rows.length ? `<table class="tt-rows">${c.rows.map(([label, a, b, k]) => { return `<tr><td>${esc(label)}</td><td>${a}</td><td>→</td><td class="${b > a ? "up" : "down"}">${b} <i>(${b > a ? "+" : ""}${b - a})</i></td></tr>`; }).join("")}</table>` : `<div class="tt-same">Nothing on the sheet moves.</div>`; }
      const others = B.each.filter((e) => e !== B.best).map((e) => `${esc(e.h.name)} ${!e.c ? "-" : e.c.why ? "<span class='down'>can't</span>" : e.c.gain === null ? "?" : e.c.gain > 0 ? `<span class='up'>+${e.c.gain}</span>` : e.c.gain < 0 ? `<span class='down'>${e.c.gain}</span>` : "same"}`);
      if (others.length) h += `<div class="tt-others">${others.join(" · ")}</div>`; }
    return h;
  };
  const show = (el, item, e) => { if (!tip) { tip = document.createElement("div"); tip.className = "itemtip"; document.body.appendChild(tip); } tip.innerHTML = body(item); tip.classList.add("on"); place(e); host = el; if (el.title) { el.dataset.tipTitle = el.title; el.removeAttribute("title"); } };
  const hide = () => { if (tip) tip.classList.remove("on"); if (host && host.dataset.tipTitle !== undefined) { host.title = host.dataset.tipTitle; delete host.dataset.tipTitle; } host = null; };
  const place = (e) => { if (!tip) return; const w = tip.offsetWidth, hgt = tip.offsetHeight, x = Math.min(window.innerWidth - w - 8, e.clientX + 16), y = Math.min(window.innerHeight - hgt - 8, e.clientY + 14); tip.style.left = `${Math.max(8, x)}px`; tip.style.top = `${Math.max(8, y)}px`; };
  document.addEventListener("mouseover", (e) => { const el = e.target.closest && e.target.closest("[title], [data-tip-title]"); if (!el) { if (host) hide(); return; } if (el === host) return; const item = lookup(el.title || el.dataset.tipTitle); if (item) show(el, item, e); else if (host) hide(); });
  document.addEventListener("mousemove", (e) => { if (host) place(e); });
  document.addEventListener("mouseout", (e) => { if (host && (!e.relatedTarget || !host.contains(e.relatedTarget))) hide(); });
  document.addEventListener("mousedown", () => { if (host) hide(); });
}
