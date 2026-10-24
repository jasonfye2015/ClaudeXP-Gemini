#!/bin/bash
# Kithylin AI on its own, on a Mac (Apple silicon), with the Timeline's Mac Python. Double-click it in Finder.
cd "$(dirname "$0")/.."
export PYTHONNOUSERSITE=1
export PYTHONPYCACHEPREFIX="$HOME/Library/Caches/Claude Timeline/pycache"
../Python-mac/bin/python3 -m kithylinai
