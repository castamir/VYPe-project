from SymbolTable import Symbol,SymbolTable

#
# scheme
# ( CODE, OPERAND1, OPERAND2, RESULT_LABEL )
#
# list of INSTRUCTIONS and their FORMAT
# =
#
# ADD
# SUB
# MUL
# DIV
#
# OR
# AND
#
# LT
# LQ
# GT
# GQ
# EQ
# NQ
#
# FUNCTION
# GOTO
#

class ThreeAddressCodeGenerator:
    def __init__(self):
        self.counter = 0
        self.labels = {
            'if': [],
            'endif': [],
            'else': [],
            'loop': [],
            'endloop': [],
        }

    def getLabel(self, type=None):
        if type not in self.labels and type is not None:
            # todo error
            pass
        self.counter += 1
        label = "$" + str(self.counter)
        if type in self.labels:
            self.labels[type].append(self.counter)
        return self.counter

    def add(self, p, operation, operand1=None, operand2=None):
        if not operation in self.labels:
            print 'UNKNOWN OPERATION', operation
            return None
        assert isinstance(operand1, Symbol)
        assert isinstance(operand2, Symbol)
        assert isinstance(p, list)
        if operand1.type in ['CINT', 'CSTRING', 'CCHAR']:
            p.append(('=', operand1, None, self.getLabel()))
            pass
        # todo label
        # todo type checking
        #return ('ADD', operand1, operand2, label)
        return p
