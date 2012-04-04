#!/bin/bash

aircraft="OH-CTL"

TAG="START"
REPLACE="Multiline comment
Test
More test
"

cat test.html | perl -i -pe 'BEGIN{undef $/;} s:/\*'$TAG'\*/.*?/\*'$TAG'\*/:'"$REPLACE"':smg'
