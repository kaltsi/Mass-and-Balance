#!/usr/bin/env python3
"""Generate the landing page from the published aircraft specs.

Usage: ./generate_index.py <index.html.j2> <specs_dir> [output_dir]

Only the specs with `publish` true get a row in the aircraft table, listed in
registration order. The Updates section shows the three latest commits that
touched a published spec. A commit message line like `OH-STL: CG limits updated`
is shown as the note for that aircraft, one note per line; a line like
`Publish: something` is shown as the first entry for that day; aircraft without a
note are listed together as one comma separated entry. The update dates come from
git, so this only works inside a git clone.

Template variables:
  aircraft   the published specs, sorted by registration
  updates    the three latest update dates, newest first, each with the publish
             entries of that commit, its notes and the registrations that have no
             note
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import jinja2

UPDATE_COUNT = 3
DATE_FORMAT = "%d.%m.%Y"
NOTE = re.compile(r"([A-Z]{2}-[A-Z]{3}):\s*(.+)")
PUBLISH = re.compile(r"Publish:\s*(.+)", re.IGNORECASE)


def last_commit(spec_path):
    """Latest commit that touched spec_path as (date, message), or (None, "")."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ci%n%B", "--", str(spec_path)],
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().split("\n")
    if not lines[0]:
        return None, ""
    return datetime.strptime(lines[0], "%Y-%m-%d %H:%M:%S %z"), "\n".join(lines[1:])


def build_context(specs_dir):
    """Template variables: the published aircraft and the latest updates."""
    aircraft = []
    for spec_path in sorted(Path(specs_dir).glob("*.json")):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        if not spec.get("publish", False):
            continue

        day, message = last_commit(spec_path)
        note = None
        for match in NOTE.finditer(message):
            if match.group(1) == spec["registration"]:
                note = match.group(0).strip()
                break
        publish = PUBLISH.search(message)

        aircraft.append({
            "registration": spec["registration"],
            "aircraft_type": spec["aircraft_type"],
            "sheet": spec_path.stem + ".html",
            "updated": day,
            "date": day.strftime(DATE_FORMAT) if day else "",
            "note": note,
            "publish": publish.group(1).strip() if publish else None,
        })

    by_date = {}
    for plane in aircraft:
        if plane["updated"]:
            by_date.setdefault(plane["updated"], []).append(plane)

    updates = []
    for day in sorted(by_date, reverse=True)[:UPDATE_COUNT]:
        planes = by_date[day]
        publish = []
        for plane in planes:
            if plane["publish"] and plane["publish"] not in publish:
                publish.append(plane["publish"])

        updates.append({
            "date": day.strftime(DATE_FORMAT),
            "publish": publish,
            "notes": [plane["note"] for plane in planes if plane["note"]],
            "plain": [plane["registration"] for plane in planes if not plane["note"]],
        })

    return {"aircraft": aircraft, "updates": updates}


def main(argv):
    if len(argv) < 3:
        print(f"Usage: {argv[0]} index.html.j2 specs [output_dir]")
        return 1

    template_path, specs_dir = Path(argv[1]), Path(argv[2])
    if not template_path.is_file():
        print(f"FAIL: template file: {template_path} - not found.")
        return 1
    if not specs_dir.is_dir():
        print(f"FAIL: specs directory: {specs_dir} - not found.")
        return 1

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path.parent),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template(template_path.name)

    out_dir = Path(argv[3]) if len(argv) > 3 else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"

    print(f"Handling file: {template_path}")
    out_file.write_text(template.render(**build_context(specs_dir)), encoding="utf-8")
    print(f"Output file is: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
