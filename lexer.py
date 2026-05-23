import ply.lex as lex
import sys

errores_lexicos = []

reservadas = [
    'create', 
    'while', 
    'bool', 
    'if', 
    'true', 
    'false', 
    'int', 
    'bot', 
    'on', 
    'activation', 
    'store', 
    'end', 
    'execute', 
    'activate'
]
reservadas = {palabra: 'Tk' + palabra.capitalize() for palabra in reservadas}

tokens = [
    'TkIdent', 
    'TkNum', 
    'TkCaracter',
    'TkComa', 
    'TkPunto', 
    'TkDosPuntos', 
    'TkParAbre', 
    'TkParCierra',
    'TkSuma', 
    'TkResta', 
    'TkMult', 
    'TkDiv', 
    'TkMod',
    'TkConjuncion', 
    'TkDisyuncion', 
    'TkNegacion',
    'TkMenor', 
    'TkMenorIgual', 
    'TkMayor', 
    'TkMayorIgual', 
    'TkIgual'
] + list(reservadas.values())

t_ignore = ' \t'

t_TkComa = r'\,'
t_TkPunto = r'\.'
t_TkDosPuntos = r'\:'
t_TkParAbre = r'\('
t_TkParCierra = r'\)'
t_TkSuma = r'\+'
t_TkResta = r'\-'
t_TkMult = r'\*'
t_TkDiv = r'/'
t_TkMod = r'%'
t_TkConjuncion = r'/\\'
t_TkDisyuncion = r'\\/'
t_TkNegacion = r'~'
t_TkMenor = r'<'
t_TkMenorIgual = r'<='
t_TkMayor = r'>'
t_TkMayorIgual = r'>='
t_TkIgual = r'='

def t_TkIdent(t):
    r'[a-zA-Z][a-zA-Z0-9]*'
    t.type = reservadas.get(t.value, 'TkIdent')
    return t

def t_TkNum(t):
    r'\d+'
    t.value = int(t.value)
    t.type = 'TkNum'
    return t

def t_TkCaracter(t):
    r"'.'"
    t.type = 'TkCaracter'
    return t

def t_comentario(t):
    r'\$-(.|\n)*?-\$'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def columna(entrada, token):
    inicio_linea = entrada.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - inicio_linea) + 1

def t_error(t):
    col = columna(t.lexer.lexdata, t)
    mensaje = f'Error: Caracter inesperado "{t.value[0]}" en la fila {t.lineno}, columna {col}'
    errores_lexicos.append(mensaje)
    t.lexer.skip(1)

lexer = lex.lex()

if len(sys.argv) < 2:
    sys.exit(1)

with open(sys.argv[1], 'r') as archivo:
    d = archivo.read()

lexer.input(d)

tokens_salida = []
for t in lexer:
    col = columna(d, t)
    if t.type == 'TkIdent':
        extra = f'("{t.value}")'
    elif t.type == 'TkNum':
        extra = f'({t.value})'
    elif t.type == 'TkCaracter':
        extra = f"('{t.value}')"
    else:
        extra = ''
    tokens_salida.append(f'{t.type}{extra} {t.lineno} {col}')

if errores_lexicos:
    for error in errores_lexicos:
        print(error)
else: 
    print(', '.join(tokens_salida))
