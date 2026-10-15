"""The image-only comic rips, built into websites: Housepets!, Hardblush and Jay Naylor's site.

Housepets! strips are named '2008-06-02-when-boredom-strikes.png'; they're re-dated nine years earlier (to fit
ClaudeXP's 2001) and read like the real site: a strip a page with First / Previous / Next / Latest and an archive.
Hardblush is a folder per story plus loose art; Jay Naylor's is his comics, sketchbooks and saved sketch blogs."""
import re
from datetime import date
from urllib.parse import quote

from . import Site, file_response
from .builder import e, file_url, grid, images_in, natural_key, page_number, pager, rel, serve_files, shell, thumb_url
from .rips import resolve

SWF = ".swf"


def _title(stem):
    """'2008-06-02-when-boredom-strikes' -> 'When Boredom Strikes'; '1203054331.onta_onta_peacock' -> 'Onta Peacock'."""
    t = re.sub(r"^\d{4}-\d\d-\d\d-", "", stem)
    t = re.sub(r"^\d{9,}\.?", "", t)
    t = re.sub(r"[_\-.]+", " ", t).strip()
    words = t.split()
    out = [w if w.isupper() and len(w) > 1 else w.capitalize() for w in words]
    for i, w in enumerate(out[1:], 1):
        if w.lower() in ("a", "an", "the", "of", "in", "on", "to", "and", "or", "for", "it", "is"):
            out[i] = w.lower()
    return " ".join(out) or stem


# ---- Housepets! -------------------------------------------------------------------------------------------------

HP_CSS = """body { background: #2B5C8A; margin: 0; font-family: Verdana, Arial, sans-serif; font-size: 12px; color: #222; }
#page { width: 900px; margin: 0 auto; background: #FFFDF5; border-left: 4px solid #F5B335; border-right: 4px solid #F5B335; }
#top { background: #F5B335 url() no-repeat; padding: 14px 20px; }
#top h1 { margin: 0; font-family: 'Comic Sans MS', Verdana; font-size: 34px; color: #FFFFFF; text-shadow: 2px 2px #8A5A00; }
#top span { color: #5A3A00; font-weight: bold; }
#menu { background: #8A5A00; padding: 6px 20px; } #menu a { color: #FFE9B0; font-weight: bold; margin-right: 18px; text-decoration: none; }
#body { padding: 16px 20px 24px; text-align: center; }
.strip img { max-width: 860px; border: 1px solid #C9B98A; }
.nav { margin: 10px 0; font-size: 14px; font-weight: bold; } .nav a { color: #2B5C8A; margin: 0 10px; }
.date { color: #8A7A50; font-size: 11px; } h2 { font-family: 'Comic Sans MS', Verdana; color: #8A5A00; }
.archive td { text-align: left; padding: 2px 8px; } .grid td { font-size: 11px; }
#foot { background: #8A5A00; color: #FFE9B0; text-align: center; padding: 8px; font-size: 10px; }
a { color: #2B5C8A; }"""


