"""BabyDuck scanner (PLY lex): tokens and regular expressions."""
import ply.lex as lex

# Keywords: matched by t_ID, then re-typed with this table.
reserved = {
    'program': 'PROGRAM', 'main': 'MAIN', 'end': 'END', 'var': 'VAR',
    'int': 'INT', 'float': 'FLOAT', 'void': 'VOID', 'print': 'PRINT',
    'read': 'READ', 'while': 'WHILE', 'if': 'IF', 'else': 'ELSE',
    'return': 'RETURN',
}

tokens = [
    'ID', 'CTE_INT', 'CTE_FLOAT', 'CTE_STRING',
    # operators
    'ASSIGN', 'PLUS', 'MINUS', 'MULT', 'DIV',
    'GT', 'LT', 'NE', 'EQ', 'GE', 'LE',
    # delimiters
    'SEMICOLON', 'COMMA', 'COLON', 'LPAREN', 'RPAREN',
    'LBRACE', 'RBRACE',
] + list(reserved.values())

# Simple tokens. PLY tries them longest regex first, so '==' beats '='.
t_NE = r'!='
t_EQ = r'=='
t_GE = r'>='
t_LE = r'<='
t_ASSIGN = r'='
t_PLUS = r'\+'
t_MINUS = r'-'
t_MULT = r'\*'
t_DIV = r'/'
t_GT = r'>'
t_LT = r'<'
t_SEMICOLON = r';'
t_COMMA = r','
t_COLON = r':'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'

t_ignore = ' \t\r'              # spaces and tabs
t_ignore_COMMENT = r'//[^\n]*'  # // comments


# Function tokens are tried in file order: CTE_FLOAT must come before CTE_INT.
def t_CTE_FLOAT(t):
    r'[0-9]+\.[0-9]+'
    t.value = float(t.value)
    return t


def t_CTE_INT(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t


def t_CTE_STRING(t):
    r'"[^"\n]*"'
    return t


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t


def t_newline(t):
    r'\n+'
    # Counts lines; returns nothing, so newlines are not tokens.
    t.lexer.lineno += len(t.value)


def t_error(t):
    raise SyntaxError(
        f"Lexical error: illegal character {t.value[0]!r} at line {t.lineno}")


def build_lexer():
    return lex.lex()


def tokenize(source):
    """Return (type, value, line) for every token. Used by --tokens and tests."""
    lexer = build_lexer()
    lexer.input(source)
    return [(tok.type, tok.value, tok.lineno) for tok in lexer]
