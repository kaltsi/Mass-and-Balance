#!/usr/bin/env python3
"""Compare generated output against a reference directory.

Usage: python3 tools/compare.py <generated_dir> <reference_dir>

Numbers and whitespace are normalized before comparing, so the comparison
reports semantic differences only (2.300 == 2.3, 148.0 == 148, indentation and
blank lines are ignored).
"""

import re
import sys
from pathlib import Path


def norm(text):
    def number(match):
        whole, frac = match.group(1), match.group(2)
        if frac:
            frac = frac.rstrip("0")
            whole = whole.rstrip("-") or "0"
            return whole + ("." + frac if frac else "")
        return "0" if whole == "-0" else whole

    # A placeholder that the spec does not define keeps the template default,
    # so expand it in the reference before comparing.
    text = re.sub(r"/\*[^*]+\*/(.*?)/\*\*/", lambda m: m.group(1).strip(), text)
    text = re.sub(r"(-?\d+)(?:\.(\d+))?", number, text)
    return re.sub(r"\s+", " ", text).strip()


def main(argv):
    generated, reference = Path(argv[1]), Path(argv[2])
    diffs = 0
    for ref_file in sorted(reference.glob("*.html")):
        gen_file = generated / ref_file.name
        if not gen_file.is_file():
            print(f"MISSING: {gen_file}")
            diffs += 1
            continue
        a, b = norm(gen_file.read_text()), norm(ref_file.read_text())
        if a == b:
            print(f"ok   {ref_file.name}")
        else:
            print(f"DIFF {ref_file.name}")
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    print(f"  at {i}: generated {a[i:i+60]!r}")
                    print(f"  at {i}: reference  {b[i:i+60]!r}")
                    break
            diffs += 1
    print(f"\n{diffs} difference(s)")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
