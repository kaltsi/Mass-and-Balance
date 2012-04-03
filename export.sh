#!/bin/bash
#
# Script for exporting files to gh-pages
#

export_dir=$PWD/gh

sources="index,oh-cox,oh-ctl,oh-esr,oh-pyw,oh-srh"

files=$(eval ls {$sources}.html)

mkdir -p $export_dir

git archive --format=tar HEAD $files | (cd $export_dir && tar xf -)
