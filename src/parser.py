"""BabyDuck parser (PLY yacc).

Each p_ function is one grammar rule, written in its docstring.
Nonterminals are lowercase, tokens UPPERCASE. 'empty' is epsilon.
The first rule (program) is the start symbol.
"""
import os

import ply.yacc as yacc
from lexer import tokens, build_lexer  # noqa: F401  (PLY needs `tokens` here)


# ---------------------------------------------------------------------------
# Block 1: Program, variables, functions
# ---------------------------------------------------------------------------

def p_program(p):
    'program : PROGRAM ID SEMICOLON vars_opt func_list MAIN body END'
    p[0] = 'OK'


def p_vars_opt(p):
    '''vars_opt : vars
                | empty'''


def p_func_list(p):
    '''func_list : funcs func_list
                 | empty'''


def p_vars(p):
    'vars : VAR decl decl_list'


def p_decl_list(p):
    '''decl_list : decl decl_list
                 | empty'''


def p_decl(p):
    'decl : ID id_list COLON type SEMICOLON'


def p_id_list(p):
    '''id_list : COMMA ID id_list
               | empty'''


def p_type(p):
    '''type : INT
            | FLOAT'''


def p_funcs(p):
    'funcs : func_type ID LPAREN params RPAREN LBRACE func_body RBRACE'


def p_func_body(p):
    '''func_body : VAR decl local_decls
                 | statement_list'''


def p_local_decls(p):
    '''local_decls : decl local_decls
                   | statement_list'''


def p_func_type(p):
    '''func_type : VOID
                 | type'''


def p_params(p):
    '''params : ID COLON type params_list
              | empty'''


def p_params_list(p):
    '''params_list : COMMA ID COLON type params_list
                   | empty'''


def p_body(p):
    'body : LBRACE statement_list RBRACE'


def p_statement_list(p):
    '''statement_list : statement statement_list
                      | empty'''


# ---------------------------------------------------------------------------
# Block 2: Statements
# ---------------------------------------------------------------------------

def p_statement(p):
    '''statement : assign
                 | condition
                 | cycle
                 | f_call
                 | print
                 | read
                 | return'''


def p_read(p):
    'read : READ LPAREN ID RPAREN SEMICOLON'


def p_return(p):
    'return : RETURN expresion SEMICOLON'


def p_assign(p):
    'assign : ID ASSIGN expresion SEMICOLON'


# if / else / while require { }, so every else follows a } (no dangling else).
def p_condition(p):
    '''condition : IF LPAREN expresion RPAREN body
                 | IF LPAREN expresion RPAREN body ELSE body'''


def p_cycle(p):
    'cycle : WHILE LPAREN expresion RPAREN body'


# As a statement a call ends in ';'; inside an expression it does not.
def p_f_call(p):
    'f_call : call SEMICOLON'


def p_call(p):
    'call : ID LPAREN args RPAREN'


def p_args(p):
    '''args : expresion args_list
            | empty'''


def p_args_list(p):
    '''args_list : COMMA expresion args_list
                 | empty'''


def p_print(p):
    'print : PRINT LPAREN print_item print_list RPAREN SEMICOLON'


def p_print_item(p):
    '''print_item : expresion
                  | CTE_STRING'''


def p_print_list(p):
    '''print_list : COMMA print_item print_list
                  | empty'''


# ---------------------------------------------------------------------------
# Block 3: Expressions
# ---------------------------------------------------------------------------

def p_expresion(p):
    'expresion : exp rel_opt'


def p_rel_opt(p):
    '''rel_opt : GT exp
               | LT exp
               | NE exp
               | EQ exp
               | GE exp
               | LE exp
               | empty'''


def p_exp(p):
    'exp : termino exp_list'


def p_exp_list(p):
    '''exp_list : PLUS termino exp_list
                | MINUS termino exp_list
                | empty'''


def p_termino(p):
    'termino : factor termino_list'


def p_termino_list(p):
    '''termino_list : MULT factor termino_list
                    | DIV factor termino_list
                    | empty'''


# No optional (empty) sign: each case is written with and without it, so the
# parser reads ID first and the next token decides variable vs call.
def p_factor(p):
    '''factor : LPAREN expresion RPAREN
              | ID
              | sign ID
              | cte
              | sign cte
              | call'''


def p_sign(p):
    '''sign : PLUS
            | MINUS'''


def p_cte(p):
    '''cte : CTE_INT
           | CTE_FLOAT'''


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def p_empty(p):
    'empty :'


def p_error(p):
    if p:
        raise SyntaxError(
            f"Syntax error: unexpected {p.type} ({p.value!r}) at line {p.lineno}")
    raise SyntaxError("Syntax error: unexpected end of file")


_parser = None


def build_parser():
    # Built once. Writes src/parser.out with the parser states and any conflicts.
    global _parser
    if _parser is None:
        out = os.path.join(os.path.dirname(__file__), 'parser.out')
        with open(out, 'w', encoding='utf-8') as f:
            _parser = yacc.yacc(debug=True, debuglog=yacc.PlyLogger(f),
                                write_tables=False)
    return _parser


def parse(source):
    """Parse a BabyDuck program. Returns 'OK' or raises SyntaxError."""
    return build_parser().parse(source, lexer=build_lexer())
