import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

from lexer import tokenize  # noqa: E402
from parser import parse    # noqa: E402


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
                self.assertEqual(parse(read(path)), 'OK')

    def test_invalid_programs(self):
        for path in files('invalid'):
            with self.subTest(file=os.path.basename(path)):
                with self.assertRaises(SyntaxError):
                    parse(read(path))


if __name__ == '__main__':
    unittest.main(verbosity=2)
