if [ $# -ne 1 ] 
then
    echo Usage ME testname
    exit
fi
testname=$1
host=`hostname`
hostfile=$host.hostfile
echo $testname
echo $host

mpirun -hostfile $hostfile -np 3 bash -c "./quickrun.sh $testname &> /tmp/quickrun.log"
python ./merge_z_files.py $testname 

