"""ICQ 2001b, Trillian 0.71, Skype 1.0 and Kik - more messengers with the same buddies (see generic.py).

ICQ: everyone has a UIN, a nine-digit number. Trillian: one window for every network, so each buddy shows which
service they're on. Skype and Kik came later than 2001, styled as their earliest versions (Kik in a phone-sized
window with chat bubbles)."""
import hashlib
import re

from .core import AWAY, BUSY, OFFLINE, ONLINE
from .generic import Theme, make, number


def _plain(name):
    return re.sub(r"[^a-z0-9]+", "", name.lower()) or "user"


ICQ = Theme(
    key="icq", title="ICQ", version="2001b (Build #3659)", icon="icq_logo",
    status_icons={ONLINE: "icq_online", AWAY: "icq_away", BUSY: "icq_away", OFFLINE: "icq_offline"},
    handle=lambda c, sec: sec.get("uin") or number(c.screen_name, 9),
    my_handle=lambda me: number(me, 9),
    statuses=[("Available", ONLINE), ("Free For Chat", ONLINE), ("Away", AWAY), ("N/A (Extended Away)", AWAY),
              ("Occupied (Urgent Msgs)", BUSY), ("DND (Do not Disturb)", BUSY), ("Privacy (Invisible)", AWAY)],
    groups=[("Online", lambda b: b.presence != OFFLINE), ("Offline", lambda b: b.presence == OFFLINE)],
    head_top="#FFFFFF", head_bottom="#CDE9C4", head_text="#1A4A10", accent="#2E9A1E", page="#F2FAEE",
    subtitle="I Seek You", signin_title="Log in to ICQ", signin_field="ICQ# (UIN):", signin_button="Connect",
    buttons=["Send File", "Chat", "Add Contact", "History", "Info"], footer=["Main", "Services", "My ICQ"],
    me_color="#2244AA", them_color="#AA2222", line_style="stamp", main_size=(220, 470),
    message_sound="ICQ_Messenger_Notification_Sound.wav", signin_sound="ICQ_User_Online_Login_Sound.wav",
    toast=("#FFFFFF", "#CDE9C4", "#2E9A1E", "#1A4A10"),
    label=lambda b: b.name,
)

TRILLIAN = Theme(
    key="trillian", title="Trillian", version="0.71", icon="trillian_logo",
    status_icons={ONLINE: "dot_online", AWAY: "dot_away", BUSY: "dot_away", OFFLINE: "dot_offline"},
    handle=lambda c, sec: c.screen_name,
    my_handle=lambda me: me,
    statuses=[("Online", ONLINE), ("Away", AWAY), ("Busy", BUSY), ("Invisible", AWAY)],
    groups=[("Buddies", lambda b: b.presence != OFFLINE), ("Offline", lambda b: b.presence == OFFLINE)],
    head_top="#4E6A86", head_bottom="#22344A", head_text="#E6F0FA", accent="#3E7CB8", page="#D9E2EC",
    subtitle="AIM, ICQ, MSN & Yahoo! - all in one", signin_title="Connect to your networks",
    signin_field="Screen name:", signin_button="Connect All",
    buttons=["Profile", "Send File", "Logging"], footer=["Trillian", "Connections"],
    me_color="#1F5FA8", them_color="#A8401F", line_style="stamp", main_size=(230, 470),
    message_sound="trillian_Messenger_Notification_Sound.mp3", signin_sound="trillian_Messenger_Notification_Sound.mp3",
    toast=("#4E6A86", "#22344A", "#0E1A26", "#E6F0FA"),
    label=lambda b: b.name,
    tag=lambda b: ("AIM", "ICQ", "MSN", "Yahoo!")[int(hashlib.md5(b.contact.id.encode()).hexdigest(), 16) % 4],
)

SKYPE = Theme(
    key="skype", title="Skype", version="1.0.0.106 (Beta)", icon="skype_logo",
    status_icons={ONLINE: "skype_online", AWAY: "skype_away", BUSY: "skype_away", OFFLINE: "skype_offline"},
    handle=lambda c, sec: sec.get("name") or f"{_plain(c.screen_name)}{number(c.screen_name, 2)}",
    my_handle=lambda me: f"{_plain(me)}{number(me, 2)}",
    statuses=[("Online", ONLINE), ("Skype Me", ONLINE), ("Away", AWAY), ("Not Available", AWAY),
              ("Do Not Disturb", BUSY), ("Invisible", AWAY)],
    groups=[("Contacts", lambda b: True)],
    head_top="#FFFFFF", head_bottom="#C9EBFA", head_text="#00558A", accent="#00AFF0", page="#F2FAFE",
    subtitle="Free Internet telephony that just works", signin_title="Sign in to Skype",
    signin_field="Skype Name:", signin_button="Sign In",
    buttons=["Call", "Send File", "Add to Chat", "Block"], footer=["Contacts", "Dial", "Call List"],
    me_color="#00558A", them_color="#3A3A3A", line_style="stamp", main_size=(240, 470),
    message_sound="Skype_Message received.mp3", signin_sound="Skype Go online.mp3",
    signoff_sound="Skype Go offline.mp3", login_sound="Skype Go online.mp3",
    button_sounds={"Call": "Skype Phone ring.mp3", "Add to Chat": "Skype Knocking.mp3"},
    toast=("#FFFFFF", "#C9EBFA", "#00AFF0", "#00558A"),
)

KIK = Theme(
    key="kik", title="Kik", version="1.0", icon="kik_logo",
    status_icons={ONLINE: "dot_online", AWAY: "dot_away", BUSY: "dot_away", OFFLINE: "dot_offline"},
    handle=lambda c, sec: sec.get("username") or _plain(c.screen_name),
    my_handle=lambda me: _plain(me),
    statuses=[("Online", ONLINE), ("Busy", BUSY)],
    groups=[("Chats", lambda b: True)],
    head_top="#9AD13A", head_bottom="#6FA21C", head_text="#FFFFFF", accent="#82BC23", page="#F4F4F4",
    font="Arial", subtitle="Kik Messenger", signin_title="Log In", signin_field="Username:", signin_button="Log In",
    me_color="#82BC23", line_style="bubble", main_size=(260, 480), convo_size=(320, 480),
    toast=("#FFFFFF", "#E8F5D0", "#82BC23", "#2A4A0A"),
)

launch_icq, shutdown_icq, icq_icon, icq_client = make(ICQ)
launch_trillian, shutdown_trillian, trillian_icon, trillian_client = make(TRILLIAN)
launch_skype, shutdown_skype, skype_icon, skype_client = make(SKYPE)
launch_kik, shutdown_kik, kik_icon, kik_client = make(KIK)
