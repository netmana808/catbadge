# CatBadge v8.4 — compact handheld polish

V8.4 softens exposed edges and adds subtle cheek grips while retaining the v8.3 size, four integral rim catches and independent sliding battery cover. It uses the existing PLA+ workflow and requires no case screws or separate keeper plate.

The front and rear exterior perimeter edges and battery-cover exterior edge have nominal **0.6 mm, 45-degree bevels**. The antenna mounting land, battery latch beam/root/tooth, sliding tabs and mating surfaces are protected from these cuts. The latch guards receive smaller 0.25 mm edge bevels and 0.30 mm rounded vertical corners to keep their corners within the print envelope. Layered perimeter bevels use 0.05 mm CAD increments; the button bevel is a continuous revolved surface.

All six button faces retain their flat round tops and gain **0.3 mm edge bevels** (9.4 mm flat top, original 10 mm guide diameter below the bevel). Stems, sockets, captive flanges and projection are preserved. Each cheek has **four shallow, rounded grip lines**, nominally 2.4 mm long, 0.8 mm wide and 0.25 mm deep, angled 20 degrees in mirrored directions. They are recessed into the outer wall, clear of catches and ports. The exterior entrances to the four release notches gain a 0.25 mm bevel; their internal access and catches remain unchanged.

This is an **unprinted PLA+ prototype**. The supplied Cynthion case informed the overlapping rim and local catches; its dimensions were not copied as validated CatBadge tolerances. Digital clearance and mesh checks do not establish physical snap force or fatigue life. Only the original v0.1 case has user-confirmed physical fit.

## Print files

- **`CatBadge-v8.4-COMBINED-HANDHELD.3mf`** — default, with original spring-antenna access retained in the left ear.
- `CatBadge-v8.4-COMBINED-HANDHELD-NO-SPRING-ONLY.3mf` — alternate with both ear faces closed around the LED stripes; use only if the original spring antenna is absent. SAO stays open.
- **`PRINT_FIRST_v8.4_Comfort_Only.3mf`** — cheek-grip coupon, battery-cover edge coupon and one 3.2 mm socket button cap: a quick three-piece feel check.
- **`PRINT_FIRST_v8.4_Fit_and_Comfort.3mf`** — all 15 coupons/trials: the comfort samples, three rim-fit trials, shared tray, battery latch pair, front-button section, four cap socket sizes, LED/SAO section and screen ring.

Each combined file contains **9 named objects**: one faceplate, one rear tray, one battery cover and six button caps. Select one combined file; the two faceplates are alternatives. There are no separate case pins, screws or nuts. The antenna adapter still uses its own real metal retaining nut.

Individual STL and 3MF files are under `parts/` and `tests/`. All geometry uses millimeters. The combined layout fits within a nominal 220 x 220 mm area before brims; it contains no printer profile or G-code. Keep the supplied orientations: faceplate and caps face down, tray and battery cover exterior down. The exported ramps pass the project's 0.2 mm layer / 45-degree support-envelope check. Inspect the slicer's actual thin-wall and first-layer paths before printing.

**V8.4 retains the v8.3 mechanical interfaces.** Exported-mesh checks cover both directions of mixed v8.3/v8.4 faceplate/tray, battery-cover/tray and button/faceplate combinations. Physical interchangeability still needs a fit check. These case halves do not mate with the earlier v8/v8.1 pin-mounted halves.

## Rim and catches

The outer faceplate tongue overlaps the rear tray at the seam. The nominal side gap is 0.30 mm; the faceplate tongue is approximately 1.15 mm thick and extends 3.0 mm below the original internal mating plane. The PCB seat and upper restraint retain the original 0.2 mm nominal board float. The tongue stays outside the board-clearance envelope.

Four 5 mm wide catches sit on the two upper cheek walls and two lower cheek curves. The catches point inward into matching tray recesses; the faceplate rim flexes outward during engagement/release. Both catch flanks are shallow ramps. These are releasable detents, not square locking hooks. Small exterior notches beside the catches allow a thin plastic pick to reach the seam without entering the PCB space.

The full case selects **0.25 mm nominal engagement**. The three coupon faceplates use 0.15, 0.25 and 0.35 mm engagement and share the same mating tray. These numbers describe engagement, not tongue thickness or clearance. Their files are named `PRINT_FIRST_rim_lid_0p15`, `0p25`, `0p35`, and `PRINT_FIRST_rim_tray`.

The catch roots use the continuous curved rim rather than narrow upright hooks. Local fit still depends on the filament, layer adhesion and slicer paths. The cropped coupon has different overall stiffness from the full case, so passing it is followed by an empty-case fit check. The inherited source parameter `P['catch_overlap']` in `source/generate_v83.py` controls full-case engagement; changing it requires regeneration and validation of both kits and parts.

## Fit sequence

1. Print the three-piece comfort set to assess the bevels, grip texture and button feel. Then print the shared rim tray and the 0.15 mm coupon lid first. Progress to the 0.25 mm and 0.35 mm trials only to compare retention. Select a fit that seats and releases gently. Whitening, cracking or a seam requiring force is a failed fit.
2. Check repeated opening and closing on the coupon. Twenty cycles is a useful initial screening exercise, not a lifetime qualification.
3. Check the two empty v8.4 case halves together before installing electronics. Confirm that the four catches retain the seam and release through their notches. The default full case corresponds to the 0.25 mm coupon.
4. Test button sockets from the largest 3.3 mm trial downward to a gentle fit. The combined case uses 3.2 mm provisionally. Verify the screen fit ring, retained button motion and any untested port/ear clearances.

