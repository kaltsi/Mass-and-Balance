#!/usr/bin/env python3
"""Convert aircraft .specs files to JSON.

The JSON files are the machine-readable form of the spec files; they are
consumed by parse_template.py.

Usage:
    tools/specs_to_json.py specs/oh-stl.specs [output_dir]
    tools/specs_to_json.py specs/               # convert every .specs file

Schema (one object per aircraft):

    {
      "registration": "OH-STL",
      "aircraft_type": "Diamond DA 40 NG Star",
      "data_source": "Numbers: ...",
      "fuel_density_kg_per_l": 0.84,
      "envelope": {                         # the drawn limit polygon
        "moment_arms": [2.4, ...],          # x-coordinates
        "takeoff_mass_limits": [940, ...],  # y-coordinates, take-off
        "landing_mass_limits": [940, ...],  # y-coordinates, landing
        "landing_limit_arm_start": 2.44,
        "landing_limit_arm_end": 2.55,
        "moment_axis_max": 475,
        "mass_axis_max": 390,
        "chart_x_offset": 50
      },
      "invalid_data": "visible",            # only if uncommented in the spec
      "load_points": [
        {
          "name": "BASIC_WEIGHT",           # JS variable name / saveable key
          "row_type": "computed_reversed",
          "label": {"en": "Basic weight", "fi": "Perusmassa"},   # '#' in the spec means space
          "unit": "kg",
          "default": 909.4,
          "min": 0,
          "max": 1,
          "show_max": false,                # negative max in the spec
          "moment_arm": 2.43,
          "step": 0.1,                      # omitted when the spec has no step
          "save": true
        }
      ]
    }

The .specs files use the old upper-case names; the mapping below is what turns
them into the readable keys above.
"""

import json
import os
import sys

# .specs key -> JSON key
KEY_MAP = {
    "ACFT": "registration",
    "ACFT_TYPE": "aircraft_type",
    "DATA_ORIGIN": "data_source",
    "LITRE2KILO": "fuel_density_kg_per_l",
    "MOMENT_ARMS": "moment_arms",
    "TOF_MASS_LIMITS": "takeoff_mass_limits",
    "LND_MASS_LIMITS": "landing_mass_limits",
    "MOM_DRAW_MAX": "moment_axis_max",
    "MASS_DRAW_MAX": "mass_axis_max",
    "TRANSLATE_X": "chart_x_offset",
    "LND_LIMIT_X1": "landing_limit_arm_start",
    "LND_LIMIT_X2": "landing_limit_arm_end",
    "INVALID_DATA": "invalid_data",
}

ENVELOPE_KEYS = {
    "moment_arms",
    "takeoff_mass_limits",
    "landing_mass_limits",
    "landing_limit_arm_start",
    "landing_limit_arm_end",
    "moment_axis_max",
    "mass_axis_max",
    "chart_x_offset",
}

# .specs key -> value type
LIST_KEYS = ("MOMENT_ARMS", "TOF_MASS_LIMITS", "LND_MASS_LIMITS")
INT_KEYS = ("MOM_DRAW_MAX", "MASS_DRAW_MAX", "TRANSLATE_X")
FLOAT_KEYS = ("LITRE2KILO", "LND_LIMIT_X1", "LND_LIMIT_X2")

LIST_KEYS = ("MOMENT_ARMS", "TOF_MASS_LIMITS", "LND_MASS_LIMITS")
INT_KEYS = ("MOM_DRAW_MAX", "MASS_DRAW_MAX", "TRANSLATE_X")
FLOAT_KEYS = ("LITRE2KILO", "LND_LIMIT_X1", "LND_LIMIT_X2")

# LP_<type>_ letter -> readable row type
ROW_TYPES = {
    "N": "computed",
    "R": "computed_reversed",
    "I": "interactive",
    "F": "fuel_flow",
    "C": "checkbox",
}
SAVEABLE_TYPES = ("interactive", "fuel_flow", "checkbox")

# Key order in the JSON files: identity, then the chart, then the load points.
TOP_ORDER = [
    "registration",
    "aircraft_type",
    "data_source",
    "fuel_density_kg_per_l",
    "envelope",
    "invalid_data",
    "load_points",
]

ENVELOPE_ORDER = [
    "moment_arms",
    "takeoff_mass_limits",
    "landing_mass_limits",
    "landing_limit_arm_start",
    "landing_limit_arm_end",
    "moment_axis_max",
    "mass_axis_max",
    "chart_x_offset",
]

LP_ORDER = [
    "name",
    "row_type",
    "label",
    "unit",
    "default",
    "min",
    "max",
    "show_max",
    "moment_arm",
    "step",
    "save",
]

LABEL_ORDER = ["en", "fi"]


def order(data, keys):
    """Return the dict with the keys in the given order (unknown keys last)."""
    out = {key: data[key] for key in keys if key in data}
    for key in data:
        if key not in out:
            out[key] = data[key]
    return out


def num(s):
    """Return an int when possible, otherwise a float."""
    v = float(s)
    return int(v) if v.is_integer() else v


def parse_load_point(value):
    """Parse 'LP_I_NAME "English" "Finnish" "unit" def min max arm [step]'."""
    parts = value.split()
    if len(parts) < 8:
        raise ValueError("bad load point: %s" % value)

    lp = parts[0]
    if not lp.startswith("LP_") or lp[3] not in ROW_TYPES:
        raise ValueError("unknown load point type: %s" % lp)

    row_type = ROW_TYPES[lp[3]]
    max_value = num(parts[6])

    point = {
        "name": lp[5:],
        "row_type": row_type,
        "label": {
            "en": parts[1].strip('"').replace("#", " "),
            "fi": parts[2].strip('"').replace("#", " "),
        },
        "unit": parts[3].strip('"'),
        "default": num(parts[4]),
        "min": num(parts[5]),
        "max": abs(max_value),
        "show_max": max_value > 0,
        "moment_arm": num(parts[7]),
        "save": row_type in SAVEABLE_TYPES,
    }
    if len(parts) > 8:
        point["step"] = num(parts[8])
    point = order(point, LP_ORDER)
    return point


def parse_specs(path):
    data = {}
    envelope = {}
    load_points = []

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError("bad line in %s: %s" % (path, line))

            key, value = line.split("=", 1)
            value = value.strip()
            name = KEY_MAP.get(key, key)

            if key == "LOAD_POINT":
                load_points.append(parse_load_point(value))
            else:
                if key in LIST_KEYS:
                    parsed = [num(x) for x in value.strip("[]").split(",")]
                elif key in INT_KEYS:
                    parsed = int(float(value))
                elif key in FLOAT_KEYS:
                    parsed = float(value)
                else:
                    parsed = value.strip('"')
                target = envelope if name in ENVELOPE_KEYS else data
                target[name] = parsed

    if envelope:
        data["envelope"] = order(envelope, ENVELOPE_ORDER)
    data["load_points"] = load_points
    return order(data, TOP_ORDER)


def convert(path, out_dir=None):
    name = os.path.splitext(os.path.basename(path))[0]
    data = parse_specs(path)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, name + ".json")
    else:
        out_path = name + ".json"

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    return out_path


def main(argv):
    if len(argv) < 2:
        print("Usage: %s aircraft.specs [output_dir]" % argv[0])
        return 1

    target = argv[1].rstrip("/")
    out_dir = argv[2].rstrip("/") if len(argv) > 2 else None

    if os.path.isdir(target):
        files = sorted(f for f in os.listdir(target) if f.endswith(".specs"))
        for f in files:
            print(convert(os.path.join(target, f), out_dir or target))
    else:
        print(convert(target, out_dir))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
