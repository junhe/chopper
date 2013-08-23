import glob
import os
import sys
import re

dirpath = sys.argv[1]
filenamekey = sys.argv[2]

#filenamekey = "2013-08-19-13-39-52"
linekey = "_walkman_config"
os.chdir(dirpath)


files = glob.glob("*"+filenamekey+"*")
files = sorted(files)


header = ""
entries = ""
for fn in files:
    with open(fn, 'r') as f:
        for line in f:
            if "DATAMARKER"+linekey in line:
                items = line.strip()
                items = items.split()
                items = [str(x).ljust(40) for x in items]
                entry = " ".join(items) + '\n'
                print entry,

            elif "HEADERMARKER".lower()+linekey in line and header == "":
                items = line.strip().split()
                items = [str(x).ljust(40) for x in items]
                header = " ".join(items) + '\n'
                print header,
            else:
                pass

