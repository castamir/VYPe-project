__author__ = 'Malanka'

import string
# first typ operace
# second je prvni operand
# third je druhy operand
# forth je vysledek
# .globl visible outside the module
#todo Bytes instead of int lw  - > lb , sw - > sb apod
#list_reg = ['zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3', 'k0', 'k1', 'gp', 'sp',
#            'fp', 'ra', 't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 's0', 's1', 's2', 's3', 's4', 's5',
#            's6', 's7']
list_reg = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18',
            '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']
list_reg_param = ['a0', 'a1', 'a2', 'a3']
ForRead = 'read'
ForWrite = 'write'
debug = False
vestavene_funkce = ['print', 'read_char', 'read_string', 'read_int', 'get_at', 'set_at', 'strcat']


class CodeGenerator:                        # type , Varname , isDifferentFromMemory
    Reg = {}                                # reserved , None  / free, None  /  used , name_of_variable
    AddressTable = {}                       # ( memory, (segment,offset), registername, namevariable)
    goffset = 0                             # indicates an offset in global segment. Always of the first free row
    foffset = 0                             # indicates offsets in segments. Always  of the first free row
    is_data_segment = None                  # None - no segment started, true - data segment started, False -text segment
    main_started = False
    is_in_func = False                      # if we are in the body of some function
    parametrs = {}                          # tuples of paramets
    arg_offset = -4

    #change a segment to .data
    def change_segment_type_to_data(self):
        if (self.is_data_segment is None) or not self.is_data_segment:
            self.gen('.data')
            self.is_data_segment = True

    #change a segment to .text
    def change_segment_type_to_text(self):
        if (self.is_data_segment is None) or self.is_data_segment:
            self.gen('.text')
            self.is_data_segment = False

    #returns True if this statement is in "global"
    #returns False if this statement is in some function
    def is_in_global(self):        # todo int a; function test(void){int o; o =9}; int b; int main(void){int b;}
        if not self.is_in_func:
            return True
        else:
            return False

    #returns True if variable is global
    #returns False if variable is local, temp, parameter, string
    def is_global_variable(self, variable):
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == variable:
                if self.AddressTable[i][1] is not None:         # gp 28
                    if (self.AddressTable[i][1][1] is not None) and self.AddressTable[i][1][0] == '28':
                        return True
        return False

    #returns True if variable is string
    #returns False if variable is not string
    def is_string_variable(self, variable):
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == variable:
                if self.AddressTable[i][1] is not None:
                    if self.AddressTable[i][1][1] is None and self.AddressTable[i][1][0] == '28':
                        return True
        return False

    #modify TR,TA. Indicates that variable is associated with this register
    def use_register(self, preg, varname, purpose):
        if purpose == ForRead:                              # modify TR
            self.Reg[preg] = 'used', varname, False
        else:
            self.Reg[preg] = 'used', varname, True
        self.set_register_in_ta(varname, preg)              # modify TA

    #save a new variable stored in the register PREG into the stack
    def save_new_variable_into_stack(self, preg):
        self.save_word_into_stack(preg)                 # fp 30
        self.AddressTable[len(self.AddressTable)] = 'memory', (
            '30', self.foffset - 4), None, self.Reg[preg][1]    # save information in TA about variable

    #save word into stack                               #sp 29
    def save_word_into_stack(self, preg):
        self.gen('subu $29, $29, 4')                    # decrement sp to make space for word
        self.gen('sw $' + preg + ',4($29)')             # save word in stack
        self.foffset += 4                               # calculate offset of the next word in this segment

    # synchronise value of register with the memory, and then free the register
    def free_register(self, preg):
        if self.Reg[preg][0] == 'used':                         # only used registers can be free
            self.synch_reg_with_memory(preg)
            self.set_register_in_ta(self.Reg[preg][1], None)    # modify TA
            self.Reg[preg] = 'free', None, False                # modify TR

    # move value from the register PREG to the memory
    # if it is needed then it allocates a space in stack
    # if it is needed then it relocate strings
    def synch_reg_with_memory(self, preg):
        if self.Reg[preg][2]:                               # if isDifferent then to the memory
            address = self.get_address(self.Reg[preg][1])
            if address is None:                             # allocate space in stack.
                self.save_new_variable_into_stack(preg)
            else:                                           # Global variables MUST have already allocated space
                if not self.is_string_variable(self.Reg[preg][1]):
                    self.gen('sw $' + preg + ',' + address)             # move to memory SW for all variables in STACK
                else:
                    pass  # todo strcpy if it is needed
            p1, p2, p3 = self.Reg[preg]
            self.Reg[preg] = p1, p2, False

    # synchronise value of variable with the memory
    def synch_variable_value_with_memory(self, variable):
        preg = self.look_variable_in_register(variable)
        if preg is not None:            # if variable is in some register
            self.synch_reg_with_memory(preg)

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
                if reason == ForRead:  # load current value, Modify TR, TA
                    self.load_variable_to_register_from_address(varname, treg)
                    #todo strings
            else:
                print 'AllRegisters are used'
                # todo vybrat iz zanatych kakojto treg
                # uloz obsah R do pameti a modifikuj TR & TA
                # rapisat v treg todo
                #            self.use_register(t, forth)
        return treg

    def get_address(self, varname):  # todo renaming of global variables
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == varname:
                if self.is_string_variable(varname):  # it is a string in data segment, its name is its address
                    return self.AddressTable[i][3]
                else:
                    if self.AddressTable[i][1][0] == '30':  # variable is in a current frame
                        return str(-self.AddressTable[i][1][1]) + '($30)'
                    else:   # variable is in a global segment
                        return str(self.AddressTable[i][1][1]) + '($28)'
        return None     # didnt find a variable in the TA

    def set_register_in_ta(self, varname, register):    # todo renaming of global variables
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][3] == varname:
                first, second, third, forth = self.AddressTable[i]
                self.AddressTable[i] = (first, second, register, forth)
                return True
        return False  # didnt find a variable in the TA

    def load_variable_to_register_from_address(self, varname, register):
        address = self.get_address(varname)
        self.gen('lw $' + register + ',' + address)     # todo string/byte
        self.use_register(register, varname, ForRead)

    def gen(self, command):
        self.program = self.program + (command + '\n')      # program
        self.pc += 1                                        # program counter

    def __init__(self):
        self.program = ''
        self.Reg['0'] = 'reserved', None, False
        self.Reg['1'] = 'reserved', None, False
        self.Reg['2'] = 'reserved', None, False
        self.Reg['3'] = 'reserved', None, False
        self.Reg['4'] = 'reserved', None, False
        self.Reg['5'] = 'reserved', None, False
        self.Reg['6'] = 'reserved', None, False
        self.Reg['7'] = 'reserved', None, False
        self.Reg['26'] = 'reserved', None, False
        self.Reg['27'] = 'reserved', None, False
        self.Reg['28'] = 'reserved', None, False
        self.Reg['29'] = 'reserved', None, False
        self.Reg['30'] = 'reserved', None, False
        self.Reg['31'] = 'reserved', None, False
        self.Reg['8'] = 'free', None, False
        self.Reg['9'] = 'free', None, False
        self.Reg['10'] = 'free', None, False
        self.Reg['11'] = 'free', None, False
        self.Reg['12'] = 'free', None, False
        self.Reg['13'] = 'free', None, False
        self.Reg['14'] = 'free', None, False
        self.Reg['15'] = 'free', None, False
        self.Reg['24'] = 'free', None, False
        self.Reg['25'] = 'free', None, False
        self.Reg['16'] = 'free', None, False
        self.Reg['17'] = 'free', None, False
        self.Reg['18'] = 'free', None, False
        self.Reg['19'] = 'free', None, False
        self.Reg['20'] = 'free', None, False
        self.Reg['21'] = 'free', None, False
        self.Reg['22'] = 'free', None, False
        self.Reg['23'] = 'free', None, False
        self.pc = 0
        self.change_segment_type_to_data()
        self.gen('tm_empty_string' + ':')
        self.gen('.asciz ""')  # store an empty string in a memory
        self.gen('.text')
        self.gen('.org 0')
        self.gen('nop')
        self.gen('nop')
        self.gen('addiu $sp, $0, 0x4000')
        self.gen('jal main')
        self.gen('nop')
        self.gen('break')

        # self.gen('.text')
        # self.gen('main:')
        # self.gen('.align 2')    # todo ??

    def getbinop(self, x):
        return {
            '+': 'add', # add $r,$s,$t           $r=$s+$t
            '-': 'sub', # sub $r,$s,$t           $r=$s-$t
            '*': 'mul', # mul $r,$s,$t           $r=$s*$t (first 32 bits)
            '/': 'div', # div $s,$t ; mflo $d    quotient                    (pseudo)
            '%': 'rem', # div $s,$t ; mfhi $d    reminder                    (pseudo)
            '&&': 'and', # and $r,$s,$t           $t= $r bitwise AND $s
            '||': 'or', # or  $r,$s,$t           $t= $r bitwise OR $s
            '<': 'slt', # slt $r,$s,$t           $t= ($r < $s)
            '==': 'seq', # seq $r,$s,$t           $t= ($r == $s)              (pseudo)
            '>': 'sgt', # sgt $r,$s,$t           $t= ($r > $s)               (pseudo)
            '>=': 'sge', # sge $r,$s,$t           $t= ($r >= $s)              (pseudo)
            '<=': 'sle', # sle $r,$s,$t           $t= ($r <= $s)              (pseudo)
            '!=': 'sne', # sne $r,$s,$t           $t= ($r != $s)              (pseudo)
        }.get(x, None)

    def getreg_param(self, x):
        return {
            1: '4',
            2: '5',
            3: '6',
            4: '7',
        }.get(x, 'STACK')

    def getunop(self, y):
        return {
            'NOT': 'not', # not $r,$s           $r=!$s                      (pseudo)
            '=': 'move', # move $r,$s          $r=$s                       (pseudo)
            'UMINUS': 'neg', # neg $r,$s           $r=-$s                      (pseudo)
        }.get(y, None)

    def compile_bin_operation(self, element):
        first, second, third, forth = element
        r = self.getreg(second, ForRead)
        s = self.getreg(third, ForRead)
        t = self.getreg(forth, ForWrite)
        self.gen(self.getbinop(first) + ' $' + t + ',$' + r + ', $' + s)
        self.use_register(t, forth, ForWrite)
        self.check_temp_var(element)                    # free used temp variables
        #todo STRINGS
        # U retezcu se porovnn
        # prov lexikograficky. Vsledkem porovnn je celocseln hodnota 1 (jedna) v prpade
        # pravdivosti relace, jinak 0

    def compile_un_op(self, element):
        first, second, third, forth = element
        if not self.is_string_variable(forth):
            r = self.getreg(second, ForRead)
            t = self.getreg(forth, ForWrite)
            self.gen(self.getunop(first) + ' $' + t + ',$' + r)
            self.use_register(t, forth, ForWrite)
            self.check_temp_var(element)                    # free used temp variables
        else:
            pass
        # todo STRINGS =

    def is_temp_variable(self, variable):
        if string.find(variable, 'tm_') == 0:
            return True
        else:
            return False

    def check_temp_var(self, element):
        first, variable1, variable2, forth = element
        if variable1 is not None:
            if self.is_temp_variable(variable1):
                self.Reg[self.look_variable_in_register(variable1)] = 'free', None, False
        if variable2 is not None:
            if self.is_temp_variable(variable2):
                self.Reg[self.look_variable_in_register(variable2)] = 'free', None, False

    #synchs TR before return, saves only global variables and strings
    def synch_tr_before_return(self):
        for i in list_reg:
            if self.Reg[i][0] == 'used':                            # only used registers can be cleared
                if self.is_global_variable(self.Reg[i][1]):         # if variable is global, then save it
                    if self.Reg[i][2]:                              # if isDifferent then to the memory
                        address = self.get_address(self.Reg[i][1])
                        self.gen('sw $' + i + ',' + address)            # move to memory todo type checking SW SB
                if self.is_string_variable(self.Reg[i][1]):
                    #todo strings
                    pass

    #            self.set_register_in_ta(self.Reg[i][1], None)       # modify TA
    #            self.Reg[i] = 'free', None, False                   # modify TR

    #clears TA. Deleting only fp-relative variables. gp-relative variables stay
    def clear_ta_before_end_of_func(self):
        # gp-relative stay
        # fp relative delete
        for i in range(len(self.AddressTable)):
            if self.AddressTable[i][1] is not None:         # ma pamet
                if self.AddressTable[i][1][0] == '30':      # pamet je ve staku
                    del self.AddressTable[i]

    #clears TR. Erase all registers, except holding global
    def clear_tr_before_end_of_func(self):
        for i in list_reg:
            if self.Reg[i] == 'used':
                variable = self.Reg[i][2]
                j = self.look_variable_in_addresstable(variable)
                if j is None:       # assume, that clear_ta_before_end_of_func was called before
                    self.Reg[i] = 'free', None, False

    #clears TA and TR before end of function
    def do_clean_before_end_of_func(self):
        self.clear_ta_before_end_of_func()
        self.clear_tr_before_end_of_func()

    # get list of the current parameters
    # it starts from last and end at first
    def get_curr_param_list(self):
        curr_param_list = {}
        for i in reversed(xrange(len(self.parametrs))):
            curr_param_list[len(curr_param_list)] = self.parametrs[i]
            # when we finally find the first parameter, we delete it and stop
            if self.parametrs[i][2] == 1:
                del self.parametrs[i]
                break
                # after loading parameters in registers/saving parameters into the stack need to delete it from the set
            del self.parametrs[i]
        return curr_param_list

    #load all parameters into registers/stack exactly before the call
    def load_parameters_before_call(self):
        curr_param_list = self.get_curr_param_list()    # get list of the current parameters
        # go through the current list of parameters from first parameter till last parameter
        for i in reversed(xrange(len(curr_param_list))):
            # load one parameter
            # ('PARAM', type , cislo parametru , variable)
            param_reg = self.getreg_param(curr_param_list[i][2])     # choose register a0-a3/ stack
            if curr_param_list[i][1] == 'int' or curr_param_list[i][1] == 'char':
                self.change_segment_type_to_text()
                if param_reg != 'STACK':              # davame parametr do registru a0-a3
                    self.free_register(param_reg)     # if this register already has a value, then move it to the memory
                    # put parametr into registr
                    self.load_variable_to_register_from_address(
                        curr_param_list[i][3], param_reg)             # nacteme potrebnou promenou do registru
                    self.use_register(param_reg, curr_param_list[i][3], ForWrite)
                else:                       # davame parametr do stacku 4+
                    r = self.getreg(curr_param_list[i][3], ForRead)
                    self.save_word_into_stack(r)
                    # todo string
                    #if second == 'string':
                    #   self.change_segment_type_to_data()

    def read_next_arg_stack(self, variable):
        self.AddressTable[len(self.AddressTable)] = 'memory', (
            '30', self.arg_offset), None, variable   # save information in TA about the variable
        self.arg_offset -= 4

    def compile(self, element):
        first, second, third, forth = element
        if debug:
            self.gen(';' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth))

        # ('ARG', Type, Number, Variable)
        if first == 'ARG':
            r = self.getreg_param(third)
            if second == 'int' or second == 'char':
                self.change_segment_type_to_text()
                if r != 'STACK':
                    self.Reg[r] = 'used', forth, False
                else:
                    self.read_next_arg_stack(forth)
                    # if second == 'string':
                    #    self.change_segment_type_to_data()
                    #    if r != 'STACK':
                    #        #todo read from ai
                    #        pass
                    #    else:
                    #        #todo read from stack
                    #        pass

        # ('PARAM', type , cislo parametru , variable)
        if first == 'PARAM':
            self.parametrs[len(self.parametrs)] = element
            #save to the memory
            self.synch_variable_value_with_memory(forth)

        #('FUNCTION', name , none , none)
        if first == 'FUNCTION':
            self.is_in_func = True
            self.arg_offset = -4
            self.change_segment_type_to_text()
            self.gen(second + ':')
            self.gen('subu $29, $29, 8')  # decrement sp to make space to save ra, fp
            self.gen('sw $30, 8($29)')    # save fp offset =0
            self.gen('sw $31, 4($29)')    # save ra offset =4
            self.gen('addiu $30, $29, 8') # set up new fp
            #todo save $s0-$s7
            #r kolicestvo sochranennych registrov.
            # offset 0 -used, offset 4 used, offset 8 free
            roff = 0
            self.foffset = 8 + roff              # sdvig v tekuschem frame.

        # ('ENDFUNC', None , None , None)
        if first == 'ENDFUNC':
            self.is_in_func = False
            self.do_clean_before_end_of_func()

        #('DIM', 'typ', 'value', 'jmeno')
        if first == 'DIM':
            if second == 'char':  # todo it is byte! how does it work
                self.change_segment_type_to_text()
                r = self.getreg(forth, ForWrite)                    # find register for storing variable
                self.gen('li $' + r + ', ' + str(
                    third))  # self.gen('addiu $' + r + ',$zero,\'' + str(third) + '\'')        # load value in this register
                if self.is_in_global():     # todo check global
                    self.gen('sw $' + r + ',' + str(self.goffset) + '($28)')
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        '28', self.goffset), r, forth   # save information in TA about the variable
                    self.goffset += 4                  # calculate an offset of the next global variable in this segment
                else:
                    self.gen('subu $29, $29, 4')                        # decrement sp to make space for local variable
                    self.gen('sw $' + r + ',4($29)')                    # save variable in stack
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        '30', self.foffset), r, forth   # save information in TA about variable
                    self.foffset += 4                   # calculate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth, False      # use register
            if second == 'int':
                self.change_segment_type_to_text()
                r = self.getreg(forth, ForWrite)                    # find register for storing variable
                self.gen('li $' + r + ', ' + str(third))            # load value in this register
                if self.is_in_global():    # todo check global
                    self.gen('sw $' + r + ',' + str(self.goffset) + '($28)')
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        '28', self.goffset), r, forth   # save information in TA about variable
                    self.goffset += 4                   # calclate an offset of the next global variable in this segment
                else:
                    self.gen(
                        'subu $29, $29, 4')                        # decrement sp to make space for local variable
                    self.gen('sw $' + r + ',4($29)')                    # save variable in stack
                    self.AddressTable[len(self.AddressTable)] = 'memory', (
                        '30', self.foffset), r, forth           # save information in TA about variable
                    self.foffset = self.foffset + 4           # calclate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth, False
            if second == 'string': #todo check to work
                r = self.getreg(forth, ForWrite)
                self.gen('la $'+r+', tm_empty_string')
                self.gen('subu $29, $29, 4')                        # decrement sp to make space for local variable
                self.gen('sw $' + r + ',4($29)')                    # save address of the string_variable in stack
                self.AddressTable[len(self.AddressTable)] = 'string', (
                        '30', self.foffset), r, forth               # save information in TA about variable
                self.foffset += 4                   # calculate offset of the next local variable in this segment
                self.Reg[r] = 'used', forth, False

        # (BINOPERATION, 'argument1', 'argument2', 'vysledek')
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
            self.gen('beq $' + r + ',$zero, ' + forth)

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
            self.gen(forth + ':')

        #('JUMP', None, None, labelname)
        if first == 'JUMP':
            self.change_segment_type_to_text()
            self.ClearRegistersBeforeJump()
            self.gen('j ' + forth)

        #('JNZ', variable, None, labelname)
        if first == 'JNZ':
            self.change_segment_type_to_text()
            r = self.getreg(second, ForRead)
            self.ClearRegistersBeforeJump()
            self.gen('bne $' + r + ',$0, ' + forth)

        #(RETURN,variable,none,none)
        if first == 'RETURN':
            self.change_segment_type_to_text()
            if second is not None:
                r = self.getreg(second, ForRead)                   # find register for storing variable
                self.free_register('2')                           # save variable stored in 'v0'
                self.gen('move $2, $' + r)
            self.synch_tr_before_return()                          # saves globals/strings
            self.gen('move $29, $30')       # pop stackframe
            self.gen('lw $31, -4($30)')
            self.gen('lw $30, 0($30)')
            self.gen('jr $31')

        #('TEMP', type, value, tempname)
        if first == 'TEMP':
            if second == 'char':  # todo it is byte! how does it work
                self.change_segment_type_to_text()
                r = self.getreg(forth, ForWrite)                    # find register for storing variable
                self.gen('li $' + r + ', ' + str(third))        # load value in this register
                # self.gen('li $' + r + ', \'' + str(third) + '\'')        # load value in this register
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
                r = self.getreg(forth, ForWrite)                    # find a register for storing a variable
                self.gen('li $' + r + ', ' + str(third))            # load value in this register
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
                self.gen('.asciz "' + third + '"')  # store a string in a memory
                self.AddressTable[len(self.AddressTable)] = 'memory', ('28', None), None, forth # todo add to TA

        #(CALL, name, type , result)
        if first == 'CALL':
            if second in vestavene_funkce:
                self.do_vestavena_funkce(element)
            else:
                #todo jestli nado clear
                self.ClearRegistersBeforeJump() # todo ??? delete
                self.load_parameters_before_call()
                self.gen('jal ' + second)
                if forth is not None:
                    # todo int char string
                    r1 = self.getreg(forth, ForWrite)
                    self.gen('move $' + r1 + ',$2')
                    self.use_register(r1, forth, ForWrite)

    def do_vestavena_funkce(self, element):
        first, second, third, forth = element
        if second == 'print':
            curr_param_list = self.get_curr_param_list()
            for i in reversed(xrange(len(curr_param_list))):
                if curr_param_list[i][1] == 'int':
                    r = self.getreg(curr_param_list[i][3], ForRead)
                    self.gen('PRINT_INT $' + r)
                if curr_param_list[i][1] == 'char':
                    r = self.getreg(curr_param_list[i][3], ForRead)
                    self.gen('PRINT_CHAR $' + r)
                if curr_param_list[i][1] == 'string':  #todo strings
                    r = self.getreg(curr_param_list[i][3], ForRead)
                    self.gen('PRINT_STRING $' + r)
        if second == 'read_int':
            r = self.getreg(forth, ForWrite)
            self.gen('READ_INT $'+r)
            self.use_register(r, forth, ForWrite)
        if second == 'read_char':
            r = self.getreg(forth, ForWrite)
            self.gen('READ_CHAR $'+r)
            self.use_register(r, forth, ForWrite)
        if second == 'read_string':
            r = self.getreg(forth, ForWrite)
            #todo strings
            self.gen('READ_string $'+r)
            self.use_register(r, forth, ForWrite)
        if second == 'get_at':  #todo getat
            #r = self.getreg(forth, ForWrite)
            #self.gen('READ_CHAR $'+r)
            #self.use_register(r, forth, ForWrite)
            pass
        if second == 'set_at':  #todo setat
            #r = self.getreg(forth, ForWrite)
            #self.gen('READ_CHAR $'+r)
            #self.use_register(r, forth, ForWrite)
            pass
        if second == 'strcat':
            pass
            #todo strcat
    
    # Save content of registers. Synchs the content of registers with variables in memory
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