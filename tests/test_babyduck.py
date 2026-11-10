import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

from lexer import tokenize  # noqa: E402
from parser import parse    # noqa: E402
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
