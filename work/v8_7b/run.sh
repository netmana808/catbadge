#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
.venv/bin/python work/v8_7b/source/build.py
.venv/bin/python work/v8_7b/source/render.py
.venv/bin/python work/v8_7b/source/package.py
