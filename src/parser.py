"""BabyDuck parser (PLY yacc).

Each p_ function is one grammar rule, written in its docstring.
Nonterminals are lowercase, tokens UPPERCASE. 'empty' is epsilon.
The first rule (program) is the start symbol.

Entrega 2: the code inside some rules (neuralgic points, marked NP1..NP7)
fills the Function Directory and the Variable Tables while parsing.
PLY is bottom-up: a rule's code runs when the WHOLE rule has been read.

Entrega 3: neuralgic points Q1..Q17 generate the quadruples, using the
generator from quadruples.py (stacks POper / PilaO / PTypes + quad queue).
When an action must happen in the MIDDLE of a rule, that part is moved to a
small rule of its own (add_op, np_term, lparen, if_header...), because that
small rule is reduced at the right moment. The numbers match
docs/documentacion.md, section 10.
"""
import os

import ply.yacc as yacc
from lexer import tokens, build_lexer  # noqa: F401  (PLY needs `tokens` here)
from symbols import FunctionDirectory, SemanticError
from quadruples import QuadGenerator, Quadruple
from semantic_cube import INT, FLOAT, result_type, ERROR

# Both are filled while parsing. parse() creates new ones for every program.
directory = FunctionDirectory()
generator = QuadGenerator()


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
    # Q17: every statement must consume what its expressions pushed.
    generator.check_empty(p.lineno(1))


# NP6 (here, in assign and in factor): a used variable must be declared.
# Q12: read(x) -> (read, -, -, x)
def p_read(p):
    'read : READ LPAREN ID RPAREN SEMICOLON'
    directory.lookup_var(p[3], p.lineno(3))
    generator.quad_queue.append(Quadruple('read', None, None, p[3]))


# Q16: the value of the return is on the stacks. Until the functions delivery
# (RETURN quad) it is only discarded, so the stacks stay empty.
def p_return(p):
    'return : RETURN expresion SEMICOLON'
    generator.PilaO.pop()
    generator.PTypes.pop()


# Q10: when this runs the whole expression was read, so its result is on top
# of PilaO / PTypes. The variable doesn't need to be pushed: it is p[1].
# The cube checks the assignment (float = int ok, int = float error).
def p_assign(p):
    'assign : ID ASSIGN expresion SEMICOLON'
    info = directory.lookup_var(p[1], p.lineno(1))
    value = generator.PilaO.pop()
    exp_type = generator.PTypes.pop()
    if result_type(info.type, '=', exp_type) == ERROR:
        raise SemanticError(f"Semantic error at line {p.lineno(1)}: cannot assign type '{exp_type}' to variable '{p[1]}' of type '{info.type}'.")
    generator.quad_queue.append(Quadruple('=', value, None, p[1]))


# if / else / while require { }, so every else follows a } (no dangling else).
# The condition is split into its own rule (if_header / while_header) because
# p_condition runs only AFTER the body. The header is reduced right after the
# ')', BEFORE the body: that is where the condition must leave the stacks
# (and where GOTOF will go in Entrega 4).
def p_condition(p):
    '''condition : if_header body
                 | if_header body ELSE body'''


# Q15: pop the condition (must be bool). Entrega 4: GOTOF here.
def p_if_header(p):
    'if_header : IF LPAREN expresion RPAREN'
    generator.pop_condition(p.lineno(1))


def p_cycle(p):
    'cycle : while_header body'


# Q15: same as if_header. Entrega 4: remember the start of the loop + GOTOF.
def p_while_header(p):
    'while_header : WHILE LPAREN expresion RPAREN'
    generator.pop_condition(p.lineno(1))


# As a statement a call ends in ';'; inside an expression it does not.
# Q14: as a statement nobody uses the call's result: discard what Q13 pushed.
def p_f_call(p):
    'f_call : call SEMICOLON'
    generator.PilaO.pop()
    generator.PTypes.pop()


# NP7: the function must exist and get as many args as it has params.
# Q7 + Q13: remove the fake bottom, drop the arguments, push the result.
def p_call(p):
    'call : ID lparen args RPAREN'
    func = directory.lookup_func(p[1], p.lineno(1))
    if p[3] != len(func.params):
        raise SemanticError(
            f"Semantic error at line {p.lineno(1)}: '{p[1]}' expects "
            f"{len(func.params)} argument(s), got {p[3]}")
    # lparen pushed a fake bottom so the arguments can't use operators from
    # outside the call (doble(2) in "a * doble(2)"). Remove it now.
    generator.POper.pop()
    # The arguments are on the stacks (one per expression); drop them.
    # (Functions delivery: they become PARAM quads instead.)
    while p[3] > 0:
        p[3] -= 1
        generator.PilaO.pop()
        generator.PTypes.pop()
    # Placeholder for the call's result: the function name with its return
    # type. (Functions delivery: replaced by the real return value, after
    # ERA / PARAM / GOSUB.)
    # A void function gets type 'void', so using it in an expression fails in
    # the cube (no 'void' entries), which is the right semantic error.
    generator.PilaO.push(p[1])
    generator.PTypes.push(func.type)


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


