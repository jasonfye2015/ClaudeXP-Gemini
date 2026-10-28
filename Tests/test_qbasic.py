"""Claude QBasic Studio's interpreter, with no window: programs and exactly what they print, the errors it should find,
the shapes of program people (and the Vibe Coder) write, and every built-in example running."""
import threading
import time

import support

from qbstudio import examples, interp, screen

CASES = []          # (name, source, keys, what it prints (None: not checked), check(result) or None)


def case(name, src, prints, keys="", check=None):
    CASES.append((name, src, keys, prints, check))


# ---- the language ---------------------------------------------------------------------------------------------------
case("print basics", '''
PRINT "Hello"; " world"
PRINT 1; 2; -3
PRINT 1/3
PRINT 2^10, 7 \\ 2, 7 MOD 3, -7 MOD 3
x = 5: y% = 7.5: PRINT x * 2; y%
a$ = "abc" + "def": PRINT a$; LEN(a$)
''', ["Hello world", " 1  2 -3", " .3333333", " 1024          3             1            -1", " 10  8",
      "abcdef 6"])

case("strings", '''
s$ = "Hello, World"
PRINT LEFT$(s$, 5); "|"; RIGHT$(s$, 5); "|"; MID$(s$, 8, 3); "|"; INSTR(s$, "World")
PRINT UCASE$("abc"); LCASE$("XyZ"); "["; LTRIM$("  x "); "]"; STR$(42); "|"; VAL("3.5e2"); CHR$(65); ASC("a")
PRINT STRING$(3, "*"); SPACE$(2); "|"; HEX$(255); " "; OCT$(8)
MID$(s$, 1, 5) = "HOWDY": PRINT s$
''', ["Hello|World|Wor| 8", "ABCxyz[x ] 42| 350 A 97", "***  |FF 10", "HOWDY, World"])

case("loops and if", '''
FOR i = 1 TO 3: PRINT i;: NEXT: PRINT
FOR i = 10 TO 1 STEP -4: PRINT i;: NEXT i: PRINT
n = 0: WHILE n < 3: n = n + 1: WEND: PRINT n
DO: n = n - 1: LOOP UNTIL n = 0: PRINT n
DO WHILE n < 5: n = n + 2: LOOP: PRINT n
IF n > 5 THEN PRINT "big" ELSE PRINT "small"
IF n = 6 THEN
  PRINT "six"
ELSEIF n = 7 THEN
  PRINT "seven"
ELSE
  PRINT "other"
END IF
FOR i = 1 TO 10: IF i = 4 THEN EXIT FOR
NEXT: PRINT i
''', [" 1  2  3", " 10  6  2", " 3", " 0", " 6", "big", "six", " 4"])

case("select case", '''
FOR i = 1 TO 6
SELECT CASE i
CASE 1: PRINT "one";
CASE 2, 3: PRINT "two-three";
CASE 4 TO 5: PRINT "four-five";
CASE ELSE: PRINT "else";
END SELECT
NEXT
PRINT
a$ = "dog"
SELECT CASE a$
  CASE IS < "cat": PRINT "before cat"
  CASE "dog": PRINT "woof"
END SELECT
''', ["onetwo-threetwo-threefour-fivefour-fiveelse", "woof"])

case("subs and functions (an argument by reference before a colon)", '''
DECLARE SUB Twice (n)
DECLARE FUNCTION Fact# (n%)
x = 21: Twice x: PRINT x
PRINT Fact#(10)
CALL Hello("Ann")
PRINT Area(2, 3)
SUB Twice (n)
  n = n * 2
END SUB
FUNCTION Fact# (n%)
  IF n% <= 1 THEN Fact# = 1 ELSE Fact# = n% * Fact#(n% - 1)
END FUNCTION
SUB Hello (who$)
  PRINT "Hi, "; who$
END SUB
FUNCTION Area (w, h)
  Area = w * h
END FUNCTION
''', [" 42", " 3628800", "Hi, Ann", " 6"])

case("arrays and types (a field called name)", '''
DIM a(1 TO 5) AS INTEGER, g(2, 2)
FOR i = 1 TO 5: a(i) = i * i: NEXT
PRINT a(1); a(5); LBOUND(a); UBOUND(a)
g(1, 2) = 7: PRINT g(1, 2) + g(0, 0)
TYPE Point
  x AS INTEGER
  y AS INTEGER
  name AS STRING * 5
END TYPE
DIM p AS Point, pts(3) AS Point
p.x = 3: p.y = 4: p.name = "ab"
pts(2).x = 9
PRINT p.x + p.y; pts(2).x; "["; p.name; "]"
b(3) = 4: PRINT b(3)
REDIM c(10): c(10) = 1: PRINT c(10)
''', [" 1  25  1  5", " 7", " 7  9 [ab   ]", " 4", " 1"])

