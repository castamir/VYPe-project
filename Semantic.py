from SymbolTable import *


class DeclaredFunctionNotDefinedException(Exception):
    pass


class IncompatibleTypesException(Exception):
    pass


class Semantic:
    def __init__(self):
        self._labels = 0
        self.error = 0
        self.symbol_table = SymbolTable()
        self.function_table = FunctionTable()

    def get_symbol_from_command(self, commands):
        op, op1, op2, name = commands[-1]
        return self.get_symbol(name)

    def get_symbol(self, name):
        return self.symbol_table.get(name)

    def add_temp_symbol(self, type):
        name = self._get_new_label()
        return self.add_symbol(name, type)

    def add_symbol(self, name, type):
        return self.symbol_table.add(name, type)

    def add_function(self, type, name, args=None, infinite=False):
        self.function_table.add(name, type, args, infinite)
        for symbol in self.function_table.functions[name].args:
            self.symbol_table.add(symbol.name, symbol.type)

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
        return "$%d" % self._labels

    def check_main_function(self):
        if not "main" in self.function_table.functions:
            raise NotFoundException("Function main not found")

    def check_forgotten_declarations(self):
        if len(self.function_table.declarations) != 0:
            dict = self.function_table.declarations
            first = dict[dict.keys()[0]]
            raise DeclaredFunctionNotDefinedException("Function '%s' declared, but not defined." % first.name)

    def start_function_scope(self, name):
        self.symbol_table.push_scope()

    def end_function_scope(self):
        self.symbol_table.pop_scope()
