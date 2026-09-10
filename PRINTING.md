# Printing trials

Starting trial for an **AnkerMake M5C with a 0.4 mm nozzle**, using eufyMake Studio 3D. Plate coating, filament formulation, calibration and environment matter. These settings have not been verified by a successful print of the latest parts. Geometry-only 3MF files do not apply settings automatically.

## Transparent HS PETG case trial

The reported spool label specifies 220–260°C nozzle and 60–80°C bed; exact brand/formulation is unconfirmed. Follow the instructions for your actual spool.

| Setting | Proposed trial |
| --- | --- |
| Layer height, including first layer | 0.20 mm |
| Wall loops / perimeters | 4 |
| Nozzle / bed temperature | 240°C / 80°C |
| First-layer speed / acceleration | 20 mm/s / 500 mm/s² |
| First-layer extrusion width | 0.50 mm |
| First-layer single-wall mode | Off |
| Outer / inner wall speed | 40 / 60 mm/s |
| Sparse infill speed | 80 mm/s |
| Fan | Off for 3 layers; 40% thereafter, separate bridge cooling |
| Rear brim | 8 mm outer brim, zero gap |
| Supports | Off, subject to sliced-path inspection |

Prepare your plate coating according to its manufacturer's instructions; keep direct room-fan/AC airflow away. PETG can adhere excessively to some surfaces, so no universal glue, solvent or Z-offset setting is prescribed here. Inspect first-layer contact and ensure the plate is seated properly.

V8.7a pads add two 0.20 mm layers of contact. Print the rear alone, center it, and verify pads and brim join the case. Let the plate and print cool, then support the ears while trimming. Do not twist the case to break off pads.

## Buttons and feedback

Print faces down, sockets up, at 100% scale. Clear brim remnants from the face bevel and socket mouth. Test the comparison caps in the actual faceplate before choosing a set; smaller clearance is not automatically a better fit.

Record exact file/version, filament, printer/nozzle/plate, layer height, temperatures, cooling, brim, and when lifting begins. For the case, record seam seating and retention. For buttons, record free sliding, socket grip and release without preload. A small coupon does not predict full-case warping.

Background: [Prusa warping guidance](https://help.prusa3d.com/article/warping_2011) and [PETG guidance](https://help.prusa3d.com/article/petg_2059). The specific settings above remain a trial, not a universally validated profile.
