# Let me think about what I want to test with metawalker here.
# Examples:
#   concurrent writes, frequent file open, 

class Producer:
    """
    """
    def produce (self, np, startOff, nwrites_per_file, nfile_per_dir, ndir_per_pid,
              wsize, wstride, mountpoint, tofile=""):
        self.np = np
        self.startOff = startOff

        # pid->dir->file->writes
        self.nwrites_per_file = nwrites_per_file
        self.nfile_per_dir = nfile_per_dir
        self.ndir_per_pid = ndir_per_pid

        self.wsize = wsize
        self.wstride = wstride

        self.mountpoint = mountpoint

        workload = self._produce()

        if tofile == "":
            return workload
        else:
            with open(tofile, 'w') as f:
                f.write(workload)
            return ""
    
    def getFilepath(self, dir, pid, file_id ):
        fname = ".".join( [str(pid), str(file_id), "file"] )
        dirname = self.getDirpath(pid, dir)
        return dirname + fname

    def getDirpath(self, pid, dir):
        return "pid" + str(pid) + ".dir" + str(dir) + "/" 
        

    def _produce(self):
        workload = ""
        
        # make dir
        for p in range(self.np):
            for dir in range(self.ndir_per_pid):
                path = self.mountpoint + self.getDirpath(p, dir)
                entry = str(p)+";"+path+";"+"mkdir"+"\n";
                workload += entry

        # Open file
        for fid in range(self.nfile_per_dir):
            for dir in range(self.ndir_per_pid):
                for p in range(self.np):
                    path = self.mountpoint + self.getFilepath(dir, p, fid)
                    entry = str(p)+";"+path+";"+"open"+"\n";
                    workload += entry


        #cur_off[pid][dir][fid]
        cur_off = [[[self.startOff for x in xrange(self.nfile_per_dir)] for x in xrange(self.ndir_per_pid)] for x in xrange(self.np)]
        for w_index in range(self.nwrites_per_file):
            for fid in range(self.nfile_per_dir):
                for dir in range(self.ndir_per_pid):
                    for p in range(self.np):
                        size = self.wsize
                        path = self.mountpoint + self.getFilepath(dir, p, fid)

                        entry = str(p)+";"+path+";"+"write"+";"+str(cur_off[p][dir][fid])+";"+str(size)+"\n"
                        cur_off[p][dir][fid] += self.wstride

                        workload += entry
        # fsync file
        for fid in range(self.nfile_per_dir):
            for dir in range(self.ndir_per_pid):
                for p in range(self.np):
                    path = self.mountpoint + self.getFilepath(dir, p, fid)
                    entry = str(p)+";"+path+";"+"fsync"+"\n";
                    workload += entry


        # close file
        for fid in range(self.nfile_per_dir):
            for dir in range(self.ndir_per_pid):
                for p in range(self.np):
                    path = self.mountpoint + self.getFilepath(dir, p, fid)
                    entry = str(p)+";"+path+";"+"close"+"\n";
                    workload += entry

        return workload

#print prd.produce(np=2, startOff=0, 
                #nwrites_per_file = 1000, 
                #nfile_per_dir=3, 
                #ndir_per_pid=2,
                #wsize=3331, 
                #wstride=3331, 
                #mountpoint="/mnt/scratch/", 
                #tofile="tmp.workload"),



