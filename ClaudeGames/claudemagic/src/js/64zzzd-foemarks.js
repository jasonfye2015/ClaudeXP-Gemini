"use strict";
// A foe's marks (v63.0, UPGRADE_PLAN_58.md): what the fight screen shows on a monster's row besides its name and its
// health - each ailment, its broken or whole part, what it carries, where it hides - as short tags with a mark and a
// fuller word for the tooltip, in one place, so the window (74-fight.js) and the tests read the same list.
//   CM.foeMarks(m) -> [{ id, mark, text, title }]
//   CM.REALTIME_MODES: the modes that draw in real time on their own canvas (the window fades between them and the floor)
{ CM.REALTIME_MODES = ["tower", "cave", "fortress", "ablo", "bros", "craft"];
  CM.foeMarks = (m) => { const out = [], add = (id, mark, text, title) => out.push({ id, mark, text, title }); if (!m) return out;
    if (m.asleep > 0) add("asleep", "z", `asleep ${m.asleep}`, `Asleep for ${m.asleep} more round${m.asleep === 1 ? "" : "s"}: a blow wakes it, and lands hard`);
    if (m.held > 0) add("held", "#", `held ${m.held}`, `Held fast for ${m.held} more round${m.held === 1 ? "" : "s"}: it can't act or move`);
    if (m.marked) add("marked", "x", "marked", "Marked: the next blow on it is surer");
    if (m.blind > 0) add("blind", "o", `blinded ${m.blind}`, `Blinded for ${m.blind} more round${m.blind === 1 ? "" : "s"}: its blows miss more`);
    if (m.burning > 0) add("burning", "*", `burning ${m.burning}`, `Burning: it takes fire each round for ${m.burning} more`);
    if (m.chilled > 0) add("chilled", "~", `chilled ${m.chilled}`, `Chilled for ${m.chilled} more round${m.chilled === 1 ? "" : "s"}: slower, and acts later`);
    if (m.warded > 0) add("warded", "+", "warded", "Warded: spells do it less harm");
    if (m.part) add("part", m.part.broken ? "/" : "|", m.part.broken ? `${m.part.name} broken` : `${m.part.name} ${m.part.hp}/${m.part.max}`, m.part.broken ? `Its ${m.part.name} is broken: it has lost what the ${m.part.name} did` : `Its ${m.part.name} can be struck on its own (${m.part.hp}/${m.part.max}); broken, it loses what the ${m.part.name} does`);
    if (m.gear && m.gear.weapon) add("carries", "!", `carries ${CM.itemName ? CM.itemName(m.gear.weapon) : m.gear.weapon.name || "a weapon"}${m.gear.offhand ? " and a shield" : ""}`, "What it carries falls when it does");
    if (m.under) add("under", "_", "under the floor", "Under the floor: it can't be struck till it comes up");
    return out; };
}
