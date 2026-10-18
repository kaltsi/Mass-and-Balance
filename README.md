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

The landing page lists one row per published spec and the three latest dates with
a qualifying commit, newest first, one block per date, commits of the same date
merged. The dates come from git, so the checkout needs the full history.

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
A commit that touches no published spec is only shown when its message has a
`Publish:` line.
