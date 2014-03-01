testname=$1
host=`hostname`
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
sudo rm -rf $resultdir \
    && sudo python walkman-feedback.py ../conf/h0.conf \
    && sleep 1 \
    && sudo python ../scripts/result-parser-faster.py $resultdir $host  
sudo rm ${testname}.tar.gz 
sudo rm -rf ${testname}
sudo mv $resultdir /mnt/scratch-sda4/${testname}
tar zcvf ${testname}.tar.gz /mnt/scratch-sda4/${testname}/z*

