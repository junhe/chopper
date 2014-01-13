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

sudo rm -rf $resultdir
sudo python walkman-feedback.py ../conf/h0.conf 
sleep 1 
sudo python ../scripts/result-parser-faster.py $resultdir $host  

sudo rm -f $resultparent/${testname}.tar.gz 
sudo rm -rf $resultparent/${testname}
sudo mv $resultdir $resultparent/${testname}
echo Compressing z files
cd $resultparent 
sudo tar zcvf ${testname}.tar.gz ${testname}/z*
cd -

echo copying $testname.tar.gz file to NFS
sudo rm -f ./${testname}-$host.tar.gz
cp $resultparent/${testname}.tar.gz ./${testname}-$host.tar.gz

echo copying $testname to NFS
sudo rm -rf ./${testname}-$host
cp -r $resultparent/${testname} ./${testname}-$host

