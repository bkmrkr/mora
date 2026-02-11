"""Replace the auto-generated 1st Grade Math curriculum with a comprehensive
31-node curriculum covering the full NJ first grade math standards (NJSLS).

Domains covered:
  - Operations and Algebraic Thinking (10 nodes)
  - Number and Operations in Base Ten (8 nodes)
  - Measurement (6 nodes)
  - Data Literacy (2 nodes)
  - Geometry (5 nodes)

Run from project root: python3 scripts/seed_1st_grade_math.py
"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_PATH

TOPIC_ID = 3
TOPIC_NAME = '1st Grade Math'
TOPIC_DESC = (
    'Comprehensive first grade mathematics curriculum aligned with the '
    '2023 New Jersey Student Learning Standards (NJSLS). Covers operations '
    'and algebraic thinking, number and operations in base ten, measurement, '
    'data literacy, and geometry. Emphasizes conceptual understanding, '
    'procedural fluency within 10, and real-world application through '
    'word problems, money, time, and shapes.'
)

# Each node: (name, description, order, prerequisite_indices[])
# prerequisite_indices reference 0-based position in this list
NODES = [
    # === OPERATIONS AND ALGEBRAIC THINKING (OA) ===
    (
        'Addition Within 10',
        'Basic addition facts with sums up to 10. Use strategies like counting on, '
        'counting all, using fingers or objects. Examples: 3+2=5, 4+6=10, 0+7=7. '
        'Include adding zero. Use pictures of objects (apples, stars, blocks) to '
        'represent addition. Word form: "3 plus 4 equals what?"',
        1, [],
    ),
    (
        'Subtraction Within 10',
        'Basic subtraction facts within 10. Take away objects to find the difference. '
        'Examples: 8-3=5, 10-4=6, 7-0=7. Include subtracting zero. '
        'Relate to taking away from a group. Use pictures and number sentences.',
        2, [0],  # prereq: Addition Within 10
    ),
    (
        'Addition and Subtraction Fluency Within 10',
        'Fast, accurate recall of all addition and subtraction facts within 10. '
        'Mixed practice: 6+4, 9-3, 5+5, 10-7. Students should answer without '
        'counting — automatic recall. Timed-style practice. Include fact families: '
        'if 3+4=7, then 4+3=7, 7-3=4, 7-4=3.',
        3, [0, 1],
    ),
    (
        'Addition Within 20',
        'Addition with sums from 11 to 20. Strategies: making ten (8+6 → 8+2+4 = 10+4 = 14), '
        'doubles (7+7=14), near doubles (7+8 = 7+7+1 = 15), counting on from the larger number. '
        'Decompose numbers to make a ten. Use ten-frames and number lines. '
        'Examples: 9+5=14, 8+7=15, 6+9=15.',
        4, [2],
    ),
    (
        'Subtraction Within 20',
        'Subtraction with minuends up to 20. Use relationship to addition: '
        'to solve 15-8, think "8 + what = 15?" Decompose: 13-5 = 13-3-2 = 10-2 = 8. '
        'Count back or count up strategies. Use number lines. '
        'Examples: 14-6=8, 17-9=8, 20-5=15.',
        5, [3],
    ),
    (
        'Three Addends',
        'Add three whole numbers with a sum of 20 or less. '
        'Look for pairs that make 10 first: 4+6+3 → (4+6)+3 = 10+3 = 13. '
        'Use doubles: 5+5+2 = 10+2 = 12. Any grouping gives the same sum (associative property). '
        'Examples: 2+8+5=15, 3+3+4=10, 7+1+3=11.',
        6, [3],
    ),
    (
        'Word Problems: Add To and Take From',
        'Solve addition and subtraction word problems with result unknown, change unknown, '
        'or start unknown. "Add to" example: "Sam had 5 stickers. He got 3 more. '
        'How many now?" (5+3=8). "Take from" example: "There were 12 birds. 4 flew away. '
        'How many are left?" (12-4=8). Use drawings, objects, or equations to solve. '
        'Include missing addend: "Ella had 6 apples. She picked some more. Now she has 11. '
        'How many did she pick?" (6+?=11).',
        7, [4, 5],
    ),
    (
        'Word Problems: Compare and Put Together',
        'Solve comparison and put-together/take-apart word problems. '
        '"Compare" example: "Tom has 9 cars. Mia has 5 cars. How many more does Tom have?" '
        '(9-5=4). "Put together" example: "There are 6 red balls and 8 blue balls. '
        'How many balls in all?" (6+8=14). Include unknowns in all positions. '
        'Encourage drawing bar models or using equations.',
        8, [6],
    ),
    (
        'Understanding the Equal Sign',
        'The equal sign means "the same as," not "the answer is coming." '
        'Determine if equations are true or false: Is 6=6 true? (yes). '
        'Is 7=8-1 true? (yes). Is 5+2=6 true? (no). '
        'Equations can have expressions on both sides: 4+3 = 2+5 (both equal 7, so true). '
        'Read equations left to right and right to left.',
        9, [2],
    ),
    (
        'Unknown Number in Equations',
        'Find the missing number that makes an equation true. '
        'Use a box, question mark, or blank for the unknown. '
        'Examples: 8 + ? = 11 (answer: 3). 5 = □ - 3 (answer: 8). '
        '? + 4 = 10 (answer: 6). 14 - □ = 9 (answer: 5). '
        'Relate to fact families and inverse operations.',
        10, [8, 4],
    ),

    # === NUMBER AND OPERATIONS IN BASE TEN (NBT) ===
    (
        'Counting to 120',
        'Count forward from any number less than 120. Read and write numbers '
        'from 0 to 120. Represent numbers with objects or drawings. '
        'Count by ones starting from various starting points: "Start at 67 and count to 75." '
        'Read number words: twenty-three, forty-one, one hundred twelve. '
        'Write the numeral when given the word or a quantity.',
        11, [0],
    ),
    (
        'Understanding Tens and Ones',
        'A two-digit number is made of tens and ones. 10 ones = 1 ten. '
        'Use base-10 blocks: a rod = 10, a unit = 1. '
        'Example: 34 = 3 tens and 4 ones. Multiples of 10 (10, 20, 30, ..., 90) '
        'are some number of tens and 0 ones. 10 = 1 ten, 50 = 5 tens, 90 = 9 tens.',
        12, [10],
    ),
    (
        'Teen Numbers as Ten Plus Ones',
        'Numbers 11-19 are composed of one ten and some ones. '
        '11 = 10 + 1, 12 = 10 + 2, ..., 19 = 10 + 9. '
        'Decompose teens: "How many tens and ones in 15?" → 1 ten and 5 ones. '
        'Use ten-frames to show: one full frame (10) plus extra ones.',
        13, [11],
    ),
    (
        'Comparing Two-Digit Numbers',
        'Compare two 2-digit numbers using >, =, <. '
        'First compare the tens digit; if equal, compare the ones digit. '
        'Example: 52 > 45 (5 tens > 4 tens). 38 < 41 (3 tens < 4 tens). '
        '67 = 67. Record comparisons with symbols. '
        'Use place value reasoning to explain: "72 > 68 because 7 tens is more than 6 tens."',
        14, [11, 12],
    ),
    (
        'Adding a Two-Digit and One-Digit Number',
        'Add a two-digit number and a one-digit number within 100. '
        'Use place value: add ones to ones, keep tens. '
        'When ones sum > 9, compose a new ten: 37 + 5 = 30 + 7 + 5 = 30 + 12 = 42. '
        'Use number lines, base-10 blocks, and drawings. '
        'Examples: 24 + 3 = 27, 45 + 8 = 53, 66 + 7 = 73.',
        15, [3, 12],
    ),
    (
        'Adding a Two-Digit Number and a Multiple of 10',
        'Add a two-digit number and a multiple of 10. '
        'Only the tens digit changes: 34 + 20 = 54, 47 + 30 = 77. '
        'Use place value understanding: add tens to tens, ones stay the same. '
        'Use base-10 blocks: add rods to rods. '
        'Examples: 15 + 40 = 55, 63 + 20 = 83, 28 + 50 = 78.',
        16, [11, 12],
    ),
    (
        'Mental Math: 10 More and 10 Less',
        'Mentally find 10 more or 10 less than any two-digit number. '
        'The ones digit stays the same, only the tens digit changes. '
        '10 more than 43 = 53. 10 less than 67 = 57. '
        'Explain reasoning: "The tens digit goes up/down by 1." '
        'Use a hundreds chart to see the pattern. '
        'Examples: 10 more than 85 = 95, 10 less than 31 = 21.',
        17, [12],
    ),
    (
        'Subtracting Multiples of 10',
        'Subtract multiples of 10 from multiples of 10, within 90. '
        'Examples: 70 - 30 = 40, 50 - 20 = 30, 90 - 60 = 30. '
        'Think in terms of tens: 7 tens - 3 tens = 4 tens = 40. '
        'Use base-10 blocks (remove rods) and number lines.',
        18, [11, 16],
    ),

    # === MEASUREMENT (M) ===
    (
        'Comparing and Ordering Lengths',
        'Order 3 objects from shortest to longest or longest to shortest. '
        'Compare lengths of two objects indirectly using a third object: '
        'if pencil A is longer than string and string is longer than pencil B, '
        'then pencil A is longer than pencil B. Use words: longer, shorter, taller, '
        'same length. "Which is longer, the crayon or the marker?"',
        19, [],
    ),
    (
        'Measuring Length with Units',
        'Measure the length of an object by laying identical smaller units '
        'end-to-end with no gaps or overlaps. Express length as a whole number '
        'of units. Example: "The book is 8 paper clips long." '
        'Understand that using smaller units gives a larger number. '
        'Units must be the same size.',
        20, [18],
    ),
    (
        'Telling Time to the Hour',
        'Read and write times to the hour on analog and digital clocks. '
        'The short hand (hour hand) points to the hour number. '
        'The long hand (minute hand) points to 12 for "o\'clock." '
        'Write as 3:00, 7:00, 12:00. Say "three o\'clock." '
        'CLOCK_VISUAL: tell time to the hour',
        21, [],
    ),
    (
        'Telling Time to the Half Hour',
        'Read and write times to the half hour on analog and digital clocks. '
        'At half past, the minute hand points to 6 and the hour hand is '
        'between two numbers. Write as 3:30, 7:30, 12:30. '
        'Say "half past three" or "three thirty." '
        'CLOCK_VISUAL: tell time to half and quarter',
        22, [20],
    ),
    (
        'Coin Values and Recognition',
        'Identify coins: penny (1¢), nickel (5¢), dime (10¢), quarter (25¢). '
        'Know the value of each coin. Recognize front and back of each coin. '
        'Compare values: a dime is worth more than a nickel. '
        'Use cent notation (¢). Count collections of same coins: '
        '3 nickels = 15¢, 4 dimes = 40¢.',
        23, [0],
    ),
    (
        'Money: Dollar Values and Problems',
        'Use dollar notation ($). Know $1 = 100¢. '
        'Solve problems with money up to $20. Find equivalent values: '
        '25¢ = 2 dimes + 1 nickel = 5 nickels = 1 quarter. '
        'Count mixed coins: 1 quarter + 2 dimes + 1 nickel = 50¢. '
        'Add money amounts: $5 + $3 = $8. Make change from simple amounts.',
        24, [22, 3],
    ),

    # === DATA LITERACY (D) ===
    (
        'Organizing and Reading Data',
        'Organize data into categories (up to 3 categories). '
        'Create and read tally charts, pictographs, and simple bar graphs. '
        'Example: "We asked classmates about favorite fruit. 5 chose apple, '
        '3 chose banana, 7 chose grape." Read data from a chart: '
        '"How many chose banana?" Answer: 3.',
        25, [0],
    ),
    (
        'Interpreting Data and Answering Questions',
        'Use data from charts, pictographs, and bar graphs to answer questions. '
        '"How many total votes?" (add all categories). '
        '"How many more chose grape than banana?" (7-3=4). '
        '"How many fewer chose apple than grape?" (7-5=2). '
        'Compare categories. Find the most and least popular. '
        'Requires addition and subtraction skills.',
        26, [24, 4],
    ),

    # === GEOMETRY (G) ===
    (
        'Defining Attributes of Shapes',
        'Shapes have defining attributes (number of sides, corners, whether they are '
        'closed) and non-defining attributes (color, size, orientation). '
        'A triangle always has 3 sides and 3 corners — it can be any color or size. '
        'A rectangle has 4 sides and 4 square corners. A circle has no straight sides. '
        '"Is this a triangle?" based on sides and corners, not appearance.',
        27, [],
    ),
    (
        '2D Shapes',
        'Identify and describe 2D (flat) shapes: circle, triangle, square, rectangle, '
        'trapezoid, hexagon. Count sides and corners. A square is a special rectangle. '
        'Draw shapes given attributes: "Draw a shape with 4 equal sides." '
        'Sort shapes by number of sides. Recognize shapes in different orientations.',
        28, [26],
    ),
    (
        '3D Shapes',
        'Identify and describe 3D (solid) shapes: cube, rectangular prism (box), '
        'cone, cylinder, sphere. Describe using faces, edges, vertices. '
        'A cube has 6 square faces. A cylinder has 2 circular faces and a curved surface. '
        'Find 3D shapes in real life: a can is a cylinder, a ball is a sphere, '
        'a box is a rectangular prism.',
        29, [27],
    ),
    (
        'Composing Shapes',
        'Combine 2D shapes to make larger shapes: two triangles make a square, '
        'two squares make a rectangle. Combine 3D shapes to make structures. '
        'Use tangram-style puzzles. Identify which smaller shapes make up a composite shape. '
        '"What shapes do you see in this figure?" "How can you make a hexagon using triangles?"',
        30, [27, 28],
    ),
    (
        'Partitioning into Equal Shares',
        'Divide circles and rectangles into 2 equal shares (halves) or '
        '4 equal shares (fourths/quarters). Use the words: halves, half of, '
        'fourths, quarters, quarter of. Understand that 4 equal shares are '
        'smaller than 2 equal shares of the same whole. '
        '"If you cut a pizza into 4 equal pieces, each piece is one fourth." '
        '"Splitting equally means each part is the same size."',
        31, [27],
    ),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    cur = conn.cursor()

    # Check current state
    cur.execute('SELECT COUNT(*) FROM curriculum_nodes WHERE topic_id=?', (TOPIC_ID,))
    old_count = cur.fetchone()[0]

    # Clean up old data for topic 3 (order matters for foreign keys)
    cur.execute('''DELETE FROM attempts WHERE question_id IN (
        SELECT q.id FROM questions q
        JOIN curriculum_nodes cn ON q.curriculum_node_id = cn.id
        WHERE cn.topic_id = ?)''', (TOPIC_ID,))
    deleted_attempts = cur.rowcount

    cur.execute('''DELETE FROM questions WHERE curriculum_node_id IN (
        SELECT id FROM curriculum_nodes WHERE topic_id = ?)''', (TOPIC_ID,))
    deleted_questions = cur.rowcount

    cur.execute('''DELETE FROM student_skill WHERE curriculum_node_id IN (
        SELECT id FROM curriculum_nodes WHERE topic_id = ?)''', (TOPIC_ID,))
    deleted_skills = cur.rowcount

    cur.execute('DELETE FROM curriculum_nodes WHERE topic_id = ?', (TOPIC_ID,))
    deleted_nodes = cur.rowcount

    # Update topic description
    cur.execute('UPDATE topics SET description=? WHERE id=?', (TOPIC_DESC, TOPIC_ID))

    print(f'Cleaned up topic {TOPIC_ID}: {deleted_nodes} nodes, '
          f'{deleted_questions} questions, {deleted_attempts} attempts, '
          f'{deleted_skills} skills')

    # Insert new curriculum nodes
    node_ids = []
    for name, desc, order, _prereqs in NODES:
        cur.execute(
            '''INSERT INTO curriculum_nodes
               (topic_id, name, description, order_index, prerequisites, mastery_threshold)
               VALUES (?, ?, ?, ?, '[]', 0.75)''',
            (TOPIC_ID, name, desc, order),
        )
        node_ids.append(cur.lastrowid)

    # Resolve prerequisites (indices → actual DB IDs)
    for i, (name, desc, order, prereq_indices) in enumerate(NODES):
        if prereq_indices:
            prereq_ids = [node_ids[pi] for pi in prereq_indices]
            cur.execute(
                'UPDATE curriculum_nodes SET prerequisites=? WHERE id=?',
                (json.dumps(prereq_ids), node_ids[i]),
            )

    conn.commit()
    conn.close()

    print(f'\nInserted {len(NODES)} curriculum nodes for "{TOPIC_NAME}":')
    for i, (name, desc, order, prereqs) in enumerate(NODES):
        prereq_names = [NODES[p][0] for p in prereqs] if prereqs else []
        prefix = '  '
        if order <= 10:
            domain = 'OA'
        elif order <= 18:
            domain = 'NBT'
        elif order <= 24:
            domain = 'M'
        elif order <= 26:
            domain = 'D'
        else:
            domain = 'G'
        prereq_str = f' (prereqs: {", ".join(prereq_names)})' if prereq_names else ''
        print(f'{prefix}[{domain}] {order:2d}. {name}{prereq_str}')


if __name__ == '__main__':
    main()
