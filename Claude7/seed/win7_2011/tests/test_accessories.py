from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QImage, QPixmap, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from win7_2011.win7sim.accessories import CalculatorApp, PaintApp, WordPadApp
from win7_2011.win7sim import config
from win7_2011.win7sim.desktop import DesktopPage
from win7_2011.win7sim.snipping_tool import SnipOverlay, SnippingToolApp
from win7_2011.win7sim.sticky_notes import StickyNotesApp, load_notes
from win7_2011.win7sim.media_playlists import (
    PlaylistManagerDialog,
    SavedPlaylistStore,
)
from win7_2011.tests.test_ui import sample_account
from win7_2011.win7sim.windows_media_player import (
    WindowsMediaPlayerApp,
    find_media_files,
)


class WindowsAccessoriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        self.qt_app.processEvents()

    def test_calculator_handles_decimal_arithmetic_and_divide_by_zero(self) -> None:
        calculator = CalculatorApp()
        for key in ("1", "2", ".", "5", "+", "3", "="):
            calculator.press(key)
        self.assertEqual(calculator.display.text(), "15.5")

        for key in ("C", "8", "÷", "0", "="):
            calculator.press(key)
        self.assertEqual(calculator.display.text(), "Divide by zero")
        calculator.press("7")
        self.assertEqual(calculator.display.text(), "7")

        calculator.deleteLater()
        self.qt_app.processEvents()

    def test_calculator_accepts_keyboard_input(self) -> None:
        calculator = CalculatorApp()
        calculator.show()
        calculator.setFocus()
        self.qt_app.processEvents()
        for key in (
            Qt.Key.Key_8,
            Qt.Key.Key_Plus,
            Qt.Key.Key_2,
            Qt.Key.Key_Enter,
        ):
            QTest.keyClick(calculator, key)
        self.assertEqual(calculator.display.text(), "10")
        calculator.close()
        calculator.deleteLater()
        self.qt_app.processEvents()

    def test_paint_canvas_draws_and_saves_a_standard_png(self) -> None:
        paint = PaintApp()
        paint.canvas.pen_color = Qt.GlobalColor.red
        paint.canvas.pen_width = 5
        paint.canvas.draw_segment(QPoint(30, 30), QPoint(90, 30))
        self.assertEqual(paint.canvas.image.toImage().pixelColor(60, 30).name(), "#ff0000")

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "drawing.png"
            self.assertTrue(paint.save_picture(path))
            self.assertTrue(path.is_file())
            paint.canvas.clear()
            with patch.object(
                QMessageBox,
                "question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                self.assertTrue(paint.open_picture(path))
            self.assertEqual(paint.canvas.image.toImage().pixelColor(60, 30).name(), "#ff0000")

        paint.deleteLater()
        self.qt_app.processEvents()

    def test_wordpad_keeps_rich_html_and_reads_plain_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            formatted_path = root / "formatted.html"
            wordpad = WordPadApp()
            wordpad.editor.setHtml("<p><strong>Formatted note</strong></p>")
            self.assertTrue(wordpad.save_document(formatted_path))
            self.assertIn("font-weight:700", formatted_path.read_text(encoding="utf-8"))

            reopened = WordPadApp()
            self.assertTrue(reopened.load_document(formatted_path))
            self.assertEqual(reopened.editor.toPlainText(), "Formatted note")
            cursor = reopened.editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            reopened.editor.setTextCursor(cursor)
            self.assertGreaterEqual(
                reopened.editor.textCursor().charFormat().fontWeight(), 700
            )

            text_path = root / "plain.txt"
            text_path.write_text("A plain note", encoding="utf-8")
            self.assertTrue(reopened.load_document(text_path))
            self.assertEqual(reopened.editor.toPlainText(), "A plain note")
            wordpad.deleteLater()
            reopened.deleteLater()
            self.qt_app.processEvents()

    def test_windows_run_opens_all_accessory_aliases(self) -> None:
        desktop = DesktopPage(sample_account())
        desktop.resize(1000, 700)
        desktop.show()
        self.qt_app.processEvents()
        menu = desktop._build_accessories_menu()
        self.assertEqual(
            [action.text() for action in menu.actions()],
            [
                "Notepad",
                "Calculator",
                "Paint",
                "WordPad",
                "Sticky Notes",
                "Snipping Tool",
                "Windows Media Player",
                "Windows Defender",
                "Disk Defragmenter",
            ],
        )
        menu.deleteLater()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                with patch.object(config, "STICKY_NOTES", Path(temporary)):
                    for command, key, title in (
                        ("calc", "calculator", "Calculator"),
                        ("mspaint", "paint", "Paint"),
                        ("write", "wordpad", "WordPad"),
                        ("sticky notes", "sticky-notes", "Sticky Notes"),
                        ("snippingtool", "snipping-tool", "Snipping Tool"),
                        (
                            "wmplayer",
                            "windows-media-player",
                            "Windows Media Player",
                        ),
                    ):
                        with patch(
                            "win7_2011.win7sim.desktop.QInputDialog.getText",
                            return_value=(command, True),
                        ):
                            desktop._run_command()
                        self.qt_app.processEvents()
                        self.assertEqual(
                            desktop._windows[key].windowTitle(), title
                        )
                    media_player = desktop._windows[
                        "windows-media-player"
                    ].widget()
                    self.assertEqual(
                        media_player.profile_id,
                        desktop.account.active_profile.profile_id,
                    )
        finally:
            desktop.stop_session()
            desktop.close()
            desktop.deleteLater()
            self.qt_app.processEvents()

    def test_recent_item_file_types_open_in_the_matching_accessory(self) -> None:
        desktop = DesktopPage(sample_account())
        desktop.resize(1000, 700)
        desktop.show()
        self.qt_app.processEvents()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                image_path = root / "drawing.png"
                image = QPixmap(4, 4)
                image.fill(Qt.GlobalColor.blue)
                self.assertTrue(image.save(str(image_path)))
                html_path = root / "note.html"
                html_path.write_text("<p>WordPad note</p>", encoding="utf-8")
                text_path = root / "note.txt"
                text_path.write_text("Notepad note", encoding="utf-8")

                with patch.object(desktop, "_record_recent_document"):
                    desktop._open_recent_file(image_path)
                    self.assertIsInstance(
                        desktop._windows["paint"].widget(), PaintApp
                    )
                    desktop._open_recent_file(html_path)
                    self.assertIsInstance(
                        desktop._windows["wordpad"].widget(), WordPadApp
                    )
                    desktop._open_recent_file(text_path)
                    from win7_2011.win7sim.apps import NotepadApp

                    self.assertIsInstance(
                        desktop._windows["notepad"].widget(), NotepadApp
                    )
        finally:
            desktop.stop_session()
            desktop.close()
            desktop.deleteLater()
            self.qt_app.processEvents()

    def test_sticky_notes_save_per_profile_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(config, "STICKY_NOTES", Path(temporary)):
                notes = StickyNotesApp("profile-one", "Rook")
                notes.create_note()
                notes.editor.setPlainText("Pick up groceries")
                notes.color_box.setCurrentIndex(1)
                self.assertTrue(notes._save_now())
                self.assertEqual(len(load_notes("profile-one")), 1)
                self.assertEqual(load_notes("profile-two"), [])
                notes.close()
                notes.deleteLater()

                reopened = StickyNotesApp("profile-one", "Rook")
                self.assertEqual(reopened.editor.toPlainText(), "Pick up groceries")
                self.assertEqual(reopened.color_box.currentData(), "#bfe8ff")
                reopened.close()
                reopened.deleteLater()
                self.qt_app.processEvents()

    def test_snipping_overlay_returns_the_selected_rectangle(self) -> None:
        parent = QWidget()
        parent.resize(180, 120)
        parent.show()
        overlay = SnipOverlay(parent)
        completed = []
        overlay.finished.connect(completed.append)
        overlay.show()
        overlay.raise_()
        overlay.setFocus()
        self.qt_app.processEvents()

        QTest.mousePress(
            overlay,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(12, 16),
        )
        QTest.mouseMove(overlay, QPoint(62, 66), 10)
        QTest.mouseRelease(
            overlay,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(62, 66),
        )
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0], QRect(12, 16, 51, 51))
        parent.close()
        parent.deleteLater()
        self.qt_app.processEvents()

    def test_full_screen_snip_captures_the_simulated_desktop_and_saves(self) -> None:
        desktop = DesktopPage(sample_account())
        desktop.resize(800, 500)
        desktop.show()
        self.qt_app.processEvents()
        desktop.open_snipping_tool()
        app = desktop._windows["snipping-tool"].widget()
        desktop._begin_snip(app, "Full-screen Snip")
        QTest.qWait(250)
        self.assertIsNotNone(app.capture_image)
        self.assertGreater(app.capture_image.width(), 0)
        self.assertGreater(app.capture_image.height(), 0)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "UserData" / "Pictures" / "snip.png"
            saved_paths = []
            app.documentAccessed.connect(saved_paths.append)
            with (
                patch.object(config, "STORAGE_ROOT", root),
                patch.object(desktop.recent_documents, "record"),
                patch(
                    "win7_2011.win7sim.snipping_tool.QFileDialog.getSaveFileName",
                    return_value=(str(target), "PNG image (*.png)"),
                ),
            ):
                app.save_image()
            self.assertTrue(target.is_file())
            self.assertEqual(saved_paths, [str(target)])

        desktop.stop_session()
        desktop.close()
        desktop.deleteLater()
        self.qt_app.processEvents()

    def test_media_player_scans_local_archive_without_loading_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Storage"
            archive = root / "Media"
            (archive / "TV").mkdir(parents=True)
            (archive / "Movies").mkdir()
            (archive / "TV" / "episode.mkv").write_bytes(b"")
            (archive / "Movies" / "film.mp4").write_bytes(b"")
            (archive / "Movies" / "notes.txt").write_text("ignore", encoding="utf-8")
            with patch.object(config, "STORAGE_ROOT", root):
                player = WindowsMediaPlayerApp()
                player.scan_archive()
                self.assertEqual(
                    find_media_files(archive),
                    [archive / "Movies" / "film.mp4", archive / "TV" / "episode.mkv"],
                )
                self.assertEqual(player.playlist.count(), 2)
                self.assertIsNone(player._player)
                player.close()
                player.deleteLater()
                self.qt_app.processEvents()

    def test_named_playlists_are_profile_scoped_and_can_be_renamed_or_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Storage"
            media_file = root / "Media" / "Music" / "song.mp3"
            media_file.parent.mkdir(parents=True)
            media_file.touch()
            playlist_root = root / "UserData" / "Media Player Playlists"
            with (
                patch.object(config, "STORAGE_ROOT", root),
                patch.object(config, "MEDIA_PLAYLISTS", playlist_root),
            ):
                store = SavedPlaylistStore("profile-one")
                saved = store.save_new("Evening", [media_file])
                self.assertEqual(store.load_all(), [saved])
                self.assertEqual(SavedPlaylistStore("profile-two").load_all(), [])
                with self.assertRaisesRegex(ValueError, "already exists"):
                    store.save_new("evening", [media_file])

                renamed = store.rename(saved.playlist_id, "Quiet evening")
                self.assertEqual(renamed.name, "Quiet evening")
                self.assertEqual(renamed.media_paths, saved.media_paths)
                store.delete(saved.playlist_id)
                self.assertEqual(store.load_all(), [])

    def test_corrupt_playlist_store_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Storage"
            playlist_root = root / "UserData" / "Media Player Playlists"
            playlist_root.mkdir(parents=True)
            store_file = playlist_root / "rook-profile.json"
            original = b'{"unfinished": '
            store_file.write_bytes(original)
            with (
                patch.object(config, "STORAGE_ROOT", root),
                patch.object(config, "MEDIA_PLAYLISTS", playlist_root),
            ):
                store = SavedPlaylistStore("rook-profile")
                with self.assertRaisesRegex(ValueError, "invalid JSON"):
                    store.load_all()
                with self.assertRaisesRegex(ValueError, "invalid JSON"):
                    store.save_new("Favorites", [root / "Media" / "song.mp3"])
                self.assertEqual(store_file.read_bytes(), original)

    def test_playlist_manager_saves_opens_and_keeps_missing_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Storage"
            media_root = root / "Media" / "Music"
            media_root.mkdir(parents=True)
            audio_file = media_root / "song.mp3"
            audio_file.touch()
            missing_file = media_root / "moved-song.mp3"
            playlist_root = root / "UserData" / "Media Player Playlists"
            with (
                patch.object(config, "STORAGE_ROOT", root),
                patch.object(config, "MEDIA_PLAYLISTS", playlist_root),
            ):
                player = WindowsMediaPlayerApp("rook-profile")
                store = player.playlist_store
                original = store.save_new("Old Favorites", [audio_file, missing_file])
                dialog = PlaylistManagerDialog(
                    store, player.current_media_paths, player
                )
                dialog.openRequested.connect(player.open_saved_playlist)
                self.assertIn("1 missing", dialog.playlist_list.item(0).text())

                dialog.open_selected()
                self.assertEqual(player.playlist.count(), 1)
                self.assertIn("1 missing file", player.status.text())
                self.assertIn("kept unchanged", player.status.text())
                self.assertEqual(store.load_all()[0].media_paths, original.media_paths)

                with patch(
                    "win7_2011.win7sim.media_playlists.QInputDialog.getText",
                    return_value=("Fresh Mix", True),
                ):
                    dialog.save_current()
                self.assertEqual(len(store.load_all()), 2)
                with patch(
                    "win7_2011.win7sim.media_playlists.QInputDialog.getText",
                    return_value=("Renamed Mix", True),
                ):
                    dialog.rename_selected()
                self.assertIn(
                    "Renamed Mix", [record.name for record in store.load_all()]
                )

                with patch(
                    "win7_2011.win7sim.media_playlists.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ):
                    dialog.delete_selected()
                self.assertEqual(
                    [record.name for record in store.load_all()], ["Old Favorites"]
                )
                self.assertEqual(
                    Path(store.load_all()[0].media_paths[1]).name,
                    "moved-song.mp3",
                )
                dialog.close()
                player.close()
                dialog.deleteLater()
                player.deleteLater()
                self.qt_app.processEvents()

