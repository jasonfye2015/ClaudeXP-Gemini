"use strict";
// Where it all starts: the game, the window, the renderer, the sounds and the music wired together, the keys, and the
// frame loop (real time: a frame that comes late moves the camera as far as it should have).
window.addEventListener("DOMContentLoaded", () => {
  const game = new CM.Game();
  const ui = new CM.UI(game, document.getElementById("app"));
  const renderer = new CM.Renderer(ui.canvas);
  const link = document.createElement("link");
  link.rel = "icon"; link.href = CM.art.icon();
  document.head.appendChild(link);
  CM.game = game; CM.ui = ui; CM.renderer = renderer;                 // (for the tests, and for curiosity)

  // ---- around the game: a save or a film in the link; the app's manifest and its worker, where a server serves the file ----
  const linkIn = () => {
    const payload = CM.linkPayload(location.hash);
    if (!payload) return;
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) { /* the hash stays */ }
    setTimeout(() => ui.offerLink(payload), 50);
  };
  linkIn();
  if (!CM.linkPayload(location.hash) && !/[?&]nocard\b/.test(location.search)) ui.showSplash();   // the title card, before the first screen (not when a shared link is being opened)
  window.addEventListener("hashchange", linkIn);                         // (a link pasted into an open page's address)
  if (/^https?:$/.test(location.protocol)) {
    const m = document.createElement("link"); m.rel = "manifest"; m.href = "manifest.webmanifest"; document.head.appendChild(m);
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => { /* no worker: the page still plays */ });
  }
  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); ui.installPrompt = e; ui.showInstall(true); });
  window.addEventListener("appinstalled", () => { ui.installPrompt = null; ui.showInstall(false); game.titleNote = CM.t("install.note"); ui.refreshTitle(); });

  if (!renderer.ok) {
    const warn = document.createElement("div");
    warn.style.cssText = "position:fixed;left:0;right:0;top:0;padding:10px;background:#5A1010;color:#fff;font:14px Georgia;text-align:center;z-index:50";
    warn.textContent = renderer.error + " The dungeon can't be shown, but the Hall of Fame and your saves are safe.";
    document.body.appendChild(warn);
  }

  // ---- textures by depth and by theme, the floor's mesh, the camera ----
  let artCache = {}, cacheOrder = [];
  let themeOn = -1, lookOn = null, dreamOn = false, seasonOn = null;
  const lookNow = () => (CM.art.hasLook(game.settings.look) ? game.settings.look : "drawn");   // (a pack still decoding: the drawn art stands in)
  function useTheme(number) {
    const i = CM.themeIndex(number), look = lookNow();
    const season = CM.season ? CM.season(game) : "summer";
    const uc = CM.isUndercroft(number) || CM.isTowerFloor(number);   // (the Undercroft and the Mage Tower: sets of their own)
    if (((number === 0 ? -2 : number === -1 ? -3 : uc ? (CM.isTowerFloor(number) ? -5 : -4) : i) === themeOn && look === lookOn && Boolean(game.dream) === dreamOn && (number > 0 || season === seasonOn)) || !renderer.ok) return;
    const special = number === 0 ? CM.TOWN_THEME : number === -1 ? CM.WOOD_THEME : CM.isTowerFloor(number) ? CM.TOWER_THEME : uc ? CM.UNDERCROFT_THEME : null, key = special ? `${look}:${special.name}:${season}` : `${look}:${i}${game.dream ? ":dream" : ""}`;   // (the surface's set is the season's)
    CM.art.season = season; seasonOn = season;
    if (!artCache[key]) {
      artCache[key] = CM.art.build(special ? special : game.dream ? CM.dreamTheme(CM.THEMES[i]) : CM.THEMES[i], look);
      cacheOrder.push(key);
      while (cacheOrder.length > 6) delete artCache[cacheOrder.shift()];      // (the sets share their drawn canvases: half a dozen bands kept)
    }
    renderer.setTextures(artCache[key]);
    themeOn = number === 0 ? -2 : number === -1 ? -3 : uc ? (CM.isTowerFloor(number) ? -5 : -4) : i; lookOn = look; dreamOn = Boolean(game.dream);
  }
  // the theme changed, or its pack has arrived: the view and every portrait and icon follow
  function relook() {
    themeOn = -1;
    if (game.mode === "title") showDemo();
    else if (game.floor && renderer.ok) {
      useTheme(game.floor.number);
      renderer.setFloor(game.floor, CM.themeFor(game.floor.number));
    }
    ui.restyle();
  }
  const demo = CM.makeFloor(1, "title");                                 // the corridor behind the title
  let demoCell = null;
  function showDemo() {
    renderer.seed = "title";
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
    renderer.seed = game.seed; renderer.season = CM.season ? CM.season(game) : "summer";
    useTheme(floor.number);
    renderer.setFloor(floor, CM.themeFor(floor.number));
    renderer.setCamera(floor.pos[0], floor.pos[1], floor.facing);
  });
  let walkReady = 0;                                                    // (a heavy pack: the next step waits)
  game.on("moved", (x, y) => { const pace = game.walkPace ? game.walkPace() : 1; renderer.moveTo(x, y, game.settings.smooth ? 180 * pace : 0); walkReady = performance.now() + (pace - 1) * 220; });
  game.on("turned", (facing) => renderer.turnTo(facing, game.settings.smooth ? 160 : 0));
  game.on("mesh", () => { if (renderer.ok && game.floor) renderer.setFloor(game.floor, CM.themeFor(game.floor.number)); });
  game.on("teleported", (x, y) => renderer.setCamera(x, y, game.floor.facing));
  game.on("spin", (facing) => (game.settings.smooth ? renderer.spinTo(facing) : renderer.turnTo(facing, 0)));
  // ---- what's heard: the depth's ambience and tune, the fight's, the camp's, the title's - and the ending's ----
  const tuneFor = () => (game.mode === "combat" ? (game.foes.some((m) => CM.unmoved(m) && m.hp > 0) ? "boss" : "battle") : game.mode === "camp" ? "camp" : game.mode === "title" ? ui.ending || "title"
    : `depth${CM.themeIndex(game.floor ? game.floor.number : 1)}`);
  const soundscape = () => {
    const mode = game.mode;
    CM.audio.ambience(mode === "explore" || mode === "combat" || mode === "camp", mode === "camp" ? 4 : soundBand(game.floor ? game.floor.number : 1));
    CM.music.start(tuneFor());
  };
  game.on("mode", soundscape);
  game.on("floor", soundscape);
  ui.onEnding = soundscape;
  const STEPS = ["step", "step_water", "step_hall", "step_cold"];        // a footfall for each depth (the Deep's bands borrow one)
  const soundBand = (n) => CM.AMBIENCE_OF[CM.themeIndex(n)] || 0;
  game.on("sound", (name) => CM.audio.play(name === "step" && game.floor ? STEPS[soundBand(game.floor.number)] || "step" : name));
  game.on("near", (kind, d, pan) => CM.audio.near(kind, 1 - d / 8, pan || 0));
  game.on("magetower", () => ui.openMageTower());
  game.on("cabin", () => ui.openCabin());
  game.on("claudeita", () => ui.openClaudeita());                      // (Claudeita's cave: 76c-cave.js)
  game.on("cave", () => { caveIn = {}; caveFire = false; caveAcc = 0; ui.caveStart(); ui.refresh(); });                                // (Leshy's table: 76b-cabin.js)
  game.on("mode", (mode) => { if (mode !== "tower") { towerIn = {}; if (document.pointerLockElement && document.exitPointerLock) document.exitPointerLock(); } });   // (out of the tower: the mouse is free)
  game.on("towerfloor", (run) => { if (!renderer.ok) return; useTheme(run.fl.number); renderer.setFloor(run.fl, CM.TOWER_THEME); renderer.setCamera(run.fl.start[0], run.fl.start[1], 0); towerIn = {}; ui.refresh(); });                       // (the tower's doors: who goes in)
  game.on("snore", (d, pan) => { try { CM.audio.play("snore", 0.35 * Math.max(0.1, 1 - d / 7), pan || 0); } catch (e) { /* quiet */ } });   // (a sleeper, somewhere close)
  game.on("moved", (x, y) => { const fl = game.floor; if (!fl || !(fl.decor || []).some((dc) => dc.kind === "water" && Math.abs(dc.x - x) + Math.abs(dc.y - y) <= 2) || Math.random() > 0.3) return; try { CM.audio.play("lap", 0.25); } catch (e) { /* quiet */ } });   // (water, near)   // something is coming: louder the nearer, from the side it is on
  game.on("floor", (fl) => CM.music.setDepth(((fl.number - 1) % 5) / 4));      // deeper into its band, the tune gains a voice
  game.on("floor", (fl) => {                                             // chapter cards: the band's epigraph on its first floor; on its last, a word that the walls below will differ
    if (fl.number % 1 !== 0 || fl.number > CM.BOTTOM || game.film) return;
    if (fl.number === 0) { ui.titleCard(CM.TOWN_THEME.name, CM.t(CM.isNight(game) ? "town.card.night" : "town.card")); return; }
    if (fl.number === -1) { ui.titleCard(CM.WOOD_THEME.name, CM.isNight(game) ? "The trees close over the path, and the dark has eyes." : "Green light, birdsong, and three cave mouths somewhere under the roots."); return; }
    if (fl.number < 0) return;
    const ch = Object.values(CM.CHAPTERS).find((c) => c.band === CM.themeIndex(fl.number));
    if (!ch) return;
    if ((fl.number - 1) % 5 === 0) ui.titleCard(CM.bandName(game, fl.number), game.dream ? "What Caer Duin might have been." : ch.epigraph);
    else if (fl.number % 5 === 0 && Object.values(CM.LORE_TEXT).some((l) => l.contradicts && CM.LORE_TEXT[l.contradicts].chapter === Object.keys(CM.CHAPTERS).find((k) => CM.CHAPTERS[k] === ch))) ui.titleCard(ch.name, "Below, the walls will say otherwise.");
  });
  game.on("mode", (mode) => {
    if (mode === "title") showDemo();
    else if (game.floor && renderer.ok) {
      useTheme(game.floor.number);
      renderer.setFloor(game.floor, CM.themeFor(game.floor.number));
      renderer.setCamera(game.floor.pos[0], game.floor.pos[1], game.floor.facing);
    }
  });
  const applySettings = (s) => {
    if (lookOn !== null && lookNow() !== lookOn) relook();
    detailCap = 2; applyDetail();
    renderer.snap = !s.smooth;
    CM.audio.setEnabled(s.sound);
    CM.audio.setVolume(s.volume);
    CM.music.setEnabled(s.music !== false);
    CM.music.setVolume(s.musicVolume === undefined ? 0.5 : s.musicVolume);
    ui.$("#view .fps").classList.toggle("on", s.fps);
    CM.fxSpeed = { normal: 1, fast: 2, instant: 6 }[s.speed] || 1;
    CM.reducedMotion = s.motion === undefined ? Boolean(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) : Boolean(s.motion);
    document.getElementById("app").style.zoom = { normal: "", large: "1.15", larger: "1.32" }[s.text] || "";
    document.body.classList.toggle("contrast", Boolean(s.contrast));
    const deckShaped = window.matchMedia && window.matchMedia("(max-width: 1300px) and (max-height: 840px) and (pointer: coarse)").matches;
    document.body.classList.toggle("handheld", s.layout === "on" || (s.layout !== "off" && deckShaped));
    renderAuto = !s.render || s.render === "auto";
    if (!renderAuto) renderer.scale = { full: 1, three: 0.75, half: 0.5 }[s.render] || 1;
    else if (!renderer.scale) renderer.scale = 1;
  };
  let renderAuto = true, slowFor = 0, quickFor = 0;
  const RENDER_STEPS = [1, 0.75, 0.5];
  // the Detail setting, and how far the step-down has lowered it: the props' density, the floor rebuilt when it changes
  let detailCap = 2;
  const detailNow = () => Math.min(CM.DETAIL_ORDER.indexOf(game.settings.detail || "medium") < 0 ? 1 : CM.DETAIL_ORDER.indexOf(game.settings.detail || "medium"), detailCap);
  const applyDetail = () => { const d = CM.DETAIL[CM.DETAIL_ORDER[detailNow()]]; if (d !== renderer.density) { renderer.density = d; if (game.floor && renderer.ok && game.mode !== "title") renderer.setFloor(game.floor, CM.themeFor(game.floor.number)); } };
  function autoScale(dt) {                                               // frames coming late for two seconds: a step down (the Detail first, then the render scale); quick for ten: a step back up
    if (dt > 0.022) { slowFor += dt; quickFor = 0; } else if (dt < 0.013) { quickFor += dt; slowFor = 0; } else { slowFor = 0; quickFor = 0; }
    if (slowFor > 2 && detailNow() > 0) { detailCap = detailNow() - 1; slowFor = 0; applyDetail(); return; }
    if (!renderAuto) { if (quickFor > 10 && detailCap < 2) { detailCap += 1; quickFor = 0; applyDetail(); } return; }
    const i = RENDER_STEPS.indexOf(renderer.scale || 1);
    if (slowFor > 2 && i < RENDER_STEPS.length - 1) { renderer.scale = RENDER_STEPS[i + 1]; slowFor = 0; }
    else if (quickFor > 10 && i > 0) { renderer.scale = RENDER_STEPS[i - 1]; quickFor = 0; }
    else if (quickFor > 10 && detailCap < 2) { detailCap += 1; quickFor = 0; applyDetail(); }
  }
  game.on("settings", applySettings);
  applySettings(game.settings);
  CM.audio.unlock();                                                     // (where the page may: the Timeline's window; a browser waits for a click or key)
  soundscape();
  CM.art.load().then(() => { if (lookNow() !== lookOn) relook(); });    // the packs, decoded: a theme that waited for them comes in

  // ---- spectacle: what flies, bursts and shakes for each thing that happens; CM.Effects (45-fx.js) carries them ----
  const fxs = new CM.Effects();
  CM.fx = fxs;
  const dying = new Map();                                               // foe -> when it fell
  const flashes = new Map();                                             // foe -> flash left
  const lunges = new Map();                                              // foe -> when it lunged at the party
  const hits = new Map(), fledAt = new Map(), rising = new Map();       // foe -> when it was struck, when it ran, when it rose into its title (28-motion.js)
  const fwdV = () => [Math.sin(renderer.yaw), 0, -Math.cos(renderer.yaw)], rightV = () => [Math.cos(renderer.yaw), 0, Math.sin(renderer.yaw)];
  const fromParty = (side = 0) => { const e = renderer.eye, f = fwdV(), r = rightV(); return [e[0] + f[0] * 0.3 + r[0] * side * 0.2, 0.4, e[2] + f[2] * 0.3 + r[2] * side * 0.2]; };
  const beforeParty = (d = 0.3) => { const e = renderer.eye, f = fwdV(); return [e[0] + f[0] * d, 0.45, e[2] + f[2] * d]; };
  const atFoe = (foe, k = 0.5) => { const p = foePlace(foe); return p ? [p.wx, p.h * k, p.wz] : null; };
  const later = (fn) => { const hold = fxs.holdUntil - performance.now(); if (hold > 0) setTimeout(fn, hold); else fn(); };   // (a blow waits for its bolt to land)
  const ELEMENT = { fire: { layer: "fx:fire", tint: "rgba(255,120,30,0.28)" }, frost: { layer: "fx:frost", tint: "rgba(120,200,255,0.25)" },
    force: { layer: "fx:force", tint: "rgba(200,120,255,0.22)" }, holy: { layer: "fx:holy", tint: "rgba(255,240,180,0.3)" }, arrow: { layer: "fx:arrow", tint: null } };
  function shoot(foe, element, opts = {}) {                             // a bolt from the party to a foe, bursting where it lands
    const to = atFoe(foe);
    if (!to) return;
    const el = ELEMENT[element] || ELEMENT.force, arrow = element === "arrow";
    fxs.projectile({ from: fromParty(opts.side || 0), to, layer: el.layer, size: arrow ? 0.16 : opts.size || 0.22, ms: arrow ? 220 : 320, trail: arrow ? null : el.layer, arc: arrow ? 0.04 : 0.12,
      then: () => { fxs.burst({ at: to, layer: element === "frost" ? "fx:frost" : "fx:spark", n: arrow ? 5 : 12, size: element === "frost" ? 0.1 : 0.07 }); if (el.tint) ui.tint(el.tint, 260); } });
  }
  function blastFire(foes) {                                            // a fireball: to the middle of them, then fire on each
    const places = foes.map((m) => atFoe(m, 0.5)).filter(Boolean);
    if (!places.length) return;
    const mid = places.reduce((a, p) => [a[0] + p[0] / places.length, a[1] + p[1] / places.length, a[2] + p[2] / places.length], [0, 0, 0]);
    fxs.projectile({ from: fromParty(0), to: mid, layer: "fx:fire", size: 0.34, ms: 360, trail: "fx:fire",
      then: () => { for (const p of places) fxs.burst({ at: p, layer: "fx:fire", n: 9, size: 0.09, speed: 1.3, up: 1.4, ms: 550 }); ui.tint("rgba(255,120,30,0.45)", 400); renderer.shake(0.35); } });
  }
  function floatAt(foe, text, cls) {
    if (!renderer.ok) return;
    const where = foePlace(foe), at = where && renderer.project(where.wx, where.wh, where.wz);
    if (at) ui.floatText(at[0], at[1] - 10, text, cls);
  }
  function castFx(fx) {                                                 // a spell, a skill, a scroll or a wand: its light
    const id = fx.id, foes = fx.foes && fx.foes.length ? fx.foes : game.living();
    switch (id) {
      case "missile": shoot(fx.foe, "force"); break;
      case "firebolt": shoot(fx.foe, "fire"); break;
      case "fire": if (fx.foe) shoot(fx.foe, "fire"); else blastFire(foes); break;           // (a wand aims; a scroll is a fireball)
      case "smite": shoot(fx.foe, "holy"); break;
      case "fireball": blastFire(foes); break;
      case "frost": for (const m of foes) { const at = atFoe(m, 0); if (at) fxs.rain({ at: [at[0], 0, at[2]], n: 9 }); } ui.tint("rgba(120,200,255,0.3)", 500); break;
      case "lightning": case "calllightning": { const at = atFoe(fx.foe, 0.55); if (at) fxs.flare({ at: [at[0], 0.6, at[2]], layer: "fx:bolt", size: 1.1, ms: 300, grow: 0.1 }); ui.tint("rgba(220,235,255,0.55)", 260); renderer.shake(0.35); break; }
      case "sleep": case "lullaby": ui.tint("rgba(160,120,255,0.25)", 600); for (const m of foes) { const at = atFoe(m, 0.8); if (at) fxs.drift({ at, n: 5, size: 0.05, rise: 0.4, ms: 1100 }); } break;
      case "blink": case "teleport": ui.tint("rgba(232,216,255,0.8)", 400); break;
      case "light": ui.tint("rgba(255,240,200,0.45)", 700); break;
      case "turn": for (const m of foes) if (m.undead) { const at = atFoe(m, 0.6); if (at) fxs.flare({ at, layer: "fx:holy", size: 0.7, ms: 500, rise: 0.3, grow: 0.5 }); } ui.tint("rgba(255,240,180,0.4)", 500); break;
      case "thorns": for (const m of foes) { const at = atFoe(m, 0.05); if (at) fxs.burst({ at, layer: "fx:leaf", n: 10, size: 0.1, speed: 0.9, up: 2.6, gravity: 4 }); } break;
      case "entangle": { const at = atFoe(fx.foe, 0.05); if (at) fxs.burst({ at, layer: "fx:leaf", n: 12, size: 0.1, speed: 0.7, up: 2.4, gravity: 4 }); break; }
      case "volley": foes.slice(0, 2).forEach((m, i) => shoot(m, "arrow", { side: i ? 0.5 : -0.5 })); break;
      case "aimed": shoot(fx.foe, "arrow"); break;
      case "mark": case "mockery": { const at = atFoe(fx.foe, 0.9); if (at) fxs.drift({ at, n: 6, size: 0.05, rise: 0.25, ms: 700 }); break; }
      case "bash": { const at = atFoe(fx.foe, 0.5); if (at) fxs.burst({ at, n: 10, size: 0.06 }); renderer.shake(0.3); break; }
      case "trick": { const at = atFoe(fx.foe, 0.75); if (at) fxs.burst({ at, n: 10, size: 0.05, speed: 0.6, up: 0.4, gravity: 2 }); break; }
      case "protection": case "sanctuary": ui.tint("rgba(140,180,255,0.3)", 600); break;
      case "bless": case "rally": case "song": ui.tint("rgba(255,230,150,0.25)", 600); break;
      default: break;
    }
  }
  function spectacle(fx) {
    const now = performance.now();
    switch (fx.kind) {
      case "intent": renderer.zoomTo(0.9, 600); break;
      case "intro": if (fx.foe) rising.set(fx.foe, now); break;
      case "hit": flashes.set(fx.foe, 1); hits.set(fx.foe, now); if (fx.foe && fx.foe.hp > 0) CM.audio.bark(fx.foe.kind || fx.foe.name, "hit"); later(() => { const at = atFoe(fx.foe, 0.55); if (at && !fx.spell) fxs.burst({ at, n: 7, size: 0.05, speed: 1.0, ms: 450 }); floatAt(fx.foe, String(fx.amount), fx.spell ? "spell" : ""); }); break;
      case "miss": later(() => floatAt(fx.foe, "miss", "miss")); break;
      case "die": {
        dying.set(fx.foe, now);
        if (fx.foe && !fx.foe.fled) CM.audio.bark(fx.foe.kind || fx.foe.name, "die");
        const at = atFoe(fx.foe, 0.4);
        if (!at) break;
        fxs.burst({ at, layer: fx.foe.undead ? "fx:shard" : "fx:spark", n: CM.unmoved(fx.foe) ? 40 : 14, size: fx.foe.undead ? 0.1 : 0.06, speed: 1.6, up: 1.8 });
        if (CM.unmoved(fx.foe)) { fxs.ring({ at: [at[0], 0, at[2]], to: 3 }); renderer.shake(0.9); ui.tint(fx.foe.guardian ? CM.GUARDIANS[fx.foe.guardian].tint : "rgba(120,240,255,0.35)", 600); }
        break;
      }
      case "hurt": { const frac = fx.hero && fx.hero.max ? fx.amount / fx.hero.max : 0; if (frac >= 0.2) later(() => renderer.shake(Math.min(1, frac * 1.4))); break; }
      case "swing": renderer.punch(); if (fx.hero && fx.hero.weapon && fx.hero.weapon.props && fx.hero.weapon.props.bow && fx.foe) shoot(fx.foe, "arrow"); break;
      case "attack": {
        const from = atFoe(fx.foe, 0.6);
        if (fx.breath && from) fxs.projectile({ from, to: beforeParty(0.25), layer: "fx:fire", size: 0.5, ms: 380, arc: 0.05, then: () => { ui.tint("rgba(255,120,30,0.45)", 400); renderer.shake(0.5); } });
        else if (fx.ranged && from) fxs.projectile({ from, to: beforeParty(0.2), layer: "fx:arrow", size: 0.14, ms: 260, trail: null, arc: 0.03 });
        else lunges.set(fx.foe, now);
        break;
      }
      case "cast": castFx(fx); break;
      case "cold": ui.tint("rgba(120,200,255,0.4)", 700); fxs.rain({ at: beforeParty(0.8), n: 14, spread: 1.2 }); renderer.shake(0.25); break;
      case "trap": {
        if (fx.trap === "blade") { ui.tint("rgba(200,30,20,0.5)", 300); renderer.shake(0.6); }
        else if (fx.trap === "gas") ui.tint("rgba(120,200,60,0.45)", 900);
        else if (fx.trap === "needle") ui.tint("rgba(200,30,20,0.3)", 200);
        else if (fx.trap === "alarm") { ui.tint("rgba(255,255,255,0.5)", 250); renderer.shake(0.25); }
        break;
      }
      case "summon": for (const m of game.foes) if (m.summoned && m.hp > 0 && !dying.has(m)) { const at = atFoe(m, 0.1); if (at) fxs.burst({ at, layer: fx.layer || "fx:shard", n: 12, size: 0.09, speed: 1.2, up: 2.4 }); } renderer.shake(0.3); break;
      case "grasp": ui.tint("rgba(40,120,160,0.55)", 700); fxs.rain({ at: beforeParty(0.5), n: 10, spread: 0.8 }); renderer.shake(0.45); break;
      case "slam": { const at = atFoe(fx.foe, 0.05); if (at) fxs.ring({ at: [at[0], 0, at[2]], to: 2.6, ms: 500 }); fxs.burst({ at: beforeParty(0.4), n: 16, size: 0.06, speed: 1.4, up: 1.2 }); ui.tint("rgba(255,150,40,0.35)", 400); renderer.shake(1); break; }
      case "sear": ui.tint("rgba(255,120,30,0.3)", 220); fxs.burst({ at: beforeParty(0.3), layer: "fx:fire", n: 6, size: 0.06, speed: 0.8, up: 1.2, ms: 400 }); break;
      case "relic": ui.tint("rgba(255,230,150,0.45)", 900); fxs.drift({ at: beforeParty(0.6), n: 12, size: 0.06, spread: 1.0, rise: 0.7, ms: 1400 }); break;
      case "rise": {
        if (fx.form2) CM.music.shift(3);
        const at = atFoe(fx.foe, 0.05);
        if (at) { fxs.ring({ at: [at[0], 0, at[2]], to: 3.2, ms: 900 }); fxs.burst({ at: [at[0], 0.5, at[2]], layer: "fx:shard", n: 24, size: 0.1, speed: 1.8, up: 2.6 }); }
        ui.tint("rgba(120,240,255,0.4)", 700); renderer.shake(0.8);
        break;
      }
      case "shatter": ui.tint("rgba(120,240,255,0.5)", 500); fxs.burst({ at: beforeParty(0.6), layer: "fx:shard", n: 20, size: 0.08, speed: 2, up: 2 }); renderer.shake(0.5); break;
      case "sparkle": fxs.burst({ at: [fx.at[0] + 0.5, 0.35, fx.at[1] + 0.5], n: 16, size: 0.05, speed: 0.8, up: 1.6, gravity: 2 }); break;
      case "mend": { const at = atFoe(fx.foe, 0.3); if (at) fxs.drift({ at, layer: "fx:leaf", n: 8, size: 0.06, rise: 0.5, ms: 900 }); break; }
      case "ward": { const at = atFoe(fx.foe, 0.5); if (at) fxs.flare({ at, layer: "fx:frost", size: 0.9, ms: 500, grow: 0.3 }); break; }
      case "combo": ui.tint("rgba(255,230,150,0.35)", 500); break;
      case "intro": { const G = fx.foe.guardian ? CM.GUARDIANS[fx.foe.guardian] : null; ui.titleCard(fx.foe.name, G ? (fx.foe.echo ? "an echo, in " : "in ") + G.lair.name : "in his palace"); renderer.shake(0.35); renderer.punch(); break; }
      default: break;
    }
  }
  game.on("fx", spectacle);
  game.on("fell", () => renderer.shake(0.6));
  game.on("crowned", () => renderer.zoomTo(1.15, 1600));
  game.on("mode", (mode) => { if (mode !== "combat") { CM.music.shift(0); CM.music.setDanger(0); } });
  game.on("over", (won) => { if (!won && renderer.ok) { renderer.rollNow = 0; renderer.rollTo(0.12, 1200); setTimeout(() => renderer.rollTo(0, 2500), 1600); } });
  game.on("floor", () => fxs.clear());
  game.on("mode", (mode) => { if (mode !== "combat") { dying.clear(); flashes.clear(); lunges.clear(); hits.clear(); fledAt.clear(); rising.clear(); } if (mode === "title") fxs.clear(); });
  // a click on a foe in the view chooses it
  ui.$("#hud").addEventListener("click", (e) => {
    if (game.mode !== "combat") return;
    const r = e.currentTarget.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
    let best = null, bd = 90;
    for (const f of ui.lastHud || []) {
      const d = Math.hypot(f.sx - mx, f.sy + 40 - my);
      if (d < bd) { bd = d; best = f; }
    }
    if (best) game.setTarget(best.index);
  });

  function foePlace(foe) {
    if (game.mode !== "combat" || !game.foeKey) return null;
    const [x, y] = game.foeKey.split(",").map(Number);
    const shown = game.foes.filter((f) => (f.hp > 0 && !f.hidden) || dying.has(f)), i = shown.indexOf(foe), n = shown.length;
    if (i < 0) return null;
    const right = [Math.cos(renderer.yaw), Math.sin(renderer.yaw)];
    const off = n === 1 ? 0 : CM.clamp((i - (n - 1) / 2) * (n > 4 ? 0.22 : 0.32), -0.46, 0.46);
    let back = (i % 2) * 0.14 + (foe.summoned ? 0.3 : 0) + (foe.boss ? 0.34 : foe.guardian ? 0.22 : 0) + (foe.row === "back" ? 0.28 : 0);     // (the Lich King keeps his distance; the back row stands back)
    const fwd = [Math.sin(renderer.yaw), -Math.cos(renderer.yaw)];
    const dx = right[0] * off + fwd[0] * back, dz = right[1] * off + fwd[1] * back;
    const G = foe.guardian ? CM.GUARDIANS[foe.guardian] : null;
    const w = foe.boss ? 0.95 : G ? 0.9 * G.size : 0.85, h = foe.boss ? 0.98 : G ? 0.92 * G.size : 0.85;
    return { x, y, dx, dz, w, h, wx: x + 0.5 + dx, wz: y + 0.5 + dz, wh: h + 0.02, m: foe, shade: foe.elite ? 1.2 : 1,
      layer: `monster:${foe.kind || foe.name}`, ghost: (CM.monsterKind(foe.kind || foe.name) || {}).body === "ghost", echo: Boolean(foe.echo) };
  }

  // the air about the party: what belongs where (CM.airKinds), as many as the Detail allows; chimneys on the town's
  // houses by hash, the smoke rising from them
  const air = new CM.Air(); CM.air = air;
  let airFloor = null, chimneys = [];
  function stepAir(dt) {
    const fl = game.floor;
    if (!fl || CM.reducedMotion || game.mode === "title") { air.parts = []; return; }
    if (airFloor !== fl) { airFloor = fl; air.parts = []; chimneys = [];
      if (fl.number === 0 || fl.number === -1) chimneys = CM.chimneysOf(fl).map((c) => [c.x, c.z, c.top]); }   // (the town's, and the cabin's in the Wood)   // (the smoke from the chimneys' own tops)
    const surface = fl.number === 0 || fl.number === -1, detail = Object.keys(CM.DETAIL).find((k) => CM.DETAIL[k] === renderer.density) || "medium";   // (the Detail in force, after any step-down)
    const budget = CM.AIR_BUDGET[detail] || 0, weather = surface ? CM.weather(game) : "clear";
    const towerNear = fl.number === -1 && Math.abs(fl.pos[0] - CM.MAGE_TOWER.at[0]) + Math.abs(fl.pos[1] - CM.MAGE_TOWER.at[1]) <= 9;
    const kinds = budget ? CM.airKinds({ towerNear, surface, band: CM.themeIndex(fl.number >= 1 ? fl.number : 1), season: CM.season(game), weather, night: CM.isNight(game), hour: CM.hourOf(game), town: fl.number === 0 || (fl.number === -1 && Math.abs(fl.pos[0] - CM.CABIN.centre[0]) + Math.abs(fl.pos[1] - CM.CABIN.centre[1]) <= 12) }) : [];
    const scale = detail === "high" ? 1 : 0.6;
    air.step(Math.min(dt, 0.1), { kinds: kinds.map((k) => ({ id: k.id, rate: k.rate * scale })), eye: renderer.eye, budget, chimneys, wind: CM.windOf(weather), open: surface ? null : (x, y) => CM.isOpen(fl, x, y) });
  }

  // the lights about the party: the wall torches, the lair's embers, crystals and fungus, the props that glow, and the
  // town's lamps at night - nearest first, twelve at most (the shader's limit)
  const LIGHT = { torch: { colour: [0.95, 0.55, 0.22], reach: 3.2, z: 0.62, flicker: true }, ember: { colour: [1.0, 0.42, 0.12], reach: 2.2, z: 0.1, flicker: true },
    crystal: { colour: [0.35, 0.7, 1.0], reach: 2.4, z: 0.5 }, fungus: { colour: [0.35, 0.9, 0.55], reach: 2.0, z: 0.15 }, candle: { colour: [0.9, 0.6, 0.25], reach: 2.0, z: 0.25, flicker: true },
    candelabra: { colour: [0.95, 0.65, 0.28], reach: 2.6, z: 0.5, flicker: true }, fungi: { colour: [0.35, 0.85, 0.6], reach: 1.6, z: 0.2 }, shard: { colour: [0.4, 0.75, 1.0], reach: 1.6, z: 0.3 },
    slag: { colour: [1.0, 0.45, 0.15], reach: 1.6, z: 0.1, flicker: true }, lamp: { colour: [1.0, 0.75, 0.4], reach: 4.0, z: 1.2 } };
  function lightsNear(fl) {
    if (!fl || !renderer.ok) return [];
    const tint = CM.themeFor(fl.number).lightColour, out = [], [px, py] = fl.pos, push = (kind, x, z, y, k = 1) => { const L = LIGHT[kind]; if (L) out.push({ x, y: L.z, z, reach: L.reach, colour: (kind === "torch" && tint ? tint : L.colour).map((c) => c * k), flicker: L.flicker, d: Math.abs(x - px - 0.5) + Math.abs(z - py - 0.5) }); };
    // (the wall torches: below always, on the surface after dark)
    if (!CM.themeFor(fl.number).sky || CM.isNight(game)) for (const t of decorations(fl).torches) { if (Math.abs(t.x - px) + Math.abs(t.y - py) > 10) continue; const [dx, dy] = CM.DIRS[t.face]; push("torch", t.x + 0.5 + dx * 0.4, t.y + 0.5 + dy * 0.4); }
    for (const dc of fl.decor || []) if (LIGHT[dc.kind] && Math.abs(dc.x - px) + Math.abs(dc.y - py) <= 10) push(dc.kind, dc.x + 0.5, dc.y + 0.5);
    const night = CM.isNight(game);
    for (const p of renderer.standing) { const P = CM.PROPS[p.id] || {}; if (LIGHT[p.id] && (P.glow || (P.night && night)) && Math.abs(p.x - px) + Math.abs(p.y - py) <= 10) push(p.id, p.x + 0.5 + p.dx, p.y + 0.5 + p.dz); }
    return out.sort((a, b) => a.d - b.d).slice(0, 12);
  }

  // the living dungeon: torches on some walls (never over a lever or carving, never on a secret door) and, in the
  // flooded vaults, water on some floors - the same ones each time, from the seed
  let decor = { key: null, torches: [], water: [] };
  function decorations(fl) {
    const rain = (fl.number === 0 || fl.number === -1) && CM.weather(game) === "rain", key = `${game.seed}:${fl.number}:${fl.grid.length}:${rain ? CM.dayOf(game) : ""}`;
    if (decor.key === key) return decor;
    const torches = [], water = [], size = fl.grid.length, wet = CM.themeIndex(fl.number) === 1 || CM.isUndercroft(fl.number);   // (the Undercroft stands in water)
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      if (fl.grid[y][x] !== 0) continue;
      const here = fl.features[`${x},${y}`];
      for (let f = 0; f < 4; f++) {
        const nx = x + CM.DIRS[f][0], ny = y + CM.DIRS[f][1];
        if (!fl.grid[ny] || fl.grid[ny][nx] !== 1) continue;
        const beyond = fl.features[`${nx},${ny}`];
        if (beyond && beyond.type === "secret") continue;
        if (here && (here.type === "lever" || here.type === "carving") && here.face === f) continue;
        const h = CM.hashSeed(`${game.seed}:torch:${x}:${y}:${f}`);
        if (h % 8 === 0) torches.push({ x, y, face: f, phase: h % 3 });
      }
      if (wet && !here && CM.hashSeed(`${game.seed}:water:${x}:${y}`) % 3 === 0) water.push({ x, y, phase: CM.hashSeed(`${game.seed}:ripple:${x}:${y}`) % 3 });
    }
    if (rain) for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {   // puddles in the rain, on the roads and the paths
      const g = CM.groundAt(fl, x, y), h = CM.hashSeed(`${game.seed}:puddle:${CM.dayOf(game)}:${x}:${y}`);
      if (fl.grid[y][x] === 0 && !fl.things[`${x},${y}`] && ["dirt", "cobbles", "flags"].includes(g) && h % 4 === 0) water.push({ x, y, phase: h % 3, w: 0.35 + (h % 7) * 0.04, dx: ((h >> 4) % 40 - 20) / 100, dz: ((h >> 9) % 40 - 20) / 100 });
    }
    for (const dc of fl.decor || []) if (dc.kind === "water" && !water.some((w) => w.x === dc.x && w.y === dc.y)) water.push({ x: dc.x, y: dc.y, phase: CM.hashSeed(`${game.seed}:ripple:${dc.x}:${dc.y}`) % 3 });
    decor = { key, torches, water };
    return decor;
  }

  // the things that move between two states: when each was seen to change, and which way a door swings (away from
  // whoever opened it); a thing first seen is as it was found (no swing)
  const movers = new Map();
  function changed(id, state, sideOf) {
    let st = movers.get(id);
    if (!st) { st = { state, at: null, side: sideOf ? sideOf() : 1 }; movers.set(id, st); }
    else if (st.state !== state) { st.state = state; st.at = performance.now(); if (sideOf) st.side = sideOf(); try { CM.audio.play(id.startsWith("door") ? "hinge" : id.startsWith("gate") ? "chain" : "lever", 0.5); } catch (e) { /* quiet */ } }
    return st;
  }
  // a frame of a monster's picture, where the theme has it (the Drawn frames; the Pixel tiles stand still)
  const frameOf = (layer, pose) => (pose && renderer.index && renderer.index[`${layer}:${pose}`] !== undefined ? `${layer}:${pose}` : layer);
  function sprites() {
    const fl = game.floor, out = [], hud = [];
    if (!fl) return { out, hud };
    const now = performance.now(), right = [Math.cos(renderer.yaw), Math.sin(renderer.yaw)];
    const near = (x, y) => Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 12;
    const lit = CM.isNight(game);
    if (renderer.index.shadow !== undefined) {                          // a soft shadow under whatever stands on the floor
      const under = (x, y, w, dx = 0, dz = 0) => out.push({ x, y, dx, dz, layer: "shadow", flat: true, w: w * 1.1, alpha: 0.9 });
      for (const [key, thing] of Object.entries(fl.things)) { const [x, y] = key.split(",").map(Number); if (!near(x, y)) continue; if (["monsters", "boss", "guardian", "chest", "hermit", "adventurer", "villager", "peddler", "burner", "rivals", "strongbox"].includes(thing.type) && !(game.mode === "combat" && key === game.foeKey)) under(x, y, 0.75); }
      for (const p of renderer.standing) if (Math.abs(p.x - fl.pos[0]) + Math.abs(p.y - fl.pos[1]) <= 12) under(p.x, p.y, p.w, p.dx, p.dz);
    }
    for (const p of renderer.standing) if (Math.abs(p.x - fl.pos[0]) + Math.abs(p.y - fl.pos[1]) <= 12) out.push({ x: p.x, y: p.y, dx: p.dx, dz: p.dz, layer: p.layer, w: p.w, h: p.h, glow: CM.PROPS[p.id].glow || (lit && CM.PROPS[p.id].night ? 0.9 : 0) });   // (the standing props, near the party; lamps lit at night)
    if (renderer.sky) {                                                 // the sun and the moon: far off, along their arc from the east over the south to the west
      const S = renderer.sky, eye = renderer.eye;
      for (const [t, layer, size] of [[S.sun, "sun", 6], [S.moon, `moon:${S.phase}`, 4]]) {
        if (t === null || (layer === "sun" && S.light < 0.12)) continue;
        const a = Math.PI * t, el = Math.sin(a) * 0.5, d = 52, wx = eye[0] + Math.cos(a) * Math.cos(el) * d, wz = eye[2] + Math.sin(a) * Math.cos(el) * d, wy = Math.sin(el) * d;
        out.push({ x: wx - 0.5, y: wz - 0.5, layer, w: size, h: size, lift: wy - size / 2, glow: 2, alpha: layer === "sun" ? 1 : Math.min(1, 0.4 + (1 - S.light)) });
      }
    }
    for (const [key, thing] of Object.entries(fl.things)) {
      let [x, y] = key.split(",").map(Number);
      if (!near(x, y)) continue;
      if (thing.type === "chest") out.push({ x, y, layer: "chest", w: 0.75, h: 0.75 });
      else if (thing.type === "ladder") out.push({ x, y, layer: "hatch", w: 0.92, flat: true });
      else if (thing.type === "stairs_up") out.push({ x, y, layer: "stairs_up", w: 0.6, h: 1.0 });
      else if (thing.type === "key") out.push({ x, y, layer: "key", w: 0.4, h: 0.4 });
      else if (thing.type === "phylactery") out.push({ x, y, layer: "phylactery", w: 0.7, h: 0.7, glow: 0.5 });
      else if (thing.type === "ghost") out.push({ x, y, layer: "npc:ghost", w: 0.8, h: 0.9, alpha: 0.8, glow: 0.4, lift: 0.05 + Math.sin(now / 900 + x) * 0.035 });
      else if (thing.type === "hermit") out.push({ x, y, layer: "npc:hermit", w: 0.75, h: 0.8 });
      else if (thing.type === "adventurer") out.push({ x, y, layer: "npc:adventurer", w: 0.75, h: 0.8 });
      else if (thing.type === "bones") out.push({ x, y, layer: "bones", w: 0.6, h: 0.42 });
      else if (thing.type === "rope") out.push({ x, y, layer: "rope", w: 0.5, h: 1.0 });
      else if (thing.type === "event") { const look = (CM.EVENTS[thing.event] || {}).look || "chest"; const flat = ["ember", "water1"].includes(look); out.push({ x, y, layer: look, w: flat ? 0.95 : 0.8, h: 0.8, flat, glow: 0.3 }); }
      else if (thing.type === "strongbox") out.push({ x, y, layer: "chest", w: 0.7, h: 0.6, glow: thing.opened ? 0 : 0.4, shade: 0.7 });
      else if (thing.type === "node") { const look = (CM.NODES[thing.band] || CM.NODES[0])[1], flat = ["ember", "water1"].includes(look); out.push({ x, y, layer: look, w: flat ? 0.9 : 0.6, h: flat ? 0.9 : 0.5, flat, glow: look === "crystal" ? 0.3 : 0 }); }
      else if (thing.type === "boxkey") out.push({ x, y, layer: "key", w: 0.45, h: 0.45, glow: 0.5 });
      else if (thing.type === "peddler") out.push({ x, y, layer: "npc:hermit", w: 0.8, h: 0.85, glow: 0.3 });
      else if (thing.type === "building") {                            // the house is the block behind the doorway; what stands in the doorway says its level: a foundation, a frame, or the sign over the door
        const P = CM.TOWN_PLOTS[thing.id] || {}, V = P.village ? CM.VILLAGE[P.village] : null, lvl = CM.plotLevel(game, thing.id), stage = P.always && !V ? 4 : CM.houseStage(lvl, V ? V.costs.length : 1);
        const face = CM.DIRS.findIndex(([dx, dy]) => ["door", "shop"].includes(CM.solidAt(fl, x + dx, y + dy)));
        if (stage <= 1) out.push({ x, y, layer: stage ? "house1" : "foundation", w: 0.9, h: 0.9 });
        else if (face >= 0 && renderer.index[`sign:${thing.id}`] !== undefined) out.push({ x, y, layer: `sign:${thing.id}`, face, w: 0.6, h: 0.45, lift: 0.5, glow: CM.isNight(game) ? 0.5 : 0.15 });
      }
      else if (thing.type === "well") out.push({ x, y, layer: "well", w: 0.8, h: 0.8 });
      else if (thing.type === "ucstair") { if (!thing.hidden) out.push({ x, y, layer: "hatch", w: 0.92, flat: true, shade: 0.8 }); }   // (the Undercroft's ways)
      else if (thing.type === "ucdown" || thing.type === "ucback") out.push({ x, y, layer: "hatch", w: 0.9, flat: true, shade: 0.75 });
      else if (thing.type === "ucup") out.push({ x, y, layer: "stairs_up", w: 0.6, h: 1.0 });
      else if (thing.type === "ucdoor") out.push({ x, y, layer: CM.undercroftDoorOpen(game) || (game.tally.guardians || []).includes("bell") ? "door" : "door_locked", w: 0.7, h: 0.95, shade: 0.7 });
      else if (thing.type === "portal") out.push({ x, y, layer: "solid:portal", w: 0.95, h: 1.25, glow: 0.45 + 0.15 * Math.sin(now / 500) });   // (the Mage Tower: 61d-magetower.js)
      else if (thing.type === "plinth") out.push({ x, y, layer: "solid:plinth", w: 0.7, h: 0.6 });
      else if (thing.type === "magedoor" || thing.type === "claudeita") { /* the doors are the tower's own, the cave's mouth the crag's: in the mesh */ }
      else if (thing.type === "errand") out.push({ x, y, layer: "key", w: 0.4, h: 0.4, glow: 0.6 + 0.3 * Math.sin(now / 400 + x) });   // (an errand's thing: it catches the light)
      else if (thing.type === "towerstair") { out.push({ x, y, layer: "stairs_up", w: 0.55, h: 0.9, shade: 0.8 }); const T = CM.TOWER_STAIRS[key]; if (T && !(game.perch && game.perch.from === key)) out.push({ x: T[0], y: T[1], dx: 0.3, dz: -0.25, layer: "npc:adventurer", w: 0.5, h: 0.55, lift: CM.TOWER.h }); }   // (the stair, and the watchman on the tower's top)
      else if (thing.type === "postern") out.push({ x, y, layer: CM.posternOpen(game) ? "door" : "door_locked", face: fl.number === 0 ? 0 : 1, w: 0.62, h: 0.86, lift: 0.07 });   // (a small door in the wall, or in the cliff)
      else if (thing.type === "villager") out.push({ x, y, layer: "npc:adventurer", w: 0.75, h: 0.8 });
      else if (thing.type === "signpost") out.push({ x, y, layer: "signpost", w: 0.55, h: 0.95 });
      else if (thing.type === "cross") out.push({ x, y, layer: "cross", w: 0.55, h: 0.75 });
      else if (thing.type === "woodgate") out.push({ x, y, layer: "gate_open", w: 1.0, h: 1.0 });
      else if (thing.type === "cave") out.push({ x, y, layer: thing.n === CM.dayOf(game) % 3 ? "hatch" : "bones", w: 0.9, flat: thing.n === CM.dayOf(game) % 3, h: 0.5, shade: 0.6 });
      else if (thing.type === "caveexit") out.push({ x, y, layer: "stairs_up", w: 0.6, h: 1.0 });
      else if (thing.type === "vein") out.push({ x, y, layer: `vein:${thing.ore}`, w: 0.7, h: 0.6 });
      else if (thing.type === "hut") out.push({ x, y, layer: "house2", w: 1.0, h: 1.0 });
      else if (thing.type === "farm") out.push({ x, y, layer: "house1", w: 1.0, h: 1.0 });
      else if (thing.type === "shrine") out.push({ x, y, layer: "altar", w: 0.8, h: 0.7 });
      else if (thing.type === "burner") out.push({ x, y, layer: "npc:hermit", w: 0.8, h: 0.85 });
      else if (thing.type === "rivals") out.push({ x, y, layer: "monster:Sellsword", w: 0.85, h: 0.85 });
      else if (thing.type === "wingstair" || thing.type === "wingexit") out.push({ x, y, layer: "hatch", w: 0.8, flat: true, shade: 0.75 });
      else if (thing.type === "wingstair_up") out.push({ x, y, layer: "stairs_up", w: 0.6, h: 1.0 });
      else if ((thing.type === "monsters" || thing.type === "boss" || thing.type === "guardian") && !(game.mode === "combat" && key === game.foeKey)) {
        const m = thing.group.find((f) => f.hp > 0 && !f.fled) || thing.group[0];
        if (thing.anim) {                                               // on the move: it slides from where it was
          const k = Math.min(1, (now - thing.anim.at) / 320);
          if (k >= 1) delete thing.anim;
          else { const e = CM.ease(k); x = CM.lerp(thing.anim.from[0], x, e); y = CM.lerp(thing.anim.from[1], y, e); }
        }
        const ghost = (CM.monsterKind(m.kind || m.name) || {}).body === "ghost", G = m.guardian ? CM.GUARDIANS[m.guardian] : null;
        const M = CM.motion({ now, phase: x * 2.1 + y * 1.3, sleeping: Boolean(thing.asleep), sway: Boolean(m.boss), reduced: CM.reducedMotion });   // (alive: it breathes; asleep, it lies)
        const side = (x + 0.5 - renderer.eye[0]) * right[0] + (y + 0.5 - renderer.eye[2]) * right[1];
        out.push({ x, y, layer: frameOf(`monster:${m.kind || m.name}`, !thing.asleep && Math.floor(now / 700 + x + y) % 2 ? "idle2" : ""), w: m.boss ? 0.95 : G ? 0.9 * G.size : 0.85, h: (m.boss ? 0.98 : G ? 0.92 * G.size : 0.85) * M.scaleY, shade: (m.elite || thing.champion ? 1.2 : 1) * (thing.asleep ? 0.85 : 1), alpha: m.echo ? 0.78 : 1,
          tilt: M.tilt, skew: M.skew, scale: M.scale !== 1 ? M.scale : undefined, mirror: CM.facesMirror(side), flash: thing.champion && !CM.reducedMotion ? 0.12 + 0.08 * Math.sin(now / 300) : 0,
          lift: thing.asleep ? 0 : Math.sin(now / (ghost ? 900 : 650) + x * 1.7 + y * 2.3) * (ghost ? 0.035 : 0.01) + (ghost ? 0.04 : 0) });   // (awake: it sways; a ghost floats; a champion glints)
      }
    }
    for (const [key, f] of Object.entries(fl.features)) {
      const [x, y] = key.split(",").map(Number);
      if (!near(x, y)) continue;
      const ns = fl.grid[y - 1] && fl.grid[y - 1][x] === 0 && fl.grid[y + 1] && fl.grid[y + 1][x] === 0;   // (the corridor runs north-south)
      if (f.type === "door") {                                         // a door swings on its hinge, away from the party (28-motion.js)
        const st = changed(`door:${fl.number}:${key}`, Boolean(f.open), () => (ns ? (fl.pos[1] < y ? 1 : -1) : (fl.pos[0] < x ? 1 : -1))), k = CM.reducedMotion ? (f.open ? 1 : 0) : CM.swing(Boolean(f.open), st.at, now, CM.SWING.doorMs);
        const pic = f.locked ? "door_locked" : f.riddle !== undefined ? "door_riddle" : "door";
        if (k <= 0.001) out.push({ x, y, layer: pic, axis: ns ? "ns" : "ew", glow: f.riddle !== undefined ? 0.35 : 0 });
        else out.push({ x, y, layer: pic, axis: ns ? "ns" : "ew", swing: k * CM.SWING.doorAngle, swingSide: st.side });
      }
      else if (f.type === "plate" && (f.gate || f.known)) out.push({ x, y, layer: f.gate && !f.pressed ? "plate" : "plate_pressed", flat: true, w: 0.62 });
      else if (f.type === "gate") { const st = changed(`gate:${fl.number}:${key}`, Boolean(f.open)), k = CM.reducedMotion ? (f.open ? 1 : 0) : CM.swing(Boolean(f.open), st.at, now, CM.SWING.gateMs); out.push({ x, y, layer: "gate", axis: ns ? "ns" : "ew", lift: k * CM.SWING.gateLift }); }   // (a portcullis lifts into the lintel)
      else if (f.type === "pit") out.push({ x, y, layer: "pit", flat: true, w: 0.96 });
      else if (f.type === "trapdoor" && f.known) out.push({ x, y, layer: "trapdoor", flat: true, w: 0.96 });
      else if (f.type === "teleporter") out.push({ x, y, layer: "teleporter", flat: true, w: 0.9, glow: 0.85 });
      else if (f.type === "spores") out.push({ x, y, layer: "fungus", flat: true, w: 0.9, glow: 0.5 + 0.2 * Math.sin(now / 600 + x), alpha: 0.8 });
      else if (f.type === "vents") out.push({ x, y, layer: "ember", flat: true, w: 0.9, glow: (Math.floor(now / 700) % 3 === 0 ? 1 : 0.35) });
      else if (f.type === "bonepiles") out.push({ x, y, layer: f.spent ? "bones" : "nest", w: f.spent ? 0.6 : 0.9, h: f.spent ? 0.42 : 0.75 });
      else if (f.type === "fountain") out.push({ x, y, layer: f.used ? "fountain_dry" : "fountain", w: 0.9, h: 0.9 });
      else if (f.type === "altar") out.push({ x, y, layer: "altar", w: 0.9, h: 0.9 });
      else if (f.type === "lever") { const st = changed(`lever:${fl.number}:${key}`, Boolean(f.pulled)), k = CM.reducedMotion ? (f.pulled ? 1 : 0) : CM.swing(Boolean(f.pulled), st.at, now, CM.SWING.leverMs);   // (thrown: one picture into the other)
        if (k < 1) out.push({ x, y, layer: "lever", face: f.face, w: 0.34, h: 0.34, alpha: 1 - k }); if (k > 0) out.push({ x, y, layer: "lever_pulled", face: f.face, w: 0.34, h: 0.34, alpha: k }); }
      else if (f.type === "carving") out.push({ x, y, layer: "carving", face: f.face, w: 0.62, h: 0.5 });
    }
    for (const dc of fl.decor || []) {                                   // a lair's furniture: the heaps of the nest, the throne, the anvils, the embers
      if (!near(dc.x, dc.y)) continue;
      if (dc.kind === "nest") out.push({ x: dc.x, y: dc.y, layer: "nest", w: 0.8, h: 0.62 });
      else if (dc.kind === "throne") out.push({ x: dc.x, y: dc.y, layer: "throne", w: 0.9, h: 1.0 });
      else if (dc.kind === "anvil") out.push({ x: dc.x, y: dc.y, layer: "anvil", w: 0.7, h: 0.62 });
      else if (dc.kind === "ember") out.push({ x: dc.x, y: dc.y, layer: "ember", flat: true, w: 0.98, glow: 0.7 + 0.25 * Math.sin(now / 240 + dc.x * 2.1 + dc.y * 1.3) });
      else if (dc.kind === "fungus") out.push({ x: dc.x, y: dc.y, layer: "fungus", flat: true, w: 0.9, glow: 0.6 + 0.2 * Math.sin(now / 700 + dc.x + dc.y) });
      else if (dc.kind === "crystal") out.push({ x: dc.x, y: dc.y, layer: "crystal", w: 0.7, h: 0.9, glow: 0.55 + 0.25 * Math.sin(now / 500 + dc.x * 1.7) });
      else if (dc.kind === "root") out.push({ x: dc.x, y: dc.y, layer: "root", w: 0.9, h: 0.95 });
      else if (dc.kind === "darkshrub") out.push({ x: dc.x, y: dc.y, dx: ((dc.x * 37 + dc.y * 11) % 30 - 15) / 100, dz: ((dc.x * 13 + dc.y * 29) % 30 - 15) / 100, layer: "prop:shrub", w: 1.0, h: 0.9, shade: 0.32 });   // (dark shrubs about the Mage Tower)
    }
    const d = decorations(fl), tframe = Math.floor(now / 120), wframe = Math.floor(now / 420);
    for (const t of d.torches) if (near(t.x, t.y)) out.push({ x: t.x, y: t.y, face: t.face, layer: `torch${(tframe + t.phase) % 3}`, w: 0.26, h: 0.44, lift: 0.12, glow: 0.85 });
    const frozen = fl.number === -1 && CM.weather(game) === "snow";      // (the river frozen, as the rules have it: crossed anywhere)
    for (const w of d.water) if (near(w.x, w.y)) out.push(frozen && !w.w ? { x: w.x, y: w.y, flat: true, w: 0.99, layer: "ice" } : { x: w.x, y: w.y, dx: w.dx || 0, dz: w.dz || 0, flat: true, w: w.w || 0.98, layer: `water${(wframe + w.phase) % 3}`, alpha: 0.75, water: true });   // (the water shader: 40-render.js)
    if (game.mode === "combat") {
      const living = game.attackable();
      const fwdv = [Math.sin(renderer.yaw), -Math.cos(renderer.yaw)];
      game.foes.forEach((m, i) => {
        if (m.fled && m.hp > 0 && !fledAt.has(m)) fledAt.set(m, now);   // (it has just run: seen running)
        if ((m.fled && !fledAt.has(m)) || (m.hidden && m.hp > 0)) return;
        const place = foePlace(m);
        if (!place) return;
        if (m.hp <= 0 && !dying.has(m)) dying.set(m, now);
        const lunge = lunges.get(m); if (lunge !== undefined && now - lunge > 400) lunges.delete(m);
        const M = CM.motion({ now, phase: place.dx * 7 + i * 1.9, lungeAt: lunges.get(m), hitAt: hits.get(m), fellAt: m.hp <= 0 ? dying.get(m) : undefined, fledAt: m.fled ? fledAt.get(m) : undefined,
          roseAt: rising.get(m), ghost: place.ghost, sway: Boolean(m.boss), reduced: CM.reducedMotion });
        if (M.done) { dying.delete(m); return; }
        const solid = place.echo ? 0.78 : 1;                             // (an echo of a guardian is drawn a little through)
        const lift = Math.sin(now / (place.ghost ? 900 : 600) + place.dx * 9) * (place.ghost ? 0.03 : 0.008) + (place.ghost ? 0.04 : 0) + M.lift;
        if (m.hp > 0 && !m.fled) { place.index = living.indexOf(m); place.chosen = place.index === (game.target || 0); hud.push(place); }
        const flash = flashes.get(m) || 0;
        if (flash > 0) flashes.set(m, Math.max(0, flash - 0.08));
        const pose = m.hp > 0 && lunges.has(m) ? "attack" : m.hp > 0 && Math.floor(now / 640 + place.dx * 5) % 2 ? "idle2" : "";
        const off = place.dx * right[0] + place.dz * right[1], away = M.back - M.forward;
        out.push(Object.assign({}, place, { layer: frameOf(place.layer, pose), flash: Math.max(flash * 0.8, M.flash), alpha: solid * M.alpha, lift, w: place.w, h: place.h * M.scaleY,
          dx: place.dx + fwdv[0] * away, dz: place.dz + fwdv[1] * away, tilt: M.tilt, skew: M.skew, scale: M.scale !== 1 ? M.scale : undefined, mirror: CM.facesMirror(off) }));
      });
    }
    out.push(...fxs.sprites(now));                                      // what flies and bursts, this frame
    out.push(...air.sprites(now / 1000));                               // what drifts in the air
    return { out, hud };
  }

  // ---- keys ----
  const held = new Set();
  let MOVES = {};
  function bindMoves() {                                                 // the movement keys as set (Settings > Keys), and the arrows always
    const K = game.settings.keys || CM.DEFAULT_KEYS;
    MOVES = { ArrowUp: ["move", 0], ArrowDown: ["move", 2], ArrowLeft: ["turn", -1], ArrowRight: ["turn", 1] };
    for (const [action, m] of [["forward", ["move", 0]], ["back", ["move", 2]], ["left", ["turn", -1]], ["right", ["turn", 1]], ["strafeLeft", ["move", 3]], ["strafeRight", ["move", 1]]]) if (K[action]) MOVES[K[action]] = m;
  }
  bindMoves();
  game.on("settings", bindMoves);
  function act(code) {
    const m = MOVES[code];
    if (!m || game.mode !== "explore") return false;
    if (m[0] === "move") game.move(m[1]); else game.turn(m[1]);
    return true;
  }
  window.addEventListener("keydown", (e) => {
    CM.audio.unlock();
    if (ui.splashOn) { e.preventDefault(); ui.leaveSplash(); return; }   // (the title card: any key goes on)
    const K = game.settings.keys || CM.DEFAULT_KEYS;
    if (ui.rebinding) { e.preventDefault(); ui.rebind(ui.rebinding, e.code); return; }   // (Settings > Keys: the next key pressed is the one)
    if (e.code === "F3") { e.preventDefault(); ui.toggleFps(); return; }
    if (game.mode === "tower" && game.towerRun && !ui.dialogOpen()) {   // the Mage Tower: real time (64e-towerrun.js)
      const f = TOWER_KEYS[e.code]; if (f) { e.preventDefault(); towerIn[f] = true; return; }
      if (e.code === K.use || e.code === "KeyE") { e.preventDefault(); if (game.towerUse) game.towerUse(); ui.refresh(); return; }
      if (e.code === "KeyL" && game.towerRun.atLadder()) { e.preventDefault(); game.towerClimb(true); ui.refresh(); return; }
      if (e.code !== "Escape") return;
    }
    if (game.mode === "cave" && game.caveRun && !ui.dialogOpen()) {     // Claudeita's cave: real time (64i-claudeita.js)
      const f = CAVE_KEYS[e.code], run = game.caveRun; if (f) { e.preventDefault(); caveIn[f] = true; return; }
      if (/^Digit[1-4]$/.test(e.code)) { const n = Number(e.code.slice(-1)) - 1; if (n < run.player.wands.length) run.player.current = n; return; }
      if (e.code === "KeyE" || e.code === K.use) { e.preventDefault(); run.interact(); return; }
      if (e.code === "Tab") { e.preventDefault(); ui.caveEdit = !ui.caveEdit; ui.cavePick = null; return; }
      if (e.code === "Escape" && ui.caveEdit) { e.preventDefault(); ui.caveEdit = false; return; }
      if (e.code !== "Escape") return;
    }
    if (game.film) { if (e.code === "Escape") { e.preventDefault(); game.stopFilm(); } else if (e.code === "Space") { e.preventDefault(); game.film.playing = !game.film.playing; ui.filmBar(); } return; }   // (a film: watch, or stop)
    if (game.travel && !ui.dialogOpen()) { game.stopTravel(); if (MOVES[e.code] || e.code === K.explore) { e.preventDefault(); return; } }   // (any key stops a walk; a move key only stops it)
    if (game.autoOn() && !ui.dialogOpen() && e.code !== K.autoPlay && (MOVES[e.code] || [K.use, K.explore, K.fight, K.auto, K.item, K.defend, K.run].includes(e.code))) { game.autoPlay(false); ui.refresh(); }   // (the reins: a move or a fight key takes them back)
    if (game.mode === "combat" && game.combat && game.combat.auto && e.code !== K.auto && !ui.dialogOpen()) game.autoFight(false);
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT")) {
      if (e.code === "Enter" && e.target.id === "seed") ui.startNew();
      if (e.code === "Escape" && ui.screen === "create") ui.show("title");
      return;
    }
    if (ui.dialogOpen()) {
      const ending = ui.$("#dlg-over").classList.contains("on");
      if (e.code === "Escape" || (e.code === K.map && ui.$("#bigmap").classList.contains("on")) || (ending && (e.code === "Enter" || e.code === "Space"))) { e.preventDefault(); ui.closeDialogs(); }
      else if (ui.$("#dlg-lore").classList.contains("on") && e.code === "Space") { e.preventDefault(); ui.finishRead(); }
      else if (ui.$("#dlg-riddle").classList.contains("on") && /^Digit[1-3]$/.test(e.code)) ui.pickRiddle(Number(e.code.slice(-1)));
      else if (ui.$("#dlg-choice").classList.contains("on") && /^Digit[1-3]$/.test(e.code)) ui.pickChoice(Number(e.code.slice(-1)));
      else if (e.code === K.journal && ui.$("#dlg-journal").classList.contains("on")) ui.closeDialogs();
      return;
    }
    if (ui.screen === "title") {
      if (e.code === "Enter" || e.code === "Space") { e.preventDefault(); if (game.canContinue()) game.continueRun(); else ui.startNew(); }
      return;
    }
    if (ui.screen === "create") { if (e.code === "Escape") ui.show("title"); else if (e.code === "Enter") ui.setOut(); return; }
    if (ui.screen === "bag") { if (e.code === "Escape" || e.code === K.inventory) game.closeBag(); return; }
    if (game.mode === "combat") {                                        // a fight: the keys are the fight's
      if (e.code === "Tab" || e.code === K.map) { e.preventDefault(); game.setTarget((game.target || 0) + 1); return; }
      if (e.code === "Escape") { e.preventDefault(); if (ui.cmenu && ui.cmenu.kind !== "main") ui.combatMenu("main"); else ui.openDialog("#dlg-pause"); return; }
      if (/^Digit[5-8]$/.test(e.code) && game.combat && game.combat.waiting && (!ui.cmenu || ui.cmenu.kind === "main") && (game.belt || [])[Number(e.code.slice(-1)) - 5]) { ui.beltPick(Number(e.code.slice(-1)) - 5); return; }
      if (/^Digit[1-9]$/.test(e.code)) { ui.pick(Number(e.code.slice(-1))); return; }
      if (!(game.combat && game.combat.waiting)) return;
      if (e.code === K.fight) game.act("fight", game.target);
      else if (e.code === K.cast) ui.combatMenu(ui.cmenu && ui.cmenu.kind === "cast" ? "main" : "cast");
      else if (e.code === K.item) ui.combatMenu(ui.cmenu && ui.cmenu.kind === "item" ? "main" : "item");
      else if (e.code === K.defend) game.act("defend");
      else if (e.code === "KeyL" && game.readyPower(game.combat.waiting)) game.act("power", { who: game.target });
      else if (e.code === K.run) game.act("run");
      else if (e.code === K.auto) game.autoFight(!game.combat.auto);
      return;
    }
    if (ui.xmenu) {                                                      // a list open between fights
      if (e.code === "Escape" || e.code === K.cast) { e.preventDefault(); ui.closeMenu(); return; }
      if (/^Digit[1-9]$/.test(e.code)) { ui.pickOutside(Number(e.code.slice(-1))); return; }
      return;
    }
    if (["Digit1", "Digit2", "Digit3", "Digit4"].includes(e.code) && game.mode !== "title") { ui.openSheet(Number(e.code.slice(-1)) - 1); return; }
    if (/^Digit[5-8]$/.test(e.code) && (game.mode === "explore" || game.mode === "camp")) { const note = game.useBelt(Number(e.code.slice(-1)) - 5); if (note) game.say(note); ui.refresh(); return; }
    if (e.code === "Escape") { e.preventDefault(); ui.openDialog("#dlg-pause"); return; }
    if (e.code === K.autoPlay && game.mode !== "title" && !ui.dialogOpen()) { e.preventDefault(); game.autoPlay(); ui.refresh(); return; }
    if (e.code === K.map || e.code === "Tab") { e.preventDefault(); if (game.mode !== "title") ui.toggleBigMap(); return; }
    if (e.code === K.cast && (game.mode === "explore" || game.mode === "camp")) { ui.outsideCast(); return; }
    if (e.code === K.journal && (game.mode === "explore" || game.mode === "camp")) { ui.openJournal(); return; }
    if (e.code === K.calendar && (game.mode === "explore" || game.mode === "camp")) { ui.openCalendar(); return; }
    if (e.code === K.douse && game.mode === "explore" && game.floor && CM.isDeep(game.floor.number)) { game.douse(); ui.refresh(); return; }
    if (e.code === K.whereTo && game.mode === "explore" && game.floor && game.floor.number <= 0 && game.floor.number % 1 === 0 && !CM.isUndercroft(game.floor.number)) { ui.openWhereTo(); return; }
    if (game.mode === "explore") {
      if (MOVES[e.code]) { e.preventDefault(); if (!e.repeat) { held.add(e.code); if (!renderer.busy) act(e.code); } return; }
      if (e.code === K.use) { e.preventDefault(); game.use(); }
      else if (e.code === K.inventory) game.openBag();
      else if (e.code === K.explore) game.explore();
    } else if (game.mode === "camp") {
      if (e.code === K.inventory) game.openBag();
    }
  });

  // ---- a gamepad: the pad or stick moves, A uses or picks, B steps back, X the pack, Y casts, the shoulders sidestep or
  // pick the target, Start pauses, Select the map; in a list or a dialog the pad moves a highlight and A presses ----
  const padWas = {}, padHeld = {};
  const padKey = (code) => window.dispatchEvent(new KeyboardEvent("keydown", { code, bubbles: true, cancelable: true }));
  function padRole(i) {                                                 // what button i stands for, by Settings > Keys > Gamepad
    const P = game.settings.pad || CM.DEFAULT_PAD;
    let r = i >= 12 ? ["up", "down", "left", "right"][i - 12] + "Pad" : null;
    if (!r) for (const k of Object.keys(P)) if (P[k] === i) { r = k; break; }
    if (game.settings.swapAB && (r === "use" || r === "back")) r = r === "use" ? "back" : "use";   // (Settings: confirm with B, back with A)
    return r;
  }
  function padButton(i, now) {                                           // what button i does right now
    const K = game.settings.keys || CM.DEFAULT_KEYS, inFight = game.mode === "combat", listOpen = ui.padTargets().length > 0;
    const r = padRole(i);
    if (!r) return;
    if (game.travel) game.stopTravel();
    if (ui.screen === "title") { if (r === "use" || r === "pause") padKey("Enter"); return; }
    if (ui.screen === "create") { if (r === "use") padKey("Enter"); else if (r === "back") padKey("Escape"); return; }
    if (ui.screen === "bag") { if (r === "back" || r === "bag") padKey("Escape"); return; }
    if (listOpen) {
      if (r === "use") ui.padPress();
      else if (r === "back" || r === "pause") padKey("Escape");
      else if (r === "upPad" || r === "leftPad" || r === "left") ui.padFocus(-1);
      else if (r === "downPad" || r === "rightPad" || r === "right") ui.padFocus(1);
      return;
    }
    if (inFight) {
      if (r === "use") padKey(K.fight); else if (r === "back") padKey(K.defend); else if (r === "bag") padKey(K.item); else if (r === "cast") padKey(K.cast);
      else if (r === "left" || r === "right") padKey("Tab"); else if (r === "pause") padKey("Escape"); else if (r === "run") padKey(K.run); else if (r === "belt") padKey("Digit5");
      return;
    }
    if (r === "use") padKey(K.use); else if (r === "back" || r === "pause") padKey("Escape"); else if (r === "bag") padKey(K.inventory); else if (r === "cast") padKey(K.cast);
    else if (r === "map") padKey(K.map); else if (r === "left") act(K.strafeLeft || "KeyQ"); else if (r === "right") act(K.strafeRight || "KeyE"); else if (r === "belt") padKey("Digit5");
    else if (r === "upPad") act("ArrowUp"); else if (r === "downPad") act("ArrowDown"); else if (r === "leftPad") act("ArrowLeft"); else if (r === "rightPad") act("ArrowRight");
  }
  function pollGamepad(now) {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    const pad = [...pads].find((p) => p && p.connected);
    if (!pad) return;
    const pressed = pad.buttons.map((b) => b.pressed), ax = pad.axes[0] || 0, ay = pad.axes[1] || 0;
    if (Math.abs(ax) > 0.6 || Math.abs(ay) > 0.6) {                      // the stick, as the pad
      const dir = Math.abs(ax) > Math.abs(ay) ? (ax > 0 ? 15 : 14) : (ay > 0 ? 13 : 12);
      for (const d of [12, 13, 14, 15]) if (d !== dir) pressed[d] = pressed[d] || false;
      pressed[dir] = true;
    }
    if (ui.rebindingPad) {                                               // (Settings > Keys > Gamepad: the next button pressed is the one)
      const i = pressed.findIndex((down, j) => down && !padWas[j] && j < 12);
      if (i >= 0) ui.rebindPad(ui.rebindingPad, i);
      pressed.forEach((down, j) => { padWas[j] = down; });
      return;
    }
    pressed.forEach((down, i) => {
      if (down && !padWas[i]) { padButton(i, now); padHeld[i] = now; }
      else if (down && [12, 13, 14, 15].includes(i) && game.mode === "explore" && !ui.dialogOpen() && now - padHeld[i] > 260 && !renderer.busy) { padButton(i, now); padHeld[i] = now - 100; }   // (walking while held)
      padWas[i] = down;
    });
  }
  CM.pad = { button: (i) => padButton(i, performance.now()), poll: pollGamepad, role: padRole };   // (for the tests, and for curiosity)
  // a tap or a click on the view walks, out of a fight (in one, a click picks a foe)
  const view = ui.$("#view");
  let tapStart = null;
  view.addEventListener("pointerdown", (e) => { if (e.target.closest("button")) return; if (game.travel) game.stopTravel(); tapStart = { x: e.clientX, y: e.clientY, t: performance.now() }; });
  view.addEventListener("pointerup", (e) => {
    if (!tapStart || e.target.closest("button")) return;
    const moved = Math.hypot(e.clientX - tapStart.x, e.clientY - tapStart.y), quick = performance.now() - tapStart.t < 600;
    tapStart = null;
    if (moved > 24 || !quick) return;
    const r = view.getBoundingClientRect();
    if (ui.tapView((e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height)) e.preventDefault();
  });
  window.addEventListener("keyup", (e) => { held.delete(e.code); const f = TOWER_KEYS[e.code]; if (f) towerIn[f] = false; const g = CAVE_KEYS[e.code]; if (g) caveIn[g] = false; });
  // ---- Claudeita's cave's hands and feet: the mouse on its canvas aims and casts, and works the wand editor ----
  const caveXY = (e) => { const c = ui.$("#cavecanvas"), r = c.getBoundingClientRect(); return [(e.clientX - r.left) * (c.width / r.width), (e.clientY - r.top) * (c.height / r.height)]; };
  view.addEventListener("mousedown", (e) => { if (game.mode !== "cave" || !game.caveRun || !e.target.closest("#cavecanvas")) return; e.preventDefault(); const at = ui.caveMouse = caveXY(e); if (ui.caveEdit) ui.caveEditorClick(game.caveRun, at[0], at[1], e.button === 2); else if (e.button === 0) caveFire = true; });
  window.addEventListener("mouseup", (e) => { if (e.button === 0) caveFire = false; });
  window.addEventListener("mousemove", (e) => { if (game.mode === "cave" && ui.$("#cavecanvas")) ui.caveMouse = caveXY(e); });
  view.addEventListener("contextmenu", (e) => { if (game.mode === "cave") e.preventDefault(); });
  view.addEventListener("wheel", (e) => { if (game.mode !== "cave" || !game.caveRun || ui.caveEdit) return; e.preventDefault(); const pl = game.caveRun.player; if (pl.wands.length) pl.current = (pl.current + (e.deltaY < 0 ? -1 : 1) + pl.wands.length) % pl.wands.length; }, { passive: false });
  view.addEventListener("mousedown", (e) => { if (game.mode !== "tower" || e.target.closest("button")) return; e.preventDefault(); if (document.pointerLockElement !== view && view.requestPointerLock) { try { view.requestPointerLock(); } catch (er) { /* not here */ } } if (e.button === 2) towerIn.spell = true; else towerIn.fire = true; });
  window.addEventListener("mouseup", (e) => { if (e.button === 2) towerIn.spell = false; else towerIn.fire = false; });
  view.addEventListener("contextmenu", (e) => { if (game.mode === "tower") e.preventDefault(); });
  window.addEventListener("mousemove", (e) => { if (game.mode === "tower" && document.pointerLockElement === view) towerIn.look = (towerIn.look || 0) + e.movementX * 0.0028; });
  window.addEventListener("blur", () => held.clear());
  window.addEventListener("beforeunload", () => { if (game.dirty) game.saveRun(); });
  window.addEventListener("pointerdown", () => CM.audio.unlock(), { once: false });

  // ---- the Mage Tower's hands and feet (64e-towerrun.js): held keys, the mouse's turn ----
  const TOWER_KEYS = { KeyW: "fwd", ArrowUp: "fwd", KeyS: "back", ArrowDown: "back", KeyA: "left", KeyD: "right", KeyQ: "turnL", ArrowLeft: "turnL", KeyE_: "", ArrowRight: "turnR", Space: "fire", KeyF: "fire", KeyR: "spell", Digit2: "spell" };
  let towerIn = {}, towerMapT = 0;
  const CAVE_KEYS = { KeyA: "left", ArrowLeft: "left", KeyD: "right", ArrowRight: "right", KeyW: "jump", ArrowUp: "jump", Space: "jump" };
  let caveIn = {}, caveFire = false, caveAcc = 0, caveSfx = {};
  // a frame in Claudeita's cave: the run takes its steps by real time (30 a second, however often the frame comes), its
  // events become sounds, the canvas is drawn; when it is over, a moment to read the end, and out
  function caveFrame(now, dt) {
    const run = game.caveRun; if (!run) return;
    const still = ui.dialogOpen() || ui.caveEdit || ui.screen !== "play";
    if (!still && !run.over) { caveAcc += dt; let n = 0; while (caveAcc >= CM.CV.TICK && n < 4) { run.step(caveIn, ui.caveAim(run), caveFire); caveAcc -= CM.CV.TICK; n++; } if (n === 4) caveAcc = 0; } else caveAcc = 0;
    const sfx = (name, vol, gap = 0.06, rate = 1) => { if (now - (caveSfx[name] || 0) < gap * 1000) return; caveSfx[name] = now; try { CM.audio.play(name, vol, 0, rate); } catch (er) { /* quiet */ } };
    for (const ev of run.events) {
      if (ev.kind === "cast") sfx(ev.name === "Bomb" || ev.name === "Black Hole" ? "lever" : ev.name === "Digging Bolt" || ev.name === "Luminous Drill" ? "wanddig" : "zap", 0.22, 0.05, ev.name === "Spark Bolt" ? 1 : 0.8);
      else if (ev.kind === "boom") sfx("wandboom", Math.min(0.7, 0.25 + ev.r / 30), 0.08);
      else if (ev.kind === "zap") sfx("spell", 0.35, 0.1, 1.4);
      else if (ev.kind === "splash") sfx("splash", 0.3, 0.1);
      else if (ev.kind === "hit") sfx("hit", 0.18, 0.06);
      else if (ev.kind === "kill") sfx(ev.boss ? "toll" : "monster", ev.boss ? 0.8 : 0.25, 0.08);
      else if (ev.kind === "hurt") { sfx("hurt", 0.4, 0.15); ui.tint("rgba(200,30,20,0.3)", 200); }
      else if (ev.kind === "gold") sfx("coin", 0.2, 0.05);
      else if (ev.kind === "heart" || ev.kind === "fountain") sfx("heal", 0.5, 0.5);
      else if (ev.kind === "take" || ev.kind === "buy") sfx("chest", 0.4, 0.2);
      else if (ev.kind === "boss") sfx("elite", 0.7, 1);
      else if (ev.kind === "blink") sfx("teleport", 0.5, 0.3);
      else if (ev.kind === "foecast") sfx("miss", 0.15, 0.12);
      else if (ev.kind === "biome") { sfx("wind", 0.4, 1); if (ev.b) game.say(`${game.caveRun.player.name} comes down into ${CM.CV_BIOMES[ev.b].name}.`); }
      else if (ev.kind === "bossdown") { game.say(`${CM.CV_BOSSES[ev.b]} falls${ev.b < 4 ? ": the gate below it opens on a sanctuary - a fountain, a shop, and a rope up to the daylight" : ""}.`); ui.renderLog(); }
      else if (ev.kind === "dead") sfx("death", 0.7, 1);
      else if (ev.kind === "rope") sfx("stairs", 0.6, 1);
    }
    run.events.length = 0;
    if (run.over && !run.endAt) { run.endAt = now + (run.over === "dead" ? 2600 : 2200); if (run.over === "won") sfx("victory", 0.8, 1); }
    if (run.over && now >= run.endAt) { caveFire = false; caveIn = {}; game.leaveClaudeita(run.over); ui.refresh(); return; }
    ui.drawCave(run);
    if ((towerMapT += dt) > 0.5) { towerMapT = 0; ui.refresh(); }
  }
  function towerFrame(now, dt) {                                        // a frame in the tower: the run steps, the view follows the hero
    const run = game.towerRun; if (!run) return;
    run.update(dt, towerIn); towerIn.look = 0;
    for (const ev of run.events) {
      if (ev.kind === "hit") { fxs.burst({ at: ev.at, n: 7, size: 0.06, speed: 1.2, up: 1 }); CM.audio.bark(ev.mon.kind, "hit"); }
      else if (ev.kind === "die") { fxs.burst({ at: ev.at, layer: "fx:spark", n: 16, size: 0.07, speed: 1.6, up: 1.6 }); CM.audio.bark(ev.mon.kind, "die"); }
      else if (ev.kind === "wall") fxs.burst({ at: ev.at, layer: ev.layer, n: 4, size: 0.05, speed: 0.8, up: 0.6 });
      else if (ev.kind === "burst") { fxs.ring({ at: [ev.at[0], 0, ev.at[2]], to: 1.7 }); renderer.shake(0.3); try { CM.audio.play("slam", 0.4); } catch (er) { /* */ } }
      else if (ev.kind === "shoot") { try { CM.audio.play(ev.arrow ? "miss" : "spell", 0.25); } catch (er) { /* */ } }
      else if (ev.kind === "spell") { try { CM.audio.play("spell", 0.5); } catch (er) { /* */ } }
      else if (ev.kind === "hurt") { ui.tint("rgba(200,30,20,0.35)", 250); renderer.shake(0.25); }
      else if (ev.kind === "alert") CM.audio.bark(ev.mon.kind, "hit");
      else if (ev.kind === "monshoot") { try { CM.audio.play("miss", 0.3); } catch (er) { /* */ } }
      else if (ev.kind === "dodge") { try { CM.audio.play("miss", 0.2); } catch (er) { /* */ } }
      else if (ev.kind === "bossdown") { game.say(`${ev.mon.name} falls. The ladder up is free - and it left ${ev.item.name} (${CM.itemLabel(ev.item)}).`); renderer.shake(0.6); try { CM.audio.play("toll", 0.6); } catch (er) { /* */ } ui.refresh(); }
      else if (ev.kind === "kingspeaks") game.say(ev.line);
      else if (ev.kind === "teleport") { fxs.burst({ at: ev.from, layer: "fx:force", n: 18, size: 0.08, speed: 1.8, up: 1.2 }); fxs.burst({ at: ev.to, layer: "fx:force", n: 18, size: 0.08, speed: 1.4, up: 1.4 }); try { CM.audio.play("spell", 0.5, 0, 0.6); } catch (er) { /* */ } }
      else if (ev.kind === "kingcast") { try { CM.audio.play(ev.spell === "ring" ? "slam" : ev.spell === "summon" ? "elite" : "spell", 0.4); } catch (er) { /* */ } if (ev.spell === "curse") ui.tint("rgba(120,60,200,0.35)", 600); }
      else if (ev.kind === "kingdown") { game.say(ev.line); game.say(`On the dais: ${ev.item.name}.`); renderer.shake(1); ui.tint("rgba(200,180,255,0.5)", 900); try { CM.audio.play("toll", 0.8); } catch (er) { /* */ } ui.refresh(); }
      else if (ev.kind === "pickup") { try { CM.audio.play("coin", 0.4); } catch (er) { /* */ } }
      else if (ev.kind === "fell") { setTimeout(() => { if (game.towerRun === run) { game.leaveMageTower("fell"); ui.refresh(); } }, 900); }
    }
    run.events.length = 0;
    renderer.eye = [run.x, 0.5, run.z]; renderer.yaw = run.yaw; renderer.move = renderer.turn = null; renderer.bob = 0;
    renderer.light = 1; renderer.sky = null; renderer.lights = run.lights();
    stepAir(0);
    renderer.setSprites(run.sprites(now).concat(fxs.sprites(now)));
    renderer.frame(dt);
    ui.drawTowerHud(run);
    if ((towerMapT += dt) > 0.25) { towerMapT = 0; ui.drawAutomap(ui.$("#automap")); ui.renderActions(); }   // (and the ladder's buttons, when the hero comes to it)
  }
  // ---- the frame loop ----
  let last = performance.now(), fpsTime = 0, frames = 0, fps = 0, lastStep = 0, lastAuto = 0, lastAutoStep = 0;
  // what a frame costs: frames and the time spent in this function (the JavaScript's share), since CM.perf.reset();
  // CM.perf.hold keeps the step-down still while something is measured
  CM.perf = { frames: 0, cpu: 0, since: performance.now(), hold: false, reset() { this.frames = 0; this.cpu = 0; this.since = performance.now(); },
    read() { const s = (performance.now() - this.since) / 1000; return { fps: s > 0 ? Math.round(this.frames / s * 10) / 10 : 0, cpuMs: this.frames ? Math.round(this.cpu / this.frames * 100) / 100 : 0, frames: this.frames, scale: renderer.scale || 1, detail: CM.DETAIL_ORDER[detailNow()] }; } };
  function frame(now) {
    const t0 = performance.now();
    const dt = Math.min(0.1, Math.max(0, (now - last) / 1000));
    last = now;
    if (renderer.ok) {
      if (game.mode !== "title" && document.visibilityState !== "hidden" && !CM.perf.hold) autoScale(dt);
      renderer.resize();
      if (ui.splashOn) { const pads = navigator.getGamepads ? [...navigator.getGamepads()].filter(Boolean) : []; if (pads.some((p) => p.buttons.some((b) => b.pressed))) ui.leaveSplash(); }   // (a pad button goes on from the title card)
      if (game.mode === "tower") towerFrame(now, dt);
      else if (game.mode === "cave") caveFrame(now, dt);
      else if (game.mode === "title") {
        renderer.yaw += dt * 0.08;                                        // a slow look around
        renderer.light = 1; renderer.sky = null;
        renderer.setSprites([]);
        if (ui.rebindingPad) pollGamepad(now);
      } else {
        pollGamepad(now);
        if (game.mode === "explore" && !renderer.busy && now >= walkReady && held.size) {
          for (const code of held) if (act(code)) break;                  // walking while the key is held
        }
        if (ui.screen === "play" && !ui.dialogOpen()) game.tick(dt);    // the monsters move (not while you read a sheet or the pack); the run saves now and then
        if (game.mode === "combat") { const up = game.party.filter((h) => h.hp > 0); const worst = up.length ? Math.min(...up.map((h) => h.hp / h.max)) : 0; CM.music.setDanger(up.length < game.party.length ? 1 : worst < 0.5 ? 0.6 : 0); }   // the battle tune in layers
        if (game.film && game.film.playing && !renderer.busy && ui.screen === "play" && !ui.dialogOpen() && now >= fxs.holdUntil && now - game.film.last > 260 / game.film.speed) { game.film.last = now; game.filmStep(); }   // the film plays
        if (game.travel && game.mode === "explore" && !renderer.busy && now >= walkReady && ui.screen === "play" && !ui.dialogOpen() && now - lastStep > (game.settings.smooth ? 30 : 120)) { lastStep = now; game.travelStep(); }   // the party walks by itself
        if (game.mode === "combat" && game.combat && game.combat.auto && game.combat.waiting && ui.screen === "play" && !ui.dialogOpen() && now >= fxs.holdUntil && now - lastAuto > 420 / (CM.fxSpeed || 1)) { lastAuto = now; game.autoTurn(); }
        if (game.autoOn() && (ui.screen === "play" || ui.screen === "bag") && !renderer.busy && now >= walkReady && !ui.dialogOpen() && now >= fxs.holdUntil && now - lastAutoStep > (game.mode === "camp" ? 900 : game.settings.smooth ? 150 : 240)) {   // Automatic: a step a tick
          lastAutoStep = now;
          if (ui.screen === "bag") ui.show("play");
          const did = game.auto.step();
          if (ui.dialogOpen() && !ui.$("#dlg-over").classList.contains("on")) ui.closeDialogs();   // (what it read, answered, or opened in the town: out of the way)
          if (ui.screen === "bag") ui.show("play");
          if (!did || game.mode === "camp") ui.refresh();
        }
        renderer.light = game.lightFactor();
        renderer.sky = game.floor && CM.themeFor(game.floor.number).sky ? CM.sky(game) : null;
        renderer.perch = game.perch ? { x: game.perch.tower[0], y: game.perch.tower[1], h: CM.TOWER.h } : null;   // (on a gate tower's top)
        renderer.wet = renderer.sky && CM.weather(game) === "rain" ? 1 : 0;   // (the rain on the ground: 40-render.js)
        renderer.snow = renderer.sky && CM.snowLying(game) ? 1 : 0; renderer.mist = renderer.sky && (CM.weather(game) === "mist" || (game.floor.number === -1 && Math.abs(game.floor.pos[0] - CM.MAGE_TOWER.at[0]) + Math.abs(game.floor.pos[1] - CM.MAGE_TOWER.at[1]) <= 8)) ? 1 : 0;   // (and always about the Mage Tower)   // (snow lying, mist low: the seasons seen)
        { const night = Boolean(renderer.sky && renderer.sky.night) && (game.floor.number === 0 || game.floor.number === -1);   // the town's windows lit at dusk, and out at dawn: the floor's mesh made again
          if (night !== Boolean(renderer.night)) { renderer.night = night; if (renderer.ok && game.mode !== "title" && (game.floor.number === 0 || game.floor.number === -1)) renderer.setFloor(game.floor, CM.themeFor(game.floor.number)); } }
        renderer.lights = lightsNear(game.floor);
        stepAir(dt);
        const { out, hud } = sprites();
        renderer.setSprites(out);
        renderer.frame(dt);
        ui.drawHud(hud, (x, y, z) => renderer.project(x, y, z));
        if (dying.size && !game.foes.some((m) => dying.has(m))) dying.clear();
      }
      if (game.mode === "title") renderer.frame(dt);
    }
    frames++; fpsTime += dt; CM.perf.frames++; CM.perf.cpu += performance.now() - t0;
    if (fpsTime >= 0.5) { fps = Math.round(frames / fpsTime); frames = 0; fpsTime = 0; ui.$("#view .fps").textContent = `${fps} fps - v${CM.version} ${CM.built}`; }
    requestAnimationFrame(frame);
  }
  showDemo();
  requestAnimationFrame(frame);
});
