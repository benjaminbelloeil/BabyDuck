import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

from lexer import tokenize  # noqa: E402
import parser               # noqa: E402  (to read parser.generator after parse())
from parser import parse    # noqa: E402
from quadruples import Quadruple, Stack, Queue  # noqa: E402
from semantic_cube import result_type, unary_type, INT, FLOAT, BOOL, ERROR  # noqa: E402
from symbols import FunctionDirectory, SemanticError  # noqa: E402


def files(folder):
    path = os.path.join(HERE, folder)
    return sorted(os.path.join(path, f) for f in os.listdir(path) if f.endswith('.bd'))


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


class TestLexer(unittest.TestCase):
    def types(self, src):
        return [t[0] for t in tokenize(src)]

    def test_reserved_vs_id(self):
        self.assertEqual(self.types('program programa while_1'),
                         ['PROGRAM', 'ID', 'ID'])

    def test_return_keyword(self):
        self.assertEqual(self.types('return returns'), ['RETURN', 'ID'])

    def test_numbers(self):
        self.assertEqual(tokenize('42 3.14'),
                         [('CTE_INT', 42, 1), ('CTE_FLOAT', 3.14, 1)])

    def test_operators(self):
        self.assertEqual(self.types('= != < > + - * /'),
                         ['ASSIGN', 'NE', 'LT', 'GT', 'PLUS', 'MINUS', 'MULT', 'DIV'])

    def test_two_char_comparisons(self):
        self.assertEqual(self.types('== <= >= = < >'),
                         ['EQ', 'LE', 'GE', 'ASSIGN', 'LT', 'GT'])

    def test_comments(self):
        self.assertEqual(self.types('x = 1; // comment ; = x\ny'),
                         ['ID', 'ASSIGN', 'CTE_INT', 'SEMICOLON', 'ID'])

    def test_delimiters(self):
        self.assertEqual(self.types('; , : ( ) { }'),
                         ['SEMICOLON', 'COMMA', 'COLON', 'LPAREN', 'RPAREN',
                          'LBRACE', 'RBRACE'])

    def test_string(self):
        self.assertEqual(tokenize('"hola mundo"'), [('CTE_STRING', '"hola mundo"', 1)])

    def test_line_numbers(self):
        self.assertEqual([t[2] for t in tokenize('a\nb\n\nc')], [1, 2, 4])

    def test_illegal_char(self):
        with self.assertRaises(SyntaxError):
            tokenize('x @ y')


class TestParser(unittest.TestCase):
    def test_valid_programs(self):
        for path in files('valid'):
            with self.subTest(file=os.path.basename(path)):
                self.assertIsInstance(parse(read(path)), FunctionDirectory)

    def test_invalid_programs(self):
        for path in files('invalid'):
            with self.subTest(file=os.path.basename(path)):
                with self.assertRaises(SyntaxError):
                    parse(read(path))


