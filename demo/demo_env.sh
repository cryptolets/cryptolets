#!/usr/bin/env bash
set -euo pipefail

DEMO_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_ROOT_DIR="$(cd "${DEMO_SCRIPT_DIR}/.." && pwd)"

cd "${DEMO_ROOT_DIR}"
