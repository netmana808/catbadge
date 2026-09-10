#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python_bin="${CATBADGE_PYTHON:-.venv/bin/python}"
version="${1:-v8.7b}"
case "$version" in
  v8.4|v8.7|v8.7a|v8.7b|all) ;;
  *) echo 'Usage: bash rebuild.sh [v8.7b|v8.7a|v8.7|v8.4|all]' >&2; exit 2 ;;
esac
if [[ "$version" == all ]]; then
  for target in v8.7 v8.7a v8.7b; do bash rebuild.sh "$target"; done
  exit 0
fi
if [[ "$version" == v8.7a || "$version" == v8.7b ]]; then
  folder="work/${version//./_}"
  "$python_bin" "$folder/source/build.py"
  if [[ "$version" == v8.7b ]]; then "$python_bin" "$folder/source/render.py"; fi
  exit 0
fi
if [[ -n "${OPENSCAD_BIN:-}" ]]; then
  [[ -x "$OPENSCAD_BIN" ]] || { echo 'OPENSCAD_BIN must name an executable' >&2; exit 1; }
  mkdir -p .venv/catbadge-bin
  ln -sf "$OPENSCAD_BIN" .venv/catbadge-bin/openscad
  export PATH="$PWD/.venv/catbadge-bin:$PATH"
elif ! command -v openscad >/dev/null && [[ -x /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD ]]; then
  mkdir -p .venv/catbadge-bin
  ln -sf /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD .venv/catbadge-bin/openscad
  export PATH="$PWD/.venv/catbadge-bin:$PATH"
fi
command -v openscad >/dev/null || { echo 'Install OpenSCAD on PATH, or set OPENSCAD_BIN' >&2; exit 1; }
folder="work/${version//./_}"
suffix="${version//./}"
"$python_bin" "$folder/source/generate_${suffix}.py" --coupons
"$python_bin" "$folder/source/validate_snaps.py"
"$python_bin" "$folder/source/check_overhangs.py" --coupons
"$python_bin" "$folder/source/generate_${suffix}.py"
"$python_bin" "$folder/source/validate_${suffix}.py" --standalone
"$python_bin" "$folder/source/check_overhangs.py"
"$python_bin" "$folder/source/render_${suffix}.py"
