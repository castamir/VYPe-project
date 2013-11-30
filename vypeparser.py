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


def p_program(p):
    '''program : program global_statement
               | global_statement'''
    if len(p) == 2 and p[1]:
        try:
            semantic.check_main_function()
            semantic.check_forgotten_declarations()
        except (NotFoundException, DeclaredFunctionNotDefinedException) as e:
            p.parser.error = 3
            print >> sys.stderr, e.message
            return
        p[0] = []
        p[0].append(p[1])
    elif len(p) == 3 and p[2]:
        p[0] = p[1]
        if not p[0]: p[0] = []
        if p[2]:
            p[0].append(p[2])


def p_global_statement(p):
    '''global_statement : variable_declaration'''
    if p[1] is None:
        return None
        #op, type, name, value = p[1]
    #p[0] = (op, type, name, value)
    p[0] = p[1]
    return p


def p_variable_declaration(p):
    '''variable_declaration : type id_list SEMI'''
    type = p[2]
    for id in p[2]:
        try:
            semantic.add_symbol(id, type)
        except AlreadyDefinedException as e:
            p.parser.error = 3
            print >> sys.stderr, e.message
            return
    if p[1] == "string":
        init_value = ""
    elif p[1] == "char":
        init_value = '\0'
    else:
        init_value = 0
    p[0] = ('DIM', p[1], p[2], init_value)
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
        p[0] = []
        p[0].append(p[1])
    elif len(p) == 4:
        p[0] = p[1]
        if p[2]:
            p[0].append(p[3])
    return p

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
    try:
        p = VYPeParser.parse(data, debug=debug)
        return p
    except lex.LexError:
        VYPeParser.error = 1
        return None


