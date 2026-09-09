#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
.venv/bin/python work/v8_4/source/generate_v84.py --coupons
.venv/bin/python work/v8_4/source/validate_snaps.py
.venv/bin/python work/v8_4/source/check_overhangs.py --coupons
.venv/bin/python work/v8_4/source/generate_v84.py
.venv/bin/python work/v8_4/source/validate_v84.py
.venv/bin/python work/v8_4/source/check_overhangs.py
.venv/bin/python work/v8_4/source/render_v84.py
.venv/bin/python work/v8_4/source/package_v84.py
