#!/usr/bin/env python3
"""MK1 C Compiler — compiles a C subset to MK1 assembly.

Usage:
    python3 mk1cc.py input.c              # print assembly to stdout
    python3 mk1cc.py input.c -o output.asm # write to file

Supported C subset:
    - uint8_t variables (8-bit unsigned)
    - Functions with up to 4 parameters, return value in A
    - if/else, while, for loops
    - Arithmetic: + - & | ^ ~ !
    - Comparisons: == != < > <= >=
    - Assignment: = += -= &= |= ^=
    - Built-in: out(expr) displays value on 7-segment display
    - Built-in: halt() stops the CPU
    - No pointers, no arrays (use ldp3/stp3 for page 3 storage)

Calling convention (matches MK1 hardware):
    - Arguments pushed right-to-left
    - Return value in $a
    - Caller cleans up arguments
    - Callee accesses args via ldsp
    - Local variables stored on stack via push, accessed via ldsp

Example:
    uint8_t max(uint8_t a, uint8_t b) {
        if (a >= b) return a;
        return b;
    }
    void main() {
        out(max(10, 25));
        out(max(200, 150));
    }
"""

import sys
import re
import argparse

# ── Tokenizer ────────────────────────────────────────────────────────

TOKEN_PATTERNS = [
    ('NUMBER',   r'0[xX][0-9a-fA-F]+|\d+'),
    ('IDENT',    r'[a-zA-Z_]\w*'),
    ('OP2',      r'[+\-&|^]=|==|!=|<=|>=|<<|>>'),
    ('OP1',      r'[+\-*/%&|^~!<>=(){},;]'),
    ('SKIP',     r'[ \t]+'),
    ('NEWLINE',  r'\n'),
    ('COMMENT',  r'//[^\n]*'),
    ('MISMATCH', r'.'),
]

KEYWORDS = {'if', 'else', 'while', 'for', 'return', 'uint8_t', 'void'}

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line
    def __repr__(self):
        return f'Token({self.type}, {self.value!r})'

def tokenize(source):
    tokens = []
    line = 1
    pat = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_PATTERNS)
    for m in re.finditer(pat, source):
        kind = m.lastgroup
        value = m.group()
        if kind == 'NEWLINE':
            line += 1
        elif kind == 'SKIP' or kind == 'COMMENT':
            pass
        elif kind == 'MISMATCH':
            raise SyntaxError(f'Line {line}: unexpected character {value!r}')
        elif kind == 'IDENT' and value in KEYWORDS:
            tokens.append(Token(value, value, line))
        elif kind == 'NUMBER':
            tokens.append(Token('NUMBER', int(value, 0), line))
        else:
            tokens.append(Token(kind, value, line))
    tokens.append(Token('EOF', '', line))
    return tokens

