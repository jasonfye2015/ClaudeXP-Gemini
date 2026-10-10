"""Runs a program under the debugger for Copilot Python Studio. Started by the studio with:
    python dbg_runner.py <port> <script> <breakpoints-json>
It talks to the studio over a local socket, one JSON message per line, so the program's own input and output are
untouched."""
import bdb
import json
import os
import socket
import sys
import traceback

START_STEPPING = False
MAX_VALUE = 200
MAX_ITEMS = 80


def short(value):
    try:
        text = repr(value)
    except Exception as exc:  # a broken __repr__ must not stop the debugger
        text = f"<repr failed: {exc.__class__.__name__}>"
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE] + "..."


class Debugger(bdb.Bdb):
    def __init__(self, sock, script):
        super().__init__()
        self.io = sock.makefile("rwb", buffering=0)
        self.script = os.path.normcase(os.path.abspath(script))
        self.root = os.path.normcase(os.path.dirname(self.script))
        self.frame = None

    # ---- messages ------------------------------------------------------------------------------------
    def send(self, **msg):
        self.io.write((json.dumps(msg) + "\n").encode("utf-8"))

    def receive(self):
        line = self.io.readline()
        if not line:
            raise bdb.BdbQuit
        return json.loads(line.decode("utf-8"))

    # ---- what counts as the user's own code ----------------------------------------------------------
    def is_user(self, filename):
        name = os.path.normcase(os.path.abspath(filename))
        return name.startswith(self.root) and "site-packages" not in name and "python312" not in name \
            and not name.endswith("dbg_runner.py")

    def stop_here(self, frame):
        return self.is_user(frame.f_code.co_filename) and super().stop_here(frame)

    def user_line(self, frame):
        self.pause(frame)

    def user_exception(self, frame, exc_info):
        if exc_info[0] is not KeyboardInterrupt and self.is_user(frame.f_code.co_filename) and self.catch_errors:
            self.send(ev="exception", text="".join(traceback.format_exception_only(exc_info[0], exc_info[1])).strip())
            self.catch_errors = False
            self.pause(frame)

    catch_errors = True

    # ---- stopping --------------------------------------------------------------------------------------
    def snapshot(self, frame):
        def table(mapping):
            rows = []
            for name, value in list(mapping.items())[:MAX_ITEMS * 3]:
                if name.startswith("__") or type(value).__name__ in ("module", "function", "type", "builtin_function_or_method"):
                    continue
                rows.append([name, type(value).__name__, short(value)])
                if len(rows) >= MAX_ITEMS:
                    break
            return rows
        stack, f = [], frame
        while f is not None:
            if self.is_user(f.f_code.co_filename):
                stack.append([f.f_code.co_filename, f.f_lineno, f.f_code.co_name])
            f = f.f_back
        return {"file": frame.f_code.co_filename, "line": frame.f_lineno, "func": frame.f_code.co_name,
                "locals": table(frame.f_locals if frame.f_code.co_name != "<module>" else {}),
                "globals": table(frame.f_globals), "stack": stack}

    def pause(self, frame):
        self.frame = frame
        self.send(ev="stop", **self.snapshot(frame))
        while True:
            msg = self.receive()
            cmd = msg.get("cmd")
            if cmd == "continue":
                self.set_continue()
                return
            if cmd == "step":
                self.set_step()
                return
            if cmd == "next":
                self.set_next(frame)
                return
            if cmd == "out":
                self.set_return(frame)
                return
            if cmd == "quit":
                raise bdb.BdbQuit
            if cmd == "break":
                self.set_break(os.path.abspath(msg["file"]), int(msg["line"]))
            if cmd == "clear":
                self.clear_break(os.path.abspath(msg["file"]), int(msg["line"]))
            if cmd == "eval":
                try:
                    result = short(eval(msg["expr"], frame.f_globals, frame.f_locals))
                except Exception as exc:
                    result = f"{exc.__class__.__name__}: {exc}"
                self.send(ev="eval", expr=msg["expr"], result=result)


def main():
    global START_STEPPING
    port, script, breaks = int(sys.argv[1]), sys.argv[2], json.loads(sys.argv[3])
    START_STEPPING = len(sys.argv) > 4 and sys.argv[4] == "step"
    sock = socket.create_connection(("127.0.0.1", port), timeout=15)
    sock.settimeout(None)
    dbg = Debugger(sock, script)
    for file, lines in breaks.items():
        for n in lines:
            dbg.set_break(os.path.abspath(file), int(n))
    with open(script, "rb") as f:
        source = f.read()
    sys.argv = [script]
    sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
    namespace = {"__name__": "__main__", "__file__": script, "__builtins__": __builtins__, "__doc__": None}
    code = compile(source, script, "exec")
    status = 0
    try:
        if START_STEPPING:
            dbg.reset()
            dbg.set_step()
            sys.settrace(dbg.trace_dispatch)
            try:
                exec(code, namespace, namespace)
            finally:
                sys.settrace(None)
                dbg.quitting = True
        else:
            # a stopframe that never matches keeps bdb from pausing on the first line
            dbg.reset()
            dbg._set_stopinfo(object(), None, -1)
            sys.settrace(dbg.trace_dispatch)
            try:
                exec(code, namespace, namespace)
            finally:
                sys.settrace(None)
                dbg.quitting = True
    except bdb.BdbQuit:
        status = 1
    except SystemExit as exc:
        status = exc.code if isinstance(exc.code, int) else 0
    except BaseException:
        traceback.print_exc()
        status = 1
    try:
        dbg.send(ev="end", code=status)
    except Exception:
        pass
    sys.stdout.flush()
    os._exit(status)


if __name__ == "__main__":
    main()
