"""Kiwix's content: the books in E:\\Kiwix (ZIM files), what can be downloaded, and downloading it.

CATALOG lists offline packages that fit ClaudeXP's budget (BUDGET, 15 GB for everything together). The newest file
of each family is looked up on download.kiwix.org when you open Get Content (with the size the server reports); if
that can't be reached, the last known file name and size are used. Downloads go through llm_setup's Installer
(resume, retries, size check) with the SHA-256 that Kiwix publishes beside each file.
"""
import re
import shutil
import urllib.request
from pathlib import Path

from ...llm_setup import Installer, fmt

BUDGET = 15 * 1000 ** 3
SERVER = "https://download.kiwix.org/zim/"
# (key = file name prefix, folder on the server, title, what it is, last known file, its size, recommended?)
CATALOG = [
    ("wikipedia_en_top_maxi", "wikipedia", "Wikipedia - the 50,000 most-read articles, with pictures",
     "The articles people read most, complete, with images.", "wikipedia_en_top_maxi_2026-09.zim",
     6991081681, True),
    ("wikipedia_en_top1m_mini", "wikipedia", "Wikipedia - the top 1 million articles, introductions",
     "A million articles: each one's introduction and infobox, no pictures.", "wikipedia_en_top1m_mini_2026-04.zim",
     3022411034, True),
    ("wikipedia_en-simple_all_maxi", "wikipedia", "Simple English Wikipedia, with pictures",
     "Every Simple English article - plain language, complete, with images.",
     "wikipedia_en-simple_all_maxi_2026-09.zim", 3121060947, True),
    ("wikipedia_en_all_mini", "wikipedia", "Wikipedia - every article, introductions only",
     "All 6.9 million English articles, introductions only. Takes almost the whole budget on its own.",
     "wikipedia_en_all_mini_2026-09.zim", 14386799064, False),
    ("wikipedia_en_top_nopic", "wikipedia", "Wikipedia - the 50,000 most-read articles, no pictures",
     "The same articles as 'with pictures', text only.", "wikipedia_en_top_nopic_2026-09.zim", 2745850723, False),
    ("wikipedia_en-simple_all_nopic", "wikipedia", "Simple English Wikipedia, no pictures",
     "Every Simple English article, text only.", "wikipedia_en-simple_all_nopic_2026-09.zim", 1094936257, False),
    ("wikipedia_en_100", "wikipedia", "Wikipedia - 100 essential articles",
     "A tiny starter: 100 of the most important articles, with pictures.", "wikipedia_en_100_2026-08.zim",
     333429922, False),
]


def folder():
    from ...explorer.vfs import local_storage
    path = local_storage() / "Kiwix"
    path.mkdir(parents=True, exist_ok=True)
    return path


def books():
    """The ZIM files in E:\\Kiwix (finished ones only)."""
    return sorted(p for p in folder().glob("*.zim") if p.is_file())


def used():
    return sum(p.stat().st_size for p in books())


def installed_family(prefix):
    return next((p for p in books() if re.fullmatch(re.escape(prefix) + r"_\d{4}-\d{2}\.zim", p.name)), None)


_listings = {}


def _listing(directory, timeout):
    """The server's file list for a folder (fetched once per session)."""
    if directory not in _listings:
        with urllib.request.urlopen(urllib.request.Request(SERVER + directory + "/", headers={
                "User-Agent": "ClaudeXP-Kiwix/1.0"}), timeout=timeout) as r:
            _listings[directory] = r.read().decode("utf-8", "replace")
    return _listings[directory]


def latest(prefix, directory, known_file, known_size, timeout=12):
    """(file name, size, url) of the newest file of a family on the server (or the last known one)."""
    try:
        page = _listing(directory, timeout)
        names = sorted(set(re.findall(r'href="(' + re.escape(prefix) + r'_\d{4}-\d{2}\.zim)"', page)))
        if names:
            name = names[-1]
            url = SERVER + directory + "/" + name
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ClaudeXP-Kiwix/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                size = int(r.headers.get("Content-Length") or 0)
            return name, size or known_size, url
    except Exception:
        pass
    return known_file, known_size, SERVER + directory + "/" + known_file


class KiwixInstaller(Installer):
    """llm_setup's downloader, pointed at E:\\Kiwix. Items are made on the fly: {key, title, files: [one file]}."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = {}

    def add(self, key, title, name, url, size):
        self.items[key] = {"key": key, "title": title, "kind": "book",
                           "files": [{"name": name, "url": url, "size": size, "sha256": ""}]}
        return self.items[key]

    def item(self, key):
        return self.items[key]

    def target_dir(self, it):
        return folder()

    def installed(self, it):
        f = it["files"][0]
        t = folder() / f["name"]
        return t.is_file() and (not f["size"] or t.stat().st_size == f["size"])

    def _download_item(self, it, urls):
        f = it["files"][0]
        url = urls.get(f["name"]) or f["url"]
        if not f["sha256"]:                     # Kiwix publishes the checksum beside each file
            try:
                with urllib.request.urlopen(urllib.request.Request(url + ".sha256", headers={
                        "User-Agent": "ClaudeXP-Kiwix/1.0"}), timeout=20) as r:
                    f["sha256"] = r.read().decode("ascii", "replace").split()[0].strip().lower()
            except Exception:
                f["sha256"] = ""
        super()._download_item(it, urls)

    def _finish(self, it):
        pass


def bring_in(src):
    """A .zim you already have: linked into E:\\Kiwix if on the same drive, else copied. -> destination."""
    import os
    src = Path(src)
    dest = folder() / src.name
    if dest.exists():
        return dest
    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)
    return dest


__all__ = ["BUDGET", "CATALOG", "KiwixInstaller", "books", "bring_in", "fmt", "folder", "installed_family",
           "latest", "used"]
