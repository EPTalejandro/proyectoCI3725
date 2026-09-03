from lexer import tokens, lexer
import ply.yacc as yac
import sys
from parser import *

class Symbol:
    def __init__(self, name, tipo, kind, line):
        self.name = name
        self.tipo = tipo
        self.kind = kind
        self.line = line


class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def declare(self, symbol):
        self.symbols[symbol.name] = symbol

    def lookup(self, name):
        scope = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None


class SymbolTable:
    def __init__(self):
        self.scopes = [Scope()]
        self.errors = []

    def current(self):
        return self.scopes[-1]

    def push(self):
        self.scopes.append(Scope(self.current()))

    def pop(self):
        self.scopes.pop()

    def declare(self, name, tipo, kind, line):
        sym = Symbol(name, tipo, kind, line)
        self.current().declare(sym)
        return sym

    def lookup(self, name):
        return self.current().lookup(name)

parser = yac.yacc(debug=True, write_tables=False)

def parse(codigo_fuente):
    return parser.parse(codigo_fuente)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: ./ContBot <Archivo.bot>")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r') as archivo:
            codigo = archivo.read()
    except FileNotFoundError:
        print(f"Error: El archivo '{sys.argv[1]}' no existe.")
        sys.exit(1)

    lexer.lineno = 1
    resultado = parser.parse(codigo, lexer=lexer)

    if resultado is not None:
        pass


