import pprint
import producer

# {
#   'class':   'ChunkBox',
#   'pre_ops': [],
#   'chunk':   {},
#   'post_ops':[]
# }

def get_empty_ChunkBox():
    d = {
      '!class':   'ChunkBox',
      'pre_ops': [], # [{'opname':NA, 'opvalue':TrueOrFalse},{},{}]
      'chunk':   {'offset':None,
                  'length':None},
      'post_ops':[],
      'attrs':   {}
    }
    return d

def get_empty_ChunkSeq():
    d = {
      '!class':   'ChunkSeq',
      'seq'  :   []   # this is a list of ChunkBox
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
        cbox = get_empty_ChunkBox()
        cbox['chunk']['offset'] = chk[0]
        cbox['chunk']['length'] = chk[1]

        for i in range(OPS_PER_CHUNK):
            op = ops[op_base + i]
            if i == 0:
                name = 'open'
                d = { 'opname'  :name,
                      'opvalue' :op }
                cbox['pre_ops'].append(d)
            elif i == 1:
                name = 'fsync'
                d = { 'opname'  :name,
                      'opvalue' :op }
                cbox['post_ops'].append(d)
            elif i == 2:
                name = 'close'
                d = { 'opname'  :name,
                      'opvalue' :op }
                cbox['post_ops'].append(d)
            elif i == 3:
                name = 'sync'
                d = { 'opname'  :name,
                      'opvalue' :op }
                cbox['post_ops'].append(d)
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
        fileid = chkbox['attrs']['fileid']

        # pre operations
        for op in chkbox['pre_ops']:
            if op['opname'] == 'open':
                prd.addUniOp('open', pid=0, dirid=0, fileid=fileid)
            else:
                print 'Unrecognized operation'
                exit(1)

        # write the chunk
        prd.addReadOrWrite('write', pid=0, dirid=0,
                           fileid=fileid, 
                           off=chkbox['chunk']['offset'], 
                           len=chkbox['chunk']['length'])
        
        # post operations
        for op in chkbox['post_ops']:
            if op['opname'] == 'fsync':
                prd.addUniOp('fsync', pid=0, dirid=0, fileid=fileid)
            elif op['opname'] == 'close':
                prd.addUniOp('close', pid=0, dirid=0, fileid=fileid)
            elif op['opname'] == 'sync':
                prd.addOSOp('sync', pid=0)

    prd.display()
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

    symbol_dict = {
                    'open' :'(',
                    'chunk':'C',
                    'fsync':'F',
                    'close':')',
                    'sync' :'S'
                   }
    offsets = set()
    for chkbox in chkseq['seq']:
        offsets.add( chkbox['chunk']['offset'] )
    offsets = list(offsets)
    offsets.sort()
    off_dict = {}
    l = len(offsets)
    for i in range(l):
        off_dict[ offsets[i] ] = i

    slotnames = []
    values = []
    fileids = []
    types = []
    for chkbox in chkseq['seq']:
        # pre operations
        for op in chkbox['pre_ops']:
            slotnames.append( symbol_dict[op['opname']] )
            values.append( op['opvalue'] )
            fileids.append( chkbox['attrs']['fileid'] )
            types.append('O')

        # chunk info
        slotnames.append( symbol_dict['chunk'] )
        values.append( off_dict[ chkbox['chunk']['offset'] ] )
        fileids.append( chkbox['attrs']['fileid'] )
        types.append('C')

        # post operations
        for op in chkbox['post_ops']:
            slotnames.append( symbol_dict[op['opname']] )
            values.append( op['opvalue'] )
            fileids.append( chkbox['attrs']['fileid'] )
            types.append('O')
    
    # slotnames
    slotnames = ''.join(slotnames)
    fileids = [str(x) for x in fileids]
    fileids = ''.join(fileids)
    types = ''.join(types)

    # values
    for i,v in enumerate(values):
        if v == False:
            values[i] = 0
        elif v == True:
            values[i] = 1
    values = [str(x) for x in values]
    values = ''.join(values)
    
    ret = {
            'slotnames':slotnames,
            'values': values,
            'fileids': fileids,
            'types': types
          }

    return ret


