"""Mora v2 — All 40 math skills defined in code.

Each skill has:
  id:            unique string key (used in DB as skill_id)
  name:          human-readable name
  grade:         1-4
  domain:        math sub-domain
  prerequisites: list of skill IDs that must be mastered first
"""

SKILLS = {
    # ── Grade 1 ──────────────────────────────────────────────
    'g1_add_10': {
        'id': 'g1_add_10',
        'name': 'Addition within 10',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': [],
    },
    'g1_sub_10': {
        'id': 'g1_sub_10',
        'name': 'Subtraction within 10',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': [],
    },
    'g1_add_20': {
        'id': 'g1_add_20',
        'name': 'Addition within 20',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': ['g1_add_10'],
    },
    'g1_sub_20': {
        'id': 'g1_sub_20',
        'name': 'Subtraction within 20',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': ['g1_sub_10'],
    },
    'g1_place_value': {
        'id': 'g1_place_value',
        'name': 'Place value (tens and ones)',
        'grade': 1,
        'domain': 'number_sense',
        'prerequisites': [],
    },
    'g1_counting': {
        'id': 'g1_counting',
        'name': 'Counting to 120',
        'grade': 1,
        'domain': 'number_sense',
        'prerequisites': [],
    },
    'g1_comparing': {
        'id': 'g1_comparing',
        'name': 'Comparing numbers',
        'grade': 1,
        'domain': 'number_sense',
        'prerequisites': ['g1_counting'],
    },
    'g1_time': {
        'id': 'g1_time',
        'name': 'Telling time (hour and half-hour)',
        'grade': 1,
        'domain': 'measurement',
        'prerequisites': [],
    },
    'g1_shapes': {
        'id': 'g1_shapes',
        'name': 'Basic shapes',
        'grade': 1,
        'domain': 'geometry',
        'prerequisites': [],
    },
    'g1_word_problems': {
        'id': 'g1_word_problems',
        'name': 'Word problems (add/sub)',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': ['g1_add_20', 'g1_sub_20'],
    },

    # ── Grade 2 ──────────────────────────────────────────────
    'g2_add_sub_100': {
        'id': 'g2_add_sub_100',
        'name': 'Add/sub with regrouping (within 100)',
        'grade': 2,
        'domain': 'operations',
        'prerequisites': ['g1_add_20', 'g1_sub_20'],
    },
    'g2_add_sub_1000': {
        'id': 'g2_add_sub_1000',
        'name': 'Add/sub within 1000',
        'grade': 2,
        'domain': 'operations',
        'prerequisites': ['g2_add_sub_100'],
    },
    'g2_intro_multiply': {
        'id': 'g2_intro_multiply',
        'name': 'Intro multiplication (equal groups)',
        'grade': 2,
        'domain': 'operations',
        'prerequisites': ['g1_add_20'],
    },
    'g2_money': {
        'id': 'g2_money',
        'name': 'Money (coins and change)',
        'grade': 2,
        'domain': 'measurement',
        'prerequisites': ['g2_add_sub_100'],
    },
    'g2_time': {
        'id': 'g2_time',
        'name': 'Telling time to 5 minutes',
        'grade': 2,
        'domain': 'measurement',
        'prerequisites': ['g1_time'],
    },
    'g2_measurement': {
        'id': 'g2_measurement',
        'name': 'Measurement (length)',
        'grade': 2,
        'domain': 'measurement',
        'prerequisites': ['g1_comparing'],
    },
    'g2_fractions_intro': {
        'id': 'g2_fractions_intro',
        'name': 'Fractions intro (halves, thirds, fourths)',
        'grade': 2,
        'domain': 'fractions',
        'prerequisites': ['g1_shapes'],
    },
    'g2_comparing_3digit': {
        'id': 'g2_comparing_3digit',
        'name': 'Comparing 3-digit numbers',
        'grade': 2,
        'domain': 'number_sense',
        'prerequisites': ['g1_comparing', 'g1_place_value'],
    },
    'g2_two_step': {
        'id': 'g2_two_step',
        'name': 'Two-step word problems',
        'grade': 2,
        'domain': 'operations',
        'prerequisites': ['g1_word_problems', 'g2_add_sub_100'],
    },
    'g2_odd_even': {
        'id': 'g2_odd_even',
        'name': 'Odd and even numbers',
        'grade': 2,
        'domain': 'number_sense',
        'prerequisites': ['g1_counting'],
    },

    # ── Grade 3 ──────────────────────────────────────────────
    'g3_mult_facts': {
        'id': 'g3_mult_facts',
        'name': 'Multiplication facts (0-12)',
        'grade': 3,
        'domain': 'operations',
        'prerequisites': ['g2_intro_multiply'],
    },
    'g3_div_facts': {
        'id': 'g3_div_facts',
        'name': 'Division facts (0-12)',
        'grade': 3,
        'domain': 'operations',
        'prerequisites': ['g3_mult_facts'],
    },
    'g3_multi_digit_mult': {
        'id': 'g3_multi_digit_mult',
        'name': 'Multi-digit multiply (2x1 digit)',
        'grade': 3,
        'domain': 'operations',
        'prerequisites': ['g3_mult_facts'],
    },
    'g3_area_perimeter': {
        'id': 'g3_area_perimeter',
        'name': 'Area and perimeter',
        'grade': 3,
        'domain': 'measurement',
        'prerequisites': ['g3_mult_facts', 'g2_measurement'],
    },
    'g3_fraction_compare': {
        'id': 'g3_fraction_compare',
        'name': 'Fraction comparison and equivalence',
        'grade': 3,
        'domain': 'fractions',
        'prerequisites': ['g2_fractions_intro'],
    },
    'g3_fraction_add_sub': {
        'id': 'g3_fraction_add_sub',
        'name': 'Fraction add/sub (same denominator)',
        'grade': 3,
        'domain': 'fractions',
        'prerequisites': ['g3_fraction_compare'],
    },
    'g3_rounding': {
        'id': 'g3_rounding',
        'name': 'Rounding',
        'grade': 3,
        'domain': 'number_sense',
        'prerequisites': ['g2_comparing_3digit'],
    },
    'g3_mult_div_word': {
        'id': 'g3_mult_div_word',
        'name': 'Mult/div word problems',
        'grade': 3,
        'domain': 'operations',
        'prerequisites': ['g3_mult_facts', 'g3_div_facts'],
    },
    'g3_elapsed_time': {
        'id': 'g3_elapsed_time',
        'name': 'Elapsed time',
        'grade': 3,
        'domain': 'measurement',
        'prerequisites': ['g2_time'],
    },
    'g3_data': {
        'id': 'g3_data',
        'name': 'Data interpretation',
        'grade': 3,
        'domain': 'data',
        'prerequisites': ['g2_add_sub_100'],
    },

    # ── Grade 4 ──────────────────────────────────────────────
    'g4_multi_digit_mult': {
        'id': 'g4_multi_digit_mult',
        'name': 'Multi-digit multiply (2x2 digit)',
        'grade': 4,
        'domain': 'operations',
        'prerequisites': ['g3_multi_digit_mult'],
    },
    'g4_long_division': {
        'id': 'g4_long_division',
        'name': 'Long division',
        'grade': 4,
        'domain': 'operations',
        'prerequisites': ['g3_div_facts'],
    },
    'g4_fraction_ops': {
        'id': 'g4_fraction_ops',
        'name': 'Fraction operations (unlike denominators)',
        'grade': 4,
        'domain': 'fractions',
        'prerequisites': ['g3_fraction_add_sub'],
    },
    'g4_decimal_place_value': {
        'id': 'g4_decimal_place_value',
        'name': 'Decimal place value',
        'grade': 4,
        'domain': 'number_sense',
        'prerequisites': ['g3_fraction_compare'],
    },
    'g4_decimal_add_sub': {
        'id': 'g4_decimal_add_sub',
        'name': 'Decimal add/sub',
        'grade': 4,
        'domain': 'operations',
        'prerequisites': ['g4_decimal_place_value'],
    },
    'g4_angles': {
        'id': 'g4_angles',
        'name': 'Angles',
        'grade': 4,
        'domain': 'geometry',
        'prerequisites': ['g1_shapes'],
    },
    'g4_geometry': {
        'id': 'g4_geometry',
        'name': 'Geometry (parallel and perpendicular)',
        'grade': 4,
        'domain': 'geometry',
        'prerequisites': ['g4_angles'],
    },
    'g4_factors_multiples': {
        'id': 'g4_factors_multiples',
        'name': 'Factors and multiples',
        'grade': 4,
        'domain': 'number_sense',
        'prerequisites': ['g3_mult_facts', 'g3_div_facts'],
    },
    'g4_multi_step_word': {
        'id': 'g4_multi_step_word',
        'name': 'Multi-step word problems',
        'grade': 4,
        'domain': 'operations',
        'prerequisites': ['g3_mult_div_word', 'g4_multi_digit_mult'],
    },
    'g4_equivalent_fractions': {
        'id': 'g4_equivalent_fractions',
        'name': 'Equivalent fractions',
        'grade': 4,
        'domain': 'fractions',
        'prerequisites': ['g3_fraction_compare'],
    },
}


def get_skill(skill_id):
    """Return a single skill dict by ID, or None."""
    return SKILLS.get(skill_id)


def get_skills_for_grade(grade):
    """Return list of skills for a given grade."""
    return [s for s in SKILLS.values() if s['grade'] == grade]


def get_all_skill_ids():
    """Return all skill IDs."""
    return list(SKILLS.keys())


def get_starter_skills():
    """Return skills with no prerequisites (grade 1 entry points)."""
    return [s for s in SKILLS.values() if not s['prerequisites']]
