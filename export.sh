#!/bin/bash
#
# Script for exporting files to gh-pages
#
export LC_CTYPE=C

export_dir=$PWD/gh

files="index.html template.html"

mkdir -p $export_dir

# Expand the gitvariables
git archive --format=tar HEAD $files | tar xf - -C $export_dir

echo Exported $files to $export_dir

for spec in specs/*.specs; do
    ./parse_template.sh $export_dir/template.html $spec $export_dir
done
