#!/bin/sh

set -e

image="mass-and-balance"

if [ "${1}" = "--docker" ]; then
    use_docker=1
    shift
fi

out_dir="${1}"
if [ -z "${out_dir}" ]; then
    echo "Usage: ${0} [--docker] <output directory>"
    echo "Run python through the Dockerfile image."
    exit 1
fi

mkdir -p "${out_dir}"

if [ "${use_docker}" = "1" ]; then
    docker build -q -t "${image}" . > /dev/null

    # Export the tracked files so the export-subst footer dates are still
    # expanded, then run python inside the container with the work tree and
    # the output directory mounted.
    work="$(mktemp -d)"
    trap 'rm -rf "${work}"' EXIT
    git archive HEAD generate_sheet.py generate_index.py src specs README.md | tar -C "${work}" -x

    mounts="-v ${work}:/app -v $(cd "${out_dir}" && pwd):/app/out"
    if [ -d .git ]; then
        mounts="${mounts} -v $(cd .git && pwd):/app/.git"
    fi

    py() {
        # The image's ENTRYPOINT is "python3 generate_sheet.py ...", so
        # override it to run arbitrary python commands. Run as the current
        # user so the generated files are owned by it, not by root.
        docker run --rm --user "$(id -u):$(id -g)" ${mounts} --entrypoint python3 "${image}" "$@"
    }

    # Inside the container the work tree is /app and the output is /app/out.
    out_arg="out"
else
    py() {
        python3 "$@"
    }
    out_arg="${out_dir}"
fi

for spec in specs/*.json; do
    if [ "$(py -c 'import json,sys; print("true" if json.load(open(sys.argv[1])).get("publish", False) else "false")' "${spec}")" != "true" ]; then
        echo "Skipping ${spec} (publish is not true)"
        continue
    fi
    py generate_sheet.py src/template.html.j2 "${spec}" "${out_arg}"
done

py generate_index.py src/index.html.j2 specs "${out_arg}"
