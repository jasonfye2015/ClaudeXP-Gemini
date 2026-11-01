"use strict";
// The South Fields, the village's hands - the window's side (v19.2): sprinklers and cloches in the view and on the
// board, the plan shown faint on empty plots, the board's modes (set a sprinkler, lift one, put on a cloche, plan a
// crop, clear a plan), the shed's workbench (sprinklers from bars, cloches, the seed-maker), the crew (hands, purse,
// silo), and "Tend everything". The rules are 69l-fieldhands.js.
{ const FH = CM.FIELDHANDS, CP = CM.cropPack;
  { const ps0 = CM.plotSprites; CM.plotSprites = (game, key, x, y) => { const P = game.fields().plots[key]; if (P && P.spr) return [{ x, y, layer: `sprinkler:${P.spr}`, w: 0.6, h: 0.6 }];
      const out = ps0(game, key, x, y); if (P && P.cloche) out.push({ x, y, layer: "cloche", w: 0.95, h: 0.95, alpha: 0.9 }); return out; }; }
  const picOf = (f) => { const A = CM.art.crops && CM.art.crops.atlas; if (!A || f === undefined) return ""; const [cw, ch] = CP.cell, c = document.createElement("canvas"); c.width = cw; c.height = ch; const p = c.getContext("2d"); p.imageSmoothingEnabled = false; p.drawImage(A, (f % CP.cols) * cw, Math.floor(f / CP.cols) * ch, cw, ch, 0, 0, cw, ch); return c.toDataURL(); };
  const planPics = new Map(), planPic = (crop) => { if (!planPics.has(crop)) planPics.set(crop, CP.frames[crop] ? picOf(CP.frames[crop].s[3]) : ""); return planPics.get(crop); };
  const MODES = { lift: "Lift a sprinkler", cloche: `Put on a cloche (${FH.clocheGold}g + ${FH.clocheStone} stone)`, plan: "Plan", unplan: "Clear a plan" };
  const rf0 = CM.UI.prototype.renderFields;
  Object.assign(CM.UI.prototype, {
    renderFields() { rf0.call(this); const g = this.game, box = this.$("#fd-body"); if (!box || g.fieldsLevel() < 1) return; const F = g.fields(), here = g.atFields(), mode = this.fdMode || "", spr = F.sprinklers || {};
      box.querySelectorAll("[data-fd]").forEach((b) => { const k = b.dataset.fd, P = F.plots[k] || {};
        if (P.spr) { b.classList.add("spr", `spr-${P.spr}`); b.innerHTML = "<i class='fdspr'></i>"; b.title = `${FH.SPRINKLERS[P.spr].name}: it waters ${FH.SPRINKLERS[P.spr].reach.length} plots round it at every dawn.`; }
        if (P.cloche) b.classList.add("cloche");
        if (P.plan && !P.crop && !P.spr) { b.insertAdjacentHTML("afterbegin", `<img class="fdplan" src="${planPic(P.plan)}" alt="">`); b.title += ` (planned: ${CM.CROPS[P.plan].name.toLowerCase()})`; }
        if (mode && mode !== "compost") { const nb = b.cloneNode(true); b.replaceWith(nb); nb.disabled = !here; nb.addEventListener("click", () => {
            const r = mode.startsWith("spr:") ? g.fieldSetSprinkler(k, mode.slice(4)) : mode === "lift" ? g.fieldLiftSprinkler(k) : mode === "cloche" ? g.fieldCloche(k) : mode === "plan" ? g.fieldPlan(k, this.fdPlanCrop || F.pick) : g.fieldPlan(k, null);
            this.fdNote = r || ""; if (mode.startsWith("spr:") && !((F.sprinklers || {})[mode.slice(4)] > 0)) this.fdMode = null; this.renderFields(); this.refresh && this.refresh(); }); } });
      const head = box.querySelector(".fdhead"); if (head) { const t = document.createElement("button"); t.textContent = "Tend everything"; t.className = "primary"; t.disabled = !here; t.title = "Pull the weeds, pick the ripe, sow the plan from the pack, and water as far as the can goes"; head.append(t); t.addEventListener("click", () => { g.fieldTendAll(); this.fdNote = ""; this.renderFields(); this.refresh && this.refresh(); }); }
      const crops = Object.keys(CM.CROPS).filter((c) => CP.frames[c]), planCrop = this.fdPlanCrop || F.pick || "";
      const hands = document.createElement("div"); hands.className = "fdhands";
      hands.innerHTML = `<div><div class="list-title">On the board</div><div class="fdmodes">${[...Object.keys(FH.SPRINKLERS).map((s) => [`spr:${s}`, `Set ${FH.SPRINKLERS[s].name.toLowerCase()} (${spr[s] || 0})`, !(spr[s] > 0)]), ...Object.entries(MODES).map(([m, w]) => [m, w, false])]
          .map(([m, w, off]) => `<button data-fdm="${m}" class="${mode === m ? "on" : ""}" ${here && !off ? "" : "disabled"}>${this.esc(w)}</button>`).join("")}
          <select data-fdplancrop>${crops.map((c) => `<option value="${c}" ${c === planCrop ? "selected" : ""}>${this.esc(CM.CROPS[c].name)}</option>`).join("")}</select>${mode ? `<button data-fdm="">Done</button>` : ""}</div>
          <div class="list-title">The workbench</div><div class="fdbench">${Object.entries(FH.SPRINKLERS).map(([s, S]) => `<button data-fdmake="${s}" ${here ? "" : "disabled"} title="a ${S.bars[0] === "stariron" ? "star-iron" : S.bars.join(" or ")} bar and ${S.gold} gold; waters ${S.reach.length} plots">Make ${/^[aeiou]/i.test(S.name) ? "an" : "a"} ${S.name.toLowerCase()}</button>`).join("")}
            ${(() => { const mine = [...new Set(g.bag.filter((i) => i.kind === "ingredient" && CM.CROPS[i.ingredient]).map((i) => i.ingredient))]; return mine.length ? `<span class="small">Seed-maker (one picked makes two seeds):</span>${mine.map((c) => `<button data-fdseedmk="${c}" ${here ? "" : "disabled"}>${this.esc(CM.CROPS[c].name)}</button>`).join("")}` : `<span class="small">The seed-maker wants a crop from the pack.</span>`; })()}</div></div>
        <div><div class="list-title">The crew</div><p class="small">Each hand does ${FH.jobs} jobs a dawn - weeds, picking into the silo, sowing the plan, watering - for ${FH.wage} gold a dawn from their purse.</p>
          <div class="fdcrew">${[0, 1, 2, 3].map((n) => `<button data-fdhire="${n}" class="${(F.crew || 0) === n ? "on" : ""}" ${here ? "" : "disabled"}>${n ? `${n} hand${n > 1 ? "s" : ""}` : "None"}</button>`).join("")}</div>
          <p>Purse: <b>${F.purse || 0}</b> gold${F.unpaid ? " <em>(empty: they stood idle)</em>" : ""} <button data-fdpurse="50" ${here ? "" : "disabled"}>+50</button><button data-fdpurse="200" ${here ? "" : "disabled"}>+200</button><button data-fdpurse="-${F.purse || 0}" ${here && F.purse ? "" : "disabled"}>Take it back</button></p>
          <p>The silo: <b>${(F.silo || []).length}</b> of ${FH.silo} <button data-fdsilo ${here && (F.silo || []).length ? "" : "disabled"}>Take it all</button>${Object.values(F.seedBox || {}).some((n) => n > 0) ? ` <span class="small">seed box: ${Object.entries(F.seedBox).filter(([, n]) => n > 0).map(([c, n]) => `${n} ${CM.CROPS[c].name.toLowerCase()}`).join(", ")}</span>` : ""}</p></div>`;
      const care = box.querySelector(".fdcare") || box.querySelector(".fdgrid"); if (care) care.after(hands);
      hands.querySelectorAll("[data-fdm]").forEach((b) => b.addEventListener("click", () => { this.fdMode = b.dataset.fdm || null; this.renderFields(); }));
      hands.querySelector("[data-fdplancrop]").addEventListener("change", (e) => { this.fdPlanCrop = e.target.value; this.fdMode = "plan"; this.renderFields(); });
      const act = (sel, fn) => hands.querySelectorAll(sel).forEach((b) => b.addEventListener("click", () => { this.fdNote = fn(b) || ""; this.renderFields(); this.refresh && this.refresh(); }));
      act("[data-fdmake]", (b) => g.fieldMakeSprinkler(b.dataset.fdmake)); act("[data-fdseedmk]", (b) => g.fieldSeedMaker(b.dataset.fdseedmk)); act("[data-fdhire]", (b) => g.fieldHire(Number(b.dataset.fdhire)));
      act("[data-fdpurse]", (b) => g.fieldPurse(Number(b.dataset.fdpurse))); act("[data-fdsilo]", () => g.fieldTakeSilo()); },
  });
}
