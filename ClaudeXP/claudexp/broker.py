"""Moved to the Claude Timeline's ClaudeCore (claudecore/ai/broker.py); this name keeps working for ClaudeXP."""
import sys

from claudecore.ai import broker as _moved

sys.modules[__name__] = _moved
