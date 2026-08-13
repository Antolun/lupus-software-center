#!/usr/bin/python3
from pisi.actionsapi import pisitools
import os

WorkDir = "."

def build():
    pass

def install():
    src_dir = os.environ.get("PISIM_SRC_DIR", os.getcwd())

    possible_bins = [
        os.path.join(src_dir, "src-tauri/target/release/pisim"),
        os.path.join(src_dir, "target/release/pisim"),
        os.path.join(src_dir, "pisim"),
        "src-tauri/target/release/pisim",
        "target/release/pisim",
        "pisim",
    ]

    bin_path = None
    for p in possible_bins:
        if os.path.isfile(p):
            bin_path = p
            break

    if not bin_path:
        raise RuntimeError(f"pisim binary not found in any path! Searched: {possible_bins}")

    pisitools.dobin(bin_path)

    desktop_path = os.path.join(src_dir, "pisim.desktop")
    if not os.path.isfile(desktop_path):
        desktop_path = "pisim.desktop"
    if os.path.isfile(desktop_path):
        pisitools.insinto("/usr/share/applications", desktop_path)

    icon_path = os.path.join(src_dir, "src-tauri/icons/128x128.png")
    if not os.path.isfile(icon_path):
        icon_path = os.path.join(src_dir, "logo.png")
    if not os.path.isfile(icon_path):
        icon_path = "src-tauri/icons/128x128.png"
    if os.path.isfile(icon_path):
        pisitools.insinto("/usr/share/icons/hicolor/128x128/apps", icon_path, "pisim.png")

    readme_path = os.path.join(src_dir, "README.md")
    if not os.path.isfile(readme_path):
        readme_path = "README.md"
    if os.path.isfile(readme_path):
        pisitools.dodoc(readme_path)

    license_path = os.path.join(src_dir, "LICENSE")
    if not os.path.isfile(license_path):
        license_path = "LICENSE"
    if os.path.isfile(license_path):
        pisitools.dodoc(license_path)
