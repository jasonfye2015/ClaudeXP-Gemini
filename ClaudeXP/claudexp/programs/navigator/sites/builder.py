"""Pieces the built sites share: finding pictures, thumbnails, picture URLs, a page shell, a pager, a grid."""
import hashlib
import html
import re
from pathlib import Path
from urllib.parse import quote

from ....paths import DATA
from . import Response

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
THUMBS = DATA / "web_thumbs"
e = html.escape


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(s))]


def images_in(folder, deep=False):
    """Pictures in a folder (optionally its sub-folders too), in natural order."""
    folder = Path(folder)
    found = folder.rglob("*") if deep else folder.iterdir()
    return sorted((p for p in found if p.is_file() and p.suffix.lower() in IMAGE_EXTS), key=lambda p: natural_key(p))


def rel(root, path):
    return Path(path).relative_to(root).as_posix()


def file_url(relpath):
    """The site-relative URL of a file in the site's folder (served by Site.handle as /files/...)."""
    return "/files/" + quote(relpath)


def thumb_url(relpath, width=160):
    return f"/thumbs/{width}/" + quote(relpath)


def thumbnail(path, width):
    """A JPEG of the picture scaled to width (cached in data/web_thumbs) -> Response, or None."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage
    path = Path(path)
    if not path.is_file():
        return None
    width = max(40, min(600, int(width)))
    st = path.stat()
    key = hashlib.sha1(f"{path}|{st.st_size}|{int(st.st_mtime)}|{width}".encode()).hexdigest()
    cached = THUMBS / key[:2] / f"{key}.jpg"
    if cached.is_file():
        return Response(cached.read_bytes(), "image/jpeg")
    img = QImage(str(path))
    if img.isNull():
        return None
    if img.width() > width:
        img = img.scaledToWidth(width, Qt.SmoothTransformation)
    if img.height() > width * 2:
        img = img.copy(0, 0, img.width(), width * 2)        # very tall strips: just the top
    cached.parent.mkdir(parents=True, exist_ok=True)
    img.convertToFormat(QImage.Format_RGB32).save(str(cached), "JPG", 85)
    return Response(cached.read_bytes(), "image/jpeg")


def serve_files(site_root, path):
    """/files/<rel> and /thumbs/<w>/<rel> for any built site -> Response or None."""
    from . import file_response
    if path.startswith("/files/"):
        target = (site_root / path[len("/files/"):]).resolve()
        if site_root.resolve() in target.parents:
            return file_response(target)
        return None
    m = re.match(r"/thumbs/(\d+)/(.+)$", path)
    if m:
        target = (site_root / m.group(2)).resolve()
        if site_root.resolve() in target.parents:
            return thumbnail(target, int(m.group(1)))
    return None


def pager(base, page, pages, sep="&"):
    """'« Prev  1 2 3 ... Next »' linking to base + 'page=N'."""
    if pages <= 1:
        return ""
    join = "&" if "?" in base else "?"
    items = []
    if page > 1:
        items.append(f'<a href="{base}{join}page={page - 1}">&laquo; Prev</a>')
    for n in range(1, pages + 1):
        if n in (1, pages) or abs(n - page) <= 3:
            items.append(f"<b>{n}</b>" if n == page else f'<a href="{base}{join}page={n}">{n}</a>')
        elif items[-1] != "...":
            items.append("...")
    if page < pages:
        items.append(f'<a href="{base}{join}page={page + 1}">Next &raquo;</a>')
    return '<div class="pager">' + " &nbsp; ".join(items) + "</div>"


def page_number(query):
    m = re.search(r"(?:^|&)page=(\d+)", query or "")
    return max(1, int(m.group(1))) if m else 1


def grid(items, cols=5, width=160):
    """items: [(link, thumb_url, caption_html)] -> a table of thumbnails."""
    cells = [f'<td class="cell" valign="top" align="center"><a href="{link}"><img src="{thumb}" '
             f'style="max-width:{width}px;max-height:{width}px"></a><br>{cap}</td>' for link, thumb, cap in items]
    rows = ["<tr>" + "".join(cells[i:i + cols]) + "</tr>" for i in range(0, len(cells), cols)]
    return '<table class="grid" cellspacing="6">' + "".join(rows) + "</table>"


def shell(title, body, css, head=""):
    return (f"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">\n<html><head>"
            f"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"><title>{e(title)}</title>"
            f"<style>{css}</style>{head}</head><body>{body}</body></html>")
