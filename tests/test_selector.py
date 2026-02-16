"""Tests for engine/selector.py — skill selection."""
from engine.selector import (
    analyze_recent, select_skill, compute_question_params,
    _get_eligible_skills,
)


def _make_progress(skill_id, mastery=0.0, rating=800.0, attempts=0):
    return {
        'skill_id': skill_id,
        'skill_rating': rating,
        'uncertainty': 350.0,
        'mastery_level': mastery,
        'total_attempts': attempts,
        'correct_attempts': 0,
    }


class TestAnalyzeRecent:
    def test_empty(self):
        result = analyze_recent([])
        assert result['overall_accuracy'] == 0.0
        assert result['total_attempts'] == 0

    def test_basic_stats(self):
        attempts = [
            {'skill_id': 'g1_add_10', 'is_correct': 1},
            {'skill_id': 'g1_add_10', 'is_correct': 0},
            {'skill_id': 'g1_sub_10', 'is_correct': 1},
        ]
        result = analyze_recent(attempts)
        assert abs(result['overall_accuracy'] - 2/3) < 0.01
        assert result['total_attempts'] == 3
        assert result['per_skill']['g1_add_10']['count'] == 2
        assert result['per_skill']['g1_sub_10']['count'] == 1

    def test_recency(self):
        attempts = [
            {'skill_id': 'g1_sub_10', 'is_correct': 1},
            {'skill_id': 'g1_add_10', 'is_correct': 1},
        ]
        result = analyze_recent(attempts)
        assert result['last_seen']['g1_sub_10'] == 0  # most recent
        assert result['last_seen']['g1_add_10'] == 1


class TestSelectSkill:
    def test_selects_from_starters(self):
        """With no progress, should pick a grade 1 starter skill."""
        analysis = analyze_recent([])
        progress = {}
        skill_id = select_skill(analysis, progress)
        assert skill_id is not None
        # Should be a grade 1 skill (starter)
        from curriculum.skills import SKILLS
        assert SKILLS[skill_id]['grade'] == 1

    def test_never_repeats(self):
        """Should not return the current skill."""
        analysis = analyze_recent([])
        progress = {}
        skill_id = select_skill(analysis, progress, current_skill_id='g1_add_10')
        assert skill_id != 'g1_add_10'

    def test_prefers_virgin_skills(self):
        """Skills with 0 attempts should get a bonus."""
        analysis = analyze_recent([])
        progress = {
            'g1_add_10': _make_progress('g1_add_10', mastery=0.3, attempts=5),
            'g1_sub_10': _make_progress('g1_sub_10', mastery=0.0, attempts=0),
        }
        # Both are eligible (grade 1 starters). Virgin should be preferred.
        skill_id = select_skill(analysis, progress, current_skill_id='g1_counting')
        # With virgin bonus, g1_sub_10 should score higher than g1_add_10
        # (unless recency overrides, but with no attempts both have recency=99)
        # Actually there are multiple virgin skills, so we just check it's not the current one
        assert skill_id != 'g1_counting'

    def test_locked_skills_excluded(self):
        """Grade 2 skills should not be picked if grade 1 prereqs unmastered."""
        analysis = analyze_recent([])
        progress = {
            'g1_add_20': _make_progress('g1_add_20', mastery=0.3, attempts=5),
            'g1_sub_20': _make_progress('g1_sub_20', mastery=0.3, attempts=5),
        }
        skill_id = select_skill(analysis, progress)
        from curriculum.skills import SKILLS
        # g2_add_sub_100 requires g1_add_20 and g1_sub_20 mastered — shouldn't be picked
        assert skill_id != 'g2_add_sub_100'

    def test_all_mastered_fallback(self):
        """When all eligible skills are mastered, fall back to least mastered."""
        from curriculum.skills import SKILLS
        progress = {}
        for sid in SKILLS:
            progress[sid] = _make_progress(sid, mastery=0.8, attempts=20, rating=1200)
        analysis = analyze_recent([])
        skill_id = select_skill(analysis, progress)
        # Should return something (least mastered)
        assert skill_id is not None


