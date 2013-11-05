import glob
import os
import sys
import re

class cd:
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def prettyline(line):
    "line is string with items separated by white space"
    items = line.strip()
    items = items.split()
    items = [str(x).ljust(40) for x in items]
    line = " ".join(items) + '\n'
    return line

keys = ['_extstats', '_extstatssum', '_freefrag_sum',
        '_freefrag_hist', '_freeblocks', '_freeinodes',
        '_walkman_config', '_extlist']

headerwritten = {}
tablefiles = {}

def parsefile(filepath):
    print "doing", filepath
   
    rawfile = open(filepath, 'r')
    
    for line in rawfile:
        mo = re.search(r'(HEADERMARKER|DATAMARKER)(_\w+)', line.upper())
        if mo:
            groups = mo.groups()
            #print groups 
            type = groups[0]
            type = type.upper()
            linekey = groups[1]
            linekey = linekey.lower()
            #print 'type:', type, 'linekey:', linekey

            if type == 'HEADERMARKER' and headerwritten[linekey] == False:
                tablefiles[linekey].write(line)
                headerwritten[linekey] = True
            if type == 'DATAMARKER':
                tablefiles[linekey].write(line)

    rawfile.close()

def main(args):
    if len(args) != 3:
        print "usage:", args[0], 'dirpath', 'filenamekey'
        exit(1)

    dirpath = args[1]
    filenamekey = args[2]

    with cd(dirpath):
        files = glob.glob("*"+filenamekey+"*")
        files = sorted(files)

        # clean up
        zfiles = glob.glob("z*")
        for f in zfiles:
            os.remove(f)
            print "Removed", f

    for key in keys:
        headerwritten[key] = False

    for key in keys:
        tablefiles[key] = open('zparsed.'+key, 'a')
        print "Opened table file for", key

    for f in files:
        if f.endswith(".rows"): # this files are for human readers only
            continue
        parsefile(f)

    for key in keys:
        tablefiles[key].close()
        print "Closed table file for", key

if __name__ == "__main__":
    """
    what we have in the result dir:
        In *result.log*:
            _extstats: how many metadata/data blocks per file, and more
            _extstatssum: total numbers of metadata/data blocks for
                the whole file system
            _freefrag_sum: average size of extent....
            _freefrag_hist: the histgram of extents
            _freeblocks: the start and end block number of each free extent
            _freeinodes: free inode number ranges
        In *.cols:
            _walkman_config: the config of this run (system and workload)
    """
    main(sys.argv)
