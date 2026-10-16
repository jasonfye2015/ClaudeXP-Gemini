from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, QTimer, QSize, Signal
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QMdiArea,
    QMdiSubWindow,
    QMessageBox,
    QPushButton,
    QMenu,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .apps import MessengerApp, NotepadApp, ProfileDirectoryApp
from .accessories import CalculatorApp, PaintApp, WordPadApp
from .antivirus import WindowsDefenderApp, WindowsDefenderService, WindowsDefenderTrayButton
from .defragmenter import DefragmenterService, DiskDefragmenterApp
from .windows_update import WindowsUpdateApp, WindowsUpdateService
from .torrent_client import TorrentClientApp, TorrentClientService, TorrentTrayButton
from .sticky_notes import StickyNotesApp
from .snipping_tool import SnipOverlay, SnippingToolApp
from .windows_media_player import WindowsMediaPlayerApp
from .ai_service import AIService
from .msn import MSNContactListApp, MSNConversationApp
from .msn_presence import MSNPresence
from .msn_state import MSNState
from .msn_history import MSNHistorySession
from .msn_tray import MSNTrayButton
from .llm_activity import LLMActivityApp, LLMActivityLog, LLMActivityMonitor
from .contacts import CONTACTS, MSN_ASSETS
from .clock import format_locked_date, format_locked_time
from .config import USER_DOCUMENTS
from .identity import UserAccount
from .recent import RecentDocuments
from .options import OptionsWindow
from .service import ConnectionSimulator
from .screensaver import IdleScreenSaverController
from .network_activity import DSLNetworkTrayButton
from .mush import MushClientApp
from .mush_tray import MushTrayButton
from .mush_world import MUSH_ASSETS
from .irc import IRCClientApp
from .irc_tray import IRCTrayButton
from .irc_world import IRC_ASSETS
from .shell import DESKTOP_ASSETS, DesktopShortcut, RecycleBinApp, RecycleBinError, RecycleBinStore, WindowsComputerApp


def _load_wallpaper() -> QPixmap:
    path = _menu_asset("Background1.jpg")
    if not path.is_file():
        raise FileNotFoundError(f"Required Windows 7 wallpaper is missing: {path}")
    wallpaper = QPixmap(str(path))
    if wallpaper.isNull():
        raise RuntimeError(f"Could not load Windows 7 wallpaper: {path}")
    return wallpaper


def _menu_asset(filename: str) -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "start-menu" / filename


