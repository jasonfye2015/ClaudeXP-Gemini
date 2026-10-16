"""Moved to the Claude Timeline's ClaudeCore (claudecore/ai/llm_setup.py); this name keeps working for ClaudeXP."""
import sys

from claudecore.ai import llm_setup as _moved

sys.modules[__name__] = _moved
