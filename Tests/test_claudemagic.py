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
    """Every floor, three seeds deep: the ladder (or the Lich King) can be reached, chests and monsters are as many
    as the depth says, the maze grows with the depth, and the same seed lays the same floor"""
    rows = ask("""(function(){ const out = [];
      for (const seed of ["ember-crypt-417", "iron-oath-9", "x"]) for (let n = 1; n <= 20; n++) {
        const f = CM.makeFloor(n, seed), t = Object.values(f.things);
        out.push({n, seed, size: f.grid.length, ok: CM.solvable(f), chests: t.filter(x => x.type === 'chest').length,
          groups: t.filter(x => x.type === 'monsters').length, goal: t.some(x => x.type === (n === 20 ? 'boss' : 'ladder')),
          start: f.grid[1][1] === 0 && f.pos[0] === 1 && f.pos[1] === 1, same: JSON.stringify(CM.makeFloor(n, seed)) === JSON.stringify(f)});
      }
      out.push({differ: JSON.stringify(CM.makeFloor(1, 'a').grid) !== JSON.stringify(CM.makeFloor(1, 'b').grid)});
      return out; })()""")
    assert rows.pop()["differ"], "two seeds gave the same floor"
    for r in rows:
        where = f"floor {r['n']} of {r['seed']}"
        assert r["ok"] and r["goal"] and r["start"], f"{where} can't be finished"
        assert r["same"], f"{where} isn't the same twice"
        assert r["size"] == min(17 + (r["n"] // 4) * 2, 27), where
        assert r["chests"] == 3 + r["n"] // 4 and r["groups"] == 5 + r["n"] // 2, (where, r["chests"], r["groups"])


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
    assert got["stock"] == 9, got


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