case("gosub, goto, on, data (a space before a quoted item)", '''
GOSUB tell
GOTO skip
PRINT "not here"
skip:
FOR i = 1 TO 2: ON i GOSUB one, two: NEXT
READ a, b$, c
PRINT a; b$; c
RESTORE more
READ d: PRINT d
END
tell: PRINT "told": RETURN
one: PRINT "one": RETURN
two: PRINT "two": RETURN
DATA 10, "hi, there", -2.5
more:
DATA 99
''', ["told", "one", "two", " 10 hi, there-2.5", " 99"])

case("shared and static", '''
DIM SHARED total
CONST LIMIT = 3
FOR i = 1 TO LIMIT: Add i: NEXT
PRINT total; Counter; Counter; Counter
SUB Add (n)
  total = total + n
END SUB
FUNCTION Counter
  STATIC c
  c = c + 1
  Counter = c
END FUNCTION
''', [" 6  1  2  3"])

case("on error and resume next", '''
ON ERROR GOTO handler
x = 1 / 0
PRINT "after"; ERR
END
handler:
PRINT "caught"; ERR
RESUME NEXT
''', ["caught 11", "after 0"])

case("input and inkey", '''
INPUT "Name"; n$
INPUT "Age", a
PRINT n$; a + 1
LINE INPUT "Say: "; s$
PRINT s$
k$ = INKEY$: PRINT "["; k$; "]"
''', ["Name? Ann", "Age41", "Ann 42", "Say: hi, you", "hi, you", "[]"], keys="Ann\r41\rhi, you\r")

case("input with redo from start", '''
INPUT "Number"; n
PRINT n * 2
INPUT a$, b$
PRINT b$; a$
''', ["Number? abc", "Redo from start", "Number? 21", " 42", "? x,y", "yx"], keys="abc\r21\rx,y\r")

case("print using", '''
PRINT USING "###.##"; 3.14159
PRINT USING "$$#,###.##"; 1234.5
PRINT USING "Name: & Score: ###"; "Ann"; 97
PRINT USING "!"; "Hello"
''', ["  3.14", " $1,234.50", "Name: Ann Score:  97", "H"])

case("print zones and tab", '''
PRINT "a", "b", "c"
PRINT TAB(5); "x"; SPC(3); "y"
PRINT "n="; 5
''', ["a             b             c", "    x   y", "n= 5"])

case("numbers (double precision)", '''
PRINT 100000 * 3; 1.5E+10; 1 / 7#; 2 ^ 0.5
PRINT INT(-2.5); FIX(-2.5); CINT(2.5); CINT(3.5); ABS(-3); SGN(-9)
PRINT 7 AND 3; 4 OR 1; NOT 0; 5 XOR 1
DIM SHARED d#
d# = 1 / 3#: PRINT d#; 1 / 3
''', [" 300000  1.5E+10  .1428571428571428  1.414214", "-3 -2  2  4  3 -1", " 3  5 -1  4",
      " .3333333333333333  .3333333"])

case("keywords as names, TRUE and FALSE", '''
color = 3: PRINT color
ok = TRUE: IF ok THEN PRINT "yes"
DIM f AS BOOLEAN: f = FALSE: PRINT f; TRUE
''', [" 3", "yes", " 0 -1"])

case("the DOS box-drawing and shade characters", '''
PRINT CHR$(201); STRING$(3, CHR$(205)); CHR$(187)
PRINT CHR$(176); CHR$(177); CHR$(178); CHR$(219)
''', ["╔═══╗", "░▒▓█"])

case("recursion", '''
PRINT Fib(20)
FUNCTION Fib (n)
IF n < 2 THEN Fib = n ELSE Fib = Fib(n - 1) + Fib(n - 2)
END FUNCTION
''', [" 6765"])

case("graphics statements", '''
SCREEN 13
LINE (0, 0)-(319, 199), 4, BF
CIRCLE (160, 100), 50, 14
PAINT (160, 100), 2, 14
PSET (1, 1), 15
PRINT POINT(1, 1); POINT(160, 100); POINT(300, 5)
DIM spr(100)
GET (150, 90)-(160, 100), spr
PUT (10, 10), spr, PSET
DRAW "C9 BM20,20 R10 D10 L10 U10"
SCREEN 12: COLOR 14: PRINT "graphics text"
''', None)

