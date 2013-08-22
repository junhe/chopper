import glob
import os
import sys
import re

dirpath = sys.argv[1]
filenamekey = sys.argv[2]

#filenamekey = "2013-08-19-13-39-52"
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
                print entry,

            elif "HEADERMARKER"+linekey in line and header == "":
                header = line.lstrip().rstrip('\n') + " start_num start_unit\n"
                print header,
            else:
                pass

