#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo " LupuS Software Center — Luppo Package Builder"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LUPUS_SOFTWARE_CENTER_SRC_DIR="${SCRIPT_DIR}"
cd "${SCRIPT_DIR}"

echo "[1/2] Building Rust / Tauri release binary..."
cd src-tauri
cargo build --release
cd ..

echo "[2/2] Creating Luppo package (.luppo)..."
if command -v luppo &>/dev/null; then
    luppo build lopec.xml --no-sandbox --ignore-dependency
else
    echo "Error: luppo command not found!"
    exit 1
fi

echo "Locating generated .luppo package..."

LUPPO_FILE=$(find . /var/luppo /tmp -name "lupus-software-center-*.luppo" 2>/dev/null | head -n 1 || true)

if [ -n "${LUPPO_FILE}" ] && [ -f "${LUPPO_FILE}" ]; then
    TARGET_PATH="${SCRIPT_DIR}/$(basename "${LUPPO_FILE}")"
    if [ "${LUPPO_FILE}" != "${TARGET_PATH}" ]; then
        cp -f "${LUPPO_FILE}" "${TARGET_PATH}"
    fi

    if [ -n "${SUDO_USER:-}" ]; then
        chown "${SUDO_USER}:" "${TARGET_PATH}" 2>/dev/null || true
    fi

    echo ""
    echo "=========================================="
    echo " SUCCESS! .luppo package saved to:"
    echo " ${TARGET_PATH}"
    echo "=========================================="
else
    echo "Error: .luppo package file could not be found."
    exit 1
fi
