"""Claude11 - WORKSTATION-2025: a Windows 11 Home computer from October 2025, in the Claude Timeline."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude11.launch import main  # noqa: E402

if __name__ == "__main__":
    main()
