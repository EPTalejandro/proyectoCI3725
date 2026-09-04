from lexer import tokens, lexer
import ply.yacc as yac
import sys
from parser import *

class Symbol:
    def __init__(self, name, tipo, kind):
        self.name = name
        self.tipo = tipo
        self.kind = kind


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

    def declare(self, name, tipo, kind):
        sym = Symbol(name, tipo, kind)
        self.current().declare(sym)
        return sym

    def lookup(self, name):
        return self.current().lookup(name)
    
def analizar_expresion(expr, tabla):
    if isinstance(expr, NumberNode):
        expr.type = "int"
        return "int"

    if isinstance(expr, BoolNode):
        expr.type = "bool"
        return "bool"

    if isinstance(expr, VariableNode):
        sym = tabla.lookup(expr.name)
        if sym is None:
            tabla.errors.append(f"Variable '{expr.name}' no declarada")
            expr.type = "unknown"
            return "unknown"
        expr.type = sym.tipo
        return sym.tipo

    if isinstance(expr, AritOpNode):
        t1 = analizar_expresion(expr.left, tabla)
        t2 = analizar_expresion(expr.right, tabla)
        if t1 != "int" or t2 != "int":
            tabla.errors.append(f"Operación aritmética inválida: '{expr.op}'")
        expr.type = "int"
        return "int"

    if isinstance(expr, RelOpNode):
        t1 = analizar_expresion(expr.left, tabla)
        t2 = analizar_expresion(expr.right, tabla)
        if t1 != t2:
            tabla.errors.append(f"Comparación inválida entre '{t1}' y '{t2}'")
        expr.type = "bool"
        return "bool"

    if isinstance(expr, BoolOpNode):
        t1 = analizar_expresion(expr.left, tabla)
        t2 = analizar_expresion(expr.right, tabla)
        if t1 != "bool" or t2 != "bool":
            tabla.errors.append(f"Operación booleana inválida: '{expr.op}'")
        expr.type = "bool"
        return "bool"

    if isinstance(expr, UnaOpNode):
        t = analizar_expresion(expr.expr, tabla)
        if expr.op == "~":
            if t != "bool":
                tabla.errors.append("La negación solo aplica a expresiones booleanas")
            expr.type = "bool"
            return "bool"
        elif expr.op == "-":
            if t != "int":
                tabla.errors.append("El signo menos solo aplica a enteros")
            expr.type = "int"
            return "int"

    return "unknown"


# -----------------------------
# Visita de sentencias
# -----------------------------
def visitar_sentencia(stmt, tabla):
    if isinstance(stmt, IfNode):
        tipo_cond = analizar_expresion(stmt.condicion, tabla)
        if tipo_cond != "bool":
            tabla.errors.append("La condición del if debe ser booleana")

        if stmt.cuerpo is not None:
            for s in stmt.cuerpo.statements:
                visitar_sentencia(s, tabla)

        if stmt.cuerpo_else is not None:
            for s in stmt.cuerpo_else.statements:
                visitar_sentencia(s, tabla)

    elif isinstance(stmt, WhileNode):
        tipo_cond = analizar_expresion(stmt.condition, tabla)
        if tipo_cond != "bool":
            tabla.errors.append("La condición del while debe ser booleana")

        if stmt.body is not None:
            for s in stmt.body.statements:
                visitar_sentencia(s, tabla)

    elif isinstance(stmt, StoreNode):
        analizar_expresion(stmt.expr, tabla)

    elif isinstance(stmt, ContNodes):
        for var in stmt.var_list.vars:
            if isinstance(var, VariableNode):
                sym = tabla.lookup(var.name)
                if sym is None:
                    tabla.errors.append(f"Variable '{var.name}' no declarada")

    elif isinstance(stmt, ReadNode):
        if stmt.var_name is not None:
            sym = tabla.lookup(stmt.var_name)
            if sym is None:
                tabla.errors.append(f"Variable '{stmt.var_name}' no declarada")

    elif isinstance(stmt, CollectNode):
        if stmt.var_name is not None:
            registrar_variable_automatica(tabla, stmt.var_name, tipo="unknown", kind="collect")

    elif isinstance(stmt, DropNode):
        analizar_expresion(stmt.expr, tabla)

    elif isinstance(stmt, MovimientoNode):
        if stmt.expr is not None:
            t = analizar_expresion(stmt.expr, tabla)
            if t != "int":
                tabla.errors.append("La cantidad de movimiento debe ser entera")

    elif isinstance(stmt, OnNode):
        # Se puede procesar el cuerpo del evento
        if stmt.cuerpo is not None:
            for s in stmt.cuerpo.statements:
                visitar_sentencia(s, tabla)

    elif isinstance(stmt, EstListNodes):
        for s in stmt.statements:
            visitar_sentencia(s, tabla)


# -----------------------------
# Análisis de contexto
# -----------------------------
def analizar_contexto(programa):
    tabla = SymbolTable()

    # Registrar variables de los bots declarados
    if programa.declaraciones is not None:
        for bot in programa.declaraciones.bots:
            if isinstance(bot, BotDefNode):
                for var in bot.nombres.vars:
                    if isinstance(var, VariableNode):
                        tabla.declare(var.name, bot.tipo, "bot_variable")
                    registrar_variable_automatica(tabla, "me", tipo=bot.tipo, kind="self")

                if bot.comportamientos is not None:
                    for on_stmt in bot.comportamientos.statements:
                        visitar_sentencia(on_stmt, tabla)

    # Recorrer el cuerpo principal del programa
    if programa.controlador is not None:
        for stmt in programa.controlador.statements:
            visitar_sentencia(stmt, tabla)

    return tabla


def registrar_variable_automatica(tabla, nombre, tipo='unknown', kind='variable'):
    if tabla.lookup(nombre) is None:
        tabla.declare(nombre, tipo, kind)

# -----------------------------
# Parser de PLY
# -----------------------------
parser = yac.yacc(debug=False, write_tables=False)


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
        tabla = analizar_contexto(resultado)
        if tabla.errors:
            print("Errores de contexto:")
            for err in tabla.errors:
                print("-", err)
        else:
            print("Sin errores de contexto.")
