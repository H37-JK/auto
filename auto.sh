#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "$(uname -s)" == Darwin ]]; then
  echo "macOS에는 백그라운드 모드가 없어 마우스를 움직이는 일반 모드로 실행합니다."
  exec /usr/bin/env python3 -u autoclick_mac.py
fi
PYTHON="${PYTHON:-$PWD/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi
exec "$PYTHON" -u autoclick_linux.py --background "$@"
