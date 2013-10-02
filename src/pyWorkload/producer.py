# Let me think about what I want to test with metawalker here.
# Examples:
#   concurrent writes, frequent file open, 
import os
class Producer:
    """
    """
    def __init__ (self, np=1, startOff=0, nwrites_per_file=1, nfile_per_dir=1, 
              ndir_per_pid=1, wsize=1, wstride=1, rootdir="", tofile="", 
              fsync_per_write=False):
        self.setParameters(
              np, startOff, nwrites_per_file, nfile_per_dir, ndir_per_pid,
              wsize, wstride, rootdir, tofile, fsync_per_write)
        self.workload = ""

    def addReadOrWrite(self, op, pid, dirid, fileid, off, len):
        "op: read/write"
        path = self.getFilepath(dir=dirid, pid=pid, file_id=fileid)
        entry = str(pid)+";"+path+";"+op.lower()+";"+str(off)+";"+str(len)+"\n"
        self.workload += entry

    def addUniOp(self, op, pid, dirid, fileid):
        "op: open/close/fsync"
        path = self.getFilepath(dir=dirid, pid=pid, file_id=fileid)
        entry = str(pid)+";"+path+";"+op.lower()+"\n";
        self.workload += entry

    def addDirOp(self, op, pid, dirid):
        path = self.getDirpath(dir=dirid, pid=pid)
        entry = str(pid)+";"+path+";"+op.lower()+"\n";
        self.workload += entry


    def display(self):
        print self.workload

    def setParameters(self, 
              np, startOff, nwrites_per_file, nfile_per_dir, ndir_per_pid,
              wsize, wstride, rootdir, tofile, fsync_per_write):
        self.np = np
        self.startOff = startOff

        self.nwrites_per_file = nwrites_per_file
        self.nfile_per_dir = nfile_per_dir
        self.ndir_per_pid = ndir_per_pid

        self.wsize = wsize
        self.wstride = wstride

        self.rootdir = rootdir
        self.tofile = tofile

        self.fsync_per_write = fsync_per_write

    def saveWorkloadToFile(self):
         self.save2file(self.workload, self.tofile)
  
    def save2file(self, workload_str, tofile=""):
        if tofile != "":
            with open(tofile, 'w') as f:
                f.write(workload_str)
                f.flush()
            print "save2file. workload saved to file"
        else:
            print "save2file. no output file assigned"

    def produce_rmdir (self, np, ndir_per_pid, rootdir, pid=0, tofile=""):
        workload = ""
        for p in range(np):
            for dir in range(ndir_per_pid):
                path = self.getDirpath(p, dir)
                entry = str(p)+";"+path+";"+"rm"+"\n";
                workload += entry
        
        return workload

    def produce (self, 
              np, startOff, nwrites_per_file, nfile_per_dir, ndir_per_pid,
              wsize, wstride, rootdir, tofile="", fsync_per_write=False):
        self.np = np
        self.startOff = startOff

        # pid->dir->file->writes
        self.nwrites_per_file = nwrites_per_file
        self.nfile_per_dir = nfile_per_dir
        self.ndir_per_pid = ndir_per_pid

        self.wsize = wsize
        self.wstride = wstride
        self.fsync_per_write = fsync_per_write

        self.rootdir = rootdir

        workload = self._produce()
        
        if tofile != "":
            self.save2file(workload, tofile=tofile)
        
        return workload

    
    def getFilepath(self, dir, pid, file_id ):
        fname = ".".join( ['pid',str(pid).zfill(5), 'file',
            str(file_id).zfill(5)] )
        dirname = self.getDirpath(pid, dir)
        return os.path.join(dirname, fname)

    def getDirpath(self, pid, dir):
        dirname = "pid" + str(pid).zfill(5) + ".dir" + str(dir).zfill(5) + "/" 
        return os.path.join(self.rootdir, dirname)
        

    def _produce(self):
        workload = ""
        
        # make dir
        for p in range(self.np):
            for dir in range(self.ndir_per_pid):
                path = os.path.join(self.rootdir, self.getDirpath(p, dir))
                entry = str(p)+";"+path+";"+"mkdir"+"\n";
                workload += entry

        # Open file
        for fid in range(self.nfile_per_dir):
            for dir in range(self.ndir_per_pid):
                for p in range(self.np):
                    path = self.getFilepath(dir, p, fid)
                    entry = str(p)+";"+path+";"+"open"+"\n";
                    workload += entry

        #cur_off[pid][dir][fid]
        cur_off = [[[self.startOff for x in xrange(self.nfile_per_dir)] for x in xrange(self.ndir_per_pid)] for x in xrange(self.np)]
        for w_index in range(self.nwrites_per_file):
            for fid in range(self.nfile_per_dir):
                for dir in range(self.ndir_per_pid):
                    for p in range(self.np):
                        size = self.wsize
                        path = self.getFilepath(dir, p, fid)

                        entry = str(p)+";"+path+";"+"write"+";"+str(cur_off[p][dir][fid])+";"+str(size)+"\n"
                        cur_off[p][dir][fid] += self.wstride

                        workload += entry

                        if self.fsync_per_write:
                            entry = str(p)+";"+path+";"+"fsync"+"\n";
                        workload += entry

        # fsync file
        for fid in range(self.nfile_per_dir):
            for dir in range(self.ndir_per_pid):
                for p in range(self.np):
                    path = self.getFilepath(dir, p, fid)
                    entry = str(p)+";"+path+";"+"fsync"+"\n";
                    workload += entry


        # close file
        for fid in range(self.nfile_per_dir):
            for dir in range(self.ndir_per_pid):
                for p in range(self.np):
                    path = self.getFilepath(dir, p, fid)
                    entry = str(p)+";"+path+";"+"close"+"\n";
                    workload += entry

        return workload


#prd = Producer(rootdir='/l0')

#prd.addUniOp('open', 0, 0, 0)
#prd.addReadOrWrite('read', 0, 0, 0, 8, 3)
#prd.addReadOrWrite('read', 0, 0, 0, 8, 3)
#prd.addReadOrWrite('read', 0, 0, 0, 8, 3)
#prd.addReadOrWrite('read', 0, 0, 0, 8, 3)
#prd.addReadOrWrite('write', 0, 0, 0, 8, 3)
#prd.addUniOp('fsync', 0, 0, 0)
#prd.addUniOp('close', 0, 0, 0)
#prd.display()
##print prd.produce(np=1, startOff=0, 
                ##nwrites_per_file = 64, 
                ##nfile_per_dir=1, 
                ##ndir_per_pid=1,
                ##wsize=16, 
                ##wstride=16, 
                ##rootdir="/mnt/scratch/", 
                ##tofile="tmp.workload",
                ##fsync_per_write=True),

#print prd.produce(np=1, startOff=0, 
                #nwrites_per_file = 1024*1024, 
                #nfile_per_dir=1, 
                #ndir_per_pid=1,
                #wsize=1, 
                #wstride=1, 
                #rootdir="/mnt/scratch/", 
                #tofile="tmp.workload",
                #fsync_per_write=True),


