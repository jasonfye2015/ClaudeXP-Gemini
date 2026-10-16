ClaudeArchive - the tools that present the furry media archive, in every era
=============================================================================

The Claude Timeline exists first of all to show the archive in Local Storage. These tools are the same on every
computer; each OS only draws its own window around them.

  comix/        FurComix Reader - comics (CBR, CBZ, folders) from the Furry Media Archive
  folio/        FurFolio (artists' portfolios), FurStory Reader (stories), Fur CD Viewer (art CDs and DVDs),
                Furry Con CD Viewer (convention discs) and the Furry Video Browser
  claudetv/     ClaudeTV and its TV Guide: channels made from TV and Movies (assets/: the static clips and the
                show guide)
  archivepaths.py   where the archive folders are in Local Storage
  tools/7-Zip/  7-Zip, for comic archives and disc images (ClaudeXP's WinRAR and Alcohol 120% use it too)

They talk to the computer only through ClaudeCore's host (see ClaudeGames/README.txt): its windows, sounds, message
boxes, clock and data folder. Flash movies and media files are handed to that OS's own players
(host.open_flash, host.open_media). Reading positions, favourites and thumbnail caches are each computer's own
(host.data); the archive itself is never written to.
