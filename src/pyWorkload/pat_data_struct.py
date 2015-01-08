# This module is an important part of generating workload

import pprint
import copy
import producer
import sys
import os

curdir = os.path.dirname( os.path.abspath( __file__ ) )
lib_path = os.path.join(curdir, '..') 
sys.path.append(lib_path)
import MWpyFS

# {
#   'class':   'ChunkBox',
#   'pre_ops': [],
#   'chunk':   {},
#   'post_ops':[]
# }

def get_empty_ChunkBox2():
    "the dictionary describes what we do to a chunk "
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

def file_treatment_to_df_foronefile(ftreatment):
    df = MWpyFS.dataframe.DataFrame()
    
    ftreatment['nchunks'] = len(ftreatment['chunks'])
    for k,v in ftreatment.items():
        if k in ['chunks']:
            valuestr = "|".join([ "("+str(c['offset'])+","+str(c['length'])+")" 
                                for c in v ])
        elif k.endswith('_bitmap'):
            valuestr = "".join( [ str(int(x)) for x in v ] )
        elif k in ['write_order', 'writer_cpu_map']:
            valuestr = "".join( [str(x) for x in v] )
        else:
            valuestr = str(v).replace(' ','')

        df.addColumn(key = k,
                     value = valuestr)
    return df


####################################################
####################################################
def treatment_to_df_morefactors(treatment):
    "Put treatment info to a datafarme, which will be written to output"
    df = None
    for ftreatment in treatment['files']:
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
    return df


