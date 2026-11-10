"""Usage:
    python3 src/main.py <file.bd>            parse a file
    python3 src/main.py <file.bd> --tokens   only print the token stream
    python3 src/main.py <file.bd> --symbols  also print the function directory
"""
import sys
from lexer import tokenize
from parser import parse
from symbols import SemanticError


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
    except (SyntaxError, SemanticError) as e:
        print(f"{path}: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
