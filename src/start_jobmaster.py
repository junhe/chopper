import subprocess
import sys
import argparse

parser = argparse.ArgumentParser(description='Little script to start jobmaster')
parser.add_argument('--resultpath', action='store')
parser.add_argument('--jobtag', action='store')
parser.add_argument('--mode', choices=('usefinished','notusefinished'))

args = parser.parse_args()

if None in list(vars(args).values()):
    parser.print_help()
    exit(1)

cmd = ['python', './jobmaster.py',
       '--resultpath', args.resultpath, 
       '--jobtag', args.jobtag, 
       '--mode', args.mode]
subprocess.call(cmd)

