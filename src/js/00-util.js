"use strict";
// Claude and Magic - the shared bits: the version, a seeded random, saving in the browser, small maths.
// Everything the game is lives on window.CM, so the Timeline's tests can reach it with page.runJavaScript.
const CM = window.CM = { version: "__VERSION__", built: "__BUILT__" };

// a 32-bit number from any text (FNV-1a) - a seed word becomes a dungeon
CM.hashSeed = function (text) {
  let h = 2166136261 >>> 0;
  const s = String(text);
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  return h >>> 0;
};

// mulberry32: small and fast, and the same dungeon from the same seed in every browser
CM.Random = class {
  constructor(seed) { this.s = (typeof seed === "number" ? seed : CM.hashSeed(seed == null ? Math.random() : seed)) >>> 0; }
  next() {
    let t = (this.s = (this.s + 0x6D2B79F5) >>> 0);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  int(a, b) { return a + Math.floor(this.next() * (b - a + 1)); }        // both ends in, like Python's randint
  pick(list) { return list[Math.floor(this.next() * list.length)]; }
  chance(p) { return this.next() < p; }
  shuffle(list) {
    for (let i = list.length - 1; i > 0; i--) { const j = Math.floor(this.next() * (i + 1)); [list[i], list[j]] = [list[j], list[i]]; }
    return list;
  }
};

// localStorage, which may be missing, full or forbidden (a file opened in a strict browser): never let that stop the game
CM.store = {
  get(key, fallback) {
    try { const v = localStorage.getItem("claudemagic." + key); return v === null ? fallback : JSON.parse(v); } catch (e) { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem("claudemagic." + key, JSON.stringify(value)); return true; } catch (e) { return false; }
  },
  remove(key) { try { localStorage.removeItem("claudemagic." + key); } catch (e) { /* nothing to remove */ } },
};

CM.clamp = (v, a, b) => Math.max(a, Math.min(b, v));
CM.lerp = (a, b, t) => a + (b - a) * t;
CM.ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);      // in and out
CM.plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
CM.ordinal = (n) => `${n}${n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] || "th"}`;

// a seed you can say out loud: "ember-crypt-417"
CM.SEED_WORDS = ["ember", "crypt", "raven", "lantern", "sable", "hollow", "thorn", "cinder", "vesper", "moss", "iron", "gloam",
  "wyrm", "candle", "marrow", "grave", "frost", "amber", "shade", "stone", "echo", "rune", "oath", "dusk"];
CM.randomSeed = function () {
  const r = new CM.Random(Math.floor(Math.random() * 4294967296));
  return `${r.pick(CM.SEED_WORDS)}-${r.pick(CM.SEED_WORDS)}-${r.int(100, 999)}`;
};

CM.today = function () {                       // the Hall of Fame's date, the way the old game wrote it: m/d/yyyy
  const d = new Date();
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}/${d.getFullYear()}`;
};
