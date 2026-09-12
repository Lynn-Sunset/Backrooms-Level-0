# Model and rendering checks — realism pass, 2026-09-12

All six GLBs pass `scripts/validate-models.py`. `validation.json` records counts,
triangle and size budgets, embedded resources, normal maps, UVs, unit normals,
finite geometry and zero degenerate triangles. The bottle also passes a physical
glass transmission check. The assets contain 21 normal-mapped materials in total.

| Asset | Triangles | Material meshes | Size, MiB |
| --- | ---: | ---: | ---: |
| Pavilion | 83,900 | 12 | 12.91 |
| Almond water | 13,408 | 6 | 1.19 |
| Walnut door | 9,356 | 7 | 5.38 |
| Industrial door | 13,972 | 9 | 1.03 |
| Fluorescent fixture | 6,028 | 5 | 0.80 |
| Column | 2,804 | 2 | 2.04 |

The Blender sources now include tileable PBR surfaces, physical-scale UVs,
manufactured edges, ornate joinery, detailed hardware and a glass inner wall.
The pavilion has carved braces, lotus bases, stone inlays and a geometric CJK
nameboard. Its steps no longer contain overlapping coplanar tread caps. Object
transforms are baked after material grouping to preserve accurate runtime bounds.

All six final GLBs were imported back into Blender 5.2.1 LTS and rendered with
Cycles at 48 samples. The PNGs show each asset, including the fixture underside;
`pavilion-detail.png` shows the carving and paving. `before-realism/` retains the
preceding renders and validation report. Visual inspection led to corrections
for stretched platform UVs, excessive patina and tiny screw bevels.

The browser archive was inspected for the pavilion, walnut door and bottle.
The three game levels all loaded six models on Ultra at pixel ratio 2, with three
exits and the expected supply counts (2/4/4). The pavilion, resized pickup and
industrial exit were inspected in their actual environments. Completed scene
loads reported no browser warnings or JavaScript errors.

Two new garden layouts contained 6 and 2 pavilions. The real movement function
completed 44 and 13 perimeter/doorway routes respectively: **57 passed, 0 failed**.
One automation wait expired during a heavier scene build; the resulting scene
finished loading normally and its route results were inspected afterward.
The six existing gameplay regression tests also passed, including camera drift
and native-resolution checks. No depth-of-field or afterimage pass was active.

All six Godot copies match the web GLBs by SHA-256. The Godot runtime was not
exercised. JavaScript syntax checks and `git diff --check` passed.

The in-app browser cannot capture the mouse for a full first-person playthrough.
Camera feedback is covered by the regression tests; scene loads and route checks
do not require pointer lock. Texture downloads and physical transmission add
rendering cost, so these checks do not imply a frame-rate guarantee. Static
meshes still share materials and are batched spatially for frustum culling.
