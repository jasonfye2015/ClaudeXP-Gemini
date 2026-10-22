"""The Web of October 2025 where ClaudeXP's pages say 2001: MSN as Microsoft Edge's start page (Bing search, the
Microsoft 365 links, that autumn's stories), the fandom and favourite links of the day, and the swaps the Outlook.com
and Fur Affinity pages get on their way out."""
import functools

from . import clock

FANDOM_LINKS = [("http://www.furnet.irc/", "FurNet IRC Network - still here"), ("http://www.pawprintsmuck.com/", "PawPrints MUCK"),
                ("http://www.furrycities.com/", "FurryCities - furry homepages"),
                ("http://www.furaffinity.net/", "Fur Affinity"),
                ("http://bsky.app/", "Bluesky - the furry feeds"),
                ("http://www.furryconventions.com/", "Convention listings 2025-2026"),
                ("http://t.me/", "Telegram furry groups")]
COOL_SITES = [("http://www.youtube.com/", "YouTube"), ("http://www.reddit.com/", "Reddit"), ("http://bsky.app/", "Bluesky"),
              ("http://www.facebook.com/", "Facebook"), ("http://www.twitch.tv/", "Twitch"), ("http://xkcd.com/", "xkcd"),
              ("http://en.wikipedia.org/", "Wikipedia")]
NEWS = [("windows10_end", "Windows 10 reached the end of support on October 14: time to move to Windows 11"),
        ("windows11_25h2", "Windows 11 version 25H2 rolls out with a leaner Start menu and Copilot everywhere"),
        ("iphone17", "Apple's iPhone 17 and the ultra-thin iPhone Air arrive in stores"),
        ("battlefield6", "Battlefield 6 launches to record player counts"),
        ("switch2", "Nintendo Switch 2 passes ten million sold in its first four months"),
        ("kpop_demon_hunters", "KPop Demon Hunters becomes Netflix's most-watched film ever"),
        ("pokemon_za", "Pokemon Legends: Z-A is out on Switch and Switch 2")]
SEARCHES = [("furry+conventions+2026", "furry conventions 2026"), ("windows+11+25h2", "Windows 11 25H2"),
            ("iphone+17+review", "iPhone 17 review"), ("battlefield+6", "Battlefield 6")]
WEB_SWAPS = (("2001", "2025"), ("Windows XP", "Windows 11"), ("MSN Hotmail", "Outlook.com"),
             ("Get MSN Messenger", "Get Microsoft Teams"), ("MSN Messenger", "Microsoft Teams"),
             ("Internet Explorer 6", "Microsoft Edge"),
             ('<span class="logo">msn<span>.</span> Hotmail</span>', '<span class="logo">Outlook</span>'),
             ("MSN Home", "Microsoft"), ("Hotmail", "Outlook.com"))
OUTLOOK_CSS = """
body { margin: 0; background: #FFFFFF; font-family: 'Segoe UI Variable Text', 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #242424; }
td, th, div, li, p, form, select, input { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
a { color: #0F6CBD; text-decoration: none; } a:hover { text-decoration: underline; } a:visited { color: #0F6CBD; }
.top { background: #0F6CBD; color: #FFFFFF; }
.logo { font-family: 'Segoe UI', Arial; font-size: 18px; font-weight: 600; color: #FFFFFF; }
.logo span { color: #FFFFFF; font-size: 12px; vertical-align: super; }
.tabs td { padding: 8px 14px; font-size: 13px; }
.tab { background: #0F6CBD; } .tab a { color: #FFFFFF; }
.tab-on { background: #FFFFFF; border-radius: 6px 6px 0 0; } .tab-on a { color: #0F6CBD; font-weight: 600; }
.bar { background: #FAFAFA; border-bottom: 1px solid #E0E0E0; }
.btn { font-family: 'Segoe UI'; font-size: 13px; background: #FFFFFF; border: 1px solid #D1D1D1; border-radius: 4px; padding: 5px 12px; }
.folders { background: #F5F5F5; border-right: 1px solid #E0E0E0; }
.folders a { color: #242424; }
.list th { background: #FFFFFF; color: #616161; text-align: left; font-size: 12px; padding: 8px; border-bottom: 1px solid #E0E0E0; }
.list td { padding: 8px; border-bottom: 1px solid #F0F0F0; font-size: 13px; }
.unread td { font-weight: 600; background: #FFFFFF; }
.read td { background: #FFFFFF; color: #616161; }
.ad { background: #F5F5F5; border: 1px solid #E0E0E0; border-radius: 8px; font-size: 12px; padding: 10px; }
.meter { width: 120px; height: 6px; border: none; border-radius: 3px; background: #E0E0E0; }
.meter div { height: 6px; border-radius: 3px; background: #0F6CBD; }
.foot { color: #616161; font-size: 12px; }
.msghead td { font-size: 13px; padding: 3px 6px; }
pre.body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; white-space: pre-wrap; margin: 12px; }
input.text, textarea { font-family: 'Segoe UI', Arial; font-size: 13px; border: 1px solid #D1D1D1; border-radius: 4px; padding: 4px; }
"""


def swap(text):
    for old, new in WEB_SWAPS:
        text = text.replace(old, new)
    return text


def wrap(owner, attr):
    """Replace owner.attr with a version whose string result has its years swapped."""
    original = getattr(owner, attr)

    @functools.wraps(original)
    def wrapped(*args, **kwargs):
        out = original(*args, **kwargs)
        return swap(out) if isinstance(out, str) else out
    setattr(owner, attr, wrapped)


