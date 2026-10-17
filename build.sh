#!/bin/sh

set -e

out_dir="${1}"
if [ -z "${out_dir}" ]; then
    echo "Usage: ${0} <output directory>"
    exit 1
fi

mkdir -p "${out_dir}"
git archive HEAD generate_sheet.py generate_index.py src README.md | tar -C "${out_dir}" -x

for spec in specs/*.json; do
    if [ "$(python3 -c 'import json,sys; print("true" if json.load(open(sys.argv[1])).get("publish", False) else "false")' "${spec}")" != "true" ]; then
        echo "Skipping ${spec} (publish is not true)"
        continue
    fi
    python3 generate_sheet.py src/template.html.j2 "${spec}" "${out_dir}"
done

python3 generate_index.py src/index.html.j2 specs "${out_dir}"
