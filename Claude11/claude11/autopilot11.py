"""Kithylin Autopilot on WORKSTATION-2025: XP's autopilot (claudexp.autopilot) runs here through xpcompat's aliases,
as on Windows 7 - the engine, his day, the panel, the legs - with what 2025 changes. There's no ClaudeAIM here, so
his chatting and his roleplays are in Telegram (claudexp.autopilot.telegram: the AIM legs, played in Telegram
Desktop); his words are 2025's; the Web leg wanders in Microsoft Edge; his away status goes to Telegram."""

SEARCHES_2025 = ["furry art", "husky plush", "furry conventions 2025", "anthro wolf art", "furry comics",
                 "fursuit making", "angel wings costume", "upstate new york hiking", "coffee roasting",
                 "snow husky pictures", "husky videos", "bluesky furry artists", "vr chat avatars",
                 "local llm models", "steam deck games", "telegram sticker packs"]


def patch_legs(m):
    """claudexp.autopilot.legs: 2025's words, and the Web in Edge."""
    from claudexp.autopilot import telegram
    m.IM_NOTE, m.RP_NOTE = telegram.IM_NOTE, telegram.RP_NOTE
    m.MAIL_NOTE = m.MAIL_NOTE.replace("your Hotmail account", "your Outlook.com account")
    b = m.Browse
    b.__doc__ = "Microsoft Edge: a wander through the Web - a link, a read, another link, a search now and then."
    b.title = "The Web"
    b.blurb = "wander the Web in Microsoft Edge"
    b.SEARCHES = list(SEARCHES_2025)


def patch_panel(m):
    """claudexp.autopilot: Telegram's legs in AIM's place, and his away status in Telegram."""
    if m.__doc__:
        m.__doc__ = m.__doc__.replace("EPOCH-2001", "WORKSTATION-2025")
    xp_leg_classes = m.leg_classes

    def leg_classes():
        from claudexp.autopilot import legs, telegram
        swap = {legs.Messengers: telegram.TelegramChat, legs.Roleplay: telegram.TelegramRoleplay}
        return [swap.get(cls, cls) for cls in xp_leg_classes()]
    m.leg_classes = leg_classes

    def set_away(self, away, message=""):
        from claudexp.autopilot import telegram
        win = telegram._window()
        if win is not None:
            telegram.TelegramApp(win.content).world.set_user_away(away, message)
    m.XPAdapter.set_away = set_away
