"""ELO-like skill model with Bayesian uncertainty.

Core formulas from spec:
  P(correct) = 1 / (1 + 10^((D - S) / 400))
  target_difficulty = S + 400 * log10(1/P_target - 1)
  delta = K * (actual - expected)
  K = base_K * (uncertainty / initial_uncertainty)
"""
import math

from config.settings import ELO_DEFAULTS, DIFFICULTY_DEFAULTS


def p_correct(skill_rating, difficulty,
              scale=DIFFICULTY_DEFAULTS['elo_scale_factor']):
    """Probability of answering correctly given skill and question difficulty."""
    return 1.0 / (1.0 + 10 ** ((difficulty - skill_rating) / scale))


def target_difficulty(skill_rating,
                      target_p=DIFFICULTY_DEFAULTS['target_success_rate'],
                      scale=DIFFICULTY_DEFAULTS['elo_scale_factor']):
    """Compute question difficulty D such that P(correct) = target_p.

    For P=0.8: D = S + 400 * log10(0.25) = S - 241
    """
    if target_p <= 0 or target_p >= 1:
        return skill_rating
    return skill_rating + scale * math.log10(1.0 / target_p - 1.0)


def compute_k_factor(uncertainty,
                     base_k=ELO_DEFAULTS['base_k_factor'],
                     initial_uncertainty=ELO_DEFAULTS['initial_uncertainty']):
    """Dynamic K-factor: higher when uncertain, lower when confident."""
    return base_k * (uncertainty / initial_uncertainty)


def update_skill(skill_rating, uncertainty, difficulty, is_correct,
                 base_k=ELO_DEFAULTS['base_k_factor'],
                 initial_uncertainty=ELO_DEFAULTS['initial_uncertainty']):
    """Update skill_rating and uncertainty after an attempt.

    Returns (new_skill_rating, new_uncertainty).
    """
    expected = p_correct(skill_rating, difficulty)
    actual = 1.0 if is_correct else 0.0
    k = compute_k_factor(uncertainty, base_k, initial_uncertainty)

    delta = k * (actual - expected)
    new_rating = skill_rating + delta

    # Reduce uncertainty ~5% per attempt, floor at 50
    new_uncertainty = max(uncertainty * 0.95, 50.0)

    return new_rating, new_uncertainty


def compute_mastery(skill_rating, recent_accuracy,
                    weight_skill=0.6, weight_recent=0.4):
    """Compute mastery_level (0-1) from normalized skill + recent accuracy.

    Normalize skill_rating: 400-1600 range → 0-1.
    """
    normalized = max(0.0, min(1.0, (skill_rating - 400) / 1200))
    return weight_skill * normalized + weight_recent * recent_accuracy


def is_mastered(mastery_level,
                threshold=ELO_DEFAULTS['mastery_threshold']):
    return mastery_level >= threshold
