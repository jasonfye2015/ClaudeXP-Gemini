"""Moved to the Claude Timeline's ClaudeCore (claudecore/ai/llm_server.py); this name keeps working for ClaudeXP."""
import sys

from claudecore.ai import llm_server as _moved

sys.modules[__name__] = _moved
