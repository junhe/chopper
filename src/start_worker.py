import sys
import subprocess

#hostsuf = 'ubt8n.plfs'
#np = 8
#jobmaster = 'h0.ubt32n.plfs'

if len(sys.argv) != 4:
    print "usage:", sys.argv[0], 'jobmaster hostsuf np'
    print "example:", sys.argv[0], 'h0.noloop1n.plfs noloop1n.plfs 4'
    exit(1)

jobmaster = sys.argv[1]
hostsuf =   sys.argv[2]
np = int(sys.argv[3])


#jobmaster = 'h0.noloop1n.plfs'
#hostsuf = 'noloop1n.plfs'
#np = 1

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
       #'python worker.py '+jobmaster+' 2>&1 |grep WORKERINFO']
       'python worker.py '+jobmaster+' ']
#cmd = ['mpirun', 
       #'-np', np,
       #'-H', ','.join(hostlist),
       #'sudo',
       #'hostname']

cmd = [str(x) for x in cmd]
subprocess.call( cmd )



