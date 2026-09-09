# Attribution and licensing notes

- **Badge hardware:** [RetiaLLC/DefconBadge2026](https://github.com/RetiaLLC/DefconBadge2026), specifically `hardware/kicad/2024_def_con_badge_v1.kicad_pcb`. The enclosure helpers transcribe the board outline and selected footprint locations; they do not contain a complete electronics assembly. Credit and ownership of the upstream hardware remain with its designers.
- **Enclosure:** independent CatBadge case development, published by `netmana808`. The v8.4 release retains the local project's source, geometry, measured constraints and validation artifacts.
- **Snap-fit reference:** locally supplied Cynthion case meshes informed the overlapping rim and catch concept. Those Cynthion meshes are not redistributed. Inspection measurements and file hashes are recorded in `work/v8_4/reference/cynthion_joint_measurements.json`; their dimensions are not validated CatBadge tolerances.
- **Tools:** NumPy, Shapely, Trimesh, Manifold, OpenSCAD, VTK and Pillow retain their respective licenses. Their applications, source distributions and fonts are not bundled.

The upstream repository did not expose a top-level license file or a detected license through GitHub when checked for this publication on 2026-09-09. No blanket license is assigned here to upstream or third-party material. Public availability alone should not be treated as a separate license grant. This publication does not relicense the badge hardware.
