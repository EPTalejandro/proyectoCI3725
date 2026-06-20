from lexer import tokens, lexer
import ply.yacc as yac
import sys

class Node:
    pass

class ProgramNode(Node):
    def __init__(self, declaraciones, controlador):
        self.declaraciones = declaraciones   # bot_list o None
        self.controlador = controlador       # statement_list

class BotListNode(Node):
    def __init__(self, bots=None):
        self.bots = bots if bots is not None else []
    def append(self, bot):
        self.bots.append(bot)

class BotDefNode(Node):
    def __init__(self, tipo, nombres, comportamientos):
        self.tipo = tipo                     # 'int' | 'bool' | 'char'
        self.nombres = nombres               # VarListNode
        self.comportamientos = comportamientos  # EstListNodes (de OnNode) o None

class NumberNode(Node):
    def __init__(self, value): 
        self.value = value
        self.type = "int"
        
class BoolNode(Node):
    def __init__(self, value):
        self.value = value
        self.type = "bool"
        
class VariableNode(Node):
    def __init__(self, name):
        self.name = name
        self.type = "unknown" 
    def __str__(self): 
        return str(self.name)
    
class IfNode(Node):
    def __init__(self, condicion, cuerpo, cuerpo_else=None):
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.cuerpo_else = cuerpo_else
        
