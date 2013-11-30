'''
empty :

program                 : function_declaration
                        | function_definition
                        | var_declaration

var_declaration         : type id var_list

var_list                : , type var_list
                        | empty

function_declaration    : type id ( param_types ) ;

param_types             : void
                        | type param_type_list

param_type_list         : , type param_type_list
                        | empty

function_definition     : type id ( params ) { block }

params                  : void
                        | param_item param_list

param_list              : , param_item param_list
                        | empty

param_item              : type id

block                   : statement block
                        | empty

statement               : assignment
                        | var_declaration
                        | condition
                        | loop
                        | function_call
                        | return

assignment              : id = expr ;
if_statement            : if ( expr ) { block } else_statement
else_statement          : else { block }
                        | empty
loop                    : while ( expr ) { block }
function_call           : id ( ) ;
return                  : return return_value ;
return_value            : expr
                        | empty

expr                    : expr + expr
                        | expr - expr
                        | expr * expr
                        | expr / expr
                        | expr % expr
                        | expr < expr
                        | expr <= expr
                        | expr > expr
                        | expr >= expr
                        | expr == expr
                        | expr != expr
                        | CINT
                        | ID


'''

from Semantic import *
import lexer
import sys

sys.path.insert(0, "./libs")

tokens = lexer.tokens

semantic = Semantic()
semantic.add_predefined_function('void', 'print', infinite=True)
semantic.add_predefined_function('string', 'read_string')
semantic.add_predefined_function('char', 'read_char')
semantic.add_predefined_function('int', 'read_int')
semantic.add_predefined_function('char', 'get_at', ['string', 'int'])
semantic.add_predefined_function('char', 'set_at', ['string', 'int', 'char'])

# Parsing rules

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NE'),
    ('left', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    ('left', 'NOT'),
    ('right', 'UMINUS'),
    ('right', 'FUNCTION'),
)

code = {}


def p_program(p):
    '''program : program global_statement
               | global_statement'''
    if len(p) == 2 and p[1]:
        p[0] = p[1]
    elif len(p) == 3 and p[2]:
        p[0] = p[1]
        p[0] = p[0] + p[2]


def p_global_statement(p):
    '''global_statement : variable_declaration
                        | function_definition'''
    if p[1] is None:
        return None
    p[0] = p[1]
    return p

###########################
# variable declaration

def p_variable_declaration(p):
    '''variable_declaration : type id_list SEMI'''
    p[0] = []
    type = p[1]
    if type == "string":
        init_value = ""
    elif type == "char":
        init_value = '\0'
    else:
        init_value = 0
    for name in p[2]:
        try:
            semantic.add_symbol(name, type)
        except AlreadyDefinedException as e:
            p.parser.error = 3
            print >> sys.stderr, e.message
            return
        p[0].append(('DIM', p[1], name, init_value))
    return p


def p_type(p):
    '''type : INT
            | CHAR
            | STRING'''
    p[0] = p[1]
    return p


def p_id_list(p):
    '''id_list : id_list COMMA ID
               | ID'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1]
        p[0].append(p[3])
    return p


###########################
# function definition
def p_function_definition(p):
    '''function_definition : function_header LBRACE block RBRACE'''
    p[0] = p[1] + p[3]
    semantic.end_function_scope()
    return p


def p_function_header(p):
    '''function_header : type ID LPAREN function_args RPAREN'''
    semantic.start_function_scope(p[2])
    semantic.add_function(p[1], p[2], p[4])
    p[0] = []
    p[0].append(('FUNCTION', p[2], None, None))
    if p[4] is not None:
        for arg in p[4]:
            type, name = arg
            p[0].append(('ARG', type, name, None))
    return p


def p_function_args(p):
    '''function_args : VOID
                     | args'''
    if p[1] == "void":
        p[0] = None
    else:
        p[0] = p[1]
    return p


def p_args(p):
    '''args : args COMMA type ID
            | type ID'''
    if len(p) == 3:
        p[0] = [[p[1], p[2]]]
    elif len(p) == 5:
        p[0] = p[1]
        p[0].append([p[3], p[4]])
    return p


###########################
# block
def p_block(p):
    '''block : empty
             | non_empty_block'''
    if not isinstance(p[1], list):
        p[0] = []
    else:
        p[0] = p[1]
    return p


def p_non_empty_block(p):
    '''non_empty_block : non_empty_block variable_declaration
                       | variable_declaration'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 3:
        p[0] = p[1]
        p[0].append(p[2])
    return p


#### empty production
def p_empty(p):
    '''empty :'''


#### Catastrophic error handler
def p_error(p):
    if not p:
        print >> sys.stderr, "Syntax error at the end of file"
    VYPeParser.error = 2


import ply.yacc as yacc
import ply.lex as lex

VYPeParser = yacc.yacc()


def parse(data, debug=0):
    global VYPeParser
    VYPeParser.error = 0
    global code
    code = {0: ("BEGIN", None, None, None)}
    try:
        p = VYPeParser.parse(data, debug=debug)
        #try:
        #    semantic.check_main_function()
        #    semantic.check_forgotten_declarations()
        #except (NotFoundException, DeclaredFunctionNotDefinedException) as e:
        #    p.parser.error = 3
        #    print >> sys.stderr, e.message
        #    return None
        return p
    except lex.LexError:
        VYPeParser.error = 1
        return None


