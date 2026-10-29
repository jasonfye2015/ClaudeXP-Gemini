"use strict";
// Where it all starts: the game, the window, the renderer and the sounds wired together, the keys, and the frame loop
// (real time: a frame that comes late moves the camera as far as it should have).
window.addEventListener("DOMContentLoaded", () => {
  const game = new CM.Game();
  const ui = new CM.UI(game, document.getElementById("app"));
  const renderer = new CM.Renderer(ui.canvas);
  const link = document.createElement("link");
  link.rel = "icon"; link.href = CM.art.icon();
  document.head.appendChild(link);
  CM.game = game; CM.ui = ui; CM.renderer = renderer;                 // (for the tests, and for curiosity)

  if (!renderer.ok) {
    const warn = document.createElement("div");
    warn.style.cssText = "position:fixed;left:0;right:0;top:0;padding:10px;background:#5A1010;color:#fff;font:14px Georgia;text-align:center;z-index:50";
    warn.textContent = renderer.error + " The dungeon can't be shown, but the Hall of Fame and your saves are safe.";
    document.body.appendChild(warn);
  }

  // ---- textures by depth, the floor's mesh, the camera ----
  const artCache = {};
  let themeOn = -1;
  function useTheme(number) {
    const i = CM.themeIndex(number);
    if (i === themeOn || !renderer.ok) return;
    if (!artCache[i]) artCache[i] = CM.art.build(CM.THEMES[i]);
    renderer.setTextures(artCache[i]);
    themeOn = i;
  }
  const demo = CM.makeFloor(1, "title");                                 // the corridor behind the title
  let demoCell = null;
  function showDemo() {
    useTheme(1);
    renderer.setFloor(demo, CM.THEMES[0]);
    if (!demoCell) {                                                     // a square with a long view down a corridor
      const dist = CM.distances(demo.grid, [1, 1]);
      let best = null, score = -1;
      for (const k of dist.keys()) {
        const [x, y] = k.split(",").map(Number);
        for (let f = 0; f < 4; f++) {
          let d = 0;
          while (d < 9 && demo.grid[y + CM.DIRS[f][1] * (d + 1)] && demo.grid[y + CM.DIRS[f][1] * (d + 1)][x + CM.DIRS[f][0] * (d + 1)] === 0) d++;
          if (d > score) { score = d; best = [x, y, f]; }
        }
      }
      demoCell = best || [1, 1, 2];
    }
    renderer.setCamera(demoCell[0], demoCell[1], demoCell[2]);
    renderer.setSprites([]);
  }
  game.on("floor", (floor) => {
    if (!renderer.ok) return;
    useTheme(floor.number);
    renderer.setFloor(floor, CM.themeFor(floor.number));
    renderer.setCamera(floor.pos[0], floor.pos[1], floor.facing);
  });
  game.on("moved", (x, y) => renderer.moveTo(x, y, game.settings.smooth ? 180 : 0));
  game.on("turned", (facing) => renderer.turnTo(facing, game.settings.smooth ? 160 : 0));
  game.on("mesh", () => { if (renderer.ok && game.floor) renderer.setFloor(game.floor, CM.themeFor(game.floor.number)); });
  game.on("teleported", (x, y) => renderer.setCamera(x, y, game.floor.facing));
  game.on("spin", (facing) => (game.settings.smooth ? renderer.spinTo(facing) : renderer.turnTo(facing, 0)));
  game.on("mode", (mode) => {
    CM.audio.ambience(mode === "explore" || mode === "combat");
    if (mode === "title") showDemo();
    else if (game.floor && renderer.ok) {
      useTheme(game.floor.number);
      renderer.setFloor(game.floor, CM.themeFor(game.floor.number));
      renderer.setCamera(game.floor.pos[0], game.floor.pos[1], game.floor.facing);
    }
  });
  game.on("sound", (name) => CM.audio.play(name));
  const applySettings = (s) => {
    renderer.snap = !s.smooth;
    CM.audio.setEnabled(s.sound);
    CM.audio.setVolume(s.volume);
    ui.$("#view .fps").classList.toggle("on", s.fps);
  };
  game.on("settings", applySettings);
  applySettings(game.settings);

  // ---- what stands in the corridors: the floor's things, or the foes of the fight ----
  const dying = new Map();                                               // foe -> when it fell
  const flashes = new Map();                                             // foe -> flash left
  game.on("fx", (fx) => {
    if (fx.kind === "hit") flashes.set(fx.foe, 1);
    if (fx.kind === "die") dying.set(fx.foe, performance.now());
    if ((fx.kind === "hit" || fx.kind === "miss") && renderer.ok) {
      const where = foePlace(fx.foe);
      const at = where && renderer.project(where.wx, where.wh, where.wz);
      if (at) ui.floatText(at[0], at[1] - 10, fx.kind === "miss" ? "miss" : String(fx.amount), fx.kind === "miss" ? "miss" : fx.spell ? "spell" : "");
    }
  });
  game.on("mode", (mode) => { if (mode !== "combat") { dying.clear(); flashes.clear(); } });

  function foePlace(foe) {
    if (game.mode !== "combat" || !game.foeKey) return null;
    const [x, y] = game.foeKey.split(",").map(Number);
    const foes = game.foes, i = foes.indexOf(foe), n = foes.length;
    const right = [Math.cos(renderer.yaw), Math.sin(renderer.yaw)];
    const off = n === 1 ? 0 : CM.clamp((i - (n - 1) / 2) * 0.32, -0.42, 0.42);
    const back = (i % 2) * 0.12;
    const fwd = [Math.sin(renderer.yaw), -Math.cos(renderer.yaw)];
    const dx = right[0] * off + fwd[0] * back, dz = right[1] * off + fwd[1] * back;
    const big = foe.boss ? 1.25 : 0.85;
    return { x, y, dx, dz, w: big, h: big, wx: x + 0.5 + dx, wz: y + 0.5 + dz, wh: big + 0.02, m: foe };
  }

  function sprites() {
    const fl = game.floor, out = [], hud = [];
    if (!fl) return { out, hud };
    const now = performance.now();
    const near = (x, y) => Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 12;
    for (const [key, thing] of Object.entries(fl.things)) {
      let [x, y] = key.split(",").map(Number);
      if (!near(x, y)) continue;
      if (thing.type === "chest") out.push({ x, y, layer: "chest", w: 0.75, h: 0.75 });
      else if (thing.type === "ladder") out.push({ x, y, layer: "hatch", w: 0.92, flat: true });
      else if (thing.type === "stairs_up") out.push({ x, y, layer: "stairs_up", w: 0.6, h: 1.0 });
      else if (thing.type === "key") out.push({ x, y, layer: "key", w: 0.4, h: 0.4 });
      else if ((thing.type === "monsters" || thing.type === "boss") && !(game.mode === "combat" && key === game.foeKey)) {
        const m = thing.group[0];
        if (thing.anim) {                                               // on the move: it slides from where it was
          const k = Math.min(1, (now - thing.anim.at) / 320);
          if (k >= 1) delete thing.anim;
          else { const e = CM.ease(k); x = CM.lerp(thing.anim.from[0], x, e); y = CM.lerp(thing.anim.from[1], y, e); }
        }
        out.push({ x, y, layer: `monster:${m.name}`, w: m.boss ? 1.25 : 0.85, h: m.boss ? 1.25 : 0.85 });
      }
    }
    for (const [key, f] of Object.entries(fl.features)) {
      const [x, y] = key.split(",").map(Number);
      if (!near(x, y)) continue;
      const ns = fl.grid[y - 1] && fl.grid[y - 1][x] === 0 && fl.grid[y + 1] && fl.grid[y + 1][x] === 0;   // (the corridor runs north-south)
      if (f.type === "door") out.push({ x, y, layer: f.open ? "door_open" : f.locked ? "door_locked" : "door", axis: ns ? "ns" : "ew" });
      else if (f.type === "gate") out.push({ x, y, layer: f.open ? "gate_open" : "gate", axis: ns ? "ns" : "ew" });
      else if (f.type === "pit") out.push({ x, y, layer: "pit", flat: true, w: 0.96 });
      else if (f.type === "trapdoor" && f.known) out.push({ x, y, layer: "trapdoor", flat: true, w: 0.96 });
      else if (f.type === "teleporter") out.push({ x, y, layer: "teleporter", flat: true, w: 0.9, glow: 0.85 });
      else if (f.type === "fountain") out.push({ x, y, layer: f.used ? "fountain_dry" : "fountain", w: 0.9, h: 0.9 });
      else if (f.type === "altar") out.push({ x, y, layer: "altar", w: 0.9, h: 0.9 });
      else if (f.type === "lever") out.push({ x, y, layer: f.pulled ? "lever_pulled" : "lever", face: f.face, w: 0.34, h: 0.34 });
      else if (f.type === "carving") out.push({ x, y, layer: "carving", face: f.face, w: 0.62, h: 0.5 });
    }
    if (game.mode === "combat") {
      for (const m of game.foes) {
        const place = foePlace(m);
        if (!place) continue;
        let alpha = 1;
        if (m.hp <= 0) {
          const t = (now - (dying.get(m) || now)) / 700;
          if (t >= 1) continue;
          alpha = 1 - t;
        } else hud.push(place);
        const flash = flashes.get(m) || 0;
        if (flash > 0) flashes.set(m, Math.max(0, flash - 0.08));
        out.push(Object.assign({ layer: `monster:${m.name}`, flash: flash * 0.8, alpha }, place));
      }
    }
    return { out, hud };
  }

  // ---- keys ----
  const held = new Set();
  const MOVES = { KeyW: ["move", 0], ArrowUp: ["move", 0], KeyS: ["move", 2], ArrowDown: ["move", 2], KeyA: ["turn", -1], ArrowLeft: ["turn", -1],
    KeyD: ["turn", 1], ArrowRight: ["turn", 1], KeyQ: ["move", 3], KeyE: ["move", 1] };
  function act(code) {
    const m = MOVES[code];
    if (!m || game.mode !== "explore") return false;
    if (m[0] === "move") game.move(m[1]); else game.turn(m[1]);
    return true;
  }
  window.addEventListener("keydown", (e) => {
    CM.audio.unlock();
    if (e.code === "F3") { e.preventDefault(); ui.toggleFps(); return; }
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT")) {
      if (e.code === "Enter" && e.target.id === "seed") ui.startNew();
      if (e.code === "Escape" && ui.screen === "create") ui.show("title");
      return;
    }
    if (ui.dialogOpen()) { if (e.code === "Escape" || (e.code === "Tab" && ui.$("#bigmap").classList.contains("on"))) { e.preventDefault(); ui.closeDialogs(); } return; }
    if (ui.screen === "title") {
      if (e.code === "Enter" || e.code === "Space") { e.preventDefault(); if (game.canContinue()) game.continueRun(); else ui.startNew(); }
      return;
    }
    if (ui.screen === "create") { if (e.code === "Escape") ui.show("title"); else if (e.code === "Enter") ui.setOut(); return; }
    if (ui.screen === "bag") { if (e.code === "Escape" || e.code === "KeyI") game.closeBag(); return; }
    if (["Digit1", "Digit2", "Digit3", "Digit4"].includes(e.code) && game.mode !== "title") { ui.openSheet(Number(e.code.slice(-1)) - 1); return; }
    if (e.code === "Escape") { e.preventDefault(); ui.openDialog("#dlg-pause"); return; }
    if (e.code === "Tab") { e.preventDefault(); if (game.mode !== "title") ui.toggleBigMap(); return; }
    if (game.mode === "explore") {
      if (MOVES[e.code]) { e.preventDefault(); if (!e.repeat) { held.add(e.code); if (!renderer.busy) act(e.code); } return; }
      if (e.code === "Space") { e.preventDefault(); game.use(); }
      else if (e.code === "KeyI") game.openBag();
    } else if (game.mode === "combat") {
      const a = { KeyF: "fight", KeyC: "cast", KeyP: "potion", KeyR: "run" }[e.code];
      if (a) game.combatRound(a);
    } else if (game.mode === "camp") {
      if (e.code === "KeyI") game.openBag();
    }
  });
  window.addEventListener("keyup", (e) => held.delete(e.code));
  window.addEventListener("blur", () => held.clear());
  window.addEventListener("beforeunload", () => { if (game.dirty) game.saveRun(); });
  window.addEventListener("pointerdown", () => CM.audio.unlock(), { once: false });

  // ---- the frame loop ----
  let last = performance.now(), fpsTime = 0, frames = 0, fps = 0;
  function frame(now) {
    const dt = Math.min(0.1, Math.max(0, (now - last) / 1000));
    last = now;
    if (renderer.ok) {
      renderer.resize();
      if (game.mode === "title") {
        renderer.yaw += dt * 0.08;                                        // a slow look around
        renderer.light = 1;
        renderer.setSprites([]);
      } else {
        if (game.mode === "explore" && !renderer.busy && held.size) {
          for (const code of held) if (act(code)) break;                  // walking while the key is held
        }
        game.tick(dt);                                                    // the monsters move; the run saves now and then
        renderer.light = game.lightFactor();
        const { out, hud } = sprites();
        renderer.setSprites(out);
        renderer.frame(dt);
        ui.drawHud(hud, (x, y, z) => renderer.project(x, y, z));
      }
      if (game.mode === "title") renderer.frame(dt);
    }
    frames++; fpsTime += dt;
    if (fpsTime >= 0.5) { fps = Math.round(frames / fpsTime); frames = 0; fpsTime = 0; ui.$("#view .fps").textContent = `${fps} fps`; }
    requestAnimationFrame(frame);
  }
  showDemo();
  requestAnimationFrame(frame);
});
