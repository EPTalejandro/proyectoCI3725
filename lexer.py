import ply.lex as lex
import sys

# Lista para caracteres que no pertenezcan a BOT
errores_lexicos = []

# Nombre de palabras reservadas por el lenguaje BOT
reservadas = [
    'create', 
    'while', 
    'bool', 
    'if', 
    'else', 
    'true', 
    'false', 
    'int', 
    'bot', 
    'on', 
    'activation', 
    'char',
    'store', 
    'end', 
    'execute', 
    'activate',
    'collect',
    'send',
    'drop',
    'left',
    'right',
    'up',
    'down',
    'deactivate',
    'advance',
    'receive',
    'default'
]
reservadas = {palabra: 'Tk' + palabra.capitalize() for palabra in reservadas}

# Son los tokens o etiquetas que PLY reconoce como parte del lenguaje 
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

# tanto las funciones como las variables que comienzan por "t_" la forma de decirle a la libreria PLY que lo definido a continuacion forma parte 
# del lenguaje que estamos construyendo (BOT), los simbolos que siempre seran iguales como (*,-,+) se guardan en variables, asi se le dice a la libreria
# que tipo de tokens son, es básicamente una regla de etiquetamiento 

# los espacios en blanco no forman parte del lenguaje, para ello se usa la variable especial de t_ignore para no tomarlo en cuenta
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

# Las funciones que comienzan por t_ son para decirle a PLY como debe guardarlos, pero se define como funcion ya que son expresiones que pueden variar,
# además de ser utilizadas por si se debe realizar algun procesado adicional a los datos antes de utilizarlos 

def t_TkIdent(t):
    r'[a-zA-Z][a-zA-Z0-9]*'
    t.type = reservadas.get(t.value, f'TkIdent("{t.value}")')
    return t

def t_TkNum(t):
    r'\d+'
    t.value = int(t.value)
    t.type = f'TkNum{(t.value)}'
    return t

def t_TkCaracter(t):
    r"'.'"
    t.type = 'TkCaracter'
    return t

def t_comentario_multiliea(t):
    r'\$-(.|\n)*?-\$'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_comentario_simple(t):
    r'\$\$.*\n'
    t.lexer.lineno += 1

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def columna(entrada, token):
    inicio_linea = entrada.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - inicio_linea) + 1

def t_error(t):
    global errores_lexicos
    col = columna(t.lexer.lexdata, t)
    mensaje = f'Error: Caracter inesperado "{t.value[0]}" en la fila {t.lineno}, columna {col}'
    errores_lexicos.append(mensaje)
    t.lexer.skip(1)

# al iniciar el lexer con lex.lex() se le dice que lea todas las reglas que definimos anteriormente para que pueda saber cuales son 
# sus reglas 
lexer = lex.lex()

# Verificación de la entrada de un archivo de texto
if len(sys.argv) < 2:
    sys.exit(1)

# Lee el achivo y luego lo pasa a lexer
with open(sys.argv[1], 'r') as archivo:
    d = archivo.read()

lexer.input(d)

tokens_salida = []

# Se itera sobre todos los caracteres del archivo, se obtiene su columna e informacion adicional que pueda dar, una vez hecho esto se guarda
# en la lista de tokens a imprimir
for t in lexer:
    col = columna(d, t)

    if t.type == 'TkIdent':
        extra = f'("{t.value}")'
    elif t.type == 'TkNum':
        extra = f'({t.value})'
    elif t.type == 'TkCaracter':
        extra = f"({t.value})"
    else:
        extra = ''

    tokens_salida.append(f'{t.type}{extra} {t.lineno} {col}')

# En caso de haber errores, sólo se imprimen estos, de no ser así se imprimen todos tokens
if errores_lexicos:
    for error in errores_lexicos:
        print(error)
else: 
    print(', '.join(tokens_salida))
