from lexer import tokens
import ply.yacc as yac

class Node:
    pass
class NumberNode(Node):
    def __init__(self, value): 
        self.value = value
        self.type = "int"
class BooleanNode(Node):
    def __init__(self, value):
        self.value = value
        self.type = "bool"
class BoolOpNode(Node):
    def __init__(self, left, op, right):
        self.left = left; self.op = op; self.right = right
        if left.type == "bool" and right.type == "bool":
            self.type = "bool"
        else:
            self.type = "error"
            print(f"Error de tipos: Operación booleana '{op}' requiere booleanos")
    def __str__(self): return f"LogOp({self.op}): {self.type}"
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
    ('right', 'TkNegacion',''),
    ('right', 'UMENOS')
)

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
    
def p_expression_numero(p):
    'expression : NUMBER'
    p[0] = NumberNode(p[1])