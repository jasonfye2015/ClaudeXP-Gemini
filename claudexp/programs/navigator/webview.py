"""Netscape's second engine: a real web engine (Qt WebEngine) for the furry web's sites (sites/), which are real
websites the simple 2001 engine can't draw. It only ever talks to ClaudeXP's own server on 127.0.0.1: every other
request is blocked, and following a link off the site hands the address back to Netscape, which decides what's
there (another ripped site, or the made-up 2001 web)."""
from PySide6.QtCore import QTimer, QUrl, Signal
from PySide6.QtWebEngineCore import (QWebEnginePage, QWebEngineProfile, QWebEngineSettings,
                                     QWebEngineUrlRequestInterceptor)
from PySide6.QtWebEngineWidgets import QWebEngineView

from . import sites

_profile = None


class _OfflineOnly(QWebEngineUrlRequestInterceptor):
    """Pictures and scripts may only come from ClaudeXP's server (old ad banners and counters stay blank)."""

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if sites.is_local(url) or url.startswith(("data:", "blob:", "about:")):
            return
        if sites.site_for(url) is not None:                 # an absolute link to one of our sites
            info.redirect(QUrl(sites.local_url(url)))
            return
        info.block(True)


def profile():
    global _profile
    if _profile is None:
        from PySide6.QtWidgets import QApplication
        _profile = QWebEngineProfile(QApplication.instance())      # off the record: nothing kept on disk
        _profile.setHttpUserAgent("Mozilla/4.79 [en] (Windows NT 5.1; U)")
        _profile.interceptor = _OfflineOnly(_profile)
        _profile.setUrlRequestInterceptor(_profile.interceptor)
    return _profile


class _Page(QWebEnginePage):
    def __init__(self, view):
        super().__init__(profile(), view)
        self.view = view

    def acceptNavigationRequest(self, url, kind, main_frame):
        if not main_frame or kind == QWebEnginePage.NavigationType.NavigationTypeRedirect:
            return True                                      # (a site's own redirect, e.g. after a favourite)
        target = url.toString()
        if self.view.expected and target == self.view.expected:
            self.view.expected = ""
            return True                                      # the load Netscape itself asked for
        logical = sites.logical_url(target)
        # Netscape takes it from here (history, address bar); not from inside this call: starting a new load while
        # the engine is still deciding about this one crashes it
        if logical.lower().endswith(".swf"):
            QTimer.singleShot(0, lambda: self.view.flash_requested.emit(target))
        else:
            QTimer.singleShot(0, lambda: self.view.link_followed.emit(logical))
        return False

    def createWindow(self, _kind):
        return self                                          # 'open in new window' links open in place

    def javaScriptConsoleMessage(self, *args):
        pass


class SiteView(QWebEngineView):
    link_followed = Signal(str)        # a link was clicked: the address it goes to (as Netscape shows it)
    flash_requested = Signal(str)      # a .swf was clicked: its (local) address

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expected = ""
        self.setPage(_Page(self))
        s = self.settings()
        s.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        s.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)

    def open(self, url):
        """Show a furry-web address (http://www.furaffinity.net/...)."""
        local = QUrl(sites.local_url(url))
        self.expected = local.toString()          # (compared the way the engine will report it back)
        self.load(local)
