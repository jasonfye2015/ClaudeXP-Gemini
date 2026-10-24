"""The three computers of the Claude Timeline, with the specs from the spec sheets (Images/Z Specs and Details)."""
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

TIMELINE = Path(__file__).resolve().parent.parent.parent
IMAGES = TIMELINE / "ClaudeLauncher" / "Images"


@dataclass
class System:
    key: str                  # EPOCH-2001 ...
    folder: str               # its folder in the Timeline
    year: int
    os_name: str
    short: list               # the card's one-line specs: (label, value)
    tagline: str
    specs: list = field(default_factory=list)       # (part, value, description)
    accent: str = "#E8A040"

    @property
    def path(self):
        return TIMELINE / self.folder

    @property
    def installed(self):
        return (self.path / "main.py").is_file()

    def image(self, kind=""):
        name = f"Desktop_{self.year}{'_' + kind if kind else ''}.jpg"
        return IMAGES / name

    def python(self):
        """The interpreter that runs this computer: its own .venv when this PC has the Python it was made from (the
        development PC), else the Timeline's portable Python (on the external SSD, on any PC)."""
        if sys.platform == "darwin":                     # a Mac: the Timeline's Mac Python (Python-mac on the SSD)
            mac = TIMELINE / "Python-mac" / "bin" / "python3"
            return mac if mac.is_file() else Path(sys.executable)
        windowed = "pythonw.exe" if os.name == "nt" else "python"
        venv = self.path / ".venv" / "Scripts" / windowed
        if venv.is_file() and venv_usable(self.path / ".venv"):
            return venv
        portable = TIMELINE / "Python" / windowed
        if portable.is_file():
            return portable
        return Path(sys.executable)


PORTABLE_PYTHON = TIMELINE / "Python"
PORTABLE_PYTHONS = (PORTABLE_PYTHON, TIMELINE / "Python-mac")


def venv_usable(venv):
    """A .venv only works where the Python it was made from (pyvenv.cfg's 'home') is installed."""
    try:
        for line in (venv / "pyvenv.cfg").read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "home":
                return Path(value.strip()).is_dir()
    except OSError:
        pass
    return False


SYSTEMS = [
    System("EPOCH-2001", "ClaudeXP", 2001, "Windows XP Home Edition",
           [("CPU", "Intel Pentium III"), ("RAM", "256 MB"), ("OS", "WinXP-v2001")],
           "The freshly released, colorful interface that brought stability and consumer multimedia to the "
           "forefront of computing.",
           [("Processor", "Intel Pentium III @ 866 MHz",
             "A reliable \"Coppermine\" core chip for productivity, early web browsing and casual gaming."),
            ("Memory", "256 MB SDRAM", "Plenty for several applications at once; XP feels quite responsive."),
            ("Graphics", "NVIDIA GeForce 2 MX", "The most popular entry-level card of 2001, for Half-Life and "
                                                "SimCity 3000."),
            ("Storage", "80 GB IDE Hard Drive", "Incredibly spacious in 2001: thousands of MP3s, photos and games."),
            ("Display", "17-inch Dell UltraScan CRT, 1024x768", "The bulky, vibrant standard of the day."),
            ("Internet", "56 Kbps dial-up modem", "The screaming handshake was the gateway to AOL, IRC and the Web."),
            ("Printer", "Epson dot matrix", "Noisy, reliable, with tear-off perforated paper.")],
           accent="#E8A040"),
    System("SYSTEM-2011", "Claude7", 2011, "Windows 7 Home Premium (64-bit)",
           [("CPU", "Intel Core i5"), ("RAM", "8 GB"), ("OS", "Win7-v2011")],
           "The slick Aero Glass interface that restored confidence with stability and speed.",
           [("Processor", "Intel Core i5-2500K @ 3.30 GHz", "The legendary quad-core \"Sandy Bridge\" overclocker."),
            ("Memory", "8 GB DDR3", "Room for 64-bit computing, HD media and aggressive multi-tab browsing."),
            ("Graphics", "NVIDIA GeForce GTX 560 Ti (1 GB)", "Skyrim, Battlefield 3 and Portal 2 in full HD."),
            ("Storage", "1 TB SATA III Hard Drive (7200 RPM)", "Photo collections, music libraries and HD movies."),
            ("Display", "23-inch widescreen LCD, 1920x1080", "A slim 1080p panel replaces the heavy CRT."),
            ("Internet", "Wi-Fi 4 (802.11n) and broadband", "Always on: YouTube streams without tying up the phone."),
            ("Printer", "HP Photosmart All-in-One inkjet", "Photo prints, scanning and copying in one unit.")],
           accent="#40C8E8"),
    System("WORKSTATION-2025", "Claude11", 2025, "Windows 11 Home (64-bit)",
           [("CPU", "AMD Ryzen 7"), ("RAM", "32 GB"), ("OS", "Win11-v2025")],
           "A modern, centered UI with AI-assisted features, DirectX 12 Ultimate and auto-HDR gaming.",
           [("Processor", "AMD Ryzen 7 7800X3D", "8 cores with 3D V-Cache, among the fastest gaming chips."),
            ("Memory", "32 GB DDR5 @ 6000 MHz", "Heavy gaming, 4K streaming and creative work with ease."),
            ("Graphics", "NVIDIA GeForce RTX 4070 Ti Super (16 GB)", "Ray tracing and DLSS 3 frame generation."),
            ("Storage", "2 TB NVMe M.2 PCIe 4.0 SSD", "Boot times and load screens all but disappear."),
            ("Display", "34-inch ultrawide curved QHD, 3440x1440", "A 144 Hz IPS panel with room for everything."),
            ("Internet", "Wi-Fi 6E and gigabit fiber", "A 100 GB game downloads in minutes."),
            ("Printer", "HP Smart Tank All-in-One", "Cartridge-free, wireless, printing straight from a phone.")],
           accent="#5A8CFF"),
]
