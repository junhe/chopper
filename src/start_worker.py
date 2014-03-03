import sys
import subprocess

hostsuf = 'ubt3n.plfs'
np = 3

hostlist = []
for i in range(np):
    prefix = 'h'+str(i)
    hname = '.'.join( [prefix, hostsuf] )
    hostlist.append(hname)

print hostlist
#mpirun -np 2 -H h1.ubt3n.plfs,h2.ubt3n.plfs sudo bash -c 'python worker.py h0.ubt3n.plfs 2>&1 |grep WORKERINFO'
cmd = ['mpirun', 
       '-np', np,
       '-H', ','.join(hostlist),
       'sudo',
       'bash',
       '-c',
       'python worker.py '+'h0.'+hostsuf+' 2>&1 |grep WORKERINFO']
cmd = [str(x) for x in cmd]
subprocess.call( cmd )



