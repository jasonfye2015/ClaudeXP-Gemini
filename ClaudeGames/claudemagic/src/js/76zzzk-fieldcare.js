"use strict";
// The South Fields, water and quality - the window's side (v19.1): weeds and withered plants on the plots (in the view
// and on the board), the giant drawn over its nine plots, each plot's stars-to-be in its note; the bin, "compost when
// sowing", a Compost mode for the board (a click composts instead of tending), and the shed's scarecrow.
{ const FC = CM.FIELDCARE, CP = CM.cropPack;
  // in the view
  { const ps0 = CM.plotSprites; CM.plotSprites = (game, key, x, y) => { const P = game.fields().plots[key];
      if (P && P.giant) { const out = ps0(game, key, x, y).filter((s) => s.layer === "shadow"); if (P.giant === key && CP.frames[P.crop]) out.push({ x, y, layer: `crop:${CP.frames[P.crop].s[3]}`, w: 1.9, h: 3.8, shade: 0.97 }); return out; }
      let out = ps0(game, key, x, y);
      if (P && P.t && !P.crop && P.withered && CP.frames[P.last]) out = out.concat([[-0.18, -0.1], [0.2, 0.14]].map(([dx, dz]) => ({ x, y, dx, dz, layer: `crop:${CP.frames[P.last].s[1]}`, w: 0.36, h: 0.72, shade: 0.42, tilt: 0.35 })));
      if (P && P.weed) out.push({ x, y, dx: 0.28, dz: -0.24, layer: "prop:weed", w: 0.32, h: 0.32 }, { x, y, dx: -0.3, dz: 0.26, layer: "prop:weed", w: 0.28, h: 0.28 });
      return out; }; }
  const rf0 = CM.UI.prototype.renderFields;
  Object.assign(CM.UI.prototype, {
    renderFields() { rf0.call(this); const g = this.game, box = this.$("#fd-body"); if (!box || g.fieldsLevel() < 1) return; const F = g.fields(), here = g.atFields();
      // each plot's marks: weeds, withered, a giant, its stars-to-be
      box.querySelectorAll("[data-fd]").forEach((b) => { const k = b.dataset.fd, P = F.plots[k]; if (!P) return;
        if (P.weed) { b.classList.add("weedy"); b.insertAdjacentHTML("beforeend", "<i class='fdweed'></i>"); b.title = `Weeds: click to pull them${P.crop ? " (it won't grow till they're out)" : ""}`; }
        if (!P.crop && P.withered) { b.classList.add("withered"); if (!P.weed) b.title = `The ${CM.CROPS[P.last] ? CM.CROPS[P.last].name.toLowerCase() : "crop"} withered (four dry days). Click to sow again.`; }
        if (P.giant) { b.classList.add("giant"); if (P.giant === k) b.insertAdjacentHTML("beforeend", "<i class='fdgiant'>GIANT</i>"); }
        if (P.crop && !P.weed) { const q = FC.quality(g, k); b.title += ` - it would be ${CM.stars ? CM.stars(q) : q} picked now${P.comp ? " (composted)" : ""}${P.rested ? " (rested soil)" : ""}${P.everDry ? " (it went dry once)" : ""}`; }
        if (P.comp) b.classList.add("comp");
        if (this.fdMode === "compost") { const nb = b.cloneNode(true); b.replaceWith(nb); nb.addEventListener("click", () => { this.fdNote = g.fieldCompost(k) || "Composted."; this.renderFields(); }); } });
      const binning = (F.bin || []).length, care = document.createElement("div"); care.className = "fdcare";
      care.innerHTML = `<span>The bin: <b>${F.trim || 0}</b>/${FC.binFor} trimmings${binning ? `, ${binning} load${binning > 1 ? "s" : ""} rotting` : ""}, <b>${F.compost || 0}</b> compost ready</span>
        <label><input type="checkbox" data-fdauto ${F.autoCompost ? "checked" : ""}> compost when sowing</label>
        <button data-fdmode class="${this.fdMode === "compost" ? "on" : ""}" ${here && F.compost > 0 ? "" : "disabled"}>${this.fdMode === "compost" ? "Compost mode: click a crop (done)" : "Compost a crop..."}</button>
        ${F.scarecrow ? "<span>A scarecrow keeps the crows off.</span>" : `<button data-fdcrow ${here ? "" : "disabled"}>Buy a scarecrow (${FC.scarecrowGold}g)</button>`}${F.best ? `<span>Best yet: ${CM.stars ? CM.stars(F.best) : F.best}${F.giants ? `, ${F.giants} giant${F.giants > 1 ? "s" : ""}` : ""}</span>` : ""}`;
      const head = box.querySelector(".fdhead"); if (head) head.after(care);
      care.querySelector("[data-fdauto]").addEventListener("change", (e) => { g.fieldAutoCompost(e.target.checked); this.renderFields(); });
      care.querySelector("[data-fdmode]").addEventListener("click", () => { this.fdMode = this.fdMode === "compost" ? null : "compost"; this.renderFields(); });
      const cb = care.querySelector("[data-fdcrow]"); if (cb) cb.addEventListener("click", () => { this.fdNote = g.fieldBuyScarecrow() || "The scarecrow goes up by the shed."; this.renderFields(); this.refresh && this.refresh(); }); },
  });
  const close0 = CM.UI.prototype.closeDialogs; CM.UI.prototype.closeDialogs = function () { this.fdMode = null; return close0.call(this); };
}
