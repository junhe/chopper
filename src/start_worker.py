import sys
import subprocess

#hostsuf = 'ubt8n.plfs'
#np = 8
jobmaster = 'h0.ubt32n.plfs'

hostlist = []

hostsuf = 'ubt32n.plfs'
np = 14
for i in range(np):
    prefix = 'h'+str(i)
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
#cmd = ['mpirun', 
       #'-np', np,
       #'-H', ','.join(hostlist),
       #'sudo',
       #'hostname']

cmd = [str(x) for x in cmd]
subprocess.call( cmd )



