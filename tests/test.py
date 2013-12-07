import sys
import libs.ply.lex as lex

sys.path.insert(0, "../")
import os
import subprocess
from os import listdir
from os.path import isfile, join

separator = "*******************************"
errors = 0
total = 0

tests = {
    0: ('./examples/correct', 'Expected zero errors'),
    1: ('./examples/error/1', 'Expected lexical errors')
}

print separator, "\ntesting started\n", separator
for expected in tests:
    mypath, description = tests[expected]
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for filename in files:
        total += 1
        message = "Testing:" + filename
        filename = "%s/%s" % (mypath, filename)
        x = subprocess.Popen("python ../vype.py --file=%s 2> output" % filename)
        x.wait()
        if x.returncode == expected:
            print message, "SUCCESS"
        else:
            errors += 1
            print message, "FAILED"
    print separator

print "\nTOTAL tests: %d, FAILED: %d" % (total, errors)

