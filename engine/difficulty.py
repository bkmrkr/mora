"""Difficulty calibration from recent-30 window.

If recent accuracy > 80%, increase target difficulty (harder).
If < 80%, decrease (easier). Self-calibrating feedback loop.
"""
from config.settings import DIFFICULTY_DEFAULTS


def calibrate_from_recent(base_target_difficulty, recent_results,
                          target=DIFFICULTY_DEFAULTS['target_success_rate']):
    """Adjust target difficulty based on recent attempt results.

    Args:
        base_target_difficulty: ELO-computed target D.
        recent_results: list of booleans (True=correct).

    Returns adjusted target difficulty.
    """
    if len(recent_results) < 3:
        return base_target_difficulty

    recent_accuracy = sum(recent_results) / len(recent_results)
    error = recent_accuracy - target
    # Scale: 10% off target → ~10 ELO points adjustment
    adjustment = error * 100

    return base_target_difficulty + adjustment
