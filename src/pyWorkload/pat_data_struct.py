import pprint
import producer

# {
#   'class':   'ChunkBox',
#   'pre_ops': [],
#   'chunk':   {},
#   'post_ops':[]
# }

# This structure is bad. very hard to use because
# pre_ops and post_ops are separate. Very hard to 
# iterate them
def get_empty_ChunkBox():
    d = {
      '!class':   'ChunkBox',
      'pre_ops': [], # [{'opname':NA, 'opvalue':TrueOrFalse},{},{}]
      'chunk':   {'offset':None,
                  'length':None,
                  'fileid':None},
      'post_ops':[],
      'attrs':   {}
    }
    return d

def get_empty_ChunkBox2():
    d = {
      '!class':   'ChunkBox2',
      'opseq': [], # [{'opname':'open','close'..'chunk' 
                   #   'optype':'pre_op'or'post_op'or'chunk',
                   #   'opvalue':TrueOrFalse, 'C' for CHUNK},
                   #  {},{}]
      'chunk':   {'offset':None,
                  'length':None,
                  'fileid':None},
      'attrs':   {}
    }
    return d


def get_empty_ChunkSeq():
    d = {
      '!class':   'ChunkSeq',
      'seq'  :   []   # this is a list of ChunkBox, or ChunkBox2
    }
    return d


def chunkop_to_chunkseq ( chunkop ):
    """
    input:
      {'chunks': ((0, 6), (6, 6)),
      'wrappers': (True, False, False, False, False, False, True, True)}
    output:
      ChunkSeq
    """
    ops = chunkop['wrappers']
    op_base = 0
    OPS_PER_CHUNK = 4
    cseq = get_empty_ChunkSeq() 
    for chk in chunkop['chunks']:
        cbox = get_empty_ChunkBox2()
        cbox['chunk']['offset'] = chk[0]
        cbox['chunk']['length'] = chk[1]

        for i in range(OPS_PER_CHUNK):
            op = ops[op_base + i]
            if i == 0:
                name = 'open'
                d = { 'opname'  :name,
                      'optype'  :'op',
                      'opvalue' :op }
                cbox['opseq'].append(d)

                # also put the chunk marker here
                name = 'chunk'
                d = { 'opname'  :name,
                      'optype'  :'chunk',
                      'opvalue' :'C' }
                cbox['opseq'].append(d)

            elif i == 1:
                name = 'fsync'
                d = { 'opname'  :name,
                      'optype'  :'op',
                      'opvalue' :op }
                cbox['opseq'].append(d)
            elif i == 2:
                name = 'close'
                d = { 'opname'  :name,
                      'optype'  :'op',
                      'opvalue' :op }
                cbox['opseq'].append(d)
            elif i == 3:
                name = 'sync'
                d = { 'opname'  :name,
                      'optype'  :'op',
                      'opvalue' :op }
                cbox['opseq'].append(d)
            else:
                assert False, 'cannot translate'
        op_base += OPS_PER_CHUNK
        cseq['seq'].append(cbox)
    return cseq

def ChunkSeq_to_workload(chkseq, rootdir, tofile):
    assert chkseq['!class'] == 'ChunkSeq'

    prd = producer.Producer(
            rootdir = rootdir,
            tofile = tofile)
    prd.addDirOp('mkdir', pid=0, dirid=0)

    for chkbox in chkseq['seq']:
        fileid = chkbox['chunk']['fileid']

        for op in chkbox['opseq']:
            if op['opname'] == 'open':
                prd.addUniOp('open', pid=0, dirid=0, fileid=fileid)
            elif op['opname'] == 'chunk':
                prd.addReadOrWrite('write', pid=0, dirid=0,
                           fileid=fileid, 
                           off=chkbox['chunk']['offset'], 
                           len=chkbox['chunk']['length'])
            elif op['opname'] == 'fsync':
                prd.addUniOp('fsync', pid=0, dirid=0, fileid=fileid)
            elif op['opname'] == 'close':
                prd.addUniOp('close', pid=0, dirid=0, fileid=fileid)
            elif op['opname'] == 'sync':
                prd.addOSOp('sync', pid=0)

    #prd.display()
    prd.saveWorkloadToFile()
    return True

def ChunkSeq_to_strings(chkseq):
    """
    It returns:
        slotnames: it is operation name and chunk name for operation or chunk
        values: it is a values to indicate if an operation has been conducted
                or not. 
        fileids: it indicates the fileid corresponding to
                each slot
        types:  what type it is. 'O':for operations, 'C':for chunks
    slots and fileids have the same length
    """
    assert chkseq['!class'] == 'ChunkSeq'

    offsets = set()
    for chkbox in chkseq['seq']:
        offsets.add( chkbox['chunk']['offset'] )
    offsets = list(offsets)
    offsets.sort()
    off_dict = {}
    l = len(offsets)
    for i in range(l):
        off_dict[ offsets[i] ] = i

    ret = None
    for chkbox in chkseq['seq']:
        chkbox_dic = ChunkBox_to_lists( chkbox )
        chkbox_dic['used_ops'] = ChunkBox_filter_used_ops( chkbox_dic ) 
        chkbox_dic = ChunkBox_lists_to_strings( chkbox_dic )
        if ret == None:
            ret = chkbox_dic
        else:
            for k,v in chkbox_dic.items():
                ret[k] += v
    return ret

#############################################
symbol_dict = {
                'open' :'(',
                'chunk':'C',
                'fsync':'F',
                'close':')',
                'sync' :'S'
               }

name_dict = {}
for k,v in symbol_dict.items():
    name_dict[v] = k

symbol2type_dict = {
                     '(':'op',
                     'C':'chunk',
                     'F':'op',
                     ')':'op',
                     'S':'op'
                   }

#############################################

def name2symbol(name):
    return symbol_dict[name]

def symbol2name(symbol):
    return name_dict[symbol]

def symbol2type(symbol):
    return symbol2type_dict[symbol]

def ChunkBox_to_lists(chkbox):
    slotnames = []
    values = []
    fileids = []
    types = []

    typedic = {
                'op':'O',
                'chunk':'C'
              }
    
    # pre operations
    for op in chkbox['opseq']:
        slotnames.append( name2symbol(op['opname']) )
        values.append( op['opvalue'] )
        fileids.append( chkbox['chunk']['fileid'] )
        types.append(typedic[op['optype']])

    ret = {
            'slotnames':slotnames,
            'values': values,
            'fileids': fileids,
            'types': types
          }

    return ret

def ChunkBox_filter_used_ops( chkbox_dic ):
    used_ops = []
    for name, value in zip( chkbox_dic['slotnames'], 
                            chkbox_dic['values'] ):
        if value != False:
            used_ops.append( name )
    return used_ops

def ChunkBox_lists_to_strings( chkbox_dic ):
    # values
    values = chkbox_dic['values']
    for i,v in enumerate(values):
        if v == False:
            values[i] = 0
        elif v == True:
            values[i] = 1
    
    for k,v in chkbox_dic.items():
        s = [str(x) for x in v]
        s = ''.join(s)
        chkbox_dic[k] = s
    
    return chkbox_dic



