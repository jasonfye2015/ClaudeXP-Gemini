"""His notebook: what's written when, and kept - across nights, across deaths."""
import tempfile

from hollowoak.game import moods as M
from hollowoak.game import notes as N
from hollowoak.game.records import Records


def test_the_pages_hang_together():
    assert set(N.SECTIONS) == {v[0] for v in N.PAGES.values()}
    assert len(N.SUITORS) == 7 and all(s in N.PAGES and N.PAGES[s][0] == "Her guests" for s in N.SUITORS)
    for ids in list(N.NODES.values()):
        assert all(i in N.PAGES for i in ids)


def test_what_writes_them():
    assert N.unlock_for(("her", "glimpse")) == ["edge"] and N.unlock_for(("her", "bite")) == ["bite"]
    assert N.unlock_for(("crawler", 1)) == ["small_ones"] and N.unlock_for(("fall", 3.0)) == []
    assert "name" in N.for_line("I am Ysmeine, the Weaver Below.")
    assert "fire" in N.for_line("Fire. It is the one thing here that frightens me.")
    assert "hidden" in N.for_line("It is what I am called. It is not what I am.")
    assert N.for_node("hername") == ["name", "hidden"]
    m = M.Moods()
    assert N.for_moods(m) == []
    m.hunger, m.suspicion = 70, 60
    assert N.for_moods(m) == ["hunger_tell", "suspicion_tell"]


def test_kept_across_nights():
    with tempfile.TemporaryDirectory() as d:
        r = Records(d)
        assert r.note("name") is True and r.note("name") is False
        r.note("orrin")
        again = Records(d)
        assert set(again.notes) == {"name", "orrin"}
