from Semantic import *
import Scanner
import sys


class ParserBaseException(Exception):
    def __init__(self, message='', line=0):
        self.message = message
        self.line = line


class SyntaxErrorException(ParserBaseException):
    pass


class EOFException(SyntaxErrorException):
    pass


tokens = Scanner.tokens

semantic = Semantic()

# Parsing rules

precedence = (
    ('left', 'OR'), ('left', 'AND'), ('left', 'EQ', 'NE'), ('left', 'LT', 'LE', 'GT', 'GE'), ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'), ('right', 'NOT'), ('right', 'UMINUS'), ('right', 'FUNCTION'),
)

code = {}


def p_program(p):
    '''program : program global_statement
               | global_statement'''
    if len(p) == 2:
        if p[1] is None:
            return None
        p[0] = p[1]
    elif len(p) == 3:
        if p[1] is None or p[2] is None:
            return None
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
            e.line = p.lineno(-1)
            raise
        p[0].append(('DIM', p[1], init_value, name))
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

    if len(p) > 0:
        last_statement = p[0][-1]
        statement, arg2, arg3, arg4 = last_statement
        found = statement == "RETURN"
    else:
        found = False
        # function without return statement
    if not found:
        function = semantic.get_current_function()
        if function.type == 'void':
            p[0] = p[0] + [('RETURN', None, None, None)]
        elif function.type == 'int':
            symbol = semantic.add_temp_symbol(function.type)
            if function.type == "string":
                init_value = ""
            elif function.type == "char":
                init_value = '\0'
            else:
                init_value = 0
            p[0] = p[0] + [('TEMP', function.type, init_value, symbol.name), ('RETURN', symbol.name, None, None)]

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
    args_counter = 0
    if args is not None:
        for arg in args:
            args_counter += 1
            type, name = arg
            p[0].append(('ARG', type, args_counter, name))
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
                 | assignment
                 | return
                 | if_statement
                 | loop_statement'''
    p[0] = p[1]
    return p


def p_loop_statement(p):
    '''loop_statement : WHILE LPAREN expr RPAREN block_body'''
    symbol = semantic.get_symbol_from_command(p[3])
    label_start = semantic.get_loop_start_label()
    label_end = semantic.get_loop_end_label()
    p[0] = []
    p[0] += [('LABEL', None, None, label_start)]
    p[0] += p[3]
    # jump to the end if zero (if false)
    p[0] += [('JZ', symbol.name, None, label_end)]
    # loop body
    p[0] += p[5]
    p[0] += [('JUMP', None, None, label_start)]
    p[0] += [('LABEL', None, None, label_end)]
    return p


def p_if_statement(p):
    '''if_statement : IF LPAREN expr RPAREN block_body if_false'''
    symbol = semantic.get_symbol_from_command(p[3])
    label_true = semantic.get_if_true_label()
    label_end = semantic.get_if_end_label()
    p[0] = p[3]
    # jump to else branch if not zero (if not false)
    p[0] += [('JNZ', symbol.name, None, label_true)]
    # else branch
    p[0] += p[6]
    p[0] += [('JUMP', None, None, label_end)]
    p[0] += [('LABEL', None, None, label_true)]
    # true branch
    p[0] += p[5]
    # end of statement
    p[0] += [('LABEL', None, None, label_end)]
    return p


def p_if_false(p):
    '''if_false : ELSE block_body'''
    p[0] = p[2]
    return p


def p_block_body(p):
    '''block_body : block_start block_end'''
    p[0] = p[2]
    return p


def p_block_start(p):
    '''block_start : LBRACE'''
    semantic.symbol_table.push_scope()
    return p


def p_block_end(p):
    '''block_end : block RBRACE'''
    p[0] = p[1]
    semantic.symbol_table.pop_scope()
    return p


def p_return(p):
    '''return : RETURN expr SEMI
              | RETURN SEMI'''
    if len(p) == 3:
        if semantic.get_current_function().type == 'void':
            raise InvalidArgumentException("Void functions cannot return a value.", p.lineno(-1))
        p[0] = [('RETURN', None, None, None)]
    else:
        symbol = semantic.get_symbol_from_command(p[2])
        current_function = semantic.get_current_function()
        if current_function.type != 'void':
            raise InvalidArgumentException("Non-void functions cannot have a non-value return statement.", p.lineno(-1))
        if current_function.type != symbol.type:
            raise InvalidArgumentException(
                "Invalid type of a return value. Expected '%s', but '%s' given" % (current_function.type, symbol.type),
                p.lineno(-1))
        p[0] = p[2] + [('RETURN', symbol.name, None, None)]
    return p


def p_assignment(p):
    '''assignment : ID ASSIGN expr SEMI'''
    lsymbol = semantic.get_symbol(p[1])
    rsymbol = semantic.get_symbol_from_command(p[3])
    if lsymbol.type != rsymbol.type:
        raise IncompatibleTypesException(
            "Unable to assign value of type '%s' into a variable of type '%s'." % (rsymbol.type, lsymbol.type),
            p.lineno(-1))
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
            "Arithmetic operations requires int operands, '%s' and '%s' given." % (lsymbol.type, rsymbol.type),
            p.lineno(-1))
    result = semantic.add_temp_symbol('int')
    p[0] = p[1] + p[3] + [(p[2], lsymbol.name, rsymbol.name, result.name)]
    return p


def p_expr_number(p):
    '''expr : CINT'''
    symbol = semantic.add_temp_symbol('int')
    p[0] = [('TEMP', 'int', p[1], symbol.name)]
    return p


def p_expr_char(p):
    '''expr : CCHAR'''
    symbol = semantic.add_temp_symbol('char')
    p[0] = [('TEMP', 'char', p[1], symbol.name)]
    return p


def p_expr_string(p):
    '''expr : CSTRING'''
    symbol = semantic.add_temp_symbol('string')
    p[0] = [('TEMP', 'string', p[1], symbol.name)]
    return p


def p_expr_single_variable(p):
    '''expr : ID'''
    symbol = semantic.get_symbol(p[1])
    p[0] = [('LOAD', symbol.type, None, symbol.name)]
    return p


def p_expr_parentless(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = p[2]
    return p


def p_expr_uminus(p):
    '''expr : MINUS expr %prec UMINUS'''
    symbol = semantic.get_symbol_from_command(p[2])
    if symbol.type != 'int':
        raise IncompatibleTypesException("Unary minus requires 'int', but '%s' given." % symbol.type, p.lineno(-1))
    result = semantic.add_temp_symbol('int')
    p[0] = p[2] + [('UMINUS', symbol.name, None, result.name)]
    return p


def p_expr_explicit_retype(p):
    '''expr : LPAREN type RPAREN LPAREN expr RPAREN'''
    symbol = semantic.get_symbol_from_command(p[4])
    new_symbol = semantic.add_temp_symbol(p[2])
    if symbol.type == 'int' and new_symbol.type == 'char':
        instruction = 'INT_TO_CHAR'
    elif symbol.type == 'char' and new_symbol.type == 'string':
        instruction = 'CHAR_TO_STRING'
    elif symbol.type == 'char' and new_symbol.type == 'int':
        instruction = 'CHAR_TO_INT'
    else:
        raise InvalidTypeException("Unable to convert '%s' to '%s'." % (symbol.type, new_symbol.type), p.lineno(-1))
    p[0] = p[4] + [(instruction, symbol.name, None, new_symbol.name)]
    return p


def p_expr_bool(p):
    '''expr : expr OR expr
            | expr AND expr'''
    lsymbol = semantic.get_symbol_from_command(p[1])
    rsymbol = semantic.get_symbol_from_command(p[3])
    if lsymbol.type != 'int' or rsymbol.type != 'int':
        raise IncompatibleTypesException(
            "Logic operations requires int operands, '%s' and '%s' given." % (lsymbol.type, rsymbol.type), p.lineno(-1))
    result = semantic.add_temp_symbol('int')
    p[0] = p[1] + p[3] + [(p[2], lsymbol.name, rsymbol.name, result.name)]
    return p


def p_expr_bool_not(p):
    '''expr : NOT expr %prec NOT'''
    symbol = semantic.get_symbol_from_command(p[2])
    if symbol.type != 'int':
        raise IncompatibleTypesException("Logic NOT requires int operand, '%s' given." % symbol.type, p.lineno(-1))
    result = semantic.add_temp_symbol('int')
    p[0] = p[2] + [('NOT', symbol.name, None, result.name)]
    return p


def p_expr_relation(p):
    '''expr : expr EQ expr
            | expr NE expr
            | expr LT expr
            | expr LE expr
            | expr GT expr
            | expr GE expr'''
    lsymbol = semantic.get_symbol_from_command(p[1])
    rsymbol = semantic.get_symbol_from_command(p[3])
    if lsymbol.type != rsymbol.type:
        raise IncompatibleTypesException(
            "Relation operations requires operands of the same type, '%s' and '%s' given." % (
                lsymbol.type, rsymbol.type), p.lineno(-1))
    result = semantic.add_temp_symbol('int')
    p[0] = p[1] + p[3] + [(p[2], lsymbol.name, rsymbol.name, result.name)]
    return p


#### empty production
def p_empty(p):
    '''empty :'''


#### Catastrophic error handler
def p_error(p):
    if not p:
        raise EOFException("Unexpected end of file.")
    raise SyntaxErrorException("syntax error", p.lineno)


import libs.ply.yacc as yacc
import libs.ply.lex as lex

VYPeParser = yacc.yacc()


def parse(data, debug=0):
    global VYPeParser, semantic
    semantic = Semantic()
    semantic.add_predefined_function('void', 'print', infinite=True)
    semantic.add_predefined_function('string', 'read_string')
    semantic.add_predefined_function('char', 'read_char')
    semantic.add_predefined_function('int', 'read_int')
    semantic.add_predefined_function('char', 'get_at', ['string', 'int'])
    semantic.add_predefined_function('char', 'set_at', ['string', 'int', 'char'])
    semantic.add_predefined_function('string', 'strcat', ['string', 'string'])

    p = VYPeParser.parse(data, debug=debug)
    semantic.check_main_function()
    semantic.check_forgotten_declarations()
    return p


