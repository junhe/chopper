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

    def addUniOp(self, op, pid, dirid, fileid):
        "op: open/close/fsync"
        path = self.getFilepath(dir=dirid, pid=pid, file_id=fileid)
        entry = str(pid)+";"+path+";"+op.lower()+"\n";
        self.workload += entry

    def addDirOp(self, op, pid, dirid):
        path = self.getDirpath(dir=dirid, pid=pid)
        entry = str(pid)+";"+path+";"+op.lower()+"\n";
        self.workload += entry

    def addOSOp(self, op, pid):
        """
        op: sync(call sync())
        This assigned pid should do this
        """
        entry = str(pid)+";"+"NA"+";"+op.lower()+"\n";
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

def GenFBWorkload(write_pattern_dic,
                 writes_per_flush=1,
                 rootdir = "/tmp",
                 tofile = "/tmp/workload"
                 ):
    """
    write_pattern_dic: a dictionary has file size, segment size, write size
        and write direction('INCREASE' or 'DECREASE'). 
    """
    # You'd better be aligned
    assert write_pattern_dic['file_size'] % write_pattern_dic['segment_size'] == 0
    assert write_pattern_dic['segment_size'] % write_pattern_dic['write_size'] == 0

    n_writes_per_seg = write_pattern_dic['segment_size'] / \
                        write_pattern_dic['write_size']
    n_segments = write_pattern_dic['file_size'] / \
                  write_pattern_dic['segment_size']

    writes_in_seg = range(0, n_writes_per_seg)
    if write_pattern_dic['direction'] == 'DECREASE':
        writes_in_seg.sort(reverse=True)

    # OK, produce the workload
    prd = Producer(
            rootdir = rootdir,
            tofile = tofile)
    prd.addDirOp('mkdir', pid=0, dirid=0)
    prd.addUniOp('open', pid=0, dirid=0, fileid=0)

    nwrites_finished = 0
    for write_i in writes_in_seg:
        for seg_i in range(0, n_segments):
            woff = seg_i * write_pattern_dic['segment_size'] +\
                    write_i * write_pattern_dic['write_size']
            wsize = write_pattern_dic['write_size']

            #print woff, wsize
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=woff, len=wsize)
            nwrites_finished += 1

            if nwrites_finished % writes_per_flush == 0:
                prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

    prd.addUniOp('close', pid=0, dirid=0, fileid=0)

    prd.display()
    prd.saveWorkloadToFile()


##################################################
##################################################
##################################################
##################################################
# The fancy state exploration
##################################################


def SingleFileTraverse(
                filesize,
                num_of_chunks):
    chunk_size = filesize / num_of_chunks
    chunk_sizes = [chunk_size] * num_of_chunks
    offsets = range(0, filesize, chunk_size)
    chunks = zip(offsets, chunk_sizes)

    chunk_iter = itertools.permutations(chunks)
    wrapper_iter = itertools.product([False, True], repeat=num_of_chunks*4)
    # it is like this
    # OPEN chunk FSYNC CLOSE, OPEN chunk FSYNC CLOSE, ...
    # every 3 number in wrapper_iter represents whether or not
    # do OPEN FSYNC CLOSE SYNC
    # Each chunk has such a wrapper, so there are num_of_chunks*3 numbers

    # Let's not trim the results first. 
    # Get a prototype working!
    #
    # Rules:
    #   Fsync/chunks must within open-close
    #   SYNC must be out of open-close
    #   no nested open-close
    #   
    
    for chks in chunk_iter:
        for wraps in wrapper_iter:
            # check if wrapper is legal
            GenWorkloadFromChunks(chks, wraps,
                    rootdir='/mnt/scratch',
                    tofile='/tmp/workload')
        break


def Filter( opstr, keep ):
    # input is like (FSYNC, True)
    if keep:
        return opstr 
    else:
        return ""

def IsLegal( wrappers ):
    "conver to string and use regex"
    num_of_chunks = len(wrappers) / 4
    #strs = ['OPEN', 'FSYNC', 'CLOSE', 'SYNC'] * num_of_chunks
    symbols = ['(', 'C', 'F', ')', 'S'] * num_of_chunks

    choices = [ (wrappers[i], True, wrappers[i+1], wrappers[i+2], wrappers[i+3]) \
                    for i in range(0, num_of_chunks*4, 4) ]
    choices = list(itertools.chain.from_iterable(choices))
    seq = map(Filter, symbols, choices)
    seq = ''.join(seq)
   
    # use regex to check seq
    #
    # GOOD ONE backup: mo = re.match(r'^(\((C+F?)+\)S?)+$', seq, re.M)
    mo = re.match(r'^(\(((CC)+F?)+\)S)+$', seq, re.M)
    if mo:
        print "good match!", seq
        return True
    else:
        #print 'BAD match!', seq
        return False

def GenWorkloadFromChunks( chunks,
                           wrappers,
                           rootdir,
                           tofile
                           ):
        
    # check if it is legal
    if not IsLegal( wrappers ):
        return False

    num_of_chunks = len(chunks)

    # organize it as dictionary
    chunks = [ dict( zip( ['offset', 'length'], c ) ) \
                                                    for c in chunks ]
    # group wrapers to 3 element groups
    wrappers = [wrappers[i:i+4] for i in range(0, num_of_chunks*4, 4) ]
    wrappers = [ dict( zip(['OPEN', 'FSYNC', 'CLOSE', 'SYNC'], w) ) \
                                                    for w in wrappers]

    prd = Producer(
            rootdir = rootdir,
            tofile = tofile)
    prd.addDirOp('mkdir', pid=0, dirid=0)

    # ( (off,size), {wrapper} )
    entries = zip(chunks, wrappers)
    for entry in entries:
        #print entry
        if entry[1]['OPEN']:
            prd.addUniOp('open', pid=0, dirid=0, fileid=0)
        
        # the chunk write
        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=0, off=entry[0]['offset'], len=entry[0]['length'])

        if entry[1]['FSYNC']: 
            prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        if entry[1]['CLOSE']: 
            prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        if entry[1]['SYNC']:
            prd.addOSOp('sync', pid=0)

    prd.display()
    prd.saveWorkloadToFile()
    return True

def debug_main():
    wpd = {
            'segment_size': 100,
            'write_size'  : 50,
            'file_size'   : 200,
            #'direction'   : 'INCREASE'
            'direction'   : 'DECREASE'
          }
    GenFBWorkload(write_pattern_dic = wpd,
                 writes_per_flush = 2)



#SingleFileTraverse(filesize=100, num_of_chunks=4)
#debug_main()
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


