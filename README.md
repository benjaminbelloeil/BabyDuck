# BabyDuck compiler (PLY)

## Setup (once)
    ./setup.sh                  # creates .venv and installs PLY
    source .venv/bin/activate   # every time you open a new terminal

## Run
    python3 src/main.py tests/valid/10_full.bd            # parse a file
    python3 src/main.py tests/valid/10_full.bd --tokens   # token stream only
    python3 -m unittest -v tests/test_babyduck.py         # full test plan

## Structure
    src/lexer.py      scanner: tokens + regular expressions        (done)
    src/parser.py     parser: grammar rules                        (done)
    src/main.py       command line entry point
    tests/valid/      programs that must be accepted
    tests/invalid/    programs that must be rejected
    tests/test_babyduck.py   test runner
    docs/notes.md     cheat sheet: how the compiler works
    docs/documentacion.md   documentation for the submission

## Checks
- PLY prints no "shift/reduce" or "reduce/reduce" conflicts
- PLY prints no "Token ... defined, but not used" warnings
- `python3 -m unittest -v tests/test_babyduck.py` ends in OK
