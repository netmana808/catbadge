# CatBadge v8.7a — rear tray with removable adhesion pads

Back-only reprint trial for the report that both rear ears lifted off the bed. This is the v8.7 rear tray with four sacrificial bed pads; the original case geometry is preserved within export precision. Use with the existing **v8.7** front and battery cover. Compatibility with other versions is not established, and the reported failed print file is not confirmed.

- [Rear tray 3MF](parts/CatBadge-v8.7a-Rear-Tray-Adhesion-Tabs.3mf)
- [Rear tray STL](parts/CatBadge-v8.7a-Rear-Tray-Adhesion-Tabs.stl)
- [Print-first ear/pad removal coupon](tests/PRINT_FIRST_v8.7a_Ear_Pad_Removal.3mf)
- [Bed-contact preview](preview/bed-contact.png)
- [Digital validation](validation.json)

## What changed

Two 24 mm diameter pads overlap the ear tips; two 20 mm pads overlap the lower outside corners. All are 0.40 mm tall and join the case directly at bed level. They add approximately 1,434 mm² of first-layer contact and 572 mm³ of material. The complete print envelope is 154 × 112 × 12.2 mm, or at most 170 × 128 mm including an 8 mm brim.

These are removable adhesion aids, not permanent case extensions or overhang supports. The 2.4 mm rear floor, snap rim, PCB seat, antenna port, battery opening and cover interfaces retain the v8.7 geometry. Do not thicken the floor or add internal ribs for this trial: those require electronics-clearance review and would not directly anchor the ear tips.

The pads target corner lifting but do not guarantee a warp-free print. The cause of this print's lifting remains unconfirmed. [Prusa's warping guidance](https://help.prusa3d.com/article/warping_2011) recommends a brim and, for persistent local lifting, small removable cylinders a few layers tall. The particular dimensions here are a design trial, not a manufacturer-validated M5C recipe.

## Reprint

1. Print the small coupon first to check first-layer contact and pad trimming. It is a cropped real ear tip with its pad and 2.4 mm floor. It does not predict full-case thermal warping or test the snaps.
2. Import the rear **by itself**, at 100% scale. Keep its exterior flat face and all four pads on the bed, open interior facing up. Center it on the plate.
3. For an M5C with compatible PETG, the proposed adhesion trial is 0.20 mm first/subsequent layers, four walls, 20 mm/s first layer, 240°C nozzle / 80°C bed, 8 mm outer brim with zero gap. Supports stay off. The 3MF contains geometry only; enter settings in your slicer. See the public repository PRINTING.md for context.
4. In the sliced preview, check that each pad touches the case and prints for two layers, and that the brim joins the exterior/pads. No slicing or printer job was performed during this CAD change. Keep direct AC/fan drafts away and prepare the actual plate surface appropriately; its coating remains unconfirmed.
5. Let the print and plate cool. Support each ear while carefully trimming the thin pads flush to the original case outline. Avoid twisting an ear to snap off a pad. Clear brim/pad remnants before trying the front and battery cover.

Reuse your front and cover if they are v8.7 and usable. No new screws or permanent support plate are required. Record the exact source file, selected profiles, whether corners stay down, pad-removal behavior and fit. Physical print results are pending.

## Source and verification

From the public checkout run `bash rebuild.sh v8.7a`. This rebuilds only v8.7a. The included `reference/rear_tray_v87.stl` is the untouched v8.7 geometry input; the original version's parametric sources remain in `work/v8_7/source/`. The input hash is recorded in `validation.json`.

The standalone `source/build.py` also runs from an extracted package using a Python environment with `source/requirements.txt`. It creates the coupon first, exports and reloads both STL/3MF pairs, verifies millimeter units and named single-solid objects, compares the rear against the reference, checks holes remain open, and checks the 0.20 mm layer support envelope. Numerical acceptance is 0.003 mm³ for export residual volumes and 0.025 mm² for section differences, not a physical fit allowance. The actual maximum section difference above the pads is approximately 0.00023 mm².

The PCB source is RetiaLLC/DefconBadge2026; this is an independent enclosure prototype. Existing v8.7 physical fit uncertainties remain. Physical validation is pending.
