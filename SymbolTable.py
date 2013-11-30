class AlreadyDefinedException(Exception):
    pass


class NotFoundException(Exception):
    pass


class InvalidArgumentException(Exception):
    pass


class SymbolTable(list):
    def __init__(self):
        super(SymbolTable, self).__init__()
        self.scope = [{}]
        self.current = self.scope[0]

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
        return ", ".join(self.functions.keys())

    def add(self, name, type, args=None, infinite=False):
        if not args:
            args = []
        if self.is_declared(name):
            self.validate(self.declarations[name], args)
            del self.declarations[name]
        if name in self.functions:
            raise AlreadyDefinedException("Function '%s' is already defined" % name)
        types = []
        for a in args:
            types.append(a[0])
        self.functions[name] = Function(name, type, types, infinite)
        for a in args:
            self.functions[name].args.add(a[1], a[0])

    def declare(self, name, type, arg_types=None, infinite=False):
        if self.is_declared(name) or self.is_defined(name):
            return None
        self.declarations[name] = Function(name, type, arg_types, infinite)
        return self.declarations[name]

    def is_defined(self, name):
        return name in self.functions.keys

    def is_declared(self, name):
        return name in self.declarations.keys

    def validate(self, declaration, args):
        # TODO
        #raise InvalidArgumentException()
        pass


class Function:
    def __init__(self, name, type, arg_types=None, infinite=False):
        self.name = name
        self.type = type
        self.arg_types = arg_types
        self.has_infinite_args = infinite
        self.void = arg_types is None and infinite is False
        self.args = SymbolTable()


if __name__ == "__main__":
    table = SymbolTable()
    table.add('variable1', 'string')
    print table
    table.push_scope()
    table.add('vefunkci', 'int')
    table.add('vefunkci2', 'char')
    print table

