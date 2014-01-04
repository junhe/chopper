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

            



























    
        

