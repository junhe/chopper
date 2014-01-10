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

def main(args):
    if len(args) != 2:
        print "usage:", args[0], 'dirpath'
        exit(1)

    dirpath = args[1]

    with cd(dirpath):
        files = glob.glob("*.rows")
        files = sorted(files)

        for f in files:
            print f
            prefix = '.'.join(f.split('.')[0:-2])
            isext4 = False
            with open(f, 'r') as fo:
                for line in fo:
                    if line.strip() == 'filesystem = ext4':
                        isext4 = True
                        break
            print isext4
            if isext4:
                os.remove( prefix + ".conf.rows" )
                os.remove( prefix + ".conf.cols" )
                r = prefix + ".result.log.year00000.season00001" 
                if os.path.exists(r):
                    os.remove(r)

if __name__ == "__main__":
    main(sys.argv)
