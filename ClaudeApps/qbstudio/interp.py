"""QBasic, for Claude QBasic Studio: a lexer, a one-pass compiler (statements become a flat list of small Python
closures with jumps, per SUB and FUNCTION) and a machine that runs them on a worker thread.

What it speaks: QBasic 1.1 as programs actually use it - line numbers and labels, GOTO/GOSUB, block and one-line IF,
SELECT CASE, FOR/WHILE/DO loops and EXIT, SUBs and FUNCTIONs with by-reference arguments, STATIC and SHARED, DIM
(arrays of any rank, bounds, user TYPEs), REDIM, CONST, DEFtype, DATA/READ/RESTORE, the string, maths and conversion
functions, PRINT (USING, TAB, SPC, zones), INPUT/LINE INPUT/INKEY$, files (OPEN/PRINT#/INPUT#/LINE INPUT#/WRITE#/
EOF), ON ERROR/RESUME, the screen (CLS, LOCATE, COLOR, SCREEN 0-13 with pages and PCOPY, PSET, LINE, CIRCLE, PAINT,
DRAW, GET/PUT sprites, POINT, PALETTE) and sound (BEEP, SOUND, PLAY). The screen is screen.Screen."""
import math
import os
import random
import re
import threading
import time
from collections import deque
from datetime import datetime


