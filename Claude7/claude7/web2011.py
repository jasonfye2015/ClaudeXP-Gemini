"""The Web of October 2011 where ClaudeXP's pages say 2001: MSN.com as Internet Explorer 9's home page (Bing, the
Windows Live links, that autumn's news), the fandom and cool-site links of the day, and the year swaps the Hotmail
and Fur Affinity pages get on their way out."""
import functools

from . import clock

FANDOM_LINKS = [("http://www.furnet.irc/", "FurNet IRC Network"), ("http://www.pawprintsmuck.com/", "PawPrints MUCK"),
                ("http://www.furrycities.com/", "FurryCities - furry homepages"),
                ("http://www.livejournal.com/", "LiveJournal - your friends' journals"),
                ("http://www.furryconventions.com/", "Convention listings 2011-2012"),
                ("http://www.fursuitnation.com/", "Fursuit Nation"),
                ("http://www.claudeaim.com/", "AIM - download &amp; buddy icons")]
COOL_SITES = [("http://www.facebook.com/", "Facebook"), ("http://www.youtube.com/", "YouTube"), ("http://www.reddit.com/", "reddit"),
              ("http://xkcd.com/", "xkcd"), ("http://www.homestarrunner.com/", "Homestar Runner"),
              ("http://www.penny-arcade.com/", "Penny Arcade"), ("http://en.wikipedia.org/", "Wikipedia")]
NEWS = [("windows8_preview", "Windows 8 Developer Preview: a first look at the Metro Start screen"),
        ("iphone4s", "Apple's iPhone 4S goes on sale with Siri, the talking assistant"),
        ("steve_jobs", "Remembering Steve Jobs, 1955-2011"),
        ("skyrim", "Skyrim, Modern Warfare 3 and Batman: the holiday games rush begins"),
        ("google_plus", "Google+ opens to everyone - will it catch Facebook?"),
        ("occupy", "Occupy Wall Street protests spread to more cities")]
SEARCHES = [("furry+conventions+2012", "furry conventions 2012"), ("windows+8+preview", "Windows 8 preview"),
            ("iphone+4s+review", "iPhone 4S review"), ("free+aim+buddy+icons", "free AIM buddy icons")]
WEB_SWAPS = (("2001", "2011"), ("Windows XP", "Windows 7"), ("MSN Hotmail", "Windows Live Hotmail"),
             ("Get MSN Messenger", "Get Windows Live Messenger"), ("MSN Messenger", "Windows Live Messenger"),
             ("Internet Explorer 6", "Internet Explorer 9"),
             ('<span class="logo">msn<span>.</span> Hotmail</span>',
              '<span class="logo">Windows Live<span>&trade;</span> Hotmail</span>'),
             ("MSN Home", "Windows Live"))
