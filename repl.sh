#!/bin/bash
#
# perl -i -pe 'BEGIN{undef $/;} s:/\*'$TAG'\*/.*?/\*'$TAG'\*/:'"$REPLACE"':smg'
#

export LC_CTYPE=C

if [ $# -ne 2 ]; then
    echo "Usage $0 template.html aircraft.specs";
    exit 1;
fi

if [ ! -f $1 ]; then
    echo "template file: $1 - not found.";
    exit 1;
fi

if [ ! -f $2 ]; then
    echo "template file: $2 - not found.";
    exit 1;

fi

INPUT_FILE="$2"
OUTPUT_FILE="$INPUT_FILE.html"
TEMPLATE_FILE="$1"

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
    perl -i -pe 'BEGIN{undef $/;} s§/\*'$a'\*/.*?/\*\*/§'"$b"'§smg' $OUTPUT_FILE
}

WORK_FILE=$INPUT_FILE.wrk
cp $TEMPLATE_FILE $OUTPUT_FILE
cp $INPUT_FILE $WORK_FILE

code_output=""
variable_names=""
saveables_group=""
saveable_group_values=""

while read i; do
    if [[ "${i:0:1}" != "#" ]] && [[ "${i:0:1}" != " " ]] && [[ "${i:0:1}" != '' ]]; then
	name=`echo "$i" | cut -f 1 -d =`
	value=`echo "$i" | cut -f 2- -d =`
	code_output=""

	if [ z"$name" == z"LOAD_POINT" ]; then
	    create_lp $value

	    variable_names="$variable_names$g_name\n"
	    code_output="$code_output"$(echo $g_code_line | sed -e "s/#/ /g")"\n"

	    if [ "${value:0:5}" == "LP_I_" ] ||[ "${value:0:5}" == "LP_F_" ]; then
		saveables_group="$saveables_group$g_saveable_group\n"
		saveable_group_values="$saveable_group_values$g_saveable_group_value\n"
	    fi
	    create_row $value
	    code_output="$code_output$g_code_line\n"

	    simple_replace "$g_code_line_name" "$code_output"
	else
	    simple_replace "$name" "$value"
	fi

   fi
done < $WORK_FILE

for i in `echo -e $variable_names | sed -e "s/\\n/ /g"`; do
    simple_replace "$i" "$i"
done

simple_replace "SAVEABLES" "$saveables_group"
simple_replace "SAVEABLE_VALUES" "$saveable_group_values"

exit 0


