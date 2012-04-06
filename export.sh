#!/bin/bash
#
# Script for exporting files to gh-pages
#
export LC_CTYPE=C

export_dir=$PWD/gh

sources="index,template"

files=$(eval ls {$sources}.html)

mkdir -p $export_dir

# Expand the gitvariables
git archive --format=tar HEAD $files | (cd $export_dir && tar xf -)

echo Exported $files to $export_dir

for spec in $(ls specs/*.specs); do
    ./parse_template.sh ./gh/template.html $spec ./gh
done

