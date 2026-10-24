#!/bin/bash
# Claude Timeline on a Mac (Apple silicon): the SYSTEC Multi-Boot Manager, on the Timeline's own Mac Python
# (Python-mac, beside the Windows one). Double-click it in Finder.
# Python's compiled-code cache goes on the Mac's own disk, not the SSD (where every small file takes 256 KB).
cd "$(dirname "$0")"
export PYTHONNOUSERSITE=1
export PYTHONPYCACHEPREFIX="$HOME/Library/Caches/Claude Timeline/pycache"
if [ ! -x "./Python-mac/bin/python3" ]; then
    echo "The Mac Python (Python-mac) isn't on this drive."
    read -n 1 -s -r -p "Press any key to close."
    exit 1
fi
./Python-mac/bin/python3 ClaudeLauncher/main.py