# Q11: print_item reduces once per item, left to right: one quad per item.
# An expression is popped from the stacks; a string never touched them.
def p_print_item(p):
    '''print_item : expresion
                  | CTE_STRING'''
    if p.slice[1].type == 'expresion':
        value = generator.PilaO.pop()
        _ = generator.PTypes.pop()
        generator.quad_queue.append(Quadruple('print', value, None, None))
    else:  # CTE_STRING
        generator.quad_queue.append(Quadruple('print', p[1], None, None))


def p_print_list(p):
    '''print_list : COMMA print_item print_list
                  | empty'''


# ---------------------------------------------------------------------------
# Block 3: Expressions
#
# exp_list / termino_list are right-recursive: PLY reduces the LAST one
# first. If the quads were generated there, a - b - c would become
# a - (b - c). So the actions live in small rules that PLY reduces at the
# right moment: add_op / mult_op (when the operator is read) and
# np_term / np_factor (when each operand is complete).
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
    # Q9: rel_opt reduces AFTER its second exp, so both operands are already
    # on PilaO. Push the operator and reuse generate_binary (result: bool).
    if len(p) == 3:
        generator.POper.push(p[1])
        generator.generate_binary(p.lineno(1))


def p_exp(p):
    'exp : np_term exp_list'


def p_exp_list(p):
    '''exp_list : add_op np_term exp_list
                | empty'''


def p_add_op(p):
    '''add_op : PLUS
              | MINUS'''
    generator.POper.push(p[1])    # Q2: push + / - as soon as it is read


# Q4: reduced right after EACH termino. If a + / - is waiting, both of its
# operands are ready now: generate it (this keeps a - b - c left to right).
def p_np_term(p):
    '''np_term : termino'''
    if not generator.POper.is_empty() and generator.POper.top() in ('+', '-'):
        generator.generate_binary(p.lineno(1))


def p_termino(p):
    'termino : np_factor termino_list'


def p_termino_list(p):
    '''termino_list : mult_op np_factor termino_list
                    | empty'''


def p_mult_op(p):
    '''mult_op : MULT
               | DIV'''
    generator.POper.push(p[1])    # Q3: push * / / as soon as it is read


# Q5: same as Q4, one level down: after EACH factor, generate a waiting * or /.
def p_np_factor(p):
    '''np_factor : factor'''
    if not generator.POper.is_empty() and generator.POper.top() in ('*', '/'):
        generator.generate_binary(p.lineno(1))


# Q6: fake bottom. Reduced as soon as '(' is read (in a factor or a call).
# Q4 / Q5 only look for + - * /, so they stop at '(': the operators outside
# the parentheses wait until it is removed (Q7).
def p_lparen(p):
    '''lparen : LPAREN'''
    generator.POper.push('(')


# No optional (empty) sign: each case is written with and without it, so the
# parser reads ID first and the next token decides variable vs call.
def p_factor(p):
    '''factor : lparen expresion RPAREN
              | ID
              | sign ID
              | cte
              | sign cte
              | call'''
    # NP6 + Q1: in "ID" and "sign ID" the variable is the last symbol.
    # Check it is declared, then push its name and type.
    # (A constant was already pushed by p_cte.)
    last = len(p) - 1
    if p.slice[last].type == 'ID':
        info = directory.lookup_var(p[last], p.lineno(last))
        generator.PilaO.push(p[last])
        generator.PTypes.push(info.type)

    # Q7: the expression inside ( ) is done: remove the fake bottom.
    if p.slice[1].type == 'lparen':
        generator.POper.pop()

    # Q8: unary minus. '+x' is just x, so only '-' does something.
    if p.slice[1].type == "sign" and p[1] == "-":
        if p.slice[last].type == "cte":
            # The value is known now: p_cte already pushed it, negate it in place.
            value = generator.PilaO.pop()
            generator.PilaO.push(-value)

        if p.slice[last].type == "ID":
            # The value is only known at run time: translate -x as x * -1.
            # x and its type are already on the stacks (pushed above).
            generator.PilaO.push(-1)
            generator.PTypes.push(INT)
            generator.POper.push('*')
            generator.generate_binary(p.lineno(last))


def p_sign(p):
    '''sign : PLUS
            | MINUS'''
    p[0] = p[1]    # '+' or '-', read by p_factor (Q8)


# Q1: push the constant and its type (from its token: CTE_INT or CTE_FLOAT).
def p_cte(p):
    '''cte : CTE_INT
           | CTE_FLOAT'''
    generator.PilaO.push(p[1])
    generator.PTypes.push(INT if p.slice[1].type == 'CTE_INT' else FLOAT)


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
    global directory, generator
    directory = FunctionDirectory()
    generator = QuadGenerator()    # fresh tables for every program
    # tracking=True: PLY also keeps the line of NONTERMINALS (the line of
    # their first token). Without it p.lineno(1) in np_term / np_factor /
    # statement is 0 and error messages say "line 0".
    return build_parser().parse(source, lexer=build_lexer(), tracking=True)
