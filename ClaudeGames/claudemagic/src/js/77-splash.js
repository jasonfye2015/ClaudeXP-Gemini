"use strict";
// The title card: what the game opens on, before the first screen of choices. A dark, warm hall: the game's emblem
// strikes the stone in a shower of sparks, the name is forged letter by letter, the sky outside keeps the real hour and
// season (the sun or the moon in its phase; leaves, snow, petals or fireflies), the eleven callings stand in a row,
// three lines of what the game holds drift past, and the version stamp sits in the corner. A click, any key or a pad
// button goes on to the title.
CM.SPLASH_LINES = [
  ["Fifty floors in ten bands", "The Lich King on floor 20", "The Root of the World on floor 50", "Endless: no bottom at all", "A guardian and its relic over every fifth shaft", "Camps, a merchant and a temple between",
    "Branching wings, riddle doors, pits and plates", "The Deep: six bands below the king"],
  ["Eleven callings, two paths each", "A party of four, turn by turn", "Gear with affixes, sets and curses", "A belt of potions and things to throw", "Cooking, mining, forging and farming",
    "Automatic: the party plays by itself", "Films of every run", "Daily and weekly dungeons", "The Hall of Fame"],
  ["Caer Duin on its hill", "Lantern Street and the Square", "The Deep Wood beyond the gate", "The river, the ford and the bridge", "A sky that keeps the hour and the moon",
    "Seasons, festivals and the weather", "The story told by the carvings", "Three endings", "Pixel tiles or photographed stone"],
];
Object.assign(CM.UI.prototype, {
  splashSky() {
    const now = new Date(), h = now.getHours() + now.getMinutes() / 60, night = h >= 20 || h < 6, m = now.getMonth();
    const season = m <= 1 || m === 11 ? "winter" : m <= 4 ? "spring" : m <= 7 ? "summer" : "autumn";
    const phase = Math.round((((now - new Date(2000, 0, 6, 18, 14)) / 864e5) % 29.53) / 29.53 * 8) % 8;   // (the moon's age from a new moon in January 2000)
    const orb = night ? `<div class="sp-moon" data-phase="${phase}"><div class="disc"></div><div class="shade" style="--k:${(phase - 4) / 4}"></div></div>` : `<div class="sp-sun"><div class="rays"></div><div class="disc"></div></div>`;
    const falls = { autumn: ["#C86A28", "#D8A040", "#A8442C"], winter: ["#F4F6FA", "#E8ECF4", "#FFFFFF"], spring: ["#F4B8C8", "#F8D8E0", "#F0A0B8"] }[season];
    let parts = "";
    for (let i = 0; i < 28; i++) {
      const l = (Math.random() * 100).toFixed(1), d = (8 + Math.random() * 9).toFixed(1), dl = (-Math.random() * 16).toFixed(1);
      if (falls && !(season === "summer")) parts += `<span class="sp-fall ${season}" style="left:${l}%;background:${falls[i % 3]};width:${season === "winter" ? 5 : 9}px;height:${season === "winter" ? 5 : 6}px;animation-duration:${d}s,${(2 + Math.random() * 2).toFixed(1)}s;animation-delay:${dl}s,${dl}s"></span>`;
      else parts += `<span class="sp-fly" style="left:${l}%;top:${(30 + Math.random() * 60).toFixed(0)}%;animation-duration:${(3 + Math.random() * 4).toFixed(1)}s;animation-delay:${(-Math.random() * 6).toFixed(1)}s"></span>`;
    }
    return `<div class="sp-sky${night ? " night" : ""}">${orb}${parts}</div>`;
  },
  showSplash() {
    if (document.getElementById("splash")) return;
    const forged = (text, start) => [...text].map((c, i) => (c === " " ? " " : `<i class="fl" style="--d:${(start + i * 0.07).toFixed(2)}s">${this.esc(c)}</i>`)).join("");
    const lines = CM.SPLASH_LINES.map((L, i) => { const t = L.join("&nbsp;&nbsp;&middot;&nbsp;&nbsp;") + "&nbsp;&nbsp;&middot;&nbsp;&nbsp;"; return `<div class="marq m${i + 1}${i === 1 ? "" : " toright"}"><div style="animation-duration:${Math.round(L.join(" ").length * 0.22)}s"><span>${t}</span><span>${t}</span></div></div>`; }).join("");
    const el = document.createElement("div");
    el.id = "splash";
    el.innerHTML = `${this.splashSky()}<div class="splashcard"><div class="shk">
      <div class="forge"><div class="emblem"></div><div class="stone"></div></div>
      <h1>${forged("Claude", 1.15)}<span> ${forged("and Magic", 1.6)}</span></h1>
      <p class="tag">Fifty floors down, the Lich King waits - and below him, the Deep</p>
      <p class="credit">Created by <b>Claude</b>, an AI by Anthropic<br>Designed together with its very first player</p>
      <div class="lineup"></div>
      <p class="press">Click or press any key</p>
      <div class="marqs">${lines}</div></div></div>
      <div class="vstamp">Claude and Magic <b>v${this.esc(CM.version)}</b>${CM.built && !String(CM.built).startsWith("__") ? ` - built ${this.esc(CM.built)}` : ""}</div>`;
    el.querySelector(".emblem").appendChild(CM.art.emblem(96));
    const row = el.querySelector(".lineup");
    Object.keys(CM.CLASSES).forEach((cls, i) => {
      const fig = document.createElement("div"); fig.className = "hero"; fig.style.setProperty("--i", i); fig.title = cls;
      fig.appendChild(this.portrait(cls, 52)); const name = document.createElement("small"); name.textContent = cls; fig.appendChild(name);
      row.appendChild(fig);
    });
    document.body.appendChild(el);
    el.addEventListener("click", () => this.leaveSplash());
    this.splashOn = true;
    this.splashTimer = setTimeout(() => this.splashStrike(), 1050);
  },
  // the emblem strikes the stone: sparks, and a little shake
  splashStrike() {
    const f = document.querySelector("#splash .forge"), w = document.querySelector("#splash .shk");
    if (!f || CM.reducedMotion) return;
    for (let i = 0; i < 28; i++) {
      const sp = document.createElement("span"), a = -Math.PI * (0.08 + Math.random() * 0.84), v = 40 + Math.random() * 120;
      sp.className = "spk"; sp.style.setProperty("--dx", `${(Math.cos(a) * v).toFixed(0)}px`); sp.style.setProperty("--dy", `${(Math.sin(a) * v).toFixed(0)}px`); sp.style.animationDuration = `${(0.5 + Math.random() * 0.6).toFixed(2)}s`;
      f.appendChild(sp); setTimeout(() => sp.remove(), 1300);
    }
    if (w) { w.classList.remove("cshake"); void w.offsetWidth; w.classList.add("cshake"); }
    try { CM.audio.play("slam"); } catch (e) { /* (no sound before a gesture: the card is quiet) */ }
  },
  leaveSplash() {
    const el = document.getElementById("splash");
    if (!el || !this.splashOn) return;
    this.splashOn = false; clearTimeout(this.splashTimer);
    CM.audio.unlock();
    try { CM.audio.play("level"); } catch (e) { /* quiet */ }
    el.classList.add("leaving");
    setTimeout(() => el.remove(), 600);
  },
});