class _ImageFrame(QFrame):
    def __init__(self, image_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._image = QPixmap(str(image_path))
        if self._image.isNull():
            raise RuntimeError(f"Could not load desktop artwork: {image_path}")

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(self.rect(), self._image)


class _VerticalUserName(QWidget):
    def __init__(self, text: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.text = text
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(max(8, round(self.height() / 22)))
        painter.setFont(font)
        painter.translate(0, self.height())
        painter.rotate(-90)
        painter.drawText(0, 0, self.height(), self.width(), Qt.AlignmentFlag.AlignCenter, self.text)


class _MenuItemButton(QPushButton):
    highlighted = Signal()

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt event name
        self.highlighted.emit()
        super().enterEvent(event)

    def focusInEvent(self, event) -> None:  # noqa: N802 - Qt event name
        self.highlighted.emit()
        super().focusInEvent(event)


class WindowsMark(QWidget):
    def __init__(self, size: int = 24, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(size, size))

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = ("#00a4ef", "#f25022", "#7fba00", "#ffb900")
        edge = min(self.width(), self.height()) * 0.43
        gap = edge * 0.12
        left = (self.width() - 2 * edge - gap) / 2
        top = (self.height() - 2 * edge - gap) / 2
        rects = (
            (left, top, edge, edge),
            (left + edge + gap, top, edge, edge),
            (left, top + edge + gap, edge, edge),
            (left + edge + gap, top + edge + gap, edge, edge),
        )
        painter.setPen(Qt.PenStyle.NoPen)
        for color, (x, y, width, height) in zip(colors, rects, strict=True):
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(int(x), int(y), int(width), int(height), 2, 2)


class DesktopPage(QWidget):
    shutdownRequested = Signal()
    formatReinstallRequested = Signal()
    logOffRequested = Signal()

    def __init__(self, account: UserAccount, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.account = account
        self.service = ConnectionSimulator(self)
        self.ai_service = AIService(self)
        self._active_maintenance_modes: set[str] = set()
        self.defender = WindowsDefenderService(self)
        self.defender.maintenanceModeChanged.connect(
            lambda active: self._set_ai_maintenance_mode("defender", active)
        )
        self.defragmenter = DefragmenterService(self)
        self.defragmenter.settingsError.connect(
            lambda message: QMessageBox.warning(
                self, "Disk Defragmenter", f"Could not save timing settings: {message}"
            )
        )
        self.defragmenter.maintenanceModeChanged.connect(
            lambda active: self._set_ai_maintenance_mode("defragmenter", active)
        )
        self.windows_update = WindowsUpdateService(self)
        self.windows_update.maintenanceModeChanged.connect(
            lambda active: self._set_ai_maintenance_mode("windows-update", active)
        )
        self.torrent_client_service: TorrentClientService | None = None
        profile = account.active_profile
        self.msn_preferences = MSNState(profile.profile_id) if profile else None
        activity_profile_id = (
            profile.profile_id if profile else account.active_profile_id or "desktop"
        )
        self.llm_activity_log = LLMActivityLog(activity_profile_id, self)
        self.llm_activity_log.connect_service(self.ai_service)
        self.msn_presence = MSNPresence(self, preferences=self.msn_preferences, service=self.service)
        self.msn_history = MSNHistorySession(self)
        self._windows: dict[str, QMdiSubWindow] = {}
        self._taskbar_buttons: dict[str, QPushButton] = {}
        self._snip_overlay: SnipOverlay | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.mdi_area = QMdiArea()
        self.mdi_area.setFrameShape(QFrame.Shape.NoFrame)
        self._source_wallpaper = _load_wallpaper()
        self.recent_documents = RecentDocuments(USER_DOCUMENTS / ".recent-items.json")
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.mdi_area, 1)
        self._apply_wallpaper()

        self.welcome_note = QLabel(self.mdi_area.viewport())
        self.welcome_note.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        active = account.profile_by_id(account.active_profile_id)
        persona_name = active.fursona_name if active else account.desktop_name
        self.welcome_note.setText(
            f"Welcome, {persona_name}\n"
            "Use Start to open a local program."
        )
        self.welcome_note.setStyleSheet(
            "color: white; background: rgba(5, 23, 44, 120); "
            "border: 1px solid rgba(255,255,255,80); border-radius: 5px; "
            "padding: 10px 13px; font-size: 11pt;"
        )
        self.welcome_note.adjustSize()
        self.recycle_bin_store = RecycleBinStore(self)
        self.recycle_bin_store.changed.connect(self._update_recycle_bin_icon)
        self.desktop_shortcuts: dict[str, DesktopShortcut] = {}
        shortcut_entries = (
            ("Recycle Bin", DESKTOP_ASSETS / "Recycle Bin - Empty.png", self.open_recycle_bin),
            ("Desktop", DESKTOP_ASSETS / "Desktop.png", self.open_desktop_folder),
            ("Firefox", DESKTOP_ASSETS / "Firefox.ico", self.open_firefox_placeholder),
            ("MSN Messenger", MSN_ASSETS / "MSN_Icon.ico", self.open_messenger),
            ("MushClient", MUSH_ASSETS / "mush_icon.png", self.open_mush_client),
            ("IRC Client", IRC_ASSETS / "mirc_icon.png", self.open_irc_client),
        )
        for name, icon_path, callback in shortcut_entries:
            shortcut = DesktopShortcut(name, icon_path, self.mdi_area.viewport())
            shortcut.openRequested.connect(callback)
            shortcut.customContextMenuRequested.connect(
                lambda point, name=name, shortcut=shortcut:
                self._show_desktop_shortcut_menu(name, shortcut, point)
            )
            self.desktop_shortcuts[name] = shortcut
        try:
            self._update_recycle_bin_icon(bool(self.recycle_bin_store.entries()))
        except RecycleBinError as exc:
            self.desktop_shortcuts["Recycle Bin"].setToolTip(str(exc))
        self._layout_desktop_shortcuts()

        self.taskbar = _ImageFrame(_menu_asset("BG1_Bar.jpg"))
        self.taskbar.setFixedHeight(40)
        self.taskbar.setObjectName("taskbar")
        taskbar_layout = QHBoxLayout(self.taskbar)
        taskbar_layout.setContentsMargins(0, 0, 0, 0)
        taskbar_layout.setSpacing(0)

        self.start_button = QToolButton()
        self.start_button.setObjectName("startButton")
        self.start_button.setIcon(QIcon(str(_menu_asset("Start_Button_A.jpg"))))
        self.start_button.setIconSize(QSize(60, 40))
        self.start_button.setFixedSize(60, 40)
        self.start_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.start_button.setStyleSheet("QToolButton { border: 0; padding: 0; }")
        self.start_button.clicked.connect(self._toggle_start_menu)
        taskbar_layout.addWidget(self.start_button)
        self.bar_transition = QLabel()
        self.bar_transition.setFixedSize(37, 40)
        self.bar_transition.setPixmap(QPixmap(str(_menu_asset("Menu_Bar_Transition_Template.jpg"))))
        taskbar_layout.addWidget(self.bar_transition)

        self.window_buttons = QHBoxLayout()
        self.window_buttons.setSpacing(0)
        self.window_buttons.addStretch(1)
        taskbar_layout.addLayout(self.window_buttons, 1)

        self.system_tray = _ImageFrame(_menu_asset("Menu_System_Tray_Template.jpg"))
        self.system_tray.setFixedHeight(40)
        self.tray_icons = QWidget(self.system_tray)
        self.tray_icon_layout = QHBoxLayout(self.tray_icons)
        self.tray_icon_layout.setContentsMargins(0, 0, 0, 0)
        self.tray_icon_layout.setSpacing(4)
        self._tray_buttons = []
        self.clock_panel = QWidget(self.system_tray)
        clock_layout = QVBoxLayout(self.clock_panel)
        clock_layout.setContentsMargins(0, 0, 0, 0)
        clock_layout.setSpacing(0)
        self.time_label = QLabel()
        self.date_label = QLabel()
        self.service_label = QLabel(self.service.status_text)
        self.service_label.setObjectName("internetStatus")
        self.service_label.hide()
        self.system_tray.setToolTip(self.service.status_text)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.service_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.service_label.setStyleSheet("color: white; font-size: 7pt;")
        self.time_label.setStyleSheet("color: white; font-size: 10pt;")
        self.date_label.setStyleSheet("color: white; font-size: 8pt;")
        clock_layout.addWidget(self.time_label)
        clock_layout.addWidget(self.date_label)
        tray_layout = QHBoxLayout(self.system_tray)
        tray_layout.setContentsMargins(8, 2, 18, 2)
        tray_layout.setSpacing(0)
        tray_layout.addWidget(self.tray_icons)
        tray_layout.addSpacing(14)
        tray_layout.addWidget(self.clock_panel)
        self.msn_tray = MSNTrayButton(self.msn_presence, self.system_tray)
        self.msn_tray.activated.connect(self._open_msn_from_tray)
        self.msn_tray.closeRequested.connect(self.close_messenger)
        self._add_tray_icon(self.msn_tray)
        self.network_tray = DSLNetworkTrayButton(self.system_tray)
        self.network_tray.set_connection_state(self.service.state)
        self.service.stateChanged.connect(self.network_tray.set_connection_state)
        self.windows_update.set_network_available(self.network_tray.connected)
        self.service.stateChanged.connect(
            lambda *_: self.windows_update.set_network_available(
                self.network_tray.connected
            )
        )
        self.service.stateChanged.connect(
            lambda *_: (
                self.torrent_client_service.set_network_available(
                    self.network_tray.connected
                )
                if self.torrent_client_service is not None
                else None
            )
        )
        self.windows_update.networkTransferRequested.connect(
            self.network_tray.report_transfer
        )
        self.msn_presence.userStatusChanged.connect(self._record_msn_status_traffic)
        self.msn_presence.changed.connect(self._record_contact_presence_traffic)
        self._add_tray_icon(self.network_tray)
        self.llm_monitor = LLMActivityMonitor(self.system_tray)
        self.llm_monitor.openRequested.connect(self.open_llm_activity)
        self.ai_service.llmPhaseChanged.connect(self.llm_monitor.set_phase)
        self.llm_activity_log.errorChanged.connect(self.llm_monitor.set_log_error)
        self._add_tray_icon(self.llm_monitor)
        self.mush_tray = MushTrayButton(self.system_tray)
        self.mush_tray.openRequested.connect(self.open_mush_client)
        self.mush_tray.connectRequested.connect(self.connect_mush_from_tray)
        self.mush_tray.disconnectRequested.connect(self.disconnect_mush_from_tray)
        self.mush_tray.closeRequested.connect(self.close_mush_client)
        self.mush_tray.exitRequested.connect(self.exit_mush_client)
        self.mush_tray.aboutRequested.connect(self._about_mush_client)
        self._add_tray_icon(self.mush_tray)
        self.irc_tray = IRCTrayButton(self.system_tray)
        self.irc_tray.openRequested.connect(self.open_irc_client)
        self.irc_tray.connectRequested.connect(self.connect_irc_from_tray)
        self.irc_tray.disconnectRequested.connect(
            lambda: self._irc_client_action("disconnect_server")
        )
        self.irc_tray.awayRequested.connect(
            lambda: self._irc_client_action("toggle_away")
        )
        self.irc_tray.nicknameRequested.connect(
            lambda: self._irc_client_action("nickname_dialog")
        )
        self.irc_tray.closeRequested.connect(self.close_irc_client)
        self.irc_tray.exitRequested.connect(self.close_irc_client)
        self._add_tray_icon(self.irc_tray)
        self.defender_tray = WindowsDefenderTrayButton(self.defender, self.system_tray)
        self.defender_tray.openRequested.connect(self.open_windows_defender)
        self.defender_tray.aboutRequested.connect(self._about_windows_defender)
        self._add_tray_icon(self.defender_tray)
        self.torrent_tray = TorrentTrayButton(self.system_tray)
        self.torrent_tray.openRequested.connect(self.open_torrent_client)
        self.torrent_tray.pauseAllRequested.connect(self.pause_torrent_transfers)
        self.torrent_tray.resumeAllRequested.connect(self.resume_torrent_transfers)
        self.torrent_tray.closeWindowRequested.connect(
            self.close_torrent_client_window
        )
        self.torrent_tray.exitRequested.connect(self.exit_torrent_client)
        self._add_tray_icon(self.torrent_tray)
        taskbar_layout.addWidget(self.system_tray)
        self.mdi_area.subWindowActivated.connect(self._acknowledge_msn_window)
        layout.addWidget(self.taskbar)
        self.service.stateChanged.connect(self._update_service_status)

        self.start_menu = self._build_start_menu()
        self.start_menu.hide()
        self._position_start_menu()
        self.screen_saver = IdleScreenSaverController(self)
        self.options_window = OptionsWindow(
            self.ai_service,
            self,
            screen_saver_controller=self.screen_saver,
        )
        self.options_window.formatReinstallRequested.connect(self._confirm_format_reinstall)

        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start()
        self._update_clock()
        self._desktop_viewport = self.mdi_area.viewport()
        self._desktop_viewport.installEventFilter(self)
        self.taskbar.installEventFilter(self)

    def _build_start_menu(self) -> QFrame:
        menu = QFrame(self)
        menu.setObjectName("startMenu")
        menu.setFixedSize(270, 267)
        background = QLabel(menu)
        background.setGeometry(menu.rect())
        background.setPixmap(QPixmap(str(_menu_asset("Menu_Empty_Template.jpg"))))
        background.lower()
        name_strip = _VerticalUserName(self.account.desktop_name, menu)
        name_strip.setGeometry(1, 2, 22, 263)
        self.start_menu_buttons: dict[str, QPushButton] = {}
        entries = (
            ("Programs", "Programs.ico", "start-programs", self._open_programs_menu, True),
            ("Recent Items", "Recent.ico", "start-recent-items", self._open_recent_menu, True),
            ("Search...", "Search.ico", "start-search", self._search_documents, False),
            ("Options", "Options.ico", "start-options", self._show_options, True),
            ("Help and Support", "Help.ico", "start-help-and-support", self._show_help, False),
            ("Run...", "Run.ico", "start-run", self._run_command, False),
            ("Log Off", "Log_Off.ico", "start-log-off", self.logOffRequested.emit, False),
            ("Shut Down", "Shut_Down.ico", "shutdownButton", self._request_shutdown, False),
        )
        for index, (label, icon_name, object_name, callback, expandable) in enumerate(entries):
            y = 4 + index * 30 if index < 6 else 201 + (index - 6) * 30
            button = _MenuItemButton(label, menu)
            button.setObjectName(object_name)
            button.setIcon(QIcon(str(_menu_asset(icon_name))))
            button.setIconSize(QSize(22, 22))
            button.setGeometry(27, y, 239, 29)
            if expandable:
                arrow = QLabel("›", button)
                arrow.setGeometry(217, 0, 17, 29)
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            button.setStyleSheet(
                "QPushButton { text-align: left; padding: 2px 5px; color: #202b35; "
                "border: 1px solid transparent; background: transparent; }"
                "QPushButton:hover { background: rgba(94,175,225,95); "
                "border: 1px solid #68a9d2; }"
            )
            button.highlighted.connect(self._play_menu_command_sound)
            button.clicked.connect(callback)
            self.start_menu_buttons[label] = button
        return menu

    def _confirm_format_reinstall(self) -> None:
        self._close_start_menu()
        self.options_window.hide()
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Format and reinstall Windows")
        dialog.setText(
            "This permanently removes the Windows account, fursona profiles "
            "and their local images, saved personal documents, Sticky Notes, "
            "saved Media Player playlists, screen-saver preferences, Messenger conversations, and private "
            "LLM activity logs."
        )
        dialog.setInformativeText(
            "Preinstalled programs and Storage/Media, Storage/ROMs, and "
            "Storage/Models will be kept. Sticky Notes in "
            "Storage/UserData/Sticky Notes, saved playlists in "
            "Storage/UserData/Media Player Playlists, Messenger conversations in "
            "Storage/UserData/Messenger and per-fursona LLM activity logs will "
            "be erased. Screen-saver preferences in "
            "Storage/UserData/Screen Saver will also be erased. The simulator will "
            "shut down; the next launch will start at boot and first-run setup.\n\n"
            "To keep your saved chats, choose Cancel and open Windows Live "
            "Messenger. Use “Export all saved chats…” for each fursona, or "
            "“Export saved conversation…” for one contact. Save the export "
            "outside Storage before continuing.\n"
            "To keep the LLM log, open the hard-drive activity icon on the "
            "taskbar and choose “Export to text…”. Save that export outside Storage.\n\n"
            "If you are formatting the real computer, copy the backup to "
            "another drive first; a file on the drive being formatted will "
            "also be erased."
        )
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        confirm_button = dialog.button(QMessageBox.StandardButton.Yes)
        if confirm_button is not None:
            confirm_button.setText("Format and reinstall")
        dialog.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if dialog.exec() == QMessageBox.StandardButton.Yes:
            self.formatReinstallRequested.emit()

    def _toggle_start_menu(self) -> None:
        self._play_menu_sound("Windows Navigation Start.wav")
        if self.start_menu.isVisible():
            self._close_start_menu()
        else:
            self._position_start_menu()
            self.start_button.setIcon(QIcon(str(_menu_asset("Start_Button_B.jpg"))))
            self.start_menu.show()
            self.start_menu.raise_()

    def _close_start_menu(self) -> None:
        self.start_menu.hide()
        self.start_button.setIcon(QIcon(str(_menu_asset("Start_Button_A.jpg"))))
        submenu = getattr(self, "_active_submenu", None)
        if submenu is not None:
            submenu.hide()

    def _play_menu_command_sound(self) -> None:
        self._play_menu_sound("Windows Menu Command.wav")

    def _play_menu_sound(self, filename: str) -> None:
        if sys.platform != "win32":
            return
        import winsound

        try:
            winsound.PlaySound(
                str(_menu_asset(filename)),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        except (RuntimeError, OSError) as exc:
            print(f"Could not play Start menu sound: {exc}", file=sys.stderr)

    def _show_submenu(self, button_name: str, menu: QMenu) -> None:
        button = self.start_menu_buttons[button_name]
        self._play_menu_sound("Windows Navigation Start.wav")
        previous = getattr(self, "_active_submenu", None)
        if previous is not None:
            previous.hide()
            previous.deleteLater()
        self.start_menu.show()
        self.start_menu.raise_()
        self.start_button.setIcon(QIcon(str(_menu_asset("Start_Button_B.jpg"))))
        self._active_submenu = menu
        menu.hovered.connect(lambda _action: self._play_menu_command_sound())
        menu.aboutToHide.connect(
            lambda: self._play_menu_sound("Windows Navigation Start.wav")
        )
        menu.aboutToHide.connect(self.start_menu.hide)
        menu.aboutToHide.connect(
            lambda: self.start_button.setIcon(
                QIcon(str(_menu_asset("Start_Button_A.jpg")))
            )
        )
        menu.popup(button.mapToGlobal(QPoint(button.width(), 0)))

    def _open_programs_menu(self) -> None:
        menu = QMenu(self)
        for title, callback in (
            ("Furry Directory", self.open_directory),
            ("Windows Live Messenger", self.open_messenger),
            ("MushClient", self.open_mush_client),
            ("mIRC", self.open_irc_client),
            ("Windows Update", self.open_windows_update),
            ("Torrent Client", self.open_torrent_client),
            ("Computer", self.open_computer),
        ):
            action = menu.addAction(title)
            action.triggered.connect(callback)
        menu.addSeparator()
        menu.addMenu(self._build_accessories_menu())
        self._show_submenu("Programs", menu)

    def _build_accessories_menu(self) -> QMenu:
        menu = QMenu("Accessories", self)
        for title, callback in (
            ("Notepad", self.open_notepad),
            ("Calculator", self.open_calculator),
            ("Paint", self.open_paint),
            ("WordPad", self.open_wordpad),
            ("Sticky Notes", self.open_sticky_notes),
            ("Snipping Tool", self.open_snipping_tool),
            ("Windows Media Player", self.open_windows_media_player),
            ("Windows Defender", self.open_windows_defender),
            ("Disk Defragmenter", self.open_disk_defragmenter),
        ):
            action = menu.addAction(title)
            action.triggered.connect(callback)
        return menu

    def _open_recent_menu(self) -> None:
        menu = QMenu(self)
        try:
            files = self.recent_documents.entries()
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Recent Items", f"Could not read recent history:\n{exc}")
            return
        if not files:
            action = menu.addAction("No recent documents")
            action.setEnabled(False)
        for path in files:
            action = menu.addAction(path.name)
            action.setToolTip(str(path))
            action.triggered.connect(lambda _checked=False, p=path: self._open_recent_file(p))
        self._show_submenu("Recent Items", menu)

    def _open_recent_file(self, path: Path) -> None:
        self._open_explorer_file(path)

    def _record_recent_document(self, filename: str) -> None:
        try:
            self.recent_documents.record(Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Recent Items", f"Could not save recent history:\n{exc}")

    def _search_documents(self) -> None:
        self._close_start_menu()
        text, accepted = QInputDialog.getText(self, "Search", "Search documents for:")
        if not accepted or not text.strip():
            return
        documents = USER_DOCUMENTS
        matches = [
            path.name for path in documents.glob("*")
            if path.is_file() and not path.name.startswith(".")
            and text.casefold() in path.name.casefold()
        ] if documents.is_dir() else []
        message = "\n".join(matches) if matches else "No matching documents were found."
        QMessageBox.information(self, "Search results", message)

    def _show_options(self) -> None:
        self._close_start_menu()
        self.options_window.show()
        self.options_window.raise_()

    def _show_help(self) -> None:
        self._close_start_menu()
        QMessageBox.information(
            self, "Help and Support", "Help and Support are not implemented yet."
        )

    def _run_command(self) -> None:
        self._close_start_menu()
        command, accepted = QInputDialog.getText(self, "Run", "Enter a program name:")
        if not accepted:
            return
        actions = {
            "mirc": self.open_irc_client,
            "irc": self.open_irc_client,
            "directory": self.open_directory,
            "messenger": self.open_messenger,
            "notepad": self.open_notepad,
            "notepad.exe": self.open_notepad,
            "calculator": self.open_calculator,
            "calc": self.open_calculator,
            "calc.exe": self.open_calculator,
            "paint": self.open_paint,
            "mspaint": self.open_paint,
            "mspaint.exe": self.open_paint,
            "wordpad": self.open_wordpad,
            "write": self.open_wordpad,
            "write.exe": self.open_wordpad,
            "wordpad.exe": self.open_wordpad,
            "sticky notes": self.open_sticky_notes,
            "sticky notes.exe": self.open_sticky_notes,
            "stikynot": self.open_sticky_notes,
            "stikynot.exe": self.open_sticky_notes,
            "snippingtool": self.open_snipping_tool,
            "snippingtool.exe": self.open_snipping_tool,
            "windows media player": self.open_windows_media_player,
            "wmplayer": self.open_windows_media_player,
            "wmplayer.exe": self.open_windows_media_player,
            "windows update": self.open_windows_update,
            "wuapp": self.open_windows_update,
            "wuapp.exe": self.open_windows_update,
            "control update": self.open_windows_update,
            "torrent": self.open_torrent_client,
            "torrent client": self.open_torrent_client,
            "torrentclient": self.open_torrent_client,
            "bittorrent": self.open_torrent_client,
            "bittorrent.exe": self.open_torrent_client,
            "computer": self.open_computer,
        }
        callback = actions.get(command.strip().casefold())
        if callback is None:
            QMessageBox.information(self, "Run", "That program is not implemented.")
        else:
            callback()

    def _position_start_menu(self) -> None:
        if not hasattr(self, "start_menu"):
            return
        x = 0
        y = max(8, self.height() - self.taskbar.height() - self.start_menu.height() - 5)
        self.start_menu.move(x, y)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        super().resizeEvent(event)
        self._apply_wallpaper()
        self._position_start_menu()
        if hasattr(self, "desktop_shortcuts"):
            self._layout_desktop_shortcuts()

    def _layout_desktop_shortcuts(self) -> None:
        if not self.desktop_shortcuts:
            return
        viewport = self.mdi_area.viewport()
        width = next(iter(self.desktop_shortcuts.values())).width()
        rows = max(1, (viewport.height() - 16) // 88)
        for index, shortcut in enumerate(self.desktop_shortcuts.values()):
            column, row = divmod(index, rows)
            shortcut.move(8 + column * (width + 4), 8 + row * 88)
        self.welcome_note.adjustSize()
        self.welcome_note.move(
            max(12, viewport.width() - self.welcome_note.width() - 14), 14
        )

    def _update_recycle_bin_icon(self, is_full: bool) -> None:
        shortcut = self.desktop_shortcuts.get("Recycle Bin")
        if shortcut is None:
            return
        filename = "Recycle Bin - Full.png" if is_full else "Recycle Bin - Empty.png"
        shortcut.setIcon(QIcon(str(DESKTOP_ASSETS / filename)))
        shortcut.setToolTip(
            "Recycle Bin — " + ("contains deleted items" if is_full else "empty")
        )

    def _build_desktop_shortcut_menu(self, name, shortcut) -> QMenu:
        menu = QMenu(self)
        menu.addAction("Open", lambda: self._open_desktop_shortcut(name))
        if name == "Recycle Bin":
            try:
                full = bool(self.recycle_bin_store.entries())
            except RecycleBinError as exc:
                full = False
                shortcut.setToolTip(str(exc))
            restore = menu.addAction("Restore all items", self._restore_all_recycle_bin_items)
            restore.setEnabled(full)
            empty = menu.addAction("Empty Recycle Bin", self._empty_recycle_bin)
            empty.setEnabled(full)
        elif name == "Desktop":
            menu.addSeparator()
            menu.addAction("Open in new window", self._open_desktop_in_new_window)
        menu.addSeparator()
        menu.addAction("Properties", lambda: self._show_desktop_properties(name))
        return menu

    def _show_desktop_shortcut_menu(self, name, shortcut, point) -> None:
        menu = self._build_desktop_shortcut_menu(name, shortcut)
        menu.aboutToHide.connect(menu.deleteLater)
        menu.popup(shortcut.mapToGlobal(point))

    def _open_desktop_shortcut(self, name) -> None:
        callbacks = {
            "Recycle Bin": self.open_recycle_bin,
            "Desktop": self.open_desktop_folder,
            "Firefox": self.open_firefox_placeholder,
            "MSN Messenger": self.open_messenger,
            "MushClient": self.open_mush_client,
            "IRC Client": self.open_irc_client,
        }
        callbacks[name]()

    def _show_desktop_properties(self, name) -> None:
        QMessageBox.information(
            self, f"{name} Properties", f"{name}\nWindows 7 desktop shortcut"
        )

    def open_firefox_placeholder(self) -> None:
        QMessageBox.information(self, "Firefox", "Feature not implemented yet.")

    def _open_computer_window(self, key, title) -> None:
        app = WindowsComputerApp(self.recycle_bin_store, window_name=title)
        app.openFileRequested.connect(self._open_explorer_file)
        app.recycleBinRequested.connect(self.open_recycle_bin)
        self._open_app(key, title, app)

    def open_desktop_folder(self) -> None:
        self._open_computer_window("desktop-folder", "Desktop")

    def _open_desktop_in_new_window(self) -> None:
        sequence = getattr(self, "_extra_desktop_window_sequence", 0) + 1
        self._extra_desktop_window_sequence = sequence
        self._open_computer_window(f"desktop-folder-{sequence}", "Desktop")

    def open_recycle_bin(self) -> None:
        try:
            self.recycle_bin_store.entries()
        except RecycleBinError as exc:
            QMessageBox.warning(self, "Recycle Bin", str(exc))
            return
        self._open_app(
            "recycle-bin", "Recycle Bin", RecycleBinApp(self.recycle_bin_store)
        )

    def _restore_all_recycle_bin_items(self) -> None:
        window = self._windows.get("recycle-bin")
        if window is None:
            self.open_recycle_bin()
            window = self._windows.get("recycle-bin")
        if window is not None and isinstance(window.widget(), RecycleBinApp):
            window.widget().items.selectAll()
            window.widget().restore_selected()

    def _empty_recycle_bin(self) -> None:
        window = self._windows.get("recycle-bin")
        if window is None:
            self.open_recycle_bin()
            window = self._windows.get("recycle-bin")
        if window is not None and isinstance(window.widget(), RecycleBinApp):
            window.widget().empty_bin()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt event name
        super().showEvent(event)
        self.window().installEventFilter(self)
        QTimer.singleShot(0, self._acknowledge_msn_window)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - Qt event name
        if (
            watched in getattr(self, "_tray_buttons", [])
            and event.type() in (QEvent.Type.Show, QEvent.Type.Hide)
        ):
            QTimer.singleShot(0, self._update_tray_geometry)
        if event.type() == QEvent.Type.WindowActivate:
            QTimer.singleShot(0, self._acknowledge_msn_window)
        if event.type() == QEvent.Type.Resize and watched is getattr(self, "_desktop_viewport", None):
            self._apply_wallpaper()
            self._layout_desktop_shortcuts()
        elif event.type() == QEvent.Type.MouseButtonPress:
            self._close_start_menu()
        return super().eventFilter(watched, event)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if not self.confirm_session_end("close the desktop"):
            event.ignore()
            return
        self.stop_session()
        self._desktop_viewport.removeEventFilter(self)
        self.taskbar.removeEventFilter(self)
        super().closeEvent(event)

    def confirm_session_end(self, action: str) -> bool:
        for window in self._windows.values():
            widget = window.widget()
            if isinstance(widget, MessengerApp) and not widget.confirm_close(action):
                window.showNormal()
                window.raise_()
                self.mdi_area.setActiveSubWindow(window)
                return False
        return True

    def _apply_wallpaper(self) -> None:
        size = self.mdi_area.viewport().size()
        if size.width() <= 0 or size.height() <= 0:
            return
        scaled = self._source_wallpaper.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        left = max(0, (scaled.width() - size.width()) // 2)
        top = max(0, (scaled.height() - size.height()) // 2)
        crop = scaled.copy(left, top, size.width(), size.height())
        self.mdi_area.setBackground(QBrush(crop))

    def _update_clock(self) -> None:
        if getattr(self, "_session_stopped", False):
            return
        now = datetime.now().astimezone()
        self.time_label.setText(format_locked_time(now))
        self.date_label.setText(format_locked_date(now))
        self._update_tray_geometry()

    def _add_tray_icon(self, icon: QWidget) -> None:
        """Keep the newest registered icon at the left of the notification area."""
        self._tray_buttons.append(icon)
        self.tray_icon_layout.insertWidget(0, icon)
        icon.installEventFilter(self)
        QTimer.singleShot(0, self._update_tray_geometry)

    def _update_tray_geometry(self) -> None:
        if getattr(self, "_session_stopped", False):
            return
        # Reserve the clock's full text width independently from the icon strip.
        # Explicit hidden state also works before the desktop itself is shown.
        labels = (self.time_label, self.date_label)
        for label in labels:
            label.ensurePolished()
        clock_width = max(
            label.fontMetrics().horizontalAdvance(label.text()) for label in labels
        ) + 12
        self.clock_panel.setFixedWidth(clock_width)
        visible = [icon for icon in self._tray_buttons if not icon.isHidden()]
        icon_width = sum(icon.width() for icon in visible)
        icon_width += max(0, len(visible) - 1) * self.tray_icon_layout.spacing()
        self.tray_icons.setFixedWidth(icon_width)
        # Left padding, a clear clock gap, and the right show-desktop margin.
        self.system_tray.setFixedWidth(8 + icon_width + 14 + clock_width + 18)
        self.taskbar.layout().activate()
        self.system_tray.layout().activate()

    def open_computer(self) -> None:
        self._open_computer_window("computer", "Computer")

    def _open_explorer_file(self, filename) -> None:
        path = Path(filename)
        if path.suffix.casefold() in (".html", ".htm", ".md"):
            existing = self._windows.get("wordpad")
            if existing is not None and isinstance(existing.widget(), WordPadApp):
                wordpad = existing.widget()
                if wordpad.load_document(path):
                    self._restore_app("wordpad")
                return
            wordpad = WordPadApp()
            wordpad.documentAccessed.connect(self._record_recent_document)
            if wordpad.load_document(path):
                self._open_app("wordpad", "WordPad", wordpad)
            else:
                wordpad.deleteLater()
            return
        if path.suffix.casefold() in (".png", ".jpg", ".jpeg", ".bmp"):
            existing = self._windows.get("paint")
            if existing is not None and isinstance(existing.widget(), PaintApp):
                paint = existing.widget()
                if paint.open_picture(path):
                    self._restore_app("paint")
                return
            paint = PaintApp()
            paint.documentAccessed.connect(self._record_recent_document)
            if paint.open_picture(path):
                self._open_app("paint", "Paint", paint)
            else:
                paint.deleteLater()
            return
        existing = self._windows.get("notepad")
        if existing is not None:
            notepad = existing.widget()
            if not isinstance(notepad, NotepadApp):
                return
            if notepad.load_file(path):
                self._restore_app("notepad")
            return
        notepad = NotepadApp()
        notepad.documentAccessed.connect(self._record_recent_document)
        if notepad.load_file(path):
            self._open_app("notepad", "Notepad", notepad)
        else:
            notepad.deleteLater()

    def open_directory(self) -> None:
        self._open_app(
            "directory",
            "Furry Directory",
            ProfileDirectoryApp(self.account),
        )

    def open_notepad(self) -> None:
        notepad = NotepadApp()
        notepad.documentAccessed.connect(self._record_recent_document)
        self._open_app("notepad", "Notepad", notepad)

    def open_calculator(self) -> None:
        self._open_app("calculator", "Calculator", CalculatorApp())

    def open_paint(self) -> None:
        paint = PaintApp()
        paint.documentAccessed.connect(self._record_recent_document)
        self._open_app("paint", "Paint", paint)

    def open_wordpad(self) -> None:
        wordpad = WordPadApp()
        wordpad.documentAccessed.connect(self._record_recent_document)
        self._open_app("wordpad", "WordPad", wordpad)

    def open_sticky_notes(self) -> None:
        profile = self.account.active_profile
        profile_id = (
            profile.profile_id
            if profile
            else self.account.active_profile_id or "desktop"
        )
        profile_name = profile.fursona_name if profile else self.account.desktop_name
        self._open_app(
            "sticky-notes",
            "Sticky Notes",
            StickyNotesApp(profile_id, profile_name),
        )

    def open_snipping_tool(self) -> None:
        app = SnippingToolApp()
        app.documentAccessed.connect(self._record_recent_document)
        app.captureRequested.connect(
            lambda mode, snipping_app=app: self._begin_snip(snipping_app, mode)
        )
        self._open_app("snipping-tool", "Snipping Tool", app)

    def _begin_snip(self, app: SnippingToolApp, mode: str) -> None:
        if getattr(self, "_session_stopped", False):
            return
        window = self._windows.get("snipping-tool")
        if window is None or window.widget() is not app:
            return
        self._close_start_menu()
        if self._snip_overlay is not None:
            self._cancel_desktop_snip()
        window.showMinimized()
        if mode == "Full-screen Snip":
            QTimer.singleShot(160, lambda: self._capture_full_desktop(app))
            return
        overlay = SnipOverlay(self)
        self._snip_overlay = overlay
        overlay.finished.connect(
            lambda rectangle, snipping_app=app: self._finish_desktop_snip(
                snipping_app, rectangle
            )
        )
        overlay.cancelled.connect(self._cancel_desktop_snip)
        overlay.show()
        overlay.raise_()
        overlay.setFocus()

    def _finish_desktop_snip(self, app: SnippingToolApp, rectangle: QRect) -> None:
        overlay = self._snip_overlay
        self._snip_overlay = None
        if overlay is not None:
            overlay.hide()
            overlay.deleteLater()
        area = rectangle.intersected(self.rect())
        if area.isEmpty():
            self._cancel_desktop_snip()
            return
        QTimer.singleShot(
            100, lambda: self._save_desktop_snip(app, area)
        )

    def _capture_full_desktop(self, app: SnippingToolApp) -> None:
        self._save_desktop_snip(app, self.rect())

    def _save_desktop_snip(self, app: SnippingToolApp, area: QRect) -> None:
        if getattr(self, "_session_stopped", False):
            return
        window = self._windows.get("snipping-tool")
        if window is None or window.widget() is not app:
            return
        image = self.grab(area).toImage()
        app.set_capture(image)
        self._restore_app("snipping-tool")

    def _cancel_desktop_snip(self) -> None:
        overlay = self._snip_overlay
        self._snip_overlay = None
        if overlay is not None:
            overlay.hide()
            overlay.deleteLater()
        if not getattr(self, "_session_stopped", False):
            self._restore_app("snipping-tool")

    def open_windows_media_player(self) -> None:
        profile = self.account.active_profile
        profile_id = (
            profile.profile_id
            if profile
            else self.account.active_profile_id or "desktop"
        )
        self._open_app(
            "windows-media-player",
            "Windows Media Player",
            WindowsMediaPlayerApp(profile_id),
        )

    def open_windows_defender(self) -> None:
        self._open_app(
            "windows-defender",
            "Windows Defender",
            WindowsDefenderApp(self.defender),
        )

    def open_windows_update(self) -> None:
        self._open_app(
            "windows-update",
            "Windows Update",
            WindowsUpdateApp(self.windows_update),
        )

    def open_torrent_client(self) -> TorrentClientApp:
        existing = self._windows.get("torrent-client")
        if existing:
            self._restore_app("torrent-client")
            self.torrent_tray.set_window_open(True)
            return existing.widget()

        if self.torrent_client_service is None:
            self.torrent_client_service = TorrentClientService(self)
            self.torrent_client_service.networkTransferRequested.connect(
                self.network_tray.report_transfer
            )
            self.torrent_client_service.activityChanged.connect(
                self.torrent_tray.set_activity
            )
            self.torrent_tray.bind_service(self.torrent_client_service)
            self.torrent_client_service.set_network_available(
                self.network_tray.connected
            )
        self.torrent_tray.activate()
        self.torrent_client_service.start()
        client = TorrentClientApp(self.torrent_client_service)
        client.closeWindowRequested.connect(self.close_torrent_client_window)
        client.exitRequested.connect(self.exit_torrent_client)
        self._open_app("torrent-client", "Torrent Client", client)
        self.torrent_tray.set_window_open(True)
        return client

    def pause_torrent_transfers(self) -> None:
        if self.torrent_client_service is not None:
            self.torrent_client_service.pause_all()

    def resume_torrent_transfers(self) -> None:
        if self.torrent_client_service is not None:
            self.torrent_client_service.resume_all()

    def close_torrent_client_window(self) -> None:
        window = self._windows.get("torrent-client")
        if window:
            window.close()
        else:
            self.torrent_tray.set_window_open(False)

    def exit_torrent_client(self) -> None:
        service = self.torrent_client_service
        self.torrent_client_service = None
        if service is not None:
            service.stop_session()
            service.deleteLater()
        self.close_torrent_client_window()
        self.torrent_tray.deactivate()

    def _about_windows_defender(self) -> None:
        QMessageBox.information(
            self,
            "About Windows Defender",
            "Windows Defender is represented here as a local simulation. "
            "It does not provide real antivirus protection or inspect local files.",
        )

    def open_disk_defragmenter(self) -> None:
        self.defragmenter.start()
        self._open_app(
            "disk-defragmenter",
            "Disk Defragmenter",
            DiskDefragmenterApp(self.defragmenter),
        )

    def _set_ai_maintenance_mode(self, reason: str, active: bool) -> None:
        if active:
            self._active_maintenance_modes.add(reason)
        else:
            self._active_maintenance_modes.discard(reason)
        self.ai_service.set_maintenance_priority_mode(
            bool(self._active_maintenance_modes)
        )

    def open_llm_activity(self) -> None:
        self._open_app(
            "llm-activity",
            "Local LLM Activity",
            LLMActivityApp(self.llm_activity_log),
        )

    def open_messenger(self) -> None:
        self.msn_tray.activate()
        existing = self._windows.get("messenger")
        if existing:
            existing.showNormal()
            existing.raise_()
            self.mdi_area.setActiveSubWindow(existing)
            return
        messenger = MSNContactListApp(
            self.account, self.service, ai_service=self.ai_service, presence=self.msn_presence,
            history_session=self.msn_history,
        )
        messenger.aiSettingsRequested.connect(self.options_window.open_ai_tab)
        messenger.conversationRequested.connect(self.open_msn_conversation)
        messenger.browserRequested.connect(self.open_advertisement)
        messenger.closeMessengerRequested.connect(self.close_messenger)
        messenger.trayVisibilityRequested.connect(self.msn_tray.set_enabled)
        self.msn_tray.visibilityChanged.connect(
            messenger.tray_visibility_action.setChecked
        )
        self._open_app(
            "messenger",
            "MSN Messenger",
            messenger,
        )

    def open_mush_client(self) -> MushClientApp:
        self.mush_tray.activate()
        existing = self._windows.get("mush-client")
        if existing:
            existing.showNormal()
            existing.raise_()
            self.mdi_area.setActiveSubWindow(existing)
            return existing.widget()
        client = MushClientApp(
            self.account, self.service, self.ai_service, presence=self.msn_presence
        )
        client.aiSettingsRequested.connect(self.options_window.open_ai_tab)
        client.activityRequested.connect(self.mush_tray.mark_activity)
        client.connectionChanged.connect(self.mush_tray.set_connected)
        client.networkTransferRequested.connect(self.network_tray.report_transfer)
        self._open_app("mush-client", "MushClient — PawPrints MUCK", client)
        return client

    def connect_mush_from_tray(self) -> None:
        client = self.open_mush_client()
        client.connect_current()

    def open_irc_client(self) -> IRCClientApp:
        existing = self._windows.get("irc-client")
        if existing:
            self._restore_app("irc-client")
            return existing.widget()
        client = IRCClientApp(
            self.account, self.service, self.ai_service, presence=self.msn_presence
        )
        client.aiSettingsRequested.connect(self.options_window.open_ai_tab)
        client.stateChanged.connect(self.irc_tray.set_state)
        client.networkTransferRequested.connect(self.network_tray.report_transfer)
        client.networkTransferRequested.connect(self.irc_tray.mark_transfer)
        self.irc_tray.activate()
        self._open_app("irc-client", "mIRC — FurNet", client)
        return client

    def connect_irc_from_tray(self) -> None:
        self.open_irc_client().connect_current()

    def _irc_client_action(self, method: str) -> None:
        window = self._windows.get("irc-client")
        if window:
            getattr(window.widget(), method)()

    def close_irc_client(self) -> None:
        window = self._windows.get("irc-client")
        if window:
            window.close()
        self.irc_tray.deactivate()

    def disconnect_mush_from_tray(self) -> None:
        window = self._windows.get("mush-client")
        if window:
            widget = window.widget()
            if isinstance(widget, MushClientApp):
                widget.disconnect_player()

    def close_mush_client(self) -> None:
        window = self._windows.get("mush-client")
        if window:
            window.close()
        self.mush_tray.deactivate()

    def exit_mush_client(self) -> None:
        self.close_mush_client()
        self.mush_tray.deactivate()

    def _about_mush_client(self) -> None:
        window = self._windows.get("mush-client")
        if window and isinstance(window.widget(), MushClientApp):
            window.widget().show_about()
            return
        QMessageBox.information(
            self,
            "About MushClient",
            "MushClient connects only to the local PawPrints MUCK simulation. "
            "No real MUCK server is contacted.",
        )

    def open_msn_conversation(self, contact) -> None:
        key = "msn-chat-" + contact.contact_id
        existing = self._windows.get(key)
        if existing:
            existing.showNormal()
            existing.raise_()
            self.mdi_area.setActiveSubWindow(existing)
            return
        chat = MSNConversationApp(
            self.account, self.service, contact, ai_service=self.ai_service,
            presence=self.msn_presence,
            history_session=self.msn_history,
        )
        chat.aiSettingsRequested.connect(self.options_window.open_ai_tab)
        chat.messageArrived.connect(self._msn_message_arrived)
        chat.networkTransferRequested.connect(self.network_tray.report_transfer)
        self._open_app(key, f"{contact.online_name} — Conversation", chat)

    def _msn_chat_is_readable(self, window):
        return bool(
            window and self.isVisible() and self.window().isActiveWindow()
            and self.mdi_area.activeSubWindow() is window
            and window.isVisible() and not window.isMinimized()
        )

    def _msn_message_arrived(self, contact_id):
        window = self._windows.get("msn-chat-" + contact_id)
        if not self._msn_chat_is_readable(window):
            contact = next(
                (c for c in CONTACTS if c.contact_id == contact_id), None
            )
            self.msn_tray.notify_message(contact_id, contact.online_name if contact else contact_id)

    def _acknowledge_msn_window(self, _window=None):
        if getattr(self, "_session_stopped", False):
            return
        window = self.mdi_area.activeSubWindow()
        if self._msn_chat_is_readable(window) and isinstance(window.widget(), MSNConversationApp):
            self.msn_tray.mark_read(window.widget()._chat_contact.contact_id)

    def _open_msn_from_tray(self, contact_id):
        contact = next((c for c in CONTACTS if c.contact_id == contact_id), None)
        if contact:
            self.open_msn_conversation(contact)
            self.msn_tray.mark_read(contact_id)
        else:
            self.open_messenger()

    def close_messenger(self):
        """Close every MSN window and hide its tray icon; leave Windows running."""
        windows = [
            (key, window, window.widget())
            for key, window in tuple(self._windows.items())
            if isinstance(window.widget(), MessengerApp)
        ]
        for _key, window, widget in windows:
            if not widget.confirm_close("close MSN Messenger"):
                window.showNormal()
                window.raise_()
                self.mdi_area.setActiveSubWindow(window)
                return False
        for _key, _window, widget in windows:
            widget._close_preapproved = True
        self.msn_presence.set_user_status("Offline")
        for _key, window, _widget in windows:
            window.close()
        self.msn_tray.deactivate()
        return True

    def open_advertisement(self, url) -> None:
        # Keep ads inside the simulation; never launch a real external browser.
        from .msn_browser import MSNBrowser
        browser = self._windows.get("msn-browser")
        if browser:
            browser.widget().navigate(url)
            browser.showNormal()
            self.mdi_area.setActiveSubWindow(browser)
        else:
            app = MSNBrowser(url)
            app.networkTransferRequested.connect(self.network_tray.report_transfer)
            self._open_app("msn-browser", "Internet Explorer — Local Web", app)

    def _update_service_status(self, _state, status: str) -> None:
        self.network_tray.set_connection_state(_state, status)
        self.ai_service.set_simulated_availability(
            self.service.chat_available, self.service.background_work_paused
        )
        self.service_label.setText(status)
        self.system_tray.setToolTip(status)
        color = "#dbe8f3" if status == "Internet: Connected" else "#ffe0a3"
        self.service_label.setStyleSheet(f"color: {color}; font-size: 7pt;")

    def _record_msn_status_traffic(self, previous, current) -> None:
        if previous == "Offline" and current != "Offline":
            self.network_tray.report_transfer(
                "outgoing", 192 + len(self.msn_presence.away_message.encode("utf-8")),
                "MSN sign-in",
            )
            roster_size = sum(
                len(contact_id.encode("utf-8"))
                + len(state.encode("utf-8"))
                + 32
                for contact_id, state in self.msn_presence.states.items()
            )
            self.network_tray.report_transfer(
                "incoming", roster_size + 160, "MSN contact and presence list"
            )
        elif previous != current and current == "Offline":
            self.network_tray.report_transfer("outgoing", 112, "MSN sign-out")
        elif current != "Offline":
            self.network_tray.report_transfer(
                "outgoing", 96 + len(self.msn_presence.away_message.encode("utf-8")),
                "MSN presence update",
            )

    def _record_contact_presence_traffic(self, _contact_id, state) -> None:
        if self.msn_presence.user_status != "Offline" and state != "Blocked":
            self.network_tray.report_transfer(
                "incoming", 96, "MSN contact presence update"
            )

    def _open_app(self, key: str, title: str, app_widget: QWidget) -> None:
        self._play_menu_sound("Windows Navigation Start.wav")
        self._close_start_menu()
        existing = self._windows.get(key)
        if existing is not None:
            existing.showNormal()
            existing.raise_()
            self.mdi_area.setActiveSubWindow(existing)
            app_widget.deleteLater()
            return

        window = QMdiSubWindow()
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        window.setWindowTitle(title)
        icon_type = {
            "computer": QStyle.StandardPixmap.SP_ComputerIcon,
            "directory": QStyle.StandardPixmap.SP_DirHomeIcon,
            "messenger": QStyle.StandardPixmap.SP_MessageBoxInformation,
            "llm-activity": QStyle.StandardPixmap.SP_DriveHDIcon,
            "disk-defragmenter": QStyle.StandardPixmap.SP_DriveHDIcon,
        }.get(key, QStyle.StandardPixmap.SP_FileIcon)
        if key == "windows-defender":
            window.setWindowIcon(self.defender_tray.icon())
        elif isinstance(app_widget, (MSNContactListApp, MSNConversationApp)):
            window.setWindowIcon(QIcon(str(MSN_ASSETS / "MSN_Icon.ico")))
        elif isinstance(app_widget, MushClientApp):
            window.setWindowIcon(QIcon(str(MUSH_ASSETS / "mush_icon.png")))
        elif isinstance(app_widget, IRCClientApp):
            window.setWindowIcon(QIcon(str(IRC_ASSETS / "mirc_icon.png")))
        elif isinstance(app_widget, WindowsComputerApp):
            window.setWindowIcon(QIcon(str(DESKTOP_ASSETS / "Desktop.png")))
        elif isinstance(app_widget, RecycleBinApp):
            window.setWindowIcon(QIcon(str(DESKTOP_ASSETS / "Recycle Bin - Empty.png")))
        else:
            window.setWindowIcon(self.style().standardIcon(icon_type))
        window.setWidget(app_widget)
        window.installEventFilter(self)
        app_widget.installEventFilter(self)
        for child in app_widget.findChildren(QWidget):
            child.installEventFilter(self)
        if isinstance(app_widget, CalculatorApp):
            window.resize(300, 390)
        elif isinstance(app_widget, StickyNotesApp):
            window.resize(700, 450)
        elif isinstance(app_widget, SnippingToolApp):
            window.resize(900, 620)
        elif isinstance(app_widget, WindowsMediaPlayerApp):
            window.resize(1020, 680)
        elif isinstance(app_widget, DiskDefragmenterApp):
            window.resize(950, 700)
        elif isinstance(app_widget, (MSNContactListApp, MSNConversationApp)):
            hint = app_widget.sizeHint()
            window.resize(hint.width(), min(hint.height(), max(480, self.mdi_area.height() - 10)))
        else:
            window.resize(760, 520)
        self.mdi_area.addSubWindow(window)
        self._windows[key] = window

        taskbar_button = QPushButton()
        taskbar_button.setObjectName(f"taskbar-{key}")
        taskbar_button.setToolTip(title)
        taskbar_button.setIcon(window.windowIcon())
        taskbar_button.setIconSize(QSize(24, 24))
        taskbar_button.setFixedSize(60, 40)
        taskbar_button.setStyleSheet(
            "QPushButton { border: 0; padding: 0; "
            f"border-image: url('{_menu_asset('Menu_Program_Template.jpg').as_posix()}'); }}"
            "QPushButton:hover { background: rgba(255,255,255,70); }"
        )
        taskbar_button.clicked.connect(
            lambda _checked=False, app_key=key: self._toggle_taskbar_app(app_key)
        )
        self._taskbar_buttons[key] = taskbar_button
        self.window_buttons.insertWidget(self.window_buttons.count() - 1, taskbar_button)
        window.destroyed.connect(lambda _obj=None, app_key=key: self._forget_app(app_key))
        window.show()
        self.mdi_area.setActiveSubWindow(window)

    def _restore_app(self, key: str) -> None:
        window = self._windows.get(key)
        if window is not None:
            if window.isMinimized():
                window.showNormal()
            window.raise_()
            self.mdi_area.setActiveSubWindow(window)

    def _toggle_taskbar_app(self, key: str) -> None:
        self._close_start_menu()
        window = self._windows.get(key)
        if window is None:
            return
        if window.isVisible() and not window.isMinimized():
            self._play_menu_sound("Windows Minimize.wav")
            window.showMinimized()
        else:
            self._play_menu_sound("Windows Restore.wav")
            self._restore_app(key)

    def _forget_app(self, key: str) -> None:
        self._windows.pop(key, None)
        if getattr(self, "_session_stopped", False):
            self._taskbar_buttons.pop(key, None)
            return
        if key == "mush-client":
            self.mush_tray.deactivate()
        elif key == "irc-client":
            self.irc_tray.deactivate()
        elif key == "torrent-client":
            self.torrent_tray.set_window_open(False)
        button = self._taskbar_buttons.pop(key, None)
        if button is not None:
            self.window_buttons.removeWidget(button)
            button.deleteLater()

    def _request_shutdown(self) -> None:
        self._close_start_menu()
        self.shutdownRequested.emit()

    def stop_session(self) -> None:
        if getattr(self, "_session_stopped", False):
            return
        self._session_stopped = True
        if self._snip_overlay is not None:
            overlay = self._snip_overlay
            self._snip_overlay = None
            overlay.hide()
            overlay.deleteLater()
        self.clock_timer.stop()
        self.screen_saver.stop_session()
        for window in tuple(self._windows.values()):
            widget = window.widget()
            if isinstance(widget, MessengerApp):
                widget.client.cancel()
            elif isinstance(widget, (MushClientApp, IRCClientApp)):
                widget.stop()
            elif isinstance(widget, StickyNotesApp):
                widget._save_now()
        self.msn_tray.stop()
        self.mush_tray.deactivate()
        self.irc_tray.deactivate()
        self.network_tray.stop_activity()
        if self.torrent_client_service is not None:
            self.torrent_client_service.stop_session()
        self.torrent_tray.deactivate()
        self.defender.stop()
        self.defragmenter.stop()
        self.windows_update.stop_session()
        self.service.stop()
        self.msn_presence.stop()
        self.ai_service.stop()
