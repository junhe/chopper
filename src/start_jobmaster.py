import subprocess
import sys

if len(sys.argv) != 3:
    print "Usage:", sys.argv[0], "resultpath usefinished|notusefinished"
    exit(1)

resultpath = sys.argv[1]
arg_usefinished = sys.argv[2]

cmd = ['python', './jobmaster.py', resultpath, arg_usefinished]
subprocess.call(cmd)
