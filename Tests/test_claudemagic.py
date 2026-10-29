"""Claude and Magic, the one-file game (ClaudeGames/claudemagic/game), driven in Qt WebEngine offscreen on a scratch
profile - the real saves are never touched: the built file is current with its source; every floor is solvable and
stocked, and the same from the same seed; the rules are the old game's (a fight ends, the party learns, a chest
opens, the camp trades and rests, the run ends in the Hall of Fame); a run saves and comes back after the page
reloads, and travels as text; the first-person view draws (WebGL, composited in software here); and the Timeline's
window opens, hands the page the old Python game's saves once, and closes."""
import importlib.util
import json
import os

import support

os.environ["CLAUDE_STANDALONE_DATA"] = str(support.scratch("standalone data"))
os.environ["CLAUDE_STANDALONE_STORAGE"] = str(support.scratch("empty Local Storage"))
support.qapp()
from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings  # noqa: E402
from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: E402
from claudecore import standalone as S  # noqa: E402

S.install()
import claudemagic as M  # noqa: E402

GAME = support.TIMELINE / "ClaudeGames" / "claudemagic"
SEED = "ember-crypt-417"
_page = {}


def build_module():
    spec = importlib.util.spec_from_file_location("claudemagic_build", GAME / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Page(QWebEnginePage):
    def __init__(self, *a):
        super().__init__(*a)
        self.said = []

    def javaScriptConsoleMessage(self, level, msg, line, source):
        self.said.append(f"{str(level).split('.')[-1]}: {msg} ({line})")


def page():
    """The game, open in one offscreen web view on a scratch profile (made once; the tests share it)."""
    if "view" not in _page:
        profile = QWebEngineProfile("claudemagic-test", support.qapp())
        store = support.scratch("claudemagic profile")
        profile.setPersistentStoragePath(str(store / "storage"))
        profile.setCachePath(str(store / "cache"))
        view = QWebEngineView()
        pg = Page(profile, view)
        pg.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        view.setPage(pg)
        view.resize(1000, 700)
        view.show()
        _page["view"], _page["page"] = view, pg
        load(view)
    return _page["page"]


def load(view, reload=False):
    done = []
    view.loadFinished.connect(lambda ok: done.append(ok))
    if reload:
        view.reload()
    else:
        view.load(QUrl.fromLocalFile(str(M.game_file())))
    assert support.pump(30, until=lambda: done), "the page didn't load"
    assert support.pump(10, until=lambda: ask("typeof CM !== 'undefined' && !!CM.game")), "the game didn't start"
    support.pump(0.4)


def ask(expr, timeout=20):
    """What a JavaScript expression comes to, as Python; a JavaScript error raises."""
    box = []
    code = ("(function(){ try { return JSON.stringify({v: (" + expr + ")}); }"
            " catch (e) { return JSON.stringify({error: String(e && e.stack || e)}); } })()")
    page().runJavaScript(code, lambda r: box.append(r))
    assert support.pump(timeout, until=lambda: box), f"no answer from the page for: {expr[:80]}"
    got = json.loads(box[0]) if box[0] else {}
    assert "error" not in got, f"JavaScript error: {got['error']}"
    return got.get("v")


def run(code, timeout=20):
    """Run JavaScript statements (wrapped in a function) and wait for them."""
    return ask("(function(){ " + code + " ; return true; })()", timeout)


def test_the_build_is_current():
    """The built file in game/ matches the source in src/ (python build.py redoes it), and stands alone"""
    b = build_module()
    built = M.game_file()
    assert built is not None and built.name == b.NAME.format(b.VERSION), built
    text = built.read_text(encoding="utf-8")
    assert text == b.build_text(), "game/Claude and Magic v*.html is out of date: run  python build.py  in ClaudeGames/claudemagic"
    assert "<script src" not in text and "<link rel=\"stylesheet\"" not in text, "the one file leans on another"
    assert f"v{b.VERSION}" in text and "__VERSION__" not in text


def test_floors_are_solvable_and_stocked():
    """Every floor, four seeds deep: the ladder (or the Lich King) can be reached - keys found before their doors,
    levers before their gates, no pit in the only way; every room can be walked to; the furniture sits where it
    should (doors in doorways, teleporters in pairs, nothing two things deep, nothing to fall into on the last floor);
    chests and monsters at least as many as the depth says; the maze grows with the depth; and the same seed lays
    the same floor"""
    rows = ask("""(function(){ const out = [];
      for (const seed of ["ember-crypt-417", "iron-oath-9", "x", "candle-echo-461"]) for (let n = 1; n <= 20; n++) {
        const f = CM.makeFloor(n, seed), t = Object.values(f.things), F = Object.entries(f.features);
        const grid = f.grid, open = (x, y) => CM.inBounds(f, x, y) && (grid[y][x] === 0 || (f.features[x + ',' + y] || {}).type === 'secret');
        const walk = CM.distances(grid, f.pos, open);
        const roomsReached = f.rooms.every(r => { for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) if (!walk.has(x + ',' + y)) return false; return true; });
        const problems = [];
        for (const [k, ft] of F) {
          const [x, y] = k.split(',').map(Number);
          if (f.things[k]) problems.push(ft.type + ' on a thing at ' + k);
          if (ft.type === 'door' || ft.type === 'gate') {
            const ns = grid[y - 1][x] === 0 && grid[y + 1][x] === 0 && grid[y][x - 1] === 1 && grid[y][x + 1] === 1;
            const ew = grid[y][x - 1] === 0 && grid[y][x + 1] === 0 && grid[y - 1][x] === 1 && grid[y + 1][x] === 1;
            if (!(ns || ew)) problems.push(ft.type + ' not in a doorway at ' + k);
          }
          if (ft.type === 'teleporter') { const to = f.features[ft.to[0] + ',' + ft.to[1]]; if (!to || to.type !== 'teleporter' || to.to[0] !== x || to.to[1] !== y) problems.push('teleporter unpaired at ' + k); }
          if (ft.type === 'lever' && !(f.features[ft.gate] && f.features[ft.gate].type === 'gate')) problems.push('lever to nothing at ' + k);
          if ((ft.type === 'lever' || ft.type === 'carving') && grid[y + CM.DIRS[ft.face][1]][x + CM.DIRS[ft.face][0]] !== 1) problems.push(ft.type + ' not on a wall at ' + k);
          if ((ft.type === 'pit' || ft.type === 'trapdoor') && (n === 20 || (x === f.pos[0] && y === f.pos[1]))) problems.push(ft.type + ' where it must not be at ' + k);
          if (ft.type === 'secret' && grid[y][x] !== 1) problems.push('secret door in the open at ' + k);
        }
        const locked = F.filter(([, ft]) => ft.type === 'door' && ft.locked).length, keys = t.filter(x => x.type === 'key').length;
        if (keys < locked) problems.push('fewer keys than locked doors');
        out.push({n, seed, size: grid.length, ok: CM.solvable(f), chests: t.filter(x => x.type === 'chest').length,
          groups: t.filter(x => x.type === 'monsters').length, goal: t.some(x => x.type === (n === 20 ? 'boss' : 'ladder')),
          start: grid[f.pos[1]][f.pos[0]] === 0 && (n === 1 || (f.things[f.pos[0] + ',' + f.pos[1]] || {}).type === 'stairs_up'),
          roomsReached, problems, carving: F.some(([, ft]) => ft.type === 'carving' && ft.text === n - 1),
          same: JSON.stringify(CM.makeFloor(n, seed)) === JSON.stringify(f)});
      }
      out.push({differ: JSON.stringify(CM.makeFloor(1, 'a').grid) !== JSON.stringify(CM.makeFloor(1, 'b').grid)});
      return out; })()""")
    assert rows.pop()["differ"], "two seeds gave the same floor"
    kinds = {"door": 0, "secret": 0, "pit": 0, "trapdoor": 0, "teleporter": 0, "spinner": 0, "fountain": 0, "altar": 0, "lever": 0}
    for r in rows:
        where = f"floor {r['n']} of {r['seed']}"
        assert r["ok"] and r["goal"] and r["start"], f"{where} can't be finished"
        assert r["roomsReached"], f"{where} has a room no one can walk to"
        assert not r["problems"], (where, r["problems"])
        assert r["same"], f"{where} isn't the same twice"
        assert r["carving"], f"{where} doesn't tell its part of the story"
        assert r["size"] == min(17 + (r["n"] // 4) * 2, 27), where
        assert r["chests"] >= 3 + r["n"] // 4 and r["groups"] >= 5 + r["n"] // 2, (where, r["chests"], r["groups"])
    totals = ask("""(function(){ const c = {}; for (const seed of ["ember-crypt-417", "iron-oath-9", "x", "candle-echo-461"]) for (let n = 1; n <= 20; n++)
      for (const f of Object.values(CM.makeFloor(n, seed).features)) c[f.type] = (c[f.type] || 0) + 1; return c; })()""")
    for kind in kinds:
        assert totals.get(kind, 0) > 0, f"no {kind} on eighty floors: {totals}"


def test_the_rules():
    """The old game's rules: a fight ends in victory or flight, the party learns and levels, a chest gives up its
    gold, the ladder under floor 5 leads to the camp, the merchant sells and buys, gear equips, resting and raising
    cost what they did, and the whole party falling ends the run in the Hall of Fame"""
    got = ask(f"""(function(){{ const g = CM.game, out = {{}};
      CM.store.remove('run'); CM.store.remove('fame'); g.fame = []; g.lastRun = null;
      g.newGame({json.dumps(SEED)}); g.rnd = new CM.Random(7);
      const fl = g.floor, foes = Object.entries(fl.things).filter(([k, t]) => t.type === 'monsters').map(([k]) => k.split(',').map(Number));
      let best = null, bd = 1e9;
      for (const [x, y] of foes) {{ const d = Math.abs(x - 1) + Math.abs(y - 1); if (d < bd) {{ bd = d; best = [x, y]; }} }}
      for (let f = 0; f < 4; f++) {{ const [dx, dy] = CM.DIRS[f], px = best[0] - dx, py = best[1] - dy;
        if (fl.grid[py] && fl.grid[py][px] === 0) {{ fl.pos = [px, py]; fl.facing = f; break; }} }}
      const goldBefore = g.gold;
      g.move(0);
      out.combatStarted = g.mode === 'combat' && g.foes.length > 0;
      let rounds = 0;
      while (g.mode === 'combat' && rounds < 60) {{ g.combatRound('fight'); rounds++; }}
      out.rounds = rounds; out.modeAfter = g.mode;
      out.learned = g.mode === 'explore' ? (g.gold > goldBefore && g.alive().every(m => m.xp > 0)) : null;
      for (let i = 0; i < 12; i++) {{ g.foes = CM.monsterGroup(6, g.rnd); g.foeKey = '0,0'; g.mode = 'combat'; g.wonFight(); }}
      out.levelled = g.party.some(m => m.level > 1) && g.party.every(m => m.hp === m.max);
      const chest = Object.entries(g.floor.things).find(([k, t]) => t.type === 'chest');
      g.floor.pos = chest[0].split(',').map(Number); g.mode = 'explore';
      const bag = g.bag.length, gold = g.gold; g.use();
      out.chest = g.gold > gold && g.bag.length > bag && !(chest[0] in g.floor.things);
      g.floor = CM.makeFloor(5, g.seed);
      const ladder = Object.entries(g.floor.things).find(([k, t]) => t.type === 'ladder');
      g.floor.pos = ladder[0].split(',').map(Number); g.use();
      out.camp = g.mode === 'camp';
      g.openBag(true); out.stock = g.stock.length;
      out.lightSold = g.stock.some(i => i.kind === 'torch') && g.stock.some(i => i.kind === 'lantern');
      g.gold = 500;
      const potion = g.stock.findIndex(i => i.kind === 'heal');
      out.bought = g.buy(potion) === '' && g.gold === 480 && g.bag[g.bag.length - 1].kind === 'heal';
      out.poor = g.buy(g.stock.findIndex(i => i.kind === 'revive')) === '' && g.gold === 360;
      g.gold = 10; out.cantAfford = g.buy(0) === "You can't afford that.";
      g.gold = 500;
      const sword = {{name: 'Long Sword', kind: 'weapon', power: 9, value: 240}}; g.bag.push(sword);
      out.equipped = g.give(g.bag.length - 1, 0) === '' && g.party[0].weapon === sword && g.bag.some(i => i.name === 'Club');
      const n = g.bag.length; out.sold = g.sell(g.bag.length - 1) === '' && g.bag.length === n - 1 && g.gold === 502;
      g.closeBag();
      g.party[0].hp = 1; g.party[2].mp = 0; g.rest(); out.rested = g.gold === 482 && g.party[0].hp === g.party[0].max && g.party[2].mp === g.party[2].maxmp;
      g.party[1].hp = 0; const lvl = g.party[1].level;
      g.gold = 100 * lvl - 1; g.raiseDead(); out.tooPoorToRaise = g.party[1].hp === 0 && g.gold === 100 * lvl - 1;
      g.gold = 2000; g.raiseDead(); out.raised = g.party[1].hp === g.party[1].max && g.gold === 2000 - 100 * lvl;
      g.leaveCamp(); out.deeper = g.floor.number === 6 && g.mode === 'explore' && g.stock === null;
      g.endRun(false);
      out.over = g.mode === 'title' && g.fame.length === 1 && g.fame[0].floor === 6 && !g.fame[0].won && CM.store.get('run', null) === null && CM.store.get('fame', []).length === 1;
      return out; }})()""")
    assert got["combatStarted"], got
    assert got["modeAfter"] in ("explore", "title") and got["rounds"] < 60, got
    assert got["learned"] in (True, None), got
    for key in ("levelled", "chest", "camp", "bought", "poor", "cantAfford", "equipped", "sold", "rested", "tooPoorToRaise", "raised",
                "deeper", "over"):
        assert got[key] is True, (key, got)
    assert got["stock"] == 11 and got["lightSold"], got


PARSE = """
  CM.testFloor = function (n, rows) {
    const size = Math.max(rows.length, ...rows.map(r => r.length));
    const f = { number: n, grid: [], pos: [1, 1], facing: 1, things: {}, features: {}, dark: [], seen: [], rooms: [] };
    for (let y = 0; y < size; y++) f.grid.push(new Array(size).fill(1));
    let tele = null, gate = null, lever = null;
    rows.forEach((row, y) => [...row].forEach((c, x) => {
      const k = x + ',' + y;
      if (c === '#') return;
      f.grid[y][x] = 0;
      if (c === 'X') f.pos = [x, y];
      else if (c === 'D') f.features[k] = { type: 'door', open: false, locked: false };
      else if (c === 'L') f.features[k] = { type: 'door', open: false, locked: true };
      else if (c === 'S') { f.grid[y][x] = 1; f.features[k] = { type: 'secret', found: false }; }
      else if (c === 'P') f.features[k] = { type: 'pit' };
      else if (c === 'T') f.features[k] = { type: 'trapdoor', known: false };
      else if (c === 'O') { if (tele) { f.features[k] = { type: 'teleporter', to: tele, known: false }; f.features[tele[0] + ',' + tele[1]].to = [x, y]; } else { tele = [x, y]; f.features[k] = { type: 'teleporter', to: null, known: false }; } }
      else if (c === '@') f.features[k] = { type: 'spinner', known: false };
      else if (c === 'F') f.features[k] = { type: 'fountain', kind: 'heal', used: false, known: false };
      else if (c === 'Q') f.features[k] = { type: 'fountain', kind: 'poison', used: false, known: false };
      else if (c === 'A') f.features[k] = { type: 'altar', used: false };
      else if (c === 'G') { f.features[k] = { type: 'gate', open: false }; gate = k; }
      else if (c === '/') { f.features[k] = { type: 'lever', face: 0, gate: null, pulled: false }; lever = k; }
      else if (c === 'W') f.features[k] = { type: 'carving', face: 0, text: n - 1, read: false };
      else if (c === '~') f.dark.push(k);
      else if (c === 'K') f.things[k] = { type: 'key' };
      else if (c === 'C') f.things[k] = { type: 'chest', gold: 10, items: [] };
      else if (c === '>') f.things[k] = { type: 'ladder' };
      else if (c === '<') f.things[k] = { type: 'stairs_up' };
      else if (c === 'M') f.things[k] = { type: 'monsters', group: CM.monsterGroup(n, new CM.Random(3)) };
    }));
    if (lever && gate) f.features[lever].gate = gate;
    return f;
  };
  CM.useFloor = function (g, f) { g.floors[f.number] = f; g.floor = f; g.mode = 'explore'; g.look(); g.emit('floor', f); return f; };
"""


def test_the_dungeon():
    """The dungeon's furniture, on hand-made floors: a door opens when walked into and a locked one wants the key
    picked up on the way; a secret door is found by searching the wall; a pit and a trapdoor drop the party a floor,
    bruised, and the floor above is kept to climb back to; a teleporter moves them, a spinner turns them; a fountain
    and an altar give once; a lever raises its gate; the stairs lead back up (and the camp both ways); a torch burns
    down and a fresh one is lit, and in the dark the automap stops; monsters that see you come for you"""
    run(PARSE)
    got = ask(f"""(function(){{ const g = CM.game, out = {{}}, lore = [];
      g.on('lore', (t) => lore.push(t));
      CM.store.remove('run'); g.lastRun = null; g.newGame({json.dumps(SEED)}); g.rnd = new CM.Random(7);
      const hp = () => g.party.map(m => m.hp);
      // a door, and a locked one with its key
      let f = CM.useFloor(g, CM.testFloor(2, ["########", "#X.DKL>#", "########"]));
      g.move(0); g.move(0); out.doorStays = g.floor.pos[0] === 2 && f.features['3,1'].open === true;
      g.move(0); g.move(0); out.key = g.floor.pos[0] === 4 && g.bag.some(i => i.kind === 'key') && !f.things['4,1'];
      g.move(0); out.unlocked = g.floor.pos[0] === 4 && f.features['5,1'].open && !f.features['5,1'].locked && !g.bag.some(i => i.kind === 'key');
      g.move(0); g.move(0); out.through = g.floor.pos[0] === 6;
      // no key: the door stays shut
      f = CM.useFloor(g, CM.testFloor(2, ["#####", "#XL.#", "#####"]));
      g.move(0); out.lockedStays = g.floor.pos[0] === 1 && !f.features['2,1'].open && g.messages[g.messages.length - 1].includes('locked');
      // a secret door
      f = CM.useFloor(g, CM.testFloor(2, ["#####", "#XS.#", "#####"]));
      g.use(); out.secret = f.features['2,1'].found && f.grid[1][2] === 0; g.move(0); out.secretWalked = g.floor.pos[0] === 2;
      g.turn(-1); g.use(); out.searchNothing = g.messages[g.messages.length - 1].includes('find nothing'); g.turn(1);
      // a pit: down a floor, bruised, the floor above kept
      f = CM.useFloor(g, CM.testFloor(2, ["####", "#XP#", "####"]));
      const before = hp();
      g.move(0);
      out.fell = g.floor.number === 3 && g.floors[2] === f && g.floors[3] && CM.passable(g.floor, g.floor.pos[0], g.floor.pos[1])
        && hp().every((h, i) => h < before[i] && h >= 1) && g.mode === 'explore';
      f = CM.useFloor(g, CM.testFloor(2, ["####", "#XT#", "####"]));
      g.move(0); out.trapdoor = g.floor.number === 3 && f.features['2,1'].known;
      // a teleporter and a spinner
      f = CM.useFloor(g, CM.testFloor(2, ["#########", "#XO...O.#", "#########"]));
      g.move(0); out.teleported = g.floor.pos[0] === 6 && f.features['2,1'].known && f.features['6,1'].known;
      f = CM.useFloor(g, CM.testFloor(2, ["#####", "#X@.#", "#####"]));
      g.move(0); out.spun = g.floor.pos[0] === 2 && g.floor.facing !== 1 && f.features['2,1'].known;
      // a fountain and an altar, once each
      f = CM.useFloor(g, CM.testFloor(2, ["#####", "#XFA#", "#####"]));
      for (const m of g.party) m.hp = 1;
      g.move(0); g.use(); out.drank = g.party.every(m => m.hp === m.max) && f.features['2,1'].used;
      for (const m of g.party) m.hp = 1;
      g.use(); out.dry = g.party.every(m => m.hp === 1) && g.messages[g.messages.length - 1].includes('dry');
      g.move(0); g.use(); out.knelt = g.party.every(m => m.hp > 1 && m.hp < m.max) && f.features['3,1'].used;
      f = CM.useFloor(g, CM.testFloor(2, ["####", "#XQ#", "####"]));
      for (const m of g.party) m.hp = m.max;
      g.move(0); g.use(); out.poisoned = g.party.every(m => m.hp < m.max && m.hp >= 1);
      // a lever and its gate
      f = CM.useFloor(g, CM.testFloor(2, ["#######", "#X/.G>#", "#######"]));
      g.move(0); g.move(0); g.move(0); out.gateStops = g.floor.pos[0] === 3 && g.messages[g.messages.length - 1].includes('portcullis');
      g.move(2); g.turn(1); g.use();                                                   // (back on the lever's square, facing the wrong wall)
      out.wrongWall = g.floor.pos[0] === 2 && !f.features['2,1'].pulled && g.messages[g.messages.length - 1].includes('find nothing');
      g.turn(1); g.turn(1); g.use(); out.pulled = f.features['2,1'].pulled && f.features['4,1'].open;
      g.turn(1); g.move(0); g.move(0); g.move(0); out.throughGate = g.floor.pos[0] === 5;
      // a carving
      f = CM.useFloor(g, CM.testFloor(2, ["####", "#XW#", "####"]));
      g.move(0); g.turn(-1); g.use(); out.read = lore.length === 1 && lore[0] === CM.LORE[1] && f.features['2,1'].read;
      // the stairs: up to a floor kept as it was, and down again to the very square
      f = CM.useFloor(g, CM.testFloor(2, ["######", "#X<.D#", "######"]));
      g.move(0); g.move(0); g.move(0); out.doorOpened = f.features['4,1'].open;
      g.floor.pos = [2, 1]; g.use();
      out.climbed = g.floor.number === 1 && (g.floor.things[g.floor.pos[0] + ',' + g.floor.pos[1]] || {{}}).type === 'ladder' && g.floors[2] === f;
      g.use(); out.downAgain = g.floor === f && g.floor.pos[0] === 2 && f.features['4,1'].open;
      // the camp, both ways
      g.floors = {{}}; f = CM.useFloor(g, CM.testFloor(5, ["####", "#X>#", "####"]));
      g.move(0); g.use(); out.camp = g.mode === 'camp' && g.floor === f;
      g.backUp(); out.backUp = g.mode === 'explore' && g.floor === f && g.floor.pos[0] === 2;
      g.use(); g.leaveCamp(); out.deeper = g.floor.number === 6 && g.mode === 'explore';
      g.climbUp(); out.campAgain = g.mode === 'camp' && g.floor === f;
      // light: a torch burns down and a fresh one is lit; then the dark
      f = CM.useFloor(g, CM.testFloor(6, ["##########", "#X.......#", "##########"]));
      g.bag = g.bag.filter(i => i.kind !== 'torch'); g.bag.push(CM.torch()); g.light = {{ kind: 'torch', left: 2 }};
      g.move(0); g.move(0); out.relit = g.light.kind === 'torch' && g.light.left === CM.TORCH_STEPS && !g.bag.some(i => i.kind === 'torch');
      g.light = {{ kind: 'torch', left: 1 }}; g.move(0);
      out.dark = g.light.kind === null && g.lightFactor() < 0.3 && g.messages[g.messages.length - 1].includes('gutters');
      f.seen = []; g.look(); out.darkMap = f.seen.length <= 9 && !f.seen.some(([x]) => x > g.floor.pos[0] + 1);
      g.light = {{ kind: 'lantern', left: 0 }}; f.seen = []; g.look(); out.lanternMap = f.seen.some(([x]) => x > g.floor.pos[0] + 1) && g.lightFactor() > 1;
      f = CM.useFloor(g, CM.testFloor(6, ["########", "#X~~~~.#", "########"]));
      g.move(0); out.magicDark = g.inDark() && g.lightFactor() < 0.5; f.seen = []; g.look(); out.magicDarkMap = f.seen.length === 1;
      g.light = {{ kind: 'torch', left: 100 }};
      // monsters that see you come for you
      f = CM.useFloor(g, CM.testFloor(3, ["##########", "#X.....M.#", "##########"]));
      g.tick(1.2); const after = Object.keys(f.things)[0]; out.crept = after === '6,1' && f.things[after].anim !== undefined;
      let ticks = 0; while (g.mode === 'explore' && ticks < 12) {{ g.tick(1.2); ticks++; }}
      out.caught = g.mode === 'combat' && g.messages[g.messages.length - 1].includes('out of the dark') && ticks <= 6;
      // and the save knows the floors and the light
      g.mode = 'explore'; g.saveRun(); const saved = CM.store.get('run');
      out.saved = Object.keys(saved.floors).length >= 2 && saved.light.kind === 'torch' && saved.floor.number === 3;
      return out; }})()""")
    for key, value in got.items():
        assert value is True, (key, got)


def test_a_run_saves_and_comes_back():
    """A run saves as it goes: after the page reloads it's there to continue, where it was; and it travels as text"""
    run(f"""const g = CM.game; CM.store.remove('run'); g.lastRun = null; g.newGame({json.dumps(SEED)});
      const open = []; g.floor.grid.forEach((row, y) => row.forEach((c, x) => {{ if (!c) open.push([x, y]); }}));
      g.floor.pos = open[Math.floor(open.length / 2)]; g.floor.facing = 3; g.gold = 777; g.look(); g.saveRun()""")
    pos = ask("CM.game.floor.pos")
    support.pump(0.3)
    load(_page["view"], reload=True)
    assert ask("CM.game.mode") == "title" and ask("CM.game.canContinue()"), "the run wasn't there after a reload"
    assert ask("CM.game.lastRun.gold") == 777 and ask("CM.game.lastRun.seed") == SEED
    assert ask("CM.game.continueRun()") and ask("CM.game.mode") == "explore"
    assert ask("CM.game.floor.pos") == pos and ask("CM.game.floor.facing") == 3 and ask("CM.game.gold") == 777
    assert ask("CM.game.floor.seen.length") > 0, "what the party had seen was forgotten"
    assert ask("CM.game.floors[1] === CM.game.floor && CM.game.light.kind === 'torch'"), "the floors walked, or the light, were forgotten"
    text = ask("CM.game.exportText()")
    assert json.loads(text)["run"]["gold"] == 777
    assert run("CM.store.remove('run'); CM.game.lastRun = null") and not ask("CM.game.canContinue()")
    assert ask(f"CM.game.importText({json.dumps(text)})") == "" and ask("CM.game.canContinue()")
    assert "isn't a Claude and Magic save" in ask("CM.game.importText('{\"game\": \"other\"}')")


def test_the_view_draws():
    """The first-person view draws with WebGL: the floor's mesh is built, the context holds, and the picture isn't
    black - in the dungeon and behind the title"""
    support.pump(0.6)
    got = ask("""(function(){ const r = CM.renderer; const w = r.canvas.width, h = r.canvas.height;
      return {ok: r.ok, error: r.error, lost: r.gl.isContextLost(), count: r.staticCount, w, h,
        floor: r.pixel(Math.floor(w / 2), Math.floor(h * 0.85)), ceiling: r.pixel(Math.floor(w / 2), Math.floor(h * 0.12))}; })()""")
    assert got["ok"] and not got["lost"], got
    assert got["count"] > 100 and got["w"] > 100 and got["h"] > 100, got
    assert sum(got["floor"][:3]) > 30 and sum(got["ceiling"][:3]) > 10, f"the view is black: {got}"
    assert got["floor"] != got["ceiling"], got
    run("CM.game.setMode('title')")
    support.pump(0.6)
    px = ask("CM.renderer.pixel(Math.floor(CM.renderer.canvas.width / 2), Math.floor(CM.renderer.canvas.height * 0.85))")
    assert sum(px[:3]) > 10 and not ask("CM.renderer.gl.isContextLost()"), f"nothing behind the title: {px}"
    said = [s for s in page().said if "Error" in s or "error" in s]
    assert not said, f"the page's console: {said[:5]}"


def test_the_window_and_the_old_saves():
    """The Timeline's window: the page opens on the shared profile (here a scratch one), learns the player's name,
    takes the old Python game's Hall of Fame and run once (the files are kept as *.imported.json), and closes"""
    from PySide6.QtWidgets import QApplication
    caught = support.catch_errors()
    saves = support.scratch("claudemagic old saves")
    M.SAVES = M.PROFILE_DIR = saves
    M.RUN_FILE, M.FAME_FILE = saves / "run.json", saves / "hall_of_fame.json"
    M._profile = None
    fame = [{"name": "Jason", "floor": 7, "gold": 1200, "won": False, "date": "10/18/2026"},
            {"name": "Jason", "floor": 3, "gold": 300, "won": False, "date": "10/17/2026"}]
    old_run = {"party": json.loads(ask("JSON.stringify(CM.newParty())")), "bag": [], "gold": 55,
               "floor": json.loads(ask(f"JSON.stringify(CM.makeFloor(3, {json.dumps(SEED)}))")), "mode": "explore"}
    M.RUN_FILE.write_text(json.dumps(old_run), encoding="utf-8")
    M.FAME_FILE.write_text(json.dumps(fame), encoding="utf-8")
    desktop = S.Desktop()
    win = M.launch(desktop)
    body = win.content
    assert body.view is not None, "the game file wasn't found"
    assert support.pump(40, until=lambda: body.imported is not None), "the page never said what it took"
    assert body.imported == ["fame", "run"], body.imported
    assert not M.RUN_FILE.exists() and (saves / "run.imported.json").exists() and (saves / "hall_of_fame.imported.json").exists()
    box = []
    body.page.runJavaScript("JSON.stringify({fame: CM.game.fame.length, floor: CM.game.lastRun.floor.number, gold: CM.game.lastRun.gold, "
                            "name: CM.playerName})", lambda r: box.append(r))
    assert support.pump(10, until=lambda: box)
    got = json.loads(box[0])
    assert got["fame"] == 2 and got["floor"] == 3 and got["gold"] == 55 and got["name"], got
    main = desktop.main
    main.request_close()
    assert support.pump(10, until=lambda: main not in desktop.windows), "it didn't close"
    assert QApplication.activeModalWidget() is None
    support.pump(0.3)
    support.no_errors(caught)


if __name__ == "__main__":
    support.main(globals())
