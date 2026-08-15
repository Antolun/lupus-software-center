#!/usr/bin/python3
from luppo.actionsapi import luppotools
import os

WorkDir = "."

def build():
    pass

def install():
    src_dir = os.environ.get("LUPUS_SOFTWARE_CENTER_SRC_DIR", os.getcwd())

    possible_bins = [
        os.path.join(src_dir, "src-tauri/target/release/lupus-software-center"),
        os.path.join(src_dir, "target/release/lupus-software-center"),
        os.path.join(src_dir, "lupus-software-center"),
        "src-tauri/target/release/lupus-software-center",
        "target/release/lupus-software-center",
        "lupus-software-center",
    ]

    bin_path = None
    for p in possible_bins:
        if os.path.isfile(p):
            bin_path = p
            break

    if not bin_path:
        raise RuntimeError(f"lupus-software-center binary not found in any path! Searched: {possible_bins}")

    luppotools.dobin(bin_path)

    desktop_path = os.path.join(src_dir, "lupus-software-center.desktop")
    if not os.path.isfile(desktop_path):
        desktop_path = "lupus-software-center.desktop"
    if os.path.isfile(desktop_path):
        luppotools.insinto("/usr/share/applications", desktop_path)

    icon_path = os.path.join(src_dir, "src-tauri/icons/128x128.png")
    if not os.path.isfile(icon_path):
        icon_path = os.path.join(src_dir, "128x128.png")
    if not os.path.isfile(icon_path):
        icon_path = "src-tauri/icons/128x128.png"
    if os.path.isfile(icon_path):
        luppotools.insinto("/usr/share/icons/hicolor/128x128/apps", icon_path, "lupus-software-center.png")

    readme_path = os.path.join(src_dir, "README.md")
    if not os.path.isfile(readme_path):
        readme_path = "README.md"
    if os.path.isfile(readme_path):
        luppotools.dodoc(readme_path)

    license_path = os.path.join(src_dir, "LICENSE")
    if not os.path.isfile(license_path):
        license_path = "LICENSE"
    if os.path.isfile(license_path):
        luppotools.dodoc(license_path)
