import copy


class SemanticErrorException(Exception):
    def __init__(self, message='', line=0):
        self.message = message
        self.line = line


class InvalidArgumentException(SemanticErrorException):
    pass


class TooManyArgumentsException(InvalidArgumentException):
    pass


class TooFewArgumentsException(InvalidArgumentException):
    pass


class InvalidTypeException(InvalidArgumentException):
    pass


class AlreadyDefinedException(SemanticErrorException):
    pass


class NotFoundException(SemanticErrorException):
    pass


class DeclaredFunctionNotDefinedException(SemanticErrorException):
    pass


class IncompatibleTypesException(SemanticErrorException):
    pass


class SymbolTable(list):
    def __init__(self):
        super(SymbolTable, self).__init__()
        self.scope = [{}]
        self.current = self.scope[0]

    def is_empty(self):
        return len(self.get_visible_symbols()) == 0

    def push_scope(self):
        self.current = {}
        self.scope.append(self.current)

    def pop_scope(self):
        self.scope.pop()
        self.current = self.scope[-1]

    def add(self, name, type, rename=True):
        if name in self.current:
            raise AlreadyDefinedException("Identifier '%s' is already defined" % name)
        if rename:
            self.current[name] = Symbol("x%s" % name, type)
        else:
            self.current[name] = Symbol(name, type)
        return self.current[name]

    def get(self, name):
        symbols = self.get_visible_symbols()
        if not name in symbols.keys():
            raise NotFoundException("Identifier '%s' not found" % name)
        return symbols[name]

    def get_visible_symbols(self):
        symbols = {}
        for scope in self.scope:
            for symbol in scope:
                symbols[symbol] = scope[symbol]
        return symbols

    def __str__(self):
        return ", ".join(self.get_visible_symbols().keys())


class Symbol:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class FunctionTable:
    def __init__(self):
        self.declarations = {}
        self.functions = {}
        self.current = None

    def __str__(self):
        functions = []
        for name in self.functions:
            f = self.functions[name]
            if f.has_void_args():
                args = 'void'
            else:
                args = []
                for arg in f.args:
                    args.append(arg.type)
                args = ", ".join(args)
            description = f.type + " " + f.name + "(" + args + ")"
            functions.append(description)
        return ", ".join(functions)

    def get(self, name):
        if self.is_declared(name):
            return self.declarations[name]
        elif self.is_defined(name):
            return self.functions[name]
        else:
            raise NotFoundException("Function '%s' not found." % name)

    def add(self, name, type, args=None, infinite=False):
        if args is None:
            args = []
        if self.is_declared(name):
            self.validate(self.declarations[name], args)
            del self.declarations[name]
        if name in self.functions:
            raise AlreadyDefinedException("Function '%s' is already defined." % name)
        types = []
        for a in args:
            types.append(a[0])
        self.functions[name] = Function(name, type, types, infinite)
        for a in args:
            self.functions[name].args.append(Symbol(a[1], a[0]))
        if name == "main":
            if len(self.functions[name].args) > 0:
                raise InvalidArgumentException("Function main can not have arguments.")
            if self.functions[name].type != "int":
                raise InvalidTypeException(
                    "Invalid argument of function main. Expected 'int', but '%s' given." % self.functions[name].type)

    def declare(self, name, type, arg_types=None, infinite=False):
        if self.is_declared(name) or self.is_defined(name):
            return None
        self.declarations[name] = Function(name, type, arg_types, infinite)
        return self.declarations[name]

    def is_defined(self, name):
        return name in self.functions

    def is_declared(self, name):
        return name in self.declarations

    def validate(self, declaration, args):
        if declaration.arg_types is None:
            declared = 0
        else:
            declared = len(declaration.arg_types)
        if args is None:
            defined = 0
        else:
            defined = len(args)
        if declared < defined:
            raise TooManyArgumentsException(
                "Too many arguments in the definition of function '%s'. Expected %d, but %d given." % (
                    declaration.name, declared, defined))
        elif declared > defined:
            raise TooFewArgumentsException(
                "Too few arguments in the definition of function '%s'. Expected %d, but %d given." % (
                    declaration.name, declared, defined))
        elif defined != 0:
            given_args = copy.copy(args)
            for expected_type in declaration.arg_types:
                given_type, name = given_args.pop(0)
                if expected_type != given_type:
                    raise InvalidArgumentException(
                        "Invalid argument of function '%s'. Expected '%s', but '%s' given." % (
                            declaration.name, expected_type, given_type))


