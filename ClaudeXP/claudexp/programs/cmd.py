"""Command Prompt: a cmd.exe for the virtual drives. dir, cd, type, md, rd, del (to the Recycle Bin), copy,
ren, tree, cls, ver, echo, title, color, date/time, ipconfig, ping (needs the dial-up), hostname, shutdown,
format c: (restarts into System Recovery), start, exit, and program names (notepad, calc, winmine...)."""
import random
import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap, QTextCursor
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from .. import clock, network
from ..wm import XPWindow

BANNER = "Microsoft Windows XP [Version 5.1.2600]\n(C) Copyright 1985-2001 Microsoft Corp.\n"
NOT_FOUND = "'{0}' is not recognized as an internal or external command,\noperable program or batch file."
PALETTE = ["#000000", "#000080", "#008000", "#008080", "#800000", "#800080", "#808000", "#C0C0C0",
           "#808080", "#0000FF", "#00FF00", "#00FFFF", "#FF0000", "#FF00FF", "#FFFF00", "#FFFFFF"]
HELP = """For more information on a specific command, type the command name.
CD             Displays the name of or changes the current directory.
CLS            Clears the screen.
COLOR          Sets the default console foreground and background colors.
COPY           Copies one or more files to another location.
DATE           Displays the date.
DEL            Deletes one or more files.
DIR            Displays a list of files and subdirectories in a directory.
ECHO           Displays messages.
EXIT           Quits the CMD.EXE program (command interpreter).
FORMAT         Formats a disk for use with Windows.
HOSTNAME       Prints the name of this computer.
IPCONFIG       Displays the dial-up connection's IP address.
MD             Creates a directory.
PING           Checks a connection to another computer.
RD             Removes a directory.
REN            Renames a file or files.
SHUTDOWN       Shuts down (-s) or restarts (-r) the computer.
START          Starts a program, opens a folder or a web address.
TIME           Displays the system time.
TITLE          Sets the window title for a CMD.EXE session.
TREE           Graphically displays the directory structure of a drive or path.
TYPE           Displays the contents of a text file.
VER            Displays the Windows XP version."""


def cmd_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setPen(QPen(QColor("#5070A0"), 1))
    p.setBrush(QColor("#D8E4F8"))
    p.drawRect(QRectF(2.5, 4.5, 27, 23))
    p.fillRect(QRectF(3, 5, 27, 4), QColor("#2A5DD6"))
    p.fillRect(QRectF(5, 11, 22, 14), QColor("black"))
    f = QFont("Lucida Console")
    f.setPixelSize(8)
    p.setFont(f)
    p.setPen(QColor("#C0C0C0"))
    p.drawText(QRectF(6, 12, 22, 10), Qt.AlignLeft, "C:\\>")
    p.end()
    return QIcon(pm)


