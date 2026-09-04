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
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

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
        self.in_behavior = False

    def current(self):
        return self.scopes[-1]

    def push(self):
        self.scopes.append(Scope(self.current()))

    def pop(self):
        self.scopes.pop()

    def declare(self, name, tipo, kind):
        sym = Symbol(name, tipo, kind)
        if not self.current().declare(sym):
            self.errors.append(f"Redeclaración de la variable '{name}' en el mismo alcance.")
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
        if expr.name == "me":
            if not tabla.in_behavior:
                tabla.errors.append("Utilización de la palabra reservada 'me' fuera de un comportamiento.")
            expr.type = "bot"
            return "bot"

        sym = tabla.lookup(expr.name)
        if sym is None:
            tabla.errors.append(f"Variable '{expr.name}' no declarada.")
            expr.type = "unknown"
            return "unknown"
        expr.type = sym.tipo
        return sym.tipo

    if isinstance(expr, AritOpNode):
        t1 = analizar_expresion(expr.left, tabla)
        t2 = analizar_expresion(expr.right, tabla)
        if (t1 != "int" and t1 != "unknown") or (t2 != "int" and t2 != "unknown"):
            tabla.errors.append(f"Error de tipo: Operación aritmética '{expr.op}' requiere enteros.")
        expr.type = "int"
        return "int"

    if isinstance(expr, RelOpNode):
        t1 = analizar_expresion(expr.left, tabla)
        t2 = analizar_expresion(expr.right, tabla)
        if (t1 != "int" and t1 != "unknown") or (t2 != "int" and t2 != "unknown"):
            tabla.errors.append(f"Error de tipo: Comparación '{expr.op}' requiere enteros.")
        expr.type = "bool"
        return "bool"

    if isinstance(expr, BoolOpNode):
        t1 = analizar_expresion(expr.left, tabla)
        t2 = analizar_expresion(expr.right, tabla)
        if (t1 != "bool" and t1 != "unknown") or (t2 != "bool" and t2 != "unknown"):
            tabla.errors.append(f"Error de tipo: Operación booleana '{expr.op}' requiere booleanos.")
        expr.type = "bool"
        return "bool"

    if isinstance(expr, UnaOpNode):
        t = analizar_expresion(expr.expr, tabla)
        if expr.op == "~":
            if t != "bool" and t != "unknown":
                tabla.errors.append("Error de tipo: La negación (~) solo aplica a booleanos.")
            expr.type = "bool"
            return "bool"
        elif expr.op == "-":
            if t != "int" and t != "unknown":
                tabla.errors.append("Error de tipo: El signo menos (-) solo aplica a enteros.")
            expr.type = "int"
            return "int"

    return "unknown"


# -----------------------------
# Visita de sentencias
# -----------------------------
def visitar_sentencia(stmt, tabla):
    if isinstance(stmt, IfNode):
        tipo_cond = analizar_expresion(stmt.condicion, tabla)
        if tipo_cond != "bool" and tipo_cond != "unknown":
            tabla.errors.append("Error de tipo: La condición del 'if' debe ser booleana.")

        if stmt.cuerpo is not None:
            tabla.push()
            for s in stmt.cuerpo.statements:
                visitar_sentencia(s, tabla)
            tabla.pop()

        if stmt.cuerpo_else is not None:
            tabla.push()
            for s in stmt.cuerpo_else.statements:
                visitar_sentencia(s, tabla)
            tabla.pop()

    elif isinstance(stmt, WhileNode):
        tipo_cond = analizar_expresion(stmt.condition, tabla)
        if tipo_cond != "bool" and tipo_cond != "unknown":
            tabla.errors.append("Error de tipo: La condición del 'while' debe ser booleana.")

        if stmt.body is not None:
            tabla.push()
            for s in stmt.body.statements:
                visitar_sentencia(s, tabla)
            tabla.pop()

    elif isinstance(stmt, StoreNode):
        analizar_expresion(stmt.expr, tabla)

    elif isinstance(stmt, ContNodes):
        for var in stmt.var_list.vars:
            if isinstance(var, VariableNode):
                sym = tabla.lookup(var.name)
                if sym is None:
                    tabla.errors.append(f"Variable '{var.name}' no declarada.")

    elif isinstance(stmt, ReadNode):
        if stmt.var_name is not None:
            sym = tabla.lookup(stmt.var_name)
            if sym is None:
                tabla.errors.append(f"Variable '{stmt.var_name}' en 'read as' no declarada.")

    elif isinstance(stmt, CollectNode):
        if stmt.var_name is not None:
            sym = tabla.lookup(stmt.var_name)
            if sym is None:
                tabla.errors.append(f"Variable '{stmt.var_name}' en 'collect as' no declarada.")

    elif isinstance(stmt, DropNode):
        analizar_expresion(stmt.expr, tabla)

    elif isinstance(stmt, MovimientoNode):
        if stmt.expr is not None:
            t = analizar_expresion(stmt.expr, tabla)
            if t != "int" and t != "unknown":
                tabla.errors.append("Error de tipo: La cantidad de movimiento debe ser entera.")

    elif isinstance(stmt, OnNode):
        prev_in_behavior = tabla.in_behavior
        tabla.in_behavior = True
        
        if stmt.cuerpo is not None:
            tabla.push()
            for s in stmt.cuerpo.statements:
                visitar_sentencia(s, tabla)
            tabla.pop()
            
        tabla.in_behavior = prev_in_behavior

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

                if bot.comportamientos is not None:
                    for on_stmt in bot.comportamientos.statements:
                        visitar_sentencia(on_stmt, tabla)

    # Recorrer el cuerpo principal del programa
    if programa.controlador is not None:
        for stmt in programa.controlador.statements:
            visitar_sentencia(stmt, tabla)

    return tabla


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
            for err in tabla.errors:
                print(err)
        else:
            imprimir_arbol(resultado)
