# Baby_Duck: Scanner y Parser (Entrega 1)

Herramienta usada: **PLY** (Python Lex-Yacc). Genera un scanner con `ply.lex`
y un parser LALR(1) con `ply.yacc`.

## 1. Cómo se dieron de alta las expresiones regulares (scanner)

Archivo: `src/lexer.py`

- Todos los tokens se declaran en la lista `tokens`.
- Tokens simples: variables `t_NOMBRE = r'regex'`.
- Tokens con acción: funciones `t_NOMBRE(t)` con la regex en el docstring.
- Palabras reservadas: diccionario `reserved`. Se reconocen como `ID` y después
  se cambia su tipo si la palabra está en el diccionario.
- `t_ignore` ignora espacios y tabs; `t_ignore_COMMENT` ignora comentarios `//`;
  `t_newline` cuenta líneas; `t_error` marca caracteres ilegales.

| Token         | Expresión regular                                                     |
|---------------|-----------------------------------------------------------------------|
| ID            | `[a-zA-Z_][a-zA-Z0-9_]*`                                              |
| CTE_INT       | `[0-9]+`                                                              |
| CTE_FLOAT     | `[0-9]+\.[0-9]+`                                                      |
| CTE_STRING    | `"[^"\n]*"`                                                           |
| Comentario    | `//[^\n]*` (se ignora)                                                |
| Operadores    | `=  +  -  *  /`                                                       |
| Comparación   | `>  <  !=  ==  >=  <=`                                                |
| Delimitadores | `;  ,  :  (  )  {  }`                                                 |
| Reservadas    | `program main end var int float void print read while if else return` |

- `CTE_FLOAT` se define antes que `CTE_INT` porque PLY prueba las funciones en
  orden; si no, `3.14` se cortaría en `3` y `.`.
- Los operadores de dos caracteres (`==`, `<=`, `>=`, `!=`) ganan sobre los de uno
  porque PLY ordena los tokens simples de la regex más larga a la más corta.

## 2. Cómo se dieron de alta las reglas gramaticales (parser)

Archivo: `src/parser.py`

- Cada regla es una función `p_nombre(p)` y la regla va en su docstring:
  `'assign : ID ASSIGN expresion SEMICOLON'`.
- Las alternativas (`|`) van en líneas separadas del mismo docstring.
- ε se escribe con la regla `empty :`.
- La primera regla del archivo (`program`) es el símbolo inicial.

Gramática final:

```
program        : PROGRAM ID ; vars_opt func_list MAIN body END
vars_opt       : vars | ε
vars           : VAR decl decl_list
decl_list      : decl decl_list | ε
decl           : ID id_list : type ;
id_list        : , ID id_list | ε
type           : INT | FLOAT
func_list      : funcs func_list | ε
funcs          : func_type ID ( params ) { func_body }
func_type      : VOID | type
params         : ID : type params_list | ε
params_list    : , ID : type params_list | ε
func_body      : VAR decl local_decls | statement_list
local_decls    : decl local_decls | statement_list
body           : { statement_list }
statement_list : statement statement_list | ε
statement      : assign | condition | cycle | f_call | print | read | return
assign         : ID = expresion ;
condition      : IF ( expresion ) body
               | IF ( expresion ) body ELSE body
cycle          : WHILE ( expresion ) body
f_call         : call ;
call           : ID ( args )
args           : expresion args_list | ε
args_list      : , expresion args_list | ε
print          : PRINT ( print_item print_list ) ;
print_item     : expresion | CTE_STRING
print_list     : , print_item print_list | ε
read           : READ ( ID ) ;
return         : RETURN expresion ;
expresion      : exp rel_opt
rel_opt        : > exp | < exp | != exp | == exp | >= exp | <= exp | ε
exp            : termino exp_list
exp_list       : + termino exp_list | - termino exp_list | ε
termino        : factor termino_list
termino_list   : * factor termino_list | / factor termino_list | ε
factor         : ( expresion ) | ID | sign ID | cte | sign cte | call
sign           : + | -
cte            : CTE_INT | CTE_FLOAT
```

