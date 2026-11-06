"use strict";
// Presentation, third pass (UPGRADE_PLAN_74.md, release 3): the pack and the gear. The pack is a grid of framed things
// (the frame's colour its rarity) rather than a long list; beside it, the four heroes as cards with their portraits
// and what each wears, a click on a card the same as its "Equip on" button (and a dragged thing still lands on the
// party's own cards below); and the thing picked is described on a parchment card in Claude's ink. Every button, the
// shop's list, the belt, the filters and the drag and drop are the game's own, unchanged.
{ const css = `
#bag { background: radial-gradient(ellipse at 50% 30%, #2A2016 0%, #15100B 70%); }
#bag .lists { gap: 12px; }
#bag-heroes { flex: 0 0 210px; display: flex; flex-direction: column; gap: 6px; overflow: auto; }
#bag-heroes .hcard { display: grid; grid-template-columns: 46px 1fr; gap: 2px 8px; padding: 6px; border: 1px solid rgba(200,168,96,0.35); border-radius: 6px; background: rgba(40,30,20,0.75); cursor: pointer; }
#bag-heroes .hcard:hover { border-color: rgba(232,184,96,0.9); } #bag-heroes .hcard.fallen { opacity: 0.55; }
#bag-heroes .hcard .who { font: 600 13px Georgia, serif; color: #E8D4A8; } #bag-heroes .hcard .who small { color: #A89878; font-weight: normal; }
#bag-heroes .hcard .worn { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 3px; }
#bag-heroes .hcard .worn span { width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; border-radius: 4px; background: rgba(0,0,0,0.35); border: 1px solid rgba(200,168,96,0.25); }
#bag-heroes .hcard .worn canvas, #bag-heroes .hcard .worn img { width: 22px; height: 22px; }
#bag-heroes .hcard .cmp { grid-column: 2; font: 11px Georgia, serif; color: #A89878; } #bag-heroes .hcard .cmp.good { color: #9AD08A; } #bag-heroes .hcard .cmp.bad { color: #E09080; }
#bag-list, #shop-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(104px, 1fr)); gap: 6px; align-content: start; overflow: auto; }
#bag-list > .head, #shop-list > .head, #bag-list > .empty, #shop-list > .empty { grid-column: 1 / -1; }
#bag-list > .item, #shop-list > .item { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 4px; padding: 8px 4px 6px; min-height: 86px; border-radius: 6px;
  border: 1px solid rgba(160,140,110,0.4); background: linear-gradient(180deg, rgba(56,42,28,0.9), rgba(30,22,14,0.9)); font-size: 11px; line-height: 1.2; }
#bag-list > .item canvas, #bag-list > .item img, #shop-list > .item canvas, #shop-list > .item img { width: 40px; height: 40px; image-rendering: pixelated; }
#bag-list > .item .what, #shop-list > .item .what { display: none; }
#bag-list > .item.r-fine, #shop-list > .item.r-fine { border-color: #6A9AD8; } #bag-list > .item.r-rare, #shop-list > .item.r-rare { border-color: #E0C050; }
#bag-list > .item.r-relic, #shop-list > .item.r-relic { border-color: #E07838; box-shadow: inset 0 0 10px rgba(224,120,56,0.25); } #bag-list > .item.r-unique, #shop-list > .item.r-unique { border-color: #C070E0; box-shadow: inset 0 0 10px rgba(192,112,224,0.25); }
#bag-list > .item.r-cursed, #shop-list > .item.r-cursed { border-color: #A03030; }
#bag-list > .item.sel, #shop-list > .item.sel { outline: 2px solid #E8B860; outline-offset: 1px; background: linear-gradient(180deg, rgba(90,66,36,0.95), rgba(46,34,20,0.95)); }
#bag .note { min-height: 44px; padding: 10px 14px; border-radius: 4px; color: #2E2014; font: 14px/1.4 Georgia, serif; white-space: pre-line;
  background: linear-gradient(180deg, #EFE2C2, #E2D0A8); box-shadow: inset 0 0 18px rgba(120,80,30,0.25), 0 2px 6px rgba(0,0,0,0.5); }
#bag .note b.title { display: block; font: 600 16px Georgia, serif; margin-bottom: 2px; }`;
  const style = () => { if (document.getElementById("pack-css")) return; const st = document.createElement("style"); st.id = "pack-css"; st.textContent = css; document.head.appendChild(st); };
  const shown = (ui, g) => { const F = CM.BAG_FILTERS[ui.bagFilter || "all"]; return g.bag.map((it, i) => i).filter((i) => !F.kinds || F.kinds.includes(g.bag[i].kind)); };
  const fb0 = CM.UI.prototype.fillBag; CM.UI.prototype.fillBag = function (...a) { const out = fb0.apply(this, a), g = this.game; style(); try {
      // the frames: each row's rarity
      const rows = shown(this, g), packItems = [...this.$("#bag-list").querySelectorAll(":scope > .item")]; packItems.forEach((el, n) => { const it = g.bag[rows[n]]; if (it) el.classList.add(`r-${CM.rarityOf(it)}`); });
      [...this.$("#shop-list").querySelectorAll(":scope > .item")].forEach((el, n) => { const it = (g.stock || [])[n]; if (it) el.classList.add(`r-${CM.rarityOf(it)}`); });
      // the heroes, and what each wears
      const lists = this.$("#bag .lists"); let H = this.$("#bag-heroes"); if (!H) { H = document.createElement("div"); H.id = "bag-heroes"; lists.insertBefore(H, lists.firstChild); }
      H.innerHTML = ""; const give = [...this.$("#bag-give").querySelectorAll("button")];
      g.party.forEach((h, i) => { const c = document.createElement("div"); c.className = "hcard" + (h.hp <= 0 ? " fallen" : ""); c.title = give[i] ? give[i].title || give[i].textContent : h.name;
        c.appendChild(this.portrait(h, 44)); const who = document.createElement("div"); who.innerHTML = `<div class="who">${this.esc(h.name)} <small>${this.esc(h.cls)} ${h.level}</small></div>`;
        const cmp = give[i] && give[i].querySelector(".cmp"); if (cmp) { const d = document.createElement("div"); d.className = cmp.className; d.textContent = cmp.textContent; who.appendChild(d); }
        c.appendChild(who); const worn = document.createElement("div"); worn.className = "worn"; for (const it of CM.equipped(h)) { if (!it || (it.props && it.props.fists)) continue; const s = document.createElement("span"); s.title = it.name; s.appendChild(this.icon(it)); worn.appendChild(s); }
        c.appendChild(worn); c.addEventListener("click", () => { const b = this.$("#bag-give").querySelectorAll("button")[i]; if (b) b.click(); }); H.appendChild(c); });
      // the picked thing, on parchment
      const picked = this.bagRow >= 0 ? g.bag[this.bagRow] : null, note = this.$("#bag-note");
      if (picked && note && note.textContent === CM.itemCard(picked)) { const name = picked.unknown ? CM.baseName(picked) : picked.name, body = CM.itemCard(picked).replace(name, "").replace(/^[\s:,.-]+/, "");
        note.innerHTML = `<b class="title rarity-${CM.rarityOf(picked)}">${this.esc(name)}</b>${this.esc(body)}`; }
    } catch (e) { /* (the game's own pack stands if anything here fails) */ }
    return out; };
}
