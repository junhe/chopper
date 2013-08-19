# walkman is the driver/integrator of the MetaWalker.
# the workflow is like:
#   0. format the whole system
#   1. genearate workloads by Producer
#   2. For each workload:
#       2. play workload by player
#       3. monitor the FS status
# 
#
# Possible ways to make more fragments:
#   1. delete previous files
#   2. append previous files
import subprocess
import MWpyFS
import pyWorkload
import time
import shutil
import os
import socket


class Config:
    def __init__(self):
        self.dic = {}

    def display(self, style="columns", colwidth=15, save2file=""):
        contents = ""
        if style == "columns":
            header = self.dic.keys()
            header = [ str(x).ljust(colwidth) for x in header]
            header = " ".join(header) + '\n'

            vals = self.dic.values()
            vals = [ str(x).ljust(colwidth) for x in vals]
            vals = " ".join(vals) + '\n'

            contents = header + vals
        else:
            tablestr = ""
            for keyname in self.dic:
                k = str(keyname).ljust(colwidth)
                v = str(self.dic[keyname]).ljust(colwidth)
                entry = " ".join([k, v]) 
                tablestr += entry + '\n'

            contents = tablestr

        if save2file != "":
            with open(save2file, 'w') as f:
                f.write(contents)
                f.flush()
        return contents

class Walkman:
    def __init__(self):
        self.conf = Config()

        self.conf.dic['devname'] = '/dev/sdb'

        self.conf.dic['partition'] = '/dev/sdb1'
        self.conf.dic['diskconf'] = '../conf/sfdisk.conf'
        self.conf.dic['mountpoint'] = '/mnt/scratch/'
        self.conf.dic['jobid'] = socket.gethostname() + "-" \
                + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())

        self.conf.dic['workloadpath'] = "./pyWorkload/workload.buf"
        self.conf.dic['playerpath'] = "../build/src/player"
        self.conf.dic['mpirunpath'] = "/home/junhe/installs/openmpi-1.4.3/bin/mpirun"
        self.conf.dic['resultdir'] = "./results/"

        self.conf.dic['np'] = 3 # put it here guide mpirun and wl producer
        self.conf.dic['ndir_per_pid'] = 2 
        self.conf.dic['startOff'] = 0
        self.conf.dic['nwrites_per_file'] = 4
        self.conf.dic['nfile_per_dir'] = 3
        self.conf.dic['wsize'] = 4097
        self.conf.dic['wstride'] = 4098

        self.conf.dic['HEADERMARKER_walkman_config'] = \
                'DATAMARKER_walkman_config'

       
        # monitor
        self.monitor = MWpyFS.Monitor.FSMonitor(self.conf.dic['partition'], 
                                                 self.conf.dic['mountpoint'],
                                                 ld = self.conf.dic['resultdir']) # logdir
        # producer
        self.wl_producer = pyWorkload.producer.Producer()


    def displayandsaveConfig(self):
        colwidth = 30
        conflog = self.conf.dic['resultdir'] + \
                    "walkmanJOB-"+self.conf.dic['jobid']+".conf.rows"
        print self.conf.display(style="rows",
                                colwidth=colwidth,
                                save2file=conflog)

        conflog = self.conf.dic['resultdir'] + \
                    "walkmanJOB-"+self.conf.dic['jobid']+".conf.columns"
        self.conf.display(style="columns",
                                colwidth=colwidth,
                                save2file=conflog)

    def rebuildFS(self):
        MWpyFS.FormatFS.buildNewExt4(self.conf.dic["devname"],
                self.conf.dic['mountpoint'], self.conf.dic['diskconf'], "junhe")

    def remakeExt4(self):
        MWpyFS.FormatFS.remakeExt4(partition=self.conf.dic['partition'],
                                   mountpoint=self.conf.dic['mountpoint'],
                                   username="junhe")


    #def produceWorkload_rmdir(self, rootdir):
        #self.wl_producer.produce_rmdir(np=self.conf.dic['np'],
                                       #ndir_per_pid=self.ndir_per_pid,
                                       #rootdir=self.mountpoint+rootdir,
                                       #tofile=self.workloadpath)

    def produceWorkload(self, rootdir):
        self.wl_producer.produce(np=self.conf.dic['np'], 
                                startOff=self.conf.dic['startOff'],
                                nwrites_per_file = self.conf.dic['nwrites_per_file'], 
                                nfile_per_dir=self.conf.dic['nfile_per_dir'], 
                                ndir_per_pid=self.conf.dic['ndir_per_pid'],
                                wsize=self.conf.dic['wsize'], 
                                wstride=self.conf.dic['wstride'], 
                                rootdir=self.conf.dic['mountpoint']+rootdir,
                                tofile=self.conf.dic['workloadpath'])
    def play(self):
        cmd = [self.conf.dic['mpirunpath'], "-np", self.conf.dic['np'], 
                self.conf.dic['playerpath'], self.conf.dic['workloadpath']]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def getrootdirByIterIndex(self, i):
        rootdir = "round"+str(i)+"/"   #TODO: fix the "/" must thing
        return rootdir

    def getLogFilenameBySeasonYear(self, season, year):
        return "walkmanJOB-"+self.conf.dic['jobid']+\
                ".result.log.year-"+str(year).zfill(5)+\
                ".season-"+str(season).zfill(5)

    def displayFreeFrag():
        e2ff = self.monitor.e2freefrag()
        print e2ff[0]
        print e2ff[1]
        return 

def main():
    walkman = Walkman()

    #print walkman.monitor.dumpfsSTR(),
    #return


    #walkman.rebuildFS()
    walkman.remakeExt4()
    print 'sleeping 5 sec after building fs....'
    time.sleep(5)

    walkman.displayandsaveConfig()
    time.sleep(5)

    nyears=100
    nseasons_per_year = 7 
    
    for y in range(nyears):
        for s in range(nseasons_per_year):
            rootdir = walkman.getrootdirByIterIndex(s)
            walkman.produceWorkload(rootdir=rootdir)

            walkman.play()

            time.sleep(3)
            walkman.monitor.display(savedata=True, 
                                    logfile=walkman.getLogFilenameBySeasonYear(s,y))

            # now, delete the previous dir if it exists
            pre_s = (s - (nseasons_per_year-1))%nseasons_per_year
            pre_s_rootdir = walkman.getrootdirByIterIndex(pre_s)
            fullpath = os.path.join(walkman.conf.dic['mountpoint'],pre_s_rootdir)
            try:
                print "removing ", fullpath
                shutil.rmtree(fullpath)
            except:
                print "failed to rmtree (but should be OK):", fullpath

            print "------ End of this year, sleep 10 sec ----------"
            time.sleep(10)
            

if __name__ == "__main__":
    main()

