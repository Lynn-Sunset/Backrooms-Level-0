# Backrooms

A Three.js exploration game with three procedural environments: the yellow rooms,
an industrial warehouse, and a night garden. The existing Chinese game interface
and gameplay are preserved.

## Run locally

```sh
node server.js
```

Open [the game](http://localhost:8000/) or the [interactive model archive](http://localhost:8000/model-viewer.html).
The server uses port 8000 unless `PORT` is set. Three.js and the optional leaderboard
SDK load from their existing CDNs, so the browser needs an internet connection.

Use WASD to move, the mouse to look, Shift to sprint, Space to jump, and Escape to
pause. The start screen includes automatic and manual graphics settings. Auto
starts desktop browsers at High and reduces rendering cost if frame times worsen.
Ultra renders at native display density and retains SSAO, bloom and warehouse
reflections. Depth-of-field blur and sprint afterimages are disabled in gameplay.
Use a regular Chrome or Edge window for gameplay: the Codex in-app browser can
render the scenes and model archive, but rejects first-person pointer capture.

## Models

All six GLBs have been rebuilt with a reproducible Blender pipeline. Textures are
embedded; the assets are also copied into `godot/BackroomsGodot/assets/models/`.
The Godot project remains a separate prototype; the browser game is the main entry
point.

| Asset | Details | Triangles |
| --- | --- | ---: |
| Garden pavilion | Carved corbels, lotus bases, patterned paving, scalloped tile ends, bronze accents and a 听雨亭 plaque | 83,900 |
| Almond water | Inner glass wall, physical refraction, liquid meniscus, paper relief, cap emblem and tamper bridges | 13,408 |
| Walnut door | Ogee molding, brass stringing, directional grain, patina and slotted hardware | 9,356 |
| Industrial door | Coating relief, brushed metal, wired glazing, stamped seams, articulated closers and panic hardware | 13,972 |
| Fluorescent fixture | Folded reflectors, ballast cover, endcaps, pins, sockets, wiring and service clips | 6,028 |
| Fluted column | Carved shaft, stone molding, mineral variation and fine limestone pores | 2,804 |

The archive supports orbit, zoom, pan, wireframe, automatic rotation, resetting the
camera and downloading the actual in-game GLBs. Asset dimensions use metres.
The bottle asset is approximately 22 cm tall, with a modest enlargement for
pickup visibility in the game. Pavilions still fit the protected circulation
space automatically.

Surfaces use deterministic 512–1024 px base-color, roughness and tangent-space
normal maps; bronze also includes a metallic map. Timber UVs follow each member,
and stone uses physical-scale projection. Joined meshes have their transforms
baked to keep runtime bounds accurate. Each asset remains at 12 material meshes
or fewer, with explicit triangle and download-size budgets.

## Rebuild and validate

The exports were built and rendered with Blender 5.2.1 LTS. NumPy is supplied by
Blender; no Python packages are needed for normal asset builds.

```sh
blender --background --factory-startup --python-exit-code 1 --python blender/build_assets.py
python scripts/validate-models.py
node --test scripts/gameplay.test.mjs
blender --background --factory-startup --python-exit-code 1 --python blender/render_preview.py
```

Append `-- almond_water` (or another asset name) to either Blender command to work
on one model. The original `blender/export_models.py` and
`blender/export_pavilion.py` entry points use the same pipeline.
Use `-- pavilion --detail` with the preview script for a close view of the
pavilion's carving and paving. The Chinese nameboard is converted to geometry;
builds without the Windows CJK font use an English nameboard.

The bottle label is included in `blender/textures/almond_label.png`; to edit and
regenerate it, use `python blender/generate_label.py` with Pillow installed.
After rebuilding models, copy the six GLBs from `models/` to the Godot model folder
if you use that prototype.

Validation checks binary bounds, embedded textures, triangle indices, finite
geometry, unit normals, UV availability, degenerate triangles, and model budgets.
It also checks relief textures and physical glass transmission.
Results and rendered previews are written to `artifacts/model-quality/`.
The earlier preview images are retained in `artifacts/model-quality/before-realism/`.

## Visual checks

The game supports `?shot=1&level=0` (levels 0–2), optionally with `&view=exit`,
`&view=pickup`, or `&view=pavilion` (garden). Append `&quality=high`, `medium`, `low`, or `ultra` to inspect a
particular pipeline. Screenshot mode holds its quality setting steady and does
not save leaderboard records. It logs `[SHOT] READY` and exposes readiness and
render statistics on the document body's `data-*` attributes.
`data-pavilion-routes` reports movement checks around every generated pavilion
and through its room's open doorways, using the actual collision grid.

The rendering changes fix reciprocal FXAA resolution, reduce bloom and colour
fringing, preserve prop proportions, orient door fronts into rooms, dispose
replaced postprocessing passes, and batch static meshes by area and compatible
attributes. Garden rocks share displaced vertices; bamboo uses attached curved
leaf blades instead of cones.
Exit placement reserves a clear approach through the collision map, and supplies
are moved away from obstructing props.
Pavilions stay centered with at least 1.29 m of circulation space in garden rooms;
their solid raised platforms and steps use a convex footprint, excluding roofs.
Landing feedback is a short vertical dip applied only while rendering, so it
cannot accumulate camera tilt or affect jump physics.
