# CatBadge v8.7 — closed back and reinforced snap rim

V8.7 responds to a physical print reported as flimsy and difficult to snap together satisfactorily. The printed version and slicer settings have not been confirmed, so this is a geometry revision with fit trials, not a diagnosis of the printer.

## Changes

- Close the six rear vent slots and the large rear ear windows. Battery access, UART, QWIIC, lanyard and the existing side service openings remain available. A continuous rear border ties the center section to the ears beneath the side-access header cutouts.
- Increase the main rear panel from **1.6 to 2.4 mm**, outward from the board. Its inner face remains at Z=-8 mm, preserving the existing rear component clearance.
- Increase the overlapping faceplate tongue from **1.15 to 1.4 mm nominal thickness** and widen all four catches from **5 to 8 mm**.
- Select **0.35 mm engagement**, with 0.25, 0.35 and 0.45 mm print-first trials. Preserve the 0.30 mm nominal mating gap. Widen the matching tray pockets and move the release notches clear of the wider catches.
- Move the battery cover and its mating tabs/slots/latch interface outward **0.8 mm** for the thicker rear panel. Cover shape, independent sliding access and the loaded-holder envelope are retained.
- Retain the v8.4 exterior finishing, beveled caps, 52.5 x 40 mm screen opening, LED slots, open SAO and rear outer-ear antenna port.

The catches remain opposed ramped detents, designed to release through outward rim flex. A more substantial rim, wider engagement and a closed rear panel are intended to improve feel; no physical retention force, stiffness or cycle-life claim follows from the CAD checks. These are not square permanent locking hooks.

**Print the v8.7 faceplate, rear tray and battery cover as a matched set.** Earlier shells are not the fit target. V8.4 button caps retain their geometry and may be reused if their sockets already fit gently.

## Downloads and orientation

- `CatBadge-v8.7-COMBINED-CLOSED-BACK.3mf`: default faceplate with original spring-antenna access, rear tray, battery cover and six 3.2 mm TRIAL socket caps.
- `CatBadge-v8.7-COMBINED-CLOSED-BACK-NO-SPRING-ONLY.3mf`: alternative faceplate; use only if the original spring antenna is absent. SAO remains open.
- **`PRINT_FIRST_v8.7_Snap_Only.3mf`**: three engagement trial lids and their shared tray coupon; start here.
- `PRINT_FIRST_v8.7_Fit_and_Comfort.3mf`: 16 objects, including three rim-fit trials, shared tray coupon, battery latch pair, four socket trials, front-button coupon, LED/SAO and screen checks, finishing samples and a closed rear-ear sample.
- `PRINT_FIRST_v8.7_Comfort_Only.3mf`: the three finishing samples.

Individual STL and 3MF files are in `parts/` and `tests/`. Each complete kit has nine named objects in a nominal 220 x 220 mm layout before brims. All units are millimeters. These are geometry-only 3MFs, without a printer profile or G-code.

Keep the exported orientations: faceplate and caps face down; rear tray and cover exterior down. The exported geometry is checked with a 0.2 mm layer / 45-degree support envelope. Inspect the actual sliced paths and any local bridges before printing.

## PLA+ print and fit trial

With a **0.4 mm nozzle**, a starting trial is **0.20 mm layers, four walls/perimeters, and six top/bottom layers**, using the filament maker's temperature range. This is a suggested trial, not a verified Anker/eufy profile. The 1.4 mm tongue may resolve into fewer than four extrusion lines; inspect the preview for filled, continuous material rather than relying on the wall-count setting alone. Shell walls matter more than simply increasing infill.

1. Print the shared rim tray and 0.25 mm engagement lid first. Compare the 0.35 mm trial if the first is loose. Use 0.45 mm only as a comparison after the gentler trials; do not force a tight joint.
2. Confirm that the coupon seats fully, has useful retention and releases through the notch. Gaps between extrusion lines, split layers, whitening or cracks are failed results.
3. Check repeated gentle opening/closing; twenty cycles can be an initial screening test, not lifetime qualification. The cropped coupon has different stiffness from the complete perimeter.
4. Check both empty v8.7 shell halves before fitting electronics. The combined file uses the middle 0.35 mm trial. Test the shifted battery cover and latch separately.
5. For untested cap sockets, start at 3.3 mm and work downward to a gentle fit. The combined kit's 3.2 mm socket remains provisional.

