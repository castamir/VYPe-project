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
debug = True

class CodeGenerator:                        # type , Varname , isDifferentFromMemory
    Reg = {}                                #reserved , None  / free, None  /  used , name_of_variable
    AddressTable = {}                       #( memory, (segment,offset), registername, namevariable)
    goffset = 0                             #indicates an offset in global segment. Always of the first free row
    foffset = []                            #indicates offsets in segments. Always of the first free "row"
    is_data_segment = None                  #None - no segment started, true - data segment started, False -text segment
    main_started = False
    is_in_func = False                      #if we are in the body of some function

    def change_segment_type_to_data(self):
        if (self.is_data_segment is None) or not self.is_data_segment:
            self.gen('.data')
            self.is_data_segment = True

    def change_segment_type_to_text(self):
        if (self.is_data_segment is None) or self.is_data_segment:
            self.gen('.text')
            self.is_data_segment = False

    def is_global(self):        #todo int a; function test(void){int o; o =9}; int b; int main(void){int b;}
        if not self.is_in_func:
            return True
        else:
            return False

    def use_register(self, preg, varname, purpose):
        if purpose == ForRead:                              #modify TR
            self.Reg[preg] = 'used', varname, False
        else:
            self.Reg[preg] = 'used', varname, True
        self.set_register_in_ta(varname, preg)              #modify TA

    def free_register(self, preg):                              #
        if self.Reg[preg][0] == 'used':                         #only used registers can be free
            if self.Reg[preg][2]:                               #if isDifferent then to the memory
                address = self.get_address(self.Reg[preg][1])
                if address is None:                             #allocate space in stack
                    self.gen('subu $sp, $sp, 4')                #decrement sp to make space for local variable
                    self.gen('sw $' + preg + ',4($sp)')            #save variable in stack
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        'fp', self.foffset[len(self.foffset) - 1]), None, self.Reg[preg][1]   #save information in TA about variable
                    self.foffset[len(self.foffset) - 1] = self.foffset[len(
                        self.foffset) - 1] + 4           #calclate offset of the next local variable in this segment
                else:
                    self.gen('sw $' + preg + ',' + address)             #move to memory
            self.set_register_in_ta(self.Reg[preg][1], None)    #modify TA
            self.Reg[preg] = 'free', None, False               #modify TR

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
        if treg is None:
            treg = self.find_free_register()
            if treg is not None:
                if reason == ForRead: #load current value, Modify TR, TA
                    self.load_variable_to_register(varname, treg)
            else:
                print 'AllRegisters are used'
                #vybrat iz zanatych kakojto treg
                #uloz obsah R do pameti a modifikuj TR & TA
                #rapisat v treg todo
                #            self.use_register(t, forth)
        return treg

    def get_address(self, varname): # todo renaming of global variables
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == varname:
                if self.AddressTable[i][1] is None and self.AddressTable[i][
                    2] is None: #it is a string in data segment, its name is its address
                    return self.AddressTable[i][3]
                else:
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
        self.use_register(register, varname, ForRead)

    def gen(self, command):
        self.program = self.program + (command + '\n')      #program
        self.pc += 1                                        #program counter

    def __init__(self):
        self.program = ''
        self.Reg['zero'] = 'reserved', None, False
        self.Reg['at'] = 'reserved', None, False
        self.Reg['v0'] = 'reserved', None, False
        self.Reg['v1'] = 'reserved', None, False
        self.Reg['a0'] = 'reserved', None, False
        self.Reg['a1'] = 'reserved', None, False
        self.Reg['a2'] = 'reserved', None, False
        self.Reg['a3'] = 'reserved', None, False
        self.Reg['k0'] = 'reserved', None, False
        self.Reg['k1'] = 'reserved', None, False
        self.Reg['gp'] = 'reserved', None, False
        self.Reg['sp'] = 'reserved', None, False
        self.Reg['fp'] = 'reserved', None, False
        self.Reg['ra'] = 'reserved', None, False
        self.Reg['t0'] = 'free', None, False
        self.Reg['t1'] = 'free', None, False
        self.Reg['t2'] = 'free', None, False
        self.Reg['t3'] = 'free', None, False
        self.Reg['t4'] = 'free', None, False
        self.Reg['t5'] = 'free', None, False
        self.Reg['t6'] = 'free', None, False
        self.Reg['t7'] = 'free', None, False
        self.Reg['t8'] = 'free', None, False
        self.Reg['t9'] = 'free', None, False
        self.Reg['s0'] = 'free', None, False
        self.Reg['s1'] = 'free', None, False
        self.Reg['s2'] = 'free', None, False
        self.Reg['s3'] = 'free', None, False
        self.Reg['s4'] = 'free', None, False
        self.Reg['s5'] = 'free', None, False
        self.Reg['s6'] = 'free', None, False
        self.Reg['s7'] = 'free', None, False
        self.pc = 0
        # self.gen('.text')
        # self.gen('main:')
        #self.gen('.align 2')    #todo ??

    def getbinop(self, x):
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

        #U retezcu se porovnn
        #prov lexikograficky. Vsledkem porovnn je celocseln hodnota 1 (jedna) v prpade
        #pravdivosti relace, jinak 0

    def getunop(self, y):
        return {
            'NOT': 'not', #not $r,$s           $r=!$s                      (pseudo)
            '=': 'move', #move $r,$s          $r=$s                       (pseudo)
            'UMINUS': 'neg', #neg $r,$s           $r=-$s                      (pseudo)
        }.get(y, None)

    def compile_bin_operation(self, element):
        first, second, third, forth = element
        r = self.getreg(second, ForRead)
        s = self.getreg(third, ForRead)
        t = self.getreg(forth, ForWrite)
        self.gen(self.getbinop(first) + ' $' + t + ',$' + r + ', $' + s)
        self.use_register(t, forth,ForWrite)
        self.check_temp_var(element)                    #free used temp variables

    def compile_un_op(self, element):
        first, second, third, forth = element
        r = self.getreg(second, ForRead)
        t = self.getreg(forth, ForWrite)
        self.gen(self.getunop(first) + ' $' + t + ',$' + r)
        self.use_register(t, forth,ForWrite)
        self.check_temp_var(element)                    #free used temp variables

    def check_temp_var(self, element):
        first, variable1, variable2, forth = element
        if variable1 is not None:
            if variable1[0] == '$':
                self.Reg[self.look_variable_in_register(variable1)] = 'free', None, False
        if variable2 is not None:
            if variable2[0] == '$':
                self.Reg[self.look_variable_in_register(variable2)] = 'free', None, False

    def clear_TA_before_return(self):
        pass

    def compile(self, element):
        first, second, third, forth = element
        if debug:
            self.gen(';' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth))

        #('FUNCTION', name , none , none)
        if first == 'FUNCTION':
            #save registers todo
            self.is_in_func = True
            self.change_segment_type_to_text()
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
            if second == 'char': #todo it is byte! how does it work
                self.change_segment_type_to_text()
                r = self.getreg(forth, ForWrite)                    #find register for storing variable
                self.gen('addiu $' + r + ' , $zero, \'' + str(third) + '\'')        #load value in this register
                if self.is_global():    #todo is global???
                    self.gen('sw $' + r + ',' + str(self.goffset) + '($gp)')
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
                self.Reg[r] = 'used', forth, False
            if second == 'int':
                self.change_segment_type_to_text()
                r = self.getreg(forth, ForWrite)                    #find register for storing variable
                self.gen('li $' + r + ', ' + str(third))            #load value in this register
                if self.is_global():    #todo is global???
                    self.gen('sw $' + r + ',' + str(self.goffset) + '($gp)')
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
                self.Reg[r] = 'used', forth, False
            if second == 'string': #todo check to work
                self.change_segment_type_to_data()
                self.gen(forth + ':')
                self.gen('.asciiz "' + third + '"')  #store a string in a memory
                self.AddressTable[len(self.AddressTable)] = 'memory', None, None, forth #todo add to TA

        #(BINOPERATION, 'argument1', 'argument2', 'vysledek')
        if self.getbinop(first) is not None:
            self.change_segment_type_to_text()
            self.compile_bin_operation(element)

        #('UNARYOPERATION', varname, None, vysledek)
        if self.getunop(first) is not None:
            self.change_segment_type_to_text()
            self.compile_un_op(element)

        #LOOP
        #IF

        #(RETURN,variable,none,none)
        if first == 'RETURN':
            self.change_segment_type_to_text()
            if second is not None:
                if self.look_variable_in_register(second) is None:
                    r = self.getreg(second, ForWrite)                   #find register for storing variable
                    self.gen('li $' + r + ', ' + str(
                        third))            #load value in this register #todo v zavisimosti ot type variable
                self.gen('move $v0, $' + r)
                #todo clear registers
                #todo clear addresstable
            self.gen('move $sp, $fp')
            self.gen('lw $ra, -4($fp)')
            self.gen('lw $fp, 0($fp)')
            self.gen('jr $ra')
            self.is_in_func = False

        #('TEMP', type, value, tempname)
        if first == 'TEMP':
            if second == 'char': #todo it is byte! how does it work
                self.change_segment_type_to_text()
                r = self.getreg(forth, ForWrite)                    #find register for storing variable
                self.gen('addiu $' + r + ',$zero,\'' + str(third) + '\'')        #load value in this register
                #if self.is_global():    #todo is global???
                #    self.gen('sw $' + r + ',' + str(self.goffset) + '($gp)')
                #    self.AddressTable[len(self.AddressTable)] = 'memory', (
                #        'gp', self.goffset), r, forth   #save information in TA about variable
                #    self.goffset += 4                   #calclate an offset of the next global variable in this segment
                #else:
                #    self.gen('subu $sp, $sp, 4')                        #decrement sp to make space for local variable
                #    self.gen('sw $' + r + ',4($sp)')                    #save variable in stack
                #    self.AddressTable[len(self.AddressTable)] = 'memory', (
                #        'fp', self.foffset[len(self.foffset) - 1]), r, forth   #save information in TA about variable
                #    self.foffset[len(self.foffset) - 1] = self.foffset[len(
                #        self.foffset) - 1] + 4           #calclate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth, True
                #self.AddressTable[len(self.AddressTable)] = 'memory', None, r, forth
            if second == 'int':
                self.change_segment_type_to_text()
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
                self.Reg[r] = 'used', forth, True
                #self.AddressTable[len(self.AddressTable)] = 'memory', None, r, forth
            if (second == 'string'): #todo check to work
                self.change_segment_type_to_data()
                self.gen(forth + ':')
                self.gen('.asciiz "' + third + '"')  #store a string in a memory
                self.AddressTable[len(self.AddressTable)] = 'memory', None, None, forth #todo add to TA

        #(CALL, name, type , result)
        if first == 'CALL':
            self.ClearRegistersBeforeJump()
            self.gen('jal '+second)
            if forth is not None:
                r1 = self.getreg(forth, ForWrite)
                self.gen('move $'+r1+',$t0')
                self.use_register(r1,forth,ForWrite)

    #Save content of registers. Synchs the contents of registers with variables in memory
    def ClearRegistersBeforeJump(self):
        for i in list_reg:
            if self.Reg[i][2]:
                self.free_register(i)



    def GenerateProgram(self, tac):
        for line in tac:
            self.compile(line)
        self.gen('')
        f = open('myfile.asm', 'w')
        f.write(self.program) # python will convert \n to os.linesep
        f.close() # you can omit in most cases as the destructor will call if


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

