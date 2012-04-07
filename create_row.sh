#!/bin/bash

# external
g_code_line=""

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
