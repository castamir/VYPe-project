__author__ = 'Malanka'

# first typ operace
# second je prvni operand
# third je druhy operand
# forth je vysledek
# .globl visible outside the module

list_reg = ['zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3', 'k0', 'k1', 'gp', 'sp',
            'fp', 'ra', 't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 's0', 's1', 's2', 's3', 's4', 's5',
            's6', 's7']
ForRead = 'read'
ForWrite = 'write'


class CodeGenerator:
    Reg = {}  #reserved , None   free, None ,   used , name_of_variable
    AddressTable = {}   #( memory, (segment,offset), registername, namevariable)
    goffset = 0
    foffset = []    #indicates offsets in segments. Always of the first free "row"

    def use_register(self, preg, varname):
        self.Reg[preg] = 'used', varname

    def free_register(self, preg):
        self.Reg[preg] = 'free', None

    def find_free_register(self):
        for i in list_reg:
            if self.Reg[i][0] == 'free':
                return i
        return None

    def look_variable_in_register(self, varname):
        for i in list_reg: # todo renaming of global variables
            if self.Reg[i][0] == 'used' and self.Reg[i][1] == varname:
                return i
        return None

    def getreg(self, varname, reason):
        treg = self.look_variable_in_register(varname)
        if treg is not None:
            return treg
        else:
            treg = self.find_free_register()
            if treg is not None:
                if reason == ForRead: #load current value, Modify TR, TA
                    self.load_variable_to_register(varname, treg)
                if reason == 'write':
                    print 'getreg2'
                return treg
            else:
                #vybrat iz zanatych kakojto treg
                #uloz obsah R do pameti a modifikuj TR & TA
                #rapisat v treg todo
                self.Reg[treg] = 'used', varname
                return treg
        return None

    def get_address(self, varname): # todo renaming of global variables
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == varname:
                if self.AddressTable[i][1][0] == 'fp':  #variable is in a current frame
                    return str(-self.AddressTable[i][1][1]) + '($fp)'
                else:   #variable is in a global segment
                    return str(self.AddressTable[i][1][1]) + '($gp)'
        return None     #didnt find a variable in the TA

    def set_register_in_ta(self, varname, register):    # todo renaming of global variables
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == varname:
                first, second, third, forth = self.AddressTable[i]
                self.AddressTable[i] = (first, second, register, forth)

    def load_variable_to_register(self, varname, register):
        address = self.get_address(varname)
        self.gen('la $' + register + ',' + address)
        self.set_register_in_ta(varname, register)
        self.Reg[register] = 'used', varname

    def gen(self, command):
        self.program = self.program + (command + '\n')      #program
        self.pc += 1                                        #program counter

    def __init__(self):
        self.program = ''
        self.Reg['zero'] = 'reserved', None
        self.Reg['at'] = 'reserved', None
        self.Reg['v0'] = 'reserved', None
        self.Reg['v1'] = 'reserved', None
        self.Reg['a0'] = 'reserved', None
        self.Reg['a1'] = 'reserved', None
        self.Reg['a2'] = 'reserved', None
        self.Reg['a3'] = 'reserved', None
        self.Reg['k0'] = 'reserved', None
        self.Reg['k1'] = 'reserved', None
        self.Reg['gp'] = 'reserved', None
        self.Reg['sp'] = 'reserved', None
        self.Reg['fp'] = 'reserved', None
        self.Reg['ra'] = 'reserved', None
        self.Reg['t0'] = 'free', None
        self.Reg['t1'] = 'free', None
        self.Reg['t2'] = 'free', None
        self.Reg['t3'] = 'free', None
        self.Reg['t4'] = 'free', None
        self.Reg['t5'] = 'free', None
        self.Reg['t6'] = 'free', None
        self.Reg['t7'] = 'free', None
        self.Reg['t8'] = 'free', None
        self.Reg['t9'] = 'free', None
        self.Reg['s0'] = 'free', None
        self.Reg['s1'] = 'free', None
        self.Reg['s2'] = 'free', None
        self.Reg['s3'] = 'free', None
        self.Reg['s4'] = 'free', None
        self.Reg['s5'] = 'free', None
        self.Reg['s6'] = 'free', None
        self.Reg['s7'] = 'free', None
        self.pc = 0
        self.gen('.text')
        self.gen('.align 2')    #todo ??

    @staticmethod
    def getop(x):
        return {
            '+': 'add',
            '-': 'sub',
            '*': 'mul',
            '/': 'div',
            '%': 'rem',
            'Eq': 'seq',
            'Less': 'slt',
            'AND': 'and',
            'OR': 'or',
        }.get(x, None)

    def compile_bin_operation(self, operation, element):
        first, second, third, forth = element
        self.gen('#' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth))
        r = self.getreg(second, ForRead)
        s = self.getreg(third, ForRead)
        t = self.getreg(forth, ForWrite)
        self.gen(self.getop(first)+ ' $' + t + ',$' + r + ', $' + s)
        self.Reg[t] = 'used', forth             #modify TR, result is in T
        self.set_register_in_ta(forth, t)       #modify TA, result

    def compile(self, element):
        first, second, third, forth = element

        #hlavicka funkce
        #('FUNCTION', name , none , none)
        if first == 'FUNCTION':
            self.gen('#' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth) + '\n')
            if second == 'main':
                self.gen('.globl main')
            self.gen(second + ':')
            self.gen('subu $sp, $sp, 8')  # decrement sp to make space to save ra, fp
            self.gen('sw $fp, 8($sp)')    # save fp
            self.gen('sw $ra, 4($sp)')    # save ra
            self.gen('addiu $fp, $sp, 8') # set up new fp
            self.foffset.append(8)          #sdvig v tekuschem frame. Vsegda nachinajetsa s 8.
            #if (frameSz != 0)
            #Emit("subu $sp, $sp, %d\t# decrement sp for locals/temps", frameSz);

        # promena
        #('DIM', 'typ', 'jmeno', 'value')
        if first == 'DIM':
            self.gen('#' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth))
            #   if second == 'char': #todo it is byte! how does it work
            #        self.gen('addiu $t0,$zero,\'' + str(forth))
            #        self.gen('sw $t0,4($sp)\n')        # save variable in stack
            if second == 'int':
                r = self.getreg(third, ForWrite)                 #find register for stroing variable
                self.gen('li $' + r + ', ' + str(forth))     #load value in this register
                self.gen('subu $sp, $sp, 4')                  #decrement sp to make space for local variable
                self.gen('sw $' + r + ',4($sp)')                  #save variable in stack
                self.AddressTable[len(self.AddressTable)] = 'memory', (
                    'fp', self.foffset[len(self.foffset) - 1]), r, third   #save information in TA about variable
                self.foffset[len(self.foffset) - 1] = self.foffset[len(
                    self.foffset) - 1] + 4           #calclate offset of the next local variable in this segment
                self.Reg[r] = 'used', third
                #   if second == 'string':
                #        self.gen('.data\n')
                #       self.gen(third + ':\n .asciiz "' + forth + '"\n')  #store a string in a memory
                #       self.gen('.text\n')

        #(BINOPERATION, 'argument1', 'argument2', 'vysledek')
        if self.getop(first) is not None:
            self.compile_bin_operation(first, element)

    def GenerateProgram(self, IntCode):
        return None


