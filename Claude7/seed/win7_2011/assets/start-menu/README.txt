"BG1_Bar" is a blank menu bar, grey and solid color entirely. it goes on top of a back ground image, and then all of the menu bar items go on top of this.. it's sized for a 1920x1200 resolution and background image of that size.

"Background1.jpg" is the default background image for this project, and is 1920x1200.

The start button has 1 states it can be "Start_Button_A" and "Start_Button_B". A is standard, and B is what it turns into when the user clicks on it, which also pops up the "Menu_Empty_Template" and clicking anywhere else other than a menu item, will collapse it back down, and turn the button back to state A. The users mouse with highlight menu items when hovering over them, and "Windows Menu Command.wav" will be played, each time the focus changes from item to item. When a menu item is clicked on to run it "Windows Navigation Start.wav" will play as that program is opened, or also when a start menu folder is expanded or collapsed.

The start menu has a vertical bar along the left side, the Users name in bold will be printed there, rotated so that it fits. 

The start menu has 8 total main items on the first layer. 6 on top, then a divider, then 2 on bottom.

Menu Bar Items:
1- (Icon: "Programs.ico") Text: "Programs" (Expansion indicator, justified to the right) - This will expand a menu to the side, that will have programs and folders.
2- (Icon: "Recent.ico") Text: "Recent Items" (Expansion indicator, justified to the right) - This will list the last accessed documents, up to the last 8 of them.
3- (Icon: "Search.ico") Text: "Search..." - This will open up a search box.
4- (Icon: "Options.ico") Text: "Options" (Expansion indicator, justified to the right) - This will open up the options window.
5- (Icon: "Help.ico") Text: "Help and Support" - This will open up the help window.
6- (Icon: "Run.ico") Text: "Run..." - This will open up the run window. 
(A divider between the two sections)
7- (Icon: "Log_Off.ico") Text: "Log Off" - This will return to the user log on screen.
8- (Icon: "Shut_Down.ico") Text: "Shut Down" - This will start the shut down process.

If an item does not exist yet, that a user clicks on, create a small window that states that feature has not been implemented yet.

"Menu_Bar_Transition_Template" sits on the menu bar, directly to the left of the Start_Button, this provides a buffer (and a color transition) between the Start_Button and Menu_Programs.

"Menu_Program_Template" can be tiled starting from "Menu_Bar_Transition_Template" and all the way across the menu bar, to "Menu_System_Tray_Template". For each program open, a "Menu_Program_Template" is created, with an icon of that program. clicking on "Menu_Program_Template" will hide and unhide the program associated with it ("Windows Minimize.wav" will be played when hiding, "Windows Restore.wav" will be played when unhiding) . When that program is closed, the corresponding "Menu_Program_Template" is removed.

"Menu_System_Tray_Template" sits on the Menu_Bar, all the way to the right. This is the system tray, and on it, will be the time and date, with time overtop of the date, both in white colored font, and justified to the right in the system tray. System Tray icons will also be placed here, and I will share the details of them later.




