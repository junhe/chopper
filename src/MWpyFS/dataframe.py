

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

#df = DataFrame(['h1', 'h2'], [[1,2],[3,4]])
#df = DataFrame(['h1', 'h2'])

#print df.toStr()

#df.addRow( {'h1':1, 'h2':3} )
#df.addRow( {'h1':1, 'h2':3} )
#df.addRow( {'h1':1, 'h2':3} )
#df.addRow( {'h1':1, 'h2':3} )

#print df.toStr()

#df.addColumn("newcol", 1000)

#df.addRowByList([3,4,5])
#print df.toStr()