# ---- errors ----------------------------------------------------------------------------------------------------------
class BasicError(Exception):
    """A QBasic error: its message, number and the line it happened on."""
    CODES = {"NEXT without FOR": 1, "Syntax error": 2, "RETURN without GOSUB": 3, "Out of DATA": 4,
             "Illegal function call": 5, "Overflow": 6, "Out of memory": 7, "Label not defined": 8,
             "Subscript out of range": 9, "Duplicate definition": 10, "Division by zero": 11, "Type mismatch": 13,
             "Out of string space": 14, "String formula too complex": 16, "No RESUME": 19,
             "RESUME without error": 20, "Out of stack space": 28, "Bad file name or number": 52,
             "File not found": 53, "Bad file mode": 54, "File already open": 55, "Input past end of file": 62,
             "Bad file name": 64, "Path/File access error": 75, "Path not found": 76}

    def __init__(self, message, line=None, code=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.code = code or self.CODES.get(message, 5 if message.startswith("Illegal") else 2)

    def __str__(self):
        return f"{self.message} in line {self.line}" if self.line else self.message


class CompileError(BasicError):
    pass


class EndProgram(Exception):
    pass


class StopProgram(Exception):
    """The Stop button (or the window closing)."""


# ---- the lexer -------------------------------------------------------------------------------------------------------
KEYWORDS = set("""ACCESS AND ANY APPEND AS BASE BEEP BINARY BYVAL CALL CASE CHAIN CHDIR CIRCLE CLEAR CLOSE CLS COLOR
COMMON CONST DATA DECLARE DEF DEFDBL DEFINT DEFLNG DEFSNG DEFSTR DIM DO DOUBLE DRAW ELSE ELSEIF END EQV ERASE ERROR
EXIT FIELD FILES FOR FUNCTION GET GOSUB GOTO IF IMP INPUT INTEGER IS KEY KILL LET LINE LOCATE LONG LOOP LPRINT LSET
MKDIR MOD NAME NEXT NOT OFF ON OPEN OPTION OR OUT OUTPUT PAINT PALETTE PCOPY PLAY POKE PRESET PRINT PSET PUT RANDOM
RANDOMIZE READ REDIM REM RESET RESTORE RESUME RETURN RMDIR RSET RUN SCREEN SEEK SELECT SHARED SHELL SINGLE SLEEP SOUND
STATIC STEP STOP STRING SUB SWAP SYSTEM THEN TO TROFF TRON TYPE UNLOCK UNTIL USING VIEW WAIT WEND WHILE WIDTH WINDOW
WRITE XOR""".split())
TOKEN = re.compile(r"""
 (?P<ws>[ \t]+)
|(?P<str>"[^"]*"?)
|(?P<hex>&[Hh][0-9A-Fa-f]+[%&]?)
|(?P<oct>&[Oo]?[0-7]+[%&]?)
|(?P<num>(?:\d+\.?\d*|\.\d+)(?:[EeDd][+-]?\d+)?[%&!#]?)
|(?P<id>[A-Za-z][A-Za-z0-9_.]*[$%&!#]?)
|(?P<op><>|<=|>=|=<|=>|><|[-+*/\\^=<>(),;:#.'?])
""", re.X)
SUFFIXES = "$%&!#"
# keywords that can't be a variable's name; the rest (COLOR, SCREEN, NAME, KEY, LINE ...) can be, where it's clear -
# real QBasic refused them, but people (and small AI models) write "color = 4" all the time
STRUCTURAL = set("""AND OR XOR EQV IMP NOT MOD THEN ELSE ELSEIF TO STEP AS IS UNTIL WHILE WEND LOOP NEXT DO FOR IF END
SELECT CASE SUB FUNCTION GOTO GOSUB RETURN DIM REDIM CONST SHARED STATIC TYPE DECLARE CALL LET PRINT LPRINT INPUT USING
EXIT ON ERROR RESUME OPEN CLOSE DATA READ RESTORE REM DEF DEFINT DEFLNG DEFSNG DEFDBL DEFSTR OPTION BASE INTEGER LONG
SINGLE DOUBLE STRING ANY BYVAL SWAP""".split())
NAMEABLE = KEYWORDS - STRUCTURAL


class Tok:
    __slots__ = ("kind", "value", "col", "raw")

    def __init__(self, kind, value, col, raw=""):
        self.kind, self.value, self.col, self.raw = kind, value, col, raw

    def __repr__(self):
        return f"{self.kind}:{self.value!r}"


def _number(text):
    """A numeric literal's value: an int where QBasic keeps it whole, else a float."""
    t = text.upper()
    if t.startswith("&H"):
        return int(t[2:].rstrip("%&"), 16)
    if t.startswith("&O") or t.startswith("&"):
        return int(t.lstrip("&O").rstrip("%&") or "0", 8)
    suffix = t[-1] if t[-1] in "%&!#" else ""
    body = t.rstrip("%&!#").replace("D", "E")
    if suffix in "%&" and suffix:
        return int(float(body))
    if suffix in "!#" and suffix:
        return float(body)
    if "." in body or "E" in body:
        return float(body)
    v = int(body)
    return v if -2147483648 <= v <= 2147483647 else float(v)


def tokenize(line, number=0):
    """The tokens of one source line (comments and DATA's raw text dealt with here)."""
    out = []
    i, n = 0, len(line)
    while i < n:
        m = TOKEN.match(line, i)
        if not m:
            raise CompileError(f"Syntax error: unexpected '{line[i]}'", number)
        kind = m.lastgroup
        text = m.group()
        start = i
        i = m.end()
        if kind == "ws":
            continue
        if kind == "op" and text == "'":
            break                                          # a comment to the end of the line
        if kind == "op" and text == "?":
            out.append(Tok("kw", "PRINT", start, text))     # ? is PRINT
            continue
        if kind == "str":
            out.append(Tok("str", text[1:-1] if text.endswith('"') and len(text) > 1 else text[1:], start, text))
            continue
        if kind in ("num", "hex", "oct"):
            out.append(Tok("num", _number(text), start, text))
            continue
        if kind == "id":
            up = text.upper()
            if up in ("REM",):
                break
            if up in KEYWORDS:
                out.append(Tok("kw", up, start, text))
                if up == "DATA":                             # the rest of the statement is DATA's, as typed
                    j, q = i, False
                    while j < n and (q or line[j] != ":"):
                        if line[j] == '"':
                            q = not q
                        j += 1
                    out.append(Tok("data", line[i:j], i, line[i:j]))
                    i = j
                continue
            out.append(Tok("id", up, start, text))
            continue
        out.append(Tok("op", {"=<": "<=", "=>": ">=", "><": "<>"}.get(text, text), start, text))
    return out


def split_data(raw):
    """DATA's items: comma-separated, quotes keep commas and spaces."""
    items, cur, q, had_q = [], [], False, False
    for ch in raw:
        if ch == '"':
            if not q and not had_q and not "".join(cur).strip():
                cur = []                                   # (the spaces before a quoted item aren't part of it)
            q = not q
            had_q = True
            continue
        if ch == "," and not q:
            items.append(("".join(cur) if had_q else "".join(cur).strip(), had_q))
            cur, had_q = [], False
            continue
        cur.append(ch)
    items.append(("".join(cur) if had_q else "".join(cur).strip(), had_q))
    return items


# ---- values ----------------------------------------------------------------------------------------------------------
def default_for(suffix):
    return "" if suffix == "$" else 0 if suffix in "%&" else 0.0


def coerce(value, suffix):
    """A value stored into a variable of this type (QBasic rounds to integers, half to even, and checks range)."""
    if suffix == "$":
        if not isinstance(value, str):
            raise BasicError("Type mismatch")
        return value
    if isinstance(value, str):
        raise BasicError("Type mismatch")
    if suffix == "%":
        v = int(round(value)) if isinstance(value, float) else value
        if not -32768 <= v <= 32767:
            raise BasicError("Overflow")
        return v
    if suffix == "&":
        v = int(round(value)) if isinstance(value, float) else value
        if not -2147483648 <= v <= 2147483647:
            raise BasicError("Overflow")
        return v
    return float(value)


def to_int(v):
    if isinstance(v, str):
        raise BasicError("Type mismatch")
    v = int(round(v)) if isinstance(v, float) else v
    if not -2147483648 <= v <= 2147483647:
        raise BasicError("Overflow")
    return v


def num_text(v, double=False):
    """A number as STR$ shows it (without the leading space): .5, -1.5, 1.234568E+08, 7 digits for singles."""
    if isinstance(v, int):
        return str(v)
    if v != v:
        return "NaN"
    if v == int(v) and abs(v) < (1e16 if double else 1e7):
        return str(int(v))
    s = f"{v:.{16 if double else 7}G}"
    if "E" in s:
        mant, exp = s.split("E")
        if "." in mant:
            mant = mant.rstrip("0").rstrip(".")
        e = int(exp)
        s = f"{mant}{'D' if double else 'E'}{'+' if e >= 0 else '-'}{abs(e):02d}"
    elif "." in s:
        s = s.rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


def str_dollar(v):
    s = num_text(v)
    return s if s.startswith("-") else " " + s


def val_of(s):
    """VAL: the number at the start of the text (spaces ignored, &H and &O understood)."""
    t = s.replace(" ", "").replace("\t", "").upper()
    if t.startswith("&H"):
        m = re.match(r"&H([0-9A-F]+)", t)
        return int(m.group(1), 16) if m else 0
    if t.startswith("&O"):
        m = re.match(r"&O([0-7]+)", t)
        return int(m.group(1), 8) if m else 0
    m = re.match(r"[+-]?(\d+\.?\d*|\.\d+)([ED][+-]?\d+)?", t)
    if not m:
        return 0
    text = m.group().replace("D", "E")
    v = float(text)
    return int(v) if v == int(v) and "." not in text and "E" not in text and abs(v) < 2**31 else v


class Array:
    """A DIMmed array: its bounds per dimension, its values (flat), and the sprites GET has stored in it."""
    __slots__ = ("bounds", "data", "suffix", "rtype", "blobs", "strides")

    def __init__(self, bounds, suffix, rtype=None, types=None):
        self.bounds = bounds
        self.suffix = suffix
        self.rtype = rtype
        size = 1
        self.strides = []
        for lo, hi in reversed(bounds):
            if hi < lo:
                raise BasicError("Subscript out of range")
            self.strides.insert(0, size)
            size *= hi - lo + 1
        if size > 16_000_000:
            raise BasicError("Out of memory")
        if rtype is not None:
            self.data = [new_record(rtype, types) for _ in range(size)]
        else:
            self.data = [default_for(suffix)] * size
        self.blobs = {}

    def index(self, subs):
        if len(subs) != len(self.bounds):
            raise BasicError("Subscript out of range")
        off = 0
        for s, (lo, hi), stride in zip(subs, self.bounds, self.strides):
            s = to_int(s)
            if s < lo or s > hi:
                raise BasicError("Subscript out of range")
            off += (s - lo) * stride
        return off


def new_record(tname, types):
    rec = {}
    for fname, (suffix, sub, length) in types[tname].items():
        rec[fname] = new_record(sub, types) if sub else ((" " * length) if length else default_for(suffix))
    return rec


# ---- the program -----------------------------------------------------------------------------------------------------
class Unit:
    """The main program, or a SUB or FUNCTION: its compiled operations and the source line of each."""

    def __init__(self, name, kind="main"):
        self.name, self.kind = name, kind
        self.code, self.lines, self.starts = [], [], []
        self.labels = {}
        self.params = []               # [(key, suffix, is_array, byval, rtype)]
        self.static_all = False
        self.statics = set()
        self.static_values = {}
        self.result = None             # a FUNCTION's return slot
        self.first_line = 0


class Program:
    def __init__(self):
        self.main = Unit("(main)")
        self.subs = {}
        self.functions = {}
        self.types = {}
        self.data = []                 # [(value text, was quoted)]
        self.data_labels = {}          # label -> index into data
        self.errors = []               # [CompileError] (empty: it compiled)
        self.outline = []              # [(kind, name, line)] for the editor's outline
        self.variables = set()         # names seen, for autocomplete


DEFAULT_SUFFIX = {"DEFINT": "%", "DEFLNG": "&", "DEFSNG": "!", "DEFDBL": "#", "DEFSTR": "$"}
TYPE_SUFFIX = {"INTEGER": "%", "LONG": "&", "SINGLE": "!", "DOUBLE": "#", "STRING": "$",
               "BOOLEAN": "%", "_BYTE": "%", "_UNSIGNED": "%"}   # (QB64's names, which AI models often write)


def compile_program(source):
    """Source text -> Program (program.errors lists what didn't compile; the program runs only without them)."""
    return Compiler(source).compile()


class Compiler:
    def __init__(self, source):
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.prog = Program()
        self.deftype = {}                      # letter -> suffix
        self.lines = []                        # [(line number (1-based), tokens)]
        self.unit = None
        self.blocks = []
        self.declared = {}                     # current unit: base name -> suffix or ("type", name)
        self.global_declared = {}              # main's DIMs (for SHARED)
        self.shared_globals = set()            # bases DIM SHARED in main, or CONST there
        self.sub_shared = set()
        self.arrays = {}                       # current unit: base -> suffix (DIMmed arrays)
        self.global_arrays = {}
        self.counter = 0
        self.tokens, self.pos, self.line_no = [], 0, 0

    # ---- the passes ----
    def compile(self):
        for i, text in enumerate(self.source.split("\n"), start=1):
            try:
                toks = tokenize(text, i)
            except CompileError as e:
                self.prog.errors.append(e)
                toks = []
            self.lines.append((i, toks))
        self._prescan()
        units = self._split_units()
        for unit, lines in units:
            self._compile_unit(unit, lines)
        return self.prog

    def _prescan(self):
        """What the whole program needs to know before any of it compiles: the SUBs and FUNCTIONs and their
        parameters, the TYPEs, DEFtypes, and what the main program shares (DIM SHARED, CONST)."""
        in_unit, in_type = False, None
        for no, toks in self.lines:
            if not toks:
                continue
            t0 = toks[0]
            words = [t.value for t in toks if t.kind == "kw"]
            if in_type is not None:
                if t0.kind == "kw" and t0.value == "END" and len(toks) > 1 and toks[1].value == "TYPE":
                    in_type = None
                    continue
                try:
                    self._type_field(in_type, toks, no)
                except CompileError as e:
                    self.prog.errors.append(e)
                continue
            if t0.kind == "kw" and t0.value == "TYPE" and len(toks) > 1 and toks[1].kind == "id":
                in_type = toks[1].value
                self.prog.types[in_type] = {}
                self.prog.outline.append(("TYPE", toks[1].raw, no))
                continue
            if t0.kind == "kw" and t0.value in DEFAULT_SUFFIX:
                self._deftype(toks, no)
                continue
            if t0.kind == "kw" and t0.value in ("SUB", "FUNCTION") and len(toks) > 1 and toks[1].kind == "id":
                in_unit = True
                try:
                    self._declare_unit(t0.value, toks, no)
                except CompileError as e:
                    self.prog.errors.append(e)
                continue
            if t0.kind == "kw" and t0.value == "END" and len(toks) > 1 and toks[1].value in ("SUB", "FUNCTION"):
                in_unit = False
                continue
            if not in_unit and t0.kind == "kw" and t0.value == "DIM" and "SHARED" in words:
                self._prescan_shared(toks)
            if not in_unit and t0.kind == "kw" and t0.value == "CONST":
                for j, t in enumerate(toks):
                    if t.kind == "id" and j + 1 < len(toks) and toks[j + 1].value == "=":
                        self.shared_globals.add(self._base(t.value))
            if t0.kind == "id" and len(toks) > 1 and toks[1].value == ":" and t0.value not in ("",):
                self.prog.outline.append(("label", t0.raw, no))

    def _prescan_shared(self, toks):
        depth = 0
        j = 1
        while j < len(toks):
            t = toks[j]
            if t.kind == "op" and t.value == "(":
                depth += 1
            elif t.kind == "op" and t.value == ")":
                depth -= 1
            elif t.kind == "id" and depth == 0 and toks[j - 1].value in ("SHARED", ","):
                self.shared_globals.add(self._base(t.value))
            j += 1

    def _deftype(self, toks, no):
        suffix = DEFAULT_SUFFIX[toks[0].value]
        j = 1
        while j < len(toks):
            t = toks[j]
            if t.kind == "id":
                a = t.value[0]
                b = a
                if j + 2 < len(toks) and toks[j + 1].value == "-" and toks[j + 2].kind == "id":
                    b = toks[j + 2].value[0]
                    j += 2
                for c in range(ord(a), ord(b) + 1):
                    self.deftype[chr(c)] = suffix
            j += 1

    def _type_field(self, tname, toks, no):
        if toks[0].kind not in ("id", "kw") or len(toks) < 3 or toks[1].value != "AS":
            raise CompileError("Syntax error: expected a field: name AS type", no)
        fname = toks[0].value
        tt = toks[2]
        length = 0
        if tt.value == "STRING":
            suffix, sub = "$", None
            if len(toks) > 4 and toks[3].value == "*":
                length = int(toks[4].value)
        elif tt.value in TYPE_SUFFIX:
            suffix, sub = TYPE_SUFFIX[tt.value], None
        elif tt.kind == "id" and tt.value in self.prog.types:
            suffix, sub = "", tt.value
        else:
            raise CompileError(f"Syntax error: unknown type {tt.raw}", no)
        self.prog.types[tname][fname] = (suffix, sub, length)

    def _declare_unit(self, kind, toks, no):
        name = toks[1].value
        unit = Unit(name, kind.lower())
        unit.first_line = no
        base = self._base(name)
        params = []
        j = 2
        if j < len(toks) and toks[j].value == "(":
            j += 1
            while j < len(toks) and toks[j].value != ")":
                byval = False
                if toks[j].value == "BYVAL":
                    byval = True
                    j += 1
                if toks[j].kind != "id":
                    raise CompileError("Syntax error in parameter list", no)
                pname = toks[j].value
                j += 1
                is_array = False
                if j < len(toks) and toks[j].value == "(":
                    is_array = True
                    j += 1
                    while j < len(toks) and toks[j].value != ")":
                        j += 1
                    j += 1
                suffix, rtype = self._suffix_of(pname), None
                if j < len(toks) and toks[j].value == "AS":
                    tt = toks[j + 1]
                    if tt.value in TYPE_SUFFIX:
                        suffix = TYPE_SUFFIX[tt.value]
                    elif tt.value == "ANY":
                        suffix = self._suffix_of(pname)
                    else:
                        rtype, suffix = tt.value, ""
                    j += 2
                params.append((self._base(pname), suffix, is_array, byval, rtype))
                if j < len(toks) and toks[j].value == ",":
                    j += 1
            j += 1
        if j < len(toks) and toks[j].value == "STATIC":
            unit.static_all = True
        unit.params = params
        if kind == "SUB":
            if base in self.prog.subs:
                raise CompileError("Duplicate definition", no)
            self.prog.subs[base] = unit
        else:
            unit.result = self._suffix_of(name)
            if base in self.prog.functions:
                raise CompileError("Duplicate definition", no)
            self.prog.functions[base] = unit
        self.prog.outline.append((kind, toks[1].raw, no))

    def _split_units(self):
        main, units, cur, kind = [], [], None, None
        in_type = False
        for no, toks in self.lines:
            if toks and toks[0].kind == "kw" and toks[0].value == "TYPE" and len(toks) > 1 and toks[1].kind == "id":
                in_type = True
                continue
            if in_type:
                if toks and toks[0].value == "END" and len(toks) > 1 and toks[1].value == "TYPE":
                    in_type = False
                continue
            if toks and toks[0].kind == "kw" and toks[0].value in ("SUB", "FUNCTION") and len(toks) > 1 \
                    and toks[1].kind == "id":
                base = self._base(toks[1].value)
                cur = (self.prog.subs if toks[0].value == "SUB" else self.prog.functions).get(base)
                kind = toks[0].value
                units.append((cur, []))
                continue
            if toks and toks[0].kind == "kw" and toks[0].value == "END" and len(toks) > 1 \
                    and toks[1].value in ("SUB", "FUNCTION") and cur is not None:
                cur, kind = None, None
                continue
            if cur is not None:
                units[-1][1].append((no, toks))
            elif toks and toks[0].kind == "kw" and toks[0].value == "DECLARE":
                continue
            else:
                main.append((no, toks))
        if cur is not None:
            self.prog.errors.append(CompileError(f"{kind} without END {kind}", cur.first_line))
        return [(self.prog.main, main)] + [(u, ls) for u, ls in units if u is not None]

    # ---- names ----
    def _base(self, name):
        return name[:-1] if name and name[-1] in SUFFIXES else name

    def _suffix_of(self, name):
        if name and name[-1] in SUFFIXES:
            return name[-1]
        return self.deftype.get(name[0], "!")

    def _is_global(self, base):
        if self.unit is self.prog.main:
            return True
        return base in self.shared_globals or base in self.sub_shared

    def var_key(self, name):
        """(scope, key, suffix or record type) for a scalar variable name as written."""
        base = self._base(name)
        glob = self._is_global(base)
        decl = self.declared.get(base) if not glob or self.unit is self.prog.main else None
        if decl is None and glob:
            decl = self.global_declared.get(base)
        if decl is None and not glob:
            decl = self.declared.get(base)
        if name[-1] in SUFFIXES:
            suffix = name[-1]
        elif isinstance(decl, tuple):
            return ("g" if glob else "l"), base, decl
        elif decl is not None:
            suffix = decl
        else:
            suffix = self._suffix_of(name)
        self.prog.variables.add(base)
        return ("g" if glob else "l"), base + suffix, suffix

    def array_key(self, name):
        base = self._base(name)
        glob = self._is_global(base)
        arrays = self.global_arrays if glob else self.arrays
        info = arrays.get(base)
        if name[-1] in SUFFIXES:
            suffix = name[-1]
        elif info is not None:
            suffix = info
        else:
            suffix = self._suffix_of(name)
        if isinstance(suffix, tuple):
            return ("g" if glob else "l"), base + "()", suffix
        return ("g" if glob else "l"), base + suffix + "()", suffix

    def is_array(self, name):
        base = self._base(name)
        if self._is_global(base) and base in self.global_arrays:
            return True
        return base in self.arrays

    # ---- one unit ----
    def _compile_unit(self, unit, lines):
        self.unit = unit
        self.blocks = []
        if unit is self.prog.main:
            self.declared = self.global_declared
            self.arrays = self.global_arrays
        else:
            self.declared = {}
            self.arrays = {}
            self.sub_shared = set()
            for base, suffix, is_array, _byval, rtype in unit.params:
                if is_array:
                    self.arrays[base] = ("type", rtype) if rtype else suffix
                else:
                    self.declared[base] = ("type", rtype) if rtype else suffix
            if unit.kind == "function":
                pass
        for no, toks in lines:
            if not toks:
                continue
            self.line_no = no
            self.tokens, self.pos = toks, 0
            try:
                self._line()
            except CompileError as e:
                if e.line is None:
                    e.line = no
                self.prog.errors.append(e)
            except (IndexError, ValueError) as e:
                self.prog.errors.append(CompileError(f"Syntax error ({e})" if str(e) else "Syntax error", no))
        for b in self.blocks:
            self.prog.errors.append(CompileError(
                {"IF": "Block IF without END IF", "FOR": "FOR without NEXT", "WHILE": "WHILE without WEND",
                 "DO": "DO without LOOP", "SELECT": "SELECT CASE without END SELECT"}.get(b["kind"], "Block not ended"),
                b["line"]))
        # labels: patch the jumps
        for cell, label, line in getattr(unit, "pending", []):
            if label not in unit.labels:
                self.prog.errors.append(CompileError(f"Label not defined: {label}", line))
            else:
                cell[0] = unit.labels[label]
        if hasattr(unit, "end_cell"):
            unit.end_cell[0] = len(unit.code)

    # ---- emitting ----
    def emit(self, fn, start=True):
        u = self.unit
        u.code.append(fn)
        u.lines.append(self.line_no)
        u.starts.append(start)
        return len(u.code) - 1

    def here(self):
        return len(self.unit.code)

    def label_cell(self, label):
        """A one-item list the jump reads its target from, filled once the label's place is known."""
        cell = [None]
        if not hasattr(self.unit, "pending"):
            self.unit.pending = []
        self.unit.pending.append((cell, label, self.line_no))
        return cell

    def end_cell(self):
        if not hasattr(self.unit, "end_cell"):
            self.unit.end_cell = [None]
        return self.unit.end_cell

    # ---- tokens ----
    def peek(self, k=0):
        i = self.pos + k
        return self.tokens[i] if i < len(self.tokens) else None

    def next(self):
        t = self.peek()
        if t is None:
            raise CompileError("Syntax error: the line ends too soon", self.line_no)
        self.pos += 1
        return t

    def at_end(self):
        t = self.peek()
        return t is None or (t.kind == "op" and t.value == ":") or (t.kind == "kw" and t.value == "ELSE")

    def at_kw(self, *words):
        t = self.peek()
        return t is not None and t.kind == "kw" and t.value in words

    def accept_kw(self, word):
        if self.at_kw(word):
            self.pos += 1
            return True
        return False

    def expect_kw(self, word):
        if not self.accept_kw(word):
            t = self.peek()
            raise CompileError(f"Expected: {word}" + (f" (found {t.raw or t.value})" if t else ""), self.line_no)

    def at_op(self, *ops):
        t = self.peek()
        return t is not None and t.kind == "op" and t.value in ops

    def accept_op(self, op):
        if self.at_op(op):
            self.pos += 1
            return True
        return False

    def expect_op(self, op):
        if not self.accept_op(op):
            t = self.peek()
            raise CompileError(f"Expected: {op}" + (f" (found {t.raw or t.value})" if t else ""), self.line_no)

    def expect_id(self):
        t = self.next()
        if t.kind == "kw" and t.value in NAMEABLE:
            return t.value                                      # (a keyword used as a name: see NAMEABLE)
        if t.kind != "id":
            raise CompileError(f"Expected: a name (found {t.raw or t.value})", self.line_no)
        return t.value

    # ---- a line ----
    def _line(self):
        t = self.peek()
        if t.kind == "num" and isinstance(t.value, int):                 # a line number
            self.pos += 1
            self._define_label(str(t.value))
        elif t.kind == "id" and self.peek(1) is not None and self.peek(1).kind == "op" and self.peek(1).value == ":" \
                and t.value not in self.prog.subs:
            self.pos += 2
            self._define_label(t.value)
        while self.peek() is not None:
            if self.accept_op(":"):
                continue
            self.statement()
            if self.peek() is not None and not self.accept_op(":"):
                t = self.peek()
                raise CompileError(f"Expected: end of statement (found {t.raw or t.value})", self.line_no)

    def _define_label(self, name):
        if name in self.unit.labels:
            raise CompileError(f"Duplicate label {name}", self.line_no)
        self.unit.labels[name] = self.here()
        if self.unit is self.prog.main:
            self.prog.data_labels.setdefault(name, len(self.prog.data))
            self._data_label_pending = getattr(self, "_data_label_pending", []) + [name]

    def statement(self):
        t = self.peek()
        if t.kind == "kw" and t.value in NAMEABLE:
            nxt = self.peek(1)
            if nxt is not None and nxt.kind == "op" and (nxt.value in ("=", ".") or
                                                         (nxt.value == "(" and self._looks_assign())):
                self.tokens[self.pos] = t = Tok("id", t.value, t.col, t.raw)   # color = 4: a variable
        if t.kind == "kw":
            handler = getattr(self, "st_" + t.value, None)
            if handler is None:
                raise CompileError(f"{t.value} is not supported", self.line_no)
            self.pos += 1
            handler()
            return
        if t.kind == "id":
            name = t.value
            nxt = self.peek(1)
            if name in ("MID$",) and nxt is not None and nxt.value == "(":
                self.pos += 1
                return self.st_MID_assign()
            if name == "TIMER" and nxt is not None and nxt.kind == "kw" and nxt.value in ("ON", "OFF", "STOP"):
                self.pos += 2
                return
            base = self._base(name)
            if base in self.prog.subs and (nxt is None or not (nxt.kind == "op" and nxt.value in ("=", "."))
                                           and not (nxt.kind == "op" and nxt.value == "(" and self._looks_assign())):
                self.pos += 1
                return self._call_sub(base, parens=False)
            return self.st_LET()
        raise CompileError(f"Syntax error at {t.raw or t.value}", self.line_no)

    def _looks_assign(self):
        """name(...) = ...: an array element being set, not a SUB call with brackets."""
        depth = 0
        for k in range(self.pos + 1, len(self.tokens)):
            v = self.tokens[k]
            if v.kind == "op" and v.value == "(":
                depth += 1
            elif v.kind == "op" and v.value == ")":
                depth -= 1
                if depth == 0:
                    nxt = self.tokens[k + 1] if k + 1 < len(self.tokens) else None
                    return nxt is not None and nxt.kind == "op" and nxt.value in ("=", ".")
        return False

    # ---- expressions -----------------------------------------------------------------------------------------------
    # each returns (fn(vm) -> value, kind) with kind "n" (number), "s" (string) or "?"
    def expr(self):
        return self._imp()

    def _logic(self, sub, word, op):
        a, ka = sub()
        while self.at_kw(word):
            self.pos += 1
            b, kb = sub()
            self._need_num(ka, kb)
            a = (lambda f, g: lambda vm: op(to_int(f(vm)), to_int(g(vm))))(a, b)
            ka = "n"
        return a, ka

    def _imp(self):
        return self._logic(self._eqv, "IMP", lambda x, y: (~x) | y)

    def _eqv(self):
        return self._logic(self._xor, "EQV", lambda x, y: ~(x ^ y))

    def _xor(self):
        return self._logic(self._or, "XOR", lambda x, y: x ^ y)

    def _or(self):
        return self._logic(self._and, "OR", lambda x, y: x | y)

    def _and(self):
        return self._logic(self._not, "AND", lambda x, y: x & y)

    def _not(self):
        if self.accept_kw("NOT"):
            a, k = self._not()
            self._need_num(k)
            return (lambda vm: ~to_int(a(vm))), "n"
        return self._rel()

    def _rel(self):
        a, ka = self._add()
        while self.at_op("=", "<>", "<", ">", "<=", ">="):
            op = self.next().value
            b, kb = self._add()
            if "s" in (ka, kb) and "n" in (ka, kb):
                raise CompileError("Type mismatch", self.line_no)
            f = {"=": lambda x, y: -1 if x == y else 0, "<>": lambda x, y: -1 if x != y else 0,
                 "<": lambda x, y: -1 if x < y else 0, ">": lambda x, y: -1 if x > y else 0,
                 "<=": lambda x, y: -1 if x <= y else 0, ">=": lambda x, y: -1 if x >= y else 0}[op]
            a = (lambda f, g, h: lambda vm: h(f(vm), g(vm)))(a, b, f)
            ka = "n"
        return a, ka

    def _add(self):
        a, ka = self._mod()
        while self.at_op("+", "-"):
            op = self.next().value
            b, kb = self._mod()
            if op == "+":
                if ka == "s" and kb == "s":
                    a = (lambda f, g: lambda vm: f(vm) + g(vm))(a, b)
                    continue
                if "s" in (ka, kb) and "n" in (ka, kb):
                    raise CompileError("Type mismatch", self.line_no)
                if ka in ("n", "d") and kb in ("n", "d"):
                    a = (lambda f, g: lambda vm: f(vm) + g(vm))(a, b)
                else:
                    a = (lambda f, g: lambda vm: _plus(f(vm), g(vm)))(a, b)
                    ka = "?" if "?" in (ka, kb) else _nk(ka, kb)
                    continue
            else:
                self._need_num(ka, kb)
                a = (lambda f, g: lambda vm: _minus(f(vm), g(vm)))(a, b)
            ka = _nk(ka, kb)
        return a, ka

    def _mod(self):
        a, ka = self._idiv()
        while self.accept_kw("MOD"):
            b, kb = self._idiv()
            self._need_num(ka, kb)
            a = (lambda f, g: lambda vm: _mod(f(vm), g(vm)))(a, b)
            ka = "n"
        return a, ka

    def _idiv(self):
        a, ka = self._mul()
        while self.accept_op("\\"):
            b, kb = self._mul()
            self._need_num(ka, kb)
            a = (lambda f, g: lambda vm: _idiv(f(vm), g(vm)))(a, b)
            ka = "n"
        return a, ka

    def _mul(self):
        a, ka = self._neg()
        while self.at_op("*", "/"):
            op = self.next().value
            b, kb = self._neg()
            self._need_num(ka, kb)
            if op == "*":
                a = (lambda f, g: lambda vm: _times(f(vm), g(vm)))(a, b)
            else:
                a = (lambda f, g: lambda vm: _divide(f(vm), g(vm)))(a, b)
            ka = _nk(ka, kb)
        return a, ka

    def _neg(self):
        if self.accept_op("-"):
            a, k = self._neg()
            self._need_num(k)
            return (lambda vm: _negate(a(vm))), ("d" if k == "d" else "n")
        if self.accept_op("+"):
            return self._neg()
        return self._pow()

    def _pow(self):
        a, ka = self._atom()
        while self.accept_op("^"):
            if self.accept_op("-"):
                b0, kb = self._atom()
                b = (lambda f: lambda vm: -f(vm))(b0)
            else:
                b, kb = self._atom()
            self._need_num(ka, kb)
            a = (lambda f, g: lambda vm: _power(f(vm), g(vm)))(a, b)
            ka = _nk(ka, kb)
        return a, ka

    def _need_num(self, *kinds):
        if "s" in kinds:
            raise CompileError("Type mismatch", self.line_no)

    def _atom(self):
        t = self.next()
        if t.kind == "num":
            v = t.value
            double = t.raw.endswith("#") or (isinstance(v, float) and len(re.sub(r"[^0-9]", "",
                                                                                    t.raw.split("E")[0])) > 7)
            return (lambda vm: v), ("d" if double else "n")
        if t.kind == "str":
            v = t.value
            return (lambda vm: v), "s"
        if t.kind == "op" and t.value == "(":
            e = self.expr()
            self.expect_op(")")
            return e
        if t.kind == "id":
            return self._name_expr(t.value)
        if t.kind == "kw" and t.value in NAMEABLE:
            return self._name_expr(t.value)                    # (a keyword used as a variable's name)
        raise CompileError(f"Expected: an expression (found {t.raw or t.value})", self.line_no)

    def _args(self):
        """( expr, expr ... ) - the brackets already open."""
        args = []
        if self.accept_op(")"):
            return args
        while True:
            args.append(self.expr())
            if self.accept_op(")"):
                return args
            self.expect_op(",")

    def _name_expr(self, name):
        base = self._base(name)
        # a user FUNCTION
        if base in self.prog.functions and (name[-1] not in SUFFIXES or
                                            self.prog.functions[base].result == name[-1]):
            unit = self.prog.functions[base]
            if self.at_op("("):
                self.pos += 1
                return self._call_function(unit)
            if self.unit is unit:                        # inside itself, with no arguments: its value so far
                key = "\x00result"
                return (lambda vm: vm.frame.vars.get(key, default_for(unit.result))), \
                    ("s" if unit.result == "$" else "d" if unit.result == "#" else "n")
            return self._call_function(unit, have_args=False)
        # a built-in function
        spec = BUILTINS.get(name)
        if spec is not None and not self.is_array(name):
            return self._builtin(name, spec)
        if self.at_op("("):                               # an array element (DIMmed or not)
            self.pos += 1
            get, _set, kind = self._element(name)
            return get, kind
        if "." in name:
            got = self._field_ref(name)
            if got is not None:
                return got[0], got[2]
        scope, key, suffix = self.var_key(name)
        if isinstance(suffix, tuple):
            if scope == "g":
                return (lambda vm: vm.g.vars[key]), "r"
            return (lambda vm: vm.frame.vars[key]), "r"
        d = default_for(suffix)
        kind = "s" if suffix == "$" else "d" if suffix == "#" else "n"
        if scope == "g":
            return (lambda vm: vm.g.vars.get(key, d)), kind
        return (lambda vm: vm.frame.vars.get(key, d)), kind

    def _field_ref(self, name):
        """p.x.y on a record variable: (get, set, kind), or None when p isn't a record (then p.x is just a name)."""
        parts = name.split(".")
        base = parts[0]
        scope, key, decl = self.var_key(base)
        if not isinstance(decl, tuple):
            return None
        rtype = decl[1]
        return self._field_chain(lambda vm: (vm.g if scope == "g" else vm.frame).vars[key], rtype, parts[1:])

    def _field_chain(self, rec_get, rtype, fields):
        types = self.prog.types
        suffix = ""
        for i, f in enumerate(fields):
            if rtype not in types or f not in types[rtype]:
                raise CompileError(f"Element not defined: {f}", self.line_no)
            suffix, sub, length = types[rtype][f]
            if i < len(fields) - 1:
                rec_get = (lambda g, f: lambda vm: g(vm)[f])(rec_get, f)
                rtype = sub
        last = fields[-1]
        kind = "r" if sub else ("s" if suffix == "$" else "n")

        def get(vm):
            return rec_get(vm)[last]

        def put(vm, v):
            r = rec_get(vm)
            if sub:
                r[last] = v
            elif length:
                v = coerce(v, "$")
                r[last] = (v + " " * length)[:length]
            else:
                r[last] = coerce(v, suffix)
        return get, put, kind

    def _element(self, name):
        """name( subscripts ) [.field ...]: (get, set, kind), the bracket already open."""
        scope, key, suffix = self.array_key(name)
        subs = [e for e, _k in self._args()]
        n = len(subs)
        if not self.is_array(name):
            base = self._base(name)
            arrays = self.global_arrays if scope == "g" else self.arrays
            arrays[base] = suffix                          # (used without DIM: 0 to 10 on first use)
        types = self.prog.types
        rtype = suffix[1] if isinstance(suffix, tuple) else None
        sfx = None if rtype else suffix

        def arr(vm):
            frame = vm.g if scope == "g" else vm.frame
            a = frame.arrays.get(key)
            if a is None:
                a = frame.arrays[key] = Array([(vm.option_base, 10)] * n, sfx, rtype, types)
            return a
        if n == 1:
            s0 = subs[0]

            def index(vm):
                a = arr(vm)
                return a, a.index((s0(vm),))
        elif n == 2:
            s0, s1 = subs

            def index(vm):
                a = arr(vm)
                return a, a.index((s0(vm), s1(vm)))
        else:
            def index(vm):
                a = arr(vm)
                return a, a.index([s(vm) for s in subs])

        def get(vm):
            a, i = index(vm)
            return a.data[i]

        def put(vm, v):
            a, i = index(vm)
            a.data[i] = v if rtype else coerce(v, sfx)
        if self.accept_op("."):
            fields = [self.expect_id()]
            fields = ".".join(fields).split(".")
            return self._field_chain(get, rtype, fields)
        return get, put, ("r" if rtype else "s" if sfx == "$" else "n")

    def _builtin(self, name, spec):
        fn, lo, hi, kind = spec
        args = []
        if name in ("LBOUND", "UBOUND"):
            self.expect_op("(")
            aname = self.expect_id()
            if self.accept_op("("):
                self.expect_op(")")
            scope, key, _s = self.array_key(aname)
            dim = (lambda vm: 1)
            if self.accept_op(","):
                dim = self.expr()[0]
            self.expect_op(")")
            which = 0 if name == "LBOUND" else 1

            def bound(vm):
                a = (vm.g if scope == "g" else vm.frame).arrays.get(key)
                if a is None:
                    raise BasicError("Subscript out of range")
                d = to_int(dim(vm))
                if not 1 <= d <= len(a.bounds):
                    raise BasicError("Subscript out of range")
                return a.bounds[d - 1][which]
            return bound, "n"
        if self.accept_op("("):
            args = self._args()
        elif lo > 0:
            raise CompileError(f"Expected: ( after {name}", self.line_no)
        if not lo <= len(args) <= hi:
            raise CompileError(f"Wrong number of arguments for {name}", self.line_no)
        if kind == "n" and name in DOUBLE_FOLLOWS and any(k == "d" for _a, k in args):
            kind = "d"
        if name == "STR$" and args and args[0][1] == "d":
            fn = (lambda vm, x: (lambda t: t if t.startswith("-") else " " + t)(num_text(_need_num(x), True)))
        fs = [a for a, _k in args]
        if not fs:
            return (lambda vm: fn(vm)), kind
        if len(fs) == 1:
            f0 = fs[0]
            return (lambda vm: fn(vm, f0(vm))), kind
        if len(fs) == 2:
            f0, f1 = fs
            return (lambda vm: fn(vm, f0(vm), f1(vm))), kind
        return (lambda vm: fn(vm, *[f(vm) for f in fs])), kind

    # ---- calls ----
    def _call_args(self, unit, closing=True):
        """The arguments of a SUB or FUNCTION call: [(value fn, setter or None, array getter or None)]."""
        out = []
        if closing and self.accept_op(")"):
            return out
        while True:
            out.append(self._one_arg())
            if closing:
                if self.accept_op(")"):
                    break
                self.expect_op(",")
            else:
                if not self.accept_op(","):
                    break
        if len(out) != len(unit.params):
            raise CompileError(f"Argument-count mismatch: {unit.name} takes {len(unit.params)}", self.line_no)
        return out

    def _one_arg(self):
        """An argument: a whole array (name()), a variable or element (passed by reference), or a value."""
        t = self.peek()
        if t.kind == "id" and self.peek(1) is not None and self.peek(1).value == "(" and self.peek(2) is not None \
                and self.peek(2).value == ")":
            self.pos += 3
            scope, key, _s = self.array_key(t.value)
            return (None, None, lambda vm: (vm.g if scope == "g" else vm.frame).arrays.get(key))
        start = self.pos
        if t.kind == "id" and self._base(t.value) not in self.prog.functions and t.value not in BUILTINS:
            nxt = self.peek(1)
            plain = _arg_ends(nxt)
            if plain:
                self.pos += 1
                if "." in t.value and self._field_ref(t.value) is not None:
                    get, put, _k = self._field_ref(t.value)
                    return (get, put, None)
                scope, key, suffix = self.var_key(t.value)
                if isinstance(suffix, tuple):
                    return ((lambda vm: (vm.g if scope == "g" else vm.frame).vars[key]), None, None)
                d = default_for(suffix)

                def get(vm, s=scope, k=key):
                    return (vm.g if s == "g" else vm.frame).vars.get(k, d)

                def put(vm, v, s=scope, k=key, sf=suffix):
                    (vm.g if s == "g" else vm.frame).vars[k] = coerce(v, sf)
                return (get, put, None)
            if nxt is not None and nxt.value == "(":
                save = self.pos
                self.pos += 2
                try:
                    get, put, _k = self._element(t.value)
                    if _arg_ends(self.peek()):
                        return (get, put, None)
                except CompileError:
                    pass
                self.pos = save
        self.pos = start
        return (self.expr()[0], None, None)

    def _call_function(self, unit, have_args=True):
        args = self._call_args(unit) if have_args else []
        if not have_args and unit.params:
            raise CompileError(f"Argument-count mismatch: {unit.name} takes {len(unit.params)}", self.line_no)
        kind = "s" if unit.result == "$" else "d" if unit.result == "#" else "n"
        return (lambda vm: vm.call(unit, args)), kind

    def _call_sub(self, base, parens):
        unit = self.prog.subs.get(base)
        if unit is None:
            raise CompileError(f"Subprogram not defined: {base}", self.line_no)
        if parens:
            args = self._call_args(unit) if self.accept_op("(") else self._call_args(unit, closing=False) \
                if not self.at_end() else []
        else:
            args = self._call_args(unit, closing=False) if not self.at_end() else []
        if not args and unit.params:
            raise CompileError(f"Argument-count mismatch: {unit.name} takes {len(unit.params)}", self.line_no)
        def op(vm):
            vm.call(unit, args)
        self.emit(op)

    # ---- assignment ----
    def target(self):
        """Something that can be assigned to: (set fn(vm, value), kind, get fn)."""
        name = self.expect_id()
        base = self._base(name)
        if self.unit.kind == "function" and base == self._base(self.unit.name) and not self.at_op("("):
            key, suffix = "\x00result", self.unit.result
            return (lambda vm, v: vm.frame.vars.__setitem__(key, coerce(v, suffix))), \
                ("s" if suffix == "$" else "n"), (lambda vm: vm.frame.vars.get(key, default_for(suffix)))
        if self.accept_op("("):
            get, put, kind = self._element(name)
            return put, kind, get
        if "." in name:
            got = self._field_ref(name)
            if got is not None:
                get, put, kind = got
                return put, kind, get
        scope, key, suffix = self.var_key(name)
        if isinstance(suffix, tuple):
            def put(vm, v):
                (vm.g if scope == "g" else vm.frame).vars[key] = _copy_record(v)
            return put, "r", (lambda vm: (vm.g if scope == "g" else vm.frame).vars[key])
        d = default_for(suffix)
        kind = "s" if suffix == "$" else "n"
        if scope == "g":
            if suffix == "!" or suffix == "#":
                def put(vm, v):
                    if isinstance(v, str):
                        raise BasicError("Type mismatch")
                    vm.g.vars[key] = float(v)
            else:
                def put(vm, v):
                    vm.g.vars[key] = coerce(v, suffix)
            return put, kind, (lambda vm: vm.g.vars.get(key, d))
        if suffix == "!" or suffix == "#":
            def put(vm, v):
                if isinstance(v, str):
                    raise BasicError("Type mismatch")
                vm.frame.vars[key] = float(v)
        else:
            def put(vm, v):
                vm.frame.vars[key] = coerce(v, suffix)
        return put, kind, (lambda vm: vm.frame.vars.get(key, d))

    def st_LET(self):
        put, kind, _get = self.target()
        self.expect_op("=")
        e, k = self.expr()
        if (kind == "s" and k == "n") or (kind == "n" and k == "s"):
            raise CompileError("Type mismatch", self.line_no)
        self.emit(lambda vm: put(vm, e(vm)))

    def st_MID_assign(self):
        self.expect_op("(")
        put, kind, get = self.target()
        self.expect_op(",")
        start = self.expr()[0]
        length = None
        if self.accept_op(","):
            length = self.expr()[0]
        self.expect_op(")")
        self.expect_op("=")
        e = self.expr()[0]

        def op(vm):
            s = get(vm)
            st = to_int(start(vm))
            if st < 1 or st > len(s):
                raise BasicError("Illegal function call")
            new = e(vm)
            n = len(new) if length is None else min(to_int(length(vm)), len(new))
            n = min(n, len(s) - st + 1)
            put(vm, s[:st - 1] + new[:n] + s[st - 1 + n:])
        self.emit(op)

    # ---- statements ----------------------------------------------------------------------------------------------
    def st_REM(self):
        self.pos = len(self.tokens)

    def st_PRINT(self):
        if self.accept_op("#"):
            fnum = self.expr()[0]
            self.expect_op(",")
            return self._print(fnum)
        self._print(None)

    def st_LPRINT(self):
        self._print(None)

    def _print(self, fnum):
        items = []                 # ("e", fn) | ("tab", fn) | ("spc", fn) | (";",) | (",",)
        using = None
        if self.accept_kw("USING"):
            using = self.expr()[0]
            self.expect_op(";")
        while not self.at_end():
            t = self.peek()
            if t.kind == "op" and t.value == ";":
                self.pos += 1
                items.append((";",))
                continue
            if t.kind == "op" and t.value == ",":
                self.pos += 1
                items.append((",",))
                continue
            if t.kind == "id" and t.value in ("TAB", "SPC") and self.peek(1) is not None and self.peek(1).value == "(":
                self.pos += 2
                f = self.expr()[0]
                self.expect_op(")")
                items.append((t.value.lower(), f))
                continue
            items.append(("e",) + self.expr())
        newline = not items or items[-1][0] not in (";", ",")
        if using is not None:
            vals = [it[1] for it in items if it[0] == "e"]
            self.emit(lambda vm: vm.print_using(fnum, using(vm), [v(vm) for v in vals], newline))
            return
        self.emit(lambda vm: vm.print_items(fnum, items, newline))

    def st_WRITE(self):
        fnum = None
        if self.accept_op("#"):
            fnum = self.expr()[0]
            self.expect_op(",")
        vals = []
        while not self.at_end():
            vals.append(self.expr()[0])
            if not self.accept_op(","):
                break
        self.emit(lambda vm: vm.write_items(fnum, [v(vm) for v in vals]))

    def st_CLS(self):
        arg = None if self.at_end() else self.expr()[0]
        self.emit(lambda vm: vm.scr.cls(to_int(arg(vm)) if arg else None))

    def st_LOCATE(self):
        args = self._optional_args(5)
        row, col, cur = (args + [None] * 3)[:3]

        def op(vm):
            vm.scr.locate(to_int(row(vm)) if row else None, to_int(col(vm)) if col else None)
            if cur is not None:
                vm.scr.cursor_on = bool(to_int(cur(vm)))
        self.emit(op)

    def _optional_args(self, most):
        """a, , c - expressions or None for the ones left out."""
        out = []
        while not self.at_end():
            if self.at_op(","):
                out.append(None)
                self.pos += 1
                if self.at_end():
                    out.append(None)
                continue
            out.append(self.expr()[0])
            if not self.accept_op(","):
                break
            if self.at_end():
                out.append(None)
        return out[:most]

    def st_COLOR(self):
        args = self._optional_args(3)
        fg, bg = (args + [None, None])[:2]
        self.emit(lambda vm: vm.scr.color(to_int(fg(vm)) if fg else None, to_int(bg(vm)) if bg else None))

    def st_SCREEN(self):
        args = self._optional_args(4)
        mode, _cs, apage, vpage = (args + [None] * 4)[:4]

        def op(vm):
            m = to_int(mode(vm)) if mode else None
            if m is not None and m != vm.scr.mode:
                vm.scr.set_mode(m)
            vm.scr.set_pages(to_int(apage(vm)) if apage else None, to_int(vpage(vm)) if vpage else None)
        self.emit(op)

    def st_WIDTH(self):
        args = self._optional_args(2)
        cols, rows = (args + [None, None])[:2]
        self.emit(lambda vm: vm.scr.width(to_int(cols(vm)) if cols else None, to_int(rows(vm)) if rows else None))

    def st_VIEW(self):
        if self.accept_kw("PRINT"):
            if self.at_end():
                self.emit(lambda vm: vm.scr.view_print(None, None))
                return
            top = self.expr()[0]
            self.expect_kw("TO")
            bottom = self.expr()[0]
            self.emit(lambda vm: vm.scr.view_print(to_int(top(vm)), to_int(bottom(vm))))
            return
        self.accept_kw("SCREEN")
        if self.at_end():
            self.emit(lambda vm: vm.scr.view(None))
            return
        a = self._coord()
        self.expect_op("-")
        b = self._coord()
        rest = self._optional_args(2) if self.accept_op(",") else []
        fill, border = (rest + [None, None])[:2]
        self.emit(lambda vm: vm.scr.view((a[1](vm), a[2](vm), b[1](vm), b[2](vm)),
                                         to_int(fill(vm)) if fill else None, to_int(border(vm)) if border else None))

    def st_WINDOW(self):
        screen = self.accept_kw("SCREEN")
        if self.at_end():
            self.emit(lambda vm: vm.scr.window(None))
            return
        a = self._coord()
        self.expect_op("-")
        b = self._coord()
        self.emit(lambda vm: vm.scr.window((a[1](vm), a[2](vm), b[1](vm), b[2](vm)), screen))

    def _coord(self):
        """[STEP] (x, y) -> (relative?, x fn, y fn)."""
        rel = self.accept_kw("STEP")
        self.expect_op("(")
        x = self.expr()[0]
        self.expect_op(",")
        y = self.expr()[0]
        self.expect_op(")")
        return rel, x, y

    def st_PSET(self, reset=False):
        rel, x, y = self._coord()
        c = None
        if self.accept_op(","):
            c = self.expr()[0]
        self.emit(lambda vm: vm.scr.pset(x(vm), y(vm), to_int(c(vm)) if c else None, rel, reset))

    def st_PRESET(self):
        self.st_PSET(reset=True)

    def st_LINE(self):
        if self.accept_kw("INPUT"):
            return self.st_LINE_INPUT()
        a = None
        if not self.at_op("-"):
            a = self._coord()
        self.expect_op("-")
        b = self._coord()
        c, box, style = None, None, None
        if self.accept_op(","):
            if not self.at_op(",") and not self.at_end():
                c = self.expr()[0]
            if self.accept_op(","):
                t = self.peek()
                if t is not None and t.kind == "id" and t.value in ("B", "BF"):
                    box = t.value
                    self.pos += 1
                if self.accept_op(","):
                    style = self.expr()[0]

        def op(vm):
            vm.scr.line(a[1](vm) if a else None, a[2](vm) if a else None, a[0] if a else False,
                        b[1](vm), b[2](vm), b[0], to_int(c(vm)) if c else None, box,
                        to_int(style(vm)) if style else None)
        self.emit(op)

    def st_CIRCLE(self):
        rel, x, y = self._coord()
        self.expect_op(",")
        args = self._optional_args(5)
        r, c, start, end, aspect = (args + [None] * 5)[:5]
        if r is None:
            raise CompileError("Expected: the radius", self.line_no)
        self.emit(lambda vm: vm.scr.circle(x(vm), y(vm), r(vm), to_int(c(vm)) if c else None,
                                           start(vm) if start else None, end(vm) if end else None,
                                           aspect(vm) if aspect else None, rel))

    def st_PAINT(self):
        rel, x, y = self._coord()
        paint = border = None
        if self.accept_op(","):
            args = self._optional_args(3)
            paint, border = (args + [None, None])[:2]
        self.emit(lambda vm: vm.scr.paint(x(vm), y(vm), _paint_color(paint(vm)) if paint else None,
                                          to_int(border(vm)) if border else None, rel))

    def st_DRAW(self):
        s = self.expr()[0]
        self.emit(lambda vm: vm.scr.draw(s(vm), vm))

    def st_PALETTE(self):
        if self.accept_kw("USING"):
            self.expr()
            return
        if self.at_end():
            self.emit(lambda vm: vm.scr.palette_reset())
            return
        attr = self.expr()[0]
        self.expect_op(",")
        col = self.expr()[0]
        self.emit(lambda vm: vm.scr.palette(to_int(attr(vm)), to_int(col(vm))))

    def st_PCOPY(self):
        a = self.expr()[0]
        self.expect_op(",")
        b = self.expr()[0]
        self.emit(lambda vm: vm.scr.pcopy(to_int(a(vm)), to_int(b(vm))))

    def st_GET(self):
        if self.accept_op("#"):
            raise CompileError("GET # (random-access files) is not supported", self.line_no)
        a = self._coord()
        self.expect_op("-")
        b = self._coord()
        self.expect_op(",")
        name = self.expect_id()
        scope, key, suffix = self.array_key(name)
        start = None
        if self.accept_op("("):
            start = self.expr()[0]
            self.expect_op(")")
        base = self._base(name)
        (self.global_arrays if scope == "g" else self.arrays).setdefault(base, suffix)

        def op(vm):
            arr = (vm.g if scope == "g" else vm.frame).arrays.get(key)
            if arr is None:
                raise BasicError("Illegal function call")
            idx = to_int(start(vm)) if start else arr.bounds[0][0]
            arr.blobs[idx] = vm.scr.get_block(a[1](vm), a[2](vm), b[1](vm), b[2](vm))
        self.emit(op)

    def st_PUT(self):
        if self.accept_op("#"):
            raise CompileError("PUT # (random-access files) is not supported", self.line_no)
        a = self._coord()
        self.expect_op(",")
        name = self.expect_id()
        scope, key, _s = self.array_key(name)
        start = None
        if self.accept_op("("):
            start = self.expr()[0]
            self.expect_op(")")
        action = "XOR"
        if self.accept_op(","):
            t = self.next()
            action = t.value
            if action not in ("PSET", "PRESET", "AND", "OR", "XOR"):
                raise CompileError("Expected: PSET, PRESET, AND, OR or XOR", self.line_no)

        def op(vm):
            arr = (vm.g if scope == "g" else vm.frame).arrays.get(key)
            if arr is None:
                raise BasicError("Illegal function call")
            idx = to_int(start(vm)) if start else arr.bounds[0][0]
            blob = arr.blobs.get(idx)
            if blob is None:
                raise BasicError("Illegal function call")
            vm.scr.put_block(a[1](vm), a[2](vm), blob, action)
        self.emit(op)

    def st_BEEP(self):
        self.emit(lambda vm: vm.sound.beep())

    def st_SOUND(self):
        f = self.expr()[0]
        self.expect_op(",")
        d = self.expr()[0]
        self.emit(lambda vm: vm.sound.sound(f(vm), d(vm), vm))

    def st_PLAY(self):
        if self.at_kw("ON", "OFF", "STOP"):
            self.pos += 1
            return
        s = self.expr()[0]
        self.emit(lambda vm: vm.sound.play(s(vm), vm))

    def st_SLEEP(self):
        s = None if self.at_end() else self.expr()[0]
        self.emit(lambda vm: vm.sleep(s(vm) if s else None))

    def st_WAIT(self):
        self._optional_args(3)
        self.emit(lambda vm: vm.wait_retrace())

    def st_RANDOMIZE(self):
        s = None if self.at_end() else self.expr()[0]
        self.emit(lambda vm: random.seed(s(vm) if s else time.time()))

    def st_INPUT(self):
        if self.accept_op("#"):
            fnum = self.expr()[0]
            self.expect_op(",")
            targets = self._targets()
            self.emit(lambda vm: vm.input_file(fnum(vm), targets))
            return
        same_line = self.accept_op(";")
        prompt, mark = None, True
        if self.peek() is not None and self.peek().kind == "str":
            prompt = self.next().value
            if self.accept_op(","):
                mark = False
            else:
                self.expect_op(";")
        targets = self._targets()
        self.emit(lambda vm: vm.input_vars(prompt, mark, targets, same_line))

    def _targets(self):
        out = []
        while True:
            put, kind, _g = self.target()
            out.append((put, kind))
            if not self.accept_op(","):
                return out

    def st_LINE_INPUT(self):
        if self.accept_op("#"):
            fnum = self.expr()[0]
            self.expect_op(",")
            put, kind, _g = self.target()
            self.emit(lambda vm: put(vm, vm.line_input_file(fnum(vm))))
            return
        same_line = self.accept_op(";")
        prompt = ""
        if self.peek() is not None and self.peek().kind == "str":
            prompt = self.next().value
            if not self.accept_op(";"):
                self.expect_op(",")
        put, kind, _g = self.target()
        self.emit(lambda vm: put(vm, vm.line_input(prompt, same_line)))

    # ---- declarations ----
    def st_DIM(self, redim=False):
        shared = self.accept_kw("SHARED")
        preserve = False
        if redim and self.peek() is not None and self.peek().kind == "id" and self.peek().value == "PRESERVE":
            self.pos += 1
            preserve = True
        while True:
            name = self.expect_id()
            base = self._base(name)
            bounds = None
            if self.accept_op("("):
                bounds = []
                if not self.accept_op(")"):
                    while True:
                        lo = self.expr()[0]
                        hi = None
                        if self.accept_kw("TO"):
                            hi = self.expr()[0]
                        bounds.append((lo, hi))
                        if self.accept_op(")"):
                            break
                        self.expect_op(",")
            suffix = name[-1] if name[-1] in SUFFIXES else None
            rtype, length = None, 0
            if self.accept_kw("AS"):
                t = self.next()
                if t.value == "STRING":
                    suffix = "$"
                    if self.accept_op("*"):
                        length = self.expr()[0]
                elif t.value in TYPE_SUFFIX:
                    suffix = TYPE_SUFFIX[t.value]
                elif t.kind == "id" and t.value in self.prog.types:
                    rtype = t.value
                else:
                    raise CompileError(f"Unknown type {t.raw or t.value}", self.line_no)
            if suffix is None and rtype is None:
                suffix = self._suffix_of(name)
            if shared and self.unit is self.prog.main:
                self.shared_globals.add(base)
            decl = ("type", rtype) if rtype else suffix
            if bounds is None:
                self.declared[base] = decl
                scope, key, _s = self.var_key(base if not rtype else base)
                if rtype:
                    types = self.prog.types
                    self.emit(lambda vm, s=scope, k=key, r=rtype: (vm.g if s == "g" else vm.frame).vars.
                              __setitem__(k, new_record(r, types)))
                elif length:
                    self.emit(lambda vm, s=scope, k=base + "$", ln=length: (vm.g if s == "g" else vm.frame).vars.
                              __setitem__(k, " " * to_int(ln(vm))))
                else:
                    k0 = base + suffix
                    d = default_for(suffix)
                    def op(vm, s=scope, k=k0, d=d):
                        (vm.g if s == "g" else vm.frame).vars.setdefault(k, d)
                    self.emit(op)
            else:
                arrays = self.global_arrays if self._is_global(base) else self.arrays
                arrays[base] = decl
                scope, key, _s = self.array_key(base + (suffix if suffix and name[-1] in SUFFIXES else ""))
                if name[-1] not in SUFFIXES:
                    scope, key, _s = self.array_key(base)
                types = self.prog.types

                def op(vm, s=scope, k=key, b=bounds, sf=suffix, r=rtype, pres=preserve, re_=redim):
                    frame = vm.g if s == "g" else vm.frame
                    dims = []
                    for lo, hi in b:
                        if hi is None:
                            dims.append((vm.option_base, to_int(lo(vm))))
                        else:
                            dims.append((to_int(lo(vm)), to_int(hi(vm))))
                    old = frame.arrays.get(k)
                    if old is not None and not re_ and not vm.dynamic_ok:
                        raise BasicError("Array already dimensioned")
                    new = Array(dims, None if r else sf, r, types)
                    if pres and old is not None:
                        n = min(len(old.data), len(new.data))
                        new.data[:n] = old.data[:n]
                    frame.arrays[k] = new
                self.emit(op)
            if not self.accept_op(","):
                break

    def st_REDIM(self):
        self.st_DIM(redim=True)

    def st_ERASE(self):
        while True:
            name = self.expect_id()
            scope, key, suffix = self.array_key(name)

            def op(vm, s=scope, k=key):
                frame = vm.g if s == "g" else vm.frame
                a = frame.arrays.get(k)
                if a is not None:
                    a.data = [new_record(a.rtype, self.prog.types) if a.rtype else default_for(a.suffix)
                              for _ in a.data] if a.rtype else [default_for(a.suffix)] * len(a.data)
            self.emit(op)
            if not self.accept_op(","):
                break

    def st_CONST(self):
        while True:
            name = self.expect_id()
            self.expect_op("=")
            e, k = self.expr()
            base = self._base(name)
            suffix = name[-1] if name[-1] in SUFFIXES else ("$" if k == "s" else "#" if k == "n" else "!")
            if k == "s":
                suffix = "$"
            self.declared[base] = suffix
            if self.unit is self.prog.main:
                self.shared_globals.add(base)
            scope, key, _s = self.var_key(base + suffix)
            self.emit(lambda vm, s=scope, k=key, e=e: (vm.g if s == "g" else vm.frame).vars.__setitem__(k, e(vm)))
            if not self.accept_op(","):
                break

    def st_DEFINT(self):
        self.pos = len(self.tokens)

    st_DEFLNG = st_DEFSNG = st_DEFDBL = st_DEFSTR = st_DEFINT

    def st_DECLARE(self):
        self.pos = len(self.tokens)

    def st_OPTION(self):
        self.expect_kw("BASE")
        n = self.next().value
        self.emit(lambda vm: setattr(vm, "option_base", int(n)))

    def st_SHARED(self):
        while True:
            name = self.expect_id()
            base = self._base(name)
            self.sub_shared.add(base)
            if self.accept_op("("):
                self.expect_op(")")
            if self.accept_kw("AS"):
                t = self.next()
                if t.value in TYPE_SUFFIX:
                    self.global_declared.setdefault(base, TYPE_SUFFIX[t.value])
            if not self.accept_op(","):
                break

    def st_STATIC(self):
        while True:
            name = self.expect_id()
            base = self._base(name)
            if self.accept_op("("):
                self.expect_op(")")
            if self.accept_kw("AS"):
                t = self.next()
                if t.value in TYPE_SUFFIX:
                    self.declared[base] = TYPE_SUFFIX[t.value]
            scope, key, _s = self.var_key(name)
            self.unit.statics.add(key)
            if not self.accept_op(","):
                break

    def st_COMMON(self):
        self.pos = len(self.tokens)

    def st_DEF(self):
        t = self.peek()
        if t is not None and t.kind == "id" and t.value == "SEG":
            self.pos = len(self.tokens)
            return
        raise CompileError("DEF FN is not supported - use a FUNCTION", self.line_no)

    def st_TYPE(self):
        raise CompileError("TYPE ... END TYPE belongs outside SUBs and FUNCTIONs", self.line_no)

    # ---- flow ----
    def st_END(self):
        t = self.peek()
        if t is not None and t.kind == "kw" and t.value in ("IF", "SELECT", "SUB", "FUNCTION", "TYPE", "DEF"):
            self.pos += 1
            if t.value == "IF":
                return self._end_if()
            if t.value == "SELECT":
                return self._end_select()
            return
        self.emit(_end_op)

    def st_SYSTEM(self):
        self.emit(_end_op)

    def st_STOP(self):
        self.emit(_end_op)

    def st_CLEAR(self):
        self._optional_args(3)
        self.emit(lambda vm: vm.clear())

    def st_RUN(self):
        self.pos = len(self.tokens)
        self.emit(lambda vm: vm.restart())

    def st_GOTO(self):
        label = self._label()
        cell = self.label_cell(label)
        self.emit(lambda vm: cell[0])

    def _label(self):
        t = self.next()
        if t.kind == "num":
            return str(t.value)
        if t.kind == "id":
            return t.value
        raise CompileError("Expected: a label or line number", self.line_no)

    def st_GOSUB(self):
        label = self._label()
        cell = self.label_cell(label)
        ret = self.here() + 1

        def op(vm):
            vm.frame.gosubs.append(ret)
            if len(vm.frame.gosubs) > 10000:
                raise BasicError("Out of stack space")
            return cell[0]
        self.emit(op)

    def st_RETURN(self):
        cell = None
        if not self.at_end():
            cell = self.label_cell(self._label())

        def op(vm):
            if not vm.frame.gosubs:
                raise BasicError("RETURN without GOSUB")
            r = vm.frame.gosubs.pop()
            return cell[0] if cell else r
        self.emit(op)

    def st_ON(self):
        if self.accept_kw("ERROR"):
            self.expect_kw("GOTO")
            label = self._label()
            if label == "0":
                self.emit(lambda vm: setattr(vm, "on_error", None))
                return
            cell = self.label_cell(label)
            unit = self.unit
            self.emit(lambda vm: setattr(vm, "on_error", (unit, cell)))
            return
        if self.peek() is not None and self.peek().kind == "id" and self.peek().value == "TIMER":
            self.pos = len(self.tokens)
            return
        if self.at_kw("KEY", "PLAY"):
            self.pos = len(self.tokens)
            return
        e = self.expr()[0]
        gosub = self.accept_kw("GOSUB")
        if not gosub:
            self.expect_kw("GOTO")
        cells = [self.label_cell(self._label())]
        while self.accept_op(","):
            cells.append(self.label_cell(self._label()))
        ret = self.here() + 1

        def op(vm):
            i = to_int(e(vm))
            if 1 <= i <= len(cells):
                if gosub:
                    vm.frame.gosubs.append(ret)
                return cells[i - 1][0]
            if i < 0 or i > 255:
                raise BasicError("Illegal function call")
        self.emit(op)

    def st_RESUME(self):
        if self.accept_kw("NEXT"):
            self.emit(lambda vm: vm.resume(True))
            return
        if self.at_end() or (self.peek().kind == "num" and self.peek().value == 0):
            if not self.at_end():
                self.pos += 1
            self.emit(lambda vm: vm.resume(False))
            return
        cell = self.label_cell(self._label())
        self.emit(lambda vm: vm.resume(cell[0]))

    def st_ERROR(self):
        e = self.expr()[0]

        def op(vm):
            n = to_int(e(vm))
            msg = next((m for m, c in BasicError.CODES.items() if c == n), f"Unprintable error ({n})")
            raise BasicError(msg, code=n)
        self.emit(op)

    def st_IF(self):
        cond, k = self.expr()
        if k == "s":
            raise CompileError("Type mismatch", self.line_no)
        if self.accept_kw("GOTO"):
            cell = self.label_cell(self._label())
            self.emit(lambda vm: cell[0] if cond(vm) else None)
            if self.accept_kw("ELSE"):
                self._single_else()
            return
        self.expect_kw("THEN")
        if self.peek() is None:                                  # a block IF
            false_cell = [None]
            self.emit(lambda vm: None if cond(vm) else false_cell[0])
            self.blocks.append({"kind": "IF", "line": self.line_no, "false": false_cell, "ends": [], "else": False})
            return
        false_cell = [None]
        self.emit(lambda vm: None if cond(vm) else false_cell[0])
        if self.peek().kind == "num":                           # IF x THEN 100
            cell = self.label_cell(self._label())
            self.emit(lambda vm: cell[0], start=False)
        else:
            self._single_body()
        if self.accept_kw("ELSE"):
            end_cell = [None]
            self.emit(lambda vm: end_cell[0], start=False)
            false_cell[0] = self.here()
            self._single_else()
            end_cell[0] = self.here()
        else:
            false_cell[0] = self.here()

    def _single_body(self):
        """The statements of a one-line IF's THEN part (up to ELSE or the end of the line)."""
        while self.peek() is not None and not self.at_kw("ELSE"):
            if self.accept_op(":"):
                continue
            self.statement()

    def _single_else(self):
        if self.peek() is not None and self.peek().kind == "num":
            cell = self.label_cell(self._label())
            self.emit(lambda vm: cell[0], start=False)
            return
        while self.peek() is not None:
            if self.accept_op(":"):
                continue
            self.statement()

    def _block(self, kind):
        for b in reversed(self.blocks):
            if b["kind"] == kind:
                return b
        return None

    def st_ELSEIF(self):
        b = self.blocks[-1] if self.blocks else None
        if b is None or b["kind"] != "IF" or b["else"]:
            raise CompileError("ELSEIF without IF", self.line_no)
        end_cell = [None]
        self.emit(lambda vm: end_cell[0], start=False)
        b["ends"].append(end_cell)
        b["false"][0] = self.here()
        cond, _k = self.expr()
        self.expect_kw("THEN")
        false_cell = [None]
        self.emit(lambda vm: None if cond(vm) else false_cell[0])
        b["false"] = false_cell

    def st_ELSE(self):
        b = self.blocks[-1] if self.blocks else None
        if b is None or b["kind"] != "IF" or b["else"]:
            raise CompileError("ELSE without IF", self.line_no)
        end_cell = [None]
        self.emit(lambda vm: end_cell[0], start=False)
        b["ends"].append(end_cell)
        b["false"][0] = self.here()
        b["false"] = [None]
        b["else"] = True

    def _end_if(self):
        b = self.blocks.pop() if self.blocks and self.blocks[-1]["kind"] == "IF" else None
        if b is None:
            raise CompileError("END IF without block IF", self.line_no)
        here = self.here()
        b["false"][0] = here
        for c in b["ends"]:
            c[0] = here

    def st_SELECT(self):
        self.expect_kw("CASE")
        e, k = self.expr()
        self.counter += 1
        slot = f"\x00sel{self.counter}"
        self.emit(lambda vm: vm.frame.vars.__setitem__(slot, e(vm)))
        self.blocks.append({"kind": "SELECT", "line": self.line_no, "slot": slot, "next": None, "ends": [],
                            "kindv": k})

    def st_CASE(self):
        b = self.blocks[-1] if self.blocks else None
        if b is None or b["kind"] != "SELECT":
            raise CompileError("CASE without SELECT CASE", self.line_no)
        if b["next"] is not None:
            end_cell = [None]
            self.emit(lambda vm: end_cell[0], start=False)
            b["ends"].append(end_cell)
            b["next"][0] = self.here()
        slot = b["slot"]
        if self.accept_kw("ELSE"):
            b["next"] = [None]
            return
        tests = []
        while True:
            if self.accept_kw("IS"):
                op = self.next().value
                v = self.expr()[0]
                f = {"=": lambda x, y: x == y, "<>": lambda x, y: x != y, "<": lambda x, y: x < y,
                     ">": lambda x, y: x > y, "<=": lambda x, y: x <= y, ">=": lambda x, y: x >= y}.get(op)
                if f is None:
                    raise CompileError("Expected: a comparison after IS", self.line_no)
                tests.append((lambda f, v: lambda vm, x: f(x, v(vm)))(f, v))
            else:
                lo = self.expr()[0]
                if self.accept_kw("TO"):
                    hi = self.expr()[0]
                    tests.append((lambda lo, hi: lambda vm, x: lo(vm) <= x <= hi(vm))(lo, hi))
                else:
                    tests.append((lambda v: lambda vm, x: x == v(vm))(lo))
            if not self.accept_op(","):
                break
        nxt = [None]
        b["next"] = nxt

        def op(vm):
            x = vm.frame.vars[slot]
            for t in tests:
                if t(vm, x):
                    return None
            return nxt[0]
        self.emit(op)

    def _end_select(self):
        b = self.blocks.pop() if self.blocks and self.blocks[-1]["kind"] == "SELECT" else None
        if b is None:
            raise CompileError("END SELECT without SELECT CASE", self.line_no)
        here = self.here()
        if b["next"] is not None:
            b["next"][0] = here
        for c in b["ends"]:
            c[0] = here

    def st_FOR(self):
        name = self.expect_id()
        put, kind, get = self._simple_target(name)
        self.expect_op("=")
        start = self.expr()[0]
        self.expect_kw("TO")
        end = self.expr()[0]
        step = None
        if self.accept_kw("STEP"):
            step = self.expr()[0]
        self.counter += 1
        ek, sk = f"\x00fe{self.counter}", f"\x00fs{self.counter}"

        def init(vm):
            v0 = start(vm)
            e = end(vm)
            s = step(vm) if step else 1
            put(vm, v0)
            vm.frame.vars[ek] = e
            vm.frame.vars[sk] = s
        self.emit(init)
        exit_cell = [None]
        check = self.here()

        def test(vm):
            v = get(vm)
            s = vm.frame.vars[sk]
            if (s >= 0 and v > vm.frame.vars[ek]) or (s < 0 and v < vm.frame.vars[ek]):
                return exit_cell[0]
        self.emit(test, start=False)
        self.blocks.append({"kind": "FOR", "line": self.line_no, "var": self._base(name), "put": put, "get": get,
                            "check": check, "exit": exit_cell, "sk": sk})

    def _simple_target(self, name):
        if "." in name:
            got = self._field_ref(name)
            if got is not None:
                get, put, kind = got
                return put, kind, get
        scope, key, suffix = self.var_key(name)
        d = default_for(suffix)
        if scope == "g":
            return (lambda vm, v: vm.g.vars.__setitem__(key, coerce(v, suffix))), "n", \
                (lambda vm: vm.g.vars.get(key, d))
        return (lambda vm, v: vm.frame.vars.__setitem__(key, coerce(v, suffix))), "n", \
            (lambda vm: vm.frame.vars.get(key, d))

    def st_NEXT(self):
        names = []
        if not self.at_end():
            while True:
                names.append(self.expect_id())
                if not self.accept_op(","):
                    break
        for _ in range(max(1, len(names))):
            b = self.blocks.pop() if self.blocks and self.blocks[-1]["kind"] == "FOR" else None
            if b is None:
                raise CompileError("NEXT without FOR", self.line_no)
            put, get, sk, check = b["put"], b["get"], b["sk"], b["check"]

            def op(vm, put=put, get=get, sk=sk, check=check):
                put(vm, get(vm) + vm.frame.vars[sk])
                return check
            self.emit(op)
            b["exit"][0] = self.here()

    def st_WHILE(self):
        cond = self.expr()[0]
        exit_cell = [None]
        top = self.here()
        self.emit(lambda vm: None if cond(vm) else exit_cell[0])
        self.blocks.append({"kind": "WHILE", "line": self.line_no, "top": top, "exit": exit_cell})

    def st_WEND(self):
        b = self.blocks.pop() if self.blocks and self.blocks[-1]["kind"] == "WHILE" else None
        if b is None:
            raise CompileError("WEND without WHILE", self.line_no)
        top = b["top"]
        self.emit(lambda vm: top)
        b["exit"][0] = self.here()

    def st_DO(self):
        exit_cell = [None]
        top = self.here()
        if self.accept_kw("WHILE"):
            cond = self.expr()[0]
            self.emit(lambda vm: None if cond(vm) else exit_cell[0])
        elif self.accept_kw("UNTIL"):
            cond = self.expr()[0]
            self.emit(lambda vm: exit_cell[0] if cond(vm) else None)
        else:
            self.emit(lambda vm: None)
        self.blocks.append({"kind": "DO", "line": self.line_no, "top": top, "exit": exit_cell})

    def st_LOOP(self):
        b = self.blocks.pop() if self.blocks and self.blocks[-1]["kind"] == "DO" else None
        if b is None:
            raise CompileError("LOOP without DO", self.line_no)
        top = b["top"]
        if self.accept_kw("WHILE"):
            cond = self.expr()[0]
            self.emit(lambda vm: top if cond(vm) else None)
        elif self.accept_kw("UNTIL"):
            cond = self.expr()[0]
            self.emit(lambda vm: None if cond(vm) else top)
        else:
            self.emit(lambda vm: top)
        b["exit"][0] = self.here()

    def st_EXIT(self):
        t = self.next()
        what = t.value
        if what in ("SUB", "FUNCTION", "DEF"):
            cell = self.end_cell()
            self.emit(lambda vm: cell[0])
            return
        kind = {"FOR": "FOR", "DO": "DO", "WHILE": "WHILE"}.get(what)
        b = self._block(kind) if kind else None
        if b is None:
            raise CompileError(f"EXIT {what} not within {what}", self.line_no)
        cell = b["exit"]
        self.emit(lambda vm: cell[0])

    def st_CALL(self):
        name = self.expect_id()
        self._call_sub(self._base(name), parens=True)

    def st_SUB(self):
        raise CompileError("SUB inside a SUB or FUNCTION", self.line_no)

    def st_FUNCTION(self):
        raise CompileError("FUNCTION inside a SUB or FUNCTION", self.line_no)

    def st_SWAP(self):
        p1, k1, g1 = self.target()
        self.expect_op(",")
        p2, k2, g2 = self.target()
        if k1 != k2 and "r" not in (k1, k2):
            raise CompileError("Type mismatch", self.line_no)

        def op(vm):
            a, b = g1(vm), g2(vm)
            p1(vm, b)
            p2(vm, a)
        self.emit(op)

    def st_DATA(self):
        t = self.next()
        for value, quoted in split_data(t.value):
            self.prog.data.append((value, quoted))

    def st_READ(self):
        targets = self._targets()
        self.emit(lambda vm: vm.read_data(targets))

    def st_RESTORE(self):
        label = None if self.at_end() else self._label()
        prog = self.prog

        def op(vm):
            if label is None:
                vm.data_pos = 0
            else:
                vm.data_pos = prog.data_labels.get(label, 0)
        self.emit(op)

    # ---- files ----
    def st_OPEN(self):
        fname = self.expr()[0]
        mode = "INPUT"
        if self.accept_kw("FOR"):
            t = self.next()
            mode = t.value
            if mode not in ("INPUT", "OUTPUT", "APPEND", "RANDOM", "BINARY"):
                raise CompileError("Expected: INPUT, OUTPUT, APPEND, RANDOM or BINARY", self.line_no)
        if self.accept_kw("ACCESS"):
            self.next()
            if self.at_kw("WRITE"):
                self.pos += 1
        self.expect_kw("AS")
        self.accept_op("#")
        num = self.expr()[0]
        if self.peek() is not None and self.peek().kind == "id" and self.peek().value == "LEN":
            self.pos += 1
            self.expect_op("=")
            self.expr()
        self.emit(lambda vm: vm.open_file(fname(vm), mode, to_int(num(vm))))

    def st_CLOSE(self):
        nums = []
        while not self.at_end():
            self.accept_op("#")
            nums.append(self.expr()[0])
            if not self.accept_op(","):
                break
        self.emit(lambda vm: vm.close_files([to_int(n(vm)) for n in nums]))

    def st_RESET(self):
        self.emit(lambda vm: vm.close_files([]))

    def st_KILL(self):
        f = self.expr()[0]
        self.emit(lambda vm: vm.kill(f(vm)))

    def st_NAME(self):
        a = self.expr()[0]
        self.expect_kw("AS")
        b = self.expr()[0]
        self.emit(lambda vm: os.replace(vm.path(a(vm)), vm.path(b(vm))))

    def st_MKDIR(self):
        a = self.expr()[0]
        self.emit(lambda vm: os.makedirs(vm.path(a(vm)), exist_ok=True))

    def st_CHDIR(self):
        a = self.expr()[0]
        self.emit(lambda vm: setattr(vm, "base_dir", vm.path(a(vm))))

    def st_RMDIR(self):
        a = self.expr()[0]
        self.emit(lambda vm: os.rmdir(vm.path(a(vm))))

    def st_FILES(self):
        a = None if self.at_end() else self.expr()[0]
        self.emit(lambda vm: vm.files(a(vm) if a else "*.*"))

    def st_SEEK(self):
        self.pos = len(self.tokens)

    # ---- things that do nothing here ----
    def _ignore(self):
        self.pos = len(self.tokens)

    st_KEY = st_POKE = st_OUT = st_TRON = st_TROFF = st_LOCK = st_UNLOCK = st_FIELD = st_LSET = st_RSET = _ignore
    st_SHELL = st_CHAIN = _ignore


def _nk(*kinds):
    """The kind of a sum or product: double precision if either side is."""
    return "d" if "d" in kinds else "n"


DOUBLE_FOLLOWS = {"ABS", "INT", "FIX", "SQR", "SIN", "COS", "TAN", "ATN", "EXP", "LOG", "SGN"}


def _arg_ends(t):
    """Whether an argument ends here (so a lone variable before it is passed by reference)."""
    return t is None or (t.kind == "op" and t.value in (",", ")", ":")) or (t.kind == "kw" and t.value == "ELSE")


def _end_op(vm):
    raise EndProgram()


def _copy_record(v):
    if isinstance(v, dict):
        return {k: _copy_record(x) for k, x in v.items()}
    return v


def _paint_color(v):
    if isinstance(v, str):
        return ord(v[0]) if v else 0
    return to_int(v)


# ---- arithmetic (with QBasic's errors) -------------------------------------------------------------------------------
def _plus(a, b):
    if isinstance(a, str) != isinstance(b, str):
        raise BasicError("Type mismatch")
    return a + b


def _minus(a, b):
    return a - b


def _times(a, b):
    return a * b


def _divide(a, b):
    if b == 0:
        raise BasicError("Division by zero")
    return a / b


def _idiv(a, b):
    a, b = to_int(a), to_int(b)
    if b == 0:
        raise BasicError("Division by zero")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _mod(a, b):
    a, b = to_int(a), to_int(b)
    if b == 0:
        raise BasicError("Division by zero")
    return a - b * _idiv(a, b)


def _negate(a):
    return -a


def _power(a, b):
    try:
        if a == 0 and b < 0:
            raise BasicError("Division by zero")
        if a < 0 and b != int(b):
            raise BasicError("Illegal function call")
        r = a ** b
        if isinstance(r, complex):
            raise BasicError("Illegal function call")
        return float(r) if isinstance(r, int) and abs(r) > 2**53 else r
    except OverflowError:
        raise BasicError("Overflow")


# ---- built-in functions: name -> (fn(vm, *args), fewest args, most args, kind) ---------------------------------------
def _need_str(v):
    if not isinstance(v, str):
        raise BasicError("Type mismatch")
    return v


def _need_num(v):
    if isinstance(v, str):
        raise BasicError("Type mismatch")
    return v


def _rnd(vm, n=1):
    if n < 0:
        random.seed(n)
        vm.last_rnd = random.random()
    elif n > 0:
        vm.last_rnd = random.random()
    return vm.last_rnd


def _mid(vm, s, start, n=None):
    s = _need_str(s)
    start = to_int(start)
    if start < 1 or (n is not None and to_int(n) < 0):
        raise BasicError("Illegal function call")
    return s[start - 1:] if n is None else s[start - 1:start - 1 + to_int(n)]


def _instr(vm, a, b, c=None):
    if c is None:
        start, s, t = 1, a, b
    else:
        start, s, t = to_int(a), b, c
    if start < 1:
        raise BasicError("Illegal function call")
    _need_str(s), _need_str(t)
    if t == "":
        return start if start <= len(s) else 0
    return s.find(t, start - 1) + 1


def _string(vm, n, c):
    n = to_int(n)
    if n < 0:
        raise BasicError("Illegal function call")
    ch = c[0] if isinstance(c, str) and c else chr(to_int(c) & 255) if not isinstance(c, str) else ""
    if not ch:
        raise BasicError("Illegal function call")
    return ch * n


def _chr(vm, n):
    n = to_int(n)
    if not 0 <= n <= 255:
        raise BasicError("Illegal function call")
    return chr(n)


def _asc(vm, s):
    s = _need_str(s)
    if not s:
        raise BasicError("Illegal function call")
    return ord(s[0]) & 0xFFFF


def _sqr(vm, x):
    x = _need_num(x)
    if x < 0:
        raise BasicError("Illegal function call")
    return math.sqrt(x)


def _log(vm, x):
    x = _need_num(x)
    if x <= 0:
        raise BasicError("Illegal function call")
    return math.log(x)


def _exp(vm, x):
    try:
        return math.exp(_need_num(x))
    except OverflowError:
        raise BasicError("Overflow")


def _int(vm, x):
    x = _need_num(x)
    return math.floor(x) if isinstance(x, float) else x


def _fix(vm, x):
    x = _need_num(x)
    return math.trunc(x) if isinstance(x, float) else x


def _hex(vm, n):
    n = to_int(n)
    return format(n & 0xFFFFFFFF if n < 0 else n, "X") if n >= -32768 or n < 0 else format(n, "X")


def _oct(vm, n):
    n = to_int(n)
    return format(n & 0xFFFFFFFF if n < 0 else n, "o")


def _timer(vm):
    t = datetime.now()
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6


BUILTINS = {
    "ABS": (lambda vm, x: abs(_need_num(x)), 1, 1, "n"),
    "SGN": (lambda vm, x: (_need_num(x) > 0) - (x < 0), 1, 1, "n"),
    "INT": (_int, 1, 1, "n"),
    "FIX": (_fix, 1, 1, "n"),
    "CINT": (lambda vm, x: coerce(_need_num(x), "%"), 1, 1, "n"),
    "CLNG": (lambda vm, x: coerce(_need_num(x), "&"), 1, 1, "n"),
    "CSNG": (lambda vm, x: float(_need_num(x)), 1, 1, "n"),
    "CDBL": (lambda vm, x: float(_need_num(x)), 1, 1, "d"),
    "SQR": (_sqr, 1, 1, "n"),
    "SIN": (lambda vm, x: math.sin(_need_num(x)), 1, 1, "n"),
    "COS": (lambda vm, x: math.cos(_need_num(x)), 1, 1, "n"),
    "TAN": (lambda vm, x: math.tan(_need_num(x)), 1, 1, "n"),
    "ATN": (lambda vm, x: math.atan(_need_num(x)), 1, 1, "n"),
    "EXP": (_exp, 1, 1, "n"),
    "LOG": (_log, 1, 1, "n"),
    "RND": (_rnd, 0, 1, "n"),
    "TIMER": (_timer, 0, 0, "n"),
    "LEN": (lambda vm, s: len(_need_str(s)), 1, 1, "n"),
    "LEFT$": (lambda vm, s, n: _need_str(s)[:max(0, to_int(n))], 2, 2, "s"),
    "RIGHT$": (lambda vm, s, n: _need_str(s)[len(s) - max(0, to_int(n)):] if to_int(n) > 0 else "", 2, 2, "s"),
    "MID$": (_mid, 2, 3, "s"),
    "INSTR": (_instr, 2, 3, "n"),
    "UCASE$": (lambda vm, s: _need_str(s).upper(), 1, 1, "s"),
    "LCASE$": (lambda vm, s: _need_str(s).lower(), 1, 1, "s"),
    "LTRIM$": (lambda vm, s: _need_str(s).lstrip(" "), 1, 1, "s"),
    "RTRIM$": (lambda vm, s: _need_str(s).rstrip(" "), 1, 1, "s"),
    "STR$": (lambda vm, n: str_dollar(_need_num(n)), 1, 1, "s"),
    "VAL": (lambda vm, s: val_of(_need_str(s)), 1, 1, "n"),
    "CHR$": (_chr, 1, 1, "s"),
    "ASC": (_asc, 1, 1, "n"),
    "STRING$": (_string, 2, 2, "s"),
    "SPACE$": (lambda vm, n: " " * max(0, to_int(n)), 1, 1, "s"),
    "HEX$": (_hex, 1, 1, "s"),
    "OCT$": (_oct, 1, 1, "s"),
    "DATE$": (lambda vm: datetime.now().strftime("%m-%d-%Y"), 0, 0, "s"),
    "TIME$": (lambda vm: datetime.now().strftime("%H:%M:%S"), 0, 0, "s"),
    "INKEY$": (lambda vm: vm.inkey(), 0, 0, "s"),
    "INPUT$": (lambda vm, n, f=None: vm.input_chars(to_int(n), f), 1, 2, "s"),
    "CSRLIN": (lambda vm: vm.scr.row, 0, 0, "n"),
    "POS": (lambda vm, _x=0: vm.scr.col, 0, 1, "n"),
    "POINT": (lambda vm, x, y=None: vm.scr.point(x, y), 1, 2, "n"),
    "EOF": (lambda vm, n: vm.eof(to_int(n)), 1, 1, "n"),
    "LOF": (lambda vm, n: vm.lof(to_int(n)), 1, 1, "n"),
    "FREEFILE": (lambda vm: vm.freefile(), 0, 0, "n"),
    "ERR": (lambda vm: vm.err, 0, 0, "n"),
    "ERL": (lambda vm: vm.erl, 0, 0, "n"),
    "PEEK": (lambda vm, a: 0, 1, 1, "n"),
    "INP": (lambda vm, a: 0, 1, 1, "n"),
    "FRE": (lambda vm, a: 60000, 1, 1, "n"),
    "LBOUND": (None, 1, 2, "n"),
    "UBOUND": (None, 1, 2, "n"),
    "ENVIRON$": (lambda vm, s: os.environ.get(_need_str(s), "") if isinstance(s, str) else "", 1, 1, "s"),
    "COMMAND$": (lambda vm: "", 0, 0, "s"),
    "_PI": (lambda vm: math.pi, 0, 0, "n"),
    "TRUE": (lambda vm: -1, 0, 0, "n"),            # (not QBasic's, but programs - and AI models - lean on them)
    "FALSE": (lambda vm: 0, 0, 0, "n"),
}


# ---- the machine -----------------------------------------------------------------------------------------------------
class Frame:
    __slots__ = ("vars", "arrays", "gosubs", "unit", "line")

    def __init__(self, unit):
        self.vars, self.arrays, self.gosubs, self.unit = {}, {}, [], unit
        self.line = 0


class OpenFile:
    def __init__(self, path, mode, handle):
        self.path, self.mode, self.f = path, mode, handle


class Machine:
    """Runs a compiled Program against a screen. Made on the GUI side, run() on a worker thread; the GUI talks to it
    through keys (a deque), stop(), and the debugger's pause/step/continue."""

    def __init__(self, prog, scr, sound, base_dir=".", on_pause=None):
        self.prog = prog
        self.scr = scr
        self.sound = sound
        self.base_dir = str(base_dir)
        self.keys = deque()
        self.option_base = 0
        self.dynamic_ok = True
        self.last_rnd = random.random()
        self.data_pos = 0
        self.files = {}
        self.on_error = None
        self.err, self.erl = 0, 0
        self.err_resume = None
        self.g = Frame(prog.main)
        self.frame = self.g
        self.depth = 0
        self.stack = []                         # [(unit, frame)] for the debugger's call stack
        # the debugger
        self.stopping = False
        self.breakpoints = set()
        self.step_mode = None                   # None, "into", "over", "out"
        self.step_depth = 0
        self.paused = threading.Event()
        self.resume_event = threading.Event()
        self.on_pause = on_pause
        self.pause_request = False
        self.last_line = None
        self.retrace = time.perf_counter()
        self.files_cb = None
        self.watch_on = False
        self._update_watch()

    # ---- control from the GUI ----
    def stop(self):
        self.stopping = True
        self._update_watch()
        self.resume_event.set()

    def set_breakpoints(self, lines):
        self.breakpoints = set(lines)
        self._update_watch()

    def request_pause(self):
        self.pause_request = True
        self._update_watch()

    def resume(self, how):
        """RESUME (from an error handler) - not the debugger's continue."""
        if self.err_resume is None:
            raise BasicError("RESUME without error")
        unit, pc = self.err_resume
        self.err_resume = None
        self.err = 0
        if how is True:
            return pc + 1
        if how is False:
            return pc
        return how

    def cont(self, mode=None):
        """The debugger: carry on (mode None), or step "into", "over" or "out"."""
        self.step_mode = mode
        self.step_depth = self.depth
        self._update_watch()
        self.resume_event.set()

    def _update_watch(self):
        self.watch_on = bool(self.stopping or self.breakpoints or self.step_mode or self.pause_request)

    # ---- running ----
    def run(self):
        """The whole program: returns None when it ends, or the BasicError it stopped on."""
        try:
            self.run_unit(self.prog.main, self.g)
        except EndProgram:
            pass
        except StopProgram:
            return "stopped"
        except BasicError as e:
            return e
        except RecursionError:
            return BasicError("Out of stack space", self.last_line)
        finally:
            self.close_files([])
        return None

    def run_unit(self, unit, frame):
        code, lines, starts = unit.code, unit.lines, unit.starts
        n = len(code)
        pc = 0
        prev = self.frame
        self.frame = frame
        self.depth += 1
        self.stack.append((unit, frame))
        try:
            while True:
                try:
                    while pc < n:
                        if self.watch_on:
                            self._watch(unit, pc, lines, starts)
                        r = code[pc](self)
                        pc = pc + 1 if r is None else r
                    return
                except BasicError as e:
                    if e.line is None:
                        e.line = lines[pc] if pc < n else lines[-1] if lines else 0
                    handled = self._handle(unit, pc, e)
                    if handled is None:
                        raise
                    pc = handled
                except (EndProgram, StopProgram):
                    raise
                except RecursionError:
                    raise BasicError("Out of stack space", lines[pc] if pc < n else 0)
                except ZeroDivisionError:
                    e = BasicError("Division by zero", lines[pc] if pc < n else 0)
                    handled = self._handle(unit, pc, e)
                    if handled is None:
                        raise e
                    pc = handled
                except OverflowError:
                    e = BasicError("Overflow", lines[pc] if pc < n else 0)
                    handled = self._handle(unit, pc, e)
                    if handled is None:
                        raise e
                    pc = handled
                except (TypeError, ValueError) as ex:
                    e = BasicError("Type mismatch" if isinstance(ex, TypeError) else "Illegal function call",
                                   lines[pc] if pc < n else 0)
                    handled = self._handle(unit, pc, e)
                    if handled is None:
                        raise e
                    pc = handled
                except OSError as ex:
                    msg = "File not found" if isinstance(ex, FileNotFoundError) else "Path/File access error"
                    e = BasicError(msg, lines[pc] if pc < n else 0)
                    handled = self._handle(unit, pc, e)
                    if handled is None:
                        raise e
                    pc = handled
        finally:
            self.frame = prev
            self.depth -= 1
            self.stack.pop()

    def _handle(self, unit, pc, e):
        """ON ERROR GOTO: the handler's place in this unit, or None (the error stops the program)."""
        if self.on_error is None or self.err_resume is not None:
            return None
        h_unit, cell = self.on_error
        if h_unit is not unit:
            return None
        self.err, self.erl = e.code, e.line or 0
        self.err_resume = (unit, pc)
        return cell[0]

    def _watch(self, unit, pc, lines, starts):
        if self.stopping:
            raise StopProgram()
        if not starts[pc]:
            return
        line = lines[pc]
        pause = False
        if self.pause_request:
            pause = True
            self.pause_request = False
        elif self.step_mode == "into":
            pause = True
        elif self.step_mode == "over" and self.depth <= self.step_depth:
            pause = True
        elif self.step_mode == "out" and self.depth < self.step_depth:
            pause = True
        elif line in self.breakpoints and (line != self.last_line or pc == 0):
            pause = True
        self.last_line = line
        if not pause:
            return
        self.step_mode = None
        self._update_watch()
        self.resume_event.clear()
        self.paused.set()
        if self.on_pause:
            self.on_pause(line, unit.name)
        while not self.resume_event.wait(0.1):
            if self.stopping:
                break
        self.paused.clear()
        if self.stopping:
            raise StopProgram()

    def call(self, unit, args):
        """A SUB or FUNCTION: a new frame with its parameters, by reference (copied back) unless an expression."""
        frame = Frame(unit)
        if unit.static_all:
            frame.vars = unit.static_values
        elif unit.statics:
            for k in unit.statics:
                if k in unit.static_values:
                    frame.vars[k] = unit.static_values[k]
        vals = []
        for (base, suffix, is_array, _byval, rtype), (get, put, arr) in zip(unit.params, args):
            if is_array:
                a = arr(self) if arr is not None else None
                if a is None:
                    raise BasicError("Parameter type mismatch")
                frame.arrays[base + (suffix if not rtype else "") + "()"] = a
                vals.append(None)
                continue
            v = get(self)
            if rtype:
                frame.vars[base] = v
            else:
                frame.vars[base + suffix] = coerce(v, suffix)
            vals.append(v)
        if self.depth > 2000:
            raise BasicError("Out of stack space")
        self.run_unit(unit, frame)
        for (base, suffix, is_array, byval, rtype), (get, put, arr) in zip(unit.params, args):
            if put is not None and not is_array and not byval and not rtype:
                put(self, frame.vars.get(base + suffix))
        if unit.statics and not unit.static_all:
            for k in unit.statics:
                if k in frame.vars:
                    unit.static_values[k] = frame.vars[k]
        if unit.kind == "function":
            return frame.vars.get("\x00result", default_for(unit.result))
        return None

    def clear(self):
        self.g.vars.clear()
        self.g.arrays.clear()

    def restart(self):
        raise BasicError("RUN is not supported - press F5 again")

    # ---- PRINT ----
    def print_items(self, fnum, items, newline):
        out = self._out(fnum)
        for it in items:
            kind = it[0]
            if kind == "e":
                v = it[1](self)
                if isinstance(v, str):
                    out.text(v)
                else:
                    s = num_text(v, it[2] == "d")
                    out.text((s if s.startswith("-") else " " + s) + " ")
            elif kind == ",":
                out.zone()
            elif kind == "tab":
                out.tab(to_int(it[1](self)))
            elif kind == "spc":
                out.text(" " * max(0, to_int(it[1](self))))
        if newline:
            out.newline()

    def write_items(self, fnum, vals):
        out = self._out(fnum)
        parts = [f'"{v}"' if isinstance(v, str) else num_text(v) for v in vals]
        out.text(",".join(parts))
        out.newline()

    def print_using(self, fnum, fmt, vals, newline):
        out = self._out(fnum)
        out.text(format_using(_need_str(fmt), vals))
        if newline:
            out.newline()

    def _out(self, fnum):
        if fnum is None:
            return self.scr
        n = to_int(fnum(self))
        f = self.files.get(n)
        if f is None:
            raise BasicError("Bad file name or number")
        if f.mode not in ("OUTPUT", "APPEND"):
            raise BasicError("Bad file mode")
        return _FileOut(f)

    # ---- keys and INPUT ----
    def inkey(self):
        if self.stopping:
            raise StopProgram()
        if self.keys:
            return self.keys.popleft()
        time.sleep(0)                           # (a polling loop lets the screen and keys through)
        return ""

    def wait_key(self):
        while True:
            if self.stopping:
                raise StopProgram()
            if self.keys:
                return self.keys.popleft()
            time.sleep(0.01)

    def input_chars(self, n, fnum=None):
        if fnum is not None:
            f = self._in(to_int(fnum))
            s = f.f.read(n)
            if len(s) < n:
                raise BasicError("Input past end of file")
            return s
        out = ""
        while len(out) < n:
            k = self.wait_key()
            out += k
        return out[:n]

    def line_input(self, prompt, same_line=False):
        if prompt:
            self.scr.text(prompt)
        return self._edit_line(same_line)

    def _edit_line(self, same_line=False):
        """Typing a line on the screen, as QBasic does: echo, backspace, Enter."""
        buf = ""
        self.scr.cursor_on = True
        try:
            while True:
                k = self.wait_key()
                if k == "\r":
                    break
                if k == "\x08":
                    if buf:
                        buf = buf[:-1]
                        self.scr.backspace()
                    continue
                if k == "\x1b":
                    for _ in buf:
                        self.scr.backspace()
                    buf = ""
                    continue
                if len(k) == 1 and (k >= " " or k == "\t") and len(buf) < 255:
                    buf += k
                    self.scr.text(k)
        finally:
            self.scr.cursor_on = False
        if not same_line:
            self.scr.newline()
        return buf

    def input_vars(self, prompt, mark, targets, same_line=False):
        while True:
            self.scr.text((prompt or "") + ("? " if mark else ""))
            line = self._edit_line(same_line)
            parts = _split_input(line, len(targets))
            if parts is None or len(parts) != len(targets):
                if len(targets) == 1 and parts is not None and len(parts) == 0:
                    parts = [""]
                else:
                    self.scr.text("Redo from start")
                    self.scr.newline()
                    continue
            ok = True
            values = []
            for (put, kind), p in zip(targets, parts):
                if kind == "s":
                    values.append(p)
                else:
                    t = p.strip()
                    if t and not re.fullmatch(r"[+-]?(\d+\.?\d*|\.\d+)([EeDd][+-]?\d+)?[%&!#]?|&[HhOo][0-9A-Fa-f]+",
                                              t):
                        ok = False
                        break
                    values.append(val_of(t) if t else 0)
            if not ok:
                self.scr.text("Redo from start")
                self.scr.newline()
                continue
            for (put, kind), v in zip(targets, values):
                put(self, v)
            return

    # ---- DATA ----
    def read_data(self, targets):
        for put, kind in targets:
            if self.data_pos >= len(self.prog.data):
                raise BasicError("Out of DATA")
            text, quoted = self.prog.data[self.data_pos]
            self.data_pos += 1
            if kind == "s":
                put(self, text)
            else:
                t = text.strip()
                if quoted or (t and not re.fullmatch(r"[+-]?(\d+\.?\d*|\.\d+)([EeDd][+-]?\d+)?[%&!#]?|&[HhOo]?[0-9A-Fa-f]+",
                                                     t)):
                    raise BasicError("Syntax error")
                put(self, val_of(t) if t else 0)

    # ---- time ----
    def sleep(self, secs):
        end = None if secs is None or secs <= 0 else time.monotonic() + float(secs)
        start_keys = len(self.keys)
        while True:
            if self.stopping:
                raise StopProgram()
            if len(self.keys) > start_keys:
                self.keys.popleft()                      # (the key that woke it is used up, as in QBasic)
                return
            if end is not None and time.monotonic() >= end:
                return
            time.sleep(0.01)

    def wait_retrace(self):
        """WAIT &H3DA, 8: until the next 70th of a second (the VGA's vertical retrace)."""
        now = time.perf_counter()
        nxt = self.retrace + 1 / 70
        if nxt > now:
            time.sleep(nxt - now)
            self.retrace = nxt
        else:
            self.retrace = now
        if self.stopping:
            raise StopProgram()

    # ---- files ----
    def path(self, name):
        name = _need_str(name)
        return name if os.path.isabs(name) else os.path.join(self.base_dir, name)

    def open_file(self, name, mode, num):
        if num in self.files:
            raise BasicError("File already open")
        if not 1 <= num <= 255:
            raise BasicError("Bad file name or number")
        p = self.path(name)
        try:
            if mode == "INPUT":
                h = open(p, "r", encoding="cp437", newline="")
            elif mode == "OUTPUT":
                h = open(p, "w", encoding="cp437", errors="replace", newline="")
            elif mode == "APPEND":
                h = open(p, "a", encoding="cp437", errors="replace", newline="")
            else:
                h = open(p, "a+b")
        except FileNotFoundError:
            raise BasicError("File not found")
        except OSError:
            raise BasicError("Path/File access error")
        self.files[num] = OpenFile(p, mode, h)

    def close_files(self, nums):
        for n in (nums or list(self.files)):
            f = self.files.pop(n, None)
            if f is not None:
                try:
                    f.f.close()
                except OSError:
                    pass

    def _in(self, n):
        f = self.files.get(n)
        if f is None:
            raise BasicError("Bad file name or number")
        if f.mode != "INPUT":
            raise BasicError("Bad file mode")
        return f

    def eof(self, n):
        f = self._in(n)
        pos = f.f.tell()
        ch = f.f.read(1)
        if not ch or ch == "\x1a":
            return -1
        f.f.seek(pos)
        return 0

    def lof(self, n):
        f = self.files.get(n)
        if f is None:
            raise BasicError("Bad file name or number")
        try:
            return os.path.getsize(f.path)
        except OSError:
            return 0

    def freefile(self):
        n = 1
        while n in self.files:
            n += 1
        return n

    def _read_field(self, f):
        """INPUT #: the next comma- or line-separated item (quotes respected)."""
        h = f.f
        ch = h.read(1)
        while ch in (" ", "\r", "\n", "\t"):
            ch = h.read(1)
        if not ch:
            raise BasicError("Input past end of file")
        if ch == '"':
            out = []
            ch = h.read(1)
            while ch and ch != '"':
                out.append(ch)
                ch = h.read(1)
            ch = h.read(1)
            while ch in (" ", "\t"):
                ch = h.read(1)
            if ch == "\r":
                pos = h.tell()
                if h.read(1) != "\n":
                    h.seek(pos)
            return "".join(out)
        out = []
        while ch and ch not in (",", "\n", "\r"):
            out.append(ch)
            ch = h.read(1)
        if ch == "\r":
            pos = h.tell()
            if h.read(1) != "\n":
                h.seek(pos)
        return "".join(out).strip()

    def input_file(self, fnum, targets):
        f = self._in(to_int(fnum))
        for put, kind in targets:
            v = self._read_field(f)
            put(self, v if kind == "s" else val_of(v))

    def line_input_file(self, fnum):
        f = self._in(to_int(fnum))
        line = f.f.readline()
        if not line:
            raise BasicError("Input past end of file")
        return line.rstrip("\r\n")

    def kill(self, name):
        p = self.path(name)
        try:
            os.remove(p)
        except FileNotFoundError:
            raise BasicError("File not found")

    def files(self, pattern):
        import glob
        for p in sorted(glob.glob(self.path(pattern))):
            self.scr.text(os.path.basename(p).ljust(16))
        self.scr.newline()


class _FileOut:
    """PRINT # and WRITE # go through the same calls as the screen."""

    def __init__(self, f):
        self.f = f.f
        self.col = 1

    def text(self, s):
        self.f.write(s)
        self.col += len(s)

    def newline(self):
        self.f.write("\r\n")
        self.col = 1

    def zone(self):
        n = 14 - ((self.col - 1) % 14)
        self.text(" " * n)

    def tab(self, n):
        if n > self.col:
            self.text(" " * (n - self.col))


def _split_input(line, want):
    """INPUT's answer split at commas (quotes keep commas); too many or too few is "Redo from start"."""
    parts, cur, q = [], [], False
    for ch in line:
        if ch == '"':
            q = not q
            continue
        if ch == "," and not q:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    parts.append("".join(cur).strip())
    return parts


# ---- PRINT USING -----------------------------------------------------------------------------------------------------
_FIELD = re.compile(r"(\*\*\$|\$\$|\*\*)?(\+)?([#,]*)(\.#*)?(\^\^\^\^\^?)?(-)?")


def format_using(fmt, vals):
    """PRINT USING: # digits, . the point, , thousands, + and - signs, $$ and ** in front, ^^^^ exponent; ! & and
    \\  \\ for strings; _ makes the next character literal. The format repeats while there are values."""
    out = []
    vals = list(vals)
    if not vals:
        return fmt
    i = 0
    used_any = False
    while vals:
        if i >= len(fmt):
            if not used_any:
                raise BasicError("Illegal function call")
            i = 0
        ch = fmt[i]
        if ch == "_" and i + 1 < len(fmt):
            out.append(fmt[i + 1])
            i += 2
            continue
        if ch == "!":
            v = vals.pop(0)
            out.append(_need_str(v)[:1].ljust(1))
            i += 1
            used_any = True
            continue
        if ch == "&":
            out.append(_need_str(vals.pop(0)))
            i += 1
            used_any = True
            continue
        if ch == "\\":
            j = fmt.find("\\", i + 1)
            if j > i and fmt[i + 1:j].strip() == "":
                width = j - i + 1
                out.append(_need_str(vals.pop(0))[:width].ljust(width))
                i = j + 1
                used_any = True
                continue
        m = _FIELD.match(fmt, i)
        if m and (("#" in (m.group(3) or "")) or (m.group(4) and "#" in m.group(4)) or m.group(1)) and \
                m.end() > i:
            out.append(_format_number(m, vals.pop(0)))
            i = m.end()
            used_any = True
            continue
        out.append(ch)
        i += 1
    while i < len(fmt) and fmt[i] not in "#!&\\" and not (fmt[i] in "$*+" and i + 1 < len(fmt)):
        out.append(fmt[i])
        i += 1
    return "".join(out)


def _format_number(m, v):
    v = _need_num(v)
    lead, plus, ints, frac, exp, minus = m.groups()
    ints = ints or ""
    frac = frac or ""
    width = len(ints) + (len(lead) if lead else 0)
    decimals = max(0, len(frac) - 1)
    commas = "," in ints
    neg = v < 0
    av = abs(v)
    if exp:
        digits = len(ints.replace(",", "")) + (1 if not plus and not minus else 0)
        mant_digits = max(1, len(ints.replace(",", "")) - (0 if (plus or minus) else 1))
        s = f"{av:.{decimals}E}"
        mant, e = s.split("E")
        ie = int(e)
        s = f"{mant}E{'+' if ie >= 0 else '-'}{abs(ie):02d}"
        body = s
        _ = digits, mant_digits
    else:
        body = f"{av:,.{decimals}f}" if commas else f"{av:.{decimals}f}"
        if body.startswith("0.") and len(ints.replace(",", "")) == 0:
            body = body[1:]
    sign = ""
    if plus:
        sign = "-" if neg else "+"
    elif neg and not minus:
        sign = "-"
    dollar = "$" if lead and "$" in lead else ""
    text = sign + dollar + body
    if minus:
        text = (dollar + body) + ("-" if neg else " ")
        width += 1
    total = width + len(frac) + (1 if plus else 0)
    if exp:
        total = len(text)
    fill = "*" if lead and lead.startswith("**") else " "
    if len(text) > total:
        return "%" + text
    return text.rjust(total, fill)
