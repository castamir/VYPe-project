from vypeparser import parse, VYPeParser, semantic
with open("tests/examples/hello.world.src", "r") as myfile:
    data = myfile.read()

p = parse(data)
if p is not None:
    print p
    #for r in p:
    #    print r, p[r]
else:
    exit(VYPeParser.error)

print "defined functions:", semantic.function_table
print "global symbols:", semantic.symbol_table
