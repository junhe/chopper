# Chopper is a diagnostic tool that explores file systems for unexpected
# behaviors. For more details, see paper Reducing File System Tail 
# Latencies With Chopper (http://research.cs.wisc.edu/adsl/Publications/).
#
# Please send bug reports and questions to jhe@cs.wisc.edu.
#
# Written by Jun He at University of Wisconsin-Madison
# Copyright (C) 2015  Jun He (jhe@cs.wisc.edu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

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