def msn_page(knowledge):
    """MSN in the autumn of 2025: Microsoft Edge's start page."""
    from claudexp.programs.navigator import web
    now = clock.now()
    furry_web, fa_buddies, buddies = web._home_links(knowledge)
    fandom = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in FANDOM_LINKS)
    cool = " &middot;\n".join(f'<a href="{u}">{t}</a>' for u, t in COOL_SITES)
    tabs = " &nbsp;&nbsp;&middot;&nbsp;&nbsp; ".join(f'<a href="http://{h}/" style="color:#242424">{t}</a>' for h, t in (
        ("outlook.live.com", "Outlook"), ("www.office.com", "Microsoft 365"), ("onedrive.live.com", "OneDrive"),
        ("www.bing.com", "Bing"), ("copilot.microsoft.com", "Copilot"), ("www.xbox.com", "Xbox")))
    news = "".join(f'<li style="margin:6px 0"><a href="http://www.msn.com/en-us/news/{slug}/">{t}</a></li>'
                   for slug, t in NEWS)
    q = web.MSN_SEARCH_URL
    searches = " &middot;\n".join(f'<a href="{q}{s}">{t}</a>' for s, t in SEARCHES)
    try:
        from .programs.widgets import weather_now
        temp, cond = weather_now()
    except Exception:
        temp, cond = 52, "Partly Cloudy"
    return f"""<html><head><title>MSN</title>
<style>
body {{ margin: 0; background: #F3F3F3; font-family: 'Segoe UI Variable Text', 'Segoe UI', Arial, sans-serif; color: #242424; }}
a {{ color: #0F6CBD; text-decoration: none; }} a:hover {{ text-decoration: underline; }}
.card {{ background: #FFFFFF; border-radius: 8px; padding: 14px 18px; margin: 0 0 14px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }}
h3 {{ margin: 0 0 8px 0; font-size: 15px; }}
ul {{ margin: 0; padding-left: 18px; }} li {{ margin: 4px 0; }}
.small {{ color: #616161; font-size: 12px; }}
</style></head><body>
<div style="background:#FFFFFF;border-bottom:1px solid #E0E0E0;padding:10px 24px;font-size:13px">
<span style="font-weight:600;font-size:16px;color:#0067C0">msn</span> &nbsp;&nbsp;&nbsp;&nbsp; {tabs}
<span style="float:right" class="small">{now:%A, %B} {now.day}, {now.year} &nbsp;&middot;&nbsp; {temp}&deg;F, {cond}</span></div>
<div style="padding:22px 24px 8px 24px;text-align:center">
<div style="display:inline-block;width:70%;background:#FFFFFF;border:1px solid #D1D1D1;border-radius:24px;padding:10px 18px;text-align:left;color:#616161">
&#128269;&nbsp; Search the web - type your words in the <b>address bar</b> above and press Enter</div>
<div class="small" style="margin-top:8px">Trending: {searches}</div></div>
<table width="100%" cellpadding="0" cellspacing="0" style="padding:0 24px"><tr valign="top">
<td width="62%" style="padding-right:14px">
<div class="card"><h3>Top stories</h3><ul>{news}</ul></div>
<div class="card"><h3>The Furry Web</h3><ul>{furry_web}</ul></div>
<div class="card"><h3>Your friends on Fur Affinity</h3>{fa_buddies}</div>
</td>
<td>
<div class="card"><h3>Weather</h3><div style="font-size:28px;font-weight:300">{temp}&deg;F</div>
<div class="small">{cond} &middot; Seattle, WA</div></div>
<div class="card"><h3>Your friends on the web</h3><div class="small">Their FurryCities homepages:</div>{buddies}</div>
<div class="card"><h3>Fandom</h3><ul>{fandom}</ul></div>
<div class="card"><h3>Favourites</h3>{cool}</div>
<div class="card small"><a href="http://windows.microsoft.com/">What's new in Windows 11</a><br>
<a href="http://www.microsoft.com/edge">Microsoft Edge</a><br><a href="http://windowsupdate.microsoft.com/">Windows Update</a></div>
</td></tr></table>
<div class="small" style="text-align:center;padding:14px">&copy; 2025 Microsoft &nbsp;&middot;&nbsp;
<a href="http://privacy.microsoft.com/">Privacy</a> &nbsp;&middot;&nbsp; <a href="http://www.msn.com/help/">Help</a></div>
</body></html>"""


def patch_web(web):
    """ClaudeXP's web module, 2025 edition."""
    web.msn_page = msn_page
    web.FANDOM_LINKS[:] = FANDOM_LINKS
    web.COOL_SITES[:] = COOL_SITES


def patch_hotmail(hotmail):
    hotmail.CSS = OUTLOOK_CSS
    hotmail.QUOTA = 15 * 1024 * 1024 * 1024
    wrap(hotmail, "_page")
    for obj in list(vars(hotmail).values()):
        if isinstance(obj, type) and "_login" in vars(obj):
            wrap(obj, "_login")


def patch_furaffinity(fa):
    from datetime import datetime
    fa.DST_START, fa.DST_END = datetime(2023, 1, 1).timestamp(), datetime(2025, 10, 1).timestamp()
    for obj in list(vars(fa).values()):
        if isinstance(obj, type) and "_page" in vars(obj):
            wrap(obj, "_page")
