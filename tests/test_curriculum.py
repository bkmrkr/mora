"""Tests for curriculum skill definitions."""
from curriculum.skills import (
    SKILLS, get_skill, get_skills_for_grade,
    get_all_skill_ids, get_starter_skills,
)


class TestSkillStructure:
    def test_total_skill_count(self):
        assert len(SKILLS) == 40

    def test_skills_per_grade(self):
        for grade in [1, 2, 3, 4]:
            skills = get_skills_for_grade(grade)
            assert len(skills) == 10, f"Grade {grade} has {len(skills)} skills, expected 10"

    def test_each_skill_has_required_fields(self):
        required = {'id', 'name', 'grade', 'domain', 'prerequisites'}
        for skill_id, skill in SKILLS.items():
            missing = required - set(skill.keys())
            assert not missing, f"Skill {skill_id} missing fields: {missing}"

    def test_skill_id_matches_key(self):
        for skill_id, skill in SKILLS.items():
            assert skill['id'] == skill_id

    def test_grades_are_valid(self):
        for skill_id, skill in SKILLS.items():
            assert skill['grade'] in [1, 2, 3, 4], f"{skill_id} has invalid grade"

    def test_prerequisites_exist(self):
        all_ids = set(SKILLS.keys())
        for skill_id, skill in SKILLS.items():
            for prereq in skill['prerequisites']:
                assert prereq in all_ids, \
                    f"{skill_id} has nonexistent prerequisite: {prereq}"

    def test_no_self_prerequisites(self):
        for skill_id, skill in SKILLS.items():
            assert skill_id not in skill['prerequisites'], \
                f"{skill_id} lists itself as a prerequisite"

    def test_prerequisites_are_lower_or_same_grade(self):
        for skill_id, skill in SKILLS.items():
            for prereq in skill['prerequisites']:
                prereq_grade = SKILLS[prereq]['grade']
                assert prereq_grade <= skill['grade'], \
                    f"{skill_id} (grade {skill['grade']}) has prerequisite " \
                    f"{prereq} (grade {prereq_grade})"

    def test_no_circular_prerequisites(self):
        """Verify the prerequisite graph is a DAG (no cycles)."""
        visited = set()
        path = set()

        def dfs(skill_id):
            if skill_id in path:
                raise AssertionError(f"Circular prerequisite detected: {skill_id}")
            if skill_id in visited:
                return
            path.add(skill_id)
            for prereq in SKILLS[skill_id]['prerequisites']:
                dfs(prereq)
            path.remove(skill_id)
            visited.add(skill_id)

        for skill_id in SKILLS:
            dfs(skill_id)


class TestSkillLookups:
    def test_get_skill(self):
        skill = get_skill('g1_add_10')
        assert skill is not None
        assert skill['name'] == 'Addition within 10'

    def test_get_skill_missing(self):
        assert get_skill('nonexistent') is None

    def test_get_all_skill_ids(self):
        ids = get_all_skill_ids()
        assert len(ids) == 40
        assert 'g1_add_10' in ids

    def test_get_starter_skills(self):
        starters = get_starter_skills()
        assert len(starters) > 0
        for s in starters:
            assert s['prerequisites'] == []
            assert s['grade'] == 1  # all starters should be grade 1

    def test_grade_1_has_starters(self):
        """Grade 1 must have at least some skills with no prerequisites."""
        g1 = get_skills_for_grade(1)
        starters = [s for s in g1 if not s['prerequisites']]
        assert len(starters) >= 4, "Need enough grade 1 entry points"
