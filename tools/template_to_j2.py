#!/usr/bin/env python3
"""Convert template.html (shell-script placeholders) to template.html.j2.

The old generator replaced /*NAME*/default/**/ regions with values from the
spec file. Jinja2 does the same job, so this script turns every region into a
Jinja expression:

    /*ACFT*/"OH-DEMO"/**/          ->  {{ ACFT|js("OH-DEMO") }}
    /*TOW*/g_tow/**/               ->  {{ TOW|default("g_tow") }}

Load point names keep their default variable name (g_tow, g_bw, ...) because a
spec may not define that load point at all.

The block placeholders become Jinja loops over `load_points`; those are written
out by hand below because a loop cannot be expressed as a single expression.

Usage: python3 tools/template_to_j2.py template.html template.html.j2
"""

import ast
import json
import re
import sys
from pathlib import Path

# Load point names that the template handles inline (they have a fixed
# variable name in the demo template).
LP_NAMES = [
    "BASIC_WEIGHT", "FRONT_SEAT", "BACK_SEAT", "FUEL", "TAXI_FUEL",
    "BAGGAGE", "TOW", "LNDW", "ENDURANCE", "FUEL_FLOW", "FLIGHT_TIME",
]

# Hand-written Jinja loops for the block placeholders.
BLOCKS = {
    "SAVEABLES": """{% for lp in load_points if lp.SAVEABLE %}
    {{ lp.NAME }} : {{ lp.DEFAULT }},
{% endfor %}""",

    "SAVEABLE_VALUES": """{% for lp in load_points if lp.SAVEABLE %}
\t{{ lp.NAME }}.vu.get_si(),
{% endfor %}""",

    "REPLACE_TABLE_ROWS": """{% for lp in load_points %}
\t{{ lp.NAME }}=new l_point("{{ lp.NAME }}", ["{{ lp.EN }}", "{{ lp.FI }}"], "{{ lp.UNIT }}", {{ lp.DEFAULT_EXPR }}, {{ lp.MIN }}, {{ lp.MAX }}, {{ lp.MOMENT_ARM }}{% if lp.STEP is not none %}, {{ lp.STEP }}{% endif %});{% if lp.TYPE == 'F' %} {{ lp.NAME }}.fuel_flow = true;{% endif %}
\trows.push(new {{ lp.ROW_CLASS }}interactive_row({{ lp.NAME }}{% if lp.REVERSE %}, "reverse"{% endif %}));
{% endfor %}""",

    "EXTRA_CALC_MASS": """{% for lp in extra %}
\t    {{ lp.NAME }},
{% endfor %}""",

    "EXTRA_MASS_CALC_MOMENTS": """{% for lp in extra %}
\tcalc_moment({{ lp.NAME }});
{% endfor %}""",

    "EXTRA_MASS_MOMENTS": """{% for lp in extra %}
\t    {{ lp.NAME }}.moment +
{% endfor %}""",

    "EXTRA_DEBUG": """{% for lp in extra %}{{ lp.NAME }}.moment.toFixed(3){% if not loop.last %} + {% endif %}{% endfor %}""",

    "HIDE_DEBUG": """{% if not hide_debug %}document.getElementById("debug_button").setAttribute('style', 'display');{% endif %}""",
}


def jinja_literal(text):
    """Turn the demo default text into a Jinja literal."""
    text = text.strip()
    try:
        return repr(ast.literal_eval(text))
    except (ValueError, SyntaxError):
        return json.dumps(text)


def convert(text):
    def repl(match):
        name, content = match.group(1), match.group(2)
        if name in BLOCKS:
            return BLOCKS[name]
        if name in LP_NAMES:
            return '{{ %s|default(%s) }}' % (name, json.dumps(content.strip()))
        return "{{ %s|js(%s) }}" % (name, jinja_literal(content))

    return re.sub(r"/\*([A-Z0-9_]+)\*/(.*?)/\*\*/", repl, text)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    Path(dst).write_text(convert(Path(src).read_text()))
