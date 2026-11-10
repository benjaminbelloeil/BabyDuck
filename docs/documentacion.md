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

---

# Baby_Duck: Semántica de variables (Entrega 2)

Archivos nuevos: `src/semantic_cube.py`, `src/symbols.py`.
Archivos modificados: `src/parser.py` (puntos neurálgicos), `src/main.py` (opción `--symbols`).

## 5. Cubo semántico

Archivo: `src/semantic_cube.py`

**Tipos:**
- `int` y `float`: los únicos tipos con los que se puede declarar una variable.
- `bool`: tipo interno. Nadie lo puede declarar; es el resultado de una
  comparación y el tipo que necesitan las condiciones de `if` y `while`.
- Los strings (`CTE_STRING`) no están en el cubo: solo pueden aparecer dentro
  de `print`, nunca se opera con ellos.

**Tabla 1. `+  -  *`**

| izq \ der | int   | float | bool  |
|-----------|-------|-------|-------|
| int       | int   | float | error |
| float     | float | float | error |
| bool      | error | error | error |

**Tabla 2. `/`**

| izq \ der | int   | float | bool  |
|-----------|-------|-------|-------|
| int       | int   | float | error |
| float     | float | float | error |
| bool      | error | error | error |

**Tabla 3. `>  <  >=  <=`**

| izq \ der | int   | float | bool  |
|-----------|-------|-------|-------|
| int       | bool  | bool  | error |
| float     | bool  | bool  | error |
| bool      | error | error | error |

**Tabla 4. `==  !=`**

| izq \ der | int   | float | bool  |
|-----------|-------|-------|-------|
| int       | bool  | bool  | error |
| float     | bool  | bool  | error |
| bool      | error | error | error |

**Tabla 5. `=`** (izquierda: la variable que recibe; derecha: el tipo del valor)

| variable \ valor | int   | float | bool  |
|------------------|-------|-------|-------|
| int              | int   | error | error |
| float            | float | float | error |
| bool             | error | error | error |

**Tabla 6. Signo unario (`+x`, `-x`)**

| operando | `+` / `-` |
|----------|-----------|
| int      | int       |
| float    | float     |
| bool     | error     |

**Decisiones:**
- Si un lado es `float`, el resultado es `float`: así no se pierden decimales.
- `int / int` da `int` (división entera, como en C: `7 / 2 = 3`), porque
  BabyDuck se diseñó con comportamiento tipo C.
- `bool` no es un número: no se puede usar en aritmética, ni ordenar (`>` `<`),
  ni con signo.
- `bool == bool` es error. Es alcanzable con paréntesis (`(a > b) == (c > d)`),
  pero se deja fuera para mantener el lenguaje simple.
- Asignación: un `int` cabe en un `float` (`5` se vuelve `5.0`); un `float` en
  un `int` perdería los decimales, así que es error. Un `bool` no se puede guardar
  porque ninguna variable puede ser `bool`.
- El signo no cambia el tipo de un número.

**Reglas fuera del cubo** (no son "dos tipos dan un tipo"; se validarán en la
Entrega 3, cuando se conozca el tipo de cada expresión):
- La condición de `if` y `while` debe ser `bool`.
- `print` acepta `int`, `float`, `bool` y strings.
- `read(x)`: `x` puede ser `int` o `float`.
- `return expr;` sigue la tabla de `=`, como si se asignara al tipo de retorno de
  la función: `return 5;` en una función `float` es válido, `return 2.5;` en una
  función `int` es error.
- `return` en una función `void` o en `main` es error.
- Una función `void` no se puede usar dentro de una expresión (no tiene valor).

**Estructura elegida:** un diccionario de Python con llave
`(tipo_izq, operador, tipo_der)` y valor el tipo resultante. El signo unario usa
un diccionario aparte con llave `(operador, tipo)`, porque tiene un solo operando.

- Por qué un diccionario: la consulta es O(1).
- Por qué llave tupla y no diccionarios anidados (`cubo[op][izq][der]`): una sola
  consulta, sin tener que validar cada nivel.
- Por qué solo las combinaciones válidas: la mayoría de las celdas son error; no
  guardarlas deja la tabla compacta. Si la llave no existe, el resultado es `error`.
- Los operadores que comparten tabla se agrupan en tuplas (`ARITHMETIC`,
  `ORDERING`, `EQUALITY`) y el cubo se llena con un ciclo por grupo.

**Operaciones:**
- `result_type(izq, op, der)`: regresa el tipo resultante o `error`.
- `unary_type(op, operando)`: igual para el signo.

## 6. Directorio de Funciones y Tablas de Variables

Archivo: `src/symbols.py`

