"use strict";
// The portals' own looks, the rules' side (v21.2, UPGRADE_PLAN_16.md): what each portal says when the party stands at
// it - where it goes, what's waiting there, who may pass (one hero or the whole party; fighters, casters, archers) -
// and which portal in the Wood is which court portal's twin. The pictures and the crossing: 76zzzs-portallooks.js.
{ const PC = CM.PORTALCOURT, PL = CM.PORTALLOOKS = {};
  // who may pass: [one hero alone?, the words]
  PL.WHO = { tower: [true, "one hero: a caster, or an archer with a bow"], cabin: [false, "the whole party"], claudeita: [true, "one hero: a caster"], fortress: [true, "one hero: a fighter"],
    glyph: [true, "one hero, any"], ablo: [true, "one hero, any"], gate: [true, "one hero, any"] };
  // the Wood's portals home, each the twin of one in the court
  PL.twinAt = (x, y) => { const at = { tower: CM.MAGE_PORTAL_LAND, cabin: CM.CABIN && CM.CABIN.portal, claudeita: CM.CLAUDEITA && CM.CLAUDEITA.portal, fortress: CM.FORTRESS && CM.FORTRESS.portal, glyph: CM.GLYPH_PORTAL };
    for (const [k, c] of Object.entries(at)) if (c && c[0] === x && c[1] === y) return k; return null; };
  // what's waiting beyond
  PL.status = (g, k) => { const v = g.village || {}; try {
    if (k === "tower") { const n = (g.tower && g.tower.cleared) || 0; return n >= (CM.TOWER_FLOORS || 40) ? "the King is gone; the tower is quiet" : `floor ${n + 1} of ${CM.TOWER_FLOORS || 40} next`; }
    if (k === "cabin") { const K = g.cards(), T = (CM.CARD_TABLES || []).find((t) => !K.beaten[t.id] && (!g.cardTableOpen || g.cardTableOpen(t))); return T ? `next at the table: ${T.name}` : "every game at the table won"; }
    if (k === "claudeita") { const K = v.cave || {}; return K.runs ? `deepest so far ${K.deepest || 0}, ${K.bosses || 0} of the bosses undone` : "not yet entered"; }
    if (k === "fortress") { const n = (g.fort && g.fort.cleared) || 0; return n >= (CM.FORT_FLOORS || 20) ? "the Iron Marshal is gone" : `floor ${n + 1} of ${CM.FORT_FLOORS || 20} next`; }
    if (k === "glyph") { const S = v.glyph || {}; return S.boss ? "the Unwritten is undone" : `${Object.keys(S.paid || {}).length} of 20 levels paid${S.best ? `, deepest ${S.best}` : ""}`; }
    if (k === "ablo") { const A = v.ablo || {}, deep = Math.max(0, ...Object.values(A.heroes || {}).map((p) => p.maxDepth || 0)); return A.visits ? `${A.visits} visit${A.visits === 1 ? "" : "s"}, deepest level ${deep}` : "Haven waits"; }
    if (k === "gate") { const K = v.craft || {}; return K.visits ? `${K.visits} visit${K.visits === 1 ? "" : "s"} to the island` : "the island waits"; }
  } catch (e) { /* a store not made yet */ } return ""; };
  // the words for the hint line: standing at a court portal or a twin
  PL.words = (g, x, y) => { const fl = g.floor; if (!fl) return ""; let k = null, home = false;
    if (fl.number === 0) { const P = PC.portalAt(x, y); k = P && P[0]; } else if (fl.number === -1) { k = PL.twinAt(x, y); home = Boolean(k); }
    if (!k) return ""; const P = PC.byKey[k], W = PL.WHO[k];
    return home ? `The portal home to the Portal Court - ${P[2]}'s twin. Space steps through.` : `${P[2]}: ${PL.status(g, k)}. Who may pass: ${W[1]}. Space steps through.`; };
  // the crossing: every court portal and its twin tells the window which it was
  { const G = CM.Game.prototype, up0 = G.usePortal; G.usePortal = function (t) { const k = t && PC.keyOfTo[t.to]; const out = up0.call(this, t); if (out && k && t.to !== "town") this.emit && this.emit("portalfx", k); return out; }; }
}
