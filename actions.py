#!/usr/bin/python3
from pisi.actionsapi import pisitools
from pisi.actionsapi import shelltools
import os

WorkDir = "."

def build():
    pass

def install():
    src_dir = os.environ.get("PISIM_SRC_DIR", os.getcwd())

    # Copy application main entry and package directory
    main_py = os.path.join(src_dir, "main.py")
    if not os.path.isfile(main_py):
        main_py = "main.py"
    if os.path.isfile(main_py):
        pisitools.insinto("/usr/share/pisim", main_py)

    pisi_store_dir = os.path.join(src_dir, "pisi_store")
    if not os.path.isdir(pisi_store_dir):
        pisi_store_dir = "pisi_store"
    if os.path.isdir(pisi_store_dir):
        pisitools.insinto("/usr/share/pisim", pisi_store_dir)

    # Launcher script (/usr/bin/pisim)
    launcher_path = os.path.join(src_dir, "pisim")
    if not os.path.isfile(launcher_path):
        launcher_path = "pisim"
    
    if not os.path.isfile(launcher_path):
        with open("pisim", "w") as f:
            f.write("#!/bin/bash\nexec python3 /usr/share/pisim/main.py \"$@\"\n")
        os.chmod("pisim", 0o755)
        launcher_path = "pisim"

    pisitools.dobin(launcher_path)

    # Desktop entry
    desktop_path = os.path.join(src_dir, "com.teknoanka.pisim.desktop")
    if not os.path.isfile(desktop_path):
        desktop_path = "com.teknoanka.pisim.desktop"
    if os.path.isfile(desktop_path):
        pisitools.insinto("/usr/share/applications", desktop_path)

    # App icon
    icon_path = os.path.join(src_dir, "pisi_store", "assets", "pisim.png")
    if not os.path.isfile(icon_path):
        icon_path = os.path.join("pisi_store", "assets", "pisim.png")
    if os.path.isfile(icon_path):
        pisitools.insinto("/usr/share/icons/hicolor/128x128/apps", icon_path, "pisim.png")

    # Documentation & License
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