def _when(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    try:
        dt = dt.replace(year=clock.YEAR)
    except ValueError:
        dt = dt.replace(year=clock.YEAR, day=28)
    return dt.strftime("%m/%d/%Y  %I:%M %p")


class CommandPrompt(QPlainTextEdit):
    def __init__(self, desktop):
        super().__init__()
        from ..explorer import vfs
        self.desktop = desktop
        self.frame = None
        vfs.setup_c()
        self.cwd = {"C": vfs.user_home(), "E": vfs.local_storage()}
        self.drive = "C"
        self.history, self.hist_pos = [], 0
        self.pending = None          # a function waiting for the next typed line (Y/N questions)
        self.busy = False            # ping is printing
        self.input_start = 0
        font = QFont("Lucida Console")
        font.setPixelSize(13)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setUndoRedoEnabled(False)
        self.set_colors("#000000", "#C0C0C0")
        self.write(BANNER + "\n")
        self.prompt()

    # ---- the console --------------------------------------------------------------------------------------
    def set_colors(self, bg, fg):
        self.setStyleSheet(f"QPlainTextEdit {{ background: {bg}; color: {fg}; border: none; "
                           f"selection-background-color: {fg}; selection-color: {bg}; }}")

    def write(self, text):
        cur = self.textCursor()
        cur.movePosition(QTextCursor.End)
        cur.insertText(text)
        self.setTextCursor(cur)
        self.ensureCursorVisible()

    def println(self, text=""):
        self.write(text + "\n")

    def here(self):
        from ..explorer import vfs
        return vfs.to_virtual(self.cwd[self.drive]) or f"{self.drive}:\\"

    def prompt(self):
        self.write(f"{self.here()}>")
        self.input_start = self.textCursor().position()

    def current_input(self):
        return self.toPlainText()[self.input_start:]

    def replace_input(self, text):
        cur = self.textCursor()
        cur.setPosition(self.input_start)
        cur.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cur.insertText(text)
        self.setTextCursor(cur)

    def keyPressEvent(self, event):
        key, mods = event.key(), event.modifiers()
        if self.busy:
            if key == Qt.Key_C and mods & Qt.ControlModifier:
                self.busy = False
                self.println("^C")
                self.prompt()
            return
        cur = self.textCursor()
        if mods & Qt.ControlModifier and key == Qt.Key_C and cur.hasSelection():
            QApplication.clipboard().setText(cur.selectedText())
            return
        if mods & Qt.ControlModifier and key == Qt.Key_C:
            self.write("^C\n")
            self.pending = None
            self.prompt()
            return
        if key in (Qt.Key_Return, Qt.Key_Enter):
            line = self.current_input()
            self.write("\n")
            self.run_line(line)
            return
        if key == Qt.Key_Up or key == Qt.Key_Down:
            if self.history:
                self.hist_pos = max(0, min(len(self.history), self.hist_pos + (-1 if key == Qt.Key_Up else 1)))
                self.replace_input(self.history[self.hist_pos] if self.hist_pos < len(self.history) else "")
            return
        if key == Qt.Key_Escape:
            self.replace_input("")
            return
        if cur.position() < self.input_start or cur.anchor() < self.input_start:
            cur.movePosition(QTextCursor.End)
            self.setTextCursor(cur)
        if key in (Qt.Key_Backspace, Qt.Key_Left) and self.textCursor().position() <= self.input_start \
                and not self.textCursor().hasSelection():
            return
        if key == Qt.Key_Home:
            cur = self.textCursor()
            cur.setPosition(self.input_start)
            self.setTextCursor(cur)
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        cur = self.textCursor()
        if cur.position() < self.input_start:
            cur.movePosition(QTextCursor.End)
            self.setTextCursor(cur)
        self.textCursor().insertText(source.text().replace("\r", "").split("\n")[0])

    # ---- commands -------------------------------------------------------------------------------------------
    def run_line(self, line):
        if self.pending is not None:
            pending, self.pending = self.pending, None
            pending(line.strip())
            if self.pending is None and not self.busy:
                self.prompt()
            return
        line = line.strip()
        if line:
            self.history.append(line)
        self.hist_pos = len(self.history)
        if line:
            try:
                self.execute(line)
            except OSError as e:
                self.println(f"{e.strerror or 'Access is denied.'}")
        if self.pending is None and not self.busy:
            if line and self.toPlainText()[-2:] != "\n\n":
                self.println()
            self.prompt()

    def execute(self, line):
        if len(line) == 2 and line[1] == ":":
            return self.change_drive(line[0].upper())
        low = line.lower()
        if low.startswith("echo."):
            return self.println(line[5:])
        if low.startswith(("cd..", "cd\\", "cd/")):
            return self.do_cd(line[2:])
        word, _, rest = line.partition(" ")
        name = {"chdir": "cd", "mkdir": "md", "rmdir": "rd", "erase": "del", "rename": "ren",
                "/?": "help"}.get(word.lower(), word.lower())
        handler = getattr(self, "do_" + name, None) if name.isalpha() else None
        if handler is not None:
            return handler(rest.strip())
        from .commands import resolve
        action = resolve(self.desktop, line if " " not in line else word, self.cwd[self.drive])
        if action is not None:
            action()
        else:
            self.println(NOT_FOUND.format(word))

    def path(self, arg):
        """A typed path -> real Path (relative to the current folder), or None if it leaves the drive."""
        from ..explorer import vfs
        arg = arg.strip().strip('"')
        if len(arg) >= 2 and arg[1] == ":":
            real = vfs.to_real(arg)
            if real is None:
                return None
            root = vfs.drive(arg[0]).root
        else:
            root = vfs.drive(self.drive).root
            real = root / arg.lstrip("\\") if arg.startswith("\\") else self.cwd[self.drive] / arg
        real = Path(real).resolve()
        if real != root.resolve() and root.resolve() not in real.parents:
            return root.resolve()
        return real

    def change_drive(self, letter):
        from ..explorer import vfs
        d = vfs.drive(letter)
        if d is None:
            self.println("The system cannot find the drive specified.")
        elif d.root is None:
            self.println("The device is not ready.")
        else:
            self.cwd.setdefault(letter, d.root)
            self.drive = letter

    def do_help(self, rest):
        self.println(HELP)

    def do_cls(self, rest):
        self.clear()

    def do_ver(self, rest):
        self.println("\nMicrosoft Windows XP [Version 5.1.2600]")

    def do_echo(self, rest):
        self.println(rest if rest else "ECHO is on.")

    def do_title(self, rest):
        if self.frame is not None:
            self.frame.set_title(rest or "C:\\WINDOWS\\System32\\cmd.exe")

    def do_color(self, rest):
        code = rest.strip()
        if not code:
            return self.set_colors("#000000", "#C0C0C0")
        try:
            value = int(code, 16)
        except ValueError:
            return self.println("Sets the default console foreground and background colors.\n\nCOLOR [attr]")
        bg, fg = (value >> 4) & 15, value & 15
        if len(code) == 1:
            bg, fg = 0, value
        if bg == fg:
            return
        self.set_colors(PALETTE[bg], PALETTE[fg])

    def do_date(self, rest):
        now = clock.now()
        text = now.strftime("%a %m/%d/%Y")
        self.println(text if "/t" in rest.lower() else f"The current date is: {text}")

    def do_time(self, rest):
        now = clock.now()
        self.println(now.strftime("%I:%M %p") if "/t" in rest.lower() else
                     f"The current time is: {now.strftime('%H:%M:%S')}.{random.randint(10, 99)}")

    def do_cd(self, rest):
        rest = rest.strip()
        if not rest:
            return self.println(self.here())
        target = self.path(rest)
        if target is None or not target.is_dir():
            return self.println("The system cannot find the path specified.")
        letter = rest[0].upper() if len(rest) >= 2 and rest[1] == ":" else self.drive
        self.cwd[letter] = target

    def do_dir(self, rest):
        from ..explorer import vfs
        wide = "/w" in rest.lower()
        arg = " ".join(a for a in rest.split() if not a.startswith("/"))
        pattern = "*"
        target = self.path(arg) if arg else self.cwd[self.drive]
        if target is not None and not target.exists() and any(ch in target.name for ch in "*?"):
            pattern, target = target.name, target.parent
        if target is None or not target.exists():
            return self.println("File Not Found")
        if target.is_file():
            pattern, target = target.name, target.parent
        letter = (vfs.to_virtual(target) or "C:")[0]
        self.println(f" Volume in drive {letter} has no label.")
        self.println(" Volume Serial Number is 3C2A-17F9\n")
        self.println(f" Directory of {vfs.to_virtual(target)}\n")
        entries = [p for p in sorted(target.glob(pattern), key=lambda p: p.name.lower())
                   if not vfs.hidden(p)]
        is_root = target == vfs.drive(letter).root
        files = dirs = total = 0
        rows = [] if is_root else [(".", None, target.stat().st_mtime), ("..", None, target.stat().st_mtime)]
        rows += [(p.name, None if p.is_dir() else p.stat().st_size, p.stat().st_mtime) for p in entries]
        wide_names = []
        for name, size, mtime in rows:
            if size is None:
                dirs += 1
                wide_names.append(f"[{name}]")
                if not wide:
                    self.println(f"{_when(mtime)}    <DIR>          {name}")
            else:
                files += 1
                total += size
                wide_names.append(name)
                if not wide:
                    self.println(f"{_when(mtime)}  {size:>16,} {name}")
        if wide:
            for i in range(0, len(wide_names), 5):
                self.println("".join(n[:15].ljust(16) for n in wide_names[i:i + 5]))
        usage = vfs.drive(letter).usage()
        free = usage[1] if usage else 0
        self.println(f"{files:>16} File(s) {total:>14,} bytes")
        self.println(f"{dirs:>16} Dir(s) {free:>15,} bytes free")

    def do_type(self, rest):
        target = self.path(rest)
        if target is None or not target.is_file():
            return self.println("The system cannot find the file specified.")
        data = target.read_bytes()[:200_000]
        self.println(data.decode("utf-8", errors="replace").replace("\r\n", "\n"))

    def do_md(self, rest):
        target = self.path(rest)
        if not rest or target is None:
            return self.println("The syntax of the command is incorrect.")
        if target.exists():
            return self.println(f"A subdirectory or file {rest} already exists.")
        target.mkdir(parents=True)

    def do_rd(self, rest):
        from ..explorer import vfs
        target = self.path(rest)
        if not rest or target is None or not target.is_dir():
            return self.println("The system cannot find the file specified.")
        if vfs.protected(target) or target == self.cwd[self.drive]:
            return self.println("Access is denied.")
        if any(target.iterdir()):
            return self.println("The directory is not empty.")
        target.rmdir()

    def do_del(self, rest):
        from ..explorer import vfs
        if not rest:
            return self.println("The syntax of the command is incorrect.")
        target = self.path(rest)
        matches = [target] if target is not None and target.is_file() else \
            ([p for p in target.parent.glob(target.name) if p.is_file()] if target is not None else [])
        if target is not None and target.is_dir():
            matches = [p for p in target.iterdir() if p.is_file()]
        if not matches:
            return self.println(f"Could Not Find {rest}")
        for p in matches:
            if vfs.protected(p):
                self.println(f"Access is denied - {p.name}")
            else:
                vfs.recycle(p)          # kinder than the real del: it goes to the Recycle Bin

    def do_copy(self, rest):
        parts = rest.split()
        if len(parts) != 2:
            return self.println("The syntax of the command is incorrect.")
        src, dst = self.path(parts[0]), self.path(parts[1])
        if src is None or not src.is_file():
            return self.println("The system cannot find the file specified.")
        if dst.is_dir():
            dst = dst / src.name
        shutil.copy2(src, dst)
        self.println("        1 file(s) copied.")

    def do_ren(self, rest):
        parts = rest.split()
        if len(parts) != 2 or any(c in parts[1] for c in "\\/:"):
            return self.println("The syntax of the command is incorrect.")
        src = self.path(parts[0])
        if src is None or not src.exists():
            return self.println("The system cannot find the file specified.")
        dst = src.parent / parts[1]
        if dst.exists():
            return self.println("A duplicate file name exists, or the file\ncannot be found.")
        src.rename(dst)

    def do_tree(self, rest):
        from ..explorer import vfs
        target = self.path(rest) if rest else self.cwd[self.drive]
        if target is None or not target.is_dir():
            return self.println("Invalid path - " + rest)
        self.println("Folder PATH listing\nVolume serial number is 3C2A-17F9")
        self.println(vfs.to_virtual(target))
        count = [0]

        def walk(folder, prefix, depth):
            subs = [p for p in sorted(folder.iterdir(), key=lambda p: p.name.lower()) if p.is_dir() and not vfs.hidden(p)]
            for i, sub in enumerate(subs):
                if count[0] > 300:
                    return
                count[0] += 1
                last = i == len(subs) - 1
                self.println(prefix + ("\\---" if last else "+---") + sub.name)
                if depth < 4:
                    walk(sub, prefix + ("    " if last else "|   "), depth + 1)
        walk(target, "", 0)

    def do_hostname(self, rest):
        from .. import user
        self.println(user.account().data.get("computer") or "HOME-XP")

    def do_ipconfig(self, rest):
        self.println("\nWindows IP Configuration\n")
        if network.is_connected():
            dsl = network.is_broadband()
            self.println(f"PPP adapter {network.connection_name()}:\n")
            self.println(f"        Connection-specific DNS Suffix  . : {'dsl.net' if dsl else 'aol.com'}")
            self.println(f"        IP Address. . . . . . . . . . . . : {self._ip()}")
            self.println("        Subnet Mask . . . . . . . . . . . : 255.255.255.255")
            self.println(f"        Default Gateway . . . . . . . . . : {self._ip()}")

    def _ip(self):
        if not hasattr(self, "_my_ip"):
            self._my_ip = f"152.163.{random.randint(1, 254)}.{random.randint(1, 254)}"
        return self._my_ip

    def do_ping(self, rest):
        host = (rest.split() or [""])[0]
        if not host:
            return self.println("Usage: ping target_name")
        if not network.is_connected():
            return self.println(f"Ping request could not find host {host}. Please check the name and try again.")
        ip = host if host.replace(".", "").isdigit() else \
            f"{random.randint(64, 216)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
        self.println(f"\nPinging {host} [{ip}] with 32 bytes of data:\n")
        self.busy = True
        times = []

        def reply(n):
            if not self.busy:
                return
            if n == 4:
                self.println(f"\nPing statistics for {ip}:")
                self.println("    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),")
                self.println("Approximate round trip times in milli-seconds:")
                self.println(f"    Minimum = {min(times)}ms, Maximum = {max(times)}ms, "
                             f"Average = {sum(times) // len(times)}ms\n")
                self.busy = False
                self.prompt()
                return
            t = random.randint(18, 45) if network.is_broadband() else random.randint(120, 290)   # DSL or 56k
            times.append(t)
            self.println(f"Reply from {ip}: bytes=32 time={t}ms TTL=49")
            QTimer.singleShot(1000, lambda: reply(n + 1))
        QTimer.singleShot(400, lambda: reply(0))

    def do_shutdown(self, rest):
        flags = rest.lower()
        app = self.desktop.window()
        if "-s" in flags or "/s" in flags:
            self.println("Windows is shutting down.")
            QTimer.singleShot(1000, self.desktop.turn_off)
        elif "-r" in flags or "/r" in flags:
            self.println("Windows is restarting.")
            QTimer.singleShot(1000, app.restart)
        elif "-l" in flags or "/l" in flags:
            QTimer.singleShot(500, self.desktop.log_off)
        else:
            self.println("Usage: shutdown [-l | -s | -r]\n\n    -l    Log off\n    -s    Shutdown the computer\n"
                         "    -r    Shutdown and restart the computer")

    def do_format(self, rest):
        letter = rest.strip()[:1].upper()
        if not letter:
            return self.println("Required parameter missing -")
        if letter in ("B", "D"):
            return self.println(f"Insert new disk for drive {letter}:\nThe device is not ready.")
        if letter != "C":
            return self.println("Access is denied.")
        self.println("The type of the file system is NTFS.\n\nWARNING, ALL DATA ON NON-REMOVABLE DISK\n"
                     "DRIVE C: WILL BE LOST!")
        self.write("Proceed with Format (Y/N)? ")

        def answer(text):
            if text.lower().startswith("y"):
                self.println("\nDrive C: is in use by Windows. Windows will restart and start\n"
                             "System Recovery so the drive can be formatted.")
                self.busy = True
                QTimer.singleShot(2500, lambda: self.desktop.window().restart(recovery=True))
            else:
                self.println()
        self.pending = answer

    def do_start(self, rest):
        from .commands import resolve
        if not rest:
            return open_cmd(self.desktop)
        action = resolve(self.desktop, rest, self.cwd[self.drive])
        if action is None:
            self.println(f"The system cannot find the file {rest}.")
        else:
            action()

    def do_cmd(self, rest):
        self.println(BANNER)

    def do_exit(self, rest):
        if self.frame is not None:
            QTimer.singleShot(0, self.frame.request_close)


def open_cmd(desktop):
    body = CommandPrompt(desktop)
    win = XPWindow(desktop, "C:\\WINDOWS\\System32\\cmd.exe", body, cmd_icon(), size=(680, 420))
    body.frame = win
    desktop.open_window(win)
    body.setFocus()
    return win
