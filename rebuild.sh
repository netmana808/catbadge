#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python_bin="${CATBADGE_PYTHON:-.venv/bin/python}"
if [[ -n "${OPENSCAD_BIN:-}" ]]; then
  [[ -x "$OPENSCAD_BIN" ]] || { echo "OPENSCAD_BIN must name an executable" >&2; exit 1; }
  mkdir -p .venv/catbadge-bin
  ln -sf "$OPENSCAD_BIN" .venv/catbadge-bin/openscad
  export PATH="$PWD/.venv/catbadge-bin:$PATH"
elif ! command -v openscad >/dev/null && [[ -x /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD ]]; then
  mkdir -p .venv/catbadge-bin
  ln -sf /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD .venv/catbadge-bin/openscad
  export PATH="$PWD/.venv/catbadge-bin:$PATH"
fi
command -v openscad >/dev/null || { echo "Install OpenSCAD and add its CLI to PATH, or set OPENSCAD_BIN" >&2; exit 1; }
"$python_bin" work/v8_4/source/generate_v84.py --coupons
"$python_bin" work/v8_4/source/validate_snaps.py
"$python_bin" work/v8_4/source/check_overhangs.py --coupons
"$python_bin" work/v8_4/source/generate_v84.py
"$python_bin" work/v8_4/source/validate_v84.py --standalone
"$python_bin" work/v8_4/source/check_overhangs.py
"$python_bin" work/v8_4/source/render_v84.py
