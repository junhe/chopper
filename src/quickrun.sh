testname=$1
host=`hostname`
resultparent=/mnt/scratch-sda4/
resultdir=/mnt/scratch-sda4/results.$host
echo testname $testname 
echo host: $host 
echo result dir: $resultdir
if [ $# -ne 1 ]
then
    echo Usage: ./$0 testname
    exit
fi
#sleep 1

# mkdir the nfs dir first, otherwise there might be
# some problems
nfsdir=$testname
sudo rm -rf $nfsdir
mkdir $nfsdir


sudo python walkman-feedback.py ../conf/h0.conf 
sudo mv ./result-table.txt $testname-result-table.txt
exit 0
sleep 10
sudo python ../scripts/result-parser-faster.py $resultdir $host  

sudo rm -f $resultparent/${testname}.tar.gz 
sudo rm -rf $resultparent/${testname}
sudo mv $resultdir $resultparent/${testname}
echo Compressing z files
cd $resultparent 
sudo tar zcvf ${testname}.tar.gz ${testname}/z*
cd -

sync
sleep 2

echo copying $testname.tar.gz file to NFS dir $nfsdir
sudo rm -f ./$nfsdir/${testname}-$host.tar.gz
echo cp $resultparent/${testname}.tar.gz ./$nfsdir/${testname}-$host.tar.gz
cp $resultparent/${testname}.tar.gz ./$nfsdir/${testname}-$host.tar.gz
echo $?

echo copying $testname to NFS dir $nfsdir
sudo rm -rf ./$nfsdir/${testname}-$host
mkdir ./$nfsdir/${testname}-$host
echo cp $resultparent/${testname}/z* ./$nfsdir/${testname}-$host/
cp $resultparent/${testname}/z* ./$nfsdir/${testname}-$host/
echo $?

