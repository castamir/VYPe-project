__author__ = 'Malanka'

# first typ operace
# second je prvni operand
# third je druhy operand
# forth je vysledek
# .globl visible outside the module
#todo Bytes instead of int lw  - > lb , sw - > sb apod
list_reg = ['zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3', 'k0', 'k1', 'gp', 'sp',
            'fp', 'ra', 't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 's0', 's1', 's2', 's3', 's4', 's5',
            's6', 's7']
ForRead = 'read'
ForWrite = 'write'
debug = False


class CodeGenerator:                        # type , Varname , isDifferentFromMemory
    Reg = {}                                #reserved , None  / free, None  /  used , name_of_variable
    AddressTable = {}                       #( memory, (segment,offset), registername, namevariable)
    goffset = 0                             #indicates an offset in global segment. Always of the first free row
    foffset = 0                             #indicates offsets in segments. Always of the first free "row"
    is_data_segment = None                  #None - no segment started, true - data segment started, False -text segment
    main_started = False
    is_in_func = False                      #if we are in the body of some function
    parametr_count = 0

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

    def is_string_variable(self, variable):
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == variable:
                if self.AddressTable[i][1] is not None:
                    if self.AddressTable[i][1][1] is None and self.AddressTable[i][1][0] == 'gp':
                        return True
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
                if address is None:                             #allocate space in stack. Global variables MUST have already allocated space
                    self.gen('subu $sp, $sp, 4')                #decrement sp to make space for local variable
                    self.gen('sw $' + preg + ',4($sp)')            #save variable in stack todo type checking SW SB
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        'fp', self.foffset), None, self.Reg[preg][
                        1]   #save information in TA about variable
                    self.foffset += 4#calclate offset of the next local variable in this segment
                else:
                    if not self.is_string_variable(self.Reg[preg][1]):
                        self.gen('sw $' + preg + ',' + address)             #move to memory todo type checking SW SB
                    else:
                        pass #todo strcpy if it is needed
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

    def look_variable_in_addresstable(self, varname):
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == varname:
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
                #todo vybrat iz zanatych kakojto treg
                #uloz obsah R do pameti a modifikuj TR & TA
                #rapisat v treg todo
                #            self.use_register(t, forth)
        return treg

    def get_address(self, varname): # todo renaming of global variables
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == varname:
                if self.is_string_variable(varname): #it is a string in data segment, its name is its address
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
                return True
        return False #didnt find a variable in the TA

    def load_variable_to_register(self, varname, register):
        address = self.get_address(varname)
        self.gen('lw $' + register + ',' + address)     #todo string/byte
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

    def getreg_param(self, x): #todo check starting number 0/1
        return {
            0: 'a0',
            1: 'a1',
            2: 'a2',
            3: 'a3',
        }.get(x, 'STACK')

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
        self.use_register(t, forth, ForWrite)
        self.check_temp_var(element)                    #free used temp variables
        #todo STRINGS
        # U retezcu se porovnn
        #prov lexikograficky. Vsledkem porovnn je celocseln hodnota 1 (jedna) v prpade
        #pravdivosti relace, jinak 0

    def compile_un_op(self, element):
        first, second, third, forth = element
        r = self.getreg(second, ForRead)
        t = self.getreg(forth, ForWrite)
        self.gen(self.getunop(first) + ' $' + t + ',$' + r)
        self.use_register(t, forth, ForWrite)
        self.check_temp_var(element)                    #free used temp variables
        #todo STRINGS =

    def check_temp_var(self, element):
        first, variable1, variable2, forth = element
        if variable1 is not None:
            if variable1[0] == '$':
                self.Reg[self.look_variable_in_register(variable1)] = 'free', None, False
        if variable2 is not None:
            if variable2[0] == '$':
                self.Reg[self.look_variable_in_register(variable2)] = 'free', None, False

    def clear_tr_before_return(self):
        for i in list_reg:
            if self.Reg[i][0] == 'used':                    #pouzity registr
                j = self.look_variable_in_addresstable(self.Reg[i][1])
                if j is not None:
                    if self.AddressTable[j][1][0] == 'fp':      #pouzit pro promenou lokalni
                        self.set_register_in_ta(self.Reg[i][1], None)
                        self.Reg[i] = 'free', None, False
                    else:
                        if self.AddressTable[j][1][0] == 'gp' and self.AddressTable[j][1][
                            0] is not None:    #pouzit pro globalni
                            self.free_register(i)
                        else:                                     #pouzit pro string
                            #if self.is_string_variable(self.Reg[i][1]):
                            self.set_register_in_ta(self.Reg[i][1], None)
                            self.Reg[i] = 'free', None, False
                else:
                    self.Reg[i] = 'free', None, False

    def clear_ta_before_return(self):
        # gp-relative stay
        # fp relative delete
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][1] is not None:         #ma pamet
                if self.AddressTable[i][1][0] == 'fp':      #pamet je ve staku
                    del self.AddressTable[i]
                    # string constants?

    def compile(self, element):
        first, second, third, forth = element
        if debug:
            self.gen(';' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth))

        #('ARG', Type, Number, Variable)
        if first == 'ARG':
            r = self.getreg_param(third)
            if second == 'int':
                self.change_segment_type_to_text()
                if r != 'STACK':
                    self.Reg[r] = 'used', forth, False
                    self.AddressTable[len(self.AddressTable)] = 'memory', None, r, forth   #save information in TA about parametr
                else:
                    #todo read from stack
                    pass
            #if second == 'byte':
            #    self.change_segment_type_to_text()
            #    if r != 'STACK':
            #        #todo read from ai
            #        pass
            #    else:
            #        #todo read from stack
            #        pass
            #if second == 'string':
            #    self.change_segment_type_to_data()
            #    if r != 'STACK':
            #        #todo read from ai
            #        pass
            #    else:
            #        #todo read from stack
            #        pass

        #('PARAM', type , none , variable)
        if first == 'PARAM':
            param_reg = self.getreg_param(
                self.parametr_count)          #vybrat registr a0-a3/stack v zavislosti na cisle parametru
            if second == 'int':
                self.change_segment_type_to_text()
                if param_reg != 'STACK':                #davame parametr do registru a0-a3
                    #todo save registr ai
                    #put parametr into registr
                    r = self.getreg(forth, ForRead)     #nacteme potrebnou promenou do registru
                    self.gen('move $' + param_reg + ' , $' + r) #posuneme do potrebnho registru
                    #todo optimizivat :)
                else:                       #davame parametr do stacku 4+
                    #todo push parametr into stack
                    pass
            #todo parametrs byte and string
            #if second == 'byte':
            #    self.change_segment_type_to_text()
            #if second == 'string':
            #   self.change_segment_type_to_data()
            if self.parametr_count == 0:                                #jen zaciname predavat parametry
                #todo save caller-save registers
                #$t0-$t9 $a0-$a3 $v0-$v1
                #modify offset
                pass
            self.parametr_count += 1

        #('FUNCTION', name , none , none)
        if first == 'FUNCTION':
            self.is_in_func = True
            self.change_segment_type_to_text()
            self.gen(second + ':')
            self.gen('subu $sp, $sp, 8')  # decrement sp to make space to save ra, fp
            self.gen('sw $fp, 8($sp)')    # save fp offset =4+4
            self.gen('sw $ra, 4($sp)')    # save raoffset=4+4+4
            self.gen('addiu $fp, $sp, 8') # set up new fp
            #todo save $s0-$s7
            #r kolicestvo sochranennych registrov.
            roff = 0
            self.foffset = 8+4 + roff              # sdvig v tekuschem frame.

        #('DIM', 'typ', 'value', 'jmeno')
        if first == 'DIM':
            if second == 'char': #todo it is byte! how does it work
                self.change_segment_type_to_text()
                r = self.getreg(forth, ForWrite)                    #find register for storing variable
                self.gen('addiu $' + r + ' , $zero, \'' + str(third) + '\'')        #load value in this register
                if self.is_global():
                    self.gen('sb $' + r + ',' + str(self.goffset) + '($gp)')
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        'gp', self.goffset), r, forth   #save information in TA about variable
                    self.goffset += 4                   #calclate an offset of the next global variable in this segment
                else:
                    self.gen(
                        'subu $sp, $sp, 4')                        #decrement sp to make space for local variable
                    self.gen('sb $' + r + ',4($sp)')                    #save variable in stack
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        'fp', self.foffset), r, forth   #save information in TA about variable
                    self.foffset += 4                   #calclate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth, False
            if second == 'int':
                self.change_segment_type_to_text()
                r = self.getreg(forth, ForWrite)                    #find register for storing variable
                self.gen('li $' + r + ', ' + str(third))            #load value in this register
                if self.is_global():    #todo check global
                    self.gen('sw $' + r + ',' + str(self.goffset) + '($gp)')
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        'gp', self.goffset), r, forth   #save information in TA about variable
                    self.goffset += 4                   #calclate an offset of the next global variable in this segment
                else:
                    self.gen(
                        'subu $sp, $sp, 4')                        #decrement sp to make space for local variable
                    self.gen('sw $' + r + ',4($sp)')                    #save variable in stack
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        'fp', self.foffset), r, forth           #save information in TA about variable
                    self.foffset = self.foffset + 4           #calclate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth, False
            if second == 'string': #todo check to work
                self.change_segment_type_to_data()
                self.gen(forth + ':')
                self.gen('.asciiz "' + third + '"')  #store a string in a memory
                self.AddressTable[len(self.AddressTable)] = 'memory', ('gp', None), None, forth #todo add to TA

        #(BINOPERATION, 'argument1', 'argument2', 'vysledek')
        if self.getbinop(first) is not None:
            self.change_segment_type_to_text()
            self.compile_bin_operation(element)

        #('UNARYOPERATION', varname, None, vysledek)
        if self.getunop(first) is not None:
            self.change_segment_type_to_text()
            self.compile_un_op(element)

        #LOOP
        #('LABEL', None, None, label_loop_start)
        #('=', podminka, None, vyraz)
        #('JZ', podminka, None, label_loop_end)
        #body
        #('JUMP', None, None, label_loop_start)
        #('LABEL', None, None, label_loop_end)

        if first == 'JZ':
            self.change_segment_type_to_text()
            r = self.getreg(second, ForRead)
            self.ClearRegistersBeforeJump()
            self.gen('beq $'+r+',$zero, '+forth)

        #IF
        #('JNZ', podminka, none, Label1)
        #else
        #podminka==0
        #('JUMP',none,none, label2)
        #('LABEL',none,none, label1)
        #then
        #podminka!=0
        #('LABEL',none,none, label2)

        #('LABEL',None,None,labelname)
        if first == 'LABEL':
            self.change_segment_type_to_text()
            self.ClearRegistersBeforeJump()
            self.gen(forth+':')

        #('JUMP', None, None, labelname)
        if first == 'JUMP':
            self.change_segment_type_to_text()
            self.ClearRegistersBeforeJump()
            self.gen('j '+forth)

        #('JNZ', variable, None, labelname)
        if first == 'JNZ':
            self.change_segment_type_to_text()
            r = self.getreg(second, ForRead)
            self.ClearRegistersBeforeJump()
            self.gen('bne $'+r+',$zero, '+forth)

        #(RETURN,variable,none,none)
        if first == 'RETURN':
            self.change_segment_type_to_text()
            if second is not None:
                r = self.getreg(second, ForRead)                   #find register for storing variable
                self.gen('move $v0, $' + r)
            self.clear_tr_before_return()
            self.clear_ta_before_return()
            self.gen('move $sp, $fp')       #pop stackframe
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
                #        'fp', self.foffset), r, forth   #save information in TA about variable
                #    self.foffset = self.foffset + 4           #calclate offset of the next local variable in this segment
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
                #        'fp', self.foffset), r, third   #save information in TA about variable
                #    self.foffset = self.foffset + 4           #calclate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth, True
                #self.AddressTable[len(self.AddressTable)] = 'memory', None, r, forth
            if (second == 'string'): #todo check to work
                self.change_segment_type_to_data()
                self.gen(forth + ':')
                self.gen('.asciiz "' + third + '"')  #store a string in a memory
                self.AddressTable[len(self.AddressTable)] = 'memory', ('gp', None), None, forth #todo add to TA

        #(CALL, name, type , result)
        if first == 'CALL':
            self.parametr_count = 0     #po volani funkce zaciname szitat parametry zase od zacatku
            #todo jestli nado clear
            self.ClearRegistersBeforeJump()
            self.gen('jal ' + second)
            if forth is not None:
                r1 = self.getreg(forth, ForWrite)
                self.gen('move $' + r1 + ',$v0')
                self.use_register(r1, forth, ForWrite)

    #Save content of registers. Synchs the contents of registers with variables in memory
    def ClearRegistersBeforeJump(self):
        if debug:
            self.gen('start synchronize registers with memory')
        for i in list_reg:
            if self.Reg[i][2]:
                self.free_register(i)
        if debug:
            self.gen('end synchronize registers with memory')

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