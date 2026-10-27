"""The QBasic reference behind F1: each keyword's form, what it does, and a short example."""

REF = {
    "PRINT": ("PRINT [items] [; | ,]", "Shows numbers and text. ; keeps going on the same spot, , jumps to the next "
              "14-column zone, and ending with either stays on the line. Numbers get a space in front (for the sign) "
              "and one after. ? is short for PRINT.", 'PRINT "Score:"; score, "Lives:"; lives'),
    "PRINT USING": ('PRINT USING format$; items', "Formatted numbers and text: # a digit, . the point, , thousands, "
                    "$$ a dollar sign, ** star fill, + and - signs, ^^^^ exponent; ! the first letter, & the whole "
                    "string, \\  \\ a fixed width.", 'PRINT USING "$$#,###.##"; total'),
    "INPUT": ('INPUT ["prompt"{; | ,}] var[, var...]', "Waits for the user to type and press Enter. ; after the "
              "prompt adds a question mark, , doesn't. Wrong kind of answer: \"Redo from start\".",
              'INPUT "What is your name"; name$'),
    "LINE INPUT": ('LINE INPUT ["prompt";] var$', "Reads a whole line of text, commas and all.",
                   'LINE INPUT "Message: "; msg$'),
    "INKEY$": ("k$ = INKEY$", "The key being pressed right now, or \"\" if none - it doesn't wait. Arrow keys come as "
               "CHR$(0) + \"H\" (up), \"P\" (down), \"K\" (left), \"M\" (right); Esc is CHR$(27), Enter CHR$(13).",
               'DO: k$ = INKEY$: LOOP UNTIL k$ <> ""'),
    "CLS": ("CLS", "Clears the screen and puts the cursor at the top left.", "CLS"),
    "LOCATE": ("LOCATE [row] [, column]", "Moves the text cursor (rows 1-25, columns 1-80 in SCREEN 0).",
               'LOCATE 12, 35: PRINT "Hello"'),
    "COLOR": ("COLOR [foreground] [, background]", "Text colours: 0 black, 1 blue, 2 green, 3 cyan, 4 red, 5 magenta, "
              "6 brown, 7 white, 8-15 the bright ones. In graphics modes it sets the drawing colour.",
              "COLOR 14, 1"),
    "SCREEN": ("SCREEN mode [, , apage, vpage]", "Picks the screen: 0 text 80x25, 1 320x200 4 colours, 2 640x200 2 "
               "colours, 7 320x200 16 colours (8 pages), 8 640x200, 9 640x350, 12 640x480 16 colours, 13 320x200 256 "
               "colours. apage is the page drawn on, vpage the one shown - draw on one and PCOPY it for smooth "
               "animation.", "SCREEN 13"),
    "PCOPY": ("PCOPY from, to", "Copies one screen page onto another (smooth animation in SCREEN 7, 8 and 9).",
              "SCREEN 7, 0, 1, 0: ... : PCOPY 1, 0"),
    "PSET": ("PSET [STEP](x, y) [, colour]", "Sets one pixel. STEP makes x and y relative to the last point.",
             "PSET (160, 100), 15"),
    "PRESET": ("PRESET [STEP](x, y) [, colour]", "Like PSET, but the background colour when none is given.",
               "PRESET (10, 10)"),
    "LINE": ("LINE [(x1, y1)]-(x2, y2) [, colour] [, B | BF] [, style]", "A line, or a box (B) or a filled box (BF).",
             "LINE (10, 10)-(100, 50), 4, BF"),
    "CIRCLE": ("CIRCLE (x, y), radius [, colour [, start, end [, aspect]]]", "A circle, an arc (angles in radians) "
               "or an ellipse (aspect).", "CIRCLE (160, 100), 40, 14"),
    "PAINT": ("PAINT (x, y) [, colour [, border]]", "Fills the area around (x, y) up to the border colour.",
              "PAINT (160, 100), 2, 14"),
    "DRAW": ('DRAW commands$', "A little drawing language: U D L R E F G H n to move and draw, M x,y to go to a point, "
             "B to move without drawing, N to come back, C colour, S scale, A angle, TA turn.",
             'DRAW "C14 R20 D20 L20 U20"'),
    "POINT": ("POINT(x, y)", "The colour of a pixel.", "c = POINT(10, 10)"),
    "GET": ("GET (x1, y1)-(x2, y2), array", "Copies part of the screen into an array - a sprite.",
            "DIM ship(200): GET (0, 0)-(15, 15), ship"),
    "PUT": ("PUT (x, y), array [, PSET | PRESET | XOR | OR | AND]", "Draws a sprite saved with GET. XOR (the default) "
            "draws it, and drawing it again in the same place takes it off.", "PUT (x, y), ship, PSET"),
    "PALETTE": ("PALETTE attribute, colour", "Changes what colour a number shows as. In SCREEN 13 colour is "
                "red + 256 * green + 65536 * blue, each 0-63.", "PALETTE 1, 63"),
    "IF": ("IF condition THEN ... [ELSEIF ... THEN ...] [ELSE ...] END IF", "Does things only when the condition is "
           "true. On one line: IF x > 5 THEN PRINT \"big\" ELSE PRINT \"small\".",
           'IF score > high THEN\n    high = score\nEND IF'),
    "SELECT CASE": ("SELECT CASE value / CASE ... / CASE ELSE / END SELECT", "Picks a block by value: CASE 1, 2 "
                    "(either), CASE 3 TO 9 (a range), CASE IS > 100 (a comparison).",
                    'SELECT CASE k$\n    CASE "a": x = x - 1\n    CASE "d": x = x + 1\nEND SELECT'),
    "FOR": ("FOR var = start TO end [STEP step] ... NEXT [var]", "Repeats with a counter. EXIT FOR leaves early.",
            "FOR i = 1 TO 10\n    PRINT i\nNEXT i"),
    "DO": ("DO [WHILE | UNTIL condition] ... LOOP [WHILE | UNTIL condition]", "Repeats while (or until) something is "
           "true - the test can go at the top or the bottom. EXIT DO leaves early. DO ... LOOP alone repeats forever.",
           'DO\n    k$ = INKEY$\nLOOP UNTIL k$ = CHR$(27)'),
    "WHILE": ("WHILE condition ... WEND", "Repeats while the condition is true.", "WHILE n < 10: n = n + 1: WEND"),
    "GOTO": ("GOTO label", "Jumps to a label (name:) or line number.", "GOTO again"),
    "GOSUB": ("GOSUB label ... RETURN", "Jumps to a label and comes back at RETURN.", "GOSUB DrawBoard"),
    "ON": ("ON n GOTO label1, label2 ... / ON ERROR GOTO label", "Jumps to the nth label - or, with ERROR, where to "
           "go when something goes wrong (RESUME NEXT carries on after the line that failed; ERR is its number).",
           "ON ERROR GOTO Oops"),
    "SUB": ("SUB name [(parameters)] ... END SUB", "A named piece of program you call by name (or with CALL). "
            "Variables passed in are changed if the SUB changes them. Its own variables are its own - DIM SHARED "
            "in the main program shares one.", "SUB Greet (who$)\n    PRINT \"Hi, \"; who$\nEND SUB"),
    "FUNCTION": ("FUNCTION name[type] [(parameters)] ... END FUNCTION", "Like a SUB, but it gives back a value: "
                 "assign the answer to the FUNCTION's own name.",
                 "FUNCTION Square (n)\n    Square = n * n\nEND FUNCTION"),
    "CALL": ("CALL name [(arguments)]", "Runs a SUB (you can also just write its name and the arguments).",
             "CALL Greet(\"Ann\")"),
    "DIM": ("DIM [SHARED] name[(bounds)] [AS type]", "Makes a variable or an array: DIM a(10) has 0-10, "
            "DIM b(1 TO 5, 1 TO 5) a grid. Types: INTEGER, LONG, SINGLE, DOUBLE, STRING, STRING * n, or a TYPE.",
            "DIM SHARED board(1 TO 8, 1 TO 8) AS INTEGER"),
    "REDIM": ("REDIM [PRESERVE] name(bounds)", "Makes an array again at a new size (PRESERVE keeps what's in it).",
              "REDIM items(count)"),
    "CONST": ("CONST name = value", "A value that never changes.", "CONST SPEED = 2"),
    "TYPE": ("TYPE name ... field AS type ... END TYPE", "A record with named fields (use them with a dot).",
             "TYPE Player\n    x AS INTEGER\n    y AS INTEGER\nEND TYPE\nDIM p AS Player: p.x = 10"),
    "DATA": ("DATA value, value ...", "Values kept in the program, read in order by READ.", "DATA 10, 20, \"cat\""),
    "READ": ("READ var[, var...]", "Takes the next DATA values.", "READ a, b, name$"),
    "RESTORE": ("RESTORE [label]", "Starts READ over (from a label's DATA).", "RESTORE Levels"),
    "SWAP": ("SWAP a, b", "Swaps two variables.", "SWAP a(i), a(j)"),
    "RANDOMIZE": ("RANDOMIZE [seed]", "Starts a new run of random numbers - RANDOMIZE TIMER for a different one each "
                  "time.", "RANDOMIZE TIMER"),
    "RND": ("RND", "A random number from 0 up to (not including) 1. INT(RND * 6) + 1 is a dice roll.",
            "dice = INT(RND * 6) + 1"),
    "SLEEP": ("SLEEP [seconds]", "Waits that many seconds, or until a key is pressed (no number: just the key).",
              "SLEEP 2"),
    "TIMER": ("TIMER", "Seconds since midnight (with fractions): for timing and smooth animation.",
              "t = TIMER: DO: LOOP UNTIL TIMER - t > .05"),
    "BEEP": ("BEEP", "A beep.", "BEEP"),
    "SOUND": ("SOUND frequency, duration", "A tone: frequency in hertz, duration in clock ticks (18.2 a second).",
              "SOUND 440, 9"),
    "PLAY": ('PLAY music$', "Music: notes A-G (# or + sharp, - flat), O octave, < and > octave down and up, L length "
             "(4 a quarter note), T tempo, P pause, MB plays it in the background.", 'PLAY "T160 O3 L8 CDEFGAB>C"'),
    "END": ("END", "Ends the program (END IF, END SUB ... end blocks).", "END"),
    "OPEN": ('OPEN file$ FOR INPUT | OUTPUT | APPEND AS #n', "Opens a file (next to the program) to read or write "
             "with INPUT #n, LINE INPUT #n, PRINT #n and WRITE #n; EOF(n) says when it's done; CLOSE when finished.",
             'OPEN "scores.txt" FOR APPEND AS #1\nPRINT #1, name$; score\nCLOSE #1'),
    "CLOSE": ("CLOSE [#n]", "Closes a file (or all of them).", "CLOSE #1"),
    "EOF": ("EOF(n)", "True (-1) at the end of a file being read.", "DO UNTIL EOF(1): LINE INPUT #1, a$: LOOP"),
    "WRITE": ("WRITE [#n,] items", "Like PRINT, with commas between and strings in quotes - easy to read back with "
              "INPUT #.", 'WRITE #1, name$, score'),
    "LEN": ("LEN(s$)", "How many characters a string has.", "n = LEN(name$)"),
    "LEFT$": ("LEFT$(s$, n)", "The first n characters.", 'LEFT$("Hello", 2) = "He"'),
    "RIGHT$": ("RIGHT$(s$, n)", "The last n characters.", 'RIGHT$("Hello", 3) = "llo"'),
    "MID$": ("MID$(s$, start [, length])", "Characters from the middle. As a statement it replaces them: "
             "MID$(a$, 1, 1) = \"J\".", 'MID$("Hello", 2, 3) = "ell"'),
    "INSTR": ("INSTR([start,] s$, find$)", "Where find$ is in s$ (0 if it isn't).", 'INSTR("banana", "an") = 2'),
    "UCASE$": ("UCASE$(s$)", "Capitals.", 'UCASE$("abc") = "ABC"'),
    "LCASE$": ("LCASE$(s$)", "Small letters.", 'LCASE$("ABC") = "abc"'),
    "LTRIM$": ("LTRIM$(s$)", "Without spaces at the start (STR$ puts one before positive numbers).",
               "LTRIM$(STR$(5))"),
    "RTRIM$": ("RTRIM$(s$)", "Without spaces at the end.", "RTRIM$(name$)"),
    "STR$": ("STR$(n)", "A number as text (with a space in front if it isn't negative).", 'STR$(42) = " 42"'),
    "VAL": ("VAL(s$)", "The number at the start of some text.", 'VAL("3.5 apples") = 3.5'),
    "CHR$": ("CHR$(code)", "The character with that code (0-255): CHR$(219) is a solid block, 1 and 2 smiley faces.",
             "PRINT CHR$(1)"),
    "ASC": ("ASC(s$)", "The code of the first character.", 'ASC("A") = 65'),
    "STRING$": ("STRING$(n, c$)", "A character repeated n times.", 'PRINT STRING$(40, "-")'),
    "SPACE$": ("SPACE$(n)", "n spaces.", "PRINT SPACE$(10); \"x\""),
    "INT": ("INT(n)", "The whole number at or below n.", "INT(3.7) = 3, INT(-3.2) = -4"),
    "FIX": ("FIX(n)", "n with the fraction cut off.", "FIX(-3.7) = -3"),
    "ABS": ("ABS(n)", "n without its sign.", "ABS(-5) = 5"),
    "SQR": ("SQR(n)", "The square root.", "SQR(16) = 4"),
    "SIN": ("SIN(angle)", "Sine (angles in radians: degrees * 3.14159 / 180).", "y = SIN(a) * 50"),
    "COS": ("COS(angle)", "Cosine (radians).", "x = COS(a) * 50"),
    "ATN": ("ATN(n)", "Arctangent, in radians (4 * ATN(1) is pi).", "pi = 4 * ATN(1)"),
    "MOD": ("a MOD b", "The remainder of a division.", "IF n MOD 2 = 0 THEN PRINT \"even\""),
    "CSRLIN": ("CSRLIN", "The text cursor's row.", "r = CSRLIN"),
    "POS": ("POS(0)", "The text cursor's column.", "c = POS(0)"),
    "TAB": ("PRINT TAB(column)", "Moves along to a column in a PRINT.", 'PRINT "Name"; TAB(20); "Score"'),
    "SPC": ("PRINT SPC(n)", "n spaces in a PRINT.", 'PRINT "A"; SPC(5); "B"'),
    "LBOUND": ("LBOUND(array [, dimension])", "An array's lowest index.", "FOR i = LBOUND(a) TO UBOUND(a)"),
    "UBOUND": ("UBOUND(array [, dimension])", "An array's highest index.", "n = UBOUND(names$)"),
    "VIEW PRINT": ("VIEW PRINT top TO bottom", "Text scrolls only between those rows (a status line stays put).",
                   "VIEW PRINT 2 TO 24"),
    "WINDOW": ("WINDOW [SCREEN] (x1, y1)-(x2, y2)", "Your own coordinates for the graphics statements (y goes up "
               "unless SCREEN).", "WINDOW (-10, -10)-(10, 10)"),
    "WAIT": ("WAIT &H3DA, 8", "Waits for the screen's next refresh - the old trick for smooth animation.",
             "WAIT &H3DA, 8"),
    "EXIT": ("EXIT FOR | DO | SUB | FUNCTION", "Leaves a loop, SUB or FUNCTION early.", "IF done THEN EXIT DO"),
    "REM": ("REM comment / ' comment", "A note for people reading the program; QBasic skips it.",
            "' Draw the board"),
    "DECLARE": ("DECLARE SUB name (params)", "Tells QBasic about a SUB or FUNCTION before it's used (optional here).",
                "DECLARE SUB Greet (who$)"),
    "SHARED": ("SHARED var[, var...]", "Inside a SUB: use these main-program variables.", "SHARED score, lives"),
    "STATIC": ("STATIC var / SUB name STATIC", "Keeps a SUB's variables between calls.", "STATIC count"),
}


