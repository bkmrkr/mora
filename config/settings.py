"""Mora — centralized configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'mora.db')

# Ollama
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen3:8b')

# ELO defaults
ELO_DEFAULTS = {
    'initial_skill_rating': 800.0,
    'initial_uncertainty': 350.0,
    'base_k_factor': 32.0,
    'mastery_threshold': 0.75,
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
    'max_generation_attempts': 2,
}
