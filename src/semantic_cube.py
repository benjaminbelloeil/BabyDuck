"""BabyDuck semantic cube.

The cube answers one question:
    "If I apply operator OP to a value of type LEFT and a value of type RIGHT,
     what type is the result? Or is it an error?"

Example:  int + float  ->  float
          int = float  ->  error   (a float does not fit in an int)

Storage: one dictionary.
    key   = (left_type, operator, right_type)    a tuple
    value = the resulting type
Only VALID combinations are stored. If a key is missing, the result is ERROR.

It is not used by the parser yet. In Entrega 3 it will check every operation
in an expression and tell the compiler the type of each result.
"""


# ---------------------------------------------------------------------------
# 1. Types
# ---------------------------------------------------------------------------
# Constants instead of raw strings: a typo in a constant name crashes right
# away, a typo inside a string ('flaot') would silently create a wrong key.

INT = 'int'
FLOAT = 'float'
BOOL = 'bool'      # result of a comparison; no variable can be declared bool
ERROR = 'error'    # returned when the operation is not allowed


# ---------------------------------------------------------------------------
# 2. Operator groups
# ---------------------------------------------------------------------------
# Operators that share the same table, so each table is filled with one loop.

ARITHMETIC = ('+', '-', '*')              # table 1
ORDERING = ('>', '<', '>=', '<=')         # table 3
EQUALITY = ('==', '!=')                   # table 4
# '/' (table 2) and '=' (table 5) have their own tables.


# ---------------------------------------------------------------------------
# 3. The cube
# ---------------------------------------------------------------------------

CUBE = {}

# --- Table 1: + - * --------------------------------------------------------
# If either side is float the result is float, so no decimals are lost.
# bool is not a number: any cell with bool is missing -> error.
for op in ARITHMETIC:
    CUBE[(INT, op, INT)] = INT
    CUBE[(INT, op, FLOAT)] = FLOAT
    CUBE[(FLOAT, op, INT)] = FLOAT
    CUBE[(FLOAT, op, FLOAT)] = FLOAT

# --- Table 2: / ------------------------------------------------------------
# int / int stays int (integer division, like C: 7 / 2 = 3).
CUBE[(INT, '/', INT)] = INT
CUBE[(INT, '/', FLOAT)] = FLOAT
CUBE[(FLOAT, '/', INT)] = FLOAT
CUBE[(FLOAT, '/', FLOAT)] = FLOAT

# --- Table 3: > < >= <= ----------------------------------------------------
# Any two numbers can be compared. Ordering two bools makes no sense.
for op in ORDERING:
    for left in (INT, FLOAT):
        for right in (INT, FLOAT):
            CUBE[(left, op, right)] = BOOL

# --- Table 4: == != --------------------------------------------------------
# Same as table 3. bool == bool is left out (error) to keep the language simple.
for op in EQUALITY:
    for left in (INT, FLOAT):
        for right in (INT, FLOAT):
            CUBE[(left, op, right)] = BOOL

# --- Table 5: = ------------------------------------------------------------
# LEFT is the variable being assigned, RIGHT is the value's type.
# An int fits in a float. A float in an int would lose the decimals -> error.
# No variable can be bool, and a bool value can't be stored -> error.
CUBE[(INT, '=', INT)] = INT
CUBE[(FLOAT, '=', FLOAT)] = FLOAT
CUBE[(FLOAT, '=', INT)] = FLOAT

# --- Table 6: unary sign (+x, -x) -------------------------------------------
# Only one operand, so it gets its own small dict: (op, operand) -> result.
# The sign never changes a number's type; -bool makes no sense.
UNARY = {}
for op in ('+', '-'):
    UNARY[(op, INT)] = INT
    UNARY[(op, FLOAT)] = FLOAT


# ---------------------------------------------------------------------------
# 4. Lookup
# ---------------------------------------------------------------------------

def result_type(left, op, right):
    """Return the type of `left op right`, or ERROR if it is not allowed.

    result_type(INT, '+', FLOAT)  ->  'float'
    result_type(INT, '=', FLOAT)  ->  'error'
    """
    return CUBE.get((left, op, right), ERROR)


def unary_type(op, operand):
    """Return the type of `op operand` (e.g. -x), or ERROR."""
    return UNARY.get((op, operand), ERROR)


# ---------------------------------------------------------------------------
# Quick manual test:  python3 src/semantic_cube.py
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    checks = [
        # (left, op, right, expected)
        (INT, '+', INT, INT),
        (INT, '*', FLOAT, FLOAT),
        (BOOL, '-', INT, ERROR),
        (INT, '/', INT, INT),
        (FLOAT, '/', INT, FLOAT),
        (INT, '<', FLOAT, BOOL),
        (BOOL, '>', BOOL, ERROR),
        (FLOAT, '==', INT, BOOL),
        (BOOL, '==', BOOL, ERROR),
        (FLOAT, '=', INT, FLOAT),
        (INT, '=', FLOAT, ERROR),
        (INT, '=', BOOL, ERROR),
    ]
    for left, op, right, expected in checks:
        got = result_type(left, op, right)
        mark = 'ok' if got == expected else 'WRONG'
        print(f"{left:>5} {op:<2} {right:<5} -> {got:<5}  (expected {expected})  {mark}")
    print(f"    -{FLOAT}      -> {unary_type('-', FLOAT)}")
    print(f"    -{BOOL}       -> {unary_type('-', BOOL)}")