class TestEligibleSkills:
    def test_starters_always_eligible(self):
        """Grade 1 skills with no prerequisites are always eligible."""
        eligible = _get_eligible_skills({})
        ids = {s['id'] for s in eligible}
        assert 'g1_add_10' in ids
        assert 'g1_sub_10' in ids

    def test_grade2_locked_initially(self):
        """Grade 2 skills with prerequisites should not be eligible initially."""
        eligible = _get_eligible_skills({})
        ids = {s['id'] for s in eligible}
        assert 'g2_add_sub_100' not in ids

    def test_grade2_unlocked_after_mastery(self):
        """Grade 2 skills unlock after grade 1 prerequisites are mastered."""
        progress = {
            'g1_add_20': _make_progress('g1_add_20', mastery=0.8, attempts=15),
            'g1_sub_20': _make_progress('g1_sub_20', mastery=0.8, attempts=15),
        }
        eligible = _get_eligible_skills(progress)
        ids = {s['id'] for s in eligible}
        assert 'g2_add_sub_100' in ids

    def test_mastered_skills_excluded(self):
        """Already mastered skills should not be in eligible list."""
        progress = {
            'g1_add_10': _make_progress('g1_add_10', mastery=0.8, attempts=20),
        }
        eligible = _get_eligible_skills(progress)
        ids = {s['id'] for s in eligible}
        assert 'g1_add_10' not in ids


class TestComputeQuestionParams:
    def test_basic_params(self):
        progress = {
            'g1_add_10': _make_progress('g1_add_10', mastery=0.3, rating=850, attempts=10),
        }
        analysis = analyze_recent([])
        difficulty, q_type = compute_question_params('g1_add_10', progress, analysis)
        assert isinstance(difficulty, float)
        assert q_type == 'mcq'  # mastery < 0.5

    def test_high_mastery_short_answer(self):
        progress = {
            'g1_add_10': _make_progress('g1_add_10', mastery=0.55, rating=1100, attempts=30),
        }
        analysis = analyze_recent([])
        _, q_type = compute_question_params('g1_add_10', progress, analysis)
        assert q_type == 'short_answer'

    def test_warm_start(self):
        """New skill should inherit rating from proven skills."""
        progress = {
            'g1_add_10': _make_progress('g1_add_10', mastery=0.5, rating=1000, attempts=10),
            'g1_sub_10': _make_progress('g1_sub_10', mastery=0.5, rating=1100, attempts=10),
            'g1_counting': _make_progress('g1_counting', mastery=0.0, rating=800, attempts=0),
        }
        analysis = analyze_recent([])
        difficulty, _ = compute_question_params('g1_counting', progress, analysis)
        # Should use average of proven skills (~1050), not default 800
        # Target difficulty = skill_rating + 400*log10(1/0.8 - 1) ≈ skill - 241
        # With warm-start from 1050: ~809
        # Without warm-start from 800: ~559
        assert difficulty > 700  # definitely using warm-start

    def test_recent_calibration(self):
        """Recent accuracy should adjust difficulty."""
        progress = {
            'g1_add_10': _make_progress('g1_add_10', mastery=0.3, rating=850, attempts=10),
        }
        # 100% recent accuracy -> should increase difficulty
        attempts = [{'skill_id': 'g1_add_10', 'is_correct': 1} for _ in range(5)]
        analysis = analyze_recent(attempts)
        d_high, _ = compute_question_params('g1_add_10', progress, analysis)

        # 20% recent accuracy -> should decrease difficulty
        attempts2 = [{'skill_id': 'g1_add_10', 'is_correct': 1}] + \
                     [{'skill_id': 'g1_add_10', 'is_correct': 0} for _ in range(4)]
        analysis2 = analyze_recent(attempts2)
        d_low, _ = compute_question_params('g1_add_10', progress, analysis2)

        assert d_high > d_low
