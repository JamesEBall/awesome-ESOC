# Session data

The renderer uses plain JSON. All map coordinates are in the source's projected CRS, in metres. Do not put longitude/latitude values in these fields.

Required fields:

- `title`, `author`, optional `max_total_m`.
- `map`: `file` (relative PNG path), `bounds` `[west,south,east,north]`, `scale`, `x_mm`, `y_mm`, `orientation`.
- `points`: keyed by code. Each has `xy`, `description`, `label_offset_mm`.
- `courses`: keyed by course code. Each has `controls` (ordered code strings), `distance_m`, `distance_basis`.
- `packs`: objects with `file` (PDF basename), `title`, `courses`, and optional `mode`.
- `copyright`: short credit lines.

For the supplied shared-base layout, `S` is the combined start/finish and `J` is the end of an optional marked access path. `access` contains its projected coordinates from S to J. J is an internal geometry key; it is not labelled on the map. If there is no access path, put J at S and use an empty `access` list.

Modes: `normal` (ordered course), `all` (all controls), `score` (codes without lines), `blank` (base map only). All/blank packs can have an empty course list. A score course supplies its selected codes.

For a score course, omit `distance_m` or use `null`: there is no fixed route length. Write its time limit, points and late rule on a separate host sheet. Normal courses require a positive measured distance.

The example uses A4 landscape, 8 mm margins and 1:2,000. That gives a crop 562 m wide by 388 m high. Other scales must use the same physical-to-ground calculation: ground metres = printed millimetres × scale / 1,000. Never stretch a crop to fit a page.

Distances are supplied by the planner. The renderer checks the stated cap; it does not prove a route is passable. Keep measured route geometry and the measurement method with each real session. The Ravelston example includes `route-audit.json` in the private download, not the public repository.

Build:

```sh
python3 scripts/build.py path/to/session.json --outdir build
```

Read an OCD map (optional converter dependencies):

```sh
npm ci
node scripts/render-map.cjs input.ocd path/to/session.json output/map.png
```

The converter also writes a small `.info.json` with source scale and CRS. Inspect the resulting image before choosing controls. It cannot perform a ground check.

Optional `map.exclude_objects` is an array of original OCD object indices, matching GeoJSON `properties.objectIndex`. Inspect these objects first. Use this only for verified titles, layout borders or legends that clash with the new layout. It filters an in-memory copy; it does not edit the OCD. Never remove restrictions, terrain or north lines this way. Keep original attribution in `copyright`.

The corner key, scale bar and credit strip have default positions. If they obscure needed terrain, move their TikZ positions in the generated `.tex` and recompile. Review the result at print size.

Any `.tex` host sheets beside the session JSON are copied and compiled with the map sheets. Keep their lists in sync with the JSON.

A reusable one-page host sheet is in `templates/host.tex`. Copy it beside the session JSON, edit its title, author and notes, then build.