case("locate and color", '''
CLS
LOCATE 5, 10: COLOR 14, 1: PRINT "here"
PRINT CSRLIN; POS(0)
''', None)

case("files", '''
OPEN "qbtest.txt" FOR OUTPUT AS #1
PRINT #1, "line one"
WRITE #1, "two", 2
CLOSE #1
OPEN "qbtest.txt" FOR INPUT AS #1
LINE INPUT #1, a$
INPUT #1, b$, c
PRINT a$; "|"; b$; c; EOF(1)
CLOSE
''', ["line one|two 2 -1"])

# ---- errors it should find ------------------------------------------------------------------------------------------
case("a runtime error says its line", '''
PRINT "a"
DIM z(3)
z(5) = 1
''', ["a"], check=lambda r: isinstance(r, interp.BasicError) and r.line == 4 and "Subscript" in r.message)

case("overflow", '''
x% = 40000
''', None, check=lambda r: isinstance(r, interp.BasicError) and r.message == "Overflow")

case("a type mismatch is found before running", '''
a$ = 5
''', None, check=lambda r: isinstance(r, list) and r and "Type mismatch" in r[0].message)

case("a block left open is found before running", '''
FOR i = 1 TO 3
PRINT i
''', None, check=lambda r: isinstance(r, list) and r and "FOR without NEXT" in r[0].message)

# ---- the shapes of real programs --------------------------------------------------------------------------------------
case("array parameters and string functions", '''
DECLARE SUB Fill (a() AS INTEGER, n AS INTEGER)
DECLARE FUNCTION Pad$ (s$, n)
DIM SHARED grid(1 TO 3, 1 TO 3) AS INTEGER
DIM v(5) AS INTEGER
Fill v(), 5
FOR i = 0 TO 5: PRINT v(i);: NEXT: PRINT
grid(2, 2) = 9: Show
PRINT "["; Pad$("ab", 5); "]"
names$(1) = "Ann": names$(2) = "Bob"
PRINT names$(1) + " & " + names$(2)
SUB Fill (a() AS INTEGER, n AS INTEGER)
  FOR i = LBOUND(a) TO UBOUND(a): a(i) = i * n: NEXT
END SUB
SUB Show
  PRINT grid(2, 2)
END SUB
FUNCTION Pad$ (s$, n)
  Pad$ = s$ + SPACE$(n - LEN(s$))
END FUNCTION
''', [" 0  5  10  15  20  25", " 9", "[ab   ]", "Ann & Bob"])

case("a game loop reading INKEY$ (arrow keys too)", '''
RANDOMIZE TIMER
score = 0
DO
  k$ = INKEY$
  IF k$ = "a" THEN score = score + 1
  IF k$ = CHR$(0) + "H" THEN score = score + 10
  IF k$ = CHR$(27) THEN EXIT DO
LOOP
PRINT "Score:"; score
d = INT(RND * 6) + 1: IF d < 1 OR d > 6 THEN PRINT "bad dice"
''', ["Score: 12"], keys=["a", "a", "\x00H", "\x1b"])

case("animation on hidden pages, a 256-colour palette", '''
SCREEN 7, 0, 1, 0
FOR f = 1 TO 20
  CLS
  CIRCLE (f * 10, 100), 10, 14
  PCOPY 1, 0
NEXT
SCREEN 13
FOR c = 0 TO 255: LINE (c, 0)-(c, 199), c: NEXT
PALETTE 1, 63
PRINT "done"
''', None)

case("one-line IFs and ELSE chains", '''
x = 5
IF x > 3 THEN PRINT "a": PRINT "b" ELSE PRINT "c"
IF x < 3 THEN PRINT "no" ELSE IF x = 5 THEN PRINT "five" ELSE PRINT "other"
IF x THEN y = 1
PRINT y
IF x > 1 AND x < 10 OR x = 99 THEN PRINT "range"
''', ["a", "b", "five", " 1", "range"])

case("line numbers, nested loops and GOTO", '''
10 n = 0
20 n = n + 1
30 IF n < 5 THEN GOTO 20
40 PRINT n
FOR i = 1 TO 3
  FOR j = 1 TO 3
    IF i * j = 4 THEN PRINT i; j
  NEXT j
NEXT i
c = 0
again:
c = c + 1
IF c < 3 THEN GOTO again
PRINT c
''', [" 5", " 2  2", " 3"])

