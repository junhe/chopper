import subprocess,os,sys
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

zdir = testname+"_z"
if not os.path.exists( zdir ):
    os.makedirs( zdir )

dirs = glob.glob( testname+"-*" )

#for suf in sufixs:
    #subprocess.call( "cat "+testname+"-*/"+suf+" >"+zdir+"/"+suf, shell=True)
    
for suf in sufixs:
    ofpath = os.path.join( zdir, suf )
    print ofpath
    of = open( ofpath, 'w' )
    headprinted = False
    for dir in dirs:
        if dir.endswith('tar.gz'):
            continue
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
subprocess.call( ['tar', '-zcvf', zdir+'.tar.gz', zdir] )

