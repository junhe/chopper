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

# data frame is a data structure behaves like a table.
# it is named after the same thing in R. 

class DataFrame:
    """
    This class is good for organize data in a
    row-column format. This is good for outputing as
    R input, pretty performance output.
    """
    def __init__ (self, header=None, table=None):
        """
        header has to be a list of strings, [str0, str1,..]
        table has to be a 2D list [ list.row0, list.row1, ... ]
        """
        if header == None:
            header = []
        if table == None:
            table = []
        self.header = header
        self.table = table
        self.colwidth = 15
    def toDic(self):
        d = {
              'header':self.header,
              'table': self.table 
              }
        return d

    def fromDic(self, dic ):
        self.header = dic['header']
        self.table = dic['table']

    def toStr(self, header=True, table=True):
        ret = ""
        if header:
            ret += self.headerStr()
        if table:
            ret += self.tableStr()
        return ret

    def headerStr(self):
        hd = self.items2line(self.header, linechange=True)
        return hd

    def tableStr(self):
        tblstr = ""
        for row in self.table:
            tblstr += self.items2line(row, linechange=True)
        return tblstr

    def widen(self, item):
        return str(item).ljust(self.colwidth)

    def items2line(self, items, linechange=True):
        itms = [self.widen(x) for x in items]
        line = " ".join(itms)
        if linechange:
            line += "\n"

        return line

    def addRowByList(self, rowlist):
        if len(rowlist) != len(self.header):
            print "row length does not match header length"
            exit(1)
        self.table.append(rowlist)

    def addRowByDict(self, rowdic):
        """
        to prevent from adding items in wrong order,
        row has to be added as dictionary.
        The keys of the dictionary has to be exactly
        the same as the header. otherwise, exception
        occurs
        """
        row = []
        try:
            for colname in self.header:
                row.append( rowdic[colname] )
            self.table.append( row )
        except:
            print "failed to add row:"
            print "rowdic:", sorted(rowdic.keys())
            print "header:", sorted(self.header)
    
    def delColumn(self, colname):
        if not colname in self.header:
            return False
        pos = self.header.index(colname)
        for row in self.table:
            del row[pos]
        del self.header[pos]
        return True

    def addColumn(self, key, value):
        """
        value will be the same for each row
        the number of rows of the table HAS to
        be kept the same before and after this function.
        only column should be added, not row
        DO NOT USE THIS TO INITIALIZE A DATA FRAME
        """
        self.header.append(key)
        if len(self.table) != 0:
            for row in self.table:
                row.append(value)
        else:
            self.table = [[value]]

    def addColumns(self, keylist, valuelist):
        """
        value will be the same for each row"
        the number of rows of the table HAS to
        be kept the same before and after this function.
        only column should be added, not row
        DO NOT USE THIS TO INITIALIZE A DATA FRAME
        """
        self.header.extend(keylist)
        if len(self.table) != 0:
            for row in self.table:
                row.extend(valuelist)

