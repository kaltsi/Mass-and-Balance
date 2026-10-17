# Spec files

Every aircraft has two files in this directory:

- `<registration>.specs` - the human editable source
- `<registration>.json` - the form the generator reads

The JSON is generated from the `.specs` file, so the JSON is what should be edited only
if the `.specs` file is not kept. Keys are written in reading order: the aircraft
identity, then the chart geometry (`envelope`), then the load points. A key that is not
set falls back to the default written in the template.

## Key names

The `.specs` files use upper case names; the JSON uses readable lower case keys:

| .specs | JSON |
|---|---|
| `ACFT` | `registration` |
| `ACFT_TYPE` | `aircraft_type` |
| `DATA_ORIGIN` | `data_source` |
| `LITRE2KILO` | `fuel_density_kg_per_l` |
| `MOMENT_ARMS` | `envelope.moment_arms` |
| `TOF_MASS_LIMITS` | `envelope.takeoff_mass_limits` |
| `LND_MASS_LIMITS` | `envelope.landing_mass_limits` |
| `MOM_DRAW_MAX` | `envelope.moment_axis_max` |
| `MASS_DRAW_MAX` | `envelope.mass_axis_max` |
| `TRANSLATE_X` | `envelope.chart_x_offset` |
| `LND_LIMIT_X1` | `envelope.landing_limit_arm_start` |
| `LND_LIMIT_X2` | `envelope.landing_limit_arm_end` |
| `INVALID_DATA` | `invalid_data` |
| `LOAD_POINTS` | `load_points` |

In a `.specs` file a load point line is `LP_<type>_<NAME> "English" "Finnish" "unit" default min max arm [step]`,
where the type letter becomes `row_type` and the rest of the name becomes `name`.

## Top level keys

| key | type | meaning | template default |
|---|---|---|---|
| `registration` | string | aircraft registration, the sheet title and the output file name | `OH-DEMO` |
| `aircraft_type` | string | type printed under the title | `Generic A000-Z` |
| `data_source` | string | where the numbers come from, printed in the sheet | `Mass and balance sheet for OH-DEMO 01.01.1970` |
| `fuel_density_kg_per_l` | number | fuel mass per litre (Avgas 0.721) | `0.721` |
| `envelope` | object | chart geometry, see below | |
| `invalid_data` | string | CSS visibility for the INVALID text on the chart, `hidden` or `visible` | `hidden` |
| `load_points` | array | the table rows, in the order they are printed | |

## envelope

The chart is drawn from six polygon points: moment arms on the x axis, mass on the y
axis. The takeoff polygon uses `takeoff_mass_limits`, the landing polygon uses
`landing_mass_limits`.

| key | meaning | template default |
|---|---|---|
| `moment_arms` | x of the six polygon points, m from the datum | `0.787, 0.787, 0.821, 0.925, 0.925, 0.787` |
| `takeoff_mass_limits` | y of the polygon points, kg | `450, 612, 757, 757, 450, 450` |
| `landing_mass_limits` | y of the landing polygon, kg | `450, 612, 700, 700, 450, 450` |
| `landing_limit_arm_start` | x where the landing limit line starts, m | `0.8075` |
| `landing_limit_arm_end` | x where the landing limit line ends, m | `0.925` |
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
| `checkbox` | interactive checkbox row | yes |
| `computed` | non-interactive row, the value is calculated | no |
| `computed_reversed` | non-interactive row with the result and the value cells swapped | no |

In the `.specs` files the row type is the `LP_<letter>_` prefix: `I`, `F`, `C`, `N`, `R`.

## Fixed names

These names have fixed positions in the calculation chains: `BASIC_WEIGHT`, `FRONT_SEAT`,
`FUEL`, `BAGGAGE`, `TAXI_FUEL`, `TOW`, `LNDW`, `ENDURANCE`, `FUEL_FLOW`, `FLIGHT_TIME`.
Any other load point is extra equipment and is added to the mass and moment sums by the
extras loop.

## Conventions

- A negative max in a `.specs` file means "do not print the limit". In the JSON the max is
  positive and `show_max` is false. The template re-encodes the sign when it calls
  `l_point()`, because the page code tests `max > 0`.
- Load point names stay upper case: they are JavaScript identifiers and the keys of the
  saved values.
- `step` is omitted when the spec has no step, `invalid_data` only when it is uncommented
  in the `.specs` file.

## Example

`oh-example.specs` and `oh-example.json` exercise every row type:

```json
{
  "registration": "OH-EXMPL",
  "aircraft_type": "Cessna C172M",
  "data_source": "Numbers: Reliable source 01.01.1970",
  "fuel_density_kg_per_l": 0.721,
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
