import sys
import argparse
import subprocess

parser = argparse.ArgumentParser(
            description='This script starts workers by mpirun.'
            ' All options have to be specified.')
parser.add_argument('--jobmaster', action='store',
            help='hostname of jobmaster')
parser.add_argument('--prefix', action='store',
            help='prefix of worker hostnames')
parser.add_argument('--suffix', action='store',
            help='suffix of worker hostnames')
parser.add_argument('--np', action='store', type=int,
            help='number of workers (processes)')

args = parser.parse_args()

# all options have to be specified
if None in list(vars(args).values()):
    parser.print_help()
    exit(1)

jobmaster = args.jobmaster
hostpre   = args.prefix
hostsuf   = args.suffix 
np        = args.np 

hostlist = []
for i in range(np):
    prefix = hostpre+str(i)
    hname = '.'.join( [prefix, hostsuf] )
    hostlist.append(hname)

print hostlist

cmd = ['mpirun', 
       '-np', np,
       '-H', ','.join(hostlist),
       'sudo',
       'bash',
       '-c',
       'python worker.py '+jobmaster+' 2>&1 |grep WORKERINFO']
       #'python worker.py '+jobmaster+' ']
#cmd = ['mpirun', 
       #'-np', np,
       #'-H', ','.join(hostlist),
       #'sudo',
       #'hostname']

cmd = [str(x) for x in cmd]
subprocess.call( cmd )



