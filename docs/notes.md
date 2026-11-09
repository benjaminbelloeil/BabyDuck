# BabyDuck cheat sheet

## The big picture

```
source code  →  LEXER  →  tokens  →  PARSER  →  OK or syntax error
 x = 2 + 3;              ID ASSIGN CTE_INT PLUS CTE_INT SEMICOLON
```

- **Lexer** (`src/lexer.py`): cuts the text into tokens. Knows words, not order.
- **Parser** (`src/parser.py`): checks the tokens are in an order the grammar allows.

## Lexer

- `tokens`: list of every token name.
- `t_PLUS = r'\+'`: simple token, just a regex.
- `def t_CTE_INT(t)`: token with code (convert to int, count lines...). Regex in the docstring.
- Function tokens are tried **in file order**, so FLOAT goes before INT
  (otherwise `3.14` → `3` + illegal `.`).
- Keywords: every word matches `t_ID`, then `reserved.get(word, 'ID')` changes the
  type if it is a keyword. Whole word is compared, so `returns` stays `ID`.
- Two-char operators (`==` `<=` `>=` `!=`) win over one-char ones because PLY tries
  string tokens from the longest regex to the shortest.
- `t_ignore`: spaces/tabs skipped. `t_ignore_COMMENT`: `// ...` skipped.
  `t_error`: illegal character → lexical error.

## Parser

- One function per rule: `def p_assign(p)`. The **docstring is the rule**.
- `p[1]..p[n]` = values of the right side, `p[0]` = result. Bodies are empty for
  now because we only check syntax (semantics come in stages 2 to 4).
- `empty :` = ε (nothing). Used for optional parts, e.g. `h()` has `args → empty`.
- First rule (`program`) = start symbol.
- PLY builds an LALR(1) table: reads left to right, looks **1 token ahead**.
  `src/parser.out` shows the states; it must report 0 conflicts.

## Grammar ideas worth knowing

**Precedence by levels.** `*` `/` happen before `+` `-` because of the levels:
```
expresion → exp (one > < != == >= <= exp)
exp       → termino + termino ...
termino   → factor * factor ...
factor    → number | variable | call | ( expresion )
```
`2 + 3 * 4`: `3 * 4` is one termino, so it is grouped first → 14.
Parentheses make anything a single factor.

**Only one comparison.** `rel_opt` is not recursive, so `1 < 2 < 3` is an error.

**Sign without ε.** Old rule: `SIGN_OPT ID` with an empty sign. On `x` the parser had
to decide "empty sign (variable) or not (call)" before seeing the `(` that tells them
apart. Fix: write `ID | sign ID | cte | sign cte | call`, so it reads `x` first and
decides after.

**Calls.** `call` = `g(1)` (inside expressions). `f_call` = `g(1);` (as a statement).

**if / else / while need `{ }`.** Every `else` comes right after a `}`, so it is always
clear which `if` it belongs to (no dangling else). `while` has no `do`.

**Function body.** Local vars and statements share one `{ }`. A declaration
(`t : int;`) and a statement (`t = 1;`) both start with ID, so the grammar is shaped
so the parser reads the ID first and the next token decides (`:` `,` → declaration,
`=` `(` → statement). Vars must come before statements.

## Language at a glance

```
// comments start with //
program demo;
var x, y : int;
    z : float;

int doble(a : int) {
  var t : int;
  t = a * 2;
  return t;
}

main {
  read(x);
  y = doble(x) + 1;
  if (y >= 10) { print("big", y); } else { print("small"); }
  while (x > 0) { x = x - 1; }
}
end
```

## Commands

```
python3 src/main.py tests/valid/10_full.bd            parse a file
python3 src/main.py tests/valid/10_full.bd --tokens   show tokens
python3 -m unittest -v tests/test_babyduck.py         run all tests
```
