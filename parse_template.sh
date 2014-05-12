#!/bin/bash
#
# template-file aircraft.specs [output_dir]
#

debug=0

export LC_CTYPE=C


if [ $# -lt 2 ] ; then
    echo "Usage $0 template aircraft.specs [output_dir]";
    exit 1;
fi

if [ ! -f $1 ]; then
    echo "template file: $1 - not found.";
    exit 1;
fi

if [ ! -f $2 ]; then
    echo "specs file: $2 - not found.";
    exit 1;

fi

TEMPLATE_FILE="$1"
SPECS_FILE_PATH="$2"
OUTPUT_DIR=""

if [ ! -z $3 ]; then
    OUTPUT_DIR=$3
fi

SPEC_BASE=$(basename $SPECS_FILE_PATH)
SPEC_FILE=${SPEC_BASE%.*}
SPEC_EXT=${SPEC_BASE##*.}

if [ z"$SPEC_EXT" != "zspecs" ]; then
    echo "Spec file must have .specs extension ($SPEC_EXT)"
    exit 1
fi

if [ ! -z "$OUTPUT_DIR" ]; then
    OUTPUT_FILE="$OUTPUT_DIR/$SPEC_FILE.html"
else
    OUTPUT_FILE="$SPEC_FILE.html"
fi

echo "Handling file: $SPECS_FILE_PATH"

# External variables
g_code_line=""
g_code_line_name=""
g_saveable=""
g_saveable_group=""
g_saveable_group_value=""
g_name=""
g_extra_mass=""

# These are the known load points. Anything else is considered user-added.
declare -a known=("BASIC_WEIGHT" "FRONT_SEAT" "FUEL" "BAGGAGE" "TAXI_FUEL" "TOW" "LNDW" "ENDURANCE" "FUEL_FLOW" "FLIGHT_TIME")

# Checks if a string is in the array
in_array() {
    local hay needle=$1
    shift
    for hay; do
        [[ $hay == $needle ]] && return 0
    done
    return 1
}

# name     translation       unit def min max mom   [step]
#
# LP_N_BEW "English" "Suomi" "kg" 0   0   -1  1.923  0.1
#
# LP_I_xxx = interactive load point, declares a saveable variable
# LP_F_xxx = interactive fuel flow row
# LP_C_xxx = interactive checkbox row
# LP_R_xxx = non-interactive load point with result and value cells reversed
# LP_N_xxx = non-interactive load point

function create_lp()
{
    if [ $# -lt 8 ]; then
	echo "$FUNCNAME called with $*"
	exit 1
    fi

    local lpname=$1
    local lang_en=$2
    local lang_fi=$3
    local unit=$4
    local unit_def=$5
    local unit_min=$6
    local unit_max=$7
    local mom=$8
    local steps=""

    if [ $# -eq 9 ]; then
	steps=$9
    fi

    local save_item=""
    if [ "${lpname:0:5}" == "LP_I_" ] || [ "${lpname:0:5}" == "LP_F_" ] || [ "${lpname:0:5}" == "LP_C_" ]; then
	save_item=".s"
    fi

    # Whatever comes after the first 5 chars
    local the_name="${lpname:5}"

    g_code_line=""
    g_code_line_name="$lpname"

    g_code_line="${the_name}=new l_point(\"${the_name}\","
    g_code_line="$g_code_line [$lang_en, $lang_fi],"
    g_code_line="$g_code_line ${unit},"

    # For non-interactive elements put the default value in place.
    # For interactive values put the saveable name in place.
    if [ "${lpname:0:5}" == "LP_N_" ] || [ "${lpname:0:5}" == "LP_R_" ]; then
	g_code_line="$g_code_line ${unit_def},"
    else
	g_code_line="$g_code_line g_defs${save_item}.${the_name},"
    fi

    g_code_line="$g_code_line ${unit_min}, ${unit_max}, ${mom}"

    if [ ! -z ${steps} ]; then
	g_code_line="$g_code_line, $steps"
    fi

    g_code_line="$g_code_line);"

    if [ "${lpname:0:5}" == "LP_F_" ]; then
	# fuel flow row
	g_code_line="$g_code_line ${the_name}.fuel_flow = true;"
    fi

    g_name="$the_name"
    g_saveable_group="$the_name : ${unit_def},"
    g_saveable_group_value="$the_name.vu.get_si(),"

    # check if this was an unknown load point
    g_extra_mass=""
    in_array "$the_name" "${known[@]}" || g_extra_mass=$the_name
}


# This expects the input to be of the following format
#
# LP_I_xxx = interactive load point, declares a saveable variable
# LP_F_xxx = interactive fuel flow row
# LP_C_xxx = interactive check box row
# LP_R_xxx = non-interactive load point with result and value cells reversed
# LP_N_xxx = non-interactive load point

function create_row()
{
    if [ $# -lt 1 ]; then
	echo "$FUNCNAME called with $*"
	exit 1
    fi

    local lpname=$1
    local reverse=""
    local non=""
    local cbox=""
    local the_name="${lpname:5}"

    if [ "${1:0:5}" == "LP_R_" ]; then
	reverse=", \"reverse\""
    fi

    if [[ "${1:0:5}" == "LP_N_" ]] || [[ "${1:0:5}" == "LP_R_" ]]; then
	non="non_"
    fi

    if [[ "${1:0:5}" == "LP_C_" ]]; then
	cbox="cbox_"
    fi

    g_code_line="rows.push(new ${non}${cbox}interactive_row(${the_name}${reverse}));"
}

function simple_replace()
{
    if [ $# -ne 2 ]; then
	echo $FUNCNAME needs 2 parameters
	exit 1
    fi

    local a=$1
    local b=$2

    if [[ -z $a ]]; then
	echo $FUNCNAME got zero length string
	exit 1
    fi

    if [ $debug -ne 0 ]; then
	echo "Replacing: /$a/ with /$b/"
    fi
    perl -i -pe 'BEGIN{undef $/;} s§/\*'$a'\*/.*?/\*\*/§'"$b"'§smg' $OUTPUT_FILE
}

# the modifications will be done on the output file
cp $TEMPLATE_FILE $OUTPUT_FILE

code_output=""
variable_names=""
saveables_group=""
saveable_group_values=""
extra_masses=""

while read i; do
    if [[ "${i:0:1}" != "#" ]] && [[ "${i:0:1}" != " " ]] && [[ "${i:0:1}" != '' ]]; then

	name=$(cut -f 1 -d = <<< "$i")
	value=$(cut -f 2- -d = <<< "$i")

	if [ z"$name" == z"LOAD_POINT" ]; then
	    create_lp $value

	    variable_names="$variable_names$g_name\n"
	    code_output="$code_output"$(echo $g_code_line | sed -e "s/#/ /g")"\n"

	    if [ "${value:0:5}" == "LP_I_" ] || [ "${value:0:5}" == "LP_F_" ] || [ "${value:0:5}" == "LP_C_" ]; then
		saveables_group="$saveables_group$g_saveable_group\n"
		saveable_group_values="$saveable_group_values$g_saveable_group_value\n"
	    fi
	    create_row $value
	    code_output="$code_output$g_code_line\n"
	    if [ ! -z $g_extra_mass ]; then
		extra_masses="$extra_masses $g_extra_mass"
	    fi
	else
	    simple_replace "$name" "$value"
	fi

   fi
done < $SPECS_FILE_PATH

simple_replace "REPLACE_TABLE_ROWS" "$code_output"

for i in $(echo -e $variable_names | sed -e "s/\\n/ /g"); do
    simple_replace "$i" "$i"
done

simple_replace "SAVEABLES" "$saveables_group"
simple_replace "SAVEABLE_VALUES" "$saveable_group_values"

extra_calc_mass=""
extra_mass_calc_moments=""
extra_mass_moments=""
extra_debug_lines=""

create_extra_mass()
{
    for i in $*; do
	extra_calc_mass="$extra_calc_mass$i,\n"
	extra_mass_calc_moments="${extra_mass_calc_moments}calc_moment($i);\n"
	extra_mass_moments="$extra_mass_moments$i.moment +\n"
	extra_debug_lines="${extra_debug_lines}debug.textContent += (\" \" + $i.moment.toFixed(3));\n"
    done
}

if [ "z" != z"$extra_masses" ]; then 
    create_extra_mass "$extra_masses"
else
    # create empty replace for the extra equipment
    create_extra_mass "  "
fi

simple_replace "EXTRA_CALC_MASS" "$extra_calc_mass"
simple_replace "EXTRA_MASS_CALC_MOMENTS" "$extra_mass_calc_moments"
simple_replace "EXTRA_MASS_MOMENTS" "$extra_mass_moments"
simple_replace "EXTRA_DEBUG" "$extra_debug_lines"

# finally hide the debug button from the published sheets
simple_replace "HIDE_DEBUG" " "

echo "Output file is: $OUTPUT_FILE"

exit 0
