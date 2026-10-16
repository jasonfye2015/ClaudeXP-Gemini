# Messenger contact search: Windows verification

## Status

Native Windows verification is **not yet performed**. Linux offscreen input
tests do not establish Windows clear-button appearance or display readability.
No local AI server is needed for these search checks.

The user accepted proceeding on the assumption that the Windows interaction
works, with issues to be discovered during use of the finished product.
Windows testing is therefore deferred, not a completion blocker and not a
claimed pass. Messenger now offers Normal, Large and Extra large contact text
sizes for the search field, result count and contact list. The choice applies
to the current Messenger window; it does not change chats or system scaling.

Preliminary checks in the Linux workspace passed: the new input tests together
with `test_messaging` (42 tests), plus the four input tests at the default scale
and in separate processes with `QT_SCALE_FACTOR` values 1.25, 1.5 and 2.
These used Qt's offscreen platform and Fusion style, not Windows.

## Automated input checks on Windows

Run `win7_2011\setup_windows.bat` first. From the repository root, in PowerShell:

```powershell
$env:QT_QPA_PLATFORM = "windows"
Remove-Item Env:QT_SCALE_FACTOR -ErrorAction SilentlyContinue
py -3.13 -m unittest win7_2011.tests.test_messenger_search_ui -v
```

Run this module alone: other test modules default to the offscreen platform.
It applies the simulator's stylesheet, types with Qt keyboard events, tabs to
the contact list, uses Home/Down/Up, and clicks the built-in clear control with
Qt mouse events (not `clear()` or a direct button signal). Histories are isolated
in a temporary directory; existing user chats are not modified.

Repeat at Windows Settings → System → Display → Scale values of **100%, 125%,
150%, and 200%**, restarting the test process each time. Record Windows version,
display resolution, scale, Qt platform/style printed by the test, and results.
Qt scale overrides are useful preliminary checks, but are not a substitute for
actual Windows display scaling.

## Manual appearance and physical-input checks

At each scale, launch the simulator using `win7_2011\run_windows.bat`, sign in,
and open Messenger. Use a disposable test profile, not important chats.

1. Confirm the empty search field, placeholder and contact list are readable,
   with no clipped text or overlap. Check the normal window size and after
   resizing it narrower.
2. Type `alex` with the keyboard. Confirm only matching display/online names
   remain; Tab into the list, then press Down and Up. Confirm the heading and
   conversation change to the highlighted contact.
3. Select a matching contact with existing history. Note the selected name and
   transcript. Click the native clear icon at the right of the search field.
   Confirm the text clears, all **200 contacts** return, and the same contact and
   transcript remain selected. Confirm the clear icon is visible and easy to
   click, without overlapping the query.
4. Search a complete online name as well as a display name. Confirm both match.
5. Type a nonexistent name; confirm “No matching contacts” and no selected
   contact. Click clear; confirm the full roster returns and saved chats remain
   unchanged. This case has no selected conversation to preserve.
6. Try each Contact text size option. Confirm the search text, result count and
   contact list resize without losing the search query or selected conversation.
   Confirm the clear icon still fits and works, and Normal restores the default.

Record evidence below before treating the Windows task as verified:

| Windows version / resolution | Scale | Automated result | Physical input / readability | Evidence |
| --- | --- | --- | --- | --- |
| Not run | 100% | Pending | Pending | — |
| Not run | 125% | Pending | Pending | — |
| Not run | 150% | Pending | Pending | — |
| Not run | 200% | Pending | Pending | — |
