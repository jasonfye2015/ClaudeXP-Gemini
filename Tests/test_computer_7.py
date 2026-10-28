"""SYSTEM-2011 (Windows 7) booted for real, offscreen, in a sandbox: power on to the desktop, the Start menu, programs
opening and closing, logging off and shutting down. See computers.py for what the sandbox covers."""
import support
from computers import run_computer_tests

SLOW = True
TIMEOUT = 900

run_computer_tests(2011, globals())

if __name__ == "__main__":
    support.main(globals())
