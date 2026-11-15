"""Usage:
    python3 src/main.py <file.bd>            parse a file
    python3 src/main.py <file.bd> --tokens   only print the token stream
    python3 src/main.py <file.bd> --symbols  also print the function directory
    python3 src/main.py <file.bd> --quads    also print the quadruple queue
"""
import sys
from lexer import tokenize
import parser
from parser import parse
from symbols import SemanticError


def quads_table(queue):
    """The quad queue as a numbered table (0-based, like the queue)."""
    rows = [['#', 'op', 'left', 'right', 'result']]
    for i, q in enumerate(queue):
        cells = [q.op, q.left, q.right, q.result]
        rows.append([str(i)] + ['-' if c is None else str(c) for c in cells])
    widths = [max(len(row[col]) for row in rows) for col in range(5)]
    return '\n'.join('  '.join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip()
                     for row in rows)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    try:
        with open(path, encoding='utf-8') as f:
            source = f.read()
    except OSError:
        print(f"{path}: file not found")
        sys.exit(1)
    try:
        if '--tokens' in sys.argv:
            for typ, val, line in tokenize(source):
                print(f"{line:>4}  {typ:<12} {val!r}")
            return
        directory = parse(source)
        print(f"{path}: OK, program accepted")
        if '--symbols' in sys.argv:
            print(directory.dump())
        if '--quads' in sys.argv:
            print(quads_table(parser.generator.quad_queue))
    except (SyntaxError, SemanticError) as e:
        print(f"{path}: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
