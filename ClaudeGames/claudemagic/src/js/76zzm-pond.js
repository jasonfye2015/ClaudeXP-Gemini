"use strict";
// The Fishing Pond, the window's side: the mill pond behind the Joker, under the real sky - blue by day with
// dragonflies over the reeds, gold at dusk, and at night a moon on the water and fireflies. From the jetty: hold to
// swing the rod back (the power meter), let go to cast; the float lands with a ring of ripples and bobs; nibbles dip
// it, and when it goes right under (the "!") strike - too soon and the fish is spooked, too late and it's gone. Then
// play it: hold to reel (the rod bends, the tension climbs), ease off when it runs, or the line snaps; let it run too
// long and it throws the hook. Landed, the fish is shown with its weight and price, and goes in the creel book - every
// kind with its best weight. The rules are 64zzj-draws.js.
CM.CG_TABLES.push(["pond", "The Fishing Pond"]);
CM.FISH_ART = (p, id, x, y, len, a = 0) => { const L = len, Hh = { eel: 0.12, pike: 0.2, catfish: 0.3, bream: 0.42, golden: 0.36 }[id] || 0.3, C = { roach: ["#B8C8D0", "#C04030"], perch: ["#7A9A40", "#E05030"], bream: ["#B0A070", "#8A7040"], trout: ["#9A8A60", "#3A2A1A"], pike: ["#5A7A3A", "#C0C870"], eel: ["#3A3A28", "#6A6A40"], catfish: ["#4A4A50", "#2A2A30"], golden: ["#F0C040", "#FFF0A0"] }[id];
  p.save(); p.translate(x, y); p.rotate(a);
  if (id === "boot") { p.fillStyle = "#5A3A1E"; p.beginPath(); p.moveTo(-L * 0.2, -L * 0.45); p.lineTo(L * 0.1, -L * 0.45); p.lineTo(L * 0.12, 0); p.lineTo(L * 0.45, L * 0.05); p.quadraticCurveTo(L * 0.5, L * 0.22, L * 0.4, L * 0.22); p.lineTo(-L * 0.2, L * 0.22); p.fill(); p.fillStyle = "#3A2410"; p.fillRect(-L * 0.22, L * 0.18, L * 0.66, L * 0.06); p.restore(); return; }
  if (id === "weed") { p.strokeStyle = "#3A7A30"; p.lineWidth = 3; for (let k = 0; k < 5; k++) { p.beginPath(); p.moveTo(-L * 0.3 + k * L * 0.12, L * 0.2); p.bezierCurveTo(-L * 0.4 + k * L * 0.15, -L * 0.1, -L * 0.1 + k * L * 0.1, -L * 0.2, -L * 0.2 + k * L * 0.14, -L * 0.4); p.stroke(); } p.restore(); return; }
  const h = L * Hh, gr = p.createLinearGradient(0, -h, 0, h); gr.addColorStop(0, C[1] && id === "golden" ? "#FFF0A0" : C[0]); gr.addColorStop(0.5, C[0]); gr.addColorStop(1, id === "catfish" || id === "eel" ? C[1] : "#F0F0E0");
  p.fillStyle = C[0]; p.beginPath(); p.moveTo(-L * 0.42, 0); p.lineTo(-L * 0.58, -h * 0.9); p.lineTo(-L * 0.52, 0); p.lineTo(-L * 0.58, h * 0.9); p.fill();
  if (id !== "eel") { p.fillStyle = id === "perch" || id === "roach" ? C[1] : C[0]; p.beginPath(); p.moveTo(-L * 0.1, -h * 0.85); p.quadraticCurveTo(L * 0.02, -h * 1.5, L * 0.12, -h * 0.85); p.fill(); p.beginPath(); p.moveTo(L * 0.05, h * 0.8); p.lineTo(-L * 0.02, h * 1.25); p.lineTo(-L * 0.12, h * 0.8); p.fill(); }
  p.fillStyle = gr; p.beginPath(); p.ellipse(0, 0, L * 0.46, h, 0, 0, Math.PI * 2); p.fill();
  if (id === "perch") { p.fillStyle = "rgba(30,40,10,0.5)"; for (let k = 0; k < 5; k++) p.fillRect(-L * 0.25 + k * L * 0.1, -h * 0.9, L * 0.04, h * 1.3); }
  if (id === "trout") { p.fillStyle = "#3A2010"; for (let k = 0; k < 14; k++) { p.beginPath(); p.arc(-L * 0.3 + ((k * 37) % 60) / 100 * L, -h * 0.6 + ((k * 23) % 10) / 10 * h, L * 0.015 + 0.5, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#C03030"; for (let k = 0; k < 4; k++) { p.beginPath(); p.arc(-L * 0.2 + k * L * 0.12, h * 0.1, L * 0.012 + 0.4, 0, Math.PI * 2); p.fill(); } }
  if (id === "pike") { p.fillStyle = "rgba(220,230,150,0.55)"; for (let k = 0; k < 12; k++) { p.beginPath(); p.ellipse(-L * 0.35 + k * L * 0.06, (k % 2 ? -1 : 1) * h * 0.3, L * 0.02, h * 0.15, 0, 0, Math.PI * 2); p.fill(); } }
  if (id === "golden") { const s = p.createLinearGradient(-L * 0.4, 0, L * 0.4, 0); s.addColorStop(0, "rgba(255,255,255,0)"); s.addColorStop(0.5, `rgba(255,255,255,${0.35 + 0.25 * Math.sin(performance.now() / 300)})`); s.addColorStop(1, "rgba(255,255,255,0)"); p.fillStyle = s; p.beginPath(); p.ellipse(0, 0, L * 0.46, h, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(160,100,10,0.4)"; for (let k = 0; k < 6; k++) { p.beginPath(); p.arc(-L * 0.25 + k * L * 0.1, 0, h * 0.5, -1, 1); p.stroke(); } }
  if (id === "catfish") { p.strokeStyle = "#2A2A30"; p.lineWidth = 1.5; for (const s of [-1, 1]) { p.beginPath(); p.moveTo(L * 0.42, s * h * 0.2); p.quadraticCurveTo(L * 0.6, s * h * 0.6, L * 0.55, s * h * 1.2); p.stroke(); } }
  p.fillStyle = "#FFFFFF"; p.beginPath(); p.arc(L * 0.3, -h * 0.25, Math.max(1.5, L * 0.04), 0, Math.PI * 2); p.fill(); p.fillStyle = "#101010"; p.beginPath(); p.arc(L * 0.31, -h * 0.25, Math.max(0.8, L * 0.022), 0, Math.PI * 2); p.fill();
  p.strokeStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.arc(L * 0.2, 0, h * 0.7, -1.2, 1.2); p.stroke(); p.restore(); };
{ const floor0 = CM.UI.prototype.renderFloor, POND = CM.POND, W = 520, H = 400, HZ = 128, TIP = [176, 214], HAND = [96, 372];
  const sky = (hr) => (hr >= 20 || hr < 6 ? "night" : hr >= 18 ? "dusk" : hr < 7 ? "dawn" : "day");
  const at = (d) => [300 + (d - 0.5) * 60, 330 - d * 180];
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "pond") return this.cgPond(box); return floor0.call(this, box); },
    cgPond(box) {
      const g = this.game, S = g.pdStore(), last = this.pdLast, kinds = POND.FISH.filter((f) => f[2] > 0), hr = new Date().getHours(), night = sky(hr) === "night";
      if (S.cur && !this.pd) g.pdLand(false);   // (a line left out when the window closed: that fish is gone)
      const busy = this.pd && this.pd.st !== "idle";
      box.innerHTML = `<div class="cgtable pond runestack dash"><h3>The Fishing Pond</h3><div class="rswrap"><div class="pdwrap"><canvas class="pdcanvas" width="${W}" height="${H}"></canvas><div class="pdhint">${this.pdHint || "Hold on the water to swing back; let go to cast."}</div></div>
        <div class="dashside"><p class="lore">Behind the Joker the old mill pond lies still under the willows, with a jetty and a bait shed. "Worms for the shallows, spinners if you want the big ones out deep," says the old woman at the shed. "And the eels and the catfish only come up after dark."</p>
        <div class="row">${Object.entries(POND.BAIT).map(([k, B]) => `<button data-pdbait="${k}" ${busy ? "disabled" : ""}>${B.name} (${B.price} gold, ${B.casts} casts)</button>`).join("")}</div>
        <div class="pdbait">${S.left ? `<b>${S.left}</b> cast${S.left > 1 ? "s" : ""} of ${S.bait === "worms" ? "worms" : "spinners"} left` : "No bait - buy some at the shed."} · ${night ? "Night: the eels and catfish are about." : `By day. ${sky(hr) === "dusk" ? "Dusk is falling." : ""}`}</div>
        <div class="cgnote">${this.cgNote || ""}</div>${last && !last.lost ? `<div class="pdcatch"><canvas width="150" height="70" data-pdlast></canvas><div><b>${last.name}</b>${last.tier ? `<span>${last.kg} kg</span>` : ""}<span>${last.gold ? `${last.gold} gold` : "worth nothing"}${last.tickets ? `, ${last.tickets} tickets` : ""}</span>${last.first ? `<i class="pdnew">First in the book!</i>` : last.best ? `<i class="pdnew">Your heaviest!</i>` : ""}</div></div>${last.cards.map((c) => this.cgCardWon(c)).join("")}` : ""}
        <h4>The creel book <span class="small">(${kinds.filter((f) => S.book[f[0]]).length} of ${kinds.length})</span></h4><div class="pdbook">${kinds.map((f) => `<div class="${S.book[f[0]] ? "got" : ""}"><canvas width="64" height="30" data-pdfish="${f[0]}"></canvas><b>${S.book[f[0]] ? f[1] : "?"}</b><span>${S.book[f[0]] ? `${S.best[f[0]]} kg · ${S.book[f[0]]} caught` : f[8] ? "bites at night" : ""}</span></div>`).join("")}</div>
        <div class="small">The fishmonger pays by the kilo and every fish brings tickets; the first of each kind 10 more, and the whole book a rare card${S.all ? " ✓" : ""}. The golden carp is rare - and worth a card. Landed ${S.landed}, lost ${S.lost}.</div><div class="row"><button data-leave ${busy ? "disabled" : ""}>Leave</button></div>${this.cgStats("pond")}</div></div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-pdbait]").forEach((b) => b.addEventListener("click", () => { const r = g.pdBuy(b.dataset.pdbait); this.cgNote = r.error || "A fresh pot from the bait shed."; this.cgSfx(r.error ? "miss" : "coin", 0.35); this.renderCasino(); }));
      box.querySelectorAll("[data-pdfish]").forEach((c) => { const p = c.getContext("2d"), id = c.dataset.pdfish; if (!S.book[id]) { p.globalAlpha = 0.25; p.filter = "brightness(0)"; } CM.FISH_ART(p, id, 32, 15, 48); });
      if (q("[data-pdlast]")) CM.FISH_ART(q("[data-pdlast]").getContext("2d"), last.id, 75, 36, last.tier ? Math.min(130, 60 + last.tier * 16) : 60);
      const cv = this.pdCanvas = q(".pdcanvas"), down = () => this.pdDown(), up = () => this.pdUp(); cv.addEventListener("mousedown", down); cv.addEventListener("mouseup", up); cv.addEventListener("mouseleave", () => { if (this.pd && (this.pd.st === "charge" || this.pd.reel)) up(); });
      cv.addEventListener("touchstart", (e) => { e.preventDefault(); down(); }); cv.addEventListener("touchend", (e) => { e.preventDefault(); up(); });
      this.pd = this.pd || { st: "idle" }; if (!this.pdFx) this.pdFx = { rip: [], flies: Array.from({ length: 14 }, (_, k) => ({ x: Math.random() * W, y: HZ + 20 + Math.random() * 200, p: k })) };
      if (!this.pdLoop) { let prev = performance.now(); const loop = (now) => { if (!this.pdCanvas || !this.pdCanvas.isConnected || this.cgView !== "pond") { this.pdLoop = null; if (this.pd && this.pd.st !== "idle") { this.game.pdLand(false); this.pd = { st: "idle" }; this.cgBusy = false; } return; }
          const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.pdStep(dt, now); this.pdDraw(now); this.pdLoop = requestAnimationFrame(loop); }; this.pdLoop = requestAnimationFrame(loop); }
    },
    pdSay(t) { this.pdHint = t; const el = this.$("#casino-body .pdhint"); if (el) el.textContent = t; },
    pdDown() { const D = this.pd, g = this.game; if (!D) return;
      if (D.st === "idle") { if (g.pdStore().left < 1) { this.pdSay("Buy some bait at the shed first."); this.cgSfx("miss", 0.3); return; } D.st = "charge"; D.t = 0; this.pdSay("Let go to cast..."); return; }
      if (D.st === "wait") { this.pdSay("Too soon - the fish is spooked."); this.cgSfx("splash", 0.3, 1.4); g.pdLand(false); this.pdEnd("Too soon - you pulled it out of its mouth."); return; }
      if (D.st === "bite") { D.st = "fight"; D.reel = true; D.ten = 0.25; D.slack = 0; D.run = 0; D.rest = 1 + Math.random(); this.cgSfx("splash", 0.45, 0.9); this.pdSay("Hooked! Hold to reel; ease off when it runs."); this.cgBusy = true; return; }
      if (D.st === "fight") D.reel = true; },
    pdUp() { const D = this.pd, g = this.game; if (!D) return;
      if (D.st === "charge") { const pow = Math.max(0.08, D.pow || 0), c = g.pdCast(pow); if (c.error) { D.st = "idle"; this.pdSay(c.error); return; } this.cgBusy = true; Object.assign(D, { st: "fly", t: 0, c, d: c.dist, wait: 0, nib: [] }); for (let k = 0; k < 1 + Math.floor(Math.random() * 3); k++) D.nib.push(Math.random() * Math.max(0.5, c.bite - 0.6)); this.cgSfx("zap", 0.2, 0.6); this.pdSay("..."); const b = this.$("#casino-body .pdbait"); if (b) b.innerHTML = `<b>${g.pdStore().left}</b> casts left`; return; }
      if (D.st === "fight") D.reel = false; },
    pdEnd(note, r) { this.pd = { st: "idle" }; this.cgBusy = false; this.pdLast = r || null; this.cgNote = note; this.pdHint = "Hold on the water to swing back; let go to cast."; this.renderCasino(); },
    pdStep(dt, now) {
      const D = this.pd, g = this.game, fx = this.pdFx; fx.rip = fx.rip.filter((r) => (r.t += dt) < 2.2);
      if (D.st === "charge") { D.t += dt; const k = (D.t / 1.1) % 2; D.pow = k < 1 ? k : 2 - k; }
      else if (D.st === "fly") { D.t += dt; if (D.t >= 0.8) { D.st = "wait"; D.t = 0; const [x, y] = at(D.d); fx.rip.push({ x, y, t: 0, big: true }); this.cgSfx("splash", 0.35, 1.3); } }
      else if (D.st === "wait") { D.t += dt; for (const n of D.nib) if (D.t >= n && D.t - dt < n) { const [x, y] = at(D.d); fx.rip.push({ x, y, t: 0 }); this.cgSfx("step_water", 0.2, 1.6); } if (D.t >= D.c.bite) { D.st = "bite"; D.t = 0; const [x, y] = at(D.d); fx.rip.push({ x, y, t: 0, big: true }); this.cgSfx("splash", 0.4, 1.1); this.pdSay("Strike - click now!"); } }
      else if (D.st === "bite") { D.t += dt; if (D.t > D.c.window) { g.pdLand(false); this.pdEnd(`It took the bait and was gone.`); } }
      else if (D.st === "fight") { const f = D.c.fight; D.rest -= dt;
        if (D.run > 0) { D.run -= dt; if (D.run <= 0) D.rest = 0.8 + Math.random() * (2 - f); } else if (D.rest <= 0 && f > 0) { D.run = 0.6 + f * 1.8 * Math.random() + 0.3; this.cgSfx("splash", 0.25, 1.5); const [x, y] = at(D.d); fx.rip.push({ x, y, t: 0 }); }
        const running = D.run > 0;
        if (D.reel) { D.d -= (running ? 0.03 : 0.17 - f * 0.05) * dt; D.ten += (running ? 0.5 + f * 0.6 : 0.12 + f * 0.1) * dt; D.slack = 0; } else { D.ten -= 0.55 * dt; if (running) { D.d += (0.08 + f * 0.14) * dt; D.slack += dt; } }
        D.ten = Math.max(0, D.ten); if (D.reel && Math.random() < dt * 6) this.cgSfx("card", 0.05, 2.4);
        if (D.ten >= 1) { g.pdLand(false); this.cgSfx("miss", 0.5); this.pdEnd("Snap! The line parts and the fish is away."); return; }
        if (D.slack > 2.6 || D.d > 1.15) { g.pdLand(false); this.cgSfx("splash", 0.3); this.pdEnd("It threw the hook - too much slack."); return; }
        if (D.d <= 0.02) { const r = g.pdLand(true); this.cgSfx(r.tier >= 3 ? "victory" : r.tier ? "cardwin" : "cardlose", 0.45); if (r.gold) this.cgCoins(this.$("#casino-body"), Math.min(24, 3 + r.gold)); this.pdEnd(r.tier ? `${r.name}, ${r.kg} kg!` : `${r.name}. Well... it's something.`, r); } }
    },
    pdDraw(now) {
      const p = this.pdCanvas.getContext("2d"), D = this.pd, fx = this.pdFx, hr = new Date().getHours(), sk = sky(hr), t = now / 1000;
      // the sky, the far bank, the water
      const SK = { day: ["#5A9AD8", "#B8DCF0"], dusk: ["#3A2A5A", "#F0A060"], dawn: ["#5A6AA0", "#F0C8A0"], night: ["#060A1A", "#1A2448"] }[sk], s = p.createLinearGradient(0, 0, 0, HZ); s.addColorStop(0, SK[0]); s.addColorStop(1, SK[1]); p.fillStyle = s; p.fillRect(0, 0, W, HZ);
      if (sk === "night") { for (let k = 0; k < 50; k++) { p.fillStyle = `rgba(255,255,255,${0.3 + 0.5 * Math.abs(Math.sin(t * 0.7 + k))})`; p.fillRect((k * 97) % W, (k * 31) % (HZ - 30), 1.4, 1.4); } p.fillStyle = "#F8F0D0"; p.beginPath(); p.arc(420, 40, 16, 0, Math.PI * 2); p.fill(); }
      else { p.fillStyle = sk === "day" ? "#FFF6C0" : "#FFB060"; p.beginPath(); p.arc(sk === "day" ? 90 : 440, sk === "day" ? 34 : 96, 18, 0, Math.PI * 2); p.fill(); }
      p.fillStyle = sk === "night" ? "#0A140E" : "#2A4A2A"; p.beginPath(); p.moveTo(0, HZ); for (let x = 0; x <= W; x += 20) p.lineTo(x, HZ - 16 - Math.abs(Math.sin(x * 0.05)) * 18 - (x % 60 === 0 ? 10 : 0)); p.lineTo(W, HZ); p.fill();
      p.fillStyle = sk === "night" ? "#141A10" : "#4A3A28"; p.fillRect(380, HZ - 46, 50, 34); p.fillStyle = sk === "night" ? "#F0C060" : "#2A2014"; p.fillRect(392, HZ - 34, 10, 10); p.fillStyle = sk === "night" ? "#100A08" : "#6A2A20"; p.beginPath(); p.moveTo(374, HZ - 46); p.lineTo(405, HZ - 64); p.lineTo(436, HZ - 46); p.fill();
      const w = p.createLinearGradient(0, HZ, 0, H), WC = sk === "night" ? ["#0E1830", "#04080E"] : sk === "day" ? ["#4A8AA8", "#1A4A5A"] : ["#6A5A70", "#1A2A3A"]; w.addColorStop(0, WC[0]); w.addColorStop(1, WC[1]); p.fillStyle = w; p.fillRect(0, HZ, W, H - HZ);
      if (sk === "night") { p.fillStyle = "rgba(248,240,208,0.18)"; for (let k = 0; k < 8; k++) p.fillRect(420 - 20 + Math.sin(t * 2 + k) * 6, HZ + 8 + k * 9, 40 - k * 3, 2); }
      p.strokeStyle = sk === "night" ? "rgba(140,170,220,0.12)" : "rgba(255,255,255,0.18)"; for (let k = 0; k < 14; k++) { const y = HZ + 12 + k * 18, x = (k * 83 + t * 12 * (k % 2 ? 1 : -1)) % (W + 80) - 40; p.beginPath(); p.moveTo(x, y); p.quadraticCurveTo(x + 20, y - 2, x + 40, y); p.stroke(); }
      // lily pads and reeds
      for (const [x, y, r] of [[60, 200, 14], [86, 214, 10], [470, 240, 16], [440, 226, 9]]) { p.fillStyle = sk === "night" ? "#1A3A1A" : "#3A7A30"; p.beginPath(); p.arc(x, y, r, 0.3, Math.PI * 2); p.lineTo(x, y); p.fill(); } p.fillStyle = "#F0B0D0"; p.beginPath(); p.arc(470, 236, 4, 0, Math.PI * 2); p.fill();
      p.strokeStyle = sk === "night" ? "#1A2A10" : "#5A7A2A"; p.lineWidth = 2; for (let k = 0; k < 12; k++) { const x = 470 + k * 5, sw = Math.sin(t + k) * 3; p.beginPath(); p.moveTo(x, H - 40); p.quadraticCurveTo(x + sw, H - 80, x + sw * 2, H - 110 - (k % 3) * 12); p.stroke(); } p.lineWidth = 1;
      // dragonflies by day, fireflies by night
      for (const f of fx.flies) { if (sk === "night") { const a = 0.5 + 0.5 * Math.sin(t * 3 + f.p); f.x += Math.sin(t + f.p) * 0.3; f.y += Math.cos(t * 0.7 + f.p) * 0.2; p.fillStyle = `rgba(220,255,120,${a})`; p.beginPath(); p.arc(f.x % W, f.y, 2, 0, Math.PI * 2); p.fill(); }
        else if (f.p < 3) { const x = (f.x + t * 30 * (f.p % 2 ? 1 : -1) + W * 4) % W, y = HZ + 30 + f.p * 20 + Math.sin(t * 4 + f.p) * 8; p.fillStyle = "#3080C0"; p.fillRect(x - 6, y, 12, 1.6); p.fillStyle = "rgba(220,240,255,0.6)"; p.fillRect(x - 3, y - 3 + Math.sin(t * 40) * 1, 6, 2); } }
      // ripples
      for (const r of fx.rip) { const k = r.t / 2.2; p.strokeStyle = `rgba(255,255,255,${0.6 * (1 - k)})`; for (let j = 0; j < (r.big ? 3 : 1); j++) { p.beginPath(); p.ellipse(r.x, r.y, 4 + k * 40 + j * 8, (4 + k * 40 + j * 8) * 0.3, 0, 0, Math.PI * 2); p.stroke(); } }
      // the jetty
      p.fillStyle = "#6A4A28"; p.fillRect(0, H - 42, 220, 42); p.strokeStyle = "#3A2410"; for (let k = 0; k < 11; k++) { p.beginPath(); p.moveTo(k * 20, H - 42); p.lineTo(k * 20, H); p.stroke(); } p.fillStyle = "#4A3018"; p.fillRect(30, H - 46, 8, 46); p.fillRect(190, H - 46, 8, 46);
      // the line, the float, the fish
      let tip = TIP.slice(), bend = 0; if (D.st === "charge") { tip = [TIP[0] - 50 * (D.pow || 0), TIP[1] + 30 * (D.pow || 0)]; } if (D.st === "fight") { bend = Math.min(1, D.ten); tip = [TIP[0] + 10 * bend, TIP[1] + 34 * bend]; }
      p.strokeStyle = "#4A2A10"; p.lineWidth = 3; p.beginPath(); p.moveTo(HAND[0], HAND[1]); p.quadraticCurveTo((HAND[0] + tip[0]) / 2 - bend * 10, (HAND[1] + tip[1]) / 2 - 20 + bend * 10, tip[0], tip[1]); p.stroke(); p.lineWidth = 1;
      p.fillStyle = "#3A3A4A"; p.beginPath(); p.arc(HAND[0] - 12, HAND[1] - 30, 12, 0, Math.PI * 2); p.fill(); p.fillRect(HAND[0] - 22, HAND[1] - 20, 22, 30); p.fillStyle = "#8A6A3A"; p.beginPath(); p.ellipse(HAND[0] - 12, HAND[1] - 40, 16, 5, 0, 0, Math.PI * 2); p.fill(); p.fillRect(HAND[0] - 20, HAND[1] - 50, 16, 10);
      if (D.st === "charge") { p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(20, 20, 16, 100); p.fillStyle = `hsl(${120 - D.pow * 120},80%,55%)`; p.fillRect(22, 118 - 96 * D.pow, 12, 96 * D.pow); p.fillStyle = "#FFF"; p.font = "10px Georgia"; p.fillText("far", 40, 28); p.fillText("near", 40, 118); }
      if (D.st === "fly" || D.st === "wait" || D.st === "bite" || D.st === "fight") {
        let [x, y] = at(D.d); if (D.st === "fly") { const k = D.t / 0.8; x = tip[0] + (x - tip[0]) * k; y = tip[1] + (y - tip[1]) * k - Math.sin(k * Math.PI) * 90; }
        const dip = D.st === "bite" ? 8 : D.st === "wait" && D.nib.some((n) => D.t >= n && D.t < n + 0.35) ? 4 : Math.sin(t * 2.5) * 1.2;
        p.strokeStyle = D.st === "fight" ? `rgba(255,${Math.round(255 - 200 * Math.min(1, D.ten))},${Math.round(255 - 200 * Math.min(1, D.ten))},0.9)` : "rgba(255,255,255,0.7)"; p.beginPath(); p.moveTo(tip[0], tip[1]); p.quadraticCurveTo((tip[0] + x) / 2, Math.max(tip[1], y) + (D.st === "fight" ? 4 - bend * 20 : 20), x, y); p.stroke();
        if (D.st === "fight") { const f = D.c, run = D.run > 0, sx = x + Math.sin(t * (run ? 9 : 3)) * (run ? 10 : 4); p.globalAlpha = 0.35; CM.FISH_ART(p, f.id, sx, y + 10, 30 + f.tier * 8, Math.sin(t * 5) * 0.3); p.globalAlpha = 1; if (run && Math.random() < 0.3) fx.rip.push({ x: sx, y, t: 1.2 }); }
        else { p.fillStyle = "#F0F0F0"; p.fillRect(x - 2, y - 9 + dip, 4, 5); p.fillStyle = "#E02020"; p.fillRect(x - 2, y - 4 + dip, 4, 5); if (D.st === "bite") { p.fillStyle = "#FFE040"; p.font = "bold 30px Georgia"; p.textAlign = "center"; p.fillText("!", x, y - 22 + Math.sin(t * 20) * 2); p.textAlign = "left"; } }
      }
      // the fight's gauges: the tension, and how far out it is
      if (D.st === "fight") { p.fillStyle = "rgba(0,0,0,0.55)"; p.fillRect(W - 46, 20, 26, 150); const k = Math.min(1, D.ten), gr = p.createLinearGradient(0, 170, 0, 20); gr.addColorStop(0, "#40C060"); gr.addColorStop(0.6, "#F0C040"); gr.addColorStop(1, "#F03030"); p.fillStyle = gr; p.fillRect(W - 42, 166 - 142 * k, 18, 142 * k);
        p.fillStyle = "#FFF"; p.font = "10px Georgia"; p.textAlign = "center"; p.fillText("line", W - 33, 182); p.fillText(D.run > 0 ? "RUN!" : "", W - 33, 14); p.textAlign = "left"; p.fillStyle = "rgba(0,0,0,0.55)"; p.fillRect(250, 14, 200, 10); p.fillStyle = "#80C0F0"; p.fillRect(250, 14, 200 * Math.max(0, Math.min(1, D.d)), 10); p.fillStyle = "#FFF"; p.fillText("how far out", 220, 34); }
    },
  });
}