class HousePets(Site):
    host, aliases, folder = "www.housepetscomic.com", ("housepets.com", "housepetscomic.net"), "HousePets"
    title, blurb = "Housepets!", "Rick Griffin's webcomic about pets in the suburbs"
    YEARS_BACK = 9

    def _strips(self):
        root = self.root()
        out = []
        for p in sorted((root / "comics").glob("*")):
            m = re.match(r"(\d{4})-(\d\d)-(\d\d)-(.+)$", p.stem)
            if m and p.suffix.lower() in (".png", ".jpg", ".gif"):
                month, day = int(m.group(2)), int(m.group(3))
                d = date(int(m.group(1)) - self.YEARS_BACK, month, 28 if (month, day) == (2, 29) else day)
                out.append((p, d, m.group(4)))
        from .... import clock
        today = clock.now().date()
        return [s for s in out if s[1] <= today]                  # strips 'from the future' aren't up yet

    def _page(self, title, body):
        menu = ('<a href="/">Home</a><a href="/comic/archive/">Archive</a><a href="/cast/">Characters</a>'
                '<a href="/extras/">Fan Art &amp; Extras</a><a href="/about/">About</a>')
        return shell(f"Housepets! - {title}", f'<div id="page"><div id="top"><h1>Housepets!</h1>'
                     '<span>A comic about pets, by Rick Griffin. Updates Monday, Wednesday and Friday!</span></div>'
                     f'<div id="menu">{menu}</div><div id="body">{body}</div><div id="foot">Housepets! is '
                     '&copy; Rick Griffin. All characters are copyright their owners.</div></div>', HP_CSS)

    def handle(self, path, query):
        root = self.root()
        hit = serve_files(root, path)
        if hit is not None:
            return hit
        strips = self._strips()
        if path in ("/", "/index.html"):
            return self._strip_page(strips, len(strips) - 1) if strips else self._page("Home", "<p>No comics yet.</p>")
        if path.rstrip("/") == "/comic/archive":
            rows = "".join(f'<tr><td class="date">{d:%b %d, %Y}</td><td><a href="/comic/{d:%Y-%m-%d}-{slug}/">'
                           f'{e(_title(slug))}</a></td></tr>' for _p, d, slug in reversed(strips))
            return self._page("Archive", f'<h2>Comic Archive</h2><table class="archive" align="center">{rows}</table>')
        m = re.match(r"/comic/(\d{4}-\d\d-\d\d)-(.+?)/?$", path)
        if m:
            for i, (_p, d, slug) in enumerate(strips):
                if f"{d:%Y-%m-%d}" == m.group(1) and slug == m.group(2):
                    return self._strip_page(strips, i)
            return None
        if path.rstrip("/") == "/cast":
            heads = [p for p in images_in(root) if re.search(r"head|edited|portrait", p.stem, re.I)]
            items = [(file_url(rel(root, p)), thumb_url(rel(root, p), 120),
                      e(re.sub(r"(head\d*|headedited|edited|portrait)$", "", p.stem, flags=re.I).capitalize()))
                     for p in heads]
            return self._page("Characters", "<h2>Meet the Cast</h2>" + grid(items, cols=6, width=120))
        if path.rstrip("/") == "/extras":
            extras = [p for p in images_in(root) if not re.search(r"head|edited|portrait|title|banner|vote|favicon",
                                                                  p.stem, re.I)]
            items = [(file_url(rel(root, p)), thumb_url(rel(root, p)), e(_title(p.stem))) for p in extras]
            return self._page("Fan Art & Extras", "<h2>Fan Art, Guest Strips &amp; Extras</h2>" + grid(items, 4))
        if path.rstrip("/") == "/about":
            return self._page("About", "<h2>About Housepets!</h2><p style='text-align:left'>Housepets! follows "
                              "Peanut Butter, Grape, King and the rest of the neighbourhood's pets as they get into "
                              "trouble, hold court in the backyard and try to figure out the humans. New strips go up "
                              "every Monday, Wednesday and Friday.</p>")
        return None

    def _strip_page(self, strips, i):
        p, d, slug = strips[i]
        root = self.root()

        def link(j, label):
            if j < 0 or j >= len(strips) or j == i:
                return f'<span style="color:#AAA">{label}</span>'
            _p, dj, sj = strips[j]
            return f'<a href="/comic/{dj:%Y-%m-%d}-{sj}/">{label}</a>'
        nav = (f'<div class="nav">{link(0, "&laquo; First")}{link(i - 1, "&lsaquo; Previous")}'
               f'{link(i + 1, "Next &rsaquo;")}{link(len(strips) - 1, "Latest &raquo;")}</div>')
        return self._page(_title(slug), f'<h2>{e(_title(slug))}</h2><div class="date">{d:%A, %B %d, %Y}</div>{nav}'
                          f'<div class="strip"><img src="{file_url(rel(root, p))}"></div>{nav}')


# ---- Hardblush -------------------------------------------------------------------------------------------------

HB_CSS = """body { background: #1A0B12; color: #F2D9E2; font-family: Verdana, Arial; font-size: 12px; margin: 0; }
#page { width: 920px; margin: 0 auto; background: #2A121D; border: 1px solid #6B2340; }
#top { background: linear-gradient(#7A1F45, #3A0E20); padding: 16px 22px; }
#top h1 { margin: 0; font-family: Georgia, serif; font-size: 36px; color: #FFC4DA; letter-spacing: 2px; }
#top span { color: #E890B4; } #menu { background: #4A1529; padding: 6px 22px; }
#menu a { color: #FFC4DA; margin-right: 18px; font-weight: bold; text-decoration: none; }
#body { padding: 16px 22px; } h2 { font-family: Georgia, serif; color: #FF9FC4; }
a { color: #FF9FC4; } .grid td { font-size: 11px; color: #E8B8CB; } .pager { margin: 12px 0; text-align: center; }
.reader { text-align: center; } .reader img { max-width: 880px; border: 1px solid #6B2340; }
.nav { text-align: center; margin: 10px; font-weight: bold; } .nav a { margin: 0 12px; }
#foot { text-align: center; color: #9A6178; font-size: 10px; padding: 10px; }"""


