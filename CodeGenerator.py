__author__ = 'Malanka'

# first typ operace
# second je prvni operand
# third je druhy operand
# forth je vysledek
# .globl visible outside the module



class CodeGenerator:
    Reg = {}

    def gen(self, command):
        self.program = self.program + command    #program
        self.pc += 1                    #program counter

    def __init__(self):
        self.program = ''
        for i in range(32):
            self.Reg["t%s" % i] = None
        self.pc = 0
        self.gen('.text\n')
        self.gen('.align 2\n')    #todo ??

    def compile(self, element):
        first, second, third, forth = element

        #hlavicka funkce
        #('FUNCTION', name , none , none)
        if first == 'FUNCTION':
            self.gen('#' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth) + '\n')
            if second == 'main':
                self.gen('.globl main\n')
            self.gen(second + ':\n')
            self.gen('subu $sp, $sp, 8\n')  # decrement sp to make space to save ra, fp
            self.gen('sw $fp, 8($sp)\n')    # save fp
            self.gen('sw $ra, 4($sp)\n')    # save ra
            self.gen('addiu $fp, $sp, 8\n') # set up new fp
            #if (frameSz != 0)
            #Emit("subu $sp, $sp, %d\t# decrement sp for locals/temps", frameSz);

        # promena
        #('DIM', 'typ', 'jmeno', 'value')
        if first == 'DIM':
            self.gen('#' + str(first) + ',' + str(second) + ',' + str(third) + ',' + str(forth) + '\n')
            if second == 'char': #todo it is byte! how does it work
                self.gen('addiu $t0,$zero,\'' + str(forth) + '\'\n')
                self.gen('sw $t0,4($sp)\n')        # save variable in stack
            if second == 'int':
                self.gen('li $t0,' + str(forth) + '\n')
                self.gen('subu $sp, $sp, 4\n')    #decrement sp to make space for local variable
                self.gen('sw $t0,4($sp)\n')        # save variable in stack
            if second == 'string':
                self.gen('.data\n')
                self.gen(third + ':\n .asciiz "' + forth + '"\n')  #store a string in a memory
                self.gen('.text\n')

    def GenerateProgram(self, IntCode):
        return None;



my_typle = ('FUNCTION', 'main', 3, 6)
my_typle1 = ('DIM', 'char', 'znak', 'o')
my_typle2 = ('DIM', 'string', 'retezec', "kk")
my_typle3 = ('DIM', 'int', 'a', -666)
cg = CodeGenerator()
cg.compile(my_typle)
cg.compile(my_typle1)
cg.compile(my_typle2)
cg.compile(my_typle3)


print cg.program