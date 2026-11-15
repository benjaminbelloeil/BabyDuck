"""Quadruples for BabyDuck (Entrega 3).

Structures used to translate a program into quadruples:

- Quadruple:     one instruction (op, left, right, result).
- Stack:         LIFO. Used three times by the generator: POper (operators),
                 PilaO (operands) and PTypes (the type of each operand).
- Queue:         the quads, in the order they are generated (= the order the
                 virtual machine will run them). It only grows.
- QuadGenerator: owns the 3 stacks, the queue and the temp counter.
                 parser.py only calls its methods.
"""
from symbols import SemanticError
from semantic_cube import result_type, ERROR, BOOL


class Quadruple:
    """One instruction: (op, left, right, result).

    A class (not a tuple) because Entrega 4 has to change `result` of a quad
    that is already in the queue (fill the target of a GOTOF). Empty slots
    are None and print as '-'.
    """

    def __init__(self, op, left=None, right=None, result=None):
        self.op = op
        self.left = left
        self.right = right
        self.result = result

    def __str__(self):
        values = [self.op, self.left, self.right, self.result]
        formatted_values = [str(v) if v is not None else '-' for v in values]
        return f"({', '.join(formatted_values)})"

    def __repr__(self):
        return self.__str__()


class Stack:
    """LIFO stack over a Python list: the END of the list is the top."""

    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("Stack is empty. Cannot pop from an empty stack.")
        return self.items.pop()

    def top(self):
        if self.is_empty():
            raise IndexError("Stack is empty. Cannot retrieve the top element.")
        return self.items[-1]

    def is_empty(self):
        return len(self.items) == 0

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return f"Stack({self.items})"


class Queue:
    """The quad queue. Quads are only appended, never removed.

    Numbering starts at 0. queue[i] gives quad i, so a quad already generated
    can be read or modified later (jump targets in Entrega 4).
    """

    def __init__(self):
        self.items = []
        self.index = 0      # number the NEXT quad will get (always == len(items))

    def append(self, item):
        self.items.append(item)
        self.index += 1

    def next_index(self):
        return self.index

    def __getitem__(self, i):
        return self.items[i]

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __repr__(self):
        return f"Queue({self.items})"


class QuadGenerator:
    """Everything needed to generate quads. parse() makes a new one per program."""

    def __init__(self):
        self.POper = Stack()
        self.PilaO = Stack()
        self.PTypes = Stack()
        self.quad_queue = Queue()
        self.temp_counter = 0

    def new_temp(self):
        """Next temporary: t1, t2, ..."""
        self.temp_counter += 1
        return f't{self.temp_counter}'

    def generate_binary(self, line):
        """Generate the quad for the operator on top of POper.

        Pops the RIGHT operand first (it is on top), then the left one, then
        the operator. The semantic cube gives the result type (or ERROR).
        The result goes to a new temp, which is pushed back as an operand.
        """
        right_op = self.PilaO.pop()
        right_type = self.PTypes.pop()
        left_op = self.PilaO.pop()
        left_type = self.PTypes.pop()
        op = self.POper.pop()
        result = result_type(left_type, op, right_type)
        if result == ERROR:
            raise SemanticError(f"Semantic error at line {line}: cannot apply operator '{op}' to types '{left_type}' and '{right_type}'.")
        temp = self.new_temp()
        self.quad_queue.append(Quadruple(op, left_op, right_op, temp))
        self.PilaO.push(temp)
        self.PTypes.push(result)

    def check_empty(self, line):
        """Q17: after every statement the 3 stacks must be empty again.

        If something is left, a neuralgic point pushed without popping. This is
        a bug in the compiler (not in the user's program), so the message says
        which stack and what is in it.
        """
        for name in ('POper', 'PilaO', 'PTypes'):
            stack = getattr(self, name)
            if not stack.is_empty():
                raise SemanticError(
                    f"Internal error at line {line}: {name} not empty after "
                    f"statement: {stack}")

    def pop_condition(self, line):
        """Q15: pop the condition of an if / while and check it is a bool.

        Returns the operand that holds the condition. In Entrega 4 it will be
        used for the GOTOF quad; for now nothing else is generated.
        """
        value = self.PilaO.pop()
        type_ = self.PTypes.pop()
        if type_ != BOOL:
            raise SemanticError(
                f"Semantic error at line {line}: condition must be a comparison "
                f"(bool), got '{type_}'")
        return value

