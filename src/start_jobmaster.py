import subprocess
import sys
import argparse

#if len(sys.argv) != 4:
    #print "Usage:", sys.argv[0], "resultpath jobtag usefinished|notusefinished"
    #exit(1)


parser = argparse.ArgumentParser(description='Little script to start jobmaster')
parser.add_argument('--resultpath', action='store')
parser.add_argument('--jobtag', action='store')
parser.add_argument('--mode', choices=('usefinished','notusefinished'))

args = parser.parse_args()

if None in list(vars(args).values()):
    parser.print_help()
    exit(1)

cmd = ['python', './jobmaster.py',
        args.resultpath, 
        args.jobtag, 
        args.mode]
subprocess.call(cmd)