class Function:
    def __init__(self, name, type, arg_types=None, infinite=False):
        self.name = name
        self.type = type
        self.arg_types = arg_types
        self.has_infinite_args = infinite
        self.args = []

    def has_void_args(self):
        if self.has_infinite_args or len(self.args) > 0:
            return False
        return True


class Semantic:
    def __init__(self):
        self._labels = 0
        self.error = 0
        self.symbol_table = SymbolTable()
        self.function_table = FunctionTable()

    def get_symbol_from_command(self, commands):
        op, op1, op2, name = commands[-1]
        if not name.startswith("tm_"):
            name = name[1:]
        return self.get_symbol(name)

    def get_symbol(self, name):
        return self.symbol_table.get(name)

    def get_function(self, name):
        return self.function_table.get(name)

    def add_temp_symbol(self, type):
        name = self._get_new_label()
        return self.add_symbol(name, type, False)

    def add_symbol(self, name, type, rename=True):
        return self.symbol_table.add(name, type, rename)

    def add_function(self, type, name, args=None, infinite=False):
        self.function_table.add(name, type, args, infinite)
        for symbol in self.function_table.functions[name].args:
            self.symbol_table.add(symbol.name, symbol.type)
        self.function_table.current = self.function_table.functions[name]

    def add_function_declaration(self, type, name, arg_types=None, infinite=False):
        self.function_table.declare(name, type, arg_types, infinite)

    def add_predefined_function(self, type, name, arg_types=None, infinite=False):
        if arg_types is not None:
            args = []
            for arg_type in arg_types:
                args.append([arg_type, self._get_new_label()])
            self.function_table.add(name, type, args, infinite)
        else:
            self.function_table.add(name, type, None, infinite)

    def _get_new_label(self):
        self._labels += 1
        return "tm_%d" % self._labels

    def check_main_function(self):
        if not "main" in self.function_table.functions:
            raise NotFoundException("Function main not found")

    def check_forgotten_declarations(self):
        if len(self.function_table.declarations) != 0:
            dictionary = self.function_table.declarations
            first = dictionary[dictionary.keys()[0]]
            raise DeclaredFunctionNotDefinedException("Function '%s' declared, but not defined." % first.name)

    def start_function_scope(self, name):
        self.symbol_table.push_scope()

    def end_function_scope(self):
        self.symbol_table.pop_scope()
        self.function_table.current = None

    def get_current_function(self):
        return self.function_table.current

    def get_loop_start_label(self):
        self._labels += 1
        return "loop_start_%d" % self._labels

    def get_loop_end_label(self):
        self._labels += 1
        return "loop_end_%d" % self._labels

    def get_if_true_label(self):
        self._labels += 1
        return "if_true_%d" % self._labels

    def get_if_end_label(self):
        self._labels += 1
        return "endif_%d" % self._labels

    def validate(self, function, types):
        function_arg_types = copy.copy(function.arg_types)
        for t in types:
            try:
                ft = function_arg_types.pop(0)
            except IndexError:
                if function.has_infinite_args:
                    continue
                raise TooManyArgumentsException("Too many arguments. Expected %d, but %d given." % (len(function.arg_types), len(types)))
            if ft != '*' and t != ft:
                raise InvalidTypeException("Incompatible type '%s', expected '%s'." % (t, ft))
        if len(function_arg_types) > 0:
            raise TooFewArgumentsException("Too few arguments. Expected %d, but %d given." % (len(function.arg_types), len(types)))

    def add_param_order_to_commands(self, commands):
        fixed_commands = []
        params = 1
        for c in commands:
            op, p1, p2, p3 = c
            if op == "PARAM" and p2 is None:
                c = (op, p1, params, p3)
                params += 1
            fixed_commands.append(c)
        return fixed_commands
