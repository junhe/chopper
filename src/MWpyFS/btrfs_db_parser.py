import os
import subprocess
import pprint
import re


def btrfs_debug_tree(partition):
    cmd = ['btrfs-debug-tree', partition]
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE)

    db_tree_lines = [] 
    for line in proc.stdout:
        db_tree_lines.append(line)
    proc.wait()
    return db_tree_lines


#pprint.pprint(btrfs_debug_tree('/dev/loop0'))
#print btrfs_debug_tree('/dev/loop0')

class TreeParser:
    def __init__ (self, tree_lines):
        self.lines = tree_lines
        self.line_count = len(self.lines)

    def parse(self):
        """
        number of tab before a line = level of the line
        """
        path = []
        for line in self.lines:
            d = line_dict(line)
            if d.has_key('type') and d['type'] != None:
                print d
    
def get_key(line):
    key = re.findall(r'\((\S+) (\S+) (\S+)\)', line)
    assert len(key) <= 1, 'I assume at most one key per line.'
    dic = None
    if len(key) == 1:
        dic = {'objectid':key[0][0],
                   'type':key[0][1],
                 'offset':key[0][2]
            }
    return dic

def line_dict(line):
    """
    Put information of a line into a dictionary
    """
    ldict = {}
    ldict['level'] = nPrefixTab(line)
    if ldict['level'] == 0:
        ldict['type'] = level0_type(line)
        ldict['key'] = get_key(line)
    return ldict

def level0_type(line):
    line = line.strip()
    types = ['root tree',
            'chunk tree',
            'extent tree',
            'device tree',
            'fs tree',
            'checksum tree']
    for type in types:
        if line.startswith(type):
            return type
    return None

def nPrefixTab(line):
    #print line
    count = 0
    while line.startswith('\t', count):
        count += 1 
        #print count
    return count

def debug_main():

    #line = "\t\tdebug_mainextent csum item"
    #nPrefixTab(line)
    
    #return

    #get_key("device tree key (DEV_TREE ROOT_ITEM 0)")
    #return 
    f = open("./abtrfsdebugtree-output", 'r')

    lines = []
    for line in f:
        lines.append(line)

    tparser = TreeParser(lines)
    tparser.parse()


debug_main()

