"""BabyDuck Function Directory and Variable Tables.

    FunctionDirectory.funcs    dict: function name -> FuncInfo
        FuncInfo.vars          VarTable of that function (params + locals)
        The program itself is one more entry (type 'program');
        its VarTable holds the global variables.

    VarTable.vars              dict: variable name -> VarInfo

Example, for:
    program demo;
    var x : int;
    void f(a : int) { var t : float; ... }

    funcs = {
        'demo': FuncInfo(type='program', vars={x: int global}),
        'f':    FuncInfo(type='void', params=['int'],
                         vars={a: int param, t: float local}),
    }
"""
from dataclasses import dataclass, field


class SemanticError(Exception):
    """Raised for any semantic error (declared twice, not declared, ...)."""


# ---------------------------------------------------------------------------
# Variable table
# ---------------------------------------------------------------------------

@dataclass
class VarInfo:
    """One row of a variable table."""
    name: str
    type: str      # 'int' | 'float'
    kind: str      # 'global' | 'param' | 'local'
    line: int      # where it was declared (for error messages)


class VarTable:
    """Variables of ONE scope (the globals, or one function).

    A dict because every use of a variable is a search by name: O(1).
    Python dicts keep insertion order, so printing follows the source order.
    """

    def __init__(self):
        self.vars = {}

    def add(self, name, type_, kind, line):
        """Insert a variable. Error if the name already exists in THIS table."""
        if name in self.vars:
            prev = self.vars[name]
            raise SemanticError(
                f"Semantic error at line {line}: variable '{name}' already "
                f"declared in this scope (line {prev.line})")
        self.vars[name] = VarInfo(name, type_, kind, line)

    def lookup(self, name):
        """Return the VarInfo, or None if it is not in this table."""
        return self.vars.get(name)

    def __iter__(self):
        return iter(self.vars.values())

    def __len__(self):
        return len(self.vars)


# ---------------------------------------------------------------------------
# Function directory
# ---------------------------------------------------------------------------

@dataclass
class FuncInfo:
    """One row of the function directory."""
    name: str
    type: str                                      # 'int' | 'float' | 'void' | 'program'
    line: int
    params: list = field(default_factory=list)     # param types IN ORDER, to check calls
    vars: VarTable = field(default_factory=VarTable)


class FunctionDirectory:
    """All functions of the program, plus the program entry (globals).

    `current` is the scope being filled right now. BabyDuck has only two
    levels (global and one function, no nested functions), so instead of a
    stack of tables we only need: the current table and the global one.
    """

    def __init__(self):
        self.funcs = {}
        self.program = None    # name of the program entry
        self.current = None    # name of the scope being filled

    # --- filling the directory (called from the neuralgic points) ---------

    def start_program(self, name, line):
        """NP1: create the program entry. Its table will hold the globals."""
        self.funcs[name] = FuncInfo(name, 'program', line)
        self.program = self.current = name

    def add_function(self, name, type_, line):
        """NP3: create a function entry and make it the current scope."""
        if name in self.funcs:
            prev = self.funcs[name]
            what = 'the program' if prev.type == 'program' else 'a function'
            raise SemanticError(
                f"Semantic error at line {line}: '{name}' is already "
                f"{what} (line {prev.line})")
        self.funcs[name] = FuncInfo(name, type_, line)
        self.current = name

    def add_param(self, name, type_, line):
        """NP4: a param goes in the function's table AND in its signature."""
        func = self.funcs[self.current]
        func.vars.add(name, type_, 'param', line)
        func.params.append(type_)

    def add_var(self, name, type_, line):
        """NP2: a declared variable goes in the current scope's table."""
        kind = 'global' if self.current == self.program else 'local'
        self.funcs[self.current].vars.add(name, type_, kind, line)

    def end_function(self):
        """NP5: the function is done, go back to the global scope."""
        self.current = self.program

    # --- lookups (called when a name is USED) ------------------------------

    def lookup_var(self, name, line):
        """NP6: search the current (local) table first, then the global one."""
        info = self.funcs[self.current].vars.lookup(name)
        if info is None:
            info = self.funcs[self.program].vars.lookup(name)
        if info is None:
            raise SemanticError(
                f"Semantic error at line {line}: variable '{name}' not declared")
        return info

    def lookup_func(self, name, line):
        """NP7: the called function must exist (the program is not callable)."""
        func = self.funcs.get(name)
        if func is None or func.type == 'program':
            raise SemanticError(
                f"Semantic error at line {line}: function '{name}' not declared")
        return func

    # --- printing (python3 src/main.py file.bd --symbols) ------------------

    def dump(self):
        lines = []
        for f in self.funcs.values():
            if f.type == 'program':
                lines.append(f"{f.name} (program, globals)")
            else:
                lines.append(f"{f.name} : {f.type} ({', '.join(f.params)})")
            for v in f.vars:
                lines.append(f"    {v.name:<10} {v.type:<6} {v.kind}")
        return '\n'.join(lines)
