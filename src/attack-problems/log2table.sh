#===============================================================================
#
#          FILE: log2table.sh
# 
#         USAGE: ./log2table.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: YOUR NAME (), 
#  ORGANIZATION: 
#       CREATED: 01/15/2015 02:21:58 PM EST
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
logfile=$1
grep HEADERROWMARKER $logfile |head -n2|tail -n1 > $logfile.table
grep DATAROWMARKER $logfile >> $logfile.table 

