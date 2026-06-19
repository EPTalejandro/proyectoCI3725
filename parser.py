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

def p_statement_controlador_sin_args(p):
    '''statement : TkSend TkPunto
                 | TkReceive TkPunto
                 | TkCollect TkPunto
                 | TkDrop TkPunto
                 | TkLeft TkPunto
                 | TkRight TkPunto
                 | TkUp TkPunto
                 | TkDown TkPunto'''
    p[0] = ContNodes(action_name=p[1], var_list=VarListNode())

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
    p[0] = Node()
    p[0].value = p[1]
    
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

parser = yac.yacc(debug=False, write_tables=False)


# impresion del AST

diccionario_operadores = {
    '>': 'Mayor que', '<': 'Menor que', '>=': 'Mayor o igual que', 
    '<=': 'Menor o igual que', '=': 'Igual', '/=': 'Diferente',
    '+': 'Suma', '-': 'Resta', '*': 'Multiplicacion', '/': 'Division'
}

def imprimir_arbol(nodo, sangria=""):
    if isinstance(nodo, ProgramNode):
        print("SECUENCIACION")
        for st in nodo.controlador.statements:
            imprimir_arbol(st, sangria + "  ")
            
    elif isinstance(nodo, ContNodes):
        accion = "ACTIVACION" if nodo.action_name == "activate" else \
                 "AVANCE" if nodo.action_name == "advance" else \
                 "DESACTIVACION" if nodo.action_name in ("deactivate", "deactivation") else \
                 nodo.action_name.upper()
        print(f"{sangria}{accion}")
        for var in nodo.var_list.vars:
            nombre_var = var.name if isinstance(var, VariableNode) else var
            print(f"{sangria}  var: {nombre_var}")
            
    elif isinstance(nodo, StoreNode):
        print(f"{sangria}ALMACENAMIENTO")
        if isinstance(nodo.expr, NumberNode):
            print(f"{sangria}  valor: {nodo.expr.value}")
        elif isinstance(nodo.expr, VariableNode):
            print(f"{sangria}  var: {nodo.expr.name}")
        else:
            imprimir_arbol(nodo.expr, sangria + "  ")

    elif isinstance(nodo, IfNode):
        print(f"{sangria}CONDICIONAL")
        print(f"{sangria}  guardia: ", end="")
        imprimir_arbol(nodo.condicion, sangria + "    ")
        print(f"{sangria}  exito: ", end="")
        
        for st in nodo.cuerpo.statements:
            imprimir_arbol(st, sangria + "    ")
            
        if getattr(nodo, 'cuerpo_else', None):
            print(f"{sangria}  fallo: ", end="")
            for st in nodo.cuerpo_else.statements:
                imprimir_arbol(st, sangria + "    ")
            
    elif isinstance(nodo, RelOpNode):
        print(f"BIN_RELACIONAL")
        print(f"{sangria}  operacion: '{diccionario_operadores.get(nodo.op, nodo.op)}'")
        if isinstance(nodo.left, VariableNode):
            print(f"{sangria}  operador izquierdo: {nodo.left.name}")
        if isinstance(nodo.right, NumberNode):
            print(f"{sangria}  operador derecho: {nodo.right.value}")
            
    elif isinstance(nodo, AritOpNode):
        print(f"BIN_ARITMETICO")
        print(f"{sangria}  operacion: '{diccionario_operadores.get(nodo.op, nodo.op)}'")
        if isinstance(nodo.left, VariableNode):
            print(f"{sangria}  operador izquierdo: {nodo.left.name}")
        elif isinstance(nodo.left, NumberNode):
            print(f"{sangria}  operador izquierdo: {nodo.left.value}")
            
        if isinstance(nodo.right, VariableNode):
            print(f"{sangria}  operador derecho: {nodo.right.name}")
        elif isinstance(nodo.right, NumberNode):
            print(f"{sangria}  operador derecho: {nodo.right.value}")


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