```
FunctionDirectory
    funcs     dict  nombre -> FuncInfo
    program   nombre de la entrada del programa (alcance global)
    current   nombre del alcance que se está llenando

FuncInfo     name, type ('int'|'float'|'void'|'program'), line,
             params (lista de tipos en orden), vars (VarTable)

VarTable
    vars      dict  nombre -> VarInfo

VarInfo      name, type ('int'|'float'), kind ('global'|'param'|'local'), line
```

Ejemplo para `tests/valid/10_full.bd`:

```
demo (program, globals)
    x          int    global
    y          int    global
    z          float  global
f : void (int, float)
    a          int    param
    b          float  param
    t          int    local
```

**Por qué estas estructuras**

| Qué | Estructura | Por qué |
|-----|------------|---------|
| Directorio de funciones | Tabla hash (`dict`) | Cada llamada busca la función por nombre: búsqueda e inserción O(1), y detectar un duplicado es un `in`. |
| Tabla de variables | Tabla hash (`dict`) | Cada uso de una variable es una búsqueda por nombre. Python conserva el orden de inserción, útil para imprimir y, más adelante, para asignar direcciones en orden. |
| Una tabla por función | `VarTable` dentro de cada `FuncInfo` | Cada función tiene su propio alcance, y su tabla viaja con ella. |
| Alcance actual | Nombre (`current`) en vez de una pila de tablas | BabyDuck solo tiene dos niveles (global y función) y no permite funciones anidadas; basta con la tabla actual y la global. |
| Variables globales | Tabla de la entrada `program` | Todas las tablas se manejan igual, y el nombre del programa queda reservado. |
| Parámetros | Lista ordenada de tipos (`params`) + filas `param` en la tabla | El orden importa para validar llamadas (`f(x, y)`), y un diccionario no sirve para eso. También van en la tabla porque dentro de la función se usan como variables. |
| Filas | `dataclass` (`VarInfo`, `FuncInfo`) | Registros con campos con nombre, fáciles de extender en las siguientes entregas (dirección virtual, cuádruplo de inicio, tamaño). |

**Operaciones principales**

| Operación | Qué hace | Error que detecta |
|-----------|----------|-------------------|
| `start_program(nombre)` | Crea la entrada del programa; se vuelve el alcance actual | |
| `add_function(nombre, tipo)` | Inserta la función y la vuelve el alcance actual | Función doblemente declarada, o con el nombre del programa |
| `add_param(nombre, tipo)` | Inserta en la tabla de la función y agrega el tipo a `params` | Parámetro repetido |
| `add_var(nombre, tipo)` | Inserta en la tabla del alcance actual (`global` o `local`) | Variable doblemente declarada en el mismo alcance (incluye local con el nombre de un parámetro) |
| `end_function()` | Regresa al alcance global | |
| `lookup_var(nombre)` | Busca en la tabla local y luego en la global | Variable no declarada |
| `lookup_func(nombre)` | Busca la función en el directorio | Función no declarada |
| `dump()` | Imprime el directorio (`python3 src/main.py archivo.bd --symbols`) | |

**Reglas de alcance:**
- Una variable local o un parámetro puede llamarse igual que una global; dentro
  de la función se usa la local (la búsqueda empieza por la tabla local).
- Dos funciones pueden tener locales con el mismo nombre (son tablas distintas).
- Una función se puede llamar a sí misma (recursión), porque se registra antes de
  leer su cuerpo.
- Una función debe declararse antes de ser llamada.
- Funciones y variables son espacios de nombres distintos: una global `f` y una
  función `f` pueden coexistir, porque una llamada siempre lleva `(`.

## 7. Puntos neurálgicos

PLY genera un parser bottom-up: el código de una regla se ejecuta cuando la regla
se reduce, es decir, cuando ya se leyó toda su parte derecha. Para que algo ocurra
**a la mitad** de una regla (crear la función antes de leer sus parámetros), esa
parte se separa en una regla propia (`program_header`, `func_header`). La tabla
LALR sigue con 0 conflictos.

```
program        : program_header ; vars_opt func_list MAIN body END
program_header : PROGRAM ID                                  <- NP1
decl           : ID id_list : type ;                         <- NP2
func_header    : func_type ID                                <- NP3
params         : ID : type params_list | ε                   <- NP4
funcs          : func_header ( params ) { func_body }        <- NP5
read           : READ ( ID ) ;                               <- NP6
assign         : ID = expresion ;                            <- NP6
factor         : ID | sign ID | ...                          <- NP6
call           : ID ( args )                                 <- NP7
```

