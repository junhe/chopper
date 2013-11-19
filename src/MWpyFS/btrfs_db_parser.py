import os
import subprocess
import pprint
import re
import dataframe
import Monitor


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
        # path is used to hold dictionaries along from root to the
        # current node
        path = [None]*10 

        # node_queue[i] store entries of a child node of path[i-1]
        node_queue = [[]]*10 

        # dataframe to store the results
        df_ext = dataframe.DataFrame()
        df_chunk = dataframe.DataFrame()
        df_fname = dataframe.DataFrame()

        cur_level = -1 
        for line in self.lines:
            pre_level = cur_level
            cur_level = nPrefixTab(line)
            
            line_dic = line_parts(line)
            #print "cur_level", cur_level, "pre_level", pre_level, 'linetype', 
            #if line_dic:
                #print line_dic['linetype']
            #else:
                #print "UNKNOWN"

            if cur_level > pre_level:
                #   XXXXXX <- pre
                #       XXXXXXX <- cur
                #path[cur_level] = line_dic # It could be None
                node_queue[cur_level] = [line_dic]
            elif cur_level == pre_level:
                #   XXXXXX <- pre
                #   XXXXXXX <- cur
                if line_dic != None:
                    #path[cur_level].update(line_dic)
                    node_queue[cur_level].append(line_dic)
                else:
                    pass
            else:
                #       XXXXXX <- pre
                #   XXXXXXX <- cur
                #path[pre_level] = None
                node_queue[pre_level] = [] # probably not necessary, but good to clean
                node_queue[cur_level] = [line_dic] # It can be None
            #pprint.pprint( node_queue )

            # Now you can get what you want.
            
            # Let's do the math work in R, here
            # we only print out things like:
            #
            # EXTENT_DATA_DATA INODE_NUMBER Logical_start virtual_start length

            if node_queue[cur_level] != [] and \
                    node_queue[cur_level][-1] != None and \
                    node_queue[cur_level][-1]['linetype'] == 'EXTENT_DATA_DATA_3':
                # we know we have a whole extent
                #print path[cur_level]
                #print "Parent:", path[cur_level-1]['key']['objectid']

                # for short
                ext_dic_1 = node_queue[cur_level][0]
                ext_dic_2 = node_queue[cur_level][1]
                ext_dic_3 = node_queue[cur_level][2]
                parent = node_queue[cur_level - 1][-1]

                #pprint.pprint( node_queue )

                # Note that when extent_disk_number_of_bytes == 0, this is
                # an empty extent and should not be used to show data.
                if ext_dic_1['extent_disk_byte'] != '0' and \
                        ext_dic_1['extent_disk_number_of_bytes'] != '0':
                    # Ignore the empty extent
                    
                    dic = { 'inode_number': parent['key']['objectid'],
                        'Logical_start': parent['key']['offset'],
                        'Virtual_start': int(ext_dic_1['extent_disk_byte']) + 
                                         int(ext_dic_2['in_extent_offset']),
                        'Length': ext_dic_2['in_extent_number_of_bytes']
                        }
                    if df_ext.header == []:
                        df_ext.header = dic.keys()
                    df_ext.addRowByDict(dic)
                    #print dic
            elif node_queue[cur_level] != [] and \
                    node_queue[cur_level][-1] != None and \
                    node_queue[cur_level][-1]['linetype'] == "CHUNK_ITEM_DATA_STRIPE":

                grandparent = node_queue[cur_level - 2][-1]
                
                stripe_dic = node_queue[cur_level][-1]
                stripe_dic['chunk_virtual_off_start'] = grandparent['key']['offset']

                #print stripe_dic
                if df_chunk.header == []:
                    df_chunk.header = stripe_dic.keys()
                
                df_chunk.addRowByDict(stripe_dic)

            elif node_queue[cur_level] != [] and \
                    node_queue[cur_level][-1] != None and \
                    node_queue[cur_level][-1]['linetype'] == "INODE_REF_DATA":
                parent = node_queue[cur_level - 1][-1]
                ref_dic = node_queue[cur_level][-1]

                #ref_dic.update( parent )
                #print ref_dic
                #dic = {}
                #dic['inode_number'] = ref_dic['key']['objectid']
                pass

        #print df_ext.toStr()
        #print df_chunk.toStr()
        return {'extents':df_ext, 'chunks':df_chunk}