class WhileNode(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
    
class OnNode(Node):
    def __init__(self, trigger, cuerpo):
        self.trigger = trigger
        self.cuerpo = cuerpo
    
class EstListNodes(Node):
    def __init__(self, statements=None):
        if statements is None:
            self.statements = []
        else:
            self.statements = statements
    def append(self, statement):
        self.statements.append(statement)
    
class ContNodes(Node):
    def __init__(self, action_name, var_list):
        self.action_name = action_name 
        self.var_list = var_list     

class StoreNode(Node):
    def __init__(self, expr):
        self.expr = expr
        
class VarListNode(Node):
    def __init__(self, vars=None):
        if vars is None:
            self.vars = []
        else:
            self.vars = vars
    def append(self, vars):
        self.vars.append(vars)
        
class BoolOpNode(Node):
    def __init__(self, left, op, right):
        self.left = left; self.op = op; self.right = right
        self.type = "bool"
    
class AritOpNode(Node):
    def __init__(self, left, op, right):
        self.left = left; self.op = op; self.right = right
        self.type = "int"
    
class RelOpNode(Node):
    def __init__(self, left, op, right):
        self.left = left; self.op = op; self.right = right
        self.type = "bool"
    
class UnaOpNode(Node):
    def __init__(self, op, expr):
        self.op = op; self.expr = expr

class ReadNode(Node):
    def __init__(self, var_name):
        self.var_name = var_name   # None si no hay 'as', o str con el identificador si sí

class CollectNode(Node):
    def __init__(self, var_name):
        self.var_name = var_name  # None si no hay 'as'; si no, el nombre del identificador

class DropNode(Node):
    def __init__(self, expr):
        self.expr = expr

class MovimientoNode(Node):
    def __init__(self, direccion, expr=None):
        self.direccion = direccion   # 'left' | 'right' | 'up' | 'down'
        self.expr = expr             # None si no hay expresión

class CharNode(Node):
    def __init__(self, raw):
        # raw viene como "'x'" -> extraemos lo que está entre comillas
        contenido = raw[1:-1]
        escapes = {'\\n': '\n', '\\t': '\t', "\\'": "'"}
        self.value = escapes.get(contenido, contenido)
        self.type = "char"

# Precedencia
precedence = (
    ('left', 'TkDisyuncion'),
    ('left', 'TkConjuncion'),
    ('left', 'TkIgual', 'TkDesigualdad', 'TkMenor', 'TkMenorIgual', 'TkMayor', 'TkMayorIgual'),
    ('left', 'TkSuma', 'TkResta'),
    ('left', 'TkMult', 'TkDiv','TkMod'),
    ('right', 'TkNegacion'),
    ('right', 'UMENOS')
)

start = 'programa'

# Representa la estructura general de un programa en el lenguaje BOT
# Contiene la sección create (opcional) y la sección execute

def p_programa(p):
    '''programa : TkCreate bot_list TkExecute statement_list TkEnd
                 | TkExecute statement_list TkEnd'''
    if len(p) == 6:
        p[0] = ProgramNode(declaraciones=p[2], controlador=p[4])
    else:
        p[0] = ProgramNode(declaraciones=None, controlador=p[2])

# Lista de los identificadores de los bots, si existe contiene uno o más elementos

def p_bot_list(p):
    '''bot_list : bot_list bot_def
                | bot_def'''
    if len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    else:
        p[0] = BotListNode(bots=[p[1]])

# 

def p_bot_def(p):
    '''bot_def : tipo TkBot var_id_list on_list TkEnd
               | tipo TkBot var_id_list TkEnd'''
    if len(p) == 6:
        p[0] = BotDefNode(tipo=p[1], nombres=p[3], comportamientos=p[4])
    else:
        p[0] = BotDefNode(tipo=p[1], nombres=p[3], comportamientos=None)

# Reconocimiento del tipo al declarar un bot

def p_tipo(p):
    '''tipo : TkInt
            | TkBool
            | TkChar'''
    p[0] = p[1]

def p_var_id_list(p):
    '''var_id_list : var_id_list TkComa TkIdent
                   | TkIdent'''
    if len(p) == 4:
        p[1].append(VariableNode(p[3]))
        p[0] = p[1]
    else:
        p[0] = VarListNode(vars=[VariableNode(p[1])])

def p_on_list(p):
    '''on_list : on_list statement_on
              | statement_on'''
    if len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    else:
        p[0] = EstListNodes(statements=[p[1]])

def p_expression_aritmetica(p):
    '''expression : expression TkSuma expression
                  | expression TkResta expression
                  | expression TkMult expression
                  | expression TkDiv expression
                  | expression TkMod expression'''
    p[0] = AritOpNode(left=p[1], op=p[2], right=p[3])

def p_expression_relacional(p):
    '''expression : expression TkMenor expression
                  | expression TkMenorIgual expression
                  | expression TkMayor expression
                  | expression TkMayorIgual expression
                  | expression TkIgual expression
                  | expression TkDesigualdad expression'''
    p[0] = RelOpNode(left=p[1], op=p[2], right=p[3])

def p_expression_booleana(p):
    '''expression : expression TkConjuncion expression
                  | expression TkDisyuncion expression'''
    p[0] = BoolOpNode(left=p[1], op=p[2], right=p[3])

def p_expression_negado(p):
    'expression : TkNegacion expression'
    p[0] = UnaOpNode(op='~', expr=p[2])

def p_expression_negativa(p):
    'expression : TkResta expression %prec UMENOS'
    p[0] = UnaOpNode(op='-', expr=p[2])

def p_expression_parentesis(p):
    'expression : TkParAbre expression TkParCierra'
    p[0] = p[2] 
    
def p_statement_if(p):
    '''statement : TkIf expression TkDosPuntos statement_list TkEnd
                 | TkIf expression TkDosPuntos statement_list TkElse statement_list TkEnd'''
    if len(p) == 6:
        p[0] = IfNode(condicion=p[2], cuerpo=p[4])
    else:
        p[0] = IfNode(condicion=p[2], cuerpo=p[4], cuerpo_else=p[6])
        
def p_statement_while(p):
    'statement : TkWhile expression TkDosPuntos statement_list TkEnd'
    p[0] = WhileNode(condition=p[2], body=p[4])

def p_statement_on(p):
    '''statement_on : TkOn TkActivation TkDosPuntos statement_list TkEnd
                    | TkOn TkDeactivation TkDosPuntos statement_list TkEnd
                    | TkOn TkDeactivate TkDosPuntos statement_list TkEnd
                    | TkOn expression TkDosPuntos statement_list TkEnd
                    | TkOn TkDefault TkDosPuntos statement_list TkEnd'''
    p[0] = OnNode(p[2],p[4])

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    if len(p) == 3:
        p[1].append(p[2]) 
        p[0] = p[1]       
    else:
        p[0] = EstListNodes(statements=[p[1]])

def p_statement_controlador_con_args(p):
    '''statement : TkActivate var_list TkPunto
                 | TkDeactivate var_list TkPunto
                 | TkAdvance var_list TkPunto'''
    p[0] = ContNodes(action_name=p[1], var_list=p[2])

def p_statement_send(p):
    '''statement : TkSend TkPunto'''
    p[0] = ContNodes(action_name=p[1], var_list=VarListNode())

def p_statement_read(p):
    '''statement : TkRead TkPunto
                 | TkRead TkAs TkIdent TkPunto'''
    if len(p) == 3:
        p[0] = ReadNode(var_name=None)
    else:
        p[0] = ReadNode(var_name=p[3])

def p_statement_collect(p):
    '''statement : TkCollect TkPunto
                 | TkCollect TkAs TkIdent TkPunto'''
    if len(p) == 3:
        p[0] = CollectNode(var_name=None)
    else:
        p[0] = CollectNode(var_name=p[3])

def p_statement_drop(p):
    'statement : TkDrop expression TkPunto'
    p[0] = DropNode(expr=p[2])

def p_statement_movimiento(p):
    '''statement : TkLeft TkPunto
                 | TkRight TkPunto
                 | TkUp TkPunto
                 | TkDown TkPunto
                 | TkLeft expression TkPunto
                 | TkRight expression TkPunto
                 | TkUp expression TkPunto
                 | TkDown expression TkPunto'''
    if len(p) == 3:
        p[0] = MovimientoNode(direccion=p[1], expr=None)
    else:
        p[0] = MovimientoNode(direccion=p[1], expr=p[2])

def p_statement_store(p):
    'statement : TkStore expression TkPunto'
    p[0] = StoreNode(expr=p[2])

def p_var_list(p):
    '''var_list : var_list TkComa expression
                | expression'''
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]      
    else:
        p[0] = VarListNode(vars=[p[1]])

