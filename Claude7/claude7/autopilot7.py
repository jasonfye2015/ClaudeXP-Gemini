"""Kithylin Autopilot on SYSTEM-2011: XP's autopilot (claudexp.autopilot) runs here as it is - the engine, his day,
the panel, every leg - through xpcompat's aliases, with its prompts already in 2011 (patch_years). What's left is
said here: the Web leg's words (IE9, the 2011 Web, what he'd look up in 2011), the panel's name for this computer."""

SEARCHES_2011 = ["furry art", "husky plush", "furry conventions 2011", "anthro wolf art", "furry comics",
                 "fursuit making", "angel wings costume", "upstate new york hiking", "coffee roasting",
                 "snow husky pictures", "husky videos", "minecraft skins", "skyrim mods", "android phones",
                 "furaffinity journals", "tumblr themes"]


def patch_legs(m):
    """claudexp.autopilot.legs: the Web leg in 2011."""
    b = m.Browse
    b.__doc__ = "Internet Explorer 9: a wander through the 2011 Web - a link, a read, another link, a search now and then."
    b.blurb = "wander the 2011 Web in Internet Explorer"
    b.SEARCHES = list(SEARCHES_2011)


def patch_panel(m):
    """claudexp.autopilot: the program's own words for this computer."""
    if m.__doc__:
        m.__doc__ = m.__doc__.replace("EPOCH-2001", "SYSTEM-2011")
