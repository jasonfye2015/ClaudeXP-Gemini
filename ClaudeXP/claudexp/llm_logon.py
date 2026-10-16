"""ClaudeXP's own parts of the AI engine (the engine itself is ClaudeCore's: claudecore/ai):
the warning sign by the clock when the language models are missing, and keeping ClaudeAIM's settings in step with
Control Panel > AI Models."""
from . import ai_models


def at_logon(desktop, warm=True):
    """Load the model now (so the first reply is quick), or put up a warning by the clock if it can't run.
    warm=False (msconfig's 'llama-server' startup item unchecked): the model loads on first use instead."""
    from . import llm_server
    sync_aim()                                 # ClaudeAIM's model settings follow Control Panel > AI Models
    if llm_server.available():
        if warm:
            llm_server.start_in_background()
        return
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QStyle, QSystemTrayIcon
    from .tray import TrayIcon
    old = getattr(desktop, "_llm_tray", None)
    if old is not None:
        old.hide()
    tray = TrayIcon(desktop, QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning))
    tray.setToolTip("Language model missing - your buddies can't talk")
    desktop._llm_tray = tray

    def explain(*_):
        from .aimodels_cpl import ai_models_properties
        ai_models_properties(desktop, setup=True)          # the AI Model Setup Assistant
    tray.activated.connect(lambda reason: explain() if reason in (QSystemTrayIcon.Trigger,
                                                                    QSystemTrayIcon.DoubleClick) else None)
    tray.show()
    QTimer.singleShot(1500, lambda: tray.showMessage(
        "Your buddies can't talk", "ClaudeXP's language models aren't installed (E:\\LLM Models). Everything else "
        "works. Click here to download them."))
    tray.messageClicked.connect(explain)
    check = QTimer(tray)                      # models put in place by hand are noticed within a minute
    check.timeout.connect(lambda: llm_server.recheck(desktop) and check.stop())
    check.start(60000)


def sync_aim():
    """Write the conversation model, per-buddy overrides and context size into ClaudeAIM's settings."""
    try:
        from .programs.aim import ensure_aim_path
        ensure_aim_path()
        from claudeaim.contacts import load_contacts
        from claudeaim.storage import Settings
        s = Settings()
        cfg = ai_models.config()
        contacts, _errors = load_contacts()
        by_name = {c.screen_name.lower(): c.id for c in contacts}
        ids = {m.id for m in ai_models.installed()}
        overrides = {by_name[n.lower()]: m for n, m in cfg["overrides"].items() if n.lower() in by_name and m in ids}
        want = {"default_model": ai_models.model_for("conversation") or s["default_model"], "model_overrides": overrides,
                "context_size": int(cfg["context"])}
        if not s["password"]:                  # AIM never checks it; a filled-in box just looks right
            want["password"] = "********"
        if any(s[k] != v for k, v in want.items()):
            s.update(**want)
    except Exception:
        pass


ai_models.changed_hooks.append(sync_aim)
