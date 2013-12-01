import copy


class AlreadyDefinedException(Exception):
    pass


class NotFoundException(Exception):
    pass


class InvalidArgumentException(Exception):
    pass


class TooManyArgumentsException(InvalidArgumentException):
    pass


class TooFewArgumentsException(InvalidArgumentException):
    pass


class InvalidTypeException(InvalidArgumentException):
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
        self.current = self.scope.pop()

    def add(self, name, type):
        if name in self.current:
            raise AlreadyDefinedException("Identifier '%s' is already defined" % name)
        self.current[name] = Symbol(name, type)

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

    def __str__(self):
        functions = []
        for name in self.functions:
            f = self.functions[name]
            if f.is_void():
                args = 'void'
            else:
                args = []
                for arg in f.args:
                    args.append(arg.type)
                args = ", ".join(args)
            description = f.type + " " + f.name + "(" + args + ")"
            functions.append(description)
        return ", ".join(functions)

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
                given_type, name = given_args.pop()
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
        self.void = arg_types is None and infinite is False
        self.args = []

    def is_void(self):
        if self.has_infinite_args or len(self.args) > 0:
            return False
        return True


if __name__ == "__main__":
    table = SymbolTable()
    table.add('variable1', 'string')
    print table
    table.push_scope()
    table.add('vefunkci', 'int')
    table.add('vefunkci2', 'char')
    print table

