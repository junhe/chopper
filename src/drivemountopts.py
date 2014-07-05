import subprocess
import os
import itertools
import re
import time

#opts = "barrier=1,max_batch_time=0,noauto_da_alloc,data=writeback,noauto_da_alloc,commit=7200,norecovery,data=ordered,data=journal"
#opts = "data=journal"
opts = "data=writeback,data=ordered"
opts = opts.split(',')

resultdir = 'trymount'

# 1
for optcomb in itertools.combinations(opts, 1):
    for runid in range(3):
        oparg = ','.join(optcomb)
        resultfile = re.sub(r'\W', '_', oparg)
        resultfile = resultfile + "." + time.strftime("%m-%d-%H-%M-%S", time.localtime())
        resultpath = os.path.join(resultdir, resultfile)

        cmd = ['python',
               'exp_executor.py',
               oparg,
               resultpath]
        print cmd
        time.sleep(3)

        subprocess.call(cmd)

