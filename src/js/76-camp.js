"use strict";
// The camp's doors: the tavern, the smith, the alchemist, the vault, the waystones.
Object.assign(CM.UI.prototype, {
  // ---- the waystones ----
  openWaystone() { this.renderWaystone(); this.openDialog("#dlg-waystone"); },
  openSecond() {
    const g = this.game, box = this.$("#second-list");
    box.innerHTML = "";
    g.party.forEach((h, i) => {
      const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      const can = h.hp > 0 && h.level >= CM.SECOND_AT && !h.second;
      row.innerHTML = `<div><b>${this.esc(h.name)}</b> <small>${h.cls}, level ${h.level}${h.second ? ` - and ${h.second}` : can ? "" : h.level < CM.SECOND_AT ? ` - at ${CM.SECOND_AT}` : ""}</small></div>`;
      if (can) { const sel = document.createElement("select"); sel.innerHTML = ["<option value=''>Choose...</option>"].concat(g.classesAvailable().filter((c) => c !== h.cls).map((c) => `<option value="${c}">${c}, ${CM.SECOND_COST} renown</option>`)).join(""); sel.addEventListener("change", () => { if (!sel.value) return; this.$("#second-note").textContent = g.secondCalling(i, sel.value) || "Done."; this.openSecond(); }); row.appendChild(sel); }
      box.appendChild(row);
    });
    this.$("#second-note").textContent = `Renown: ${g.renown()}. ${g.villageLevel("guildhall") < 2 ? "The guildhall must be of the second level." : ""}`;
    this.openDialog("#dlg-second");
  },
  renderWaystone() {
    const g = this.game, box = this.$("#waystone-list"), camps = g.camps || [];
    box.innerHTML = "";
    for (const n of camps) {
      const row = document.createElement("div");
      row.className = "recruit";
      row.style.gridTemplateColumns = "1fr auto";
      row.innerHTML = `<div><b>The camp below floor ${n}</b><small>${this.esc(CM.themeFor(n).name)}${g.floor && g.floor.number === n ? " - you are here" : ""}</small></div>`;
      const b = document.createElement("button");
      b.textContent = "Walk the old road";
      b.disabled = Boolean(g.floor && g.floor.number === n);
      b.addEventListener("click", () => { const note = g.waystone(n); if (note) this.$("#waystone-note").textContent = note; else this.closeDialogs(); this.refresh(); });
      row.appendChild(b);
      box.appendChild(row);
    }
    if (!camps.length) box.innerHTML = `<div class="small">No mark yet.</div>`;
    this.$("#waystone-note").textContent = "";
  },

  // ---- the tavern ----
  openTavern() {
    this.renderTavern();
    this.openDialog("#dlg-tavern");
  },

  renderTavern() {
    const g = this.game, box = this.$("#recruits");
    const fallen = g.party.map((h, i) => i).filter((i) => g.party[i].hp <= 0 || (g.party[i].status || {}).stone);
    box.innerHTML = "";
    g.tavern().forEach((r, i) => {
      const div = document.createElement("div");
      div.className = "recruit";
      div.appendChild(this.portrait(r.cls, 40));
      const text = document.createElement("div");
      text.innerHTML = `<b>${this.esc(r.name)}</b> the ${r.cls}, level ${r.level} <small>${r.max} health${r.maxmp ? `, ${r.maxmp} magic` : ""}, attack ${r.atk}, defence ${r.df} - ${CM.STATS.map((s) => `${CM.STAT_NAMES[s].slice(0, 3)} ${r.stats[s]}`).join(" ")}</small>`;
      div.appendChild(text);
      const hire = document.createElement("div");
      hire.className = "hire";
      if (fallen.length <= 1) {
        const b = document.createElement("button");
        b.textContent = r.price ? `Hire, ${r.price} gold` : "Hire - owes you their life";
        b.disabled = !fallen.length;
        b.addEventListener("click", () => { const note = g.hire(i); this.$("#tavern-note").textContent = note || `${r.name} comes along.`; this.renderTavern(); this.refresh(); });
        hire.appendChild(b);
      } else {
        for (const idx of fallen) {
          const b = document.createElement("button");
          b.textContent = r.price ? `For ${g.party[idx].name}, ${r.price} gold` : `For ${g.party[idx].name} - owes you their life`;
          b.addEventListener("click", () => { const note = g.hire(i, idx); this.$("#tavern-note").textContent = note || `${r.name} comes along.`; this.renderTavern(); this.refresh(); });
          hire.appendChild(b);
        }
      }
      div.appendChild(hire);
      box.appendChild(div);
    });
    if (!box.children.length) box.innerHTML = "<div class='small'>The benches are empty tonight.</div>";
    const fence = this.$("#fence"); fence.innerHTML = "<div class='head'>The fence, in the corner</div>";
    g.bag.forEach((it, row) => { if (!it.unknown && !(it.props && it.props.cursed)) return; const b = document.createElement("button"); b.textContent = it.unknown ? `${CM.baseName(it)} (unknown): ${Math.floor(it.value / 2)} gold` : `${it.name} (cursed): takes it for nothing`; b.addEventListener("click", () => { this.$("#tavern-note").textContent = g.fence(row) || "Done."; this.renderTavern(); this.refresh(); }); fence.appendChild(b); });
    { const b = document.createElement("button"); b.textContent = g.rumourBox ? `A rumour, bought: floor ${g.rumourBox}` : `A rumour of a strongbox (${CM.RUMOUR_PRICE} gold)`; b.disabled = Boolean(g.rumourBox); b.addEventListener("click", () => { this.$("#tavern-note").textContent = g.fenceRumour() || "Done."; this.renderTavern(); this.refresh(); }); fence.appendChild(b); }
    this.$("#tavern-note").textContent = fallen.length ? "" : "The party is whole; the recruits drink to that.";
  },

  // ---- the camp's smith and vault ----
  openSmith() { this.renderSmith(); this.openDialog("#dlg-smith"); },
  renderSmith() {
    const g = this.game, box = this.$("#smith-list");
    const diamonds = g.bag.filter((i) => i.kind === "gem" && i.gem === "diamond").length;
    const gems = g.bag.filter((i) => i.kind === "gem" && CM.GEMS[i.gem].element).map((i) => i.name), anyGem = g.bag.some((i) => i.kind === "gem");
    const scrap = g.bag.filter((i) => i.kind === "scrap").length;
    this.$("#smith-gems").textContent = `In the pack: ${diamonds ? CM.plural(diamonds, "diamond") : "no diamond"}${gems.length ? ", " + gems.join(", ") : ""}${scrap ? `, ${CM.plural(scrap, "piece")} of scrap` : ""}. Gold: ${g.gold.toLocaleString()}.`;
    box.innerHTML = "";
    g.party.forEach((h, hi) => {
      for (const slot of ["weapon", "armor", "offhand", "helm"]) {
        const it = h[slot];
        if (!it) continue;
        const row = document.createElement("div");
        row.className = "recruit";
        row.appendChild(this.icon(it, 22));
        const text = document.createElement("div");
        const n = (it.props || {}).enchant || 0;
        text.innerHTML = `<b>${this.esc(it.unknown ? CM.baseName(it) : it.name)}</b> <small>${this.esc(h.name)}'s ${CM.SLOT_NAMES[slot].toLowerCase()} - ${this.esc(CM.itemLabel(it))}${n ? ` - the smith's work: +${n}` : ""}</small>`;
        row.appendChild(text);
        const act = document.createElement("div");
        act.className = "hire";
        const b = document.createElement("button");
        b.textContent = n >= CM.SMITH.most ? "Worked to the limit" : `+1 for ${CM.SMITH.enchant * (n + 1)} gold and a diamond`;
        b.disabled = n >= CM.SMITH.most || (!diamonds && scrap < 5) || g.gold < CM.SMITH.enchant * (n + 1) || it.unknown;
        b.addEventListener("click", () => { this.$("#smith-note").textContent = g.smith("enchant", hi, slot) || "Done."; this.renderSmith(); this.refresh(); });
        act.appendChild(b);
        if (slot === "weapon") {
          const s = document.createElement("button");
          s.textContent = `Set a gem for ${CM.SMITH.gem} gold`;
          s.disabled = !gems.length || g.gold < CM.SMITH.gem || it.unknown;
          s.title = "The first ruby, sapphire or sunstone in the pack goes in: fire, frost or holiness";
          s.addEventListener("click", () => { this.$("#smith-note").textContent = g.smith("gem", hi, slot) || "Done."; this.renderSmith(); this.refresh(); });
          act.appendChild(s);
        }
        if (!(it.props && (it.props.relic || it.props.unique))) {
          const r = document.createElement("button");
          r.textContent = "Rework the suffix: a gem and 100 gold";
          r.disabled = !anyGem || g.gold < 100 || it.unknown;
          r.title = "The suffix is struck off and another worked in, from the dice";
          r.addEventListener("click", () => { this.$("#smith-note").textContent = g.smith("reroll", hi, slot) || "Done."; this.renderSmith(); this.refresh(); });
          act.appendChild(r);
          const mv = document.createElement("button");
          mv.textContent = "Move a prefix here: a worded thing from the pack and 150 gold";
          mv.disabled = g.gold < 150 || it.unknown || !g.bag.some((i) => ["weapon", "armor", "shield", "helm"].includes(i.kind) && !i.unknown && (i.props || {}).affixes && i.props.affixes.some((w) => !w.startsWith("of ")) && (i.kind === "weapon") === (it.kind === "weapon"));
          mv.title = "The first prefixed thing of the same kind of make in the pack gives up its word, and becomes scrap";
          mv.addEventListener("click", () => { this.$("#smith-note").textContent = g.smith("move", hi, slot) || "Done."; this.renderSmith(); this.refresh(); });
          act.appendChild(mv);
        }
        row.appendChild(act);
        box.appendChild(row);
      }
    });
    if (g.bag.some((i) => i.kind === "wand")) {                          // a wand charged: a gem and 60 gold for three
      const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      row.innerHTML = `<div><b>Charge a wand</b> <small>${g.bag.filter((i) => i.kind === "wand").map((w) => `${this.esc(w.name)} (${CM.plural(w.charges || 0, "charge")})`).join(", ")}</small></div>`;
      const b = document.createElement("button"); b.textContent = "Charge the first wand: a gem and 60 gold"; b.disabled = !g.bag.some((i) => i.kind === "gem") || g.gold < 60;
      b.addEventListener("click", () => { this.$("#smith-note").textContent = g.smith("recharge", 0, "weapon") || "Done."; this.renderSmith(); this.refresh(); });
      row.appendChild(b); box.appendChild(row);
    }
    const scrapRows = g.bag.map((it, i) => [it, i]).filter(([it]) => ["weapon", "armor", "shield", "helm"].includes(it.kind) && !(it.props && (it.props.relic || it.props.unique)));
    if (scrapRows.length) {
      const title = document.createElement("div");
      title.className = "list-title";
      title.textContent = `Into the fire for scrap (${g.bag.filter((i) => i.kind === "scrap").length} in the pack; five stand in for a diamond)`;
      box.appendChild(title);
      for (const [it, i] of scrapRows) {
        const row = document.createElement("div");
        row.className = "recruit";
        row.appendChild(this.icon(it, 22));
        const text = document.createElement("div");
        text.innerHTML = `<b>${this.esc(it.unknown ? CM.baseName(it) : it.name)}</b> <small>${this.esc(CM.itemLabel(it))}</small>`;
        row.appendChild(text);
        const act = document.createElement("div");
        act.className = "hire";
        const b = document.createElement("button");
        b.textContent = "Salvage";
        b.addEventListener("click", () => { this.$("#smith-note").textContent = g.salvage(i) || "Done."; this.renderSmith(); this.refresh(); });
        act.appendChild(b);
        row.appendChild(act);
        box.appendChild(row);
      }
    }
  },
  openAlchemist() { this.renderAlchemist(); this.openDialog("#dlg-alchemist"); },
  renderAlchemist() {
    const g = this.game, box = this.$("#alchemist-list");
    const have = g.bag.filter((i) => i.kind === "ingredient").map((i) => i.name);
    this.$("#alchemist-have").textContent = `In the pack: ${have.length ? have.join(", ") : "nothing she wants yet"}. Gold: ${g.gold.toLocaleString()}.${g.mode !== "camp" ? " (The field kit: a fifth over the camp's prices.)" : ""}`;
    box.innerHTML = "";
    if (g.mode === "camp") {                                             // her request
      const want = g.alchemistWants(), row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      row.innerHTML = `<div><b>She asks for three of ${this.esc(CM.INGREDIENTS[want].name)}</b><small>bring them, and the next brew is free${g.alchemistFree ? " - as it is now" : ""}</small></div>`;
      const b = document.createElement("button"); b.textContent = "Hand them over"; b.disabled = g.bag.filter((i) => i.kind === "ingredient" && i.ingredient === want).length < 3 || g.alchemistFree;
      b.addEventListener("click", () => { this.$("#alchemist-note").textContent = g.deliver() || "Done."; this.renderAlchemist(); this.refresh(); });
      row.appendChild(b); box.appendChild(row);
    }
    const meats = g.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "meat");
    for (const [it, i] of meats) {                                       // the kitchen
      const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      row.innerHTML = `<div><b>Cook the ${this.esc(it.name)}</b><small>${this.esc((CM.MEALS[it.meat] || {}).what || "")}, the next floor; everyone eats</small></div>`;
      const b = document.createElement("button"); b.textContent = g.mode === "camp" ? "Cook" : "Cook, for a torch"; b.disabled = g.mode !== "camp" && !g.bag.some((x) => x.kind === "torch");
      b.addEventListener("click", () => { this.$("#alchemist-note").textContent = g.cook(i) || "Done."; this.renderAlchemist(); this.refresh(); });
      row.appendChild(b); box.appendChild(row);
    }
    for (const [id, r] of Object.entries(CM.RECIPES)) {
      const row = document.createElement("div");
      row.className = "recruit";
      row.style.gridTemplateColumns = "1fr auto";
      const lacks = g.recipeLacks(id);
      row.innerHTML = `<div><b>${this.esc(r.name)}</b><small>${this.esc(r.what)}${lacks ? ` <i>- ${this.esc(lacks)}</i>` : ""}</small></div>`;
      const b = document.createElement("button");
      b.textContent = `Brew, ${g.alchemistFree ? "free" : `${Math.ceil(r.gold * (g.mode !== "camp" ? CM.KIT_PRICE : 1))} gold`}`;
      b.disabled = Boolean(lacks);
      b.addEventListener("click", () => { this.$("#alchemist-note").textContent = g.brew(id) || "Done."; this.renderAlchemist(); this.refresh(); });
      row.appendChild(b);
      box.appendChild(row);
    }
  },
  openVault() { this.renderVault(); this.openDialog("#dlg-vault"); },
  renderVault() {
    const g = this.game, held = this.$("#vault-held"), list = this.$("#vault-list");
    held.innerHTML = "";
    held.style.display = "block";
    (g.vaults || []).forEach((it, i) => {
      const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "40px 1fr auto";
      row.appendChild(this.icon(it, 22));
      const text = document.createElement("span");
      text.innerHTML = `<b class="rarity-${CM.rarityOf(it)}">${this.esc(it.name)}</b> <small>${this.esc(CM.itemLabel(it))}</small> `;
      row.appendChild(text);
      const b = document.createElement("button");
      b.textContent = "Take it";
      b.addEventListener("click", () => { this.$("#vault-note").textContent = g.takeHeirloom(i) || "Taken."; this.renderVault(); this.refresh(); });
      row.appendChild(b); held.appendChild(row);
    });
    if (!(g.vaults || []).length) held.innerHTML = `<span class="small">The vault is empty (${g.vaultCapacity()} ${g.vaultCapacity() === 1 ? "slot" : "slots"}). Leave something here, and the next party to come this way will find it.</span>`;
    else { const n = document.createElement("div"); n.className = "small"; n.textContent = `${g.vaults.length} of ${g.vaultCapacity()} slots.`; held.appendChild(n); }
    list.innerHTML = "";
    g.bag.forEach((it, i) => {
      if (["key", "bones", "rope", "torch"].includes(it.kind)) return;
      const row = document.createElement("div");
      row.className = "recruit";
      row.appendChild(this.icon(it, 22));
      const text = document.createElement("div");
      text.innerHTML = `<b>${this.esc(it.unknown ? CM.baseName(it) : it.name)}</b> <small>${this.esc(CM.itemLabel(it))}</small>`;
      row.appendChild(text);
      const act = document.createElement("div");
      act.className = "hire";
      const b = document.createElement("button");
      b.textContent = g.vaultRoom() ? "Leave it" : "Leave it (the oldest comes back)";
      b.addEventListener("click", () => { this.$("#vault-note").textContent = g.leaveHeirloom(i) || "Left for those who come after."; this.renderVault(); this.refresh(); });
      act.appendChild(b);
      row.appendChild(act);
      list.appendChild(row);
    });
    if (!list.children.length) list.innerHTML = `<div class="small">Nothing in the pack worth the keeping.</div>`;
  },
});
