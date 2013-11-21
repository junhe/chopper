testname=$1
host=`hostname`
resultdir=results.$host
echo testname $testname 
echo host: $host 
echo result dir: $resultdir
if [ $# -ne 1 ]
then
    echo Usage: ./$0 testname
    exit
fi
sleep 3
sudo rm -rf $resultdir \
    && sudo python walkman-troops.py ../conf/h0.conf \
    && sleep 1 \
    && sudo python ../scripts/result-parser-faster.py $resultdir $host  
sudo rm ${testname}.tar.gz 
sudo rm -rf ${testname}
sudo mv $resultdir ${testname}
tar zcvf ${testname}.tar.gz ${testname}/z*

