"""Tests for engine/difficulty.py."""
from engine.difficulty import calibrate_from_recent


def test_no_adjustment_too_few():
    """Should not adjust with fewer than 3 results."""
    d = calibrate_from_recent(800, [True, True])
    assert d == 800


def test_above_target_increases_difficulty():
    """If accuracy > 80%, push difficulty up (harder)."""
    results = [True] * 10  # 100% accuracy
    d = calibrate_from_recent(800, results)
    assert d > 800


def test_below_target_decreases_difficulty():
    """If accuracy < 80%, push difficulty down (easier)."""
    results = [False] * 8 + [True] * 2  # 20% accuracy
    d = calibrate_from_recent(800, results)
    assert d < 800


def test_at_target_no_change():
    """At exactly 80%, no adjustment."""
    results = [True] * 8 + [False] * 2  # 80%
    d = calibrate_from_recent(800, results)
    assert abs(d - 800) < 0.1


def test_adjustment_magnitude():
    """10% off target ≈ 50 points adjustment (aggressive ramp)."""
    results = [True] * 9 + [False] * 1  # 90%
    d = calibrate_from_recent(800, results)
    # 90% - 80% = 10% -> ~50 point increase
    assert abs(d - 850) < 1
