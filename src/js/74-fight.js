"use strict";
// The fight: whose turn it is, what they'll do, at whom.
Object.assign(CM.UI.prototype, {
  // ---- the fight: whose turn it is, what they'll do, at whom ----
  renderCombat() {
    const g = this.game, box = this.$("#actions"), c = g.combat || {}, h = c.waiting;
    box.classList.add("combat");
    box.dataset.mode = "combat";
    box.innerHTML = "";
    const turn = document.createElement("div");
    turn.className = "turn";
    turn.innerHTML = h ? `Round ${c.round || 1} <small>-</small> ${this.esc(h.name)}'s turn` : `Round ${c.round || 1} <small>- the foes move</small>`;
    box.appendChild(turn);
    const ground = g.terrainNote();
    if (ground) { const t = document.createElement("div"); t.className = "ground"; t.textContent = ground + "."; box.appendChild(t); }
    const menu = document.createElement("div");
    menu.className = "menu";
    const btn = (html, fn, disabled, cls) => {
      const b = document.createElement("button");
      b.innerHTML = html;
      b.disabled = Boolean(disabled);
      if (cls) b.className = cls;
      b.addEventListener("click", fn);
      menu.appendChild(b);
      return b;
    };
    const cm = this.cmenu || { kind: "main" };
    if (h && cm.kind === "main") {
      btn("<kbd>F</kbd>Fight", () => g.act("fight", g.target));
      btn("<kbd>C</kbd>Cast / Skill", () => this.combatMenu("cast"), !CM.abilitiesFor(h).length);
      btn("<kbd>P</kbd>Item", () => this.combatMenu("item"));
      btn("<kbd>D</kbd>Defend", () => g.act("defend"));
      btn("<kbd>R</kbd>Run", () => g.act("run"));
      btn(`<kbd>A</kbd>${c.auto ? "Stop auto" : "Auto"}`, () => g.autoFight(!c.auto), false, c.auto ? "on" : "");
    } else if (h && cm.kind === "cast") {
      CM.abilitiesFor(h).forEach((id, i) => {
        const a = CM.ABILITIES[id], used = a.once && h.used && h.used[id], cost = g.spellCost(h, Object.assign({ id }, a), 1), poor = h.mp < cost, est = g.spellEstimate(h, id), lvl = (h.spellLevels || {})[id] || 1;
        const b = btn(`<kbd>${i + 1}</kbd>${a.name}${lvl > 1 ? ` <small>lv ${lvl}</small>` : ""}<small>${a.mp ? cost + " MP - " : ""}${used ? "used this fight" : a.what}${est ? ` <i>(${est})</i>` : ""}</small>`, () => this.castPick(id), used || poor, "pick");
        const ic = CM.art.spellIcon(id, 18, g.settings.look);
        if (ic) { ic.className = "icon"; b.insertBefore(ic, b.firstChild.nextSibling); }
        if (a.mp && !used) {                                            // overcast: more magic in for more out; a reagent from the pack
          const wrap = document.createElement("span"); wrap.className = "overcast";
          for (const p of [2, 3]) { const c2 = g.spellCost(h, Object.assign({ id }, a), p); const o = document.createElement("button"); o.textContent = `x${p} (${c2})`; o.title = `${CM.OVERCAST[p].mult * 100 - 100}% more, for ${c2} MP${p === 3 ? "; it may bite back" : ""}`; o.disabled = h.mp < c2; o.addEventListener("click", () => this.castPick(id, p)); wrap.appendChild(o); }
          const rg = g.reagentFor(id);
          if (rg) { const o = document.createElement("button"); o.textContent = `+ ${CM.INGREDIENTS[rg.id].name}`; o.title = CM.REAGENTS[rg.id].what; o.disabled = poor; o.addEventListener("click", () => this.castPick(id, 1, rg.row)); wrap.appendChild(o); }
          menu.appendChild(wrap);
        }
      });
      btn("<kbd>Esc</kbd>Back", () => this.combatMenu("main"));
    } else if (h && cm.kind === "item") {
      const rows = this.usableRows();
      rows.forEach((row, i) => btn(`<kbd>${i + 1}</kbd>${this.esc(g.bag[row].name)}<small>${g.describe(g.bag[row])}</small>`, () => this.itemPick(row), false, "pick"));
      if (!rows.length) { const none = document.createElement("span"); none.className = "small"; none.textContent = "Nothing in the pack for a fight."; menu.appendChild(none); }
      btn("<kbd>Esc</kbd>Back", () => this.combatMenu("main"));
    } else if (h && cm.kind === "ally") {
      g.party.forEach((p, i) => btn(`<kbd>${i + 1}</kbd>${this.esc(p.name)}<small>${p.hp <= 0 ? "fallen" : `${p.hp}/${p.max}`}</small>`,
        () => this.allyPick(i), cm.fallen ? p.hp > 0 : p.hp <= 0, "pick"));
      btn("<kbd>Esc</kbd>Back", () => this.combatMenu("main"));
    }
    box.appendChild(menu);
    const targets = document.createElement("div");
    targets.className = "targets";
    g.attackable().forEach((m, i) => {
      const b = document.createElement("button");
      b.className = i === (g.target || 0) ? "chosen" : "";
      const est = h ? g.strikeEstimate(h, m) : null;
      const marks = [m.asleep > 0 ? `asleep ${m.asleep}` : "", m.held > 0 ? `held ${m.held}` : "", m.marked ? "marked" : "", m.blind > 0 ? `blinded ${m.blind}` : "", m.burning > 0 ? `burning ${m.burning}` : "",
        m.chilled > 0 ? `chilled ${m.chilled}` : "", m.warded > 0 ? "warded" : ""].filter(Boolean);
      const behind = m.row === "back" && g.living().some((f) => f !== m && f.row !== "back");
      b.innerHTML = `${this.esc(m.name)}${behind ? " <small>(behind)</small>" : ""} <small>${Math.max(0, m.hp)}/${m.max}${marks.length ? " - " + marks.join(", ") : ""}</small>${m.intent ? `<i class="odds intent">about to: ${this.esc((m.intent.text || "").split("!")[0].split(",")[0].replace(/^The [A-Za-z- ]+ /, "")) || "something terrible"}</i>` : ""}${est ? `<i class="odds">${Math.round(est.hit * 100)}% to hit, ${est.low}-${est.high}</i>` : ""}`;
      b.addEventListener("click", () => g.setTarget(i));
      targets.appendChild(b);
    });
    box.appendChild(targets);
  },

  combatMenu(kind, data) { this.cmenu = Object.assign({ kind }, data || {}); this.renderCombat(); },
  usableRows() { return this.game.bag.map((it, i) => (["heal", "greaterheal", "mana", "antidote", "revive", "bomb"].includes(it.kind) ? i : -1)).filter((i) => i >= 0); },

  castPick(id, power = 1, reagent) {
    const g = this.game, a = CM.ABILITIES[id];
    if (a.target === "ally" || a.target === "fallen") { this.combatMenu("ally", { id, power, reagent, fallen: a.target === "fallen" }); return; }
    g.act("cast", Object.assign(a.target === "foe" ? { id, target: g.target } : { id }, power > 1 ? { power } : {}, reagent !== undefined ? { reagent } : {}));
    this.refresh();
  },

  itemPick(row) { if (this.game.bag[row].kind === "bomb") { this.game.act("item", { row }); this.refresh(); return; } this.combatMenu("ally", { row, fallen: this.game.bag[row].kind === "revive" }); },

  allyPick(i) {
    const cm = this.cmenu || {};
    if (cm.row !== undefined) this.game.act("item", { row: cm.row, who: i });
    else this.game.act("cast", Object.assign({ id: cm.id, target: i }, cm.power > 1 ? { power: cm.power } : {}, cm.reagent !== undefined ? { reagent: cm.reagent } : {}));
    this.refresh();
  },

  // a number key in a fight: the chosen foe, or a pick from the open list
  pick(n) {
    const g = this.game, cm = this.cmenu || { kind: "main" };
    if (cm.kind === "main") { g.setTarget(n - 1); return true; }
    const buttons = [...this.$("#actions .menu").querySelectorAll("button.pick")], b = buttons[n - 1];
    if (b && !b.disabled) { b.click(); return true; }
    return false;
  },
});
