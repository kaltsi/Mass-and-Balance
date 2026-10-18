# Mass and Balance

Mass and balance calculation sheets for specific aircraft. Each sheet
is a standalone HTML file, so it stays usable without an internet
connection once it has been downloaded to a local device (e.g. an
iPad).

<http://kaltsi.github.io/Mass-and-Balance/>

## Making a sheet for your own aircraft

Look at the existing specification files under `specs/`, copy one, edit it, set
`publish` to `true` and run `build.sh`. The spec format is documented in
[specs/README.md](specs/README.md).

## Generator

`generate_sheet.py` renders `src/template.html.j2` with Jinja2 (`jinja2 >= 3.1`, see
`pyproject.toml`):

```sh
./generate_sheet.py src/template.html.j2 specs/oh-kas.json out
```

All templates live under `src/`. The template includes the css, javascript and svg
parts (`style.css`, `script.js.j2`, `svg.j2`) which are read from `src/`, so the
output is still one standalone HTML file.

`build.sh` runs it for every spec file that has `publish` set to `true` (default: `false`).
A spec key that is not set falls back to the default written in the template. After the
sheets it regenerates the landing page, see below.

### Template variables

The template variables are the JSON keys (`registration`, `aircraft_type`,
`data_source`, `fuel_density_kg_per_l`, `publish`, `envelope`, `invalid_data`) plus the
load point lists: `load_points` (every load point, in spec order) and `extra` (the load
points that are not part of the fixed calculation chains). Values are formatted for
JavaScript with the `js` filter.

The load point name placeholders (`lndw`, `tow`, `fuel`, ...) resolve to the load
point name when the spec has that row, otherwise to the variable name written in the
template (`g_lw`, `g_tow`, ...).

### Landing page

`generate_index.py` renders `src/index.html.j2` into `index.html`:

```sh
./generate_index.py src/index.html.j2 specs out
```

The aircraft table gets one row per spec with `publish` true, in registration order, and
the Updates section lists the three latest commits that touched a published spec. A commit
message line like `OH-STL: CG limits updated` is shown as the note for that aircraft, one
note per line, a line like `Publish: something` (case insensitive) is shown as the first
entry for that day, and the aircraft without a note are listed as one comma separated
entry. The update dates come from `git log`, so the page is regenerated whenever a
published spec changes.

### Running it in a container

The build can run through the image built from the Dockerfile with
`./build.sh --docker out`: the image is built
once, the tracked files are exported with `git archive` (so the export-subst
footer dates are still expanded) and every python call runs in the container,
as the current user's uid and gid, with the work tree, the output directory and
`.git` mounted (without a mounted history the aircraft table is still rendered,
only the Updates section stays empty).

## Publishing

The published page is the `gh-pages` branch, served by GitHub Pages exactly as it is
committed, without any build step. `index.html` is generated from `src/index.html.j2` and
links to the sheets by relative path, so the generated files must sit next to it at
the branch root.

`git archive` expands the `$Format: %ci$` placeholder in the `*.html`
files marked `export-subst` in `.gitattributes`, which is how the
footer date gets baked into the published copy.

The debug section is hidden in generated sheets: `build_context()`
sets `hide_debug`, which renders the debug button with `display:none`.
