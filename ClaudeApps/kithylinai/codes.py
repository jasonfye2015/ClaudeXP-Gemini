"""The Codes page: the Furry Code / YIFF Code encoder and decoder (the Timeline's own, from ClaudeCore), with
buttons to make the codes shown the ones Kithylin is told about, and to decode them into the chat."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from . import defaults


class CodesPage(QWidget):
    codes_chosen = Signal(dict)          # {"furcode", "yiffcode"} -> use these in the system prompt
    decode_to_chat = Signal(str)         # the decoded words, as a system message

    def __init__(self, codes):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        intro = QLabel("Type or paste a Furry Code 2.0 or YIFF Code 3.0 to decode it, or build one with the menus. "
                       "\"Use these codes\" tells Kithylin these are his (and rewrites the codes part of the system "
                       "prompt); \"Decode into the chat\" writes out what the codes say.")
        intro.setWordWrap(True)
        intro.setObjectName("hint")
        lay.addWidget(intro)
        self.editor = None
        try:
            from claudecore.furcodes.editor import CodesEditor
            self.editor = CodesEditor(codes.get("furcode", ""), codes.get("yiffcode", ""))
            lay.addWidget(self.editor, 1)
        except Exception as e:                        # standalone without ClaudeCore beside it
            missing = QLabel("The encoder/decoder needs ClaudeCore's furcodes module beside this program "
                             f"(ClaudeCore/claudecore/furcodes). {e}")
            missing.setWordWrap(True)
            lay.addWidget(missing, 1)
        row = QHBoxLayout()
        use = QPushButton("Use these codes for Kithylin")
        use.clicked.connect(lambda: self.codes_chosen.emit(self.codes()))
        decode = QPushButton("Decode into the chat")
        decode.clicked.connect(self._decode)
        reset = QPushButton("Kithylin's own codes")
        reset.clicked.connect(self.reset)
        row.addWidget(use)
        row.addWidget(decode)
        row.addStretch(1)
        row.addWidget(reset)
        lay.addLayout(row)

    def codes(self):
        return self.editor.codes() if self.editor else {}

    def set_codes(self, codes):
        if self.editor:
            self.editor.set_codes(codes)

    def reset(self):
        self.set_codes({"furcode": defaults.KITHYLIN_FURCODE, "yiffcode": defaults.KITHYLIN_YIFFCODE})

    def _decode(self):
        c = self.codes()
        words = defaults.decoded_words(c.get("furcode", ""), c.get("yiffcode", ""))
        head = []
        if c.get("furcode"):
            head.append(f"Furry Code: {c['furcode']}")
        if c.get("yiffcode"):
            head.append(f"YIFF Code: {c['yiffcode']}")
        self.decode_to_chat.emit("\n".join(head + words) if words else "Nothing to decode.")