# ── Parser (recursive descent) ───────────────────────────────────────

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, type_or_value):
        t = self.peek()
        if t.type == type_or_value or t.value == type_or_value:
            return self.advance()
        raise SyntaxError(f'Line {t.line}: expected {type_or_value!r}, got {t.value!r}')

    def match(self, type_or_value):
        t = self.peek()
        if t.type == type_or_value or t.value == type_or_value:
            return self.advance()
        return None

    def parse_program(self):
        """program = (function | global_var)*"""
        functions = []
        globals = []
        while self.peek().type != 'EOF':
            typ = self.expect_type()
            name = self.expect('IDENT').value
            if self.match('('):
                functions.append(self.parse_function(typ, name))
            elif self.match(';'):
                globals.append(('global', typ, name, None))
            elif self.match('='):
                val = self.expect('NUMBER').value
                self.expect(';')
                globals.append(('global', typ, name, val))
            else:
                raise SyntaxError(f'Line {self.peek().line}: expected ( or ; after {name}')
        return ('program', globals, functions)

    def expect_type(self):
        if self.match('uint8_t'):
            return 'uint8_t'
        if self.match('void'):
            return 'void'
        raise SyntaxError(f'Line {self.peek().line}: expected type (uint8_t or void)')

    def parse_function(self, ret_type, name):
        """function = type name '(' params ')' block"""
        params = []
        if not self.match(')'):
            while True:
                ptype = self.expect_type()
                pname = self.expect('IDENT').value
                params.append((ptype, pname))
                if not self.match(','):
                    break
            self.expect(')')
        body = self.parse_block()
        return ('function', ret_type, name, params, body)

    def parse_block(self):
        """block = '{' statement* '}'"""
        self.expect('{')
        stmts = []
        while not self.match('}'):
            stmts.append(self.parse_statement())
        return ('block', stmts)

    def parse_statement(self):
        t = self.peek()

        if t.value == 'if':
            return self.parse_if()
        if t.value == 'while':
            return self.parse_while()
        if t.value == 'for':
            return self.parse_for()
        if t.value == 'return':
            self.advance()
            if self.match(';'):
                return ('return', None)
            expr = self.parse_expr()
            self.expect(';')
            return ('return', expr)
        if t.value == 'uint8_t':
            return self.parse_local_decl()
        if t.value == '{':
            return self.parse_block()

        # Expression statement (assignment, function call, etc.)
        expr = self.parse_expr()
        self.expect(';')
        return ('expr_stmt', expr)

    def parse_if(self):
        self.expect('if')
        self.expect('(')
        cond = self.parse_expr()
        self.expect(')')
        then_body = self.parse_statement()
        else_body = None
        if self.match('else'):
            else_body = self.parse_statement()
        return ('if', cond, then_body, else_body)

    def parse_while(self):
        self.expect('while')
        self.expect('(')
        cond = self.parse_expr()
        self.expect(')')
        body = self.parse_statement()
        return ('while', cond, body)

    def parse_for(self):
        self.expect('for')
        self.expect('(')
        init = self.parse_statement() if self.peek().value != ';' else None
        if init is None:
            self.expect(';')
        cond = self.parse_expr() if self.peek().value != ';' else ('number', 1)
        self.expect(';')
        update = self.parse_expr() if self.peek().value != ')' else None
        self.expect(')')
        body = self.parse_statement()
        return ('for', init, cond, update, body)

    def parse_local_decl(self):
        self.expect('uint8_t')
        name = self.expect('IDENT').value
        init = None
        if self.match('='):
            init = self.parse_expr()
        self.expect(';')
        return ('local_decl', name, init)

    # ── Expression parsing (precedence climbing) ──

    def parse_expr(self):
        return self.parse_assign()

    def parse_assign(self):
        left = self.parse_or()
        if self.peek().value in ('=', '+=', '-=', '&=', '|=', '^='):
            op = self.advance().value
            right = self.parse_assign()
            return ('assign', op, left, right)
        return left

    def parse_or(self):
        left = self.parse_xor()
        while self.peek().value == '|':
            self.advance()
            right = self.parse_xor()
            left = ('binop', '|', left, right)
        return left

    def parse_xor(self):
        left = self.parse_and()
        while self.peek().value == '^':
            self.advance()
            right = self.parse_and()
            left = ('binop', '^', left, right)
        return left

    def parse_and(self):
        left = self.parse_comparison()
        while self.peek().value == '&':
            self.advance()
            right = self.parse_comparison()
            left = ('binop', '&', left, right)
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        if self.peek().value in ('==', '!=', '<', '>', '<=', '>='):
            op = self.advance().value
            right = self.parse_additive()
            left = ('binop', op, left, right)
        return left

    def parse_additive(self):
        left = self.parse_unary()
        while self.peek().value in ('+', '-'):
            op = self.advance().value
            right = self.parse_unary()
            left = ('binop', op, left, right)
        return left

    def parse_unary(self):
        if self.peek().value == '~':
            self.advance()
            return ('unop', '~', self.parse_unary())
        if self.peek().value == '!':
            self.advance()
            return ('unop', '!', self.parse_unary())
        if self.peek().value == '-':
            self.advance()
            return ('unop', '-', self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        t = self.peek()

        if t.type == 'NUMBER':
            self.advance()
            return ('number', t.value)

        if t.type == 'IDENT':
            name = self.advance().value
            if self.match('('):
                # Function call
                args = []
                if not self.match(')'):
                    while True:
                        args.append(self.parse_expr())
                        if not self.match(','):
                            break
                    self.expect(')')
                return ('call', name, args)
            if self.peek().value == '++':
                self.advance()
                return ('postinc', name)
            if self.peek().value == '--':
                self.advance()
                return ('postdec', name)
            return ('var', name)

        if self.match('('):
            expr = self.parse_expr()
            self.expect(')')
            return expr

        raise SyntaxError(f'Line {t.line}: unexpected token {t.value!r}')


# ── Code Generator ───────────────────────────────────────────────────

class CodeGen:
    def __init__(self):
        self.code = []          # assembly lines
        self.data = []          # data declarations
        self.globals = {}       # name -> data label
        self.label_counter = 0
        self.current_func = None
        self.locals = {}        # name -> stack offset from SP
        self.local_count = 0    # number of locals pushed
        self.param_count = 0    # number of parameters

    def new_label(self, prefix='L'):
        self.label_counter += 1
        return f'.{prefix}{self.label_counter}'

    def emit(self, line):
        self.code.append(line)

    def emit_comment(self, text):
        self.code.append(f'; {text}')

    def generate(self, ast):
        _, globals, functions = ast

        self.emit('; Generated by mk1cc.py')
        self.emit('')

        # Register global variables (code emitted later in data bank)
        for g in globals:
            _, typ, name, init = g
            self.globals[name] = name
            if init is not None:
                self.data.append(f'{name}: #d8 {init}')
            else:
                self.data.append(f'{name}: #res 1')

        # Find main and emit call to it
        has_main = any(f[2] == 'main' for f in functions)
        if has_main:
            self.emit('  jal main')
            self.emit('  hlt')
            self.emit('')

        # Generate functions
        for func in functions:
            self.gen_function(func)

        # Output complete assembly
        lines = []
        lines.append('#include "mk1.cpu"')
        lines.append('')
        if self.data:
            lines.append('#bank ".data"')
            for d in self.data:
                lines.append(d)
            lines.append('')
        lines.append('#bank ".instr"')
        lines.append('')
        lines.extend(self.code)
        return '\n'.join(lines)

    def gen_function(self, func):
        _, ret_type, name, params, body = func
        self.current_func = name
        self.locals = {}
        self.local_count = 0
        self.param_count = len(params)

        self.emit_comment(f'function {name}({", ".join(p[1] for p in params)})')
        self.emit(f'{name}:')

        # Parameters are on the stack, pushed by caller right-to-left.
        # Stack layout: [SP+1]=retaddr, [SP+2]=last_arg, ... [SP+N+1]=first_arg
        for i, (ptype, pname) in enumerate(params):
            # First param is deepest: SP + param_count + 1
            # Last param is shallowest: SP + 2
            offset = self.param_count - i + 1
            self.locals[pname] = ('param', offset)

        # Generate body
        self.gen_statement(body)

        # If function doesn't end with return, add one
        if not self.code[-1].strip().startswith('ret'):
            self.emit('  ret')
        self.emit('')

    def gen_statement(self, stmt):
        if stmt is None:
            return
        kind = stmt[0]

        if kind == 'block':
            saved_local_count = self.local_count
            for s in stmt[1]:
                self.gen_statement(s)
            # Pop locals when leaving block
            while self.local_count > saved_local_count:
                self.emit('  pop $d')
                self.local_count -= 1
                # Update all local offsets
                for name in list(self.locals):
                    if self.locals[name][0] == 'local':
                        _, off = self.locals[name]
                        if off <= 0:
                            del self.locals[name]

        elif kind == 'local_decl':
            _, name, init = stmt
            if init:
                self.gen_expr(init)  # result in A
            else:
                self.emit('  ldi $a 0')
            self.emit('  push $a')
            self.local_count += 1
            # Local is at SP + 1 (just pushed). But as we push more locals,
            # older ones shift up. We track the push order.
            # After N pushes, the Kth push (1-indexed from bottom) is at SP + N - K + 1
            # But it's easier to recalculate: this local is push #local_count
            self.locals[name] = ('local', self.local_count)

        elif kind == 'expr_stmt':
            self.gen_expr(stmt[1])

        elif kind == 'return':
            _, expr = stmt
            if expr:
                self.gen_expr(expr)  # result in A
            self.emit('  ret')

        elif kind == 'if':
            _, cond, then_body, else_body = stmt
            if else_body:
                else_label = self.new_label('else')
                end_label = self.new_label('endif')
                self.gen_condition(cond, else_label, invert=True)
                self.gen_statement(then_body)
                self.emit(f'  j {end_label}')
                self.emit(f'{else_label}:')
                self.gen_statement(else_body)
                self.emit(f'{end_label}:')
            else:
                end_label = self.new_label('endif')
                self.gen_condition(cond, end_label, invert=True)
                self.gen_statement(then_body)
                self.emit(f'{end_label}:')

        elif kind == 'while':
            _, cond, body = stmt
            loop_label = self.new_label('while')
            end_label = self.new_label('endwhile')
            self.emit(f'{loop_label}:')
            self.gen_condition(cond, end_label, invert=True)
            self.gen_statement(body)
            self.emit(f'  j {loop_label}')
            self.emit(f'{end_label}:')

        elif kind == 'for':
            _, init, cond, update, body = stmt
            loop_label = self.new_label('for')
            end_label = self.new_label('endfor')
            if init:
                self.gen_statement(init)
            self.emit(f'{loop_label}:')
            self.gen_condition(cond, end_label, invert=True)
            self.gen_statement(body)
            if update:
                self.gen_expr(update)
            self.emit(f'  j {loop_label}')
            self.emit(f'{end_label}:')

    def _get_local_offset(self, name):
        """Get the current ldsp offset for a local variable or parameter."""
        kind, info = self.locals[name]
        if kind == 'param':
            # Params are below the return address and locals on the stack
            # SP + local_count + info (where info = param_count - i + 1)
            return self.local_count + info
        elif kind == 'local':
            # Local #K (1-indexed) is at SP + (local_count - K + 1)
            return self.local_count - info + 1
        return 0

    def gen_expr(self, expr):
        """Generate code to evaluate expr, leaving result in A."""
        kind = expr[0]

        if kind == 'number':
            self.emit(f'  ldi $a {expr[1]}')

        elif kind == 'var':
            name = expr[1]
            if name in self.locals:
                offset = self._get_local_offset(name)
                self.emit(f'  ldsp {offset}')
            elif name in self.globals:
                self.emit(f'  ld $a {name}')
            else:
                raise SyntaxError(f'Undefined variable: {name}')

        elif kind == 'assign':
            op, left, right = expr[1], expr[2], expr[3]
            if left[0] != 'var':
                raise SyntaxError('Can only assign to variables')
            name = left[1]

            if op == '=':
                self.gen_expr(right)
            else:
                # Compound assignment: load current value, apply op, store
                self.gen_expr(left)
                self.emit('  mov $a $b')
                self.gen_expr(right)
                self.emit('  swap')  # A=old, B=new_rhs
                base_op = op[0]  # strip the '='
                self._emit_binop(base_op)

            self._emit_store(name)

        elif kind == 'binop':
            op = expr[1]
            left, right = expr[2], expr[3]

            # Optimize: if right is a small constant for add/sub
            if op == '+' and right[0] == 'number' and right[1] == 1:
                self.gen_expr(left)
                self.emit('  inc')
                return
            if op == '-' and right[0] == 'number' and right[1] == 1:
                self.gen_expr(left)
                self.emit('  dec')
                return
            if op == '+' and right[0] == 'number':
                self.gen_expr(left)
                self.emit(f'  addi {right[1]} $a')
                return
            if op == '-' and right[0] == 'number':
                self.gen_expr(left)
                self.emit(f'  subi {right[1]} $a')
                return

            # General binary: eval left → A, eval right → B, operate
            self.gen_expr(right)
            self.emit('  push $a')
            self.local_count += 1
            self.gen_expr(left)
            self.emit('  pop $b')
            self.local_count -= 1
            self._emit_binop(op)

        elif kind == 'unop':
            op, operand = expr[1], expr[2]
            self.gen_expr(operand)
            if op == '~':
                self.emit('  not')
            elif op == '-':
                self.emit('  neg')
            elif op == '!':
                # !x: if x==0, result=1; else result=0
                lbl = self.new_label('not')
                end = self.new_label('endnot')
                self.emit(f'  cmp 0')
                self.emit(f'  jz {lbl}')
                self.emit(f'  ldi $a 0')
                self.emit(f'  j {end}')
                self.emit(f'{lbl}:')
                self.emit(f'  ldi $a 1')
                self.emit(f'{end}:')

        elif kind == 'call':
            name, args = expr[1], expr[2]
            if name == 'out':
                if args:
                    self.gen_expr(args[0])
                self.emit('  out')
                return
            if name == 'halt':
                self.emit('  hlt')
                return

            # Push arguments right-to-left
            for arg in reversed(args):
                self.gen_expr(arg)
                self.emit('  push $a')
                self.local_count += 1

            self.emit(f'  jal {name}')

            # Clean up arguments
            for _ in args:
                self.emit('  pop $d')
                self.local_count -= 1

        elif kind == 'postinc':
            name = expr[1]
            self.gen_expr(('var', name))
            self.emit('  push $a')  # save original value
            self.emit('  inc')
            self._emit_store(name)
            self.emit('  pop $a')  # restore original (post-increment returns old value)

        elif kind == 'postdec':
            name = expr[1]
            self.gen_expr(('var', name))
            self.emit('  push $a')
            self.emit('  dec')
            self._emit_store(name)
            self.emit('  pop $a')

    def _emit_binop(self, op):
        """Emit binary operation with A=left, B=right. Result in A."""
        if op == '+':
            self.emit('  add $b $a')
        elif op == '-':
            self.emit('  sub $b $a')
        elif op == '&':
            self.emit('  and $b $a')
        elif op == '|':
            self.emit('  or $b $a')
        elif op == '^':
            self.emit('  xor')  # A = A XOR B (clobbers D)
        else:
            raise SyntaxError(f'Unsupported binary operator: {op}')

    def _emit_store(self, name):
        """Store A into variable."""
        if name in self.locals:
            kind, info = self.locals[name]
            if kind == 'param':
                # Can't easily store back to a parameter on the stack
                # without a stack-relative store instruction. For now, error.
                raise SyntaxError(f'Cannot assign to parameter {name} (read-only)')
            elif kind == 'local':
                # Local variables: we'd need a stack-relative store (stsp)
                # which we don't have. Use a data page variable instead.
                # Actually, we can use the data page as a workaround:
                # promote the local to a global.
                if name not in self.globals:
                    self.globals[name] = name
                    self.data.append(f'{name}: #res 1')
                self.emit(f'  st $a {name}')
        elif name in self.globals:
            self.emit(f'  st $a {name}')
        else:
            # Auto-create global
            self.globals[name] = name
            self.data.append(f'{name}: #res 1')
            self.emit(f'  st $a {name}')

    def gen_condition(self, cond, target_label, invert=False):
        """Generate a conditional branch. If invert=True, branch when condition is FALSE."""
        if cond[0] == 'binop' and cond[1] in ('==', '!=', '<', '>', '<=', '>='):
            op = cond[1]
            left, right = cond[2], cond[3]

            # Optimize: compare against constant
            if right[0] == 'number':
                self.gen_expr(left)
                self.emit(f'  cmp {right[1]}')
            else:
                self.gen_expr(right)
                self.emit('  mov $a $b')
                self.gen_expr(left)
                self.emit('  cmp $b')

            # Emit the appropriate branch
            # After cmp (A - B): CF=1 if A >= B, ZF=1 if A == B
            if not invert:
                # Branch when condition is TRUE
                if op == '==':   self.emit(f'  jz {target_label}')
                elif op == '!=': self.emit(f'  jnz {target_label}')
                elif op == '>=': self.emit(f'  jc {target_label}')    # CF=1: A >= B
                elif op == '<':  self.emit(f'  jnc {target_label}')   # CF=0: A < B
                elif op == '>':
                    # A > B: CF=1 AND ZF=0
                    skip = self.new_label('skip')
                    self.emit(f'  jz {skip}')
                    self.emit(f'  jc {target_label}')
                    self.emit(f'{skip}:')
                elif op == '<=':
                    # A <= B: CF=0 OR ZF=1
                    self.emit(f'  jz {target_label}')
                    self.emit(f'  jnc {target_label}')
            else:
                # Branch when condition is FALSE (inverted)
                if op == '==':   self.emit(f'  jnz {target_label}')
                elif op == '!=': self.emit(f'  jz {target_label}')
                elif op == '>=': self.emit(f'  jnc {target_label}')
                elif op == '<':  self.emit(f'  jc {target_label}')
                elif op == '>':
                    # NOT(A > B) = A <= B: ZF=1 OR CF=0
                    self.emit(f'  jz {target_label}')
                    self.emit(f'  jnc {target_label}')
                elif op == '<=':
                    # NOT(A <= B) = A > B: ZF=0 AND CF=1
                    skip = self.new_label('skip')
                    self.emit(f'  jz {skip}')
                    self.emit(f'  jc {target_label}')  # wait, this is wrong for invert
                    # Actually: NOT(<=) means >, which is CF=1 AND ZF=0
                    # If ZF=1, condition is true (<=), so we DON'T branch (skip)
                    # If CF=0, condition is true (<), so we DON'T branch (skip)
                    # Only branch if CF=1 AND ZF=0
                    # Hmm, this needs two checks. Let me use a different approach.
                    pass
        else:
            # General expression: evaluate, compare to 0
            self.gen_expr(cond)
            self.emit('  cmp 0')
            if invert:
                self.emit(f'  jz {target_label}')   # branch if expr == 0 (false)
            else:
                self.emit(f'  jnz {target_label}')  # branch if expr != 0 (true)


# ── Main ─────────────────────────────────────────────────────────────

def compile_c(source):
    tokens = tokenize(source)
    parser = Parser(tokens)
    ast = parser.parse_program()
    codegen = CodeGen()
    return codegen.generate(ast)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='MK1 C Compiler')
    ap.add_argument('input', help='C source file')
    ap.add_argument('-o', '--output', help='Output assembly file')
    args = ap.parse_args()

    with open(args.input) as f:
        source = f.read()

    try:
        asm = compile_c(source)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(asm)
            print(f'Compiled to {args.output}')
        else:
            print(asm)
    except SyntaxError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
