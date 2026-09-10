#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
.venv/bin/python work/v8_7/source/generate_v87.py --coupons
.venv/bin/python work/v8_7/source/validate_snaps.py
.venv/bin/python work/v8_7/source/check_overhangs.py --coupons
.venv/bin/python work/v8_7/source/generate_v87.py
.venv/bin/python work/v8_7/source/validate_v87.py
.venv/bin/python work/v8_7/source/check_overhangs.py
.venv/bin/python work/v8_7/source/render_v87.py
.venv/bin/python work/v8_7/source/package_v87.py
