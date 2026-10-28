"""The Manual stays whole and current: every link and picture leads somewhere, every chapter is in the contents,
every screenshot is used and listed, and chapter 15 (every program) matches the computers' registries as they are
now - add or rename a program and this says to regenerate it."""
import re

import support

MANUAL = support.TIMELINE / "Manual"
LINK = re.compile(r"\]\(([^)\s]+)\)")


def _pages():
    return sorted(MANUAL.glob("*.md"))


def test_links_and_pictures_lead_somewhere():
    """Every link and picture in the Manual leads to a file that's there"""
    broken = []
    for page in _pages():
        for target in LINK.findall(page.read_text(encoding="utf-8")):
            if target.startswith(("http:", "https:", "mailto:", "#")):
                continue
            if target.startswith(("..", "/")) or ":" in target:
                broken.append(f"{page.name}: {target} (the Manual viewer only opens pages in the Manual folder)")
            elif not (MANUAL / target.split("#")[0]).exists():
                broken.append(f"{page.name}: {target}")
    assert not broken, "\n".join(broken)


def test_every_chapter_is_in_the_contents():
    """Every chapter is listed in the contents (index.md)"""
    index = (MANUAL / "index.md").read_text(encoding="utf-8")
    listed = set(LINK.findall(index))
    missing = [p.name for p in _pages() if p.name != "index.md" and p.name not in listed]
    assert not missing, "not in index.md: " + ", ".join(missing)


def test_every_screenshot_is_used_and_listed():
    """Every screenshot in Manual/images is used by a page and listed in its README"""
    text = "".join(p.read_text(encoding="utf-8") for p in _pages())
    readme = (MANUAL / "images" / "README.md").read_text(encoding="utf-8")
    pictures = [p.name for p in (MANUAL / "images").glob("*.png")]
    unused = [n for n in pictures if f"images/{n}" not in text]
    unlisted = [n for n in pictures if f"`{n}`" not in readme]
    assert not unused and not unlisted, f"not used: {unused}; not in images/README.md: {unlisted}"


def test_program_list_is_current():
    """Chapter 15 lists the programs the three computers have now (python -m manual.catalog from ClaudeApps redoes it)"""
    from manual import catalog
    fresh = support.scratch("manual") / "15-programs.md"
    catalog.main(["--out", str(fresh)])

    def same(text):
        return re.sub(r"registries on \d{1,2} \w+ \d{4}", "registries on <date>", text).strip()
    assert same(fresh.read_text(encoding="utf-8")) == same((MANUAL / "15-programs.md").read_text(encoding="utf-8")), \
        "Manual/15-programs.md is out of date: run  python -m manual.catalog  in ClaudeApps"


if __name__ == "__main__":
    support.main(globals())
