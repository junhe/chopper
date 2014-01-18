import subprocess,os,sys
import fnmatch
import glob

if len(sys.argv) != 2:
    print "usage: me testname"
    exit(1)

testname = sys.argv[1]

sufixs = [
    '_chunks',
    '_extlist',
    '_extlistraw',
    '_extstats',
    '_extstatssum',
    '_freeblocks',
    '_freefrag_hist',
    '_freefrag_sum',
    '_freeinodes',
    '_pathinodemap',
    '_walkman_config'
    ]
sufixs = [ 'zparsed.'+x for x in sufixs ]

nfsdir = testname
zdir = os.path.join( nfsdir, testname+"_z" )
if os.path.exists( zdir ):
    os.rmdir( zdir )
os.makedirs( zdir )

#dirs = glob.glob( testname+"-*" )
for dirpath, dirnames, filenames in os.walk( nfsdir ):
    dirs = fnmatch.filter( dirnames, testname+"-*" )
    break

newdirs = []
for dir in dirs:
    if not dir.endswith( '.tar.gz' ):
        newdirs.append( os.path.join( nfsdir, dir ) )
dirs = newdirs
print dirs


#for suf in sufixs:
    #subprocess.call( "cat "+testname+"-*/"+suf+" >"+zdir+"/"+suf, shell=True)
    
for suf in sufixs:
    ofpath = os.path.join( zdir, suf )
    print ofpath
    of = open( ofpath, 'w' )
    headprinted = False
    for dir in dirs:
        zfpath = os.path.join( dir, suf )
        print zfpath
        with open(zfpath, 'r') as zf:
            for line in zf:
                if "headermarker_" in line.lower():
                    if headprinted == False:
                        of.write( line )
                        headprinted = True
                else:
                    of.write( line )
    of.close()
print "tar ing ......"
ztar = zdir+'.tar.gz'
if os.path.exists( ztar ):
    os.remove( ztar )
subprocess.call( ['tar', '-zcvf', '-C', nfsdir, ztar, zdir] )

