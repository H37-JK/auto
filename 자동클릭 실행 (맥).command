#!/usr/bin/env bash
# Finder에서 더블클릭으로 실행하는 macOS용 실행 파일
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec /usr/bin/env python3 -u autoclick_mac.py
