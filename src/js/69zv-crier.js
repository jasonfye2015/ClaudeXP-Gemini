"use strict";
// The news board (v36.4, UPGRADE_PLAN_31.md): The Caer Duin Crier, a sheet a week pinned to the noticeboard, written from
// what the runs have done: the week's expeditions (their ends, the deepest), the fallen named, the records broken, the
// South Fields' prizes and best picking, the Gilded Joker's paid and wagered, the newest legends on the Row, the feats
// earned, the town's works raised. The week is the real calendar's; the sheets of the last eight weeks are kept.
//   game.crierWeek(); game.crier(week) -> {week, headline, items: [[head, text]]}; game.crierWeeks()
{ const G = CM.Game.prototype, wk = (d) => { const t = new Date(d.getTime()); t.setHours(0, 0, 0, 0); t.setDate(t.getDate() - ((t.getDay() + 6) % 7)); return t; };
  const parse = (s) => { const m = /(\d+)\/(\d+)\/(\d+)/.exec(String(s || "")); return m ? new Date(Number(m[3]), Number(m[1]) - 1, Number(m[2])) : null; };
  G.crierWeek = function (date) { const w = wk(date || new Date()); return `${w.getFullYear()}-${String(w.getMonth() + 1).padStart(2, "0")}-${String(w.getDate()).padStart(2, "0")}`; };
  G.crierWeeks = function () { const out = []; for (let i = 0; i < 8; i++) { const d = new Date(); d.setDate(d.getDate() - 7 * i); out.push(this.crierWeek(d)); } return out; };
  G.crier = function (week) { week = week || this.crierWeek(); const inWeek = (s) => { const d = parse(s); return d && this.crierWeek(d) === week; };
    const runs = (this.fame || []).filter((e) => inWeek(e.date)), items = [];
    if (runs.length) { const deep = runs.reduce((a, b) => ((b.floor || 0) > (a.floor || 0) ? b : a)), won = runs.filter((e) => e.won).length;
      items.push(["The week below", `${runs.length} expedition${runs.length === 1 ? "" : "s"} went down the shaft${won ? `, and ${won} came back with the crown` : ""}. The deepest reached floor ${deep.floor}${deep.party && deep.party.length ? `, ${deep.party.map((p) => String(p).split(" the ")[0]).join(", ")}` : ""}.`]); }
    const fell = (this.memorial || []).filter((m) => inWeek(m.date)).slice(-4); if (fell.length) items.push(["Remembered", `${fell.map((m) => `${m.name}${m.cls ? ` the ${m.cls}` : ""}${m.floor ? `, on floor ${m.floor}` : ""}`).join("; ")}. Candles at the temple.`]);
    const fameAll = this.fame || [], best = fameAll.reduce((m, e) => Math.max(m, e.floor || 0), 0), bestWeek = runs.reduce((m, e) => Math.max(m, e.floor || 0), 0);
    if (bestWeek && bestWeek === best && fameAll.length > runs.length) items.push(["A record", `Floor ${best}: no party from Caer Duin has been deeper.`]);
    const F = this.village && this.village.fields; if (F && (F.fairWins || F.best || F.marketGold)) items.push(["The South Fields", `${F.fairWins ? `${F.fairWins} blue ribbon${F.fairWins === 1 ? "" : "s"} at the Harvest Fair. ` : ""}${F.best ? `Best picking: a ${F.best}-star crop. ` : ""}${F.marketGold ? `The stall has sold ${F.marketGold.toLocaleString("en")} gold of produce.` : ""}`.trim()]);
    const K = this.casino ? this.cgStore() : null; if (K && K.n) { const paid = Object.values(K.paid || {}).reduce((a, b) => a + b, 0), wag = Object.values(K.wagered || {}).reduce((a, b) => a + b, 0); items.push(["At the Gilded Joker", `${K.n.toLocaleString("en")} games played; ${wag.toLocaleString("en")} wagered and ${paid.toLocaleString("en")} paid out. ${paid > wag ? "The house is not amused." : "The house thanks you."}`]); }
    const legends = this.legends ? this.legends().filter((l) => inWeek(l.date)) : []; if (legends.length) items.push(["Legends' Row", `${legends.map((l) => `${l.name} the ${l.cls}, level ${l.level}`).join("; ")} took a house on the Row.`]);
    const feats = Object.entries(this.achievements || {}).filter(([, a]) => inWeek(a.date)).map(([id]) => (CM.ACHIEVEMENTS[id] || { name: id }).name); if (feats.length) items.push(["Feats", `New plaques in the hall at the Tower's foot: ${feats.slice(0, 6).join(", ")}${feats.length > 6 ? `, and ${feats.length - 6} more` : ""}.`]);
    const works = this.works ? Object.entries(this.works()).filter(([, w]) => inWeek(w.day)).map(([id]) => CM.WORKS[id].name) : []; if (works.length) items.push(["The town", `${works.join("; ")}: done this week.`]);
    if (!items.length) items.push(["A quiet week", "Nothing to report but the weather, which was weather."]);
    const head = items.find(([h]) => h === "A record") ? `A record: floor ${best}!` : runs.some((e) => e.won) ? "The crown falls again!" : fell.length ? "The town mourns" : works.length ? "The town grows" : runs.length ? "Down the shaft and back" : "A quiet week on the hill";
    return { week, headline: head, items }; };
}