def get_filepath_inode_map(mountpoint, dir):
    paths = Monitor.get_all_paths(mountpoint, dir)

    df = dataframe.DataFrame()
    df.header = ['filepath', 'inode_number']
    for path in paths:
        inode_number = Monitor.stat_a_file(os.path.join(mountpoint, path))['inode_number']
        df.addRowByList([path, inode_number])

    return df


def line_parts(line):
    """
    Parse key or item line, return parts in a dictionary
    KEY: linetype=KEYLINE
        key (0 BLOCK_GROUP_ITEM 4194304) block 29900800 (7300) gen 11
    ITEM: linetype=ITEMLINE
        item 0 key (0 BLOCK_GROUP_ITEM 4194304) itemoff 3971 itemsize 24
    LEAF: linetype=LEAFLINE
        leaf 30089216 items 9 free space 2349 generation 11 owner 1
    FSUUID: linetype=FSUUIDLINE
        fs uuid 07050600-b92a-4d31-bc52-d21ad6b02b3c
    CHUNKUUID: linetype=chunkuuid
        chunk uuid 764626ad-671b-4dd8-ab2e-a05b75602fec
    NODE: linetype=NODELINE
        node 29888512 level 1 items 3 free 118 generation 11 owner 2
    """
    orgin_line = line
    line = line.strip()

    # linetype=ROOT_ROOT_TREE_LINE
    # root tree
    mo = re.match(r'root tree', line)
    if mo:
        dic = {}
        dic['linetype'] = 'ROOT_ROOT_TREE_LINE'

        return dic

    # linetype=ROOT_CHUNK_TREE_LINE
    mo = re.match(r'chunk tree', line)
    if mo:
        dic = {}
        dic['linetype'] = 'ROOT_CHUNK_TREE_LINE'

        return dic

    # linetype=ROOT_EXTENT_TREE_LINE
    # extent tree key (EXTENT_TREE ROOT_ITEM 0)
    mo = re.match(r'extent tree key \(EXTENT_TREE ROOT_ITEM (\d+)\)',
            line)
    if mo:
        dic = {}
        dic['linetype'] = 'ROOT_EXTENT_TREE_LINE'
        dic['key'] = {
                        'objectid':'EXTENT_TREE',
                        'type':'ROOT_ITEM',
                        'offset':mo.group(1)
                     }
        return dic

    # linetype=ROOT_DEV_TREE_LINE
    # device tree key (DEV_TREE ROOT_ITEM 0)
    mo = re.match(r'device tree key \(DEV_TREE ROOT_ITEM (\d+)\)',
            line)
    if mo:
        dic = {}
        dic['linetype'] = 'ROOT_DEV_TREE_LINE'
        dic['key'] = {
                        'objectid':'DEV_TREE',
                        'type':'ROOT_ITEM',
                        'offset':mo.group(1)
                     }
        return dic

    # linetype=ROOT_FS_TREE_LINE
    # fs tree key (FS_TREE ROOT_ITEM 0)
    mo = re.match(r'fs tree key \(FS_TREE ROOT_ITEM (\d+)\)',
            line)
    if mo:
        dic = {}
        dic['linetype'] = 'ROOT_FS_TREE_LINE'
        dic['key'] = {
                        'objectid':'FS_TREE',
                        'type':'ROOT_ITEM',
                        'offset':mo.group(1)
                     }
        return dic

    # linetype=ROOT_CSUM_TREE_LINE
    # checksum tree key (CSUM_TREE ROOT_ITEM 0)
    mo = re.match(r'checksum tree key \(CSUM_TREE ROOT_ITEM (\d+)\)',
            line)
    if mo:
        dic = {}
        dic['linetype'] = 'ROOT_CSUM_TREE_LINE'
        dic['key'] = {
                        'objectid':'CSUM_TREE',
                        'type':'ROOT_ITEM',
                        'offset':mo.group(1)
                     }
        return dic

    # linetype=ROOT_DATA_RELOC_TREE_LINE
    # data reloc tree key (DATA_RELOC_TREE ROOT_ITEM 0)
    mo = re.match(r'data reloc tree key \(DATA_RELOC_TREE ROOT_ITEM (\d+)\)',
            line)
    if mo:
        dic = {}
        dic['linetype'] = 'ROOT_DATA_RELOC_TREE_LINE'
        dic['key'] = {
                        'objectid':'ROOT_RELOC_TREE',
                        'type':'ROOT_ITEM',
                        'offset':mo.group(1)
                     }
        return dic


    # Match KEYLINE
    mo = re.match(r'key \((\S+) (\S+) (\S+)\) block (\d+) \((\S+)\) gen (\d+)',
            line)
    if mo:
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'KEYLINE'
        dic['key'] = {'objectid':mo.group(1), 
                      'type': mo.group(2),
                      'offset':mo.group(3)}
        dic['pointer'] = {'block':mo.group(4),
                          'block2':mo.group(5),
                          'gen':mo.group(6)}
        return dic

    # Match item line
    mo = re.match(r'item (\d+) key \((\S+) (\S+) (\S+)\) itemoff (\d+) itemsize (\d+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'ITEMLINE'
        dic['item'] = {'number':mo.group(1),
                       'itemoff':mo.group(5),
                       'itemsize':mo.group(6)}
        dic['key'] = {'objectid': mo.group(2),
                      'type': mo.group(3),
                      'offset': mo.group(4)}
        return dic


    # LEAF: linetype=LEAFLINE
    #     leaf 30089216 items 9 free space 2349 generation 11 owner 1
    mo = re.match(r'leaf (\d+) items (\d+) free space (\d+) generation (\d+) owner (\d+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'LEAFLINE'
        dic['block'] = mo.group(1) # Not sure!
        dic['number_of_items'] = mo.group(2)
        dic['free_space'] = mo.group(3)
        dic['generation'] = mo.group(4)
        dic['owner'] = mo.group(5)
        
        return dic

    #FSUUID: linetype=FSUUIDLINE
    #    fs uuid 07050600-b92a-4d31-bc52-d21ad6b02b3c
    mo = re.match(r'fs uuid (\S+)', line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'FSUUIDLINE'
        dic['fs_uuid'] = mo.group(1)

        return dic

    #CHUNKUUID: linetype=chunkuuid
    #    chunk uuid 764626ad-671b-4dd8-ab2e-a05b75602fec
    mo = re.match(r'chunk uuid (\S+)', line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'CHUNKUUIDLINE'
        dic['chunk_uuid'] = mo.group(1)

        return dic
  
    #NODE: linetype=NODELINE
    #    node 29888512 level 1 items 3 free 118 generation 11 owner 2
    mo = re.match(r'node (\d+) level (\d+) items (\d+) free (\d+) generation (\d+) owner (\d+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'NODELINE'
        dic['block'] = mo.group(1)
        dic['level'] = mo.group(2)
        dic['number_of_items'] = mo.group(3)
        dic['free_space'] = mo.group(4)
        dic['generation'] = mo.group(5)
        dic['owner'] = mo.group(6)

        return dic



    ###########################################################
    # Chunk Tree

    # linetype=DEV_ITEM_DATA
    # dev item devid 1 total_bytes 4294967296 bytes used 896598016
    mo = re.match(r'dev item devid (\d+) total_bytes (\d+) bytes used (\d+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'DEV_ITEM_DATA'
        dic['devid'] = mo.group(1)
        dic['total_bytes'] = mo.group(2)
        dic['used_bytes'] = mo.group(3)

        return dic

    # linetype=CHUNK_ITEM_DATA
    # chunk length 8388608 owner 2 type 4 num_stripes 1
    mo = re.match(r'chunk length (\d+) owner (\d+) type (\d+) num_stripes (\d+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'CHUNK_ITEM_DATA'
        dic['length'] = mo.group(1)
        dic['owner'] = mo.group(2)
        dic['type'] = mo.group(3)
        dic['num_stripes'] = mo.group(4)

        return dic

    # linetype=CHUNK_ITEM_DATA_STRIPE
    # stripe 0 devid 1 offset 4194304
    mo = re.match(r'stripe (\d+) devid (\d+) offset (\d+)', line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'CHUNK_ITEM_DATA_STRIPE'
        dic['stripe'] = mo.group(1)
        dic['devid'] = mo.group(2)
        dic['physical_offset'] = mo.group(3)

        return dic



    ###############################
    # FS Tree

    # linetype=INODE_ITEM_DATA
    # inode generation 10 size 45 block group 0 mode 100644 links 1
    mo = re.match(r'inode generation (\d+) size (\d+) block group (\d+) mode (\d+) links (\d+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'INODE_ITEM_DATA'
        dic['generation'] = mo.group(1)
        dic['size'] = mo.group(2)
        dic['block_group'] = mo.group(3)
        dic['mode'] = mo.group(4)
        dic['links'] = mo.group(5)
        
        return dic

    # linetype=INODE_REF_DATA
    # inode ref index 5 namelen 13 name: sanity.tar.gz
    mo = re.match(r'inode ref index (\d+) namelen (\d+) name: (\S+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'INODE_REF_DATA'
        dic['index'] = mo.group(1)
        dic['namelen'] = mo.group(2)
        dic['name'] = mo.group(3)

        return dic

    # linetype=EXTENT_DATA_DATA_1
    # extent data disk byte 12582912 nr 147456
    mo = re.match(r'extent data disk byte (\d+) nr (\d+)', line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'EXTENT_DATA_DATA_1'
        dic['extent_disk_byte'] = mo.group(1)
        dic['extent_disk_number_of_bytes'] = mo.group(2)
        
        return dic

    # linetype=EXTENT_DATA_DATA_2
    # extent data offset 0 nr 147456 ram 147456
    mo = re.match(r'extent data offset (\d+) nr (\d+) ram (\d+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'EXTENT_DATA_DATA_2'
        dic['in_extent_offset'] = mo.group(1)
        dic['in_extent_number_of_bytes'] = mo.group(2)
        dic['ram_upper_bound'] = mo.group(3)

        return dic

    # linetype=EXTENT_DATA_DATA_3
    # extent compression 0
    mo = re.match(r'extent compression (\d+)', line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'EXTENT_DATA_DATA_3'
        dic['compression'] = mo.group(1)

        return dic

    # linetype=EXTENT_DATA_DATA_INLINE
    # inline extent data size 2517 ram 2517 compress 0
    mo = re.match(r'inline extent data size (\d+) ram (\d+) compress (\d+)',
            line)
    if mo:
        #print mo.group()
        #print mo.groups()
        dic = {}
        dic['linetype'] = 'EXTENT_DATA_DATA_INLINE'
        dic['data_size'] = mo.group(1)
        dic['ram_upper_bound'] = mo.group(2)
        dic['compression'] = mo.group(3)

        return dic

    #print "WARNING: an unrecognized line ->", orgin_line,
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


    #line = "key (0 BLOCK_GROUP_ITEM 4194304) block 29900800 (7300) gen 11"
    #line = "item 0 key (0 BLOCK_GROUP_ITEM 4194304) itemoff 3971 itemsize 24"
    #line = "leaf 30089216 items 9 free space 2349 generation 11 owner 1"
    #line = "node 29888512 level 1 items 3 free 118 generation 11 owner 2"
    #line = "chunk length 4194304 owner 2 type 2 num_stripes 1"
    #line = "stripe 0 devid 1 offset 4194304"
    #line = "inode generation 10 size 45 block group 0 mode 100644 links 1"
    #print line_parts(line)
    #return 
    
    f = open("./abtrfsdebugtree-output", 'r')

    lines = []
    for line in f:
        #print line_parts(line)
        lines.append(line)

    tparser = TreeParser(lines)
    tparser.parse()


#debug_main()

