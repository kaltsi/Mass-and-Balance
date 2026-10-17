#!/bin/sh

set -e

export_dir="${1}"
if [ -z "${export_dir}" ]; then
    echo "Usage: ${0} <export directory>"
    exit 1
fi

mkdir -p "${export_dir}"
git archive HEAD parse_template.py generate_index.py src README.md | tar -C "${export_dir}" -x

for spec in specs/*.json; do
    if [ "$(python3 -c 'import json,sys; print("true" if json.load(open(sys.argv[1])).get("publish", False) else "false")' "${spec}")" != "true" ]; then
        echo "Skipping ${spec} (publish is not true)"
        continue
    fi
    python3 parse_template.py src/template.html.j2 "${spec}" "${export_dir}"
done

python3 generate_index.py src/index.html.j2 specs "${export_dir}"
