import sys
import subprocess

#hostsuf = 'ubt8n.plfs'
#np = 8
#jobmaster = 'h0.ubt32n.plfs'
jobmaster = 'h0.noloop1n.plfs'
hostsuf = 'noloop1n.plfs'
np = 1

hostlist = []
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



