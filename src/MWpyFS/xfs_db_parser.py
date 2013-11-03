import os
import re
import pprint


lines01="""
u = (empty)
"""

lines02="""
next_unlinked = null
u.bmbt.level = 1
u.bmbt.numrecs = 1
u.bmbt.keys[1] = [startoff] 1:[0]
u.bmbt.ptrs[1] = 1:12299
"""

lines03="""
magic = 0x424d4150
level = 1
numrecs = 14
leftsib = null
rightsib = null
keys[1-14] = [startoff] 1:[0] 2:[721600] 3:[924800] 4:[1128000] 5:[1331200] 6:[1534400] 7:[1737600] 8:[1940800] 9:[2144000] 10:[2347200] 11:[2550400] 12:[2753600] 13:[2956800] 14:[3073600]
ptrs[1-14] = 1:196428 2:917764 3:918019 4:918274 5:918529 6:918784 7:919039 8:919294 9:919549 10:919804 11:920060 12:920315 13:920570 14:920825
"""


lines04="""
magic = 0x424d4150
level = 0
numrecs = 254
leftsib = null
rightsib = 917764
recs[1-254] = [startoff,startblock,blockcount,extentflag] 1:[0,12,16,0] 2:[800,44,16,0] 3:[1600,844,512,0] 4:[2400,1868,1024,0] 5:[4000,3916,2048,0] 6:[6400,8012,4096,0] 7:[11200,16204,8192,0] 8:[20000,32588,16384,0] 9:[36800,65356,32768,0] 10:[69600,130892,65536,0] 
"""


def xfs_parse_lines(lines):
    lines = lines.split('\n')

    # put each line to a dicitionary
    line_dict = {}
    for line in lines:
        print line
        if "=" in line:
            items = line.split("=")
            assert len(items) == 2

            key = items[0]
            key = key.strip()
            key = re.sub(r'\[.*\]', "", key)

            value = items[1]
            value = value.strip()

            assert not line_dict.has_key(key)
            line_dict[key] = value

    pprint.pprint(line_dict)
    return line_dict

def xfs_empty_u(line_dict):
    if line_dict.has_key('u') and line_dict['u'] == "(empty)":
        return True
    else:
        return False

def xfs_parse_type01(keystr):
    """ it can parse:
            u.bmbt.keys[1] = [startoff] 1:[0]
            keys[1-14] = [startoff] 1:[0] 2:[721600] 3:[924800] ....
        The return is ['0', '721600', '924800', '1128000',....
    """
    keys = re.findall(r'\d+:\[(\d+)\]', keystr)
    return keys

def xfs_parse_type02(ptrstr):
    ptrs = re.findall(r'\d+:(\d+)', ptrstr)
    return ptrs

def xfs_parse_type03(recstr):
    "The return is: [(x,x,x,x), (x,x,x,x), ...]"
    recs = re.findall(r'\d+:\[(\d+),(\d+),(\d+),(\d+)\]', recstr)
    return recs

def main():
    d = xfs_parse_lines(lines04)
    #xfs_parse_keys(d['keys'])
    #print xfs_parse_ptrs(d['ptrs'])
    #print xfs_parse_recs(d['recs'])
    #print xfs_parse_empty_u(d)
    #xfs_parse_lines(lines02)


if __name__ == "__main__":
    main()