case("SELECT CASE with IS and ranges", '''
FOR score = 40 TO 100 STEP 30
SELECT CASE score
  CASE IS >= 90: g$ = "A"
  CASE 70 TO 89: g$ = "B"
  CASE ELSE: g$ = "F"
END SELECT
PRINT g$;
NEXT
PRINT
''', ["FBA"])

case("WHILE with string building", '''
s$ = ""
i = 1
WHILE i <= 5
  s$ = s$ + LTRIM$(STR$(i))
  i = i + 1
WEND
PRINT s$; LEN(s$)
PRINT UCASE$(LEFT$("hello", 1)) + MID$("hello", 2)
t$ = "a,b,c": cnt = 0
FOR i = 1 TO LEN(t$): IF MID$(t$, i, 1) = "," THEN cnt = cnt + 1
NEXT
PRINT cnt
''', ["12345 5", "Hello", " 2"])

case("TYPE arrays changed in a SUB", '''
TYPE Ball
  x AS SINGLE
  y AS SINGLE
  dx AS SINGLE
END TYPE
DIM SHARED balls(1 TO 3) AS Ball
FOR i = 1 TO 3: balls(i).x = i: balls(i).dx = .5: NEXT
MoveAll
PRINT balls(3).x
SUB MoveAll
  FOR i = 1 TO 3
    balls(i).x = balls(i).x + balls(i).dx
  NEXT
END SUB
''', [" 3.5"])

case("DEF SEG and PEEK are let through", '''
DEF SEG = 0
k = PEEK(1047)
DEF SEG
PRINT "ok"
''', ["ok"])

case("SLEEP and TIMER", '''
t = TIMER
SLEEP 1
PRINT TIMER - t >= .9
''', ["-1"])


def _run(src, keys=""):
    """(what run() returned - None when it ended normally, a BasicError, or the compile errors - , the text on
    screen with the empty lines at the end left off)"""
    prog = interp.compile_program(src)
    if prog.errors:
        return prog.errors, []
    scr = screen.Screen()
    vm = interp.Machine(prog, scr, screen.Sound(lambda: True), base_dir=str(support.scratch("qbasic")))
    vm.keys.extend(list(keys))
    result = vm.run()
    lines = list(scr.text_lines())
    while lines and not lines[-1]:
        lines.pop()
    return result, lines


def _make(name, src, keys, prints, check):
    def test():
        result, lines = _run(src, keys)
        if check is not None:
            assert check(result), f"it returned {result!r}"
        else:
            assert result is None, f"it stopped with {result!r}"
        if prints is not None:
            assert lines == prints, f"\n   it printed {lines}\n   not        {prints}"
    test.__doc__ = name
    return test


for _i, (_name, _src, _keys, _prints, _check) in enumerate(CASES):
    globals()[f"test_{_i:02d}"] = _make(_name, _src, _keys, _prints, _check)


def test_speed():
    """Fast enough for games: a 300,000-step loop in under 3 seconds"""
    t = time.perf_counter()
    result, lines = _run("FOR i = 1 TO 300000: x = x + i * 2: NEXT\nPRINT x\n")
    took = time.perf_counter() - t
    assert result is None and lines == [" 9.00003E+10"], lines
    assert took < 3, f"it took {took:.1f} s"


def test_examples():
    """Every built-in example compiles and runs for a moment without an error"""
    problems = []
    for name, src in examples.EXAMPLES.items():
        prog = interp.compile_program(src)
        if prog.errors:
            problems.append(f"{name}: {prog.errors[0]}")
            continue
        vm = interp.Machine(prog, screen.Screen(), screen.Sound(lambda: True), base_dir=str(support.scratch("qbasic")))
        vm.keys.extend(list("5\r50\r25\r"))               # (an answer or two for the ones that ask)
        out = {}
        t = threading.Thread(target=lambda: out.setdefault("r", vm.run()), daemon=True)
        t.start()
        t.join(1.5)
        vm.stop()
        t.join(3)
        if t.is_alive():
            problems.append(f"{name}: didn't stop when asked")
        elif isinstance(out.get("r"), interp.BasicError):
            problems.append(f"{name}: {out['r'].message} (line {out['r'].line})")
    assert not problems, "\n".join(problems)


if __name__ == "__main__":
    support.main(globals())
