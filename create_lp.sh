#!/bin/bash

# External variables
g_code_line=""
g_saveable=""

# name     translation       unit min max mom   [step]
#
# LP_N_BEW "English" "Suomi" "kg" 0   -1  1.923  0.1
#
# LP_I_xxx = interactive load point, declares a saveable variable
# LP_F_xxx = interactive fuel flow row
# LP_R_xxx = non-interactive load point with result and value cells reversed
# LP_N_xxx = non-interactive load point

function create_lp()
{
    if [ $# -lt 7 ]; then
	echo "$FUNCNAME called with $*"
	exit 1
    fi

    local lpname=$1
    local lang_en=$2
    local lang_fi=$3
    local unit=$4
    local unit_min=$5
    local unit_max=$6
    local mom=$7
    local steps=""

    if [ $# -eq 8 ]; then
	steps=$8
    fi

    local save_item=""
    if [ "${lpname:0:5}" == "LP_I_" ]; then
	save_item=".s"
    fi

    # Whatever comes after the first 5 chars
    local save_name="${lpname:5}"

    g_code_line=""

    g_code_line="${lpname}=new l_point(\"${lpname}\","
    g_code_line="$g_code_line [$lang_en, $lang_fi],"
    g_code_line="$g_code_line ${unit},"

    g_code_line="$g_code_line g_defs${save_item}.${save_name}, ${unit_min}, ${unit_max}, ${mom}"

    if [ ! -z ${steps} ]; then
	g_code_line="$g_code_line, $steps"
    fi

    g_code_line="$g_code_line);"

    if [ "${lpname:0:5}" == "LP_F_" ]; then
	# fuel flow row
	g_code_line="$g_code_line ${lpname}.fuel_flow = true;"
    fi

    g_saveable="$save_name"
}

#create_lp LP_N_BEW "English" "Suomi" "kg" 0   -1  1.923  0.1
#echo $code_line

