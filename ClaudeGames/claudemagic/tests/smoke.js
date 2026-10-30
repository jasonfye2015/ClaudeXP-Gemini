"use strict";
// The built file in a real browser (Playwright's Chromium): it opens without an error, a run starts, the party
// walks and fights, the save is there after the page is loaded again, and Continue picks it up. Each theme draws.
//
//   node tests/smoke.js        (needs playwright: npm install)
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const assert = require("assert");

const ROOT = path.join(__dirname, "..");
const built = fs.readdirSync(path.join(ROOT, "game")).filter((f) => /^Claude and Magic v.*\.html$/.test(f)).sort().pop();
assert.ok(built, "no built game in game/ - run python build.py");
const url = "file://" + path.join(ROOT, "game", built);

(async () => {
  const browser = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto(url);
  await page.waitForFunction(() => window.CM && CM.game && CM.ui);
  await page.waitForTimeout(800);
  assert.ok(await page.$("#splash"), "the title card is up first");
  assert.match((await page.textContent("#splash h1")) || "", /Claude\s*and\s*Magic/);
  await page.keyboard.press("Space"); await page.waitForTimeout(800);
  assert.ok(!(await page.$("#splash")), "a key goes on from the title card");
  const title = await page.textContent("#title h1");
  assert.match(title || "", /Claude and Magic/);
  const r = await page.evaluate(() => {
    const g = CM.game;
    g.newGame("smoke-1");
    let moved = 0, fights = 0;
    for (let i = 0; i < 80; i++) {
      if (g.mode === "combat") { fights++; let guard = 0; while (g.mode === "combat" && guard++ < 100) g.combatRound("fight"); }
      if (g.mode !== "explore") break;
      if (g.move(0)) moved++; else g.turn(1);
    }
    g.saveRun();
    return { mode: g.mode, floor: g.floor.number, moved, fights, built: CM.built, version: CM.version, save: localStorage.getItem("claudemagic.run").length, ok: CM.renderer.ok };
  });
  assert.ok(r.moved > 5, "the party should have walked");
  assert.ok(r.ok, "WebGL should be up");
  assert.ok(r.save > 500 && r.save < 50000, `the save should be small (${r.save})`);
  assert.match(r.built, /^\d{4}-\d\d-\d\d$/);
  for (const look of ["pixel", "stone"]) {
    await page.evaluate((l) => { CM.game.settings.look = l; CM.game.saveSettings(); CM.game.emit("settings", CM.game.settings); }, look);
    await page.waitForTimeout(400);
  }
  await page.reload();
  await page.waitForFunction(() => window.CM && CM.game && CM.ui);
  await page.waitForTimeout(500);
  const again = await page.evaluate(() => { const g = CM.game; const can = g.canContinue(); const ok = can && g.continueRun(); return { can, ok, floor: g.floor && g.floor.number, mode: g.mode }; });
  assert.ok(again.can && again.ok, "Continue should work after a reload");
  assert.strictEqual(again.floor, r.floor);
  await page.waitForTimeout(600);
  // what a frame costs (tools/perf.js): the land at High, a room of torches, a fight with fireballs - in each look
  await page.addScriptTag({ content: fs.readFileSync(path.join(ROOT, "tools", "perf.js"), "utf8") });
  const perf = {};
  for (const look of ["pixel", "stone"]) {
    await page.evaluate((l) => { CM.game.settings.look = l; CM.game.emit("settings", CM.game.settings); }, look);
    await page.waitForTimeout(600);
    perf[look] = await page.evaluate(() => CM.perfScenes({ ms: 1500, detail: "high" }));
    for (const [scene, m] of Object.entries(perf[look])) assert.ok(m.frames > 0, `${look} ${scene}: frames are drawn`);
    assert.ok(perf[look].land.air > 0, `${look}: the air is there on the land at High`);
  }
  await browser.close();
  if (errors.length) { console.log("page errors:\n  " + errors.join("\n  ")); process.exit(1); }
  for (const [look, scenes] of Object.entries(perf)) console.log(`perf (${look}, software GL): ` + Object.entries(scenes).map(([k, m]) => `${k} ${m.fps} fps, ${m.cpuMs} ms script, ${m.lights} lights, ${m.air} motes`).join("; "));
  console.log(`smoke: ok (${built}, built ${r.built}; walked ${r.moved}, ${r.fights} fights, save ${r.save} chars, floor ${r.floor} continued)`);
})().catch((e) => { console.error(e); process.exit(1); });
