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

    def add_symbol(self, name, type):
        # TODO test if symbol is defined in current scope
        self.current[name] = Symbol(name, type)

    def find_symbol(self, name):
        # TODO bubble through a whole scope a and find symbol or throw an error
        pass


class Symbol:
    def __init__(self, name, type):
        self.name = name
        self.type = type