## Assembly and reopening

Remove power. Fit the antenna adapter with its actual retaining nut, and route its cable clear of the rim, PCB seat and cover. Seat the board, then fit the six caps gently. Lower the faceplate squarely while aligning the cap faces with their guide holes. Apply light pressure at the perimeter adjacent to the catches until the rim seats. Do not use the screen, buttons or connector as pressing points. A misaligned case must not be forced together.

To reopen, use the small notches beside the four catches to ease the **outer faceplate rim outward**, then lift it away from the tray. A thin plastic pick can hold an already released section clear while working around the seam. Keep the pick in the external notch. Do not insert it over the PCB or lever against the board. Stop if the rim needs force or shows stress damage.

The release calculation prescribes up to 0.45 mm outward rim movement for the selected 0.25 mm trial, then checks axial separation. It is a geometric model, not an instruction to measure or force that displacement, and not a prediction of hand force or sequential release behavior. Verify the actual opening procedure on the empty case.

Button flanges prevent outward escape while assembled. The caps can still leave through the rear of a removed faceplate. There are no keeper plates or extra screws.

## Battery access

The existing cover remains independent of the main-case catches. To remove it, press its bottom-edge thumb latch toward the badge center (assembly +Y), slide the cover 3.2 mm toward assembly +X (right when viewed from the front), then lift it away from the rear. Install in reverse, sliding toward -X until it clicks. The main case stays closed during this operation.

The loaded holder envelope remains **15.7 mm high x 32.7 mm wide x 59.7 mm long**, with 1 mm modeled height allowance. Its modeled top is at the PCB underside; actual mounting offsets, leads and connector clearance still need physical verification.

## Preserved dimensions and access

- Main shell depth: **22.4 mm**; over the battery cover: **30.7 mm**; including button faces: **31.2 mm**. The new joint fits within this existing depth.
- Faceplate skin: **1.6 mm**; inner surface stays at Z=11.2 mm above the PCB underside, retaining 0.7 mm nominal clearance above the measured 10.5 mm screen before board float and print tolerances.
- Screen aperture: **52.5 x 40 mm**. Left edge X=-26.04, right X=26.46; Y=-27.99 to 12.01. The v8.1 right-side correction remains.
- Rear electronics clearance stays 8 mm and the floor stays 1.6 mm. No component heights or cable envelopes were guessed to reduce them.
- Six captive button flanges, all ten LED slots, open rotated SAO connector access, speaker, lanyard and existing service access remain.
- The 6.5 mm trial antenna port stays in the rear tray's outer left-ear slope with a 2.4 mm clamping land. Exact adapter shank, nut/washer, usable thread and cable-bend fit remain unverified.
- The default retains the left-ear spring access because removal of the original spring is unconfirmed. This revision makes no electrical, RF or firmware change.

## Validation and rebuild

`validation.json` records 19 unique printable solids; STL/3MF surface equivalence; 9 objects per full kit, 15 per full coupon kit and 3 per comfort kit; no overlap in the print layout; assembled clearances; retention at all four catches; outward-flex/separation checks for both faceplates; four external release-notch probes; battery-cover motion; 120 button offsets checked against both lids; PCB seat, screen, LED, SAO and antenna checks; exterior material removal without added bulk; all eight grip recesses; button and case bevels; protected mechanical sections; mixed v8.3/v8.4 assembly and motion checks; and protected baseline hashes.

`overhangs.json` checks exported print orientations one layer at a time at 0.2 mm, allowing 0.205 mm lateral expansion and at most 0.025 mm² numerical residual per layer. All parts pass this geometric envelope. It is not a printer-specific slicing or physical print result.

Previews are generated from the exported meshes. The front and rear assembly views include only a simplified PCB reference; electronics and cables are not modeled. `preview/snap_detail.png` is an actual cross-section of the mating meshes.

From the original repository root:

```sh
bash work/v8_4/run.sh
```

From an extracted package, with Python 3.12, the listed dependencies and OpenSCAD on PATH:

```sh
python source/generate_v84.py --coupons
python source/validate_snaps.py
python source/generate_v84.py
python source/validate_v84.py --standalone
python source/check_overhangs.py
python source/render_v84.py
```

`generate_v83.py`, `generate_v81.py`, `generate_v75.py` and earlier source modules are internal geometry helpers; use `generate_v84.py` as the build entry point. Finishing parameters live in `source/finish_v84.py`. Existing local tools were sufficient; no new system tooling was installed. The package includes source, parameters, individual meshes, test coupons, previews and reports. Archive CRC and each packaged file's SHA-256 are checked; distribution checksums are in `SHA256SUMS`.

## References

- [Prusa modeling guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135): bed-facing chamfers, print orientation and tolerance iteration.

- Local `cynthion_box.stl` and `cynthion_lid.stl`: measured overlapping rim and four local ramped catches; inspection measurements/hashes are recorded in `reference/cynthion_joint_measurements.json`. Supplied Cynthion mesh files are not redistributed in this package.
- [Formlabs snap-fit guide](https://formlabs.com/global/blog/designing-3d-printed-snap-fit-enclosures/): fit, print orientation, joint types and iterative physical testing.
- [Protolabs snap-fit guidance](https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/): root geometry, deflection and clearance considerations. General process advice is not a PLA+ material qualification.
- [RetiaLLC/DefconBadge2026](https://github.com/RetiaLLC/DefconBadge2026): original PCB/outline source. Independent enclosure prototype; upstream design credit remains with its designers.