class Hardblush(Site):
    host, folder = "www.hardblush.com", "Hardblush"
    title, blurb = "Hardblush", "Onta's adult furry comics and art"
    PER_PAGE = 30

    def _base(self):
        root = self.root()
        inner = [d for d in root.iterdir() if d.is_dir()]
        return inner[0] if len(inner) == 1 else root            # the rip is one 'All_HB_...' folder

    def _stories(self):
        base = self._base()
        skip = {"blog", "flash", "randomz"}
        return [d for d in sorted(base.iterdir(), key=lambda d: natural_key(d.name))
                if d.is_dir() and d.name.lower() not in skip and images_in(d, deep=True)]

    def _page(self, title, body):
        menu = ('<a href="/">Home</a><a href="/comics/">Comics</a><a href="/gallery/">Gallery</a>'
                '<a href="/blog/">Sketch Blog</a><a href="/flash/">Flash</a>')
        return shell(f"Hardblush :: {title}", f'<div id="page"><div id="top"><h1>HARDBLUSH</h1><span>adult comics '
                     f'&amp; art by Onta &mdash; 18+ only</span></div><div id="menu">{menu}</div><div id="body">{body}'
                     '</div><div id="foot">All artwork &copy; its artists. You must be 18 or older to view this site.'
                     '</div></div>', HB_CSS)

    def handle(self, path, query):
        base = self._base()
        hit = serve_files(base, path)
        if hit is not None:
            return hit
        stories = self._stories()
        if path in ("/", "/index.html"):
            covers = [(f"/comics/{quote(d.name)}/", thumb_url(rel(base, images_in(d, deep=True)[0]), 150), e(d.name))
                      for d in stories[-10:]]
            return self._page("Home", "<h2>Welcome to Hardblush!</h2><p>Adult furry comics, pin-ups and sketches. "
                              "Pick a story below or browse the gallery.</p><h2>Latest Comics</h2>" + grid(covers, 5, 150))
        if path.rstrip("/") == "/comics":
            covers = [(f"/comics/{quote(d.name)}/", thumb_url(rel(base, images_in(d, deep=True)[0]), 150),
                       f"{e(d.name)}<br><small>{len(images_in(d, deep=True))} pages</small>") for d in stories]
            return self._page("Comics", "<h2>All Comics</h2>" + grid(covers, 5, 150))
        m = re.match(r"/comics/([^/]+)/?(\d*)/?$", path)
        if m:
            d = next((s for s in stories if s.name == m.group(1)), None)
            if d is None:
                return None
            pages = images_in(d, deep=True)
            n = max(1, min(len(pages), int(m.group(2) or 1)))
            href = f"/comics/{quote(d.name)}/"
            nav = ('<div class="nav">' + (f'<a href="{href}1">&laquo; First</a><a href="{href}{n - 1}">&lsaquo; Prev</a>'
                   if n > 1 else "") + f" Page {n} of {len(pages)} " +
                   (f'<a href="{href}{n + 1}">Next &rsaquo;</a><a href="{href}{len(pages)}">Last &raquo;</a>'
                    if n < len(pages) else "") + "</div>")
            return self._page(d.name, f"<h2>{e(d.name)}</h2>{nav}<div class='reader'><a href='{href}{min(n + 1, len(pages))}'>"
                              f"<img src='{file_url(rel(base, pages[n - 1]))}'></a></div>{nav}")
        for section, folder_name, title in (("/gallery", None, "Gallery"), ("/blog", "Blog", "Sketch Blog"),
                                             ("/randomz", "Randomz", "Randomz")):
            if path.rstrip("/") == section:
                folder = base if folder_name is None else base / folder_name
                pics = images_in(folder) if folder.is_dir() else []
                page = page_number(query)
                pages = max(1, -(-len(pics) // self.PER_PAGE))
                shown = pics[(page - 1) * self.PER_PAGE: page * self.PER_PAGE]
                items = [(file_url(rel(base, p)), thumb_url(rel(base, p), 150), e(_title(p.stem))[:40]) for p in shown]
                return self._page(title, f"<h2>{title}</h2>{pager(section + '/', page, pages)}{grid(items, 5, 150)}"
                                  f"{pager(section + '/', page, pages)}")
        if path.rstrip("/") == "/flash":
            folder = base / "Flash"
            movies = sorted(folder.glob("*.swf"), key=lambda p: natural_key(p.name)) if folder.is_dir() else []
            rows = "".join(f'<li><a href="{file_url(rel(base, p))}">{e(_title(p.stem))}</a></li>' for p in movies)
            return self._page("Flash", "<h2>Flash Animations</h2><p>Click one to play it in the Macromedia Flash "
                              f"Player.</p><ul>{rows}</ul>")
        return None


# ---- Jay Naylor --------------------------------------------------------------------------------------------------

JN_CSS = """body { background: #FFFFFF; font-family: Arial, sans-serif; font-size: 13px; color: #222; margin: 0; }
#top { background: #000; color: #FFF; padding: 18px 30px; } #top h1 { margin: 0; font-size: 30px; letter-spacing: 3px; }
#top span { color: #C33; font-weight: bold; } #menu { background: #C33; padding: 6px 30px; }
#menu a { color: #FFF; margin-right: 18px; font-weight: bold; text-decoration: none; } #body { padding: 16px 30px; }
h2 { color: #C33; border-bottom: 1px solid #DDD; } .grid td { font-size: 11px; } .reader { text-align: center; }
.reader img { max-width: 900px; } .nav { text-align: center; margin: 10px; font-weight: bold; } .nav a { margin: 0 12px; }
a { color: #C33; }"""


class JayNaylor(Site):
    host, folder = "www.jaynaylor.com", "Jay Naylor"
    title, blurb = "Jay Naylor", "comics, sketchbooks and the sketch blog"

    def _sections(self):
        """[(slug, title, folder, kind)]: kind 'comic' (images), 'blog' (saved HTML), 'book' (images)."""
        root = self.root()
        out = []
        for rip in sorted(d for d in root.iterdir() if d.is_dir()):
            inner = [d for d in rip.iterdir() if d.is_dir()]
            if "catalog" in rip.name.lower():
                for comic in sorted(inner, key=lambda d: natural_key(d.name)):
                    title = re.sub(r"^Jay Naylor - ", "", comic.name)
                    out.append((re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"), title, comic, "comic"))
                continue
            folder = inner[0] if len(inner) == 1 else rip
            title = re.sub(r"^\[fxa\]\s*", "", folder.name, flags=re.I)
            kind = "blog" if any(folder.glob("*.html")) else "book"
            out.append((re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"), title, folder, kind))
        return out

    def _page(self, title, body):
        return shell(f"JayNaylor.com - {title}", '<div id="top"><h1>JAY NAYLOR</h1><span>comics &bull; sketchbooks '
                     '&bull; adult furry art</span></div><div id="menu"><a href="/">Home</a><a href="/comics/">Comics</a>'
                     f'<a href="/sketchbooks/">Sketchbooks &amp; Blog</a></div><div id="body">{body}</div>', JN_CSS)

    def handle(self, path, query):
        root = self.root()
        sections = self._sections()
        hit = serve_files(root, path)
        if hit is not None:
            return hit
        comics = [s for s in sections if s[3] == "comic"]
        books = [s for s in sections if s[3] != "comic"]

        def cover(s):
            pics = images_in(s[2], deep=True)
            return (f"/{'comics' if s[3] == 'comic' else 'sketchbooks'}/{s[0]}/",
                    thumb_url(rel(root, pics[0]), 150) if pics else "", e(s[1]))
        if path in ("/", "/index.html"):
            return self._page("Home", "<h2>Welcome!</h2><p>The official site of Jay Naylor: read the comics, flip "
                              "through the sketchbooks and catch up on the sketch blog.</p><h2>Comics</h2>"
                              + grid([cover(s) for s in comics], 5, 150) + "<h2>Sketchbooks &amp; Blog</h2>"
                              + grid([cover(s) for s in books], 5, 150))
        if path.rstrip("/") == "/comics":
            return self._page("Comics", "<h2>Comics</h2>" + grid([cover(s) for s in comics], 5, 150))
        if path.rstrip("/") == "/sketchbooks":
            return self._page("Sketchbooks", "<h2>Sketchbooks &amp; Blog</h2>" + grid([cover(s) for s in books], 5, 150))
        m = re.match(r"/(comics|sketchbooks)/([^/]+)/(.*)$", path)
        if m:
            s = next((x for x in sections if x[0] == m.group(2)), None)
            if s is None:
                return None
            if s[3] == "blog":                                   # a saved copy of the blog: its own pages
                target = resolve(s[2], "/" + m.group(3), query)
                return file_response(target) if target else None
            pics = images_in(s[2], deep=True)
            n = int(m.group(3).strip("/") or 1) if m.group(3).strip("/").isdigit() else 1
            n = max(1, min(len(pics), n))
            href = f"/{m.group(1)}/{s[0]}/"
            nav = ('<div class="nav">' + (f'<a href="{href}{n - 1}">&lsaquo; Prev</a>' if n > 1 else "")
                   + f" {n} / {len(pics)} " + (f'<a href="{href}{n + 1}">Next &rsaquo;</a>' if n < len(pics) else "")
                   + "</div>")
            return self._page(s[1], f"<h2>{e(s[1])}</h2>{nav}<div class='reader'><a href='{href}{min(n + 1, len(pics))}'>"
                              f"<img src='{file_url(rel(root, pics[n - 1]))}'></a></div>{nav}")
        return None
