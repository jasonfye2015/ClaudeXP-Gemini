"use strict";
// Text as data: the words the player reads, keyed, so a translation is one file that sets CM.TEXT over this one.
// Only the newest screens are written through CM.t so far (the statistics, the link, installing, the gamepad); the
// older strings still live where they are used and move here as they are touched. No translation is shipped.
//
//   CM.t("stats.runs", { n: 12 })   ->  "12 expeditions"
CM.TEXT = {
  "stats.title": "Statistics",
  "stats.none": "No expedition has ended yet. The numbers begin with the first.",
  "stats.runs": "{n} expeditions, {crowns} crowned, {bottoms} to the bottom of the world, {fell} that fell",
  "stats.first": "The first set out {first}; the last ended {last}.",
  "stats.deepest": "Deepest: floor {n}.",
  "stats.totals": "{steps} steps, {fights} fights, {kills} slain, {fled} fled, {chests} chests opened.",
  "stats.bands": "Where parties fell",
  "stats.callings": "The callings, and how they fared",
  "stats.calling.row": "{n} took it, {crowns} crowned",
  "stats.spent": "Gold, and where it went",
  "stats.spent.total": "{n} gold spent in all",
  "stats.difficulty": "By difficulty",
  "stats.difficulty.row": "{n} runs, {crowns} crowned, best Ascension {a}",
  "stats.old": "({n} of these were read back from the Hall of Fame: no steps, fights or gold are known for them.)",
  "link.title": "A link came in",
  "link.save": "This link carries a save: the runs in its slots, its Hall of Fame and its settings. Import it, and they replace what this browser holds (Export first to keep what is here).",
  "link.film": "This link carries the film of a run. Watch it?",
  "link.bad": "The link's save couldn't be read.",
  "link.made": "A link to this save is in the box (and copied, where the browser allows). It opens the game with the save in it; nothing is stored anywhere but the link.",
  "link.film.made": "A link to this film is in the box. Anyone who opens it watches the run.",
  "install.button": "Install",
  "install.note": "Installed: the game opens from its own icon, and works without the network.",
  "pad.title": "Gamepad",
  "pad.note": "Change sets a button: press the one you want on the pad. The stick and the pad move, always.",
  "pad.press": "press a button...",
  "pad.help": "A gamepad works too: the stick or pad moves; the buttons as set below. On a touch screen, tap the view: the sides turn, the top walks, the bottom steps back.",
  "layout.handheld": "Handheld layout - thumb-sized buttons and larger text, as on a Steam Deck (Auto: by the screen's shape)",
};
CM.t = function (key, vars) {
  let s = CM.TEXT[key];
  if (s === undefined) return key;
  for (const [k, v] of Object.entries(vars || {})) s = s.split(`{${k}}`).join(typeof v === "number" ? v.toLocaleString() : String(v));
  return s;
};
