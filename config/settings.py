"""Mora v2 — centralized configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'mora.db')

# ELO defaults
ELO_DEFAULTS = {
    'initial_skill_rating': 800.0,
    'initial_uncertainty': 350.0,
    'base_k_factor': 32.0,
    'mastery_threshold': 0.65,
    'mastery_weight_skill': 0.3,
    'mastery_weight_recent': 0.7,
    'mastery_min_attempts': 5,
}

# Difficulty targeting
DIFFICULTY_DEFAULTS = {
    'target_success_rate': 0.80,
    'recent_window': 30,
    'elo_scale_factor': 400.0,
}

# Session defaults
SESSION_DEFAULTS = {
    'target_success_rate': 0.80,
}
