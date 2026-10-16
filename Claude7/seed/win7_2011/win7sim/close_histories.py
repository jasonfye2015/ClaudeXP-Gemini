"""Authored fictional friendship seeds, separate from public community biographies.

Keys are stable contact IDs, not roster positions. Memories predate the simulation;
they do not imply dating, consent, or events performed by the running application.
Each pair has two possible recalled moments, selected stably for a fursona.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FriendshipSeed:
    meeting: str
    memories: tuple[str, str]
    boundary: str


# Text addresses the player as "you"; the caller identifies the active fursona.
CLOSE_HISTORIES = {
    "morgan-vale": FriendshipSeed(
        "You met while sorting badges at a small convention's art desk.",
        ("You rescued Morgan's smudged fox print with a spare portfolio sleeve.",
         "Morgan helped you rebuild a convention itinerary after a bus cancellation."),
        "Ask before sharing unfinished art; convention help is not a promise of free commissions."),
    "eli-north": FriendshipSeed(
        "You met on a hobby-radio forum while troubleshooting a noisy microphone.",
        ("You and Eli traced the interference to a desk lamp and celebrated with a music swap.",
         "Eli talked you through labeling PC cables before an upgrade."),
        "Agree on a time for technical help; never request passwords or remote access without permission."),
    "rowan-ash": FriendshipSeed(
        "You met over a collaborative doodle sheet at an independent-comics table.",
        ("You drew a tiny raccoon detective that Rowan turned into a three-panel joke.",
         "Rowan traded you a handmade mini-comic for your sketch of the table's mascot."),
        "Keep sketches private unless approved; give critique only when asked."),
    "jules-river": FriendshipSeed(
        "You met while waiting outside a small all-ages music venue as adults.",
        ("You and Jules made a blurry-photo album after a rain-shortened gig.",
         "You found a quiet diner together when the opening band ran late."),
        "Friendship does not imply dating; do not press for details about Jules's former partner."),
    "alex-alder": FriendshipSeed(
        "You met during a community banner-painting afternoon.",
        ("You fixed a backwards stencil together and kept the wonky test print.",
         "You mixed the perfect sunset orange using the last two paint pots."),
        "Ask before posting shared artwork or tagging either artist."),
    "alex-bennett": FriendshipSeed(
        "You met at a beginner-friendly tabletop game night.",
        ("You saved a disastrous round by agreeing to cooperate rather than compete.",
         "You invented a house rule for a missing game token and wrote it on a coaster."),
        "Keep games welcoming; teasing stops immediately when someone is uncomfortable."),
    "alex-caldwell": FriendshipSeed(
        "You met while helping catalog a local music exchange.",
        ("You discovered a mislabeled demo tape and compared its handwritten track list.",
         "You built a shared rainy-day playlist from albums nobody else had picked."),
        "Recommendations are optional; do not mock each other's music tastes."),
    "alex-delaney": FriendshipSeed(
        "You met on a walking group's adult photo outing.",
        ("You waited together for a heron to return to an empty footbridge.",
         "You compared pictures of the same puddle and laughed at the different reflections."),
        "Ask before photographing people or revealing the location of private meetups."),
    "alex-ellis": FriendshipSeed(
        "You met at a costume-repair workshop.",
        ("You held a seam steady while Alex repaired a loose costume cuff.",
         "You sorted a spilled button tin together and found a matching pair."),
        "Never touch a costume or its wearer without permission."),
    "alex-foster": FriendshipSeed(
        "You met on an indie-game discussion board.",
        ("You mapped a confusing puzzle room together using graph paper.",
         "You compared alternate endings without spoiling them for the rest of the group."),
        "Check before sharing spoilers; no pressure to buy a recommended game."),
    "alex-greer": FriendshipSeed(
        "You met at a science-fiction paperback swap.",
        ("You traded duplicate novels and left each other spoiler-free bookmarks.",
         "You defended opposite sides of a fictional first-contact dilemma over tea."),
        "Debate the story, not each other's worth or intelligence."),
    "alex-hayes": FriendshipSeed(
        "You met while checking trail maps at a community walking meetup.",
        ("You chose the shorter loop together when the weather turned.",
         "You found a shaded bench and sketched a landmark for the group's directions."),
        "Respect requests to rest or turn back; never pressure someone into a risky route."),
    "alex-irwin": FriendshipSeed(
        "You met in an animation study group.",
        ("You made a flipbook of a bouncing acorn and compared timing notes.",
         "You spotted a missing frame in a group animation and helped restore it."),
        "Credit collaborators and ask before distributing unfinished animation."),
    "alex-jensen": FriendshipSeed(
        "You met while volunteering at a community potluck.",
        ("You saved a bland soup by adding herbs one pinch at a time.",
         "You made handwritten ingredient cards after a recipe label went missing."),
        "Respect dietary needs; do not insist someone try a dish."),
    "alex-keating": FriendshipSeed(
        "You met on a hobby website accessibility thread.",
        ("You tested a fan site's navigation together using only the keyboard.",
         "You rescued a broken guestbook layout by simplifying its markup."),
        "Offer help without taking control of someone else's site or account."),
    "alex-lennox": FriendshipSeed(
        "You met while browsing a used-record stall.",
        ("You shared a listening station for a record with an unreadable sleeve.",
         "You found two copies of an overlooked album and each took one home."),
        "Do not lend or resell the other's records without asking."),
    "alex-mercer": FriendshipSeed(
        "You met while assembling convention welcome packets.",
        ("You caught an incorrect room number before the maps were handed out.",
         "You folded paper arrows together to direct late arrivals to registration."),
        "Volunteer shifts need agreement; friendship does not make someone always on call."),
    "alex-nolan": FriendshipSeed(
        "You met in a small creative-writing circle.",
        ("You exchanged stories about an abandoned lighthouse and compared endings.",
         "You helped each other cut a rambling opening down to one strong paragraph."),
        "Drafts stay within the circle; sensitive themes require a check-in first."),
    "alex-ortega": FriendshipSeed(
        "You met at a community PC-building demonstration.",
        ("You found a loose case screw before it could cause trouble.",
         "You drew a cooling-airflow diagram together on the back of a parts list."),
        "Agree on spending limits; never assume permission to alter another person's hardware."),
    "alex-perry": FriendshipSeed(
        "You met at an informal outdoor sketch session.",
        ("You swapped pencils after both brought the wrong hardness for the exercise.",
         "You sketched the same crooked street sign from opposite sides."),
        "Art practice is not a competition; ask before offering corrections."),
    "alex-quill": FriendshipSeed(
        "You met in an adult role-playing game's introductory session.",
        ("You negotiated a peaceful solution with the fictional bridge keeper.",
         "You improvised a tavern song when the group forgot its quest notes."),
        "Agree on themes and limits before role-play; an in-character bond is not real-world consent."),
    "alex-sawyer": FriendshipSeed(
        "You met while painting scenery for a community play.",
        ("You disguised a paint spill as a tree root on the set.",
         "You steadied a cardboard castle while the stage crew secured it."),
        "Backstage access needs permission; no photos of people changing or preparing."),
    "alex-taylor": FriendshipSeed(
        "You met while packing donated art supplies.",
        ("You turned battered boxes into labeled starter kits.",
         "You tested every marker together and made a rainbow inventory sheet."),
        "Donations are voluntary; do not turn a friendship into repeated financial requests."),
    "alex-underwood": FriendshipSeed(
        "You met at a library's local-history display.",
        ("You compared an old street map with a modern walking route.",
         "You found a newspaper photo of a long-closed cinema in the archive."),
        "Discuss public history, not private addresses or identifying information."),
    "alex-vaughn": FriendshipSeed(
        "You met during a casual community bowling night.",
        ("You celebrated a single lucky spare after several gutter balls.",
         "You chose silly team names and forgot to care about the final score."),
        "Keep competition friendly; no unwanted physical celebration or roughhousing."),
    "alex-west": FriendshipSeed(
        "You met on a fan forum's moderation help thread.",
        ("You rewrote a confusing welcome message to make newcomers feel included.",
         "You helped untangle a misunderstanding by asking both sides to clarify."),
        "Private messages stay private; neither friend must take sides in every dispute."),
    "alex-young": FriendshipSeed(
        "You met while repairing decorations for a neighborhood festival.",
        ("You untangled a box of paper lanterns without tearing one.",
         "You moved the display indoors together when wind spoiled the setup."),
        "Plans can change; do not guilt someone into staying longer than agreed."),
    "alex-zimmer": FriendshipSeed(
        "You met in a puzzle-book exchange.",
        ("You solved a stubborn crossword clue by combining your guesses.",
         "You built a tiny scavenger hunt from the bookstore's public shelf signs."),
        "Hints are offered, not forced; avoid jokes that make mistakes feel embarrassing."),
    "avery-alder": FriendshipSeed(
        "You met while decorating a charity bake-sale table.",
        ("You turned spare ribbon into little price-card holders.",
         "You kept a tray steady while Avery replaced a wobbly table leg."),
        "Ask before volunteering the other's time or making public commitments."),
    "avery-bennett": FriendshipSeed(
        "You met at a board-game prototype demonstration.",
        ("You discovered that the prototype's trading rule could loop forever.",
         "You suggested a cooperative round that became the designer's favorite test."),
        "Keep prototype rules confidential until the creator agrees to share."),
    "avery-caldwell": FriendshipSeed(
        "You met while comparing concert flyers at a cafe.",
        ("You found an acoustic set hidden in the smallest print on a flyer.",
         "You swapped notes about a singer whose microphone failed mid-song."),
        "Invitations are not obligations; declining a show does not require an explanation."),
    "avery-delaney": FriendshipSeed(
        "You met at a community darkroom introduction.",
        ("You compared two prints of a station clock with different exposures.",
         "You rescued a test print by catching a timer set to the wrong duration."),
        "Photo subjects must consent; do not share recognizable portraits without approval."),
    "avery-ellis": FriendshipSeed(
        "You met while cutting felt shapes for a costume workshop.",
        ("You made a repair patch shaped like a small leaf.",
         "You practiced fastening a removable tail on a display stand."),
        "Costume assistance always requires a specific invitation before touching."),
    "avery-foster": FriendshipSeed(
        "You met in a retro adventure-game chat room.",
        ("You drew a map of a maze that kept looping back to its entrance.",
         "You finally solved a sound puzzle after noticing a repeated bell note."),
        "Ask whether help or a hint is wanted before revealing solutions."),
    "avery-greer": FriendshipSeed(
        "You met at a speculative-fiction reading circle.",
        ("You designed rival imaginary planets on scraps of paper.",
         "You compared two translations of a favorite short story."),
        "Fictional arguments should not become personal attacks; pause when either friend asks."),
    "avery-hayes": FriendshipSeed(
        "You met during a park cleanup walk.",
        ("You freed a footpath sign from tangled litter using the group's tools.",
         "You logged a damaged bench for the organizers rather than trying an unsafe repair."),
        "Safety comes first; nobody owes extra labor to prove they care."),
    "avery-irwin": FriendshipSeed(
        "You met while making a stop-motion short with a local art club.",
        ("You rebuilt a clay moon after it rolled off the miniature set.",
         "You used a paper cloud to hide a visible support wire."),
        "Agree on credits and screening permission before showing collaborative work."),
    "avery-jensen": FriendshipSeed(
        "You met at a beginner bread-making class.",
        ("You laughed together at a loaf shaped more like a slipper than a baguette.",
         "You compared kneading techniques and rescued a too-sticky dough."),
        "Food and body comments should stay kind; do not pressure someone to eat."),
    "avery-keating": FriendshipSeed(
        "You met while testing a community event website.",
        ("You found a signup button hidden behind a decorative banner.",
         "You rewrote a confusing schedule into a readable plain-text list."),
        "Never publish contact information from a registration form."),
    "avery-lennox": FriendshipSeed(
        "You met at a secondhand cassette exchange.",
        ("You identified an unmarked mixtape by its opening guitar riff.",
         "You made handwritten liner notes for a tape missing its case insert."),
        "Ask before copying or lending something borrowed; respect the owner's answer."),
    "avery-mercer": FriendshipSeed(
        "You met while staffing a convention's information table.",
        ("You found a lost sketchbook's owner without reading its private pages.",
         "You improvised a clear queue sign when the official one went missing."),
        "Lost property and attendees' personal details are not conversation gossip."),
    "avery-nolan": FriendshipSeed(
        "You met during a postcard-story challenge.",
        ("You each wrote a mystery that fit on the back of a single postcard.",
         "You swapped first lines and ended up with completely different endings."),
        "Personal experiences used in stories need permission before publication."),
    "avery-ortega": FriendshipSeed(
        "You met at a used-computer refurbishment day.",
        ("You sorted working RAM sticks into labeled antistatic bags.",
         "You revived a dusty case fan with the supervisor's approved cleaning tools."),
        "Do not inspect private files; hardware help never grants access to personal data."),
    "avery-perry": FriendshipSeed(
        "You met at a cafe's adult life-drawing practice group.",
        ("You both drew the model's chair more accurately than its complicated drape.",
         "You traded timed gesture sketches and noticed opposite strengths."),
        "Respect the model's rules; no photographs or sharing drawings without permission."),
    "avery-quill": FriendshipSeed(
        "You met while planning a tabletop campaign's first session.",
        ("You invented a traveling library as the party's meeting place.",
         "You designed a puzzle door that opened only after a polite introduction."),
        "Check comfort with story themes; respect out-of-character stops without debate."),
    "avery-sawyer": FriendshipSeed(
        "You met while sorting props for a community comedy.",
        ("You found the missing rubber chicken inside a mislabeled hat box.",
         "You made a prop newspaper with absurd but harmless headlines."),
        "Pranks require willing participants; do not embarrass someone onstage without agreement."),
    "avery-taylor": FriendshipSeed(
        "You met during an origami afternoon at a community center.",
        ("You turned a misfolded crane into an oddly charming paper duck.",
         "You assembled a paper mobile from everyone's leftover practice sheets."),
        "Patient teaching is welcome; do not take over someone else's project."),
    "avery-underwood": FriendshipSeed(
        "You met while organizing a public neighborhood map project.",
        ("You marked accessible entrances that the old map had missed.",
         "You added a quiet courtyard to the map after checking it was open to visitors."),
        "Only public places belong on the map; keep friends' homes private."),
    "avery-vaughn": FriendshipSeed(
        "You met at a casual community badminton session.",
        ("You tried a slow practice rally that lasted longer than either expected.",
         "You repaired a loose net tie before the next friendly match."),
        "Respect physical limits and requests for breaks; no unsolicited coaching."),
    "avery-west": FriendshipSeed(
        "You met while writing an online group's newcomer guide.",
        ("You replaced confusing insider jokes with useful explanations.",
         "You made a welcome checklist after a newcomer got lost between forum sections."),
        "Friendship is not permission to disclose moderation discussions or private messages."),
}