HOTMAIL_CSS = """
body { margin: 0; background: #FFFFFF; font-family: 'Segoe UI', Tahoma, Arial, sans-serif; font-size: 12px; color: #333333; }
td, th, div, li, p, form, select, input { font-family: 'Segoe UI', Tahoma, Arial, sans-serif; font-size: 12px; }
a { color: #0066CC; } a:visited { color: #0066CC; }
.top { background: linear-gradient(#2F6FC2, #1E4E8C); background-color: #2B63B0; color: #FFFFFF; }
.logo { font-family: 'Segoe UI', Arial; font-size: 24px; font-weight: 300; color: #FFFFFF; letter-spacing: 0; }
.logo span { color: #FFFFFF; font-size: 12px; vertical-align: super; }
.tabs td { padding: 5px 14px; font-size: 12px; }
.tab { background: #3B74C4; } .tab a { color: #FFFFFF; text-decoration: none; }
.tab-on { background: #FFFFFF; } .tab-on a { color: #1E4E8C; text-decoration: none; font-weight: bold; }
.bar { background: #F2F6FB; border-top: 1px solid #C9D8EA; border-bottom: 1px solid #C9D8EA; }
.btn { font-family: 'Segoe UI'; font-size: 12px; background: #F7F7F7; border: 1px solid #ABADB3; padding: 2px 8px; }
.folders { background: #F2F6FB; border-right: 1px solid #C9D8EA; }
.folders a { text-decoration: none; color: #1E4E8C; }
.list th { background: #F2F6FB; color: #4C607A; text-align: left; font-size: 12px; padding: 4px; border-bottom: 1px solid #C9D8EA; }
.list td { padding: 4px; border-bottom: 1px solid #EEF2F7; font-size: 12px; }
.unread td { font-weight: bold; background: #FFFFFF; }
.read td { background: #FAFBFD; }
.ad { background: #EEF4FB; border: 1px solid #C9D8EA; font-size: 11px; padding: 6px; }
.meter { width: 120px; height: 8px; border: 1px solid #6688BB; background: #FFFFFF; }
.meter div { height: 8px; background: #2B63B0; }
.foot { color: #808080; font-size: 11px; }
.msghead td { font-size: 12px; padding: 2px 4px; }
pre.body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; white-space: pre-wrap; margin: 8px; }
input.text, textarea { font-family: 'Segoe UI', Arial; font-size: 12px; border: 1px solid #ABADB3; }
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
    """MSN.com in the autumn of 2011: Internet Explorer 9's home page."""
    from claudexp.programs.navigator import web
    now = clock.now()
    furry_web, fa_buddies, buddies = web._home_links(knowledge)
    fandom = "".join(f'<a href="{u}">{t}</a><br>' for u, t in FANDOM_LINKS)
    cool = " &middot;\n".join(f'<a href="{u}">{t}</a>' for u, t in COOL_SITES)
    tabs = " | ".join(f'<a href="http://{h}/"><font color="#FFFFFF">{t}</font></a>' for h, t in (
        ("www.hotmail.com", "Hotmail"), ("www.bing.com", "Bing"), ("messenger.live.com", "Messenger"),
        ("skydrive.live.com", "SkyDrive"), ("www.msn.com/mobile", "Mobile")))
    channels = "".join(f'<a href="http://{h}/">{t}</a><br>' for h, t in (
        ("autos.msn.com", "Autos"), ("careers.msn.com", "Careers"), ("entertainment.msn.com", "Entertainment"),
        ("zone.msn.com", "Games"), ("health.msn.com", "Health"), ("money.msn.com", "Money"), ("msnbc.msn.com", "News"),
        ("sports.msn.com", "Sports"), ("tech.msn.com", "Tech &amp; Gadgets"), ("travel.msn.com", "Travel"),
        ("weather.msn.com", "Weather"), ("video.msn.com", "Video")))
    news = "".join(f'<li><a href="http://msnbc.msn.com/id/{slug}/">{t}</a></li>' for slug, t in NEWS)
    q = web.MSN_SEARCH_URL
    searches = " &middot;\n".join(f'<a href="{q}{s}">{t}</a>' for s, t in SEARCHES)
    return f"""<html><head><title>MSN.com</title></head>
<body bgcolor="#FFFFFF" text="#000000" link="#0033CC" vlink="#663399">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="150" bgcolor="#FFFFFF"><font face="Segoe UI, Verdana" size="6" color="#3366CC"><b>msn</b></font><font face="Verdana" size="4" color="#FF9900"><b>.</b></font>
<font face="Verdana" size="1" color="#666666">&nbsp;{now:%A, %B} {now.day}, {now.year}</font></td>
<td align="right" valign="bottom"><font face="Verdana" size="1"><a href="http://www.msn.com/">MSN Home</a> |
<a href="http://www.hotmail.com/">Hotmail</a> | <a href="http://www.bing.com/">Bing</a> |
<a href="http://messenger.live.com/">Messenger</a> | <a href="http://money.msn.com/">Money</a> |
<a href="http://www.facebook.com/">Facebook</a></font></td></tr></table>
<table width="100%" cellpadding="3" cellspacing="0" bgcolor="#3366CC"><tr><td><font face="Verdana" size="2" color="#FFFFFF">
<b>Bing</b> - type your words in the <b>Address</b> bar above and press Enter &nbsp;|&nbsp; {tabs}</font></td></tr></table>
<table width="100%" cellpadding="3" cellspacing="0" bgcolor="#DDE7F7"><tr><td><font face="Verdana" size="1">
Popular searches: {searches}</font></td></tr></table>
<table width="100%" cellpadding="6" cellspacing="0"><tr valign="top">
<td width="120" bgcolor="#EEF2FB"><font face="Verdana" size="1" color="#3366CC"><b>MSN CHANNELS</b></font><br>
<font face="Verdana" size="1">{channels}</font><br>
<font face="Verdana" size="1" color="#3366CC"><b>FURRY FANDOM</b></font><br>
<font face="Verdana" size="1">{fandom}</font></td>
<td><table width="100%" cellpadding="4" cellspacing="0" bgcolor="#FFF4E0"><tr><td>
<font face="Verdana" size="2" color="#CC6600"><b>The Furry Web</b></font>
<font face="Verdana" size="1"><ul>{furry_web}</ul></font></td></tr>
<tr><td><font face="Verdana" size="2" color="#CC6600"><b>Your Buddies on FurAffinity</b></font><br>
<font face="Verdana" size="1">{fa_buddies}</font></td></tr></table>
<br><font face="Verdana" size="2" color="#3366CC"><b>Today on MSN</b></font>
<font face="Verdana" size="1"><ul>{news}</ul></font></td>
<td width="190" bgcolor="#EEF2FB"><font face="Verdana" size="2" color="#3366CC"><b>Your Buddies on the Web</b></font><br>
<font face="Verdana" size="1" color="#666666">Their FurryCities homepages:</font><br>
<font face="Verdana" size="1">{buddies}</font><br><br>
<font face="Verdana" size="2" color="#3366CC"><b>Cool Sites</b></font><br><font face="Verdana" size="1">{cool}</font><br><br>
<font face="Verdana" size="1"><a href="http://messenger.live.com/">Get Windows Live Messenger</a><br>
<a href="http://windows.microsoft.com/ie">Internet Explorer 9</a><br>
<a href="http://windowsupdate.microsoft.com/">Windows Update</a></font></td></tr></table>
<hr size="1" color="#3366CC"><center><font face="Verdana" size="1" color="#808080">
&copy; 2011 Microsoft Corporation. All rights reserved. <a href="http://privacy.msn.com/">Privacy</a> |
<a href="http://www.msn.com/help/">Help</a></font></center>
</body></html>"""


def patch_web(web):
    """ClaudeXP's web module, 2011 edition."""
    web.msn_page = msn_page
    web.FANDOM_LINKS[:] = FANDOM_LINKS
    web.COOL_SITES[:] = COOL_SITES


def patch_hotmail(hotmail):
    hotmail.CSS = HOTMAIL_CSS
    hotmail.QUOTA = 5 * 1024 * 1024 * 1024
    wrap(hotmail, "_page")
    for obj in list(vars(hotmail).values()):
        if isinstance(obj, type) and "_login" in vars(obj):
            wrap(obj, "_login")


def patch_furaffinity(fa):
    from datetime import datetime
    fa.DST_START, fa.DST_END = datetime(2009, 1, 1).timestamp(), datetime(2011, 10, 1).timestamp()
    for obj in list(vars(fa).values()):
        if isinstance(obj, type) and "_page" in vars(obj):
            wrap(obj, "_page")