If the halves cannot seat, check for first-layer spread, an unseated PCB/cap, misplaced antenna cable or tight engagement. If a fully seated seam barely retains, compare the next engagement coupon. If the printed rim itself separates along layers or shows gaps, check extrusion and layer bonding before increasing engagement. Do not use screws, glue or force to overcome a mismatch.

## Assembly and reopening

Remove power. Fit the antenna adapter with its real metal nut and route its cable clear of the board seat, rim and battery-cover path. Check the newly enclosed rear-ear area: it retains 8 mm nominal rear clearance, but the actual adapter body, U.FL lead bend and other components are not fully modeled. Keep the existing side connector and top UART/QWIIC paths clear.

Seat the PCB and gently fitted caps, align the faceplate, then seat the perimeter next to the catches. Do not press on the screen or switches. Use a thin plastic pick in the exterior notches to ease the outer faceplate rim outward and lift it away, releasing catches progressively. Stop if the rim needs force or shows stress damage.

The digital release path prescribes up to 0.55 mm local outward displacement for the selected 0.35 mm engagement, then checks separation. This is a collision model, not a measured deflection limit or force recommendation.

To open the battery cover, press its bottom-edge latch toward the badge center, slide 3.2 mm toward assembly +X (right viewed from the front), and lift away from the rear. Install in reverse. The main case can stay closed.

Button flanges prevent outward escape while assembled; caps can still exit the rear of a removed faceplate. No extra keeper plate or case screws are required.

## Dimensions and validation limits

- Width: approximately **147.96 mm**, unchanged.
- Main shell depth: **23.2 mm**; over the battery cover: **31.5 mm**; including button faces: **32.0 mm**. The 0.8 mm increase buys rear-panel thickness while preserving electronics clearance.
- Faceplate skin remains 1.6 mm. Screen opening remains **52.5 x 40 mm**, with right edge X=26.46 and left edge X=-26.04.
- Measured loaded holder: **15.7 high x 32.7 wide x 59.7 long mm**. Its assumed top remains at the PCB underside; leads and mounting offsets require a real fit check.
- The antenna bore remains a **6.5 mm trial** with a 2.4 mm clamping land; exact adapter fit is unverified.

`validation.json` reloads 20 unique printable solids, verifies STL/3MF surfaces and kits, and checks assembly, PCB seat, service access, button motion, rim engagement/release and battery-cover travel. Revision checks prove former vent/ear closure, increased engagement geometry, the cover translation and retained button geometry. They do not measure snap force or structural stiffness. `overhangs.json` checks 0.2 mm layers with 0.205 mm lateral growth and at most 0.025 mm² residual per layer.

The user has reported poor fit/feel on an earlier print; its exact version and settings are not yet confirmed. **V8.7 is unprinted and physically unverified.** Mesh/render checks do not establish thermal, drop, fatigue, connector or full electronic-assembly performance.

## Rebuild

From the local design repository, with its Python environment and OpenSCAD installed:

```sh
bash rebuild.sh v8.7
```

From the extracted ZIP, use Python 3.12, the dependencies in `requirements-resolved.txt`, and OpenSCAD on PATH:

```sh
python source/generate_v87.py --coupons
python source/validate_snaps.py
python source/check_overhangs.py --coupons
python source/generate_v87.py
python source/validate_v87.py --standalone
python source/check_overhangs.py
python source/render_v87.py
```

`generate_v87.py` is the entry point; earlier generators are geometry helpers. All previews are generated from exported meshes; PCB display geometry is only a simplified reference. The package contains source, parameters, parts, coupons, previews and reports. CRC and per-file SHA-256 checks verify the ZIP; download checksums are in `SHA256SUMS`.

## References and credit

- [RetiaLLC/DefconBadge2026](https://github.com/RetiaLLC/DefconBadge2026): original hardware and PCB outline. Independent enclosure; upstream design credit remains with its designers.
- [Protolabs snap-fit guidance](https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/): local flexibility, width, strain, build orientation and fit iteration; printed tolerances are not universal.
- [Prusa layers and perimeters](https://help.prusa3d.com/article/layers-and-perimeters_1748): shell thickness and perimeter settings affect strength. The suggested PLA+ profile above still needs a coupon test.
- [Prusa modeling guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135): orientation, chamfers and tolerances.
- Supplied Cynthion case: earlier rim/catch reference only; original meshes are not redistributed.
