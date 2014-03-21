import pprint
import copy
import producer
import sys
import os

#sys.path.append("MWpyFS")
lib_path = os.path.abspath('..')
sys.path.append(lib_path)
import MWpyFS

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
      'opseq': [], # [{'opname':'open','close'..'chunk','mkdir' 
                   #   'optype':'pre_op'or'post_op'or'chunk','dir',
                   #   'opvalue':TrueOrFalse, 'C' for CHUNK, 
                   #             dirpath for dir },
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

def get_empty_OpBitmap():
    """
{'nchunks': 3,
 'slotnames': ['(',
               'C',
               'F',
               ')',
               'S',
               ...]
 'values': [True,
            'C',
            False,
            False,
            False,
            False,
            ...]}
    """
    d = {
            '!class'    :'OpBitmap',
            'nchunks'   :None,
            'slotnames' :[],
            'values'    :[]
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

def ChunkSeq_to_workload2(chkseq, rootdir, tofile):
    assert chkseq['!class'] == 'ChunkSeq'

    prd = producer.Producer(
            rootdir = rootdir,
            tofile = tofile)

    for chkbox in chkseq['seq']:
        if chkbox['chunk'].has_key('filepath'):
            filepath= chkbox['chunk']['filepath']
        if chkbox['chunk'].has_key('writer_pid'):
            writer_pid = chkbox['chunk']['writer_pid']

        for op in chkbox['opseq']:
            if op['opname'] == 'open' and op['opvalue'] == True:
                prd.addUniOp2('open', pid=writer_pid, path=filepath)
            elif op['opname'] == 'chunk':
                prd.addReadOrWrite2('write', 
                           pid=writer_pid, 
                           path=filepath,
                           off=chkbox['chunk']['offset'], 
                           len=chkbox['chunk']['length'])
            elif op['opname'] == 'fsync' and op['opvalue'] == True:
                prd.addUniOp2('fsync', pid=writer_pid, path=filepath)
            elif op['opname'] == 'close' and op['opvalue'] == True:
                prd.addUniOp2('close', pid=writer_pid, path=filepath)
            elif op['opname'] == 'sync' and op['opvalue'] == True:
                prd.addOSOp('sync', pid=writer_pid)
            elif op['opname'] == 'sched_setaffinity' and \
                    op['opvalue'] != -1:
                prd.addSetaffinity(pid=writer_pid, cpuid=op['opvalue'])
            elif op['opname'] == 'mkdir':
                prd.addDirOp2(op='mkdir', pid=0, path=op['opvalue'])

    #prd.display()
    #exit(0)
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
                'sched_setaffinity':'A',
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
                     'A':'op', #CPU affinity
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

def ChunkBox_filter_used_ops( opbitmap ):
    """
    Given some 
    """
    used_ops = []
    for name, value in zip( opbitmap['slotnames'], 
                            opbitmap['values'] ):
        if value != False:
            used_ops.append( name )
    return used_ops

def ChunkBox_lists_to_strings( opbitmap ):
    # values
    values = opbitmap['values']
    for i,v in enumerate(values):
        if v == False:
            values[i] = 0
        elif v == True:
            values[i] = 1
    
    for k,v in opbitmap.items():
        s = [str(x) for x in v]
        s = ''.join(s)
        opbitmap[k] = s
    
    return opbitmap

def treatment_to_df(treatment):
    df = None
    for fileid,ftreatment in enumerate(treatment['files']):
        #assert fileid == ftreatment['fileid']
        tmpdf = file_treatment_to_df( ftreatment )
        if df == None:
            df = tmpdf
        else:
            df.table.extend( tmpdf.table )
    #print df.toStr()
    
    fset = treatment.keys()
    fset = set(fset)
    fset.remove('files')
    
    for k in fset:
        if k in ['filechunk_order']:
            vstr = ",".join([str(x) for x in treatment[k]])
        else:
            vstr = treatment[k]
        df.addColumn(key=k, value=vstr)
    df.colwidth = 20

    return df

def file_treatment_to_df (ftreatment):
    df = MWpyFS.dataframe.DataFrame()
    df.header = ['variable_name', 'variable_value']

    for k,v in ftreatment.items():
        if k in ['chunks']:
            valuestr = "|".join([ "("+str(c['offset'])+","+str(c['length'])+")"  for c in v ])
        elif k.endswith('_bitmap'):
            valuestr = "".join( [ str(int(x)) for x in v ] )
        elif k in ['write_order', 'writer_cpu_map']:
            valuestr = ",".join( [str(x) for x in v] )
        else:
            valuestr = str(v).replace(' ','')

        d = {
                'variable_name': k,
                'variable_value': valuestr}
        #pprint.pprint(d)
        df.addRowByDict(d)
    df.addColumn(key='fileid', value=ftreatment['fileid'])
    #print df.toStr()
    return df

def treatment_to_df_foronefile(treatment):
    df = None
    for fileid,ftreatment in enumerate(treatment['files']):
        assert fileid == 0
        tmpdf = file_treatment_to_df_foronefile( ftreatment )
        if df == None:
            df = tmpdf
        else:
            df.table.extend( tmpdf.table )
    #print df.toStr()
    
    fset = treatment.keys()
    fset = set(fset)
    fset.remove('files')
    
    for k in fset:
        if k in ['filechunk_order']:
            vstr = ",".join([str(x) for x in treatment[k]])
        else:
            vstr = treatment[k]
        df.addColumn(key=k, value=vstr)
    df.colwidth = 20

    #writer_cpu_map  open_bitmap     close_bitmap    writer_pid      write_order     filesize        sync_bitmap     parent_dirid    chunks          fsync_bitmap    fileid
    tokeep = ['open_bitmap', 'close_bitmap',
              'write_order',  'filesize',
              'sync_bitmap',  'fsync_bitmap',
              'nchunks',  'fileid']
    headers = copy.deepcopy(df.header)
    for colname in headers:
        if not colname in tokeep:
            df.delColumn(colname)
    return df

def file_treatment_to_df_foronefile(ftreatment):
    df = MWpyFS.dataframe.DataFrame()
    
    ftreatment['nchunks'] = len(ftreatment['chunks'])
    for k,v in ftreatment.items():
        if k in ['chunks']:
            valuestr = "|".join([ "("+str(c['offset'])+","+str(c['length'])+")"  for c in v ])
        elif k.endswith('_bitmap'):
            valuestr = "".join( [ str(int(x)) for x in v ] )
        elif k in ['write_order', 'writer_cpu_map']:
            valuestr = "".join( [str(x) for x in v] )
        else:
            valuestr = str(v).replace(' ','')

        #pprint.pprint(d)
        df.addColumn(key = k,
                     value = valuestr)
    #print df.toStr()
    return df


####################################################
####################################################
def treatment_to_df_morefactors(treatment):
    df = None
    for fileid,ftreatment in enumerate(treatment['files']):
        assert fileid == 0
        tmpdf = file_treatment_to_df_foronefile( ftreatment )
        if df == None:
            df = tmpdf
        else:
            df.table.extend( tmpdf.table )
    #print df.toStr()
    
    fset = treatment.keys()
    fset = set(fset)
    fset.remove('files')
    
    for k in fset:
        if k in ['filechunk_order']:
            vstr = ",".join([str(x) for x in treatment[k]])
        else:
            vstr = treatment[k]
        df.addColumn(key=k, value=vstr)
    df.colwidth = 20
    #print ['00']*100
    #writer_cpu_map  open_bitmap     close_bitmap    writer_pid      write_order     filesize        sync_bitmap     parent_dirid    chunks          fsync_bitmap    fileid
    #tokeep = [
              #'open_bitmap', 'close_bitmap',
              #'write_order',  'filesize',
              #'sync_bitmap',  'fsync_bitmap',
              #'nchunks',  'fileid',
              #]
    #headers = copy.deepcopy(df.header)
    #for colname in headers:
        #if not colname in tokeep:
            #df.delColumn(colname)
    return df