| NP  | Regla | Cuándo se ejecuta | Acción |
|-----|-------|-------------------|--------|
| NP1 | `program_header` | Después de `program nombre` | Crea el directorio y la entrada del programa (alcance global) |
| NP2 | `decl` | Al terminar cada declaración (`;`) | Inserta cada nombre con su tipo en la tabla del alcance actual |
| NP3 | `func_header` | Después de `tipo nombre` de una función | Inserta la función con su tipo de retorno; se vuelve el alcance actual |
| NP4 | `params` | Al terminar la lista de parámetros | Inserta los parámetros en la tabla y su tipo en `params`, en orden |
| NP5 | `funcs` | Al cerrar la función (`}`) | El alcance actual vuelve a ser el global |
| NP6 | `read`, `assign`, `factor` | Al usar una variable | Verifica que esté declarada (local o global) |
| NP7 | `call` | Al terminar una llamada | Verifica que la función exista y reciba tantos argumentos como parámetros |

**Detalles de implementación:**
- En `decl` el tipo viene al final (`a, b, c : int;`), así que `id_list` regresa
  en `p[0]` la lista de nombres (con su línea) y se insertan todos al reducir `decl`.
- `params_list` es recursiva por la derecha, así que se reduce de derecha a
  izquierda (primero el último parámetro). Por eso regresa una lista y los
  parámetros se insertan juntos al reducir `params`, en el orden correcto.
- `type` y `func_type` regresan su lexema (`'int'`, `'float'`, `'void'`) en `p[0]`.
- `args` y `args_list` regresan el número de argumentos.
- `parse()` crea un directorio nuevo en cada llamada y lo regresa.
- Los errores semánticos lanzan `SemanticError` con la línea; `main.py` los
  imprime igual que los de sintaxis.

## 8. Test plan (Entrega 2)

Ejecución: `python3 -m unittest -v tests/test_babyduck.py`

- `tests/semantic/`: 15 programas sintácticamente correctos que deben dar error semántico.
- `tests/valid/17` a `20`: casos de alcance que deben ser aceptados.
- Pruebas unitarias del cubo semántico (todas las tablas) y del contenido del directorio.
- `valid/12_nested_if` e `invalid/16_call_semicolon_in_expr` ahora declaran las
  funciones que llaman, para que sigan probando lo mismo que en la Entrega 1.

| Archivo | Entrada clave | Esperado |
|---------|---------------|----------|
| semantic/01_dup_global | `var x : int; x : float;` | Variable doblemente declarada |
| semantic/02_dup_same_line | `var a, b, a : int;` | Variable doblemente declarada |
| semantic/03_dup_local | local repetida en una función | Variable doblemente declarada |
| semantic/04_dup_param | `void f(a : int, a : float)` | Parámetro repetido |
| semantic/05_local_same_as_param | `void f(a : int) { var a : float; }` | Variable doblemente declarada |
| semantic/06_dup_function | `void f()` y `int f()` | Función doblemente declarada |
| semantic/07_function_named_like_program | `program p; void p() { }` | Nombre ya usado por el programa |
| semantic/08_undeclared_assign | `y = 1;` sin declarar `y` | Variable no declarada |
| semantic/09_undeclared_in_expr | `x = y + 1;` | Variable no declarada |
| semantic/10_undeclared_read | `read(z);` | Variable no declarada |
| semantic/11_undeclared_function | `f();` sin declarar `f` | Función no declarada |
| semantic/12_wrong_arg_count | `f(x)` con `f(a, b)` | Número de argumentos incorrecto |
| semantic/13_local_not_visible_in_main | local de `f` usada en `main` | Variable no declarada |
| semantic/14_param_not_visible_in_other_func | parámetro de `f` usado en `g` | Variable no declarada |
| semantic/15_call_before_declared | `f` llama a `g`, declarada después | Función no declarada |
| valid/17_shadowing | parámetro `x` oculta la global `x` | Aceptado |
| valid/18_same_local_in_two_funcs | `t` local en `f` y en `g` | Aceptado |
| valid/19_recursion | `fact` se llama a sí misma | Aceptado |
| valid/20_globals_in_func | una función modifica una global | Aceptado |

Ejemplo de salida:

```
$ python3 src/main.py tests/valid/10_full.bd --symbols
tests/valid/10_full.bd: OK, program accepted
demo (program, globals)
    x          int    global
    y          int    global
    z          float  global
f : void (int, float)
    a          int    param
    b          float  param
    t          int    local

$ python3 src/main.py tests/semantic/01_dup_global.bd
tests/semantic/01_dup_global.bd: Semantic error at line 3: variable 'x' already declared in this scope (line 2)
```

Resultado: todas las pruebas pasan (OK).
