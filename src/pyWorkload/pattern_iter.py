# Chopper is a diagnostic tool that explores file systems for unexpected
# behaviors. For more details, see paper Reducing File System Tail 
# Latencies With Chopper (http://research.cs.wisc.edu/adsl/Publications/).
#
# Please send bug reports and questions to jhe@cs.wisc.edu.
#
# Written by Jun He at University of Wisconsin-Madison
# Copyright (C) 2015  Jun He (jhe@cs.wisc.edu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import itertools
import producer
import re
import random
import pprint
import subprocess
import pat_data_struct
import copy

def assign_operations_to_chunkseq( chunkseq, opbitmap ):
    """
    chunkseq and opbitmap has the same number of chunks.
    WARNING: chunkseq's operations should be empty! otherwise
             they will be overwritten.
    """
    nchunks = len( chunkseq['seq'] )
    assert nchunks == opbitmap['nchunks']

    # clean all the operations 
    for chkbox in chunkseq['seq']:
        chkbox['opseq'] = []
    
    seq = chunkseq['seq']
    nslots_per_chunk = len(opbitmap['slotnames']) / nchunks
    cnt = 0
    for symbol, value in zip( opbitmap['slotnames'],
                            opbitmap['values'] ):
        chunkid = int(cnt / nslots_per_chunk)
        cbox = seq[chunkid]  
        op = {
                'opname': pat_data_struct.symbol2name(symbol),
                'optype': pat_data_struct.symbol2type(symbol),
                'opvalue': value
             }      
        cbox['opseq'].append( op )
        cnt += 1
    return chunkseq



