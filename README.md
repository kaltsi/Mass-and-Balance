# Mass and Balance

Mass and balance calculation sheets for specific aircraft. Each sheet is a
standalone HTML file, so it stays usable without an internet connection once it
has been downloaded to a local computer (iPad etc.).

The published page is here: <http://kaltsi.github.io/Mass-and-Balance/>

## Making a sheet for your own aircraft

Look at the existing specification files under `specs/`, copy one, edit it, set
`publish` to `true` and run `export.sh`. The spec format is documented in
[specs/README.md](specs/README.md).

## Generator

`parse_template.py` renders `template.html.j2` with Jinja2 (`jinja2 >= 3.1`, see
`pyproject.toml`):

```sh
./parse_template.py template.html.j2 specs/oh-kas.json out
```

`export.sh` runs it for every spec file that has `publish` set to `true` (the key is
`false` when it is not set); `publish` is passed to the template but not used by it. A
spec key that is not set falls back to the default written in the template.

### Template variables

The template variables are the JSON keys (`registration`, `aircraft_type`,
`data_source`, `fuel_density_kg_per_l`, `publish`, `envelope`, `invalid_data`) plus the
load point lists: `load_points` (every load point, in spec order) and `extra` (the load
points that are not part of the fixed calculation chains). Values are formatted for
JavaScript with the `js` filter.

The load point name placeholders (`lndw`, `tow`, `fuel`, ...) resolve to the load
point name when the spec has that row, otherwise to the variable name written in the
template (`g_lw`, `g_tow`, ...).

### Running it in a container

```sh
docker build -t mass-and-balance .
docker run --rm -v "$PWD/out:/app/out" mass-and-balance specs/oh-kas.json out
```

## Publishing

The published page is the `gh-pages` branch, served by GitHub Pages exactly as it is
committed, without any build step. `index.html` is the hand written landing page and
links to the sheets by relative path, so the generated files must sit next to it at
the branch root.

`git archive` expands the `$Format: %ci$` placeholder in the `*.html` files marked
`export-subst` in `.gitattributes`, which is how the footer date gets baked into the
published copy. The generated sheets keep the placeholder, so the date only appears in
the exported copy — `export.sh` only works inside a git clone for this reason.

The debug section is hidden in generated sheets: `build_context()` sets `hide_debug`,
which renders the debug button with `display:none`.
