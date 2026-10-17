#!/bin/sh

set -e

export_dir="$1"
if [ -z "$export_dir" ]; then
    echo "Usage: $0 <export directory>"
    exit 1
fi

mkdir -p "$export_dir"
git archive HEAD parse_template.py template.html.j2 README | tar -C "$export_dir" -x

for spec in specs/*.json; do
    python3 parse_template.py template.html.j2 "$spec" "$export_dir"
done
