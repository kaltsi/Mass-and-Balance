#!/bin/bash
#
# perl -i -pe 'BEGIN{undef $/;} s:/\*'$TAG'\*/.*?/\*'$TAG'\*/:'"$REPLACE"':smg'
#

export LC_CTYPE=C

if [ $# -ne 1 ]; then
    echo "Need aircraft input file";
    exit 1;
fi

if [ ! -f $1 ]; then
    echo "Input file: $1 - not found.";
    exit 1;

fi

INPUT_FILE="$1"

echo "Handling file: $INPUT_FILE"

# load point creation
source ./create_lp.sh

# row creation
source ./create_row.sh


function simple_replace()
{
    if [ $# -ne 2 ]; then
	echo $FUNCNAME needs 2 parameters
	exit 1
    fi

    local a=$1
    local b=$2

    echo "Replacing: /$a/ with /$b/"
    #cat $INPUT_FILE | perl -i -pe 'BEGIN{undef $/;} s:/\*'$a'\*/.*?/\*\*/:'"$b"':smg'
}

WORK_FILE=$INPUT_FILE.wrk

cp $INPUT_FILE $WORK_FILE

code_output=""
saveables=""

while read i; do
    if [[ "${i:0:1}" != "#" ]] && [[ "${i:0:1}" != " " ]] && [[ "${i:0:1}" != '' ]]; then
	x=`echo "$i" | cut -f 1 -d =`
	y=`echo "$i" | cut -f 2- -d =`


	if [ z"$x" == z"LOAD_POINT" ]; then
	    create_lp $y
	    code_output="$code_output"$(echo $g_code_line | sed -e "s/#/ /g")"\n"
	    if [ "${y:0:5}" == "LP_I_" ] ||[ "${y:0:5}" == "LP_F_" ]; then
		saveables="$saveables$g_saveable\n"
	    fi
	    create_row $y
	    code_output="$code_output$g_code_line\n"
	else
	    simple_replace "$x" "$y"
	fi

   fi
done < $WORK_FILE

echo -e $code_output
echo -e $saveables

exit 0


