"""Moved to the Claude Timeline's ClaudeCore (claudecore/ai/ai_models.py); this name keeps working for ClaudeXP."""
import sys

from claudecore.ai import ai_models as _moved

sys.modules[__name__] = _moved
