#!/usr/bin/env python3
"""Generate the landing page from the published aircraft specs.

Usage: ./generate_index.py <index.html.j2> <specs_dir> [output_dir]

Only the specs with `publish` true get a row in the aircraft table, listed in
registration order. The Updates section shows the three latest commits that
touched a published spec, each one mentioning the registration whose data was
updated. The update dates come from git, so this only works inside a git clone.

Template variables:
  aircraft   the published specs, sorted by registration
  updates    the three latest update dates, newest first, with the registrations
             updated on each of those dates
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import jinja2

UPDATE_COUNT = 3
DATE_FORMAT = "%d.%m.%Y"


def last_update(spec_path):
    """Latest commit date that touched spec_path, or None if git has no history."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ci", "--", str(spec_path)],
        capture_output=True,
        text=True,
    )
    stamp = result.stdout.strip()
    if not stamp:
        return None
    return datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S %z")


def build_context(specs_dir):
    """Template variables: the published aircraft and the latest updates."""
    aircraft = []
    for spec_path in sorted(Path(specs_dir).glob("*.json")):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        if not spec.get("publish", False):
            continue
        updated = last_update(spec_path)
        aircraft.append({
            "registration": spec["registration"],
            "aircraft_type": spec["aircraft_type"],
            "sheet": spec_path.stem + ".html",
            "updated": updated,
            "date": updated.strftime(DATE_FORMAT) if updated else "",
        })

    updates = [plane for plane in aircraft if plane["updated"]]
    by_date = {}
    for plane in updates:
        by_date.setdefault(plane["updated"], []).append(plane["registration"])

    updates = [
        {"date": day.strftime(DATE_FORMAT), "registrations": by_date[day]}
        for day in sorted(by_date, reverse=True)[:UPDATE_COUNT]
    ]

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
