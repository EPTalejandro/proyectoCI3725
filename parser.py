from lexer import tokens
import ply.yacc as yac

class Node:
    pass

class ProgramNode():
    def __init__(self, create, execute):
        self.create = create
        self.execute = execute

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
    def __str__(self): 
        return f"Var({self.name})"
    
class IfNode(Node):
    def __init__(self, condicion, cuerpo, cuerpo_else=None):
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.cuerpo_else = cuerpo_else
        
class WhileNode(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
    def __str__(self): return "Instruccion_WHILE"
    
class OnNode(Node):
    def __init__(self, trigger, cuerpo):
        self.trigger = trigger
        self.cuerpo = cuerpo
    def __str__(self):
        return f"Bloque_ON(Disparador: {self.trigger})"
    
class EstListNodes(Node):
    def __init__(self, statements=None):
        if statements is None:
            self.statements = []
        else:
            self.statements = statements
    def append(self, statement):
        self.statements.append(statement)
    def __str__(self):
        return f"Bloque_De_Codigo({len(self.statements)} instrucciones)"
    
class ContNodes(Node):
    def __init__(self, action_name, var_list):
        self.action_name = action_name 
        self.var_list = var_list     
    def __str__(self):
        return f"ComandoMultiple_{self.action_name.upper()}"
    
class ControlerNode(Node):
    def __init__(self,nombre,vars):
        self.nombre=nombre
        self.vars=vars
        
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
        if left.type == "bool" and right.type == "bool":
            self.type = "bool"
        else:
            self.type = "error"
            print(f"Error de tipos: Operación booleana '{op}' requiere booleanos")
    def __str__(self): 
        return f"LogOp({self.op}): {self.type}"
    
class AritOpNode(Node):
    def __init__(self, left, op, right):
        self.left = left; self.op = op; self.right = right
        if left.type == "int" and right.type == "int":
            self.type = "int"
        else:
            self.type = "error"
            print(f"Error de tipos: No se puede aplicar '{op}' entre {left.type} y {right.type}")
    def __str__(self): return f"MathOp({self.op}): {self.type}"
    
class RelOpNode(Node):
    def __init__(self, left, op, right):
        self.left = left; self.op = op; self.right = right
        if left.type == "int" and right.type == "int":
            self.type = "bool"
        else:
            self.type = "error"
            print(f"Error de tipos: No se puede comparar {left.type} con {right.type}")
    def __str__(self): return f"RelOp({self.op}): {self.type}"
    
class UnaOpNode(Node):
    def __init__(self, op, expr):
        self.op = op; self.expr = expr

# Precedencia
precedence = (
    ('left', 'TkDisyuncion'),
    ('left', 'TkConjuncion'),
    ('left', 'TkIgual', 'TkMenor', 'TkMenorIgual', 'TkMayor', 'TkMayorIgual'),
    ('left', 'TkSuma', 'TkResta'),
    ('left', 'TkMult', 'TkDiv','TkMod'),
    ('right', 'TkNegacion'),
    ('right', 'UMENOS')
)

def p_programa(p):
    '''programa : TkCreate bot_list TkExecute statement_list TkEnd
                 | TkExecute statement_list TkEnd'''
    if len(p) == 5:
        p[0] = ProgramNode(declaraciones=p[2], controlador=p[4])
    else:
        p[0] = ProgramNode(declaraciones=None, controlador=p[2])

def p_bot_list(p):
    '''bot_list : bot_list bot_def
                | bot_def'''
    if len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    else:
        p[0] = BotListNode(bots=[p[1]])

def p_bot_def(p):
    '''bot_def : tipo TkBot var_id_list on_list TkEnd
               | tipo TkBot var_id_list TkEnd'''
    if len(p) == 6:
        p[0] = BotDefNode(tipo=p[1], nombres=p[3], comportamientos=p[4])
    else:
        p[0] = BotDefNode(tipo=p[1], nombres=p[3], comportamientos=None)

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
                  | expression TkIgual expression'''
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
                | TkIf expression TkDosPuntos statement_list TkElse statement TkEnd'''
    if len(p) == 8:
        p[0] = IfNode(condicion=p[2], cuerpo=p[4], cuerpo_else=p[6])
    else:
        p[0] = IfNode(condicion=p[2], cuerpo=p[4])
        
def p_statament_while(p):
    'statement : TkWhile expression TkDosPuntos statement_list TkEnd'
    # Sintaxis asumida: while condicion execute instrucciones end
    p[0] = WhileNode(condition=p[2], body=p[4])

def p_statament_on(p):
    '''statement : TkOn TkActivation TkDosPuntos statement_list TkEnd
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

def p_statement_controlador(p):
    '''statement : TkActivate var_list
                 | TkDeactivate var_list
                 | TkAdvance var_list'''
    
    # p[1] es el token del comando (TkActivate, TkDeactivate, o TkAdvance)
    # p[2] contiene el VarListNode que agrupó todos los elementos
    p[0] = ContNodes(action_name=p[1], var_list=p[2])

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
    
def p_booleano(p):
    '''expression : TkTrue
                  | TkFalse'''
    p[0] = BoolNode(p[1])
    
def p_error(p):
    if p:
        print(f"Error de sintaxis en línea {p.lineno}: token inesperado '{p.value}' (tipo {p.type})")
    else:
        print("Error de sintaxis: fin de archivo inesperado (EOF)")

parser = yac.yacc(debug=True)

def parse(codigo_fuente):
    return parser.parse(codigo_fuente)


