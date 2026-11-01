"use strict";
// The South Fields, the window's side (v19.0): opened at the shed, from a plot whose seed isn't chosen yet, or from the
// menu while at the fields. A top-down board of every plot - its crop drawn from the crop pack at its stage, wet earth
// where it's watered - where a click does the plot's next job (turn, sow, water, pick); the seeds in the pack to choose
// from; the shed's shelf of the season's seeds; the can and the trough. The rules are 69j-fields.js.
{ const FD = CM.SOUTHFIELDS, CP = CM.cropPack;
  const ensure = (ui) => { if (ui.$("#dlg-fields")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-fields";
    d.innerHTML = `<div class="box journalbox fdbox"><h2>The South Fields</h2><div id="fd-body"></div><div class="row"><button data-fdclose>Close</button></div></div>`;
    (ui.root || document.body).appendChild(d); d.querySelector("[data-fdclose]").addEventListener("click", () => ui.closeDialogs()); };
  // a plot's picture, cut from the crop atlas
  const pic = (frame) => { const A = CM.art.crops && CM.art.crops.atlas; if (!A || frame === null || frame === undefined) return ""; const [cw, ch] = CP.cell, fx = (frame % CP.cols) * cw, fy = Math.floor(frame / CP.cols) * ch;
    const c = document.createElement("canvas"); c.width = cw; c.height = ch; const p = c.getContext("2d"); p.imageSmoothingEnabled = false; p.drawImage(A, fx, fy, cw, ch, 0, 0, cw, ch); return c.toDataURL(); };
  const cache = new Map(), picOf = (f) => { if (!cache.has(f)) cache.set(f, pic(f)); return cache.get(f); };
  const seasonWord = { spring: "Spring", summer: "Summer", autumn: "Autumn", winter: "Winter" };
  Object.assign(CM.UI.prototype, {
    openFields(focus) { ensure(this); this.fdFocus = focus || null; this.renderFields(); this.openDialog("#dlg-fields"); },
    renderFields() { const g = this.game, box = this.$("#fd-body"); if (!box) return; const L = g.fieldsLevel(), F = g.fields(), here = g.atFields(), season = CM.season(g);
      if (L < 1) { box.innerHTML = `<p class="lore">The bowl under the south wall is rough grass and old stones. The village could make farmland of it (the village's window: The South Fields).</p>`; return; }
      g.fieldsDawns && g.fieldsDawns();
      const R = FD.rects[L], cells = CM.fieldCells(L), seeds = {}; for (const it of g.bag) if (it.kind === "seed" && CM.CROPS[it.crop]) seeds[it.crop] = (seeds[it.crop] || 0) + 1;
      const ripe = cells.filter(([x, y]) => g.plotStage(`${x},${y}`) === "ripe").length, dry = cells.filter(([x, y]) => { const P = F.plots[`${x},${y}`]; return P && P.crop && !P.ripe && !P.w; }).length;
      const plot = (x, y) => { const k = `${x},${y}`, P = F.plots[k] || {}, st = g.plotStage(k), K = P.crop && CM.CROPS[P.crop], f = CM.plotFrame ? CM.plotFrame(g, k) : null, job = g.fieldNext(k);
        const tip = st === "bare" ? "Rough ground: click to turn it" : !P.crop ? "Turned earth: click to sow" : `${K.name}: ${st === "ripe" ? "ripe - click to pick" : `${st === "sown" || st === "after" ? "just in" : "growing"}, ${Math.max(0, (P.need || K.days) - (P.g || 0))} watered day${(P.need || K.days) - (P.g || 0) === 1 ? "" : "s"} to go${P.w ? " (watered today)" : " - click to water"}`}`;
        return `<button class="fdplot ${st === "bare" ? "bare" : "tilled"}${P.w ? " wet" : ""}${st === "ripe" ? " ripe" : ""}${this.fdFocus === k ? " focus" : ""}" data-fd="${k}" title="${this.esc(tip)}" ${here ? "" : "disabled"}>${f !== null && f !== undefined ? `<img src="${picOf(f)}" alt="">` : ""}${job === "water" ? "<i class='fdthirst'></i>" : ""}</button>`; };
      let grid = ""; for (let y = R[1]; y <= R[3]; y++) { grid += `<div class="fdrow">`; for (let x = R[0]; x <= R[2]; x++) grid += plot(x, y); grid += `</div>`; }
      const shelf = g.shedSeeds().map((c) => `<div class="fdseed"><span>${this.esc(CM.CROPS[c].name)}</span><small>${CM.CROPS[c].days} days${CM.CROPS[c].regrow ? `, again every ${CM.CROPS[c].regrow}` : ""}; ${CM.CROPS[c].yields} a plot at ${CM.CROPS[c].price}g</small><b>${g.seedPrice(c)}g</b><button data-fdbuy="${c}" data-n="1" ${here ? "" : "disabled"}>Buy 1</button><button data-fdbuy="${c}" data-n="5" ${here ? "" : "disabled"}>5</button></div>`).join("");
      box.innerHTML = `<div class="fdhead"><span>${seasonWord[season]}${season === "winter" ? " - only the winter crops grow" : ""}</span><span>${ripe} ripe · ${dry} to water</span><span class="fdcan">${F.can ? `The can: <b>${F.water}</b> of ${FD.can}` : "No can yet"}</span>
          ${F.can ? `<button data-fdfill ${here && F.water < FD.can ? "" : "disabled"}>Fill at the trough</button>` : `<button data-fdcan ${here ? "" : "disabled"}>Buy a can (${FD.canGold}g)</button>`}<button data-fdwaterall ${here && F.can && dry ? "" : "disabled"}>Water what the can will</button><button data-fdpickall ${here && ripe ? "" : "disabled"}>Pick everything ripe</button></div>
        ${here ? "" : `<p class="note">You're not at the fields: the board shows them, but the work wants you there (the World map has them).</p>`}
        <div class="fdcols"><div class="fdgrid">${grid}</div><div class="fdside"><div><div class="list-title">Sowing</div>${Object.keys(seeds).length ? Object.entries(seeds).map(([c, n]) => `<button class="fdpick${F.pick === c ? " on" : ""}" data-fdpick="${c}" ${CM.CROPS[c].sow.includes(season) ? "" : `disabled title="${this.esc(`${CM.CROPS[c].name} is sown in ${CM.CROPS[c].sow.join(" or ")}`)}"`}>${this.esc(CM.CROPS[c].name)} <b>${n}</b></button>`).join("") : `<p class="small">No seeds in the pack.</p>`}
          <p class="small">A click on turned earth sows ${F.pick && CM.CROPS[F.pick] ? `<b>${this.esc(CM.CROPS[F.pick].name.toLowerCase())}</b>` : "the seed chosen here"}. Space on a plot underfoot does the same.</p>
          </div><div><div class="list-title">The shed's shelf (${seasonWord[season].toLowerCase()})</div><div class="fdshelf">${shelf || `<p class="small">Nothing to sow this season.</p>`}</div></div></div></div>
        <div class="note" id="fd-note">${this.esc(this.fdNote || g.fieldsNote || "")}</div>`;
      const done = (r) => { this.fdNote = r || ""; this.renderFields(); this.refresh && this.refresh(); };
      box.querySelectorAll("[data-fd]").forEach((b) => b.addEventListener("click", () => { const k = b.dataset.fd; this.fdFocus = k; const r = g.fieldTend(k); if (r === "pick") return done("Choose a seed to sow (in the pack, or from the shed's shelf)."); done(r); }));
      box.querySelectorAll("[data-fdbuy]").forEach((b) => b.addEventListener("click", () => done(g.fieldBuy(b.dataset.fdbuy, Number(b.dataset.n)))));
      box.querySelectorAll("[data-fdpick]").forEach((b) => b.addEventListener("click", () => { F.pick = b.dataset.fdpick; done(""); }));
      const on = (sel, fn) => { const b = box.querySelector(sel); if (b) b.addEventListener("click", fn); };
      on("[data-fdfill]", () => done(g.fieldFill())); on("[data-fdcan]", () => done(g.fieldBuyCan()));
      on("[data-fdwaterall]", () => { let n = 0; for (const [x, y] of cells) { const k = `${x},${y}`; if (g.fieldNext(k) === "water" && F.water > 0 && !g.fieldWater(k)) n++; } done(n ? `${n} plot${n > 1 ? "s" : ""} watered.${F.water ? "" : " The can's empty."}` : "Nothing watered."); });
      on("[data-fdpickall]", () => { let n = 0; for (const [x, y] of cells) { const k = `${x},${y}`; if (g.plotStage(k) === "ripe" && !g.fieldPick(k)) n++; } done(`${n} plot${n > 1 ? "s" : ""} picked.`); }); },
  });
}
