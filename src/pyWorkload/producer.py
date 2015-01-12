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

# Let me think about what I want to test with metawalker here.
# Examples:
#   concurrent writes, frequent file open, 
import os
import itertools
import re

class Producer:
    """
    """
    def __init__ (self, np=1, startOff=0, nwrites_per_file=1, nfile_per_dir=1, 
              ndir_per_pid=1, wsize=1, wstride=1, rootdir="", tofile="", 
              fsync_per_write=False, fsync_before_close=True):
        self.setParameters(
              np, startOff, nwrites_per_file, nfile_per_dir, ndir_per_pid,
              wsize, wstride, rootdir, tofile, fsync_per_write, fsync_before_close)
        self.workload = ""

    def addReadOrWrite(self, op, pid, dirid, fileid, off, len):
        "op: read/write"
        path = self.getFilepath(dir=dirid, pid=pid, file_id=fileid)
        entry = str(pid)+";"+path+";"+op.lower()+";"+str(off)+";"+str(len)+"\n"
        self.workload += entry

    def addReadOrWrite2(self, op, pid, path, off, len):
        "op: read/write"
        fullpath = self.getFullpath(path)
        entry = str(pid)+";"+fullpath+";"+op.lower()+";"+str(off)+";"+str(len)+"\n"
        self.workload += entry

    def addUniOp(self, op, pid, dirid, fileid):
        "op: open/close/fsync"
        path = self.getFilepath(dir=dirid, pid=pid, file_id=fileid)
        entry = str(pid)+";"+path+";"+op.lower()+"\n";
        self.workload += entry

    def addUniOp2(self, op, pid, path):
        """
        All functions with suffix '2' use path instead of (dirid, fileid)
        op: open/close/fsync
        """
        fullpath = self.getFullpath(path)
        entry = str(pid)+";"+fullpath+";"+op.lower()+"\n";
        self.workload += entry

    def addDirOp(self, op, pid, dirid):
        path = self.getDirpath(dir=dirid, pid=pid)
        entry = str(pid)+";"+path+";"+op.lower()+"\n";
        self.workload += entry

    def addDirOp2(self, op, pid, path):
        fullpath = self.getFullpath(path)
        entry = str(pid)+";"+fullpath+";"+op.lower()+"\n";
        self.workload += entry

    def addOSOp(self, op, pid):
        """
        op: sync(call sync())
        This assigned pid should do this
        """
        entry = str(pid)+";"+"NA"+";"+op.lower()+"\n";
        self.workload += entry

    def addSetaffinity(self, pid, cpuid):
        entry = str(pid)+";"+"NA"+";"+"sched_setaffinity;"+str(cpuid)+'\n'
        self.workload += entry

    def display(self):
        print self.workload

    def setParameters(self, 
              np, startOff, nwrites_per_file, nfile_per_dir, ndir_per_pid,
              wsize, wstride, rootdir, tofile, fsync_per_write, fsync_before_close):
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
        self.fsync_before_close = fsync_before_close

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
              wsize, wstride, rootdir, tofile="", 
              fsync_per_write=False, 
              fsync_before_close=True):
        self.np = np
        self.startOff = startOff

        # pid->dir->file->writes
        self.nwrites_per_file = nwrites_per_file
        self.nfile_per_dir = nfile_per_dir
        self.ndir_per_pid = ndir_per_pid

        self.wsize = wsize
        self.wstride = wstride
        self.fsync_per_write = fsync_per_write
        self.fsync_before_close = fsync_before_close

        self.rootdir = rootdir
        self.tofile = tofile

        self.workload = self._produce()
        
        if tofile != "":
            self.saveWorkloadToFile()
        
        return self.workload

    
    def getFilepath(self, dir, pid, file_id ):
        fname = ".".join( ['pid',str(pid).zfill(5), 'file',
            str(file_id).zfill(5)] )
        dirname = self.getDirpath(pid, dir)
        return os.path.join(dirname, fname)

    def getDirpath(self, pid, dir):
        dirname = "pid" + str(pid).zfill(5) + ".dir" + str(dir).zfill(5) + "/" 
        return os.path.join(self.rootdir, dirname)
    
    def getFullpath(self, path):
        return os.path.join(self.rootdir, path)

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
        if self.fsync_before_close:
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

