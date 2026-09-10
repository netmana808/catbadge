#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
.venv/bin/python work/v8_7a/source/build.py
.venv/bin/python work/v8_7a/source/package.py
