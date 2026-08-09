#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo " PiSiM — PiSi Package Builder"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PISIM_SRC_DIR="${SCRIPT_DIR}"
cd "${SCRIPT_DIR}"

echo "[1/1] Creating PiSi package (.pisi)..."
if command -v pisi &>/dev/null; then
    pisi build pspec.xml --no-sandbox --ignore-dependency
else
    echo "Error: pisi command not found!"
    exit 1
fi

echo "Locating generated .pisi package..."

PISI_FILE=$(find . /var/pisi /tmp -name "pisim-*.pisi" 2>/dev/null | head -n 1 || true)

if [ -n "${PISI_FILE}" ] && [ -f "${PISI_FILE}" ]; then
    TARGET_PATH="${SCRIPT_DIR}/$(basename "${PISI_FILE}")"
    if [ "${PISI_FILE}" != "${TARGET_PATH}" ]; then
        cp -f "${PISI_FILE}" "${TARGET_PATH}"
    fi
    
    if [ -n "${SUDO_USER:-}" ]; then
        chown "${SUDO_USER}:" "${TARGET_PATH}" 2>/dev/null || true
    fi
    
    echo ""
    echo "=========================================="
    echo " SUCCESS! .pisi package saved to:"
    echo " ${TARGET_PATH}"
    echo "=========================================="
else
    echo "Error: .pisi package file could not be found."
    exit 1
fi
