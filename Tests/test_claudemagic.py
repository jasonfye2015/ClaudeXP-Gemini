"""Claude and Magic, the one-file game (ClaudeGames/claudemagic/game), driven in Qt WebEngine offscreen on a scratch
profile - the real saves are never touched: the built file is current with its source; every floor is solvable and
stocked, and the same from the same seed; the rules are the old game's (a fight ends, the party learns, a chest
opens, the camp trades and rests, the run ends in the Hall of Fame); a run saves and comes back after the page
reloads, and travels as text; the first-person view draws (WebGL, composited in software here); the music is written
from a seed and follows the mode and the depth, every sound is in its place and the ending sums the run up; the three
themes (drawn, Crawl's pixel tiles, photographed stone) ride inside the file, build every depth and switch at once; and
the Timeline's window opens, hands the page the old Python game's saves once, and closes."""
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


def build_module(name="build"):
    """build.py (or pack.py) as a module, from the game's folder."""
    spec = importlib.util.spec_from_file_location("claudemagic_" + name, GAME / (name + ".py"))
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
    assert got["stock"] == 16 and got["lightSold"], got


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
      out.caught = g.mode === 'combat' && g.messages.some(m => m.includes('out of the dark')) && ticks <= 6;
      // and the save knows the floors and the light
      g.mode = 'explore'; g.saveRun(); const saved = CM.store.get('run');
      out.saved = Object.keys(saved.floors).length >= 2 && saved.light.kind === 'torch' && saved.floor.number === 3;
      return out; }})()""")
    for key, value in got.items():
        assert value is True, (key, got)


def test_the_party():
    """The party: stats rolled and a hero made from them; names; the advice on a party's balance; the creation screen
    (four slots, callings changed, named, set out); who the monsters go for (the front row, the Knight most, never
    stone); the back row (half for a Mage, a knife from behind for a Rogue); ailments (poison bites and passes, the
    paralysed and asleep can't act, the blind miss, the cursed are weaker) and their cures (antidote, rest, temple,
    fountain); the monsters' touch; the new callings' casts; a level earned is a boon offered and chosen; an old
    hero comes up to date; and the sheet"""
    got = ask("""(function(){ const g = CM.game, out = {}, r = new CM.Random(5);
      const fixed = (hit) => ({next: () => 0.5, int: (a, b) => a, pick: (l) => l[0], chance: (p) => hit(p), shuffle: (l) => l});
      const st = CM.rollStats('Mage', r);
      out.rollRange = CM.STATS.every(s => st[s] >= 3 && st[s] <= 18) && st.int >= 6;
      const h = CM.makeHero('Knight', 'Brenwyn', {str: 16, dex: 10, con: 14, int: 8, wis: 8, luck: 10}, 'front');
      out.made = h.name === 'Brenwyn' && h.max === 38 && h.atk === 9 && h.df === 3 && h.maxmp === 0 && h.row === 'front' && h.hp === h.max;
      const mage = CM.makeHero('Mage', '', {str: 8, dex: 12, con: 10, int: 16, wis: 10, luck: 10});
      out.mage = mage.name === 'Mage' && mage.maxmp === 20 && mage.row === 'back' && mage.atk === 2;
      out.names = Array.from({length: 60}, () => CM.randomName()).every(n => /^[A-Z][a-z]{3,12}$/.test(n));
      const party = (classes) => classes.map(c => ({cls: c, name: c, stats: {str: 12, dex: 12, con: 12, int: 12, wis: 12, luck: 12}, row: CM.CLASSES[c].row}));
      const classic = CM.partyAdvice(party(CM.CLASSIC));
      out.classicSound = classic.sound && classic.notes.length === 1 && classic.notes[0].startsWith('A sound party');
      const noFront = CM.partyAdvice(party(['Mage', 'Mage', 'Cleric', 'Ranger']));
      out.noFront = !noFront.sound && noFront.notes.some(n => n.includes('No one up front'));
      out.noHeal = CM.partyAdvice(party(['Knight', 'Knight', 'Rogue', 'Ranger'])).notes.some(n => n.includes('No one can heal'));
      const low = CM.partyAdvice([{cls: 'Mage', name: 'Ith', stats: {str: 10, dex: 10, con: 10, int: 7, wis: 10, luck: 10}, row: 'back'}, ...party(['Knight', 'Cleric', 'Rogue'])]);
      out.lowStat = low.notes.some(n => n.includes("Ith's Intelligence is low"));
      // the creation screen
      CM.store.remove('run'); g.lastRun = null; g.setMode('title');
      CM.ui.slots = []; CM.ui.openCreate();
      out.createShown = CM.ui.screen === 'create' && document.querySelectorAll('#slots .slot').length === 4 && CM.ui.slots.map(s => s.cls).join() === CM.CLASSIC.join();
      const sel = document.querySelector('#slots .slot:nth-child(2) .cls'); sel.value = 'Ranger'; sel.dispatchEvent(new Event('change'));
      out.classChanged = CM.ui.slots[1].cls === 'Ranger' && CM.ui.slots[1].row === 'back';
      CM.ui.slots[0].name = 'Brenwyn'; CM.ui.renderCreate();
      document.querySelector('#create-seed').value = 'ember-crypt-417';
      CM.ui.setOut();
      out.setOut = g.mode === 'explore' && g.party.length === 4 && g.party[0].name === 'Brenwyn' && g.party[1].cls === 'Ranger' && g.party.every(p => p.stats && p.row && p.status);
      out.titleClasses = document.querySelectorAll('#classes .calling').length === 8;
      g.rnd = new CM.Random(11);
      // who the monsters go for
      const knight = g.party[0]; knight.row = 'front'; for (const p of g.party.slice(1)) p.row = 'back';
      const hits = {}; for (let i = 0; i < 600; i++) { const t = g.pickTarget(); hits[t.name] = (hits[t.name] || 0) + 1; }
      out.frontTakesIt = hits['Brenwyn'] > 350;
      knight.status.stone = 999; out.stoneSpared = g.pickTarget() !== knight; delete knight.status.stone;
      // the back row (blows land, no weak spots: the dice are stilled)
      const foe = () => ({name: 'Goblin', hp: 1000, max: 1000, atk: 1, df: 0, xp: 1, gold: 1});
      const blow = (hero) => { const f = foe(); hero.status = {}; g.strike(hero, f); return 1000 - f.hp; };
      g.rnd = fixed((p) => p >= 0.5);
      const mageHero = CM.makeHero('Mage', 'Ith', {str: 12, dex: 12, con: 10, int: 14, wis: 10, luck: 10}, 'back'); g.party.push(mageHero);
      const backBlow = blow(mageHero); mageHero.row = 'front'; const frontBlow = blow(mageHero); g.party.pop();
      out.backHalf = backBlow === Math.ceil(frontBlow / 2) && frontBlow > 1;
      const rogue = CM.makeHero('Rogue', 'Sly', {str: 10, dex: 14, con: 10, int: 10, wis: 10, luck: 10}, 'back'); g.party.push(rogue);
      const rb = blow(rogue); rogue.row = 'front'; const rf = blow(rogue); out.backstab = rb === rf * 2; g.party.pop();
      g.rnd = new CM.Random(11);
      // ailments
      const vic = g.party[2]; vic.status = {}; vic.hp = vic.max; vic.stats = {str: 10, dex: 10, con: 10, int: 10, wis: 10, luck: 10};
      g.rnd = fixed(() => false);
      out.poisoned = g.afflict(vic, 'poison', 'Giant Rat') && vic.status.poison === 8;
      g.rnd = new CM.Random(3);
      g.foes = [foe()]; g.foeKey = '0,0'; g.mode = 'combat'; const hpBefore = vic.hp;
      g.combatRound('fight'); out.poisonBites = vic.hp < hpBefore && vic.status.poison === 7;
      vic.status = {paralysis: 2}; g.foes[0].hp = 1000;
      g.combatRound('fight');
      out.paralysedSkips = g.messages.some(m => m.includes(vic.name + " is paralysed and can't act")) && vic.status.paralysis === 1;
      vic.status = {blind: 3}; out.blindMisses = g.hitChance(vic) < 0.5;
      vic.status = {curse: 999}; out.cursed = g.effective(vic).atk === Math.max(1, vic.atk - 2) && g.effective(vic).df === Math.max(0, vic.df - 2);
      vic.status = {sleep: 3}; out.asleep = !g.canAct(vic);
      // cures
      g.mode = 'explore'; vic.status = {poison: 5, blind: 2};
      g.bag.push(CM.antidote()); out.antidote = g.give(g.bag.length - 1, 2) === '' && Object.keys(vic.status).length === 0;
      vic.status = {poison: 5, curse: 999}; g.gold = 100; g.rest(); out.restCures = !vic.status.poison && vic.status.curse === 999;
      g.gold = 100; out.templeUncurse = g.temple('uncurse') === true && !vic.status.curse && g.gold === 40;
      g.gold = 10; vic.status = {stone: 999}; out.templePoor = g.temple('unstone') === false && vic.status.stone === 999;
      g.gold = 200; out.templeUnstone = g.temple('unstone') === true && !vic.status.stone && g.gold === 50;
      out.templeNothing = g.temple('cure') === false;
      vic.status = {poison: 3, curse: 999}; const f = {type: 'fountain', kind: 'heal', used: false}; g.drink(f); out.fountainCures = Object.keys(vic.status).length === 0;
      // the monsters' touch
      g.rnd = fixed((p) => p >= 0.15);
      vic.status = {}; g.foes = [{name: 'Giant Rat', hp: 100, max: 100, atk: 2, df: 0, xp: 1, gold: 1}]; g.mode = 'combat';
      for (const p of g.party) p.row = 'back'; vic.row = 'front';
      g.combatRound('potion');
      out.ratPoisons = vic.status.poison === 7;                           // (bitten this round, and the round's end has passed)
      g.rnd = new CM.Random(9);
      // the new callings' casts
      const mk = (cls) => CM.makeHero(cls, cls, {str: 12, dex: 12, con: 12, int: 14, wis: 14, luck: 10});
      g.party = [mk('Paladin'), mk('Ranger'), mk('Druid'), mk('Bard')]; g.mode = 'combat'; g.song = 0;
      g.foes = [foe(), foe(), foe()];
      const before = g.foes.map(x => x.hp);
      g.party[0].hp = 5; g.cast(g.party[0], g.living()); out.lay = g.party[0].hp > 5 && g.party[0].mp === g.party[0].maxmp - 3;
      const fx2 = []; g.on('fx', (x) => fx2.push(x)); g.cast(g.party[1], g.living()); out.volley = fx2.filter(x => x.kind === 'hit' || x.kind === 'miss').length === 2;
      g.rnd = fixed(() => true);
      g.cast(g.party[2], g.living()); out.thorns = g.foes.every((x, i) => x.hp < before[i]) && g.foes.every(x => x.held === 1);
      g.cast(g.party[3], g.living()); out.song = g.song === 1 && g.effective(g.party[0]).atk === g.party[0].atk + 2;
      g.rnd = new CM.Random(9);
      // a level earned is a boon offered and chosen
      const hero = g.party[0]; hero.xp = CM.xpForLevel(2) - 1;
      g.foes = [{name: 'Goblin', hp: 0, max: 10, atk: 1, df: 0, xp: 2, gold: 1}]; g.foeKey = '0,0';
      g.wonFight(); out.levelled = hero.level === 2 && hero.pending === 1 && hero.hp === hero.max;
      const offer = g.offerBoons(hero); out.offer = offer.length === 3 && new Set(offer).size === 3 && offer[0] === 'faith' && g.offerBoons(hero) === offer;
      const wisBefore = hero.stats.wis;
      out.chosen = g.chooseBoon(hero, 'faith') === true && hero.stats.wis === wisBefore + 2 && hero.pending === 0 && hero.offer === null;
      out.chooseTwice = g.chooseBoon(hero, 'faith') === false;
      // an old hero comes up to date
      const old = {name: 'Knight', cls: 'Knight', level: 3, xp: 100, hp: 40, max: 40, mp: 0, maxmp: 0, atk: 9, df: 4, weapon: {name: 'Club', kind: 'weapon', power: 1, value: 5}, armor: {name: 'Tunic', kind: 'armor', power: 0, value: 5}};
      CM.upgradeHero(old); out.upgraded = old.stats.str === 13 && old.stats.con === 12 && old.row === 'front' && typeof old.status === 'object' && old.max === 40;
      // the sheet, with the boon on offer when there is one
      g.party[1].pending = 1; CM.ui.openSheet(1);
      out.sheet = document.querySelector('#dlg-sheet').classList.contains('on') && document.querySelectorAll('#sheet-boon .offer button').length === 3 && document.querySelector('#sheet-title').textContent.includes('Ranger');
      CM.ui.closeDialogs(); g.party[1].pending = 0; g.party[1].offer = null;
      g.setMode('explore');
      return out; })()""")
    for key, value in got.items():
        assert value is True, (key, got)


def test_the_fight():
    """The fight, turn by turn: everyone in order of speed, a hero waiting for a word; Fight at the chosen foe; Defend,
    Guard, Protection and the Song soften blows; the Mage's book known by level (Magic Missile never misses, Sleep,
    Fireball wakes), the Cleric's prayers (Heal, Cure, Turn Undead burns and routs the undead, Raise Dead), the
    Knight's Guard and Taunt, the Ranger's Aimed Shot once a fight and Mark; what the monsters do (trolls knit,
    vampires feed, kobolds bolt with a purse, goblins reach the back row, demons breathe fire, wraiths drain,
    minotaurs charge), mixed groups and leaders; a corridor lets two through; surprise both ways; running steps the
    party back, Blink two; the Rogue picks locks; healing and Light between fights; and the Lich King - he rises
    while his heart beats, calls skeletons, breathes cold, and dies for good once the phylactery (reachable on
    floor 19) is smashed"""
    run(PARSE)
    got = ask(f"""(function(){{ const g = CM.game, out = {{}};
      const fixed = (hit) => ({{next: () => 0.5, int: (a, b) => a, pick: (l) => l[0], chance: (p) => hit(p), shuffle: (l) => l}});
      const mk = (cls, name, level) => {{ const h = CM.makeHero(cls, name, {{str: 12, dex: 12, con: 12, int: 14, wis: 14, luck: 10}}); h.level = level || 1; CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; return h; }};
      const foe = (name, over) => Object.assign(CM.makeMonster(CM.monsterKind(name), 5, new CM.Random(1)), {{held: 0, asleep: 0, blind: 0, marked: false, charged: false, fled: false}}, over || {{}});
      CM.store.remove('run'); g.lastRun = null; g.newGame({json.dumps(SEED)});
      g.party = [mk('Knight', 'Dor', 5), mk('Ranger', 'Jor', 5), mk('Cleric', 'Val', 8), mk('Mage', 'Ith', 6)];
      const kn = g.party[0], rg = g.party[1], cl = g.party[2], mage = g.party[3];
      // begun by walking into monsters: turns in order of speed, a hero waiting for a word
      CM.useFloor(g, CM.testFloor(5, ["########", "#X.M...#", "########"]));
      g.rnd = fixed(() => false);
      g.move(0); g.move(0);
      out.begun = g.mode === 'combat' && g.combat.round === 1 && g.combat.order.length === g.party.length + g.foes.length && g.combat.waiting !== null;
      out.ordered = g.combat.order.every((s, i, arr) => i === 0 || arr[i - 1].init >= s.init);
      out.corridor = g.reachLimit() === 2;
      // Fight at the chosen foe
      g.foes = [foe('Goblin', {{name: 'Goblin A'}}), foe('Goblin', {{name: 'Goblin B'}}), foe('Goblin', {{name: 'Goblin C'}})]; for (const m of g.foes) m.hp = m.max = 500;
      g.combat = null; g.ensureCombat(); g.setTarget(1);
      const first = g.combat.waiting, before = g.foes.map(m => m.hp);
      g.rnd = fixed((p) => p >= 0.5);
      out.fought = g.act('fight', 1) === true && g.foes[1].hp < before[1] && g.foes[0].hp === before[0] && g.foes[2].hp === before[2] && g.combat.waiting !== first;
      // blows softened: Defend, Guard, Protection, the Song
      const vic = kn; vic.hp = vic.max; vic.defending = true; g.song = 0; g.combat.protect = false;
      const d1 = g.hurt(vic, 20, g.foes[0], {{noTouch: true}}); vic.defending = false; const d2 = g.hurt(vic, 20, g.foes[0], {{noTouch: true}});
      out.defend = d1 === 10 && d2 === 20;
      kn.hp = kn.max; mage.hp = mage.max; kn.guarding = mage; mage.guardedBy = kn;
      g.hurt(mage, 10, g.foes[0], {{noTouch: true}}); out.guarded = mage.hp === mage.max && kn.hp === kn.max - 10; mage.guardedBy = null; kn.guarding = null;
      g.combat.protect = true; const d3 = g.hurt(vic, 20, g.foes[0], {{noTouch: true}}); g.combat.protect = false; g.song = 1; const d4 = g.hurt(vic, 20, g.foes[0], {{noTouch: true}}); g.song = 0;
      out.softened = d3 === 17 && d4 === 19;
      // the Mage's book
      out.book = CM.abilitiesFor(mage).join() === 'missile,firebolt,light,sleep,frost,fireball,blink,lightning' && CM.abilitiesFor(cl).includes('raise') && !CM.abilitiesFor(mk('Cleric', 'x', 1)).includes('raise');
      g.rnd = fixed(() => false); g.combat.waiting = mage; mage.mp = mage.maxmp; const hpB = g.foes[2].hp;
      out.missile = g.act('cast', {{id: 'missile', target: 2}}) === true && g.foes[2].hp === hpB - (6 + 2 * mage.level + 4);
      g.rnd = fixed(() => true); g.combat.waiting = mage;
      out.sleep = g.act('cast', {{id: 'sleep'}}) === true && g.foes.every(m => m.asleep === 3);
      g.combat.waiting = mage; const hpC = g.foes.map(m => m.hp);
      out.fireball = g.act('cast', {{id: 'fireball'}}) === true && g.foes.every((m, i) => m.hp === hpC[i] - (8 + 4 * mage.level + 4)) && g.foes.every(m => m.asleep === 0);
      mage.mp = 1; g.combat.waiting = mage; out.cantAfford = g.act('cast', {{id: 'fireball'}}) === false && g.combat.waiting === mage;
      // the Cleric's prayers
      cl.mp = cl.maxmp; g.combat.waiting = cl; vic.hp = 1; vic.status = {{poison: 3}};
      out.heal = g.act('cast', {{id: 'heal', target: 0}}) === true && vic.hp === Math.min(vic.max, 1 + 12 + 4 * cl.level + 4);
      g.combat.waiting = cl; out.cure = g.act('cast', {{id: 'cure', target: 0}}) === true && !vic.status.poison;
      g.foes = [foe('Skeleton'), foe('Skeleton'), foe('Goblin')]; g.combat.foes = g.foes; for (const m of g.foes) m.hp = m.max = 300;
      g.rnd = fixed(() => true); g.combat.waiting = cl;
      out.turned = g.act('cast', {{id: 'turn'}}) === true && g.foes[0].fled && g.foes[1].fled && !g.foes[2].fled && g.foes[2].hp === 300;
      g.rnd = fixed(() => false); mage.hp = 0; g.combat.waiting = cl;
      out.raised = g.act('cast', {{id: 'raise', target: 3}}) === true && mage.hp === Math.floor(mage.max / 3);
      // the Knight and the Ranger
      g.foes = [foe('Orc'), foe('Orc')]; g.combat.foes = g.foes; for (const m of g.foes) m.hp = m.max = 400;
      // (the guard lasts until the Knight's next turn: so the Ranger's comes next)
      g.combat.order = [{{hero: kn, init: 9}}, {{hero: rg, init: 8}}]; g.combat.index = 1; g.combat.waiting = kn;
      out.guard = g.act('cast', {{id: 'guard', target: 3}}) === true && mage.guardedBy === kn && g.combat.waiting === rg;
      g.combat.waiting = kn; g.combat.round = 1; out.taunt = g.act('cast', {{id: 'taunt'}}) === true && g.combat.taunter === kn && g.pickTarget(g.foes[0]) === kn;
      g.combat.waiting = kn; out.tauntOnce = g.act('cast', {{id: 'taunt'}}) === false;
      g.combat.waiting = rg; const o0 = g.foes[0].hp; out.aimed = g.act('cast', {{id: 'aimed', target: 0}}) === true && g.foes[0].hp < o0;
      g.combat.waiting = rg; out.aimedOnce = g.act('cast', {{id: 'aimed', target: 0}}) === false;
      g.combat.waiting = rg; out.mark = g.act('cast', {{id: 'mark', target: 1}}) === true && g.foes[1].marked === true;
      // what the monsters do
      g.rnd = fixed(() => true); for (const p of g.party) {{ p.hp = p.max; p.status = {{}}; p.row = 'front'; p.guardedBy = null; p.defending = false; }}
      const troll = foe('Troll'); troll.hp = troll.max - 20; g.foes = [troll]; g.combat.foes = g.foes; g.endRound();
      out.regen = troll.hp === troll.max - 20 + Math.max(1, Math.floor(troll.max * 0.05));
      const vamp = foe('Vampire', {{hp: 10, max: 100}}); g.foes = [vamp]; g.combat.reached = 0; g.monsterAct(vamp); out.lifesteal = vamp.hp > 10;
      const kob = foe('Kobold', {{hp: 1, max: 100}}); g.foes = [kob]; g.gold = 1000; g.combat.reached = 0; g.monsterAct(kob); out.coward = kob.fled === true && g.gold === 950;
      g.rnd = new CM.Random(5); g.combat.taunter = null; const gob = foe('Goblin'); g.foes = [gob]; mage.row = 'back'; mage.hp = mage.max;
      let backHit = false; for (let i = 0; i < 60 && !backHit; i++) {{ g.combat.reached = 0; g.monsterAct(gob); backHit = mage.hp < mage.max; }} out.ranged = backHit;
      g.rnd = fixed(() => true); const dem = foe('Demon'); g.foes = [dem]; g.combat.reached = 0; g.monsterAct(dem); for (const p of g.party) p.hp = p.max; g.combat.reached = 0; g.monsterAct(dem);
      out.breath = g.party.every(p => p.hp < p.max);
      const wr = foe('Wraith'); g.foes = [wr]; kn.xp = 100; g.combat.taunter = kn; g.combat.tauntUntil = 99; g.combat.reached = 0; g.monsterAct(wr); out.drain = kn.xp < 100;
      const mino = foe('Minotaur'); g.foes = [mino]; kn.hp = kn.max; kn.status = {{}}; g.combat.reached = 0; g.monsterAct(mino); const charge = kn.max - kn.hp; kn.hp = kn.max; g.combat.reached = 0; g.monsterAct(mino);
      out.charge = charge > kn.max - kn.hp && mino.charged === true;
      // mixed company, and leaders
      const r8 = new CM.Random(8); let mixed = 0, elites = 0; for (let i = 0; i < 300; i++) {{ const grp = CM.monsterGroup(8, r8); if (new Set(grp.map(m => m.kind)).size > 1) mixed++; if (grp.some(m => m.elite)) elites++; }}
      out.mixed = mixed > 30 && elites > 15;
      // a corridor lets two through
      g.combat.taunter = kn; g.combat.tauntUntil = 99; kn.hp = kn.max; kn.status = {{}}; g.foes = [foe('Goblin', {{ability: null}}), foe('Goblin', {{ability: null}}), foe('Goblin', {{ability: null}})]; g.combat.reached = 0;
      g.rnd = fixed(() => true); let hits = 0; for (const m of g.foes) {{ const hp = kn.hp; g.monsterAct(m); if (kn.hp < hp) hits++; }}
      out.twoReach = hits === 2 && g.messages.some(m => m.includes('crowd behind'));
      // surprise, both ways
      g.combat = null; g.mode = 'explore'; g.rnd = fixed(() => true); for (const p of g.party) p.hp = p.max;
      g.startCombat('3,1', {{group: [foe('Orc')]}}, true); out.theirSurprise = g.messages.some(m => m.includes('before you can draw')) && g.party.some(p => p.hp < p.max);
      g.combat = null; g.mode = 'explore'; g.rnd = fixed((p) => p >= 0.3);
      g.startCombat('3,1', {{group: [foe('Orc')]}}, false); out.ourSurprise = g.combat.order.every(s => s.hero) && g.messages.some(m => m.includes('drop on them'));
      // running steps the party back; Blink two squares
      g.combat = null; g.mode = 'explore'; CM.useFloor(g, CM.testFloor(5, ["#######", "#...XM#", "#######"])); g.rnd = fixed(() => false);
      g.move(0); g.rnd = fixed(() => true); g.combat.waiting = g.party[0]; out.ran = g.act('run') === true && g.mode === 'explore' && g.floor.pos[0] === 3;
      g.floor.pos = [4, 1]; g.rnd = fixed(() => false); g.move(0); g.combat.waiting = mage; mage.mp = mage.maxmp;
      out.blinked = g.act('cast', {{id: 'blink'}}) === true && g.mode === 'explore' && g.floor.pos[0] === 2;
      out.noRunFromLich = (() => {{ g.combat = null; g.mode = 'explore'; g.floor.pos = [4, 1]; g.floor.things['5,1'] = {{type: 'boss', group: [CM.bossMonster()]}}; g.move(0); g.combat.waiting = g.party[0]; return g.act('run') === true && g.mode === 'combat'; }})();
      // the Lich King: he rises while his heart beats, calls skeletons, breathes cold - and dies for good once it's smashed
      const lich = g.foes[0]; g.phylactery = false; g.rnd = fixed(() => true);
      lich.hp = 1; g.combat.waiting = kn; g.act('fight', 0);
      out.rises = g.mode === 'combat' && lich.hp === Math.floor(lich.max * CM.LICH.riseTo) && g.foes.filter(f => f.summoned).length === 2;
      for (const s of g.foes) if (s.summoned) s.hp = 0;
      lich.hp = Math.floor(lich.max * 0.5); g.combat.summonTick = 0; g.combat.reached = 0; const n0 = g.foes.length; g.monsterAct(lich); out.summons = g.foes.length === n0 + 2;
      lich.hp = Math.floor(lich.max * 0.2); g.combat.cold = 1; for (const p of g.party) p.hp = p.max; g.monsterAct(lich); out.cold = g.party.every(p => p.hp < p.max);
      for (const s of g.foes) if (s.summoned) s.hp = 0;
      g.phylactery = true; lich.hp = 1; g.combat.waiting = kn; g.act('fight', 0);
      out.slain = g.mode === 'title' && g.fame.length > 0 && g.fame[0].won === true;
      const f19 = CM.makeFloor(19, {json.dumps(SEED)}); const pk = Object.keys(f19.things).find(k => f19.things[k].type === 'phylactery');
      out.heart = Boolean(pk) && CM.reachable(f19).has(pk) && !Object.values(CM.makeFloor(18, {json.dumps(SEED)}).things).some(t => t.type === 'phylactery');
      // the Rogue picks locks; healing and Light between fights; the heart smashed
      g.newGame({json.dumps(SEED)}); g.party = [mk('Rogue', 'Sly', 2), mk('Cleric', 'Val', 3), mk('Mage', 'Ith', 2), mk('Knight', 'Dor', 1)];
      CM.useFloor(g, CM.testFloor(5, ["#####", "#XL.#", "#####"])); g.rnd = fixed(() => true); g.bag = g.bag.filter(i => i.kind !== 'key');
      g.move(0); out.picked = g.floor.features['2,1'].open === true && g.messages.some(m => m.includes('picks the lock'));
      g.party[3].hp = 1; out.healedOutside = g.castOutside(1, 'heal', 3) === true && g.party[3].hp > 1;
      out.notOutside = g.castOutside(2, 'firebolt', null) === false;
      g.light = {{kind: null, left: 0}}; out.lit = g.castOutside(2, 'light', null) === true && g.spellLight === CM.LIGHT_STEPS && g.hasLight() && g.lightFactor() > 1;
      CM.useFloor(g, CM.testFloor(19, ["####", "#X.#", "####"])); g.floor.things['2,1'] = {{type: 'phylactery'}}; g.move(0); g.use();
      out.smashed = g.phylactery === true && !g.floor.things['2,1'] && CM.store.get('run').phylactery === true;
      // the fight's own bar
      CM.useFloor(g, CM.testFloor(5, ["########", "#X.M...#", "########"])); g.rnd = fixed(() => false); g.move(0); g.move(0);
      const bar = document.querySelector('#actions');
      out.bar = bar.classList.contains('combat') && bar.querySelector('.turn').textContent.includes(g.combat.waiting.name) && bar.querySelectorAll('.targets button').length === g.living().length;
      CM.ui.combatMenu('cast'); out.castList = bar.querySelectorAll('.menu button.pick').length === CM.abilitiesFor(g.combat.waiting).length;
      CM.ui.combatMenu('main'); g.combat = null; g.setMode('explore');
      return out; }})()""")
    for key, value in got.items():
        assert value is True, (key, got)


def test_the_hoard():
    """The hoard: every kind of thing turns up, with properties deeper down and nothing strange near the top; an
    unknown thing shows its bare name until worn or identified; who may wear what (heavy armour, bows, shields,
    two hands); rings count in the stats; a charm turns an ailment; a curse clings until the temple lifts it; a
    blessed blade bites the undead; scrolls and wands between fights (Mapping, Identify, Teleport, a Wand of
    Healing) and in them (Fire, Frost - a wand spent crumbles); a trapped chest seen to by the Rogue, or sprung
    (a blade, an alarm that brings a fight); the tavern's recruits for the fallen and the scribe; what the deepest
    run unlocks, the kits applied, today's dungeon, and the title that shows it all"""
    run(PARSE)
    got = ask(f"""(function(){{ const g = CM.game, out = {{}}, r = new CM.Random(21);
      const fixed = (hit) => ({{next: () => 0.5, int: (a, b) => a, pick: (l) => l[0], chance: (p) => hit(p), shuffle: (l) => l}});
      const kinds = {{}}, seen = {{unknown: 0, cursed: 0, element: 0, bow: 0, twohanded: 0, bonus: 0}};
      for (let i = 0; i < 600; i++) {{ const it = CM.makeItem(12, r); kinds[it.kind] = (kinds[it.kind] || 0) + 1; if (it.unknown) seen.unknown++;
        const p = it.props || {{}}; if (p.cursed) seen.cursed++; if (p.element) seen.element++; if (p.bow) seen.bow++; if (p.twohanded) seen.twohanded++; if (p.bonus) seen.bonus++; }}
      out.kinds = ['weapon', 'armor', 'heal', 'shield', 'helm', 'ring', 'amulet', 'scroll', 'wand'].every(k => kinds[k] > 0);
      out.props = seen.unknown > 100 && seen.cursed > 3 && seen.element > 10 && seen.bow > 3 && seen.twohanded > 10 && seen.bonus > 20;
      out.shallowPlain = Array.from({{length: 200}}, () => CM.makeItem(1, r)).every(it => !it.unknown && !(it.props && (it.props.cursed || it.props.element)));
      const sword = {{name: 'Flaming Long Sword +1', kind: 'weapon', slot: 'weapon', power: 12, value: 300, props: {{element: 'fire', bonus: 1}}, unknown: true}};
      out.label = CM.itemLabel(sword).startsWith('unknown') && CM.baseName(sword) === 'Long Sword' && (sword.unknown = false, CM.itemLabel(sword).includes('weapon +12') && CM.itemLabel(sword).includes('fire'));
      // who may wear what
      const mage = CM.makeHero('Mage', 'Ith', {{str: 10, dex: 10, con: 10, int: 14, wis: 10, luck: 10}}), knight = CM.makeHero('Knight', 'Dor', {{str: 14, dex: 10, con: 12, int: 8, wis: 8, luck: 10}});
      const ranger = CM.makeHero('Ranger', 'Jor', {{str: 10, dex: 14, con: 10, int: 10, wis: 10, luck: 10}});
      const plate = {{name: 'Plate Mail', kind: 'armor', slot: 'armor', power: 8, value: 900, props: {{weight: 'heavy'}}}};
      const bow = {{name: 'Long Bow', kind: 'weapon', slot: 'weapon', power: 8, value: 200, props: {{bow: true, twohanded: true}}}};
      const shield = {{name: 'Iron Shield', kind: 'shield', slot: 'offhand', power: 3, value: 180, props: {{}}}};
      const axe = {{name: 'Battle Axe', kind: 'weapon', slot: 'weapon', power: 9, value: 300, props: {{twohanded: true}}}};
      out.wearRules = CM.cantWear(mage, plate) !== '' && CM.cantWear(knight, plate) === '' && CM.cantWear(mage, bow) !== '' && CM.cantWear(ranger, bow) === '' && CM.cantWear(mage, shield) !== '' && CM.cantWear(knight, shield) === '';
      // wearing things: slots, two hands, rings in the stats, unknown things learned, curses that cling
      CM.store.remove('run'); g.lastRun = null; g.newGame({json.dumps(SEED)}); g.party = [knight, mage, ranger, CM.makeHero('Cleric', 'Val')]; g.mode = 'explore';
      g.bag = [shield, axe, {{name: 'Ring of Might +2', kind: 'ring', slot: 'ring', power: 2, value: 320, props: {{stat: 'str'}}, unknown: true}},
        {{name: 'Amulet against Poison', kind: 'amulet', slot: 'amulet', power: 0, value: 140, props: {{resist: 'poison'}}}},
        {{name: 'Dagger', kind: 'weapon', slot: 'weapon', power: 2, value: 15, props: {{cursed: true}}, unknown: true}}, bow];
      out.shieldOn = g.give(0, 0) === '' && knight.offhand === shield && CM.gearDefence(knight) === 6;
      out.axeSlings = g.give(0, 0) === '' && knight.weapon === axe && knight.offhand === null && g.bag.includes(shield) && g.bag.some(i => i.name === 'Club');
      const atkBefore = knight.atk, ringRow = g.bag.findIndex(i => i.kind === 'ring');
      out.ring = g.give(ringRow, 0) === '' && knight.ring && !knight.ring.unknown && CM.heroStat(knight, 'str') === 16 && knight.atk === atkBefore + 1 && g.messages.some(m => m.includes("it's Ring of Might +2"));
      out.cantShieldNow = g.give(g.bag.indexOf(shield), 0) !== '' && knight.offhand === null;
      out.amulet = g.give(g.bag.findIndex(i => i.kind === 'amulet'), 1) === '' && mage.amulet && mage.amulet.props.resist === 'poison';
      g.rnd = fixed(() => false); out.charm = g.afflict(mage, 'poison', 'rat') === false && !mage.status.poison && g.messages.some(m => m.includes('grows warm'));
      out.cursedClings = g.give(g.bag.findIndex(i => i.kind === 'weapon' && i.props.cursed), 2) === '' && ranger.weapon.props.cursed && !ranger.weapon.unknown && g.messages.some(m => m.includes("It's cursed"));
      out.cursedStays = g.takeOff(2, 'weapon') !== '' && g.give(g.bag.indexOf(bow), 2) !== '' && ranger.weapon.props.cursed;
      g.mode = 'camp'; g.gold = 100; out.uncursedGear = g.temple('uncurse') === true && !ranger.weapon.props.cursed && g.give(g.bag.indexOf(bow), 2) === '' && ranger.weapon === bow; g.mode = 'explore';
      out.takeOff = g.takeOff(0, 'ring') === '' && knight.ring === null && g.bag.some(i => i.kind === 'ring') && CM.heroStat(knight, 'str') === 14;
      // a blessed blade bites the undead
      g.rnd = fixed((p) => p >= 0.5); const skel = Object.assign(CM.makeMonster(CM.monsterKind('Skeleton'), 5, new CM.Random(1)), {{hp: 1000, max: 1000, df: 0}});
      knight.weapon = {{name: 'Blessed Mace', kind: 'weapon', slot: 'weapon', power: 5, value: 200, props: {{element: 'holy'}}}}; knight.row = 'front';
      g.strike(knight, skel); const holy = 1000 - skel.hp; skel.hp = 1000;
      knight.weapon = {{name: 'Mace', kind: 'weapon', slot: 'weapon', power: 5, value: 100, props: {{}}}}; g.strike(knight, skel); const plain = 1000 - skel.hp;
      out.holy = holy === Math.ceil(plain * 1.5) && plain > 0;
      // scrolls and wands
      g.bag = [CM.scroll('mapping'), CM.scroll('identify'), {{name: 'Iron Cap', kind: 'helm', slot: 'helm', power: 2, value: 60, props: {{}}, unknown: true}}, CM.scroll('teleport'), CM.wand('healing', 2), CM.scroll('fire'), CM.wand('frost', 1)];
      const fl = g.floor; fl.seen = []; out.mapping = g.give(0, 0) === '' && fl.seen.length === fl.grid.length * fl.grid.length && !g.bag.some(i => i.spell === 'mapping');
      out.identifyAsks = g.give(0, 0).includes('pick the unknown') && g.identifying === true;
      out.identified = g.identify(1) === '' && !g.bag.some(i => i.spell === 'identify') && g.bag.find(i => i.kind === 'helm').unknown === false && g.identifying === false;
      const posB = fl.pos.slice(); g.give(g.bag.findIndex(i => i.spell === 'teleport'), 0);
      out.teleport = (fl.pos[0] !== posB[0] || fl.pos[1] !== posB[1]) && CM.passable(fl, fl.pos[0], fl.pos[1]) && !g.bag.some(i => i.spell === 'teleport');
      knight.hp = 1; const wandRow = g.bag.findIndex(i => i.spell === 'healing'); out.wandHeals = g.give(wandRow, 0) === '' && knight.hp > 1 && g.bag[wandRow].charges === 1;
      out.fireIsForFights = g.give(g.bag.findIndex(i => i.spell === 'fire'), 0) !== '';
      g.foes = [Object.assign(CM.makeMonster(CM.monsterKind('Orc'), 5, new CM.Random(2)), {{hp: 500, max: 500}})]; g.combat = null; g.mode = 'combat'; g.ensureCombat();
      g.combat.waiting = knight; const o0 = g.foes[0].hp;
      out.scrollFire = g.act('item', {{row: g.bag.findIndex(i => i.spell === 'fire')}}) === true && g.foes[0].hp < o0 && !g.bag.some(i => i.spell === 'fire');
      g.combat.waiting = knight; const o1 = g.foes[0].hp;
      out.wandSpent = g.act('item', {{row: g.bag.findIndex(i => i.spell === 'frost')}}) === true && g.foes[0].hp < o1 && !g.bag.some(i => i.spell === 'frost') && g.messages.some(m => m.includes('is spent'));
      g.combat = null; g.mode = 'explore';
      // trapped chests
      const f2 = CM.useFloor(g, CM.testFloor(4, ["#####", "#XC.#", "#####"])); f2.things['2,1'].trap = 'blade'; f2.things['2,1'].items = [];
      g.party[3] = CM.makeHero('Rogue', 'Sly', {{str: 10, dex: 14, con: 10, int: 10, wis: 10, luck: 10}}); g.rnd = fixed(() => true);
      g.move(0); g.use(); out.disarmed = g.messages.some(m => m.includes('sees to it')) && !f2.things['2,1'] && g.party.every(p => p.hp > 0);
      const f3 = CM.useFloor(g, CM.testFloor(4, ["#####", "#XC.#", "#####"])); f3.things['2,1'].trap = 'blade'; f3.things['2,1'].items = [];
      g.party[3] = CM.makeHero('Cleric', 'Val'); for (const p of g.party) p.hp = p.max;
      g.move(0); g.use(); out.bladeBites = g.party[0].hp < g.party[0].max && !f3.things['2,1'];
      const f4 = CM.useFloor(g, CM.testFloor(4, ["#####", "#XC.#", "#####"])); f4.things['2,1'].trap = 'alarm'; g.rnd = fixed(() => false);
      g.move(0); g.use(); out.alarm = g.mode === 'combat' && f4.things['2,1'] && f4.things['2,1'].type === 'chest' && g.messages.some(m => m.includes('something that heard it'));
      g.combat = null; g.mode = 'explore';
      // the tavern and the scribe
      g.floor.number = 5; g.mode = 'camp'; g.party[1].hp = 0; g.gold = 1000; const recruits = g.tavern();
      out.recruits = recruits.length === 3 && recruits.every(x => x.name && x.cls && x.level >= 1 && x.price > 0) && g.tavern() === recruits;
      const price = recruits[0].price, name = recruits[0].name;
      out.hired = g.hire(0) === '' && g.party[1].name === name && g.party[1].hp > 0 && g.gold === 1000 - price && g.tavern().length === 2;
      out.whole = g.hire(0).includes('whole');
      g.bag.push({{name: 'Steel Helm', kind: 'helm', slot: 'helm', power: 4, value: 240, props: {{}}, unknown: true}}); g.gold = 100;
      out.scribe = g.scribe() === true && g.gold === 75 && !g.bag.some(i => i.unknown) && g.scribe() === false;
      // what the deepest run so far unlocks, and the kits
      out.unlocks = CM.unlocked([]).join() === 'pauper' && CM.unlocked([{{floor: 5}}]).join() === 'pauper,veteran' && CM.unlocked([{{floor: 12}}]).includes('delver')
        && !CM.unlocked([{{floor: 12}}]).includes('heir') && CM.unlocked([{{floor: 20, won: true}}]).includes('legend');
      g.fame = [{{name: 'x', floor: 16, gold: 1, won: false, date: 'd'}}];
      g.newGame({json.dumps(SEED)}, null, 'veteran'); out.veteran = g.gold === 90 && g.bag.some(i => i.kind === 'lantern') && g.kit === 'veteran';
      g.newGame({json.dumps(SEED)}, null, 'heir'); out.heir = g.party.every(p => p.weapon.power === 3 && p.weapon.name.endsWith('+1'));
      g.newGame({json.dumps(SEED)}, null, 'legend'); out.legendLocked = g.kit === 'pauper' && g.party.every(p => p.level === 1);
      g.fame = [{{name: 'x', floor: 20, gold: 1, won: true, date: 'd'}}]; g.newGame({json.dumps(SEED)}, null, 'legend');
      out.legend = g.party.every(p => p.level === 2 && p.pending === 1) && CM.store.get('run').kit === 'legend';
      // today's dungeon
      out.daily = /^daily-\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(CM.dailySeed()) && CM.dailySeed(new Date(2026, 9, 29)) === 'daily-2026-10-29';
      g.newGame(CM.dailySeed()); g.endRun(false); out.dailyMarked = g.fame.some(e => e.daily === true && Array.isArray(e.party) && e.seed === CM.dailySeed());
      // the title knows
      g.fame = [{{name: 'x', floor: 10, gold: 1, won: false, date: 'd'}}]; CM.ui.refreshTitle();
      out.titleUnlocks = document.querySelectorAll('#unlocks .unlock').length === 5 && document.querySelectorAll('#unlocks .unlock.got').length === 3 && document.querySelectorAll('#kit option').length === 3;
      g.fame = []; CM.store.set('fame', []); CM.store.remove('run'); g.lastRun = null; CM.ui.refreshTitle();
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


def test_the_sound_and_the_ending():
    """Phase 6: the music is written from a seed (the same tune every time: four chords, sixty-four steps, a tune for
    every kind) and follows the mode and the depth, as the ambience does; the new sounds are in their places (a
    door's creak, the key, the secret door's grinding, the lever, the teleporter, a fall, a trapped lid, a monster's
    call, a miss, a hero falling, an ailment) and footfalls change with the depth; something coming is heard before
    it's seen; the run keeps a tally, saved with it; the ending sums a run up (victory and defeat, the party roll,
    the tally, the place in the Hall of Fame) and its music follows; the Hall of Fame opens a row's details on a
    click and plays a seed again; the title wears its emblem; the music settings are kept"""
    run(PARSE)
    got = ask(f"""(function(){{ const g = CM.game, out = {{}};
      const fixed = (hit) => ({{next: () => 0.5, int: (a, b) => a, pick: (l) => l[0], chance: (p) => hit(p), shuffle: (l) => l}});
      // the music is written once, from a seed
      const a = CM.music.tune('battle'), b = CM.music.tune('battle');
      out.tune = a === b && a.melody.length === 64 && a.chords.length === 4 && a.melody.some(d => d !== null) && a.drums === true;
      out.kinds = Object.keys(CM.music.kinds).every(k => CM.music.tune(k).melody.length === 64 && CM.music.tune(k).chords.length === 4);
      out.differ = JSON.stringify(CM.music.tune('camp').melody) !== JSON.stringify(CM.music.tune('depth0').melody);
      out.midi = CM.music.midi(a, 0) === a.root && CM.music.midi(a, a.scale.length) === a.root + 12 && Math.round(CM.music.hz(69)) === 440;
      // ...and follows the mode and the depth, with the ambience
      CM.store.remove('run'); g.lastRun = null; g.newGame({json.dumps(SEED)}); g.rnd = new CM.Random(7);
      out.depthTune = CM.music.playing === 'depth0' && CM.audio.theme === 0 && CM.audio.ambientOn === true;
      g.setMode('combat'); out.battleTune = CM.music.playing === 'battle';
      g.setMode('camp'); out.campTune = CM.music.playing === 'camp' && CM.audio.theme === 4;
      g.setMode('explore'); CM.useFloor(g, CM.testFloor(12, ['#####', '#X..#', '#####']));
      out.hallsTune = CM.music.playing === 'depth2' && CM.audio.theme === 2;
      // footfalls by depth (the window maps 'step' to the depth's own)
      const played = [], origPlay = CM.audio.play; CM.audio.play = (n) => played.push(n);
      g.move(0); out.hallStep = played.includes('step_hall');
      CM.audio.play = origPlay;
      // the sounds, in their places
      const heard = []; g.on('sound', (n) => heard.push(n));
      const nears = [], origNear = CM.audio.near; CM.audio.near = (k, s) => nears.push([k, s]);
      let f = CM.useFloor(g, CM.testFloor(2, ['########', '#X.DKL>#', '########']));
      g.move(0); g.move(0); out.door = heard.includes('door');
      g.move(0); g.move(0); g.move(0); out.unlock = heard.includes('unlock');
      f = CM.useFloor(g, CM.testFloor(2, ['#####', '#XS.#', '#####'])); g.use(); out.grind = heard.includes('grind');
      f = CM.useFloor(g, CM.testFloor(2, ['#####', '#X/G#', '#####'])); g.move(0); g.turn(-1); g.use(); out.lever = heard.includes('lever') && f.features['3,1'].open;
      f = CM.useFloor(g, CM.testFloor(2, ['######', '#XO.O#', '######'])); g.move(0); out.teleport = heard.includes('teleport') && g.floor.pos[0] === 4;
      f = CM.useFloor(g, CM.testFloor(2, ['####', '#XP#', '####'])); g.move(0); out.fall = heard.includes('fall') && g.floor.number === 3;
      f = CM.useFloor(g, CM.testFloor(3, ['####', '#XC#', '####'])); f.things['2,1'].trap = 'blade'; g.move(0);
      const saveRnd = g.rnd; g.rnd = fixed(() => false); g.use(); g.rnd = saveRnd;
      out.trap = heard.includes('trap') && heard.includes('chest') && !f.things['2,1'] && g.tally.chests >= 1;
      f = CM.useFloor(g, CM.testFloor(3, ['#######', '#X...M#', '#######']));
      g.wander = 0; g.tick(1.2);
      out.near = nears.length > 0 && nears[0][1] > 0 && nears[0][1] <= 1 && CM.MONSTERS.some(m => m.name === nears[0][0]);
      CM.audio.near = origNear;
      const roars = new Set([...CM.MONSTERS.map(m => CM.roarFor(m.name)), CM.roarFor(CM.BOSS.name), CM.roarFor('Hulking Orc')]);
      out.roars = [...roars].every(r => ['roar_small', 'roar_big', 'roar_beast', 'roar_undead', 'lich'].includes(r)) && roars.size === 5 && CM.roarFor('Hulking Orc') === 'roar_big';
      f = CM.useFloor(g, CM.testFloor(3, ['####', '#XM#', '####'])); const fightsBefore = g.tally.fights; g.rnd = fixed(() => false); g.move(0);
      out.roar = g.mode === 'combat' && heard.some(n => n.startsWith('roar_')) && g.tally.fights === fightsBefore + 1;
      const hero = g.party[0], foe = g.foes[0];
      g.strike(hero, foe); out.miss = heard.includes('miss');
      g.afflict(g.party[2], 'poison', 'rat'); out.ailment = heard.includes('ailment') && g.party[2].status.poison > 0;
      g.hurt(g.party[3], 9999, {{name: 'Test'}}); out.fallen = heard.includes('fallen') && g.party[3].hp <= 0;
      g.rnd = new CM.Random(5);
      // the tally, kept with the run
      const killsBefore = g.tally.kills; g.wonFight(); out.kills = g.tally.kills === killsBefore + 1 && g.mode === 'explore';
      g.saveRun(); out.tallySaved = g.lastRun.tally.steps === g.tally.steps && g.tally.steps > 5 && g.lastRun.tally.kills === g.tally.kills;
      const steps = g.tally.steps; g.continueRun(); out.tallyBack = g.tally.steps === steps;
      // the ending: victory
      g.fame = []; g.party[3].hp = 0; g.party[0].hp = g.party[0].max; g.gold = 4321;
      const sayOver = []; g.on('over', (won, entry) => sayOver.push([won, entry.tally.kills, entry.kit]));
      g.endRun(true);
      const dlg = document.querySelector('#dlg-over');
      out.overEvent = sayOver.length === 1 && sayOver[0][0] === true && sayOver[0][1] === g.fame[0].tally.kills && sayOver[0][2] === 'pauper';
      out.wonShown = dlg.classList.contains('on') && dlg.classList.contains('won') && document.querySelector('#over-title').textContent.includes('Lich King is no more');
      out.wonText = document.querySelector('#over-text').textContent.includes(g.party[3].name) && document.querySelector('#over-text').textContent.includes('4,321');
      out.roll = document.querySelectorAll('#over-party > div').length === 4 && document.querySelectorAll('#over-party .fallen').length === 1 && document.querySelectorAll('#over-party canvas').length === 4;
      const tally = document.querySelector('#over-tally').textContent;
      out.tallyShown = document.querySelectorAll('#over-tally > div').length === 9 && tally.includes('1st of 1') && tally.includes('Pauper');
      out.victoryTune = CM.ui.ending === 'victory' && CM.music.playing === 'victory' && g.mode === 'title';
      CM.ui.closeDialogs(); out.closed = !dlg.classList.contains('on') && CM.ui.ending === null && CM.music.playing === 'title';
      // the Hall of Fame's details
      const row = document.querySelector('#fame tr.row'); out.noDetails = !document.querySelector('#fame tr.details');
      row.click(); const det = document.querySelector('#fame tr.details');
      out.details = det && det.textContent.includes({json.dumps(SEED)}) && det.textContent.includes('slain') && det.textContent.includes(g.fame[0].party[0]);
      document.querySelector('#seed').value = 'other'; det.querySelector('button[data-seed]').click(); out.playSeed = document.querySelector('#seed').value === {json.dumps(SEED)};
      document.querySelector('#fame tr.row').click(); out.detailsClosed = !document.querySelector('#fame tr.details');
      // the ending: defeat
      g.newGame({json.dumps(SEED)}); g.endRun(false);
      out.lostShown = dlg.classList.contains('on') && !dlg.classList.contains('won') && document.querySelector('#over-title').textContent.includes('fell on floor 1') && CM.music.playing === 'lament';
      CM.ui.closeDialogs(); out.lamentOver = CM.music.playing === 'title';
      // the emblem and the settings
      const em = CM.art.emblem(64), px = em.getContext('2d').getImageData(32, 32, 1, 1).data;
      out.emblem = em.width === 64 && px[3] > 0 && document.querySelector('#title h1 canvas') !== null && document.querySelector('#dlg-over .emblem-slot canvas') !== null;
      const music = document.querySelector('#set-music'); music.checked = false; music.dispatchEvent(new Event('input'));
      out.musicOff = g.settings.music === false && CM.music.enabled === false && CM.store.get('settings', {{}}).music === false;
      music.checked = true; music.dispatchEvent(new Event('input')); out.musicOn = g.settings.music === true && CM.music.enabled === true;
      const mvol = document.querySelector('#set-music-volume'); mvol.value = 30; mvol.dispatchEvent(new Event('input')); out.musicVolume = Math.abs(g.settings.musicVolume - 0.3) < 1e-9 && Math.abs(CM.music.volume - 0.3) < 1e-9;
      mvol.value = 50; mvol.dispatchEvent(new Event('input'));
      // the sounds themselves, where this page has an AudioContext (it needn't)
      out.audio = null;
      if (CM.audio.unlock() && CM.audio.ctx) {{
        const names = Object.keys(CM.audio.buffers);
        out.audio = ['door', 'unlock', 'lever', 'trap', 'teleport', 'fall', 'grind', 'miss', 'fallen', 'ailment', 'shatter', 'lich', 'roar_small', 'roar_big', 'roar_beast', 'roar_undead', 'step_water', 'step_hall', 'step_cold'].every(n => names.includes(n))
          && [0, 1, 2, 3, 4].every(t => Math.round(CM.audio.ambient(t).duration) === 10) && Boolean(CM.music.master);
      }}
      return out; }})()""")
    for key in ("tune", "kinds", "differ", "midi", "depthTune", "battleTune", "campTune", "hallsTune", "hallStep", "door", "unlock", "grind",
                "lever", "teleport", "fall", "trap", "near", "roars", "roar", "miss", "ailment", "fallen", "kills", "tallySaved", "tallyBack",
                "overEvent", "wonShown", "wonText", "roll", "tallyShown", "victoryTune", "closed", "noDetails", "details", "playSeed",
                "detailsClosed", "lostShown", "lamentOver", "emblem", "musicOff", "musicOn", "musicVolume"):
        assert got[key] is True, (key, got)
    assert got["audio"] in (True, None), got
    said = [s for s in page().said if "Error" in s or "error" in s]
    assert not said, f"the page's console: {said[:5]}"


def test_the_themes():
    """The second update's first phase - three themes: the art packs in the file match their sources (pack.py --check);
    the file carries the atlas of Crawl tiles and the twelve stone textures and decodes them; each theme builds a
    depth's whole set (the same layers as the drawn one; Pixel crisp at 256, Stone at 512); the heroes have paper-doll
    portraits in Pixel; every kind of thing has an icon in every theme and every spell has one in Pixel; the Theme
    chooser on the title and the one in Settings agree, apply at once (new textures, crisp or not, the party's
    portraits redrawn, the view still drawing) and are kept; the Credits name both sets; and monsters wait while a
    sheet is open"""
    pack = build_module("pack")
    assert pack.build_text() == (GAME / "src" / "js" / "35-packs.js").read_text(encoding="utf-8"), \
        "src/js/35-packs.js is out of date: run  python pack.py  in ClaudeGames/claudemagic"
    assert len(pack.PIXEL) >= 150 and len(pack.STONE) == 12 and all((GAME / "src" / "art" / "pixel" / (k + ".png")).exists() for k in pack.PIXEL)
    assert support.pump(10, until=lambda: ask("CM.art.packs.ready === true")), "the packs never decoded"
    got = ask(f"""(function(){{ const out = {{}}, g = CM.game;
      out.packs = Boolean(CM.packs) && Object.keys(CM.packs.pixel.index).length >= 150 && Object.keys(CM.packs.stone.textures).length === 12 && CM.packs.pixel.size === 32;
      out.decoded = !!CM.art.packs.atlas && CM.art.packs.atlas.width === 512 && Object.keys(CM.art.packs.stone).length === 12 && CM.art.hasLook('pixel') && CM.art.hasLook('stone');
      const theme = CM.THEMES[1], drawn = CM.art.build(theme, 'drawn'), pixel = CM.art.build(theme, 'pixel'), stone = CM.art.build(theme, 'stone');
      const names = Object.keys(drawn.index).sort();
      out.sameLayers = JSON.stringify(names) === JSON.stringify(Object.keys(pixel.index).sort()) && JSON.stringify(names) === JSON.stringify(Object.keys(stone.index).sort()) && names.length > 40;
      out.sizes = drawn.size === 256 && drawn.crisp === false && pixel.size === 256 && pixel.crisp === true && stone.size === 512 && stone.crisp === false && pixel.layers.length === names.length;
      const px = (c, x, y) => c.getContext('2d').getImageData(x, y, 1, 1).data;
      out.painted = px(pixel.layers[pixel.index.wall], 128, 128)[3] === 255 && px(pixel.layers[pixel.index['monster:Orc']], 128, 128)[3] > 0
        && px(stone.layers[stone.index.wall], 256, 256)[3] === 255 && px(stone.layers[stone.index.chest], 256, 300)[3] > 0;
      const d = (cls, look) => CM.art.portrait(cls, 32, look).toDataURL();
      out.dolls = d('Knight', 'pixel') !== d('Knight', 'drawn') && d('Knight', 'pixel') !== d('Mage', 'pixel') && CM.CLASS_ORDER.every(c => CM.art.DOLLS[c] && d(c, 'pixel').length > 200);
      const things = [CM.torch(), CM.lantern(), CM.key(), CM.antidote(), CM.scroll('fire'), CM.wand('fire', 2), {{name: 'Healing Potion', kind: 'heal'}}, {{name: 'Mana Potion', kind: 'mana'}},
        {{name: 'Phoenix Feather', kind: 'revive'}}, ...CM.WEAPONS.map(n => ({{name: n, kind: 'weapon'}})), ...CM.BOWS.map(n => ({{name: n, kind: 'weapon', props: {{bow: true}}}})),
        ...CM.ARMORS.map(n => ({{name: n, kind: 'armor'}})), ...CM.SHIELDS.map(n => ({{name: n, kind: 'shield'}})), ...CM.HELMS.map(n => ({{name: n, kind: 'helm'}})),
        {{name: 'Ring of Wit', kind: 'ring'}}, {{name: 'Amulet of Warding', kind: 'amulet'}}];
      const inked = (c) => {{ const data = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < data.length; i += 4) if (data[i] > 0) n++; return n; }};
      out.icons = ['drawn', 'pixel', 'stone'].every(look => things.every(it => inked(CM.art.itemIcon(it, 24, look)) > 20));
      out.keys = new Set(things.map(it => CM.art.itemKey(it))).size >= 25 && things.every(it => CM.packs.pixel.index[CM.art.itemKey(it)]);
      out.spells = Object.keys(CM.ABILITIES).every(id => CM.art.spellIcon(id, 18, 'pixel') !== null) && CM.art.spellIcon('fireball', 18, 'drawn') === null;
      // the chooser, on the title and in Settings
      CM.store.remove('run'); g.lastRun = null; g.newGame({json.dumps(SEED)});
      const before = CM.renderer.texture, sel = document.querySelector('#look'), sel2 = document.querySelector('#set-look');
      sel.value = 'pixel'; sel.dispatchEvent(new Event('change'));
      out.applied = g.settings.look === 'pixel' && CM.store.get('settings', {{}}).look === 'pixel' && sel2.value === 'pixel' && CM.renderer.crisp === true && CM.renderer.texture !== before;
      const card = document.querySelector('#party canvas');
      out.partyRestyled = card && card.toDataURL() === CM.art.portrait(g.party[0].cls, 44, 'pixel').toDataURL() && card.toDataURL() !== CM.art.portrait(g.party[0].cls, 44, 'drawn').toDataURL();
      sel2.value = 'stone'; sel2.dispatchEvent(new Event('change'));
      out.stoneApplied = g.settings.look === 'stone' && sel.value === 'stone' && CM.renderer.crisp === false;
      document.querySelector('#btn-credits').click();
      const credits = document.querySelector('#credits').textContent;
      out.credits = document.querySelector('#dlg-credits').classList.contains('on') && credits.includes('Dungeon Crawl Stone Soup') && credits.includes('ambientCG');
      // monsters wait while something is open over the dungeon (the frame loop leaves the game alone)
      CM.ui.closeDialogs();
      sel.value = 'pixel'; sel.dispatchEvent(new Event('change'));
      return out; }})()""")
    for key in ("packs", "decoded", "sameLayers", "sizes", "painted", "dolls", "icons", "keys", "spells", "applied", "partyRestyled", "stoneApplied", "credits"):
        assert got[key] is True, (key, got)
    support.pump(0.6)
    px = ask("CM.renderer.pixel(Math.floor(CM.renderer.canvas.width / 2), Math.floor(CM.renderer.canvas.height * 0.85))")
    assert sum(px[:3]) > 20 and ask("CM.renderer.crisp") is True, f"the pixel view is black: {px}"
    run(PARSE)
    still = ask("""(function(){ const g = CM.game; const f = CM.useFloor(g, CM.testFloor(2, ['#######', '#X...M#', '#######']));
      CM.ui.openSheet(0); const key = Object.keys(f.things)[0]; g.wander = 0; return {key, open: CM.ui.dialogOpen()}; })()""")
    assert still["open"], still
    support.pump(1.6)
    assert ask("Object.keys(CM.game.floor.things)[0]") == still["key"] and ask("CM.game.mode") == "explore", "the monsters moved while the sheet was open"
    run("CM.ui.closeDialogs()")
    support.pump(1.6)
    assert ask("Object.keys(CM.game.floor.things)[0]") != still["key"] or ask("CM.game.mode") == "combat", "the monsters didn't stir once the sheet was closed"
    run("const sel = document.querySelector('#look'); sel.value = 'drawn'; sel.dispatchEvent(new Event('change'))")
    assert ask("CM.game.settings.look") == "drawn" and ask("CM.renderer.crisp") is False
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
