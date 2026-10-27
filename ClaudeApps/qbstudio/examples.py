"""Example programs for Help > Examples (and starting points to vibe from)."""

EXAMPLES = {
    "Hello, World": '''' Hello, World - the first program everyone writes.
CLS
COLOR 14
PRINT "Hello, World!"
COLOR 7
INPUT "What is your name"; name$
PRINT "Nice to meet you, "; name$; "!"
''',
    "Guess the Number": '''' Guess the Number: the computer thinks of a number from 1 to 100.
RANDOMIZE TIMER
CLS
secret = INT(RND * 100) + 1
tries = 0
PRINT "I'm thinking of a number from 1 to 100."
DO
    INPUT "Your guess"; guess
    tries = tries + 1
    IF guess < secret THEN
        PRINT "Higher!"
    ELSEIF guess > secret THEN
        PRINT "Lower!"
    END IF
LOOP UNTIL guess = secret
COLOR 10
PRINT "You got it in"; tries; "tries!"
COLOR 7
''',
    "Rainbow Circles (SCREEN 12)": '''' Rainbow circles: SCREEN 12 is 640 x 480 with 16 colours.
SCREEN 12
FOR r = 10 TO 230 STEP 6
    CIRCLE (320, 240), r, (r \\ 6) MOD 15 + 1
NEXT
LINE (0, 0)-(639, 479), 15, B
COLOR 15
LOCATE 29, 30: PRINT "Press any key";
SLEEP
''',
    "Starfield (SCREEN 13)": '''' A starfield flying past - SCREEN 13 has 256 colours. Press any key to stop.
SCREEN 13
CONST STARS = 120
DIM x(STARS), y(STARS), z(STARS)
RANDOMIZE TIMER
FOR i = 1 TO STARS
    x(i) = RND * 320 - 160: y(i) = RND * 200 - 100: z(i) = RND * 100 + 1
NEXT
DO
    FOR i = 1 TO STARS
        sx = 160 + x(i) * 64 / z(i): sy = 100 + y(i) * 64 / z(i)
        PSET (sx, sy), 0
        z(i) = z(i) - 1
        IF z(i) < 1 THEN z(i) = 100: x(i) = RND * 320 - 160: y(i) = RND * 200 - 100
        sx = 160 + x(i) * 64 / z(i): sy = 100 + y(i) * 64 / z(i)
        PSET (sx, sy), 31 - z(i) \\ 7
    NEXT
    WAIT &H3DA, 8
LOOP WHILE INKEY$ = ""
''',
    "Bouncing Ball (smooth, SCREEN 7)": '''' A bouncing ball drawn on a hidden page and copied to the screen (no flicker).
SCREEN 7, 0, 1, 0
x = 160: y = 100: dx = 2: dy = 1.5
DO
    CLS
    LINE (0, 0)-(319, 199), 9, B
    CIRCLE (x, y), 10, 14
    PAINT (x, y), 12, 14
    PCOPY 1, 0
    x = x + dx: y = y + dy
    IF x < 11 OR x > 308 THEN dx = -dx: SOUND 600, .5
    IF y < 11 OR y > 188 THEN dy = -dy: SOUND 400, .5
    WAIT &H3DA, 8
LOOP WHILE INKEY$ = ""
''',
    "Snake": '''' Snake: arrow keys to steer, eat the stars, don't hit the walls or yourself. Esc quits.
DEFINT A-Z
DIM sx(1000), sy(1000)
RANDOMIZE TIMER
CLS
COLOR 9
FOR c = 1 TO 80: LOCATE 2, c: PRINT CHR$(205);: LOCATE 24, c: PRINT CHR$(205);: NEXT
FOR r = 2 TO 24: LOCATE r, 1: PRINT CHR$(186);: LOCATE r, 80: PRINT CHR$(186);: NEXT
LOCATE 2, 1: PRINT CHR$(201);: LOCATE 2, 80: PRINT CHR$(187);
LOCATE 24, 1: PRINT CHR$(200);: LOCATE 24, 80: PRINT CHR$(188);
length = 4: dx = 1: dy = 0: score = 0
FOR i = 1 TO length: sx(i) = 40 - i: sy(i) = 12: NEXT
GOSUB NewFood
DO
    k$ = INKEY$
    SELECT CASE k$
        CASE CHR$(0) + "H": IF dy = 0 THEN dx = 0: dy = -1
        CASE CHR$(0) + "P": IF dy = 0 THEN dx = 0: dy = 1
        CASE CHR$(0) + "K": IF dx = 0 THEN dx = -1: dy = 0
        CASE CHR$(0) + "M": IF dx = 0 THEN dx = 1: dy = 0
        CASE CHR$(27): EXIT DO
    END SELECT
    nx = sx(1) + dx: ny = sy(1) + dy
    IF nx < 2 OR nx > 79 OR ny < 3 OR ny > 23 THEN EXIT DO
    FOR i = 2 TO length
        IF sx(i) = nx AND sy(i) = ny THEN dead = 1
    NEXT
    IF dead THEN EXIT DO
    LOCATE sy(length), sx(length): PRINT " ";
    FOR i = length TO 2 STEP -1: sx(i) = sx(i - 1): sy(i) = sy(i - 1): NEXT
    sx(1) = nx: sy(1) = ny
    IF nx = fx AND ny = fy THEN
        score = score + 10: length = length + 1: sx(length) = sx(length - 1): sy(length) = sy(length - 1)
        SOUND 900, 1
        GOSUB NewFood
    END IF
    COLOR 10: LOCATE ny, nx: PRINT CHR$(219);
    COLOR 14: LOCATE 1, 2: PRINT "SCORE:"; score;
    t! = TIMER: DO: LOOP UNTIL TIMER - t! >= .08 OR TIMER < t!
LOOP
COLOR 12: LOCATE 12, 33: PRINT " GAME  OVER "
COLOR 7: LOCATE 14, 30: PRINT "Final score:"; score
END

NewFood:
DO
    fx = INT(RND * 77) + 2: fy = INT(RND * 20) + 3
    ok = 1
    FOR i = 1 TO length: IF sx(i) = fx AND sy(i) = fy THEN ok = 0
    NEXT
LOOP UNTIL ok
COLOR 14: LOCATE fy, fx: PRINT "*";
RETURN
''',
    "Music Box": '''' PLAY's music language: notes, octaves, lengths and tempo.
CLS
PRINT "Playing Ode to Joy..."
PLAY "T120 O3 L4 EEFG GFED CCDE E.D8D2"
PLAY "EEFG GFED CCDE D.C8C2"
PRINT "Now a scale, faster..."
PLAY "T200 L8 O3 CDEFGAB>C<BAGFEDC"
PRINT "Done!"
''',
    "Times Table Quiz": '''' A times-table quiz with SUBs and FUNCTIONs.
DECLARE FUNCTION Ask% (a%, b%)
RANDOMIZE TIMER
CLS
score% = 0
FOR q% = 1 TO 5
    a% = INT(RND * 9) + 2: b% = INT(RND * 9) + 2
    IF Ask%(a%, b%) THEN score% = score% + 1
NEXT
PRINT
PRINT "You scored"; score%; "out of 5."
SELECT CASE score%
    CASE 5: PRINT "Perfect!"
    CASE 3 TO 4: PRINT "Well done."
    CASE ELSE: PRINT "Keep practising."
END SELECT

FUNCTION Ask% (a%, b%)
    PRINT a%; "x"; b%; "=";
    INPUT answer%
    IF answer% = a% * b% THEN
        COLOR 10: PRINT "Right!": COLOR 7
        Ask% = -1
    ELSE
        COLOR 12: PRINT "No, it's"; a% * b%: COLOR 7
        Ask% = 0
    END IF
END FUNCTION
''',
    "Clock": '''' A clock face with moving hands. Press any key to stop.
SCREEN 12
CONST PI = 3.14159265#
DO
    t$ = TIME$
    h = VAL(LEFT$(t$, 2)) MOD 12: m = VAL(MID$(t$, 4, 2)): s = VAL(RIGHT$(t$, 2))
    IF t$ <> last$ THEN
        CLS
        CIRCLE (320, 240), 200, 15
        FOR i = 0 TO 11
            a = i * PI / 6
            LINE (320 + SIN(a) * 185, 240 - COS(a) * 185)-(320 + SIN(a) * 200, 240 - COS(a) * 200), 15
        NEXT
        a = (h + m / 60) * PI / 6: LINE (320, 240)-(320 + SIN(a) * 110, 240 - COS(a) * 110), 14
        a = (m + s / 60) * PI / 30: LINE (320, 240)-(320 + SIN(a) * 160, 240 - COS(a) * 160), 11
        a = s * PI / 30: LINE (320, 240)-(320 + SIN(a) * 175, 240 - COS(a) * 175), 12
        LOCATE 2, 36: PRINT t$
        last$ = t$
    END IF
LOOP WHILE INKEY$ = ""
''',
}
