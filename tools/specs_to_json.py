#!/usr/bin/env python3
"""Convert aircraft .specs files to JSON.

The JSON files are the machine-readable form of the spec files; they are
consumed by the (future) Python version of parse_template.sh.

Usage:
    tools/specs_to_json.py specs/oh-stl.specs [output_dir]
    tools/specs_to_json.py specs/               # convert every .specs file

Schema (one object per aircraft):

    {
      "ACFT": "OH-STL",                  # registration
      "ACFT_TYPE": "Diamond DA 40 NG Star",
      "DATA_ORIGIN": "Numbers: ...",
      "LITRE2KILO": 0.84,
      "MOMENT_ARMS": [2.4, ...],         # x-coordinates of the envelope
      "TOF_MASS_LIMITS": [940, ...],     # y-coordinates, take-off
      "LND_MASS_LIMITS": [940, ...],     # y-coordinates, landing
      "MOM_DRAW_MAX": 475,
      "MASS_DRAW_MAX": 390,
      "TRANSLATE_X": 50,
      "LND_LIMIT_X1": 2.44,
      "LND_LIMIT_X2": 2.55,
      "INVALID_DATA": null,              # "visible" if uncommented in the spec
      "LOAD_POINTS": [
        {
          "LP": "LP_R_BASIC_WEIGHT",     # original spec token, kept for reference
          "NAME": "BASIC_WEIGHT",        # JS variable name / saveable key
          "TYPE": "R",                   # N, R, I, F or C
          "EN": "Basic weight",          # '#' in the spec means space
          "FI": "Perusmassa",
          "UNIT": "kg",
          "DEFAULT": 909.4,
          "MIN": 0,
          "MAX": -1,
          "MOMENT_ARM": 2.43,
          "STEP": null,                  # optional slider step
          "SAVEABLE": false              # true for LP_I_ / LP_F_ / LP_C_
        }
      ]
    }

Key names are kept identical to the spec file names so that they map one-to-one
to the /*NAME*/ placeholders in template.html.
"""

import json
import os
import re
import sys

KNOWN_LOAD_POINTS = [
    "BASIC_WEIGHT", "FRONT_SEAT", "FUEL", "BAGGAGE", "TAXI_FUEL",
    "TOW", "LNDW", "ENDURANCE", "FUEL_FLOW", "FLIGHT_TIME",
]

# Load point types: interactive (saveable), non-interactive, fuel flow, checkbox
LP_TYPES = ("N", "R", "I", "F", "C")
SAVEABLE_TYPES = ("I", "F", "C")

LIST_KEYS = ("MOMENT_ARMS", "TOF_MASS_LIMITS", "LND_MASS_LIMITS")
INT_KEYS = ("MOM_DRAW_MAX", "MASS_DRAW_MAX", "TRANSLATE_X")
FLOAT_KEYS = ("LITRE2KILO", "LND_LIMIT_X1", "LND_LIMIT_X2")
STRING_KEYS = ("ACFT", "ACFT_TYPE", "DATA_ORIGIN", "INVALID_DATA")


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
    if not lp.startswith("LP_") or lp[3] not in LP_TYPES:
        raise ValueError("unknown load point type: %s" % lp)

    lp_type = lp[3]
    name = lp[5:]

    point = {
        "LP": lp,
        "NAME": name,
        "TYPE": lp_type,
        "EN": parts[1].strip('"').replace("#", " "),
        "FI": parts[2].strip('"').replace("#", " "),
        "UNIT": parts[3].strip('"'),
        "DEFAULT": num(parts[4]),
        "MIN": num(parts[5]),
        "MAX": num(parts[6]),
        "MOMENT_ARM": num(parts[7]),
        "STEP": num(parts[8]) if len(parts) > 8 else None,
        "SAVEABLE": lp_type in SAVEABLE_TYPES,
    }
    return point


def parse_specs(path):
    data = {}
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

            if key == "LOAD_POINT":
                load_points.append(parse_load_point(value))
            elif key in LIST_KEYS:
                data[key] = [num(x) for x in value.strip("[]").split(",")]
            elif key in INT_KEYS:
                data[key] = int(float(value))
            elif key in FLOAT_KEYS:
                data[key] = float(value)
            else:
                data[key] = value.strip('"')

    data["LOAD_POINTS"] = load_points
    return data


def convert(path, out_dir=None):
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    data = parse_specs(path)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, name + ".json")
    else:
        out_path = name + ".json"

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)
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
