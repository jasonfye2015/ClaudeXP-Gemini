"""Moved to the Claude Timeline's ClaudeCore (claudecore/ai/llmlog.py); this name keeps working for ClaudeXP."""
import sys

from claudecore.ai import llmlog as _moved

sys.modules[__name__] = _moved
