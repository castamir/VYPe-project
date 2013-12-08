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
    Reg = {}                                #reserved , None  / free, None  /  used , name_of_variable
    AddressTable = {}                       #( memory, (segment,offset), registername, namevariable)
    goffset = 0                             #indicates an offset in global segment. Always of the first free row
    foffset = []                            #indicates offsets in segments. Always of the first free "row"
    is_in_global = (False, False, False)    #started ,in a function  ended

    def use_register(self, preg, varname):
        self.Reg[preg] = 'used', varname        #modify TR
        self.set_register_in_ta(varname, preg)  #modify TA

    def free_register(self, preg):                              #free register, moving current value of variable
        if self.Reg[preg][0] == 'used':                         #to the memory (it already has an address)
            address = self.get_address(self.Reg[preg][1])
            self.gen('sw $' + preg + ',' + address)             #move to memory
            self.Reg[preg] = 'free', None                       #modify TR
            self.set_register_in_ta(self.Reg[preg][1], None)    #modify TA

    def find_free_register(self):
        for i in list_reg:
            if self.Reg[i][0] == 'free':
                return i
        return None

    def look_variable_in_register(self, varname):
        for i in list_reg:                      # todo renaming of global variables
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
                #            self.use_register(t, forth)
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
        self.use_register(register, varname)

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
        #self.gen('.align 2')    #todo ??

    @staticmethod
    def getop(x):
        return {
            '+': 'add', #add $r,$s,$t           $r=$s+$t
            '-': 'sub', #sub $r,$s,$t           $r=$s-$t
            '*': 'mul', #mul $r,$s,$t           $r=$s*$t (first 32 bits)
            '/': 'div', #div $s,$t ; mflo $d    quotient                    (pseudo)
            '%': 'rem', #div $s,$t ; mfhi $d    reminder                    (pseudo)
            '&&': 'and', #and $r,$s,$t           $t= $r bitwise AND $s
            '||': 'or', #or  $r,$s,$t           $t= $r bitwise OR $s
            '<': 'slt', #slt $r,$s,$t           $t= ($r < $s)
            '==': 'seq', #seq $r,$s,$t           $t= ($r == $s)              (pseudo)
            '>': 'sgt', #sgt $r,$s,$t           $t= ($r > $s)               (pseudo)
            '>=': 'sge', #sge $r,$s,$t           $t= ($r >= $s)              (pseudo)
            '<=': 'sle', #sle $r,$s,$t           $t= ($r <= $s)              (pseudo)
            '!=': 'sne', #sne $r,$s,$t           $t= ($r != $s)              (pseudo)
        }.get(x, None)

    def compile_bin_operation(self, operation, element):
        first, second, third, forth = element
        r = self.getreg(second, ForRead)
        s = self.getreg(third, ForRead)
        t = self.getreg(forth, ForWrite)
        self.gen(self.getop(first) + ' $' + t + ',$' + r + ', $' + s)
        self.use_register(t, forth)

    def check_temp_var(self, element):
        first, variable1, variable2, forth = element
        if variable1 is not None:
            if variable1[0] == '$':
                self.Reg[self.look_variable_in_register(variable1)] = 'free', None
        if variable2 is not None:
            if variable2[0] == '$':
                self.Reg[self.look_variable_in_register(variable2)] = 'free', None

    def compile(self, element):
        first, second, third, forth = element
        self.gen('#' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth))

        #('FUNCTION', name , none , none)
        if first == 'FUNCTION':
            if self.is_in_global[0]:
                self.gen('.text')
                started, infunc, ended = self.is_in_global
                self.is_in_global = (False, True, ended)
            if second == 'main':
                self.gen('.globl main')
                started, infunc, ended = self.is_in_global
                self.is_in_global = (started, infunc, True)
            self.gen(second + ':')
            self.gen('subu $sp, $sp, 8')  # decrement sp to make space to save ra, fp
            self.gen('sw $fp, 8($sp)')    # save fp
            self.gen('sw $ra, 4($sp)')    # save ra
            self.gen('addiu $fp, $sp, 8') # set up new fp
            self.foffset.append(8)          #sdvig v tekuschem frame. Vsegda nachinajetsa s 8.
            #if (frameSz != 0)
            #Emit("subu $sp, $sp, %d\t# decrement sp for locals/temps", frameSz);

        #('DIM', 'typ', 'value', 'jmeno')
        if first == 'DIM':
            if not self.is_in_global[0] and not self.is_in_global[1] and not self.is_in_global[2]:
                self.gen('.data')
                started, infunc, ended = self.is_in_global
                self.is_in_global = (True, infunc, ended)
            if second == 'char': #todo it is byte! how does it work
                self.gen('addiu $t0,$zero,\'' + str(third))
                self.gen('sw $t0,4($sp)\n')        # save variable in stack
            if second == 'int':
                r = self.getreg(forth, ForWrite)                    #find register for storing variable
                self.gen('li $' + r + ', ' + str(third))            #load value in this register
                if (not self.is_in_global[1]) and (not self.is_in_global[2]):
                    self.gen('sw $'+r+','+str(self.goffset)+'($gp)')
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        'gp', self.goffset), r, forth   #save information in TA about variable
                    self.goffset += 4                   #calclate an offset of the next global variable in this segment
                else:
                    self.gen('subu $sp, $sp, 4')                        #decrement sp to make space for local variable
                    self.gen('sw $' + r + ',4($sp)')                    #save variable in stack
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        'fp', self.foffset[len(self.foffset) - 1]), r, forth   #save information in TA about variable
                    self.foffset[len(self.foffset) - 1] = self.foffset[len(
                        self.foffset) - 1] + 4           #calclate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth
            if second == 'string': #todo check to work
                self.gen('.data\n')
                self.gen(forth + ':\n .asciiz "' + third + '"\n')  #store a string in a memory
                self.gen('.text\n')

        #(BINOPERATION, 'argument1', 'argument2', 'vysledek')
        if self.getop(first) is not None:
            self.compile_bin_operation(first, element)
            self.check_temp_var(element)                    #free used temp variables

        #LOOP
        #(RETURN,value,none,none)
        if first == 'RETURN':
            if second is not None:
                self.gen('move $v0,' + self.Reg[self.look_variable_in_register(second)])
                #todo clear registers

            #is_in_global infunc = false
            self.gen('move $sp, $fp')
            self.gen('lw $ra, -4($fp)')
            self.gen('lw $fp, 0($fp)')
            self.gen('jr $ra')

        #('=', varname, None, vysledek)
        if first == '=':
            r = self.getreg(second, ForRead)
            t = self.getreg(forth, ForWrite)
            self.gen('move' + ' $' + t + ',$' + r)
            self.use_register(t, forth)
            self.check_temp_var(element)                    #free used temp variables

        #('TEMP', type, value, tempname)
        if first == 'TEMP':
            #if second == 'char': #todo it is byte! how does it work
             #   self.gen('addiu $t0,$zero,\'' + str(forth))
            #    self.gen('sw $t0,4($sp)\n')        # save variable in stack
            if second == 'int':
                r = self.getreg(forth, ForWrite)                    #find a register for storing a variable
                self.gen('li $' + r + ', ' + str(third))            #load value in this register
                #self.gen('subu $sp, $sp, 4')                        #decrement sp to make space for local variable
                #self.gen('sw $' + r + ',4($sp)')                    #save variable in stack
                #if (not self.is_in_global[1]) and (not self.is_in_global[2]):
                #    self.AddressTable[len(self.AddressTable)] = 'memory', (
                #        'gp', self.goffset), r, third   #save information in TA about variable
                #    self.goffset += 4                   #calclate an offset of the next global variable in this segment
                #else:
                #    self.AddressTable[len(self.AddressTable)] = 'memory', (
                #        'fp', self.foffset[len(self.foffset) - 1]), r, third   #save information in TA about variable
                #    self.foffset[len(self.foffset) - 1] = self.foffset[len(
                #        self.foffset) - 1] + 4           #calclate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth
                #self.AddressTable[len(self.AddressTable)] = 'memory', None, r, forth
            #if second == 'string': #todo check to work
            #    self.gen('.data\n')
            #    self.gen(third + ':\n .asciiz "' + forth + '"\n')  #store a string in a memory
            #    self.gen('.text\n')
    #Uminus
    #!

    def GenerateProgram(self, tac):
        for line in tac:
            self.compile(line)
        self.gen('')


