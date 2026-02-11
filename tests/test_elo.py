"""Tests for engine/elo.py — ELO skill model."""
import math

from engine.elo import (
    p_correct, target_difficulty, compute_k_factor,
    update_skill, compute_mastery, is_mastered,
)


def test_p_correct_equal_rating():
    """When skill == difficulty, P should be 0.5."""
    assert abs(p_correct(1000, 1000) - 0.5) < 1e-9


def test_p_correct_easier_question():
    """When difficulty < skill, P > 0.5."""
    p = p_correct(1000, 800)
    assert p > 0.5


def test_p_correct_harder_question():
    """When difficulty > skill, P < 0.5."""
    p = p_correct(1000, 1200)
    assert p < 0.5


def test_target_difficulty_for_80_percent():
    """Target D should be ~241 below skill for 80% success."""
    d = target_difficulty(1000, target_p=0.8)
    expected = 1000 + 400 * math.log10(1/0.8 - 1)  # ~758.8
    assert abs(d - expected) < 0.1
    assert d < 1000  # Should be easier than skill


def test_target_difficulty_for_50_percent():
    """Target D at 50% should equal skill rating."""
    d = target_difficulty(1000, target_p=0.5)
    assert abs(d - 1000) < 0.1


def test_k_factor_high_uncertainty():
    """K-factor should be higher when uncertainty is high."""
    k_high = compute_k_factor(300, base_k=32, initial_uncertainty=300)
    k_low = compute_k_factor(100, base_k=32, initial_uncertainty=300)
    assert k_high > k_low


def test_k_factor_at_initial():
    """At initial uncertainty, K should equal base_k."""
    k = compute_k_factor(300, base_k=32, initial_uncertainty=300)
    assert abs(k - 32) < 1e-9


def test_correct_answer_increases_skill():
    """Correct answer should increase skill_rating."""
    new_rating, _ = update_skill(1000, 300, 800, True)
    assert new_rating > 1000


def test_wrong_answer_decreases_skill():
    """Wrong answer should decrease skill_rating."""
    new_rating, _ = update_skill(1000, 300, 800, False)
    assert new_rating < 1000


def test_uncertainty_decreases():
    """Uncertainty should decrease after each attempt."""
    _, new_unc = update_skill(1000, 300, 800, True)
    assert new_unc < 300
    _, new_unc2 = update_skill(1000, new_unc, 800, True)
    assert new_unc2 < new_unc


def test_uncertainty_floor():
    """Uncertainty should not go below 50."""
    _, unc = update_skill(1000, 50, 800, True)
    assert unc >= 50


def test_mastery_computation():
    """Mastery should blend normalized rating and recent accuracy."""
    m = compute_mastery(1000, 0.8)
    # normalized = (1000-400)/1200 = 0.5
    # mastery = 0.6*0.5 + 0.4*0.8 = 0.62
    assert abs(m - 0.62) < 0.01


def test_mastery_at_floor():
    m = compute_mastery(400, 0.0)
    assert m == 0.0


def test_is_mastered():
    assert is_mastered(0.8)
    assert not is_mastered(0.5)


def test_update_returns_tuple():
    result = update_skill(1000, 300, 800, True)
    assert len(result) == 2
    assert isinstance(result[0], float)
    assert isinstance(result[1], float)
