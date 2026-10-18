# Mass and Balance

Mass and balance calculation sheets for specific aircraft. Each sheet is a
standalone HTML file.

<http://kaltsi.github.io/Mass-and-Balance/>

## Making a sheet for your own aircraft

Look at the existing specification files under `specs/`, copy one, edit it, set
`publish` to `true` and run `build.sh`. The spec format is documented in
[specs/README.md](specs/README.md).

## Generator

```sh
./generate_sheet.py src/template.html.j2 specs/oh-kas.json out
```

`build.sh` runs it for every spec with `publish` true and then regenerates the
landing page:

```sh
./generate_index.py src/index.html.j2 specs out
```

The landing page lists one row per published spec and the three latest commits
that touched one, newest first, grouped by date. The dates come from git, so the
checkout needs the full history (`fetch-depth: 0`).

### Running it in a container

```sh
./build.sh --docker out
```

Runs the python calls in the Dockerfile image, as the current user, with the
work tree, the output directory and `.git` mounted.

## Publishing

Commit messages that touch a published spec show up in the landing page Updates
section. A line like `OH-STL: CG limits updated` becomes the note for that
aircraft and a line like `Publish: something` is added as an entry for that day.

Both the landing page and the sheets have a sun/moon button that switches between
the light and the dark colour scheme. In the sheets the theme is an entry in the
Settings dropdown instead. The choice is saved in `localStorage` under
`kaltsi.mb.theme`, so the landing page and all the sheets use the same theme, and
without a saved choice the system preference is used.
