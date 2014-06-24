import subprocess
import sys

if len(sys.argv) != 4:
    print "Usage:", sys.argv[0], "resultpath jobtag usefinished|notusefinished"
    exit(1)

resultpath = sys.argv[1]
jobtag = sys.argv[2]
arg_usefinished = sys.argv[3]

cmd = ['python', './jobmaster.py', resultpath, jobtag, arg_usefinished]
subprocess.call(cmd)
