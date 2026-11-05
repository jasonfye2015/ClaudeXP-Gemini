"use strict";
// The interface, closer to hand (v63.0, UPGRADE_PLAN_58.md): in a fight each foe's row carries a health bar and its
// marks as tags with tooltips (74-fight.js reads CM.foeMarks); in the pack a thing can be dragged onto a hero's card
// to give it (and, at the merchant's, onto the wares to sell it, or a ware onto the pack to buy it); and the way into
// and out of the real-time places (the Mage Tower, the cave, the Fortress, Claudeablo, Claudebros, Claudecraft) is a
// short fade rather than a cut.
{ const rowsShown = (ui, g) => { const F = CM.BAG_FILTERS[ui.bagFilter || "all"]; return g.bag.map((it, i) => i).filter((i) => !F.kinds || F.kinds.includes(g.bag[i].kind)); };
  const dragData = (e) => { try { return e.dataTransfer.getData("text/plain") || ""; } catch (err) { return ""; } };
  const wire = (el, over, drop) => { if (!el || el.dataset.dropWired) return; el.dataset.dropWired = "1";
    el.addEventListener("dragover", (e) => { if (!over()) return; e.preventDefault(); el.classList.add("drop-over"); });
    el.addEventListener("dragleave", () => el.classList.remove("drop-over"));
    el.addEventListener("drop", (e) => { el.classList.remove("drop-over"); const d = dragData(e); if (!d) return; e.preventDefault(); drop(d); }); };
  { const fb0 = CM.UI.prototype.fillBag; CM.UI.prototype.fillBag = function (...a) { const out = fb0.apply(this, a); const ui = this, g = this.game; try {
        const rows = rowsShown(ui, g), packList = ui.$("#bag-list"), shopList = ui.$("#shop-list");
        packList.querySelectorAll(".item").forEach((row, i) => { if (rows[i] === undefined) return; row.draggable = true; row.addEventListener("dragstart", (e) => { e.dataTransfer.setData("text/plain", `pack:${rows[i]}`); e.dataTransfer.effectAllowed = "move"; row.classList.add("dragging"); }); row.addEventListener("dragend", () => row.classList.remove("dragging")); });
        if (g.shopping && shopList) shopList.querySelectorAll(".item").forEach((row, i) => { row.draggable = true; row.addEventListener("dragstart", (e) => { e.dataTransfer.setData("text/plain", `shop:${i}`); e.dataTransfer.effectAllowed = "copy"; }); });
        const party = ui.$("#party"); if (party) party.querySelectorAll(".member").forEach((card, i) => wire(card, () => Boolean(g.bag.length), (d) => { const [kind, n] = d.split(":"); if (kind !== "pack") return; ui.note(g.give(Number(n), i)); ui.bagRow = -1; ui.fillBag(); }));
        wire(packList, () => Boolean(g.shopping && g.stock && g.stock.length), (d) => { const [kind, n] = d.split(":"); if (kind !== "shop") return; ui.shopRow = Number(n); ui.note(g.buy(Number(n))); ui.fillBag(); });
        if (shopList) wire(shopList, () => Boolean(g.shopping), (d) => { const [kind, n] = d.split(":"); if (kind !== "pack") return; ui.note(g.sell(Number(n))); ui.bagRow = -1; ui.fillBag(); });
      } catch (e) { /* the drag is a nicety: the clicks still work */ } return out; }; }
  // the fade between the floor and a real-time place, either way
  { const sm0 = CM.Game.prototype.setMode; CM.Game.prototype.setMode = function (mode) { const was = this.mode, R = CM.REALTIME_MODES || []; const out = sm0.call(this, mode);
      try { if (CM.transit && CM.transit.floor && !CM.reducedMotion && was !== mode && (R.includes(mode) || R.includes(was)) && mode !== "title" && was !== "title") CM.transit.floor(); } catch (e) { /* no fade, no matter */ }
      return out; }; }
}