def lookup(word):
    """The entry for a word (MID$, LINE INPUT, END IF ... all find their page), or None."""
    w = (word or "").strip().upper()
    if not w:
        return None
    for key in (w, w.split()[0] if " " in w else w):
        if key in REF:
            return key, REF[key]
    aliases = {"ELSE": "IF", "ELSEIF": "IF", "THEN": "IF", "CASE": "SELECT CASE", "SELECT": "SELECT CASE",
               "NEXT": "FOR", "STEP": "FOR", "TO": "FOR", "LOOP": "DO", "UNTIL": "DO", "WEND": "WHILE",
               "RETURN": "GOSUB", "USING": "PRINT USING", "ERROR": "ON", "RESUME": "ON", "ERR": "ON", "LET": "DIM",
               "AS": "DIM", "INTEGER": "DIM", "STRING": "DIM", "SINGLE": "DIM", "DOUBLE": "DIM", "LONG": "DIM",
               "VIEW": "VIEW PRINT", "?": "PRINT", "TAN": "SIN", "EXP": "SQR", "LOG": "SQR", "SGN": "ABS",
               "CINT": "INT", "CLNG": "INT", "HEX$": "STR$", "OCT$": "STR$", "DATE$": "TIMER", "TIME$": "TIMER",
               "OUTPUT": "OPEN", "APPEND": "OPEN", "SYSTEM": "END", "STOP": "END", "XOR": "MOD", "AND": "MOD",
               "OR": "MOD", "NOT": "MOD"}
    if w in aliases:
        return aliases[w], REF[aliases[w]]
    return None


def html(word):
    hit = lookup(word)
    if hit is None:
        return None
    key, (form, text, example) = hit
    from html import escape
    return (f"<h3 style='margin:2px 0'>{escape(key)}</h3><p style='font-family:Consolas'><b>{escape(form)}</b></p>"
            f"<p>{escape(text)}</p><p style='color:#555'>Example:</p>"
            f"<pre style='background:#0000AA;color:#FFFFFF;padding:6px'>{escape(example)}</pre>")


def index_html():
    from html import escape
    items = " &middot; ".join(f"<a href='help:{escape(k)}'>{escape(k)}</a>" for k in sorted(REF))
    return ("<h3 style='margin:2px 0'>QBasic reference</h3><p>Put the cursor on a keyword and press <b>F1</b>, or pick "
            f"one:</p><p>{items}</p>")
