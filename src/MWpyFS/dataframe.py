

class DataFrame:
    """
    This class is good for organize data in a
    row-column format. This is good for outputing as
    R input, pretty performance output.
    """
    def __init__ (self, header, table=[]):
        """
        header has to be a list of strings, [str0, str1,..]
        table has to be a 2D list [ list.row0, list.row1, ... ]
        """
        self.header = header
        self.table = table

    def toStr(self):
        return self.headerStr() + self.tableStr() 

    def headerStr(self):
        hd = self.items2line(self.header, linechange=True)
        return hd

    def tableStr(self):
        tblstr = ""
        for row in self.table:
            tblstr += self.items2line(row, linechange=True)
        return tblstr

    def widen(self, item, colwidth=20):
        return str(item).ljust(colwidth)

    def items2line(self, items, linechange=True):
        itms = [self.widen(x) for x in items]
        line = " ".join(itms)
        if linechange:
            line += "\n"

        return line

    def addRow(self, rowdic):
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
            print "rowdic:", rowdic

    def addColumn(self, key, value):
        "value will be the same for each row"
        self.header.append(str(key))
        for row in self.table:
            row.append(value)

#df = DataFrame(['h1', 'h2'], [[1,2],[3,4]])
#df = DataFrame(['h1', 'h2'])

#print df.toStr()

#df.addRow( {'h1':1, 'h2':3} )
#df.addRow( {'h1':1, 'h2':3} )
#df.addRow( {'h1':1, 'h2':3} )
#df.addRow( {'h1':1, 'h2':3} )

#print df.toStr()

#df.addColumn("newcol", 1000)

#print df.toStr()