def p_variable(p):
    'expression : TkIdent'
    p[0] = VariableNode(p[1])
    
def p_numero(p):
    'expression : TkNum'
    p[0] = NumberNode(p[1])

def p_caracter(p):
    'expression : TkCaracter'
    p[0] = CharNode(p[1])
    
def p_booleano(p):
    '''expression : TkTrue
                  | TkFalse'''
    p[0] = BoolNode(p[1])
    
def p_error(p):
    if p:
        print(f"Error sintáctico: token inesperado '{p.value}' en la línea {p.lineno}")
        sys.exit(1) # Aborta en el primer error sintáctico
    else:
        print("Error sintáctico: fin de archivo inesperado (EOF)")
        sys.exit(1)

parser = yac.yacc(debug=True, write_tables=False)


# impresion del AST

diccionario_operadores = {
    '>': 'Mayor que', '<': 'Menor que', '>=': 'Mayor o igual que',
    '<=': 'Menor o igual que', '=': 'Igual', '/=': 'Diferente',
    '+': 'Suma', '-': 'Resta', '*': 'Multiplicacion', '/': 'Division', '%': 'Modulo',
    '/\\': 'Conjuncion', '\\/': 'Disyuncion'
}

NIVEL = "    "  # 4 espacios por nivel

def _nombre_var(var):
    return var.name if isinstance(var, VariableNode) else var

def _imprimir_expresion_inline(expr, sangria):
    """
    Imprime una expresion 'pegada' a la etiqueta que la precede
    (ej. 'guardia: BIN_RELACIONAL'), y sus detalles indentados debajo.
    El llamador ya hizo print(..., end="") antes de invocar esta funcion.
    """
    if isinstance(expr, RelOpNode):
        print("BIN_RELACIONAL")
        _imprimir_binop_detalle(expr, sangria + NIVEL)
    elif isinstance(expr, AritOpNode):
        print("BIN_ARITMETICO")
        _imprimir_binop_detalle(expr, sangria + NIVEL)
    elif isinstance(expr, BoolOpNode):
        print("BIN_BOOLEANO")
        _imprimir_binop_detalle(expr, sangria + NIVEL)
    elif isinstance(expr, UnaOpNode):
        nombre = "NEGACION" if expr.op == '~' else "NEGATIVO"
        print(nombre)
        print(f"{sangria}{NIVEL}- expresion: ", end="")
        _imprimir_expresion_inline(expr.expr, sangria + NIVEL)
    elif isinstance(expr, VariableNode):
        print(f"var: {expr.name}")
    elif isinstance(expr, NumberNode):
        print(f"valor: {expr.value}")
    elif isinstance(expr, BoolNode):
        print(f"valor: {expr.value}")
    elif hasattr(expr, 'value'):  # CharNode u otro nodo de literal con .value
        print(f"valor: {expr.value}")
    else:
        print("")
        imprimir_arbol(expr, sangria + NIVEL)

def _imprimir_operando(operando, sangria, etiqueta):
    if isinstance(operando, VariableNode):
        print(f"{sangria}- {etiqueta}: {operando.name}")
    elif isinstance(operando, NumberNode):
        print(f"{sangria}- {etiqueta}: {operando.value}")
    elif isinstance(operando, BoolNode):
        print(f"{sangria}- {etiqueta}: {operando.value}")
    elif hasattr(operando, 'value'):
        print(f"{sangria}- {etiqueta}: {operando.value}")
    else:
        print(f"{sangria}- {etiqueta}: ", end="")
        _imprimir_expresion_inline(operando, sangria)

