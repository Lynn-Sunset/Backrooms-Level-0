# Gameplay regression checks — 2026-09-12

## Changes

- Garden pavilions are centered and fitted using their actual horizontal radius,
  including stairs and roof corners. Garden rooms retain at least 1.29 m between
  the fitted radius and the inner wall. The collision polygon follows geometry
  below player height, keeping the raised platform solid without blocking the
  empty corners of the old oversized box.
- Landing feedback is a bounded vertical dip applied only during rendering.
  Camera rotation is never changed, and the physics position is restored even
  if rendering throws. New jumps and level transitions clear the feedback.
- Removed autofocus depth of field and sprint afterimages. Ultra uses native
  display density; Auto keeps its existing adaptive resolution behavior. SSAO,
  bloom and Ultra warehouse reflections remain available.

## Results

`node --test scripts/gameplay.test.mjs`: **6 passed, 0 failed**.

Coverage includes 360 pavilion rotations, platform and stair collision edges,
ordinary walls, 100 repeated landings at each of 5/30/60/144 fps with unchanged
camera orientation and position, render-failure cleanup, resets, and display
densities from 1 to 3.

Browser checks used the actual game and its movement/collision grid:

| Garden layout | Pavilions | Perimeter / doorway routes | Failures |
| --- | ---: | ---: | ---: |
| 1 | 4 | 24 | 0 |
| 2 | 2 | 12 | 0 |
| 3 | 4 | 26 | 0 |
| 4 | 4 | 26 | 0 |
| 5 | 6 | 40 | 0 |
| Total | 20 | 128 | 0 |

All three levels loaded all six models on Ultra. Their active postprocessing
passes contained no BokehPass or AfterimagePass. At a 1280 × 720 CSS viewport
on a display with density 2, High rendered at 1920 × 1080 and switching to Ultra
restored 2560 × 1440. No browser warnings or errors were reported.

The pavilion was visually inspected in the garden. JavaScript syntax checks and
`git diff --check` passed. Pointer-locked manual jump testing remains unavailable
in the Codex in-app browser; landing feedback was exercised by the automated
tests, and route checks invoked the actual movement function without pointer lock.

To repeat route checks, open `/?shot=1&level=2&quality=ultra&view=pavilion` and
read the document body's `data-pavilion-routes` attribute. Each reload generates
a new maze. Refresh the normal game to load the fixes and generate new placements.
