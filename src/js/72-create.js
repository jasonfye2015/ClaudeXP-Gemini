"use strict";
// Who goes down: the creation screen.
Object.assign(CM.UI.prototype, {
  // ---- who goes down: the creation screen ----
  _create() {
    const g = this.game;
    this.slots = [];
    this.$("#btn-suggest").addEventListener("click", () => { this.fillSlots(CM.CLASSIC); this.renderCreate(); });
    this.$("#btn-reroll-all").addEventListener("click", () => { for (const s of this.slots) s.stats = CM.rollStats(s.cls); this.renderCreate(); });
    this.$("#btn-create-back").addEventListener("click", () => this.show("title"));
    this.$("#btn-setout").addEventListener("click", () => this.setOut());
    this.$("#create-seed").addEventListener("input", () => { this.$("#seed").value = this.$("#create-seed").value; this.renderCreateNote(); });
    this.$("#difficulty").innerHTML = Object.entries(CM.DIFFICULTIES).map(([id, d]) => `<option value="${id}">${d.name}</option>`).join("");
    this.$("#difficulty").value = "fair";
    this.$("#difficulty").addEventListener("change", () => this.renderCreateNote());
    this.$("#mode").addEventListener("change", () => this.renderCreateNote());
    this.$("#ascension").addEventListener("change", () => this.renderCreateNote());
    this.$("#iron").addEventListener("change", () => this.renderCreateNote());
    for (const b of this.root.querySelectorAll("#fame .boards button")) b.addEventListener("click", () => { this.fameBoard = b.dataset.board; this.fameOpen = -1; this.refreshTitle(); });
    const slots = this.$("#slots");
    for (let i = 0; i < 4; i++) {
      const div = document.createElement("div");
      div.className = "slot";
      div.innerHTML = `<div class="top"><div class="portrait-slot"></div><div class="who"><input class="name" type="text" maxlength="14" spellcheck="false" title="Their name"><button class="dice" title="Another name">&#x2684;</button>
        <select class="cls" title="Their calling"></select></div></div>
        <div class="role"></div>
        <table class="stats"></table>
        <div class="derived"></div>
        <div class="rowpick"><span>Row:</span><button data-row="front">Front</button><button data-row="back">Back</button><button class="reroll">Reroll</button></div>`;
      div.querySelector(".name").addEventListener("input", (e) => { this.slots[i].name = e.target.value; this.renderAdvice(); });
      div.querySelector(".dice").addEventListener("click", () => { this.slots[i].name = CM.randomName(); this.renderCreate(); });
      div.querySelector(".cls").addEventListener("change", (e) => {
        const s = this.slots[i];
        s.cls = e.target.value; s.stats = CM.rollStats(s.cls); s.row = CM.CLASSES[s.cls].row;
        this.renderCreate();
      });
      div.querySelector(".reroll").addEventListener("click", () => { this.slots[i].stats = CM.rollStats(this.slots[i].cls); this.renderCreate(); });
      for (const b of div.querySelectorAll("button[data-row]")) b.addEventListener("click", () => { this.slots[i].row = b.dataset.row; this.renderCreate(); });
      slots.appendChild(div);
    }
    g.on("mode", (mode) => { if (mode !== "title") this.closeDialogs(); });
  },

  fillSlots(classes) {
    const rnd = new CM.Random(Math.floor(Math.random() * 4294967296));
    this.slots = classes.map((cls) => ({ cls, name: CM.randomName(rnd), stats: CM.rollStats(cls, rnd), row: CM.CLASSES[cls].row }));
  },

  openCreate() {
    const g = this.game;
    if (g.canContinue() && !window.confirm(`A run is waiting in expedition slot ${g.slot}. Start a new expedition there and let it go? (The other slots keep theirs.)`)) return;
    for (const sel of this.root.querySelectorAll("#slots select.cls")) sel.innerHTML = g.classesAvailable().map((c) => `<option value="${c}">${c}</option>`).join("");   // (the callings earned)
    const code = CM.parseRunCode(this.$("#seed").value);
    if (code) {                                                          // a run code: the seed, the party, the difficulty and the kit as they were
      this.$("#seed").value = code.seed;
      if (code.party) this.slots = code.party.filter((p) => g.classUnlocked(p.cls)).length === 4 ? code.party : code.party.map((p) => (g.classUnlocked(p.cls) ? p : Object.assign({}, p, { cls: "Knight", stats: CM.rollStats("Knight") })));
      this.$("#difficulty").value = code.difficulty; this.$("#mode").value = code.mode; this.chosenKit = code.kit;
    }
    this.$("#mode-awakened").disabled = !g.achievements.bottom;
    if (!g.achievements.bottom && this.$("#mode").value === "awakened") this.$("#mode").value = "dungeon";
    const asc = this.$("#ascension"), max = g.ascensionMax();
    asc.innerHTML = Array.from({ length: max + 1 }, (_, i) => `<option value="${i}">${i ? `A${i}: ${CM.ASCENSION[i - 1].name}` : "none"}</option>`).join("");
    asc.value = code && code.ascension <= max ? String(code.ascension) : String(this.lastAscension || 0);
    this.$("#iron").checked = Boolean(code && code.iron);
    this.$("#ascension").style.display = this.$("#ascension-label").style.display = max ? "" : "none";
    const weekly = this.$("#seed").value === CM.weeklySeed();
    if (weekly) this.slots = CM.weeklyParty(this.$("#seed").value);        // (the week's party, the same for everyone)
    this.weekly = weekly;
    if (!this.slots.length) this.fillSlots(CM.CLASSIC);
    this.$("#create-seed").value = this.$("#seed").value;
    this.renderCreateNote();
    this.refreshTitle();                                                 // (the kits on offer)
    this.show("create");
    this.renderCreate();
  },

  renderCreate() {
    const cards = this.$("#slots").children;
    this.slots.forEach((s, i) => {
      const div = cards[i], c = CM.CLASSES[s.cls];
      const slot = div.querySelector(".portrait-slot");
      slot.innerHTML = "";
      slot.appendChild(this.portrait(s.cls, 56));
      if (div.querySelector(".name").value !== s.name) div.querySelector(".name").value = s.name;
      div.querySelector(".cls").value = s.cls;
      div.querySelector(".role").textContent = `${c.role}${c.cast ? `, casts ${CM.CASTS[c.cast]}` : ""}. ${c.blurb}`;
      div.querySelector(".stats").innerHTML = CM.STATS.map((st) => {
        const v = s.stats[st], key = st === c.key;
        return `<tr class="${key ? "key" : ""}"><td>${CM.STAT_NAMES[st]}</td><td class="v">${v}</td><td class="hint">${key ? "their calling's stat" : CM.STAT_HINTS[st]}</td></tr>`;
      }).join("");
      const h = CM.makeHero(s.cls, s.name, s.stats, s.row);
      div.querySelector(".derived").textContent = `${h.max} health${h.maxmp ? `, ${h.maxmp} magic` : ""}, attack ${h.atk}, defence ${h.df} - ${h.weapon.name} and ${h.armor.name}`;
      for (const b of div.querySelectorAll("button[data-row]")) b.classList.toggle("on", b.dataset.row === s.row);
      for (const el of div.querySelectorAll(".cls, .reroll, .dice")) el.disabled = Boolean(this.weekly);   // (the week's party is the week's)
    });
    this.$("#btn-reroll-all").disabled = Boolean(this.weekly); this.$("#btn-suggest").disabled = Boolean(this.weekly);
    this.renderAdvice();
  },

  renderAdvice() {
    const advice = CM.partyAdvice(this.slots), ul = this.$("#advice ul");
    ul.innerHTML = advice.notes.map((n) => `<li class="${advice.sound && advice.notes.length === 1 ? "good" : ""}">${this.esc(n)}</li>`).join("");
    this.$("#advice").classList.toggle("sound", advice.sound);
  },

  setOut() {
    const g = this.game, seed = this.$("#create-seed").value;
    this.$("#seed").value = seed;
    this.chosenKit = this.$("#kit").value || "pauper";
    this.lastAscension = Number(this.$("#ascension").value) || 0;
    g.newGame(seed, this.slots.map((s) => ({ cls: s.cls, name: s.name, stats: s.stats, row: s.row })), this.chosenKit, this.$("#difficulty").value, undefined, this.$("#mode").value, { ascension: this.lastAscension, iron: this.$("#iron").checked });
  },

  startNew() { this.openCreate(); },

  renderCreateNote() {
    const seed = this.$("#create-seed").value, muts = CM.mutatorsFor(seed), d = CM.DIFFICULTIES[this.$("#difficulty").value] || CM.DIFFICULTIES.fair;
    this.$("#create-note").textContent = `${d.name}: ${d.what}.` + (muts.length ? ` ${seed.startsWith("weekly-") ? "This week's challenge" : "Today's dungeon"} comes with ${muts.map((m) => `${CM.MUTATORS[m].name} (${CM.MUTATORS[m].what})`).join(" and ")}.` : "") + (seed.startsWith("weekly-") ? " The party is the week's: everyone sets out with these four." : "")
      + (this.$("#mode").value === "endless" ? " Endless: the fifty floors and the Lich King as ever, and then no bottom - the bands come round again, the guardians return as echoes every ten floors, and the dark deepens. The run goes on the Endless board, by depth." : "")
      + (this.$("#mode").value === "awakened" ? ` Awakened: ${CM.AWAKENED.what} - the Root remembers you. The run goes on the dungeon's board, marked.` : "")
      + (Number(this.$("#ascension").value) ? ` Ascension ${this.$("#ascension").value}: ${CM.ASCENSION.slice(0, Number(this.$("#ascension").value)).map((r) => `${r.name} (${r.what})`).join("; ")}.` : "")
      + (this.$("#iron").checked ? " Iron: the run is saved only at the camps - a closed window between them loses the floors since." : "");
  },
});