my_tuple = ('FUNCTION', 'main', 3, 6)
my_tuple1 = ('DIM', 'char', 'znak', 'o')
my_tuple2 = ('DIM', 'string', 'retezec', "kk")
my_tuple3 = ('DIM', 'int', 'a', 3)
my_tuple4 = ('DIM', 'int', 'b', 5)
my_tuple5 = ('DIM', 'int', 'c', 0)
my_tuple6 = ('+', 'a', 'b', 'c')
my_tuple7 = ('-', 'a', 'c', 'b')
cg = CodeGenerator()
cg.compile(my_tuple)
#cg.compile(my_tuple1)
#cg.compile(my_tuple2)
cg.compile(my_tuple3)
cg.compile(my_tuple4)
cg.compile(my_tuple5)
print cg.program
print cg.Reg
print cg.AddressTable
cg.compile(my_tuple6)
print cg.program
print cg.Reg
print cg.AddressTable
cg.compile(my_tuple7)

print cg.program
print cg.Reg
print cg.AddressTable

cg.foffset.append(7)
cg.foffset.append(8)
l = len(cg.foffset)
cg.foffset[l - 1] = cg.foffset[l - 1] + 1
print cg.foffset[1]
#varname = 'tratata'
#fr = cg.findfreeregister()
#cg.Reg[fr] = 'reserved', varname
#print cg.Reg[fr]
#print cg.lookvariableinregister(varname)
#print cg.Reg[cg.findfreeregister()]