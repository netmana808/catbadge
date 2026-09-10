# CatBadge v8.7b — taller replacement buttons

Replacement buttons for the **existing v8.7 faceplate**, including its NO-SPRING-ONLY variant. No front, back, cover or keeper plate needs to be printed. Compatible by geometry with the v8.7a rear derivative. The printed front's exact version and button fit symptoms remain unconfirmed; these are physical fit trials.

- **[Print-first six-button fit comparison](PRINT_FIRST_v8.7b_Button_Fit_Trials.3mf)**
- **[Six matching buttons: 10.2 mm guide / 3.2 mm socket](CatBadge-v8.7b-SIX-cap_G10p2_S3p2_PLUS1mm.3mf)** — provisional default; choose after testing
- [Actual mesh comparison](preview/button-comparison.png)
- [Trial-plate identification map](preview/fit-trial-layout.png)
- [Validation report](validation.json)

## Changes and retained interfaces

The face extends **1.0 mm farther outward**, increasing nominal protrusion from **0.5 to 1.5 mm** above the local faceplate. The old cap's actual assembly top is Z=13.3 mm and the new one is Z=14.3 mm; the faceplate is Z=12.8 mm. An earlier generator default of Z=13.7 was superseded by v8.1 and is not the v8.7 export height.

The main trial increases guide diameter from **10.0 to 10.2 mm** inside the unchanged 10.6 mm guide bore. Nominal radial clearance reduces from 0.30 to 0.20 mm, intended to reduce side play. A 10.3 mm comparison offers 0.15 mm radial clearance. Smaller clearance can bind on an imperfect print; use the trial that moves freely rather than selecting the largest by default.

The 0.3 mm top bevel is retained. The flange transition remains 45 degrees for face-down printing. Socket roof/contact height stays at Z=6.8 mm; socket depth remains 1.5 mm, boss diameter 4.8 mm, entry chamfer unchanged. The retaining flange remains 11.4 mm diameter at Z=9.8–10.8 mm. The taller exposed end does not extend the socket toward the board. Actual switch preload, permissible stroke, return and socket grip still require checking on the real badge.

The existing flange prevents outward escape; these buttons can still fall out through the rear of a removed faceplate. No new latch or interference-fit retention is claimed.

## Fit trial

The comparison plate contains six separate caps. G identifies the faceplate guide diameter; S identifies the socket bore diameter. Both are CAD dimensions in millimeters.

| Position in supplied plate, viewed from above | Guide | Socket | Purpose |
| --- | ---: | ---: | --- |
| Front/lower row, left | 10.0 | 3.2 | Original guide diameter with new height |
| Front/lower row, middle | 10.2 | 3.2 | Main reduced-play trial |
| Front/lower row, right | 10.3 | 3.2 | Closer guide trial |
| Back/upper row, left | 10.2 | 3.3 | Looser socket trial |
| Back/upper row, middle | 10.2 | 3.1 | Smaller socket trial |
| Back/upper row, right | 10.2 | 3.0 | Smallest socket trial |

The slicer object names retain these dimensions. Keep them in order after removal; no tiny embossed identifiers were added to the sliding or contact surfaces. Auto-arranging changes the map, so use object names if rearranged.

1. Print at 100% scale with the exported **button faces down / sockets up** orientation. Use 0.20 mm layers and a 0.4 mm nozzle, with supports off. Use settings suitable for your material; there is no material profile or G-code embedded in these geometry-only 3MFs. Inspect first-layer spread and socket paths in the slicer.
2. Allow cooling and remove brim remnants without rounding the guide or filling the socket. Test each guide in the removed faceplate before installing it on a board. It must move freely without scraping or sticking. Compare all six locations in the actual front.
3. With power removed, start socket testing at 3.3 mm if the existing size is unknown, then work downward only to a gentle fit. Do not force the cap onto a switch. These separate trials distinguish faceplate clearance from socket grip.
4. Once assembled, verify every button releases and the switches are not held down at rest. The numerical collision offsets in the report are not permission to depress the real switch by that amount. A cap that only works when forced, sanded heavily or pressed against a stressed switch is a failed fit.
5. Use the matching `CatBadge-v8.7b-SIX-...` file for the selected combination. Six-piece files exist for each of the six tested combinations. Individual STL/3MF pairs are in `parts/`. If the best guide and socket require an unprovided combination, generate that combination and rerun the checks before printing a set.

The existing v8.7 combined case kit still contains its original caps. These button-only files are a separate replacement, not an updated full-case kit. If the original guide already sticks, neither the 10.2 nor 10.3 trial is a corrective recommendation; provide that result before shrinking a new guide variant.

## Verification and rebuilding

The standalone source uses the existing NumPy/Trimesh/Shapely/Manifold pipeline. Included reference meshes are untouched v8.7 faceplate variants and socket-cap exports, with hashes recorded in `validation.json`. Their upstream case/PCB attribution remains RetiaLLC/DefconBadge2026; this is an independent enclosure prototype.

From the public checkout: `bash rebuild.sh v8.7b`. From an extracted package, install `source/requirements.txt` in a local virtual environment, then run `python source/build.py` and `python source/render.py`. These produce geometry and reports only.

Validation reloads six printable STL/3MF pairs, checks single watertight solids, positive volume, names, millimeter units and matching bounds/volume. It checks retained socket/flange sections against each original socket size, the 1 mm height change, support envelopes at 0.2 mm layers, adjacent-button clearance, **648 cap/faceplate motion cases** and **72 flange-stop cases**. The collision tests include both faceplate variants, all six positions and ±0.1 mm lateral offsets at rest. A nonintersecting CAD assembly does not establish low friction, low wobble, switch return or manufactured fit. No print or actual slicer toolpath validation has occurred.
