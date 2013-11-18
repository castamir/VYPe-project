import sys

sys.path.insert(0, "./libs")

# Reserved words
tokens = [
    # Literals (identifier, indentifier type, integer constant, string constant, char const)
    'ID', 'TYPEID', 'INTEGER', 'STRING', 'CHARACTER',

    # Operators (+, -, *, /, %, ||, &&, !, <, <=, >, >=, ==, !=)
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO',
    'OR', 'AND', 'NOT',
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',

    # Assignment (=)
    'EQUALS',

    # Ternary operator (?)
    'TERNARY',

    # Delimeters ( ) , . ; :
    'LPAREN', 'RPAREN',
    'COMMA', 'PERIOD', 'SEMI', 'COLON',
]

# Operators
t_PLUS             = r'\+'
t_MINUS            = r'-'
t_TIMES            = r'\*'
t_DIVIDE           = r'/'
t_MODULO           = r'%'
t_OR              = r'\|\|'
t_AND             = r'&&'
t_NOT             = r'!'
t_LT               = r'<'
t_GT               = r'>'
t_LE               = r'<='
t_GE               = r'>='
t_EQ               = r'=='
t_NE               = r'!='

# Assignment operators
t_EQUALS           = r'='

# ?
t_TERNARY          = r'\?'

# Delimeters
t_LPAREN           = r'\('
t_RPAREN           = r'\)'
t_COMMA            = r','
t_PERIOD           = r'\.'
t_SEMI             = r';'
t_COLON            = r':'

# Identifiers TODO - reserved strings and keywords
t_ID = r'[A-Za-z_][A-Za-z0-9_]*'

# Integer literal
def t_INTEGER(t):
    r'\d+'
    t.value = (int) (t.value)
    return t

# String literal
t_STRING = r'\"([^\\\n]|(\\.))*?\"'

# Character constant 'c' or L'c'
t_CHARACTER = r'(L)?\'([^\\\n]|(\\.))*?\''

# Comment (C-Style)
def t_COMMENT(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    t.lexer.skip(1)
    return t

# Comment (C++-Style)
def t_BLOCKCOMMENT(t):
    r'//.*\n'
    t.lexer.lineno += 1
    t.lexer.skip(1)
    return t

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
import ply.lex as lex

lex.lex()
