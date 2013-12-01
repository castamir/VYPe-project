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
    elif len(p) == 3 and p[2] is not None:
        p[0] = p[1]
        p[0] = p[0] + p[2]


def p_global_statement(p):
    '''global_statement : variable_declaration
                        | function_definition
                        | function_declaration'''
    if p[1] is None:
        return None
    p[0] = p[1]
    return p


###########################
# variable declaration
###########################
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
# function declaration
###########################
def p_function_declaration(p):
    '''function_declaration : type ID LPAREN arg_types RPAREN SEMI
                            | void_arg_function SEMI'''
    if len(p) == 3:
        type, name, args = p[1]
    else:
        type = p[1]
        name = p[2]
        args = p[4]
    semantic.add_function_declaration(type, name, args)
    p[0] = []
    return p


def p_arg_types(p):
    '''arg_types : arg_types COMMA type
                 | type'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1]
        p[0].append(p[3])
    return p


###########################
# function definition
###########################
def p_void_arg_function(p):
    '''void_arg_function : type ID LPAREN VOID RPAREN'''
    p[0] = (p[1], p[2], None)
    return p


def p_function_definition(p):
    '''function_definition : function_header LBRACE block RBRACE'''
    p[0] = p[1] + p[3]
    semantic.end_function_scope()
    return p


def p_function_header(p):
    '''function_header : type ID LPAREN args RPAREN
                       | void_arg_function'''
    if len(p) == 2:
        type, name, args = p[1]
    else:
        type = p[1]
        name = p[2]
        args = p[4]
    semantic.start_function_scope(name)
    semantic.add_function(type, name, args)
    p[0] = []
    p[0].append(('FUNCTION', name, None, None))
    if args is not None:
        for arg in args:
            type, name = arg
            p[0].append(('ARG', type, name, None))
    return p


def p_args(p):
    '''args : args COMMA type ID
            | type ID'''
    if len(p) == 3:
        p[0] = [(p[1], p[2])]
    elif len(p) == 5:
        p[0] = p[1]
        p[0].append((p[3], p[4]))
    return p


###########################
# block
###########################
def p_block(p):
    '''block : empty
             | statement_list'''
    if not isinstance(p[1], list):
        p[0] = []
    else:
        p[0] = p[1]
    return p


def p_statement_list(p):
    '''statement_list : statement_list statement
                       | statement'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = p[1] + p[2]
    return p


def p_statement(p):
    '''statement : variable_declaration
                 | assignment'''
    p[0] = p[1]
    return p


def p_assignment(p):
    '''assignment : ID ASSIGN expr SEMI'''
    lsymbol = semantic.get_symbol(p[1])
    rsymbol = semantic.get_symbol_from_command(p[3])
    if lsymbol.type != rsymbol.type:
        raise IncompatibleTypesException(
            "Unable to assign value of type '%s' into a variable of type '%s'." % (rsymbol.type, lsymbol.type))
    p[0] = p[3] + [('=', rsymbol.name, None, lsymbol.name)]
    return p


def p_expr_arithmetic(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr
            | expr MODULO expr'''
    lsymbol = semantic.get_symbol_from_command(p[1])
    rsymbol = semantic.get_symbol_from_command(p[3])
    if lsymbol.type != rsymbol.type or lsymbol.type != 'int':
        raise IncompatibleTypesException(
            "Arithmetic operations requires int operands, '%s' and '%s' given." % (lsymbol.type, rsymbol.type))
    result = semantic.add_temp_symbol('int')
    p[0] = p[1] + p[3] + [(p[2], lsymbol.name, rsymbol.name, result.name)]
    return p


def p_expr_number(p):
    '''expr : CINT'''
    symbol = semantic.add_temp_symbol('int')
    p[0] = [('TEMP', p[1], None, symbol.name)]
    return p


def p_expr_char(p):
    '''expr : CCHAR'''
    symbol = semantic.add_temp_symbol('char')
    p[0] = [('TEMP', p[1], None, symbol.name)]
    return p


def p_expr_string(p):
    '''expr : CSTRING'''
    symbol = semantic.add_temp_symbol('string')
    p[0] = [('TEMP', p[1], None, symbol.name)]
    return p


def p_expr_single_variable(p):
    '''expr : ID'''
    symbol = semantic.get_symbol(p[1])
    p[0] = [('TEMP_FROM_ID', None, None, symbol.name)]
    return p


def p_expr_parentless(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = p[2]
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
    try:
        p = VYPeParser.parse(data, debug=debug)
        try:
            semantic.check_main_function()
            semantic.check_forgotten_declarations()
        except (NotFoundException, DeclaredFunctionNotDefinedException, IncompatibleTypesException) as e:
            p.parser.error = 3
            print >> sys.stderr, e.message
            return None
        return p
    except lex.LexError:
        VYPeParser.error = 1
        return None


