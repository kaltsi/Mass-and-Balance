# Spec files

Every aircraft has one spec file, `<registration>.json`.
A key that is not set in a spec file uses the default value in the template.

## Top level keys

| key | type | meaning | template default |
|---|---|---|---|
| `registration` | string | aircraft registration, the sheet title and the output file name | `OH-DEMO` |
| `aircraft_type` | string | type printed under the title | `Generic A000-Z` |
| `data_source` | string | where the numbers come from, printed in the sheet | `Mass and balance sheet for OH-DEMO 01.01.1970` |
| `fuel_density_kg_per_l` | number | fuel mass per litre (Avgas 0.721) | `0.721` |
| `envelope` | object | chart geometry, see below | |
| `invalid_data` | string | CSS visibility for the INVALID text on the chart, `hidden` or `visible` | `hidden` |
| `publish` | boolean | whether `build.sh` generates a sheet for this spec; `false` by default | `false` |
| `load_points` | array | the table rows, in the order they are printed | |

## envelope

The chart is drawn from polygon points: moment arms on the x axis, mass on the y
axis. The takeoff polygon uses `takeoff_mass_limits`, the landing polygon uses
`landing_mass_limits`.

| key | meaning | template default |
|---|---|---|
| `moment_arms` | x of the polygon points, meters from the datum | `0.787, 0.787, 0.821, 0.925, 0.925, 0.787` |
| `takeoff_mass_limits` | y of the polygon points, kg | `450, 612, 757, 757, 450, 450` |
| `landing_mass_limits` | y of the landing polygon, kg | `450, 612, 700, 700, 450, 450` |
| `landing_limit_arm_start` | x where the landing limit line starts, meters | `0.8075` |
| `landing_limit_arm_end` | x where the landing limit line ends, meters | `0.925` |
| `moment_axis_max` | x axis maximum, kg*m | `475` |
| `mass_axis_max` | y axis maximum, kg | `375` |
| `chart_x_offset` | x offset of the chart drawing, px | `50` |

## load_points

Each load point is one row in the table.

| key | meaning |
|---|---|
| `name` | upper case identifier: the JavaScript variable name and the key of the saved value |
| `row_type` | how the row behaves, see below |
| `label.en` / `label.fi` | text printed in the first cell |
| `unit` | unit of the value: `kg`, `ltr`, `min` |
| `default` | value used when the user has not saved anything |
| `min` | smallest accepted value |
| `max` | largest accepted value |
| `show_max` | whether the max is printed in the row description (`(max 150 kg)`) |
| `moment_arm` | arm in metres from the datum, 0 for rows that are not a mass |
| `step` | slider step, interactive rows only, omitted when there is none |
| `save` | the value is stored in the browser and appears in `save_settings()` |

### row_type

| row_type | row | save |
|---|---|---|
| `interactive` | slider row, the user enters a value | yes |
| `fuel_flow` | interactive row that also drives the endurance calculation | yes |
| `checkbox` | interactive checkbox row, ON when max equals default | yes |
| `computed` | non-interactive row, the value is calculated | no |
| `computed_reversed` | non-interactive row with the result and the value cells swapped | no |

## Fixed names

These names have fixed positions in the calculation chains: `BASIC_WEIGHT`, `FRONT_SEAT`,
`FUEL`, `BAGGAGE`, `TAXI_FUEL`, `TOW`, `LNDW`, `ENDURANCE`, `FUEL_FLOW`, `FLIGHT_TIME`.
Any other load point is extra equipment and is added to the mass and moment sums by the
extras loop.

## Conventions

- `max` is always positive. `show_max` says whether the limit is printed in the row
  description; the page code tests `max > 0`, so the template passes a negative max when
  `show_max` is false.
- Load point names stay upper case: they are JavaScript identifiers and the keys of the
  saved values.
- `step` is omitted when a row has no step.

## Adding an aircraft

Copy `oh-example.json`, edit the values, set `publish` to `true` and run the build
script. `oh-example.json` exercises every row type, so it is the best starting point.
Specs with `publish` false (or missing) are skipped by `build.sh`, so a spec can be
kept in the repository without publishing its sheet.

## Example

```json
{
  "registration": "OH-EXMPL",
  "aircraft_type": "Cessna C172M",
  "data_source": "Numbers: Reliable source 01.01.1970",
  "fuel_density_kg_per_l": 0.721,
  "publish": false,
  "envelope": {
    "moment_arms": [0.89, 0.89, 0.977, 1.202, 1.202, 0.89],
    "takeoff_mass_limits": [680, 885, 1156, 1156, 680, 680],
    "landing_mass_limits": [680, 885, 1156, 1156, 680, 680],
    "landing_limit_arm_start": 0.85,
    "landing_limit_arm_end": 1.202,
    "moment_axis_max": 475,
    "mass_axis_max": 375,
    "chart_x_offset": 50
  },
  "load_points": [
    {
      "name": "BASIC_WEIGHT",
      "row_type": "computed_reversed",
      "label": {"en": "Basic weight", "fi": "Perusmassa"},
      "unit": "kg",
      "default": 697.5,
      "min": 0,
      "max": 1,
      "show_max": false,
      "moment_arm": 0.97,
      "save": false
    },
    {
      "name": "FUEL",
      "row_type": "interactive",
      "label": {"en": "Fuel", "fi": "Polttoaine"},
      "unit": "ltr",
      "default": 143,
      "min": 0,
      "max": 143,
      "show_max": true,
      "moment_arm": 1.17,
      "step": 0.1,
      "save": true
    },
    {
      "name": "FAIRINGS",
      "row_type": "checkbox",
      "label": {"en": "Wheel fairings", "fi": "Renkaiden muotosuojat"},
      "unit": "kg",
      "default": 0,
      "min": -3.75,
      "max": 0,
      "show_max": false,
      "moment_arm": 2.24,
      "save": true
    }
  ]
}
```
