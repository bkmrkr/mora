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
        'tip': 'Try counting on from the bigger number using your fingers.',
    },
    'g1_sub_10': {
        'id': 'g1_sub_10',
        'name': 'Subtraction within 10',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': [],
        'tip': 'Start at the bigger number and count backwards.',
    },
    'g1_add_20': {
        'id': 'g1_add_20',
        'name': 'Addition within 20',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': ['g1_add_10'],
        'tip': 'Make a ten first, then add what\'s left.',
    },
    'g1_sub_20': {
        'id': 'g1_sub_20',
        'name': 'Subtraction within 20',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': ['g1_sub_10'],
        'tip': 'Break it into steps: subtract to 10, then subtract the rest.',
    },
    'g1_place_value': {
        'id': 'g1_place_value',
        'name': 'Place value (tens and ones)',
        'grade': 1,
        'domain': 'number_sense',
        'prerequisites': [],
        'tip': 'The left digit tells tens, the right digit tells ones.',
    },
    'g1_counting': {
        'id': 'g1_counting',
        'name': 'Counting to 120',
        'grade': 1,
        'domain': 'number_sense',
        'prerequisites': [],
        'tip': 'Look for patterns — after 9 comes 0 with the next ten.',
    },
    'g1_comparing': {
        'id': 'g1_comparing',
        'name': 'Comparing numbers',
        'grade': 1,
        'domain': 'number_sense',
        'prerequisites': ['g1_counting'],
        'tip': 'Compare the tens digit first. If they match, compare the ones.',
    },
    'g1_time': {
        'id': 'g1_time',
        'name': 'Telling time (hour and half-hour)',
        'grade': 1,
        'domain': 'measurement',
        'prerequisites': [],
        'tip': 'The short hand shows the hour. If the long hand points to 6, it\'s half past.',
    },
    'g1_shapes': {
        'id': 'g1_shapes',
        'name': 'Basic shapes',
        'grade': 1,
        'domain': 'geometry',
        'prerequisites': [],
        'tip': 'Count the sides and corners — each shape has a unique number.',
    },
    'g1_word_problems': {
        'id': 'g1_word_problems',
        'name': 'Word problems (add/sub)',
        'grade': 1,
        'domain': 'operations',
        'prerequisites': ['g1_add_20', 'g1_sub_20'],
        'tip': 'Read carefully: "in all" or "total" means add. "Left" or "fewer" means subtract.',
    },

    # ── Grade 2 ──────────────────────────────────────────────
    'g2_add_sub_100': {
        'id': 'g2_add_sub_100',
        'name': 'Add/sub with regrouping (within 100)',
        'grade': 2,
        'domain': 'operations',
        'prerequisites': ['g1_add_20', 'g1_sub_20'],
        'tip': 'Line up the ones, then the tens. Regroup when a column goes over 9.',
    },
    'g2_add_sub_1000': {
        'id': 'g2_add_sub_1000',
        'name': 'Add/sub within 1000',
        'grade': 2,
        'domain': 'operations',
        'prerequisites': ['g2_add_sub_100'],
        'tip': 'Work column by column from right to left: ones, tens, hundreds.',
    },
    'g2_intro_multiply': {
        'id': 'g2_intro_multiply',
        'name': 'Intro multiplication (equal groups)',
        'grade': 2,
        'domain': 'operations',
        'prerequisites': ['g1_add_20'],
        'tip': 'Multiplication is repeated addition: 3 x 4 means 4 + 4 + 4.',
    },
    'g2_money': {
        'id': 'g2_money',
        'name': 'Money (coins and change)',
        'grade': 2,
        'domain': 'measurement',
        'prerequisites': ['g2_add_sub_100'],
        'tip': 'Start with the biggest coins and count up to the total.',
    },
    'g2_time': {
        'id': 'g2_time',
        'name': 'Telling time to 5 minutes',
        'grade': 2,
        'domain': 'measurement',
        'prerequisites': ['g1_time'],
        'tip': 'Count by 5s around the clock from 12. Each number is 5 more minutes.',
    },
    'g2_measurement': {
        'id': 'g2_measurement',
        'name': 'Measurement (length)',
        'grade': 2,
        'domain': 'measurement',
        'prerequisites': ['g1_comparing'],
        'tip': 'Compare the numbers — the bigger number means longer.',
    },
    'g2_fractions_intro': {
        'id': 'g2_fractions_intro',
        'name': 'Fractions intro (halves, thirds, fourths)',
        'grade': 2,
        'domain': 'fractions',
        'prerequisites': ['g1_shapes'],
        'tip': 'The bottom number says how many equal pieces. The top says how many you have.',
    },
    'g2_comparing_3digit': {
        'id': 'g2_comparing_3digit',
        'name': 'Comparing 3-digit numbers',
        'grade': 2,
        'domain': 'number_sense',
        'prerequisites': ['g1_comparing', 'g1_place_value'],
        'tip': 'Compare hundreds first, then tens, then ones. Stop at the first difference.',
    },
    'g2_two_step': {
        'id': 'g2_two_step',
        'name': 'Two-step word problems',
        'grade': 2,
        'domain': 'operations',
        'prerequisites': ['g1_word_problems', 'g2_add_sub_100'],
        'tip': 'Solve one step at a time. Use the answer from step 1 in step 2.',
    },
    'g2_odd_even': {
        'id': 'g2_odd_even',
        'name': 'Odd and even numbers',
        'grade': 2,
        'domain': 'number_sense',
        'prerequisites': ['g1_counting'],
        'tip': 'Look at the last digit: 0, 2, 4, 6, 8 are even. 1, 3, 5, 7, 9 are odd.',
    },

    # ── Grade 3 ──────────────────────────────────────────────
    'g3_mult_facts': {
        'id': 'g3_mult_facts',
        'name': 'Multiplication facts (0-12)',
        'grade': 3,
        'domain': 'operations',
        'prerequisites': ['g2_intro_multiply'],
        'tip': 'Use skip-counting or break hard facts into easier ones: 7x8 = 7x4 + 7x4.',
    },
    'g3_div_facts': {
        'id': 'g3_div_facts',
        'name': 'Division facts (0-12)',
        'grade': 3,
        'domain': 'operations',
        'prerequisites': ['g3_mult_facts'],
        'tip': 'Division is the opposite of multiplication: if 6x7=42, then 42÷7=6.',
    },
    'g3_multi_digit_mult': {
        'id': 'g3_multi_digit_mult',
        'name': 'Multi-digit multiply (2x1 digit)',
        'grade': 3,
        'domain': 'operations',
        'prerequisites': ['g3_mult_facts'],
        'tip': 'Multiply each digit separately, then add: 34x5 = (30x5) + (4x5).',
    },
    'g3_area_perimeter': {
        'id': 'g3_area_perimeter',
        'name': 'Area and perimeter',
        'grade': 3,
        'domain': 'measurement',
        'prerequisites': ['g3_mult_facts', 'g2_measurement'],
        'tip': 'Perimeter = add all sides. Area = length x width.',
    },
    'g3_fraction_compare': {
        'id': 'g3_fraction_compare',
        'name': 'Fraction comparison and equivalence',
        'grade': 3,
        'domain': 'fractions',
        'prerequisites': ['g2_fractions_intro'],
        'tip': 'Same denominator? Compare tops. Same numerator? Smaller bottom = bigger piece.',
    },
    'g3_fraction_add_sub': {
        'id': 'g3_fraction_add_sub',
        'name': 'Fraction add/sub (same denominator)',
        'grade': 3,
        'domain': 'fractions',
        'prerequisites': ['g3_fraction_compare'],
        'tip': 'Same denominator: add or subtract the tops, keep the bottom the same.',
    },
    'g3_rounding': {
        'id': 'g3_rounding',
        'name': 'Rounding',
        'grade': 3,
        'domain': 'number_sense',
        'prerequisites': ['g2_comparing_3digit'],
        'tip': 'Look at the digit to the right: 5 or more rounds up, 4 or less rounds down.',
    },
    'g3_mult_div_word': {
        'id': 'g3_mult_div_word',
        'name': 'Mult/div word problems',
        'grade': 3,
        'domain': 'operations',
        'prerequisites': ['g3_mult_facts', 'g3_div_facts'],
        'tip': '"Each" or "every" often means multiply. "Share equally" means divide.',
    },
    'g3_elapsed_time': {
        'id': 'g3_elapsed_time',
        'name': 'Elapsed time',
        'grade': 3,
        'domain': 'measurement',
        'prerequisites': ['g2_time'],
        'tip': 'Count forward from the start time to the end time in hours, then minutes.',
    },
    'g3_data': {
        'id': 'g3_data',
        'name': 'Data interpretation',
        'grade': 3,
        'domain': 'data',
        'prerequisites': ['g2_add_sub_100'],
        'tip': 'Read the labels and scale carefully before answering.',
    },

    # ── Grade 4 ──────────────────────────────────────────────
    'g4_multi_digit_mult': {
        'id': 'g4_multi_digit_mult',
        'name': 'Multi-digit multiply (2x2 digit)',
        'grade': 4,
        'domain': 'operations',
        'prerequisites': ['g3_multi_digit_mult'],
        'tip': 'Multiply by ones, then by tens, then add the two results.',
    },
    'g4_long_division': {
        'id': 'g4_long_division',
        'name': 'Long division',
        'grade': 4,
        'domain': 'operations',
        'prerequisites': ['g3_div_facts'],
        'tip': 'Divide, Multiply, Subtract, Bring down — repeat for each digit.',
    },
    'g4_fraction_ops': {
        'id': 'g4_fraction_ops',
        'name': 'Fraction operations (unlike denominators)',
        'grade': 4,
        'domain': 'fractions',
        'prerequisites': ['g3_fraction_add_sub'],
        'tip': 'Find a common denominator first, then add or subtract the numerators.',
    },
    'g4_decimal_place_value': {
        'id': 'g4_decimal_place_value',
        'name': 'Decimal place value',
        'grade': 4,
        'domain': 'number_sense',
        'prerequisites': ['g3_fraction_compare'],
        'tip': 'After the decimal: tenths, hundredths, thousandths — each spot is 10x smaller.',
    },
    'g4_decimal_add_sub': {
        'id': 'g4_decimal_add_sub',
        'name': 'Decimal add/sub',
        'grade': 4,
        'domain': 'operations',
        'prerequisites': ['g4_decimal_place_value'],
        'tip': 'Line up the decimal points, then add or subtract as usual.',
    },
    'g4_angles': {
        'id': 'g4_angles',
        'name': 'Angles',
        'grade': 4,
        'domain': 'geometry',
        'prerequisites': ['g1_shapes'],
        'tip': 'A right angle is 90°. Acute is less, obtuse is more.',
    },
    'g4_geometry': {
        'id': 'g4_geometry',
        'name': 'Geometry (parallel and perpendicular)',
        'grade': 4,
        'domain': 'geometry',
        'prerequisites': ['g4_angles'],
        'tip': 'Parallel lines never meet. Perpendicular lines form a 90° angle.',
    },
    'g4_factors_multiples': {
        'id': 'g4_factors_multiples',
        'name': 'Factors and multiples',
        'grade': 4,
        'domain': 'number_sense',
        'prerequisites': ['g3_mult_facts', 'g3_div_facts'],
        'tip': 'Factors divide evenly into the number. Multiples are the number times 1, 2, 3...',
    },
    'g4_multi_step_word': {
        'id': 'g4_multi_step_word',
        'name': 'Multi-step word problems',
        'grade': 4,
        'domain': 'operations',
        'prerequisites': ['g3_mult_div_word', 'g4_multi_digit_mult'],
        'tip': 'Break the problem into smaller steps. Solve each step before moving on.',
    },
    'g4_equivalent_fractions': {
        'id': 'g4_equivalent_fractions',
        'name': 'Equivalent fractions',
        'grade': 4,
        'domain': 'fractions',
        'prerequisites': ['g3_fraction_compare'],
        'tip': 'Multiply or divide top and bottom by the same number to get equivalent fractions.',
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
