# Control descriptions

Use the [IOF specification](https://orienteering.sport/iof/rules/control-descriptions/). The edition checked for this kit is 2024. Check for updates before a new session.

Print symbols and the grid in black. Use square cells from 5 to 7 mm; this kit uses 7 mm. Keep branding outside the table. Use eight columns:

| Column | Content |
|---|---|
| A | Control number |
| B | Control code |
| C | Which feature |
| D | Feature |
| E | Appearance or second feature |
| F | Dimensions, combination or bend |
| G | Flag position |
| H | Other information |

Include the event name, course code, distance, start row and finish-route instruction. Round the header distance to 0.1 km. Add climb only when measured. Use a heavier line after every third control and around route instructions. Junctions and crossings require both features in D and E, with the combination symbol in F.

Match the actual map feature. Closed contours use **hill (1.9)**; a small point-symbol knoll uses **knoll (1.10)**. Do not add “top” to a hill when that is the default position. Distinguish a thicket side from an areal edge. A vegetation-boundary site needs an identifiable boundary on the ground. Confirm uncertain sites before use; descriptions cannot repair the map.

The finish instruction describes the actual marking: fully taped (16.1), navigate to a taped finish section (16.2), or no tapes (16.3). Its distance is the final leg, not the course total. Do not claim the whole finish route is taped when only the access path is marked.

## Build

Add reviewed `iof` fields to each point, including S:

```json
"iof": {"D": "5.2", "E": "5.2", "F": "10.2"}
```

Add `finish_distance_m` to every course and a session setting:

```json
"descriptions": {"start_taped_m": 30, "finish_symbol": "16.2"}
```

Omit `start_taped_m` when there is no marked route from the start. Course `climb_m` is optional. Use measured distances and explain training route estimates in the host notes.

```sh
python3 scripts/descriptions.py path/to/session.json --outdir build
```

The script makes separate LaTeX strips and an all-controls table. Its TikZ symbol set is deliberately small. Unsupported symbols fail; add and visually check the correct IOF drawing before using a new feature. It does not infer descriptions from coordinates. Keep the generated `.tex` with the session sources. Rebuild after any control or sequence change, then inspect every page at print size.