def _imprimir_binop_detalle(nodo, sangria):
    simbolo = diccionario_operadores.get(nodo.op, nodo.op)
    print(f"{sangria}- operacion: '{simbolo}'")
    _imprimir_operando(nodo.left, sangria, "operador izquierdo")
    _imprimir_operando(nodo.right, sangria, "operador derecho")

def _imprimir_cuerpo(statements, sangria):
    for st in statements:
        imprimir_arbol(st, sangria)


def imprimir_arbol(nodo, sangria=""):
    if isinstance(nodo, ProgramNode):
        print(f"{sangria}SECUENCIACION")
        for st in nodo.controlador.statements:
            imprimir_arbol(st, sangria + NIVEL)

    elif isinstance(nodo, ContNodes):
        accion = "ACTIVACION" if nodo.action_name == "activate" else \
                 "AVANCE" if nodo.action_name == "advance" else \
                 "DESACTIVACION" if nodo.action_name in ("deactivate", "deactivation") else \
                 nodo.action_name.upper()
        print(f"{sangria}{accion}")
        for var in nodo.var_list.vars:
            print(f"{sangria}{NIVEL}- var: {_nombre_var(var)}")

    elif isinstance(nodo, StoreNode):
        print(f"{sangria}ALMACENAMIENTO")
        print(f"{sangria}{NIVEL}- valor: ", end="")
        _imprimir_expresion_inline(nodo.expr, sangria + NIVEL)

    elif isinstance(nodo, ReadNode):
        print(f"{sangria}LECTURA")
        if nodo.var_name is not None:
            print(f"{sangria}{NIVEL}- as: {nodo.var_name}")

    elif isinstance(nodo, CollectNode):
        print(f"{sangria}COLECCION")
        if nodo.var_name is not None:
            print(f"{sangria}{NIVEL}- as: {nodo.var_name}")

    elif isinstance(nodo, DropNode):
        print(f"{sangria}SOLTADO")
        print(f"{sangria}{NIVEL}- valor: ", end="")
        _imprimir_expresion_inline(nodo.expr, sangria + NIVEL)

    elif isinstance(nodo, MovimientoNode):
        print(f"{sangria}{nodo.direccion.upper()}")
        if nodo.expr is not None:
            print(f"{sangria}{NIVEL}- unidades: ", end="")
            _imprimir_expresion_inline(nodo.expr, sangria + NIVEL)

    elif isinstance(nodo, IfNode):
        print(f"{sangria}CONDICIONAL")
        print(f"{sangria}{NIVEL}- guardia: ", end="")
        _imprimir_expresion_inline(nodo.condicion, sangria + NIVEL)
        print(f"{sangria}{NIVEL}- exito:")
        _imprimir_cuerpo(nodo.cuerpo.statements, sangria + NIVEL * 2)
        if getattr(nodo, 'cuerpo_else', None):
            print(f"{sangria}{NIVEL}- fallo:")
            _imprimir_cuerpo(nodo.cuerpo_else.statements, sangria + NIVEL * 2)

    elif isinstance(nodo, WhileNode):
        print(f"{sangria}ITERACION")
        print(f"{sangria}{NIVEL}- guardia: ", end="")
        _imprimir_expresion_inline(nodo.condition, sangria + NIVEL)
        print(f"{sangria}{NIVEL}- cuerpo:")
        _imprimir_cuerpo(nodo.body.statements, sangria + NIVEL * 2)

    elif isinstance(nodo, (RelOpNode, AritOpNode, BoolOpNode)):
        nombre = "BIN_RELACIONAL" if isinstance(nodo, RelOpNode) else \
                 "BIN_ARITMETICO" if isinstance(nodo, AritOpNode) else \
                 "BIN_BOOLEANO"
        print(f"{sangria}{nombre}")
        _imprimir_binop_detalle(nodo, sangria + NIVEL)

    elif isinstance(nodo, UnaOpNode):
        nombre = "NEGACION" if nodo.op == '~' else "NEGATIVO"
        print(f"{sangria}{nombre}")
        print(f"{sangria}{NIVEL}- expresion: ", end="")
        _imprimir_expresion_inline(nodo.expr, sangria + NIVEL)

    else:
        # Fallback para nodos no contemplados (evita que se caiga silenciosamente)
        print(f"{sangria}NODO_DESCONOCIDO: {type(nodo).__name__}")


def parse(codigo_fuente):
    return parser.parse(codigo_fuente)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: ./SintBot <Archivo.bot>")
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
        imprimir_arbol(resultado)


