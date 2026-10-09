"""A small libretro front end in plain Python (ctypes): loads an emulator core DLL, feeds it a game, and hands back
each frame as a QImage, the sound as 16-bit stereo samples, and asks us which buttons are held.

Only what a NES core needs is implemented. Cores keep global state, so only one Core may be loaded at a time."""
import ctypes
from ctypes import (CFUNCTYPE, POINTER, Structure, c_bool, c_char_p, c_double, c_float, c_int16, c_size_t, c_uint,
                    c_void_p)

from PySide6.QtGui import QImage

# environment commands we answer
ENV_GET_CAN_DUPE = 3
ENV_GET_SYSTEM_DIRECTORY = 9
ENV_SET_PIXEL_FORMAT = 10
ENV_GET_VARIABLE = 15
ENV_GET_VARIABLE_UPDATE = 17
ENV_GET_SAVE_DIRECTORY = 31
ENV_GET_CORE_OPTIONS_VERSION = 52

PIXEL_0RGB1555, PIXEL_XRGB8888, PIXEL_RGB565 = 0, 1, 2
DEVICE_JOYPAD = 1
MEMORY_SAVE_RAM = 0

# joypad button ids
B, Y, SELECT, START, UP, DOWN, LEFT, RIGHT, A, X, L, R = range(12)


class GameInfo(Structure):
    _fields_ = [("path", c_char_p), ("data", c_void_p), ("size", c_size_t), ("meta", c_char_p)]


class SystemInfo(Structure):
    _fields_ = [("library_name", c_char_p), ("library_version", c_char_p), ("valid_extensions", c_char_p),
                ("need_fullpath", c_bool), ("block_extract", c_bool)]


class Geometry(Structure):
    _fields_ = [("base_width", c_uint), ("base_height", c_uint), ("max_width", c_uint), ("max_height", c_uint),
                ("aspect_ratio", c_float)]


class Timing(Structure):
    _fields_ = [("fps", c_double), ("sample_rate", c_double)]


class AVInfo(Structure):
    _fields_ = [("geometry", Geometry), ("timing", Timing)]


class Variable(Structure):
    _fields_ = [("key", c_char_p), ("value", c_char_p)]


ENV_CB = CFUNCTYPE(c_bool, c_uint, c_void_p)
VIDEO_CB = CFUNCTYPE(None, c_void_p, c_uint, c_uint, c_size_t)
AUDIO_CB = CFUNCTYPE(None, c_int16, c_int16)
AUDIO_BATCH_CB = CFUNCTYPE(c_size_t, POINTER(c_int16), c_size_t)
POLL_CB = CFUNCTYPE(None)
STATE_CB = CFUNCTYPE(c_int16, c_uint, c_uint, c_uint, c_uint)


