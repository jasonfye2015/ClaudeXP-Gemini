"use strict";
// The Bard's Stage, the window's side: the tavern stage under footlights - curtains at the sides, a crowd of heads
// bobbing to the beat at the bottom, four lanes of light ending in four rune-stones on the strike line (they glow and
// press down when struck); notes falling as glowing gems in each lane's colour, chords side by side; Perfect, Good and
// Miss flashing over the line, the combo counting up, the cheer bar at the side going from red to gold. The music:
// a kick and a hat on the beat, and each struck note sung by a little plucked voice, all made here with the Web Audio
// clock. D F J K (or the arrows) to strike. The rules are 64zza-bard.js.
CM.CG_TABLES.push(["bard", "The Bard's Stage"]);
{ const BD = CM.BD, W = 380, H = 500, LINE = 430, LW = 62, LX = W / 2 - LW * 2, PX = 150, COL = ["#E05050", "#50B0F0", "#60D070", "#F0C040"], KEYS = { KeyD: 0, KeyF: 1, KeyJ: 2, KeyK: 3, ArrowLeft: 0, ArrowDown: 1, ArrowUp: 2, ArrowRight: 3 };
  const scale = [0, 2, 4, 5, 7, 9, 11];
  Object.assign(CM.ARC.reg.bard, {
    ui: { W, H, scale: 1.05, frame: "#5A1A28", start: "Take the stage", go: "Level 1. Play!", over: "The bard is booed off",
      lore: "The tavern stage at the back of the Joker has a lute on a stand and a crowd that knows what it likes. \"Strike each note as it reaches the line,\" says the landlady. \"Keep them cheering and the house pays by the tune.\"",
      help: "D F J K (or ← ↓ ↑ →) to strike the four lanes as the notes cross the line: Perfect 300, Good 100, a combo of ten or more multiplies. Misses drain the crowd's cheer; empty it and you are booed off (a life). Finish the tune for a bonus by accuracy.",
      keys: Object.keys(KEYS) },
    press(L, code, ui) { const lane = KEYS[code]; if (lane === undefined) return; L.strike(lane); (ui.bdPress = ui.bdPress || [0, 0, 0, 0])[lane] = performance.now(); },
    click(L, x, y, ui) { const lane = Math.floor((x - LX) / LW); if (lane >= 0 && lane < 4) { L.strike(lane); (ui.bdPress = ui.bdPress || [0, 0, 0, 0])[lane] = performance.now(); } },
    lifeIcon(p, x, y) { p.fillStyle = "#C08040"; p.beginPath(); p.ellipse(x, y + 1, 4, 5, 0, 0, Math.PI * 2); p.fill(); p.fillRect(x - 1, y - 8, 2, 6); },
    // a little synth on the page's audio clock
    audio() { if (this.ac === undefined) { try { const A = window.AudioContext || window.webkitAudioContext; this.ac = A ? new A() : null; } catch (e) { this.ac = null; } } if (this.ac && this.ac.state === "suspended") this.ac.resume(); return this.ac; },
    tone(freq, dur, type, vol) { const ac = this.audio(); if (!ac) return; const t = ac.currentTime, o = ac.createOscillator(), g = ac.createGain(); o.type = type; o.frequency.value = freq; g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.001, t + dur); o.connect(g).connect(ac.destination); o.start(t); o.stop(t + dur + 0.02); },
    kick() { const ac = this.audio(); if (!ac) return; const t = ac.currentTime, o = ac.createOscillator(), g = ac.createGain(); o.frequency.setValueAtTime(140, t); o.frequency.exponentialRampToValueAtTime(40, t + 0.15); g.gain.setValueAtTime(0.35, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.2); o.connect(g).connect(ac.destination); o.start(t); o.stop(t + 0.22); },
    event(ui, e, now, L, fx) {
      const fl = this.flash = this.flash || [];
      if (e.kind === "beat") { if (e.n % 2 === 0) this.kick(); else this.tone(6000, 0.03, "square", 0.03); }
      else if (e.kind === "hit") { const d = e.deg, semi = scale[((d % 7) + 7) % 7] + 12 * Math.floor(d / 7), f = 261.6 * Math.pow(2, (semi + L.key) / 12); this.tone(f, 0.35, "triangle", 0.18); this.tone(f * 2, 0.12, "sine", 0.05); fl.push({ lane: e.lane, text: e.how === "perfect" ? "PERFECT" : "GOOD", c: e.how === "perfect" ? "#FFE070" : "#A0E0FF", at: now }); ui.arcBurst(fx, LX + e.lane * LW + LW / 2, LINE, [COL[e.lane], "#FFFFFF"], e.how === "perfect" ? 12 : 6, 120, 200); }
      else if (e.kind === "miss") { fl.push({ lane: e.lane, text: "MISS", c: "#FF7060", at: now }); this.tone(110, 0.15, "sawtooth", 0.05); } else if (e.kind === "empty") this.tone(180, 0.05, "square", 0.02);
      else if (e.kind === "boo") { ui.cgSfx("cardlose", 0.5); fx.shake = 0.3; } else if (e.kind === "done") { ui.cgSfx("victory", 0.5); ui.cgNote = `The tune is done: ${Math.round(e.acc * 100)}% struck, a bonus of ${e.bonus}.`; }
    },
    draw(p, L, now) {
      const bg = p.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#1A0A14"); bg.addColorStop(1, "#3A1A1A"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      for (const sx of [0, W]) { const cg = p.createLinearGradient(sx, 0, sx === 0 ? 40 : W - 40, 0); cg.addColorStop(0, "#8A1A28"); cg.addColorStop(1, "#4A0A14"); p.fillStyle = cg; p.fillRect(sx === 0 ? 0 : W - 40, 0, 40, H); p.strokeStyle = "rgba(0,0,0,0.3)"; for (let k = 0; k < 4; k++) { const x = sx === 0 ? 8 + k * 9 : W - 8 - k * 9; p.beginPath(); p.moveTo(x, 0); p.lineTo(x, H); p.stroke(); } }
      // lanes
      const beatK = L ? 1 - (((L.t % L.beat) + L.beat) % L.beat) / L.beat : 0;
      for (let i = 0; i < 4; i++) { const x = LX + i * LW, lg = p.createLinearGradient(0, 0, 0, LINE); lg.addColorStop(0, "rgba(255,255,255,0)"); lg.addColorStop(1, `${COL[i]}33`); p.fillStyle = lg; p.fillRect(x + 2, 0, LW - 4, LINE); p.strokeStyle = "rgba(255,255,255,0.08)"; p.strokeRect(x + 2.5, -1, LW - 5, LINE + 2); }
      if (L) for (let b = Math.ceil(L.t / L.beat); b * L.beat < L.t + 1.6; b++) { const y = LINE - (b * L.beat - L.t) * PX * (L.bpm / 100); p.strokeStyle = b % 4 ? "rgba(255,255,255,0.05)" : "rgba(255,220,150,0.12)"; p.beginPath(); p.moveTo(LX, y); p.lineTo(LX + 4 * LW, y); p.stroke(); }
      // the strike line and the stones
      p.fillStyle = `rgba(255,230,160,${0.25 + beatK * 0.25})`; p.fillRect(LX, LINE - 2, LW * 4, 4);

      for (let i = 0; i < 4; i++) { const x = LX + i * LW + LW / 2, k = Math.max(0, 1 - (now - (CM.ui && CM.ui.bdPress ? CM.ui.bdPress[i] : 0)) / 160); p.save(); if (k) { p.shadowColor = COL[i]; p.shadowBlur = 20 * k; } p.fillStyle = k ? COL[i] : "#2A2030"; p.beginPath(); p.ellipse(x, LINE + 4 * k, 22, 12, 0, 0, Math.PI * 2); p.fill(); p.restore(); p.strokeStyle = COL[i]; p.lineWidth = 2; p.beginPath(); p.ellipse(x, LINE + 4 * k, 22, 12, 0, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; p.fillStyle = "#F0E0D0"; p.font = "bold 12px monospace"; p.textAlign = "center"; p.fillText("DFJK"[i], x, LINE + 26); p.textAlign = "left"; }

      if (L) { // notes
        const sp = PX * (L.bpm / 100); for (const N of L.notes) { if (N.hit && N.hit !== "miss") continue; const y = LINE - (N.t - L.t) * sp; if (y < -20) break; if (y > H + 20) continue; const x = LX + N.lane * LW + LW / 2, missed = N.hit === "miss"; p.save(); p.globalAlpha = missed ? 0.3 : 1; p.shadowColor = COL[N.lane]; p.shadowBlur = missed ? 0 : 10; const g2 = p.createRadialGradient(x - 5, y - 4, 1, x, y, 16); g2.addColorStop(0, "#FFFFFF"); g2.addColorStop(1, COL[N.lane]); p.fillStyle = g2; p.beginPath(); p.moveTo(x, y - 12); p.lineTo(x + 18, y); p.lineTo(x, y + 12); p.lineTo(x - 18, y); p.closePath(); p.fill(); p.restore(); }
        // calls
        this.flash = (this.flash || []).filter((q) => now - q.at < 500); for (const q of this.flash) { const k = (now - q.at) / 500; p.globalAlpha = 1 - k; p.fillStyle = q.c; p.font = "bold 14px Georgia"; p.textAlign = "center"; p.fillText(q.text, LX + q.lane * LW + LW / 2, LINE - 30 - k * 20); p.textAlign = "left"; } p.globalAlpha = 1;
        if (L.combo >= 5) { p.fillStyle = "#FFE070"; p.font = `bold ${22 + Math.min(10, L.combo / 5)}px Georgia`; p.textAlign = "center"; p.fillText(`${L.combo}`, W / 2, 70); p.font = "11px Georgia"; p.fillText(`COMBO${L.combo >= 10 ? ` ×${1 + Math.min(3, Math.floor(L.combo / 10))}` : ""}`, W / 2, 86); p.textAlign = "left"; }
        // cheer
        const ch = Math.max(0, L.cheer) / 100; p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(W - 30, 30, 12, 300); const cg = p.createLinearGradient(0, 330, 0, 30); cg.addColorStop(0, "#E04030"); cg.addColorStop(0.5, "#F0C040"); cg.addColorStop(1, "#80F080"); p.fillStyle = cg; p.fillRect(W - 28, 330 - 296 * ch, 8, 296 * ch); p.fillStyle = "#F0E0B0"; p.font = "9px Georgia"; p.fillText("CHEER", W - 38, 344);
        const prog = CM.ARC.clamp(L.t / L.len, 0, 1); p.fillStyle = "rgba(255,255,255,0.15)"; p.fillRect(LX, 8, LW * 4, 4); p.fillStyle = "#F0C040"; p.fillRect(LX, 8, LW * 4 * prog, 4);
        if (L.t < 0) { p.fillStyle = "#FFE070"; p.font = "bold 40px Georgia"; p.textAlign = "center"; p.fillText(String(Math.ceil(-L.t / L.beat)), W / 2, 220); p.textAlign = "left"; } }
      // the crowd
      for (let k = 0; k < 14; k++) { const x = 20 + k * 26, bob = L && !L.dead ? Math.abs(Math.sin((L.t / L.beat) * Math.PI + k)) * 5 * (L.cheer / 100) : 0, y = H - 12 - bob; p.fillStyle = ["#3A2A20", "#2A2030", "#4A3020"][k % 3]; p.beginPath(); p.arc(x, y, 11, Math.PI, 0); p.fill(); p.beginPath(); p.arc(x, y - 14, 7, 0, Math.PI * 2); p.fill(); if (L && L.cheer > 70 && k % 4 === 1) { p.strokeStyle = "#3A2A20"; p.lineWidth = 3; p.beginPath(); p.moveTo(x + 6, y - 8); p.lineTo(x + 10, y - 26 - bob); p.stroke(); p.lineWidth = 1; } }
      const fl = p.createLinearGradient(0, H - 40, 0, H); fl.addColorStop(0, "rgba(255,200,120,0)"); fl.addColorStop(1, "rgba(255,200,120,0.12)"); p.fillStyle = fl; p.fillRect(0, H - 40, W, 40);
    },
  });
}
