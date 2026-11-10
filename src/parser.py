"""BabyDuck parser (PLY yacc).

Each p_ function is one grammar rule, written in its docstring.
Nonterminals are lowercase, tokens UPPERCASE. 'empty' is epsilon.
The first rule (program) is the start symbol.

Entrega 2: the code inside some rules (neuralgic points, marked NP1..NP7)
fills the Function Directory and the Variable Tables while parsing.
PLY is bottom-up: a rule's code runs when the WHOLE rule has been read.
"""
import os

import ply.yacc as yacc
from lexer import tokens, build_lexer  # noqa: F401  (PLY needs `tokens` here)
from symbols import FunctionDirectory, SemanticError

# Filled while parsing. parse() creates a new one for every program.
directory = FunctionDirectory()


# ---------------------------------------------------------------------------
# Block 1: Program, variables, functions
# ---------------------------------------------------------------------------

def p_program(p):
    'program : program_header SEMICOLON vars_opt func_list MAIN body END'
    p[0] = directory    # parse() returns the filled directory


# NP1: create the program's entry (its table = globals).
# It is its own rule so the code runs right after the name is read,
# BEFORE the global vars. Inside p_program it would run at the very end.
def p_program_header(p):
    'program_header : PROGRAM ID'
    directory.start_program(p[2], p.lineno(2))


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


# NP2: add every name of the declaration to the current scope's table.
# The type comes last (a, b, c : int;), so id_list collects the names first.
def p_decl(p):
    'decl : ID id_list COLON type SEMICOLON'
    for name, line in [(p[1], p.lineno(1))] + p[2]:
        directory.add_var(name, p[4], line)


# Returns a list of (name, line), in source order.
def p_id_list(p):
    '''id_list : COMMA ID id_list
               | empty'''
    if len(p) == 4:                         # COMMA ID id_list
        p[0] = [(p[2], p.lineno(2))] + p[3]
    else:                                   # empty
        p[0] = []


def p_type(p):
    '''type : INT
            | FLOAT'''
    p[0] = p[1]    # the lexeme: 'int' or 'float'


# NP5: the whole function was read, go back to the global scope.
def p_funcs(p):
    'funcs : func_header LPAREN params RPAREN LBRACE func_body RBRACE'
    directory.end_function()


# NP3: create the function's entry and make it the current scope, BEFORE its
# params and locals are read. Registering it here also allows recursion.
def p_func_header(p):
    'func_header : func_type ID'
    directory.add_function(p[2], p[1], p.lineno(2))


def p_func_body(p):
    '''func_body : VAR decl local_decls
                 | statement_list'''


def p_local_decls(p):
    '''local_decls : decl local_decls
                   | statement_list'''


def p_func_type(p):
    '''func_type : VOID
                 | type'''
    p[0] = p[1]    # 'void', 'int' or 'float'


# NP4: add the params to the function's table and signature, in order.
# params_list is right-recursive, so it is reduced right to left (last param
# first). That's why it returns a list and the params are added here, together.
def p_params(p):
    '''params : ID COLON type params_list
              | empty'''
    if len(p) == 5:                         # ID COLON type params_list
        for name, type_, line in [(p[1], p[3], p.lineno(1))] + p[4]:
            directory.add_param(name, type_, line)


# Returns a list of (name, type, line), in source order.
def p_params_list(p):
    '''params_list : COMMA ID COLON type params_list
                   | empty'''
    if len(p) == 6:                         # COMMA ID COLON type params_list
        p[0] = [(p[2], p[4], p.lineno(2))] + p[5]
    else:                                   # empty
        p[0] = []


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


# NP6 (here, in assign and in factor): a used variable must be declared.
def p_read(p):
    'read : READ LPAREN ID RPAREN SEMICOLON'
    directory.lookup_var(p[3], p.lineno(3))


def p_return(p):
    'return : RETURN expresion SEMICOLON'


def p_assign(p):
    'assign : ID ASSIGN expresion SEMICOLON'
    directory.lookup_var(p[1], p.lineno(1))


# if / else / while require { }, so every else follows a } (no dangling else).
def p_condition(p):
    '''condition : IF LPAREN expresion RPAREN body
                 | IF LPAREN expresion RPAREN body ELSE body'''


def p_cycle(p):
    'cycle : WHILE LPAREN expresion RPAREN body'


# As a statement a call ends in ';'; inside an expression it does not.
def p_f_call(p):
    'f_call : call SEMICOLON'


# NP7: the function must exist and get as many args as it has params.
def p_call(p):
    'call : ID LPAREN args RPAREN'
    func = directory.lookup_func(p[1], p.lineno(1))
    if p[3] != len(func.params):
        raise SemanticError(
            f"Semantic error at line {p.lineno(1)}: '{p[1]}' expects "
            f"{len(func.params)} argument(s), got {p[3]}")


# args / args_list return HOW MANY arguments there are.
def p_args(p):
    '''args : expresion args_list
            | empty'''
    p[0] = 1 + p[2] if len(p) == 3 else 0


def p_args_list(p):
    '''args_list : COMMA expresion args_list
                 | empty'''
    p[0] = 1 + p[3] if len(p) == 4 else 0


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
    # NP6: in "ID" and "sign ID" the variable is the last symbol.
    last = len(p) - 1
    if p.slice[last].type == 'ID':
        directory.lookup_var(p[last], p.lineno(last))


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
    """Parse a BabyDuck program.

    Returns the filled FunctionDirectory.
    Raises SyntaxError (lexical/syntax) or SemanticError.
    """
    global directory
    directory = FunctionDirectory()    # fresh tables for every program
    return build_parser().parse(source, lexer=build_lexer())