class Core:
    """One loaded core. buttons: a set of joypad ids held on port 0 (the owner updates it)."""

    def __init__(self, dll_path, system_dir, save_dir):
        self.dll = ctypes.CDLL(str(dll_path))
        self.system_dir = str(system_dir).encode("mbcs", "replace")
        self.save_dir = str(save_dir).encode("mbcs", "replace")
        self._system_p = c_char_p(self.system_dir)
        self._save_p = c_char_p(self.save_dir)
        self.pixel_format = PIXEL_0RGB1555
        self.frame = None                     # the latest QImage
        self.audio = bytearray()              # 16-bit stereo samples since the last take_audio()
        self.buttons = set()
        self.game = None                      # keeps the ROM bytes alive while loaded
        d = self.dll
        d.retro_get_system_av_info.argtypes = [POINTER(AVInfo)]
        d.retro_get_system_info.argtypes = [POINTER(SystemInfo)]
        d.retro_load_game.argtypes = [POINTER(GameInfo)]
        d.retro_load_game.restype = c_bool
        d.retro_serialize_size.restype = c_size_t
        d.retro_serialize.argtypes = [c_void_p, c_size_t]
        d.retro_serialize.restype = c_bool
        d.retro_unserialize.argtypes = [c_void_p, c_size_t]
        d.retro_unserialize.restype = c_bool
        d.retro_get_memory_data.argtypes = [c_uint]
        d.retro_get_memory_data.restype = c_void_p
        d.retro_get_memory_size.argtypes = [c_uint]
        d.retro_get_memory_size.restype = c_size_t
        # the callbacks must stay referenced for as long as the core can call them
        self._cbs = [ENV_CB(self._environment), VIDEO_CB(self._video), AUDIO_CB(self._audio_one),
                     AUDIO_BATCH_CB(self._audio_batch), POLL_CB(lambda: None), STATE_CB(self._input)]
        d.retro_set_environment(self._cbs[0])
        d.retro_init()
        d.retro_set_video_refresh(self._cbs[1])
        d.retro_set_audio_sample(self._cbs[2])
        d.retro_set_audio_sample_batch(self._cbs[3])
        d.retro_set_input_poll(self._cbs[4])
        d.retro_set_input_state(self._cbs[5])
        info = SystemInfo()
        d.retro_get_system_info(ctypes.byref(info))
        self.name = (info.library_name or b"").decode("utf-8", "replace")
        self.version = (info.library_version or b"").decode("utf-8", "replace")
        self.need_fullpath = bool(info.need_fullpath)
        self.av = AVInfo()

    # ---- the game -----------------------------------------------------------------------------------------
    def load(self, path):
        data = open(path, "rb").read()
        buf = ctypes.create_string_buffer(data, len(data))
        self.game = (buf, str(path).encode("mbcs", "replace"))
        gi = GameInfo(self.game[1], ctypes.cast(buf, c_void_p), len(data), None)
        if not self.dll.retro_load_game(ctypes.byref(gi)):
            self.game = None
            return False
        self.dll.retro_get_system_av_info(ctypes.byref(self.av))
        return True

    def unload(self):
        if self.game is not None:
            self.dll.retro_unload_game()
            self.game = None

    def close(self):
        self.unload()
        self.dll.retro_deinit()

    def run(self):
        """Emulate one frame (~1/60 s)."""
        self.dll.retro_run()

    def reset(self):
        self.dll.retro_reset()

    @property
    def fps(self):
        return self.av.timing.fps or 60.0988

    @property
    def sample_rate(self):
        return int(self.av.timing.sample_rate or 44100)

    def take_audio(self):
        data, self.audio = bytes(self.audio), bytearray()
        return data

    # ---- battery saves and save states --------------------------------------------------------------------
    def save_ram(self):
        size = self.dll.retro_get_memory_size(MEMORY_SAVE_RAM)
        ptr = self.dll.retro_get_memory_data(MEMORY_SAVE_RAM)
        return ctypes.string_at(ptr, size) if size and ptr else b""

    def load_ram(self, data):
        size = self.dll.retro_get_memory_size(MEMORY_SAVE_RAM)
        ptr = self.dll.retro_get_memory_data(MEMORY_SAVE_RAM)
        if size and ptr and data:
            ctypes.memmove(ptr, data, min(size, len(data)))

    def save_state(self):
        size = self.dll.retro_serialize_size()
        buf = ctypes.create_string_buffer(size)
        return buf.raw if size and self.dll.retro_serialize(buf, size) else b""

    def load_state(self, data):
        buf = ctypes.create_string_buffer(data, len(data))
        return bool(self.dll.retro_unserialize(buf, len(data)))

    # ---- callbacks from the core ----------------------------------------------------------------------------
    def _environment(self, cmd, data):
        cmd &= 0xFFFF                                     # drop the 'experimental' flag
        try:
            if cmd == ENV_SET_PIXEL_FORMAT:
                fmt = ctypes.cast(data, POINTER(c_uint))[0]
                if fmt in (PIXEL_XRGB8888, PIXEL_RGB565, PIXEL_0RGB1555):
                    self.pixel_format = fmt
                    return True
                return False
            if cmd == ENV_GET_CAN_DUPE:
                ctypes.cast(data, POINTER(c_bool))[0] = True
                return True
            if cmd == ENV_GET_SYSTEM_DIRECTORY:
                ctypes.cast(data, POINTER(c_char_p))[0] = self._system_p.value
                return True
            if cmd == ENV_GET_SAVE_DIRECTORY:
                ctypes.cast(data, POINTER(c_char_p))[0] = self._save_p.value
                return True
            if cmd == ENV_GET_VARIABLE:
                ctypes.cast(data, POINTER(Variable))[0].value = None
                return False
            if cmd == ENV_GET_VARIABLE_UPDATE:
                ctypes.cast(data, POINTER(c_bool))[0] = False
                return True
            if cmd == ENV_GET_CORE_OPTIONS_VERSION:
                ctypes.cast(data, POINTER(c_uint))[0] = 0
                return True
        except (ValueError, OSError):
            return False
        return False

    def _video(self, data, width, height, pitch):
        if not data:                                      # 'dupe': the picture didn't change
            return
        raw = ctypes.string_at(data, pitch * height)
        fmt = {PIXEL_XRGB8888: QImage.Format_RGB32, PIXEL_RGB565: QImage.Format_RGB16,
               PIXEL_0RGB1555: QImage.Format_RGB555}[self.pixel_format]
        self.frame = QImage(raw, width, height, pitch, fmt).copy()

    def _audio_one(self, left, right):
        self.audio += ctypes.string_at(ctypes.addressof(c_int16(left)), 2)
        self.audio += ctypes.string_at(ctypes.addressof(c_int16(right)), 2)

    def _audio_batch(self, data, frames):
        self.audio += ctypes.string_at(data, frames * 4)
        return frames

    def _input(self, port, device, index, button):
        if port == 0 and device == DEVICE_JOYPAD:
            return 1 if button in self.buttons else 0
        return 0
