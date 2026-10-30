"use strict";
// The story's word budget: how many words each chapter holds (13-lore.js, every telling), the whole, and how many
// long strings still live in the code rather than in 12-text.js or 13-lore.js (the door to a translation).
//
//   node tools/words.js
const fs = require("fs");
const path = require("path");
const { load } = require("./headless");

const CM = load();
const words = (t) => String(t || "").trim().split(/\s+/).filter(Boolean).length;
const byChapter = {};
for (const l of Object.values(CM.LORE_TEXT)) byChapter[l.chapter] = (byChapter[l.chapter] || 0) + l.tellings.reduce((n, t) => n + words(t), 0);
let total = 0;
console.log("The story of Caer Duin, by chapter (every telling counted):");
for (const [id, ch] of Object.entries(CM.CHAPTERS)) { const n = byChapter[id] || 0; total += n; console.log(`  ${ch.name.padEnd(26)} ${String(n).padStart(6)}`); }
const extra = [["the people (CM.PEOPLE)", CM.PEOPLE.reduce((n, p) => n + words([p.first, p.second, p.again, p.request.ask, p.request.wait, p.request.done, p.tale].join(" ")), 0)],
  ["the parleys (CM.PARLEY)", Object.values(CM.PARLEY).reduce((n, P) => n + words([P.open, P.good, P.bad, P.death, P.deathSpoken, P.after, P.gate && P.gate.text].concat(P.speak.flatMap((ex) => [ex.ask].concat(ex.replies.flatMap((r) => [r.say, r.back])))).join(" ")), 0)],
  ["the court and the king (CM.COURT, CM.REMIND)", CM.COURT.reduce((n, c) => n + words(c.line), 0) + CM.REMIND.reduce((n, r) => n + words([r.ask, r.say, r.back].join(" ")), 0) + words(CM.REMIND_END) + words(CM.REMIND_FAIL)],
  ["the village (villagers, the Patriarch's history, trainers)", Object.values(CM.VILLAGERS).reduce((n, v) => n + words([v.none].concat(v.greet).join(" ")), 0) + CM.PATRIARCH_HISTORY.reduce((n, t) => n + words(t), 0) + Object.values(CM.TRAINER_LINES).reduce((n, t) => n + words(t), 0)],
  ["the heroes (origins, banter, last words)", Object.values(CM.ORIGINS).reduce((n, o) => n + Object.values(o.lines).reduce((m, t) => m + words(t), 0), 0) + Object.values(CM.BANTER2).reduce((n, l) => n + l.reduce((m, t) => m + words(t), 0), 0) + Object.values(CM.LAST_WORDS.cls).concat(Object.values(CM.LAST_WORDS.origin), CM.LAST_WORDS.band).reduce((n, t) => n + words(t), 0)],
  ["the hermit's truths (CM.CHAPTER_TRUTH)", Object.values(CM.CHAPTER_TRUTH).reduce((n, t) => n + words(t), 0)]];
for (const [what, n] of extra) { total += n; console.log(`  ${what.padEnd(60)} ${String(n).padStart(6)}`); }
console.log(`  ${"in all".padEnd(26)} ${String(total).padStart(6)} words\n`);
// long strings still in the code: a rough count of literals of fifty characters or more, file by file
const SRC = path.join(__dirname, "..", "src", "js");
console.log("Long strings still in the code (fifty characters or more, outside 12-text.js and 13-lore.js):");
let strings = 0;
for (const f of fs.readdirSync(SRC).filter((x) => x.endsWith(".js") && !["12-text.js", "13-lore.js"].includes(x)).sort()) {
  const src = fs.readFileSync(path.join(SRC, f), "utf8");
  const n = (src.match(/"(?:[^"\\\n]|\\.){50,}"|`(?:[^`\\]|\\.){50,}`/g) || []).filter((s) => /[a-z]{3,} [a-z]{3,} [a-z]{3,}/.test(s)).length;
  if (n) { strings += n; console.log(`  ${f.padEnd(16)} ${String(n).padStart(4)}`); }
}
console.log(`  ${"in all".padEnd(16)} ${String(strings).padStart(4)}  (they move to 12-text.js as they are touched)`);