class TestSemanticCube(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(result_type(INT, '+', INT), INT)
        self.assertEqual(result_type(INT, '*', FLOAT), FLOAT)
        self.assertEqual(result_type(FLOAT, '-', INT), FLOAT)
        self.assertEqual(result_type(BOOL, '+', INT), ERROR)

    def test_division(self):
        self.assertEqual(result_type(INT, '/', INT), INT)
        self.assertEqual(result_type(INT, '/', FLOAT), FLOAT)

    def test_relational(self):
        self.assertEqual(result_type(INT, '<', FLOAT), BOOL)
        self.assertEqual(result_type(FLOAT, '==', FLOAT), BOOL)
        self.assertEqual(result_type(BOOL, '>', BOOL), ERROR)
        self.assertEqual(result_type(BOOL, '==', BOOL), ERROR)

    def test_assignment(self):
        self.assertEqual(result_type(INT, '=', INT), INT)
        self.assertEqual(result_type(FLOAT, '=', INT), FLOAT)
        self.assertEqual(result_type(INT, '=', FLOAT), ERROR)
        self.assertEqual(result_type(INT, '=', BOOL), ERROR)

    def test_unary(self):
        self.assertEqual(unary_type('-', INT), INT)
        self.assertEqual(unary_type('-', FLOAT), FLOAT)
        self.assertEqual(unary_type('-', BOOL), ERROR)


class TestSymbols(unittest.TestCase):
    def test_semantic_errors(self):
        for path in files('semantic'):
            with self.subTest(file=os.path.basename(path)):
                with self.assertRaises(SemanticError):
                    parse(read(path))

    def test_directory_contents(self):
        d = parse(read(os.path.join(HERE, 'valid', '10_full.bd')))
        self.assertEqual(list(d.funcs), ['demo', 'f'])
        self.assertEqual(d.funcs['demo'].type, 'program')
        self.assertEqual([(v.name, v.type, v.kind) for v in d.funcs['demo'].vars],
                         [('x', 'int', 'global'), ('y', 'int', 'global'),
                          ('z', 'float', 'global')])
        f = d.funcs['f']
        self.assertEqual(f.type, 'void')
        self.assertEqual(f.params, ['int', 'float'])
        self.assertEqual([(v.name, v.type, v.kind) for v in f.vars],
                         [('a', 'int', 'param'), ('b', 'float', 'param'),
                          ('t', 'int', 'local')])

    def test_fresh_directory_per_parse(self):
        parse('program a; var x : int; main { } end')
        d = parse('program b; main { } end')
        self.assertEqual(list(d.funcs), ['b'])

    def test_error_reports_line(self):
        with self.assertRaisesRegex(SemanticError, 'line 3.*line 2'):
            parse('program p;\nvar x : int;\n    x : float;\nmain { } end')


class TestQuadStructures(unittest.TestCase):
    def test_quadruple_str(self):
        self.assertEqual(str(Quadruple('+', 'a', 'b', 't1')), '(+, a, b, t1)')
        self.assertEqual(str(Quadruple('=', 't1', None, 'x')), '(=, t1, -, x)')
        self.assertEqual(str(Quadruple('-', 0, 5, 't2')), '(-, 0, 5, t2)')

    def test_stack_is_lifo(self):
        s = Stack()
        s.push('a')
        s.push('b')
        self.assertEqual(s.top(), 'b')
        self.assertEqual(s.pop(), 'b')
        self.assertEqual(s.pop(), 'a')
        self.assertTrue(s.is_empty())

    def test_empty_stack_raises(self):
        with self.assertRaises(IndexError):
            Stack().pop()
        with self.assertRaises(IndexError):
            Stack().top()

    def test_queue_keeps_order_and_allows_filling(self):
        q = Queue()
        q.append(Quadruple('*', 'b', 'c', 't1'))
        q.append(Quadruple('+', 'a', 't1', 't2'))
        self.assertEqual([str(x) for x in q], ['(*, b, c, t1)', '(+, a, t1, t2)'])
        self.assertEqual(q.next_index(), 2)
        q[0].result = 't9'          # Entrega 4 fills jump targets like this
        self.assertEqual(str(q[0]), '(*, b, c, t9)')


class TestQuads(unittest.TestCase):
    """tests/quads/NN_name.bd is compiled and its queue is compared, line by
    line, with tests/quads/NN_name.quads (written by hand)."""

    def test_quad_programs(self):
        for path in files('quads'):
            with self.subTest(file=os.path.basename(path)):
                parse(read(path))
                gen = parser.generator
                expected = read(path[:-3] + '.quads').split('\n')
                expected = [line for line in expected if line.strip()]
                self.assertEqual([str(q) for q in gen.quad_queue], expected)
                # Every statement must consume what it pushed.
                for name in ('POper', 'PilaO', 'PTypes'):
                    stack = getattr(gen, name)
                    self.assertTrue(stack.is_empty(), f'{name} not empty: {stack}')

    def test_fresh_generator_per_parse(self):
        parse('program a; var x : int; main { x = x + 1; } end')
        parse('program b; var y : int; main { y = y * 2; } end')
        self.assertEqual([str(q) for q in parser.generator.quad_queue],
                         ['(*, y, 2, t1)', '(=, t1, -, y)'])

    def test_type_error_reports_operator(self):
        with self.assertRaisesRegex(SemanticError, "'\\+'.*bool.*int"):
            parse('program p; var x : int; main { x = (x > 1) + 2; } end')

    def test_errors_inside_expressions_report_the_real_line(self):
        # Without tracking=True in parse() this said "line 0".
        with self.assertRaisesRegex(SemanticError, 'line 4'):
            parse('program p;\nvar x : int;\nmain {\n x = (x > 1) + 2;\n}\nend')


if __name__ == '__main__':
    unittest.main(verbosity=2)
