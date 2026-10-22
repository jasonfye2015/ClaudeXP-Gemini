"""Claude7 - SYSTEM-2011: a Windows 7 Home Premium computer from October 2011, in the Claude Timeline."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude7.launch import main  # noqa: E402

if __name__ == "__main__":
    main()
