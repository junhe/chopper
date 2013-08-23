import glob
import os
import sys
import re

def prettyline(line):
    "line is string with items separated by white space"
    items = line.strip()
    items = items.split()
    items = [str(x).ljust(40) for x in items]
    line = " ".join(items) + '\n'
    return line

def gethist(dirpath, filenamekey):
    linekey = "_freefrag_hist"
    os.chdir(dirpath)


    files = glob.glob("*"+filenamekey+"*")
    files = sorted(files)


    header = ""
    entries = ""
    trans={"B":1,"K":1024,"M":1024*1024,"G":1024*1024*1024}
    for fn in files:
        with open(fn, 'r') as f:
            for line in f:
                if "DATAMARKER"+linekey in line:
                    items = line.lstrip().replace("%", " ")
                    items = items.split()

                    # number
                    mo = re.search(r'\d+', items[0])
                    n = mo.group()
                    # unit
                    mo = re.search('[a-zA-Z]', items[0])
                    u = mo.group()
                    if u == "":
                        u = "B"
                    u = trans[u]
                    
                    items.extend([n,u])
                    items = [str(x) for x in items]
                    entry = " ".join(items) + '\n'
                    print prettyline(entry),

                elif "HEADERMARKER"+linekey in line and header == "":
                    header = line.lstrip().rstrip('\n') + " start_num start_unit\n"
                    print prettyline(header),
                else:
                    pass

def isDataline(linekey, line):
    linekey = "DATAMARKER" + linekey
    linekey = linekey.upper()
    ret = re.search(r'\b'+linekey+r'\b', line.upper())
    return ret

def isHeaderline(linekey, line):
    linekey = "HEADERMARKER" + linekey
    linekey = linekey.upper()
    ret = re.search(r'\b'+linekey+r'\b', line.upper())
    return ret

def gettable(dirpath, filenamekey, linekey):

    if linekey == "_freefrag_hist":
        gethist(dirpath, filenamekey)
        return

    os.chdir(dirpath)

    files = glob.glob("*"+filenamekey+"*")
    files = sorted(files)

    header = ""
    entries = ""
    for fn in files:
        with open(fn, 'r') as f:
            for line in f:
                if isDataline(linekey, line):
                    print prettyline(line),

                elif isHeaderline(linekey, line) \
                        and header == "":
                    header = line
                    print prettyline(header), 
                else:
                    pass
       
    
    
def main(args):
    dirpath = args[1]
    filenamekey = args[2]
    linekey = args[3]
    gettable(dirpath, filenamekey, linekey)

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
