"""Local archive browser and Windows Media Player-style controls."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from . import config
from .media_playlists import (
    PlaylistManagerDialog,
    SavedPlaylist,
    SavedPlaylistStore,
)

AUDIO_EXTENSIONS = frozenset(
    {".aac", ".aif", ".aiff", ".flac", ".m4a", ".mid", ".midi", ".mp3",
     ".oga", ".ogg", ".wav", ".wma"}
)
VIDEO_EXTENSIONS = frozenset(
    {".3gp", ".asf", ".avi", ".m2ts", ".m4v", ".mkv", ".mov", ".mp4",
     ".mpeg", ".mpg", ".mts", ".ts", ".vob", ".webm", ".wmv"}
)
MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


def find_media_files(folder: Path) -> list[Path]:
    """List supported local media without reading the file contents."""
    if not folder.is_dir():
        return []
    found: list[Path] = []
    def raise_walk_error(error: OSError) -> None:
        raise error

    for root, directories, filenames in os.walk(
        folder, followlinks=False, onerror=raise_walk_error
    ):
        directories[:] = sorted(
            name for name in directories if not name.startswith(".")
        )
        for filename in filenames:
            path = Path(root) / filename
            if path.suffix.casefold() in MEDIA_EXTENSIONS:
                found.append(path)
    return sorted(found, key=lambda path: str(path).casefold())


def _format_time(milliseconds: int) -> str:
    seconds = max(0, int(milliseconds / 1000))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


class WindowsMediaPlayerApp(QWidget):
    """Play audio and video from the local Storage/Media archive or chosen files."""

    def __init__(self, profile_id: str = "desktop") -> None:
        super().__init__()
        self.profile_id = profile_id
        self.archive_root = config.STORAGE_ROOT / "Media"
        self.playlist_store = SavedPlaylistStore(profile_id)
        self._player = None
        self._audio_output = None
        self._video_widget = None
        self._media_module = None
        self._backend_error: str | None = None
        self._playing_path: str | None = None

        self.archive_button = QPushButton("Scan Storage/Media")
        self.add_files_button = QPushButton("Add files…")
        self.add_folder_button = QPushButton("Choose library folder…")
        self.playlists_button = QPushButton("Playlists…")
        self.remove_button = QPushButton("Remove")
        self.playlist = QListWidget()
        self.playlist.setObjectName("media-player-library")
        self.playlist.setMinimumWidth(250)
        self.playlist.itemDoubleClicked.connect(lambda _item: self.play_selected())

        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_placeholder = QLabel(
            "Windows Media Player\n\nChoose local audio or video to play."
        )
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_placeholder.setStyleSheet(
            "QLabel { background: #101820; color: #c9d5df; "
            "font-size: 15pt; padding: 24px; }"
        )
        self.video_layout.addWidget(self.video_placeholder)

        self.play_button = QPushButton("Play")
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.stop_button = QPushButton("Stop")
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.time_label = QLabel("0:00 / 0:00")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(110)
        self.status = QLabel(
            "Local playback only. Scan Storage/Media or add files from your archive."
        )
        self.status.setWordWrap(True)

        controls = QHBoxLayout()
        controls.addWidget(self.previous_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.next_button)
        controls.addStretch(1)
        controls.addWidget(QLabel("Volume"))
        controls.addWidget(self.volume_slider)
        seek = QHBoxLayout()
        seek.addWidget(self.position_slider, 1)
        seek.addWidget(self.time_label)
        media_controls = QVBoxLayout()
        media_controls.addLayout(controls)
        media_controls.addLayout(seek)
        media_controls.addWidget(self.status)

        library_controls = QHBoxLayout()
        library_controls.addWidget(self.archive_button)
        library_controls.addWidget(self.add_files_button)
        library_controls.addWidget(self.add_folder_button)
        library_controls.addWidget(self.playlists_button)
        library_controls.addWidget(self.remove_button)
        library = QVBoxLayout()
        library.addWidget(QLabel("Media Library"))
        library.addLayout(library_controls)
        library.addWidget(self.playlist, 1)
        right = QVBoxLayout()
        right.addWidget(self.video_container, 1)
        right.addLayout(media_controls)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        library_widget = QWidget()
        library_widget.setLayout(library)
        right_widget = QWidget()
        right_widget.setLayout(right)
        splitter.addWidget(library_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root = QVBoxLayout(self)
        root.addWidget(splitter, 1)

        self.archive_button.clicked.connect(self.scan_archive)
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.choose_library_folder)
        self.playlists_button.clicked.connect(self.manage_playlists)
        self.remove_button.clicked.connect(self.remove_selected)
        self.play_button.clicked.connect(self.toggle_playback)
        self.stop_button.clicked.connect(self.stop_playback)
        self.previous_button.clicked.connect(self.play_previous)
        self.next_button.clicked.connect(self.play_next)
        self.position_slider.sliderMoved.connect(self._seek)
        self.volume_slider.valueChanged.connect(self._set_volume)

    def scan_archive(self) -> None:
        if not self.archive_root.is_dir():
            self.status.setText(
                f"The local media folder was not found: {self.archive_root}"
            )
            return
        self.status.setText("Scanning the local media archive…")
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()
        try:
            files = find_media_files(self.archive_root)
        except OSError as exc:
            self.status.setText(f"Could not scan the media archive: {exc}")
            return
        added = self.add_paths(files)
        self.status.setText(
            f"Found {len(files)} local media files; added {added} new "
            f"{'item' if added == 1 else 'items'} to the library."
        )

    def choose_library_folder(self) -> None:
        initial = self.archive_root if self.archive_root.is_dir() else config.STORAGE_ROOT
        selected = QFileDialog.getExistingDirectory(
            self, "Choose a local media library", str(initial)
        )
        if not selected:
            return
        self.archive_root = Path(selected)
        self.scan_archive()

    def add_files(self) -> None:
        initial = self.archive_root if self.archive_root.is_dir() else config.STORAGE_ROOT
        files, _selected_filter = QFileDialog.getOpenFileNames(
            self,
            "Add local media files",
            str(initial),
            "Audio and video files (*" + " *".join(
                sorted(MEDIA_EXTENSIONS)
            ) + ");;All files (*)",
        )
        if files:
            added = self.add_paths(Path(filename) for filename in files)
            self.status.setText(f"Added {added} media items.")

    def add_paths(self, paths: Iterable[Path]) -> int:
        existing = {
            str(self.playlist.item(row).data(Qt.ItemDataRole.UserRole)).casefold()
            for row in range(self.playlist.count())
        }
        added = 0
        for path in paths:
            path = Path(path)
            if (
                not path.is_file()
                or path.suffix.casefold() not in MEDIA_EXTENSIONS
                or str(path).casefold() in existing
            ):
                continue
            item = QListWidgetItem(f"{path.name}   —   {path.parent.name}")
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.playlist.addItem(item)
            existing.add(str(path).casefold())
            added += 1
        return added

    def current_media_paths(self) -> list[Path]:
        return [
            Path(self.playlist.item(row).data(Qt.ItemDataRole.UserRole))
            for row in range(self.playlist.count())
        ]

    def manage_playlists(self) -> None:
        dialog = PlaylistManagerDialog(
            self.playlist_store, self.current_media_paths, self
        )
        dialog.openRequested.connect(self.open_saved_playlist)
        dialog.exec()

    def open_saved_playlist(self, saved: SavedPlaylist) -> None:
        """Load present files while leaving missing entries in the saved record."""
        self.stop_playback()
        self.playlist.clear()
        self.position_slider.setRange(0, 0)
        self.video_placeholder.setText(
            "Windows Media Player\n\nChoose local audio or video to play."
        )
        self.video_placeholder.setVisible(True)
        if self._video_widget is not None:
            self._video_widget.hide()

        present: list[Path] = []
        missing: list[str] = []
        for media_path in saved.media_paths:
            path = Path(media_path)
            if path.is_file():
                present.append(path)
            else:
                missing.append(media_path)
        self.add_paths(present)
        if self.playlist.count():
            self.playlist.setCurrentRow(0)

        if missing:
            names = ", ".join(Path(path).name for path in missing[:3])
            more = f" and {len(missing) - 3} more" if len(missing) > 3 else ""
            self.status.setText(
                f"Opened “{saved.name}”: loaded {self.playlist.count()} file(s), "
                f"skipped {len(missing)} missing file(s) ({names}{more}). "
                "The saved playlist was kept unchanged."
            )
        else:
            self.status.setText(
                f"Opened “{saved.name}” with {self.playlist.count()} file(s)."
            )

    def remove_selected(self) -> None:
        row = self.playlist.currentRow()
        if row < 0:
            return
        path = self.playlist.item(row).data(Qt.ItemDataRole.UserRole)
        if self._playing_path == os.path.normcase(os.path.abspath(path)):
            self.stop_playback()
        self.playlist.takeItem(row)

    def play_selected(self) -> None:
        row = self.playlist.currentRow()
        if row < 0 and self.playlist.count():
            row = 0
            self.playlist.setCurrentRow(row)
        if row >= 0:
            self._play_row(row)

    def _play_row(self, row: int) -> None:
        item = self.playlist.item(row)
        if item is None:
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        if not path.is_file():
            self.status.setText(f"Media file not found: {path}")
            return
        if not self._ensure_player():
            return
        self.playlist.setCurrentRow(row)
        is_video = path.suffix.casefold() in VIDEO_EXTENSIONS
        self._show_video(is_video, path.name)
        self._playing_path = os.path.normcase(os.path.abspath(path))
        self._player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self._player.play()
        self.play_button.setText("Pause")
        self.status.setText(f"Playing: {path.name}")

    def _ensure_player(self) -> bool:
        if self._player is not None:
            return True
        if self._backend_error is not None:
            self.status.setText(f"Media playback is unavailable: {self._backend_error}")
            return False
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            from PySide6.QtMultimediaWidgets import QVideoWidget

            self._media_module = QMediaPlayer
            self._audio_output = QAudioOutput(self)
            self._audio_output.setVolume(self.volume_slider.value() / 100)
            self._player = QMediaPlayer(self)
            self._player.setAudioOutput(self._audio_output)
            self._video_widget = QVideoWidget(self.video_container)
            self._video_widget.hide()
            self.video_layout.addWidget(self._video_widget)
            self._player.setVideoOutput(self._video_widget)
            self._player.positionChanged.connect(self._position_changed)
            self._player.durationChanged.connect(self._duration_changed)
            self._player.playbackStateChanged.connect(self._playback_state_changed)
            self._player.mediaStatusChanged.connect(self._media_status_changed)
            self._player.errorOccurred.connect(self._playback_error)
            return True
        except Exception as exc:
            self._backend_error = str(exc)
            self.status.setText(
                "Media playback backend could not start. "
                f"Check the local Qt audio/video support: {exc}"
            )
            return False

    def _show_video(self, show_video: bool, filename: str) -> None:
        if not show_video:
            self.video_placeholder.setText(f"Now playing\n\n{filename}")
        if self._video_widget is None:
            return
        self.video_placeholder.setVisible(not show_video)
        self._video_widget.setVisible(show_video)

    def toggle_playback(self) -> None:
        if self._player is not None:
            state = self._player.playbackState()
            if state == self._media_module.PlaybackState.PlayingState:
                self._player.pause()
                return
            if state == self._media_module.PlaybackState.PausedState:
                self._player.play()
                return
        self.play_selected()

    def stop_playback(self) -> None:
        if self._player is not None:
            self._player.stop()
        self._playing_path = None
        self.play_button.setText("Play")
        self.time_label.setText(
            "0:00 / " + _format_time(self.position_slider.maximum())
        )

    def play_previous(self) -> None:
        row = self.playlist.currentRow()
        self._play_row(max(0, row - 1))

    def play_next(self) -> None:
        row = self.playlist.currentRow()
        if row + 1 < self.playlist.count():
            self._play_row(row + 1)

    def _set_volume(self, value: int) -> None:
        if self._audio_output is not None:
            self._audio_output.setVolume(value / 100)

    def _seek(self, position: int) -> None:
        if self._player is not None:
            self._player.setPosition(position)

    def _position_changed(self, position: int) -> None:
        self.position_slider.setValue(position)
        self.time_label.setText(
            f"{_format_time(position)} / "
            f"{_format_time(self.position_slider.maximum())}"
        )

    def _duration_changed(self, duration: int) -> None:
        self.position_slider.setRange(0, duration)
        self.time_label.setText(f"0:00 / {_format_time(duration)}")

    def _playback_state_changed(self, state) -> None:
        if self._media_module is None:
            return
        self.play_button.setText(
            "Pause"
            if state == self._media_module.PlaybackState.PlayingState
            else "Play"
        )

    def _media_status_changed(self, status) -> None:
        if (
            self._media_module is not None
            and status == self._media_module.MediaStatus.EndOfMedia
        ):
            self.play_next()

    def _playback_error(self, _error, message: str) -> None:
        self.status.setText(f"Could not play this media file: {message}")
        self.play_button.setText("Play")
