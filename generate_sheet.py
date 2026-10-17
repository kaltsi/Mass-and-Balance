#!/usr/bin/env python3
"""Generate a standalone mass & balance HTML sheet from a JSON aircraft spec.

Usage: ./generate_sheet.py <template.html.j2> <spec.json> [output_dir]

The template is a Jinja2 template. Every key in the spec JSON is available as a
template variable and the load_points list is exposed as `load_points` (and
`extra`, the load points that are not part of the fixed rows).

Load point row types:
  interactive         slider row, declares a saveable variable
  fuel_flow           interactive fuel flow row
  checkbox            interactive checkbox row
  computed            non-interactive row
  computed_reversed   non-interactive row with result and value cells reversed
Load points whose name is not one of the fixed ones below are "extra" equipment
and are injected into the mass/moment calculation chains.

The template includes the css, javascript and svg parts (style.css,
script.js.j2, svg.j2) which are looked up next to the template, so
the output is still one self-contained HTML file.
"""

import json
import sys
from pathlib import Path

import jinja2

# Load points that the template already defines by hand. Anything else is
# considered user-added equipment.
KNOWN_LOAD_POINTS = {
    # These have fixed positions in the calculation chains, everything else is
    # handled by the extras loop.
    "BASIC_WEIGHT", "FRONT_SEAT", "FUEL", "BAGGAGE", "TAXI_FUEL",
    "TOW", "LNDW", "ENDURANCE", "FUEL_FLOW", "FLIGHT_TIME",
}

# Row type -> row class prefix
ROW_PREFIX = {
    "interactive": "",
    "fuel_flow": "",
    "checkbox": "cbox_",
    "computed": "non_",
    "computed_reversed": "non_",
}


def js(value, default=None):
    """Format a JSON value the way JavaScript source expects it.

    A missing key (undefined) or a null value falls back to the template default.
    """
    if isinstance(value, jinja2.Undefined) or value is None:
        value = default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(js(v) for v in value) + "]"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if value is None:
        return ""
    return repr(value)


def build_context(spec):
    """Template variables: the spec keys plus the processed load points."""
    load_points = []
    for lp in spec["load_points"]:
        point = dict(lp)
        point["row_class"] = ROW_PREFIX[lp["row_type"]]
        point["reverse"] = lp["row_type"] == "computed_reversed"
        if lp["save"]:
            point["default_expr"] = f"g_defs.s.{lp['name']}"
        else:
            point["default_expr"] = js(lp["default"])
        load_points.append(point)

    # A load point name placeholder prints the name itself, or the template's
    # default variable name if the spec does not have that load point.
    context = {key: value for key, value in spec.items() if key != "load_points"}
    for point in load_points:
        context[point["name"].lower()] = point["name"]

    context["load_points"] = load_points
    context["extra"] = [p for p in load_points if p["name"] not in KNOWN_LOAD_POINTS]
    context["hide_debug"] = True
    return context


def render(spec, template):
    return template.render(**build_context(spec))


def main(argv):
    if len(argv) < 3:
        print(f"Usage: {argv[0]} template.html.j2 spec.json [output_dir]")
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

    if not isinstance(spec, dict) or not isinstance(spec.get("load_points"), list):
        print(f"FAIL: {spec_path} - expected an object with a load_points list")
        return 1

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path.parent),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["js"] = js
    template = env.get_template(template_path.name)

    out_dir = Path(argv[3]) if len(argv) > 3 else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (spec_path.stem + ".html")

    print(f"Handling file: {spec_path}")
    out_file.write_text(render(spec, template), encoding="utf-8")
    print(f"Output file is: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
