import sys


class LexicalErrorException(Exception):
    def __init__(self, message='', line=0):
        self.message = message
        self.line = line


# Reserved words
tokens = [# keywords and reserved words
          'CHAR', 'ELSE', 'IF', 'INT', 'RETURN', 'STRING', 'VOID', 'WHILE', 'BREAK', 'CONTINUE', 'FOR', 'SHORT',
          'UNSIGNED',

          # Literals (identifier, integer constant, string constant, char const)
          'ID', 'CINT', 'CSTRING', 'CCHAR',

          # Operators (+, -, *, /, %, ||, &&, !, <, <=, >, >=, ==, !=)
          'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO', 'UMINUS', 'FUNCTION', 'OR', 'AND', 'NOT', 'LT', 'LE', 'GT',
          'GE', 'EQ', 'NE',

          # Assignment (=)
          'ASSIGN',

          # Ternary operator (?)
          'TERNARY',

          # Delimeters ( ) , . ; :
          'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'COMMA', 'PERIOD', 'SEMI', 'COLON', ]

# Operators
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MODULO = r'%'
t_OR = r'\|\|'
t_AND = r'&&'
t_NOT = r'!'
t_LT = r'<'
t_GT = r'>'
t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='

# Assignment operators
t_ASSIGN = r'='

# ?
t_TERNARY = r'\?'

# Delimeters
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
t_PERIOD = r'\.'
t_SEMI = r';'
t_COLON = r':'

# String literal
def t_CSTRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1]
    return t

# Character constant 'c'
def t_CCHAR(t):
    r'\'([^\\\n]|(\\.))*?\''
    t.value = t.value[1:-1]
    # TODO check printable or escaped charater
    return t

# Integer literal
def t_CINT(t):
    r'\d+'
    t.value = (int)(t.value)
    return t

# Identifiers
def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    if t.value == 'char':
        t.type = 'CHAR'
    elif t.value == 'else':
        t.type = 'ELSE'
    elif t.value == 'if':
        t.type = 'IF'
    elif t.value == 'int':
        t.type = 'INT'
    elif t.value == 'return':
        t.type = 'RETURN'
    elif t.value == 'string':
        t.type = 'STRING'
    elif t.value == 'void':
        t.type = 'VOID'
    elif t.value == 'unsigned':
        t.type = 'UNSIGNED'
    elif t.value == 'short':
        t.type = 'SHORT'
    elif t.value == 'for':
        t.type = 'FOR'
    elif t.value == 'continue':
        t.type = 'CONTINUE'
    elif t.value == 'break':
        t.type = 'BREAK'
    elif t.value == 'while':
        t.type = 'WHILE'
    return t

# Comment (C-Style)
def t_COMMENT(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    #t.lexer.skip(1)

# Comment (C++-Style)
def t_BLOCKCOMMENT(t):
    r'//.*\n'
    t.lexer.lineno += 1
    #t.lexer.skip(1)


t_ignore = " \t"


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    raise LexicalErrorException("Illegal character '%s'" % t.value[0], t.lineno)
    #t.lexer.skip(1)
    #return None


# Build the lexer
import libs.ply.lex as lex

lex.lex()
