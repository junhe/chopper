import subprocess
import sys

if len(sys.argv) != 2:
    print "Usage:", sys.argv[0], "resultpath"
    exit(1)

resultpath = sys.argv[1]

cmd = ['python', './jobmaster.py', resultpath]
subprocess.call(cmd)
