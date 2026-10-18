#!/usr/bin/env python3
"""Generate the landing page from the published aircraft specs.

Usage: ./generate_index.py src/index.html.j2 specs out

Only the specs with `publish` true get a row in the aircraft table, listed in
registration order. The output is out/index.html, the output directory is created
if it does not exist. The Updates section shows the three latest commits that
touched a published spec, newest first, grouped by date, one block per date. A
commit message line like `OH-STL: CG limits updated` is shown as the note for
that aircraft, one note per line; a line like `Publish: something` is shown as
the first entry for that day; aircraft without a note are listed together as one
comma separated entry. Commits that touch no published spec are skipped, so the
page always gets three blocks when three such commits exist. The update dates
come from git, so this only works inside a git clone with the history fetched
(the GitHub Actions checkout needs fetch-depth: 0).

Template variables:
  aircraft   the published specs, sorted by registration
  updates    the three latest commits touching a published spec, newest first,
             grouped by date, each block with the publish entries of that day, its
             notes and the registrations that have no note
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import jinja2

UPDATE_COUNT = 3
# Commits fetched before filtering out the ones that touch no published spec,
# so there are still UPDATE_COUNT blocks left when some commits only change the
# spec documentation.
FETCH_COUNT = UPDATE_COUNT * 10
DATE_FORMAT = "%d.%m.%Y"
RECORD = "\x1e"  # commit record separator
FILES = "\x1f"   # commit message / changed file list separator
NOTE = re.compile(r"([A-Z]{2}-[A-Z]{3}):\s*(.+)")
PUBLISH = re.compile(r"Publish:\s*(.+)", re.IGNORECASE)


def published_specs(specs_dir):
    """Published specs as {path: spec}, in registration order."""
    specs = {}
    for spec_path in sorted(Path(specs_dir).glob("*.json")):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        if spec.get("publish", False):
            specs[spec_path] = spec
    return dict(sorted(specs.items(), key=lambda item: item[1]["registration"]))


def spec_commits(specs_dir, limit):
    """Latest commits touching specs_dir as (date, message, files), newest first."""
    result = subprocess.run(
        ["git", "log", f"-n{limit}", f"--format={RECORD}%ci%n%B{FILES}", "--name-only",
         "--", str(specs_dir)],
        capture_output=True,
        text=True,
    )

    commits = []
    for record in result.stdout.split(RECORD):
        head, _, files = record.partition(FILES)
        if not head.strip():
            continue
        lines = head.strip("\n").split("\n")
        day = datetime.strptime(lines[0], "%Y-%m-%d %H:%M:%S %z")
        commits.append((day, "\n".join(lines[1:]), [f for f in files.split("\n") if f.strip()]))
    return commits


def build_context(specs_dir):
    """Template variables: the published aircraft and the latest spec commits."""
    published = published_specs(specs_dir)
    by_name = {path.name: spec for path, spec in published.items()}

    aircraft = [
        {
            "registration": spec["registration"],
            "aircraft_type": spec["aircraft_type"],
            "sheet": path.stem + ".html",
        }
        for path, spec in published.items()
    ]

    updates = []
    by_date = {}
    taken = 0
    for day, message, files in spec_commits(specs_dir, FETCH_COUNT):
        if taken >= UPDATE_COUNT:
            break

        planes = [by_name[Path(f).name] for f in files if Path(f).name in by_name]
        if not planes:
            continue
        taken += 1

        registrations = [plane["registration"] for plane in planes]
        block = by_date.setdefault(day.date(), {"publish": [], "notes": [], "plain": []})

        for match in PUBLISH.finditer(message):
            entry = match.group(1).strip()
            if entry not in block["publish"]:
                block["publish"].append(entry)

        for match in NOTE.finditer(message):
            if match.group(1) in registrations:
                note = match.group(0).strip()
                if note not in block["notes"]:
                    block["notes"].append(note)

        for reg in registrations:
            if reg in block["plain"] or any(n.startswith(f"{reg}:") for n in block["notes"]):
                continue
            block["plain"].append(reg)

    updates = [
        {"date": day.strftime(DATE_FORMAT), **block}
        for day, block in sorted(by_date.items(), reverse=True)
    ]

    return {"aircraft": aircraft, "updates": updates}


def main(argv):
    if len(argv) < 3:
        print(f"Usage: {argv[0]} src/index.html.j2 specs out")
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