#my_tuple = ('FUNCTION', 'main', 3, 6)
#my_tuple1 = ('DIM', 'char', 'znak', 'o')
#my_tuple2 = ('DIM', 'string', 'retezec', "kk")
#my_tuple3 = ('DIM', 'int', 3,'a')
#my_tuple4 = ('DIM', 'int', 5,'b')
#my_tuple5 = ('DIM', 'int', 0,'c')
#my_tuple6 = ('+', 'a', 'b', 'c')
#my_tuple7 = ('-', 'a', 'c', 'b')
#cg = CodeGenerator()
#cg.compile(my_tuple4)
#cg.compile(my_tuple)
##cg.compile(my_tuple1)
##cg.compile(my_tuple2)
#cg.compile(my_tuple3)
##cg.compile(my_tuple4)
#cg.compile(my_tuple5)
##print cg.program
##print cg.Reg
##print cg.AddressTable
#cg.free_register('t0')
#cg.compile(my_tuple6)
#print cg.program
#print cg.Reg
#print cg.AddressTable
#cg.compile(my_tuple7)

#print cg.program
#print cg.Reg
#print cg.AddressTable

#cg.foffset.append(7)
#cg.foffset.append(8)
#l = len(cg.foffset)
#cg.foffset[l - 1] = cg.foffset[l - 1] + 1

