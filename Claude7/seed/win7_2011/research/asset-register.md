# Boot and branding reference register

This register separates sourced period facts from visual elements recreated for
the simulator. The machine profile is a representative 2011 custom desktop, not
a claim that every Windows 7 PC used this exact board.

| Element | Reference and verified fact | Simulator treatment | Confidence |
| --- | --- | --- | --- |
| Motherboard and firmware | [ASUS P8P67 Deluxe support page](https://www.asus.com/us/supportonly/p8p67%20deluxe/helpdesk_bios/) lists BIOS 1204 dated 2011-01-27. The [January 2011 P8P67 Deluxe manual](https://theretroweb.com/motherboard/manual/e6306-p8p67-deluxe-6868132e79eab995326350.pdf) describes the board as using an EFI AMI BIOS. | Identify ASUS as the board maker and American Megatrends as the firmware vendor. Do not present this ASUS board as an AMI-branded motherboard. The boot screen uses a text POST treatment; it is not a pixel-perfect capture of the board's UEFI interface. | High for board/firmware facts; medium for the representative POST look. |
| Firmware date/version | ASUS lists BIOS 1204 as released 2011-01-27. The manual identifies a January 2011 board/firmware generation. | Use BIOS 1204 and the P8P67 Deluxe identity in the reference POST. | High. |
| POST-screen layout and logos | User-supplied AMI POST example, American Megatrends logo, ENERGY STAR logo, and README. The README places AMI at upper left, ENERGY STAR at upper right, and specifies a black background with white text. | Recreate the supplied 640×480 composition, using the individual logos and the example for positioning; the example screenshot itself is not shown. | User-provided reference and assets. |
| Local AI branding during POST | User-supplied Gemma 4 logo (542×132) and Gemini star (53×56). | Show the small Gemini star beside the Gemma 4 wordmark in the lower-right of the POST screen, above the footer. These are model/provider marks, not BIOS vendor or motherboard branding. | User-provided assets and direction. |
| POST sound and memory check | User-supplied `Boot_sounds.mp3`; its README says to start playback immediately and places the POST beep five seconds into the clip. | Preserve the full MP3 and create a 6.5-second PCM WAV boot excerpt for Windows playback. Show the memory-test result at five seconds and leave the BIOS screen visible for about 6.7 seconds. | User-provided source; WAV is an excerpt and format conversion. |
| Windows 7 startup animation | [Softpedia's December 2008 Windows 7 boot-screen report](https://news.softpedia.com/news/Feast-Your-Eyes-on-the-New-Windows-7-Boot-Screen-99244.shtml) describes the four colored spheres forming the Windows mark in Windows 7 development builds. The user also supplied 105 200×200 BMP frames dated 2010-08-31 with sequencing instructions. | Play frames 000–104 at 20 fps, then repeat three cycles of frames 103–060 and 061–104. Space skips to login. Render bold “Starting Windows” text and the gray Microsoft copyright line over black. | High for the supplied sequence; historical article is supporting context. |
| Windows startup sound | User-supplied `windows-7-startup.mp3` in the same asset bundle. | Preserve the MP3 and bundle a PCM WAV conversion for one-shot playback through Windows' built-in `winsound` when the desktop appears. | User-provided source; WAV is a format conversion only. |
| Windows 7 user login screen | User-supplied `Logon_Template.png`, Kithylin profile icon, Switch User and power-button images, hover variants for power-menu actions, and restart wallpaper. The README specifies the passwordless behavior and power actions. | Scale the template background to the display and overlay the account name, profile image, blank-or-arbitrary password field, and supplied image buttons. Restart briefly shows its supplied wallpaper, Sleep blanks the display until input, and Shut Down uses the existing shutdown path. | User-provided images and interaction directions. |
| Windows 7 user selection screen | User-supplied 1920×1200 background, six named profile icons, normal/highlight icon frames, power-menu artwork, and hover/selection WAV sounds. | First-run setup starts with the six tentative profiles prefilled; the ages are ages reached in 2011 and birth years are derived accordingly. Setup can revise them before saving. The selection screen switches only among saved profiles; editing identities later requires format-and-reinstall. | User-provided images/audio and interaction directions. |
| Windows shutdown | User-supplied shutdown wallpaper, “It's now safe to turn off your computer” image, and PCM WAV sound with README timing and button directions. | Show the wallpaper and “Shutting down...” first; after three seconds show the safe-to-power-off image and Restart, End Program, and Recovery Mode buttons. Recovery Mode confirms before clearing account/profile/document data. | User-provided images and audio. |
| Windows 7 desktop | [Microsoft Press, *Windows 7 Step by Step*](https://download.microsoft.com/download/9/a/3/9a36304d-cb64-427e-a184-4ed1bb556712/win7_sbs_earlycontent_ch1.pdf) documents the desktop, Start menu, taskbar, notification area, and session shutdown flow. | Recreate the shell layout and interaction pattern with Qt widgets and locally drawn artwork. | High for shell layout; medium for visual details. |
| Desktop shortcuts and drive browser | User-supplied `Desktop.zip`, including the README and icons for Recycle Bin, the Desktop/Computer view, Firefox, CD/DVD/floppy/external/internal drives. | Keep the welcome note at upper-right; display the six requested shortcuts in a left-side column; use the supplied drive artwork in the Computer/Explorer window. Firefox shows the exact requested not-yet-implemented message. The Recycle Bin uses the supplied empty/full artwork and supports safe restore/delete actions for eligible personal files. | User-provided assets and interaction directions. |
| Desktop wallpaper | User-provided Windows 7 wallpaper image, 1920×1200. | Bundled as the desktop's wallpaper and center-cropped with aspect-ratio preservation to fit the active display. | User-provided; treated as the intended authentic image. |
| Start menu, taskbar, and default background | User-supplied `Windows_Menu` ZIP: `Background1.jpg`, bar/menu/task/tray templates, Start A/B images, eight menu ICOs, four WAV sounds, and README. | Retained in `assets/start-menu`; rendered at native menu/taskbar sizes with the supplied wallpaper scaled to the display. The new background supersedes the previous wallpaper as the default. | User-provided assets and interaction directions; private simulator use. |
| Desktop screenshot reference | User-provided 800×450 Windows 7 desktop screenshot archived at `references/windows7_build7100_desktop_reference.jpg`; its visible watermark identifies Evaluation Copy, Build 7100, with a 2009 date. | Used as a visual reference for the shell layout only; the screenshot itself is not displayed in the application. | Useful for the Windows 7 look, but it depicts a prerelease build rather than a 2011 retail installation. |

The original frame archive is compressed in `../assets/boot/windows7_boot_frames.zip`
to keep the app asset size modest; its accompanying README preserves the user's
animation timing directions.

## MushClient / PawPrints MUCK

The user supplied `Mush_1791833264999.zip` with the Mush icon and artwork,
a MUSHClient screenshot, a PawPrints room map, `regulars.json`, and 120 background
character profile files. These are preserved under `assets/mush`; the screenshot
is a visual reference rather than a runtime window background. The client uses
the supplied icon in its window, taskbar button, and notification-area button.
The classic menu/toolbar/gray-terminal layout follows the screenshot. PawPrints
is a fictional local MUCK, not a connection to a real service.

## mIRC / FurNet IRC

The user supplied `IRC_1791835297161.zip`, containing `mirc_icon.png`,
`network.json`, and `regulars.json`. These are preserved under `assets/irc`.
The icon is used for the application window, taskbar button, and activity tray
button. No client screenshot was supplied; the layout uses a classic light
mIRC-style terminal, channel/private-message tabs, topics, and an operator-marked
nick list. Network identity, port, MOTD, channel details, and regular personas
come from the supplied files. The server and old topics retain their original
2001–2002 references; the simulated conversation and clock use 2011.
