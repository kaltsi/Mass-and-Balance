#!/usr/bin/env python3
"""Generate a standalone mass & balance HTML sheet from a JSON aircraft spec.

Usage: ./parse_template.py <template.html> <spec.json> [output_dir]

The template contains placeholders written as /*NAME*/default/**/. Every key in
the spec JSON replaces the matching placeholder, and the LOAD_POINTS list is
turned into the JavaScript row definitions. This is the Python port of
parse_template.sh; the output is identical apart from number formatting
(2.300 -> 2.3, 148.0 -> 148).

Load point types:
  LP_I  interactive row, declares a saveable variable
  LP_F  interactive fuel flow row
  LP_C  interactive checkbox row
  LP_R  non-interactive row with result and value cells reversed
  LP_N  non-interactive row
Load points whose name is not one of the fixed ones below are "extra" equipment
and are injected into the mass/moment calculation chains.
"""

import json
import re
import sys
from pathlib import Path

# Load points that the template already defines by hand. Anything else is
# considered user-added equipment.
KNOWN_LOAD_POINTS = {
    "BASIC_WEIGHT", "FRONT_SEAT", "FUEL", "BAGGAGE", "TAXI_FUEL",
    "TOW", "LNDW", "ENDURANCE", "FUEL_FLOW", "FLIGHT_TIME",
}

# LP_<type>_ -> row class prefix
ROW_PREFIX = {"I": "", "F": "", "C": "cbox_", "N": "non_", "R": "non_"}

def js_value(value):
    """Format a JSON value the way JavaScript source expects it."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(js_value(v) for v in value) + "]"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, float):
        return repr(value)
    return str(value)


def substitute(text, name, value):
    """Replace the /*name*/.../**/ region with value (like the perl one-liner)."""
    pattern = re.compile(r"/\*" + re.escape(name) + r"\*/.*?/\*\*/", re.DOTALL)
    return pattern.sub(lambda match: value, text)


def load_point_line(lp):
    """NAME=new l_point(...) definition."""
    name, lp_type = lp["NAME"], lp["TYPE"]
    if lp_type in ("N", "R"):
        value = js_value(lp["DEFAULT"])
    else:
        save_item = ".s" if lp_type in ("I", "F", "C") else ""
        value = f"g_defs{save_item}.{name}"

    line = (
        f'{name}=new l_point("{name}", [{js_value(lp["EN"])}, {js_value(lp["FI"])}], '
        f'{js_value(lp["UNIT"])}, {value}, {js_value(lp["MIN"])}, '
        f'{js_value(lp["MAX"])}, {js_value(lp["MOMENT_ARM"])}'
    )
    if lp.get("STEP") is not None:
        line += f", {js_value(lp['STEP'])}"
    line += ");"
    if lp_type == "F":
        line += f" {name}.fuel_flow = true;"
    return line


def row_line(lp):
    """rows.push(new ..._row(...)) definition."""
    name, lp_type = lp["NAME"], lp["TYPE"]
    reverse = ', "reverse"' if lp_type == "R" else ""
    return f"rows.push(new {ROW_PREFIX[lp_type]}interactive_row({name}{reverse}));"


def render(template, spec):
    rows, saveables, saveable_values, extra_mass = [], [], [], []

    for lp in spec["LOAD_POINTS"]:
        name = lp["NAME"]
        rows.append(load_point_line(lp))
        if lp["TYPE"] in ("I", "F", "C"):
            saveables.append(f"{name} : {js_value(lp['DEFAULT'])},")
            saveable_values.append(f"{name}.vu.get_si(),")
        rows.append(row_line(lp))
        if name not in KNOWN_LOAD_POINTS:
            extra_mass.append(name)

    # Every other key replaces its placeholder; order does not matter.
    for key, value in spec.items():
        if key != "LOAD_POINTS":
            template = substitute(template, key, js_value(value))

    template = substitute(template, "REPLACE_TABLE_ROWS", "\n".join(rows) + "\n")
    for name in [lp["NAME"] for lp in spec["LOAD_POINTS"]]:
        template = substitute(template, name, name)

    template = substitute(template, "SAVEABLES", "\n".join(saveables) + "\n")
    template = substitute(template, "SAVEABLE_VALUES", "\n".join(saveable_values) + "\n")

    if extra_mass:
        calc_mass = "".join(f"{n},\n" for n in extra_mass)
        calc_moments = "".join(f"calc_moment({n});\n" for n in extra_mass)
        moments = "".join(f"{n}.moment +\n" for n in extra_mass)
        debug_lines = "".join(
            f'debug.textContent += (" " + {n}.moment.toFixed(3));\n' for n in extra_mass
        )
    else:
        # Empty replacement for the extra equipment.
        calc_mass = calc_moments = moments = debug_lines = ""

    template = substitute(template, "EXTRA_CALC_MASS", calc_mass)
    template = substitute(template, "EXTRA_MASS_CALC_MOMENTS", calc_moments)
    template = substitute(template, "EXTRA_MASS_MOMENTS", moments)
    template = substitute(template, "EXTRA_DEBUG", debug_lines)

    # Finally hide the debug button from the published sheets.
    template = substitute(template, "HIDE_DEBUG", " ")

    return template


def main(argv):
    if len(argv) < 3:
        print(f"Usage: {argv[0]} template.html spec.json [output_dir]")
        return 1

    template_path, spec_path = Path(argv[1]), Path(argv[2])
    if not template_path.is_file():
        print(f"FAIL: template file: {template_path} - not found.")
        return 1
    if not spec_path.is_file():
        print(f"FAIL: spec file: {spec_path} - not found.")
        return 1

    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: {spec_path} - not valid JSON: {exc}")
        return 1

    if not isinstance(spec, dict) or not isinstance(spec.get("LOAD_POINTS"), list):
        print(f"FAIL: {spec_path} - expected an object with a LOAD_POINTS list")
        return 1

    out_dir = Path(argv[3]) if len(argv) > 3 else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (spec_path.stem + ".html")

    print(f"Handling file: {spec_path}")
    template = template_path.read_text(encoding="utf-8")
    out_file.write_text(render(template, spec), encoding="utf-8")
    print(f"Output file is: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
