import sys
import libs.ply.lex as lex

sys.path.insert(0, "../")
import os

import subprocess

filename = 'soubor'

mypath = './examples'
from os import listdir
from os.path import isfile, join

files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
for filename in files:
    filename = "%s/%s" % (mypath, filename)
    x = subprocess.Popen("python ../vype.py --file=%s" % filename)
    x.wait()
    #print x.returncode