PLY genera la tabla sin conflictos (0 shift/reduce, 0 reduce/reduce).

## 3. Cambios respecto a los diagramas

| Cambio               | Antes                               | Ahora                              | Motivo                                                          |
|----------------------|-------------------------------------|------------------------------------|-----------------------------------------------------------------|
| `return`             | no existía                          | `return x + 1;`                    | Agregado en el diagrama actualizado                             |
| Signo en FACTOR      | `SIGN_OPT -> + \| - \| ε`           | `ID \| sign ID \| cte \| sign cte` | El ε causaba un conflicto shift/reduce con la llamada a función |
| Llamada en expresión | `x = g(1); + 2;`                    | `x = g(1) + 2;`                    | Solo lleva `;` cuando es estatuto                               |
| if / else            | `if (c) s1; else s2;;`              | `if (c) { ... } else { ... }`      | Llaves obligatorias: elimina el `;;` y la ambigüedad del else   |
| while                | `while (c) do s;;`                  | `while (c) { ... }`                | Igual que if: sin `do`, llaves obligatorias                     |
| Bloque `[ ]`         | `[ s1; s2; ]`                       | eliminado                          | Las llaves `{ }` ya cumplen esa función                         |
| Funciones            | `int f() [ var t : int; { ... } ];` | `int f() { var t : int; ... }`     | Más fácil de leer y escribir                                    |
| Comparaciones        | `>  <  !=`                          | `>  <  !=  ==  >=  <=`             | Permite comparar igualdad y rangos                              |
| Comentarios          | no existían                         | `// texto`                         | Documentar el código                                            |

## 4. Test plan

Ejecución: `python3 -m unittest -v tests/test_babyduck.py`

- `tests/valid/`: 16 programas que deben ser aceptados.
- `tests/invalid/`: 25 programas que deben ser rechazados.
- Pruebas del scanner: reservadas vs ID, números, operadores, comparaciones de dos
  caracteres, comentarios, delimitadores, strings, número de línea y caracteres
  ilegales.

Principales test-cases:

| Archivo                        | Entrada clave                                        | Esperado          |
|--------------------------------|------------------------------------------------------|-------------------|
| valid/05_assign_expr           | `y = -x + (x - 1) / 2;`                              | Aceptado          |
| valid/08_print                 | `print("x =", x, x + 1);`                            | Aceptado          |
| valid/09_fcall                 | `h();`  `x = g(x) + 1;`                              | Aceptado          |
| valid/10_full                  | programa completo con vars, función, read, if, while | Aceptado          |
| valid/11_return                | `return a * 2;`                                      | Aceptado          |
| valid/12_nested_if             | if anidado con `{ }`                                 | Aceptado          |
| valid/14_comments              | `x = 1; // comentario`                               | Aceptado          |
| valid/15_comparisons           | `if (x == y) { ... }`                                | Aceptado          |
| valid/16_func_locals           | función con `var` locales y estatutos                | Aceptado          |
| invalid/01_lex_illegal_char    | `1 @ 2`                                              | Error léxico      |
| invalid/02_lex_bad_float       | `3.`                                                 | Error léxico      |
| invalid/04_missing_semicolon   | `read(x)`                                            | Error de sintaxis |
| invalid/08_keyword_as_id       | `var while : int;`                                   | Error de sintaxis |
| invalid/12_double_relational   | `1 < 2 < 3`                                          | Error de sintaxis |
| invalid/13_return_without_expr | `return;`                                            | Error de sintaxis |
| invalid/19_if_without_braces   | `if (x > 0) x = 1;`                                  | Error de sintaxis |
| invalid/21_old_while_do        | `while (x > 0) do { ... }`                           | Error de sintaxis |
| invalid/25_var_after_statement | declaración después de un estatuto                   | Error de sintaxis |

Resultado: todas las pruebas pasan (OK).
