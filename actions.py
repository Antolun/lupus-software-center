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

    # Udev kuralları kurulumu
    udev_path = os.path.join(src_dir, "udev/99-lupus-software-center.rules")
    if not os.path.isfile(udev_path):
        udev_path = "udev/99-lupus-software-center.rules"
    if os.path.isfile(udev_path):
        luppotools.insinto("/etc/udev/rules.d", udev_path)

    # Polkit kuralları ve eylem yetkilendirmesi
    polkit_rules = os.path.join(src_dir, "polkit/50-lupus-software-center.rules")
    if not os.path.isfile(polkit_rules):
        polkit_rules = "polkit/50-lupus-software-center.rules"
    if os.path.isfile(polkit_rules):
        luppotools.insinto("/usr/share/polkit-1/rules.d", polkit_rules)

    polkit_policy = os.path.join(src_dir, "polkit/tr.org.luppo.softwarecenter.policy")
    if not os.path.isfile(polkit_policy):
        polkit_policy = "polkit/tr.org.luppo.softwarecenter.policy"
    if os.path.isfile(polkit_policy):
        luppotools.insinto("/usr/share/polkit-1/actions", polkit_policy)

    # Sudoers kuralı (şifresiz paket yönetimi)
    sudoers_path = os.path.join(src_dir, "sudoers/50-lupus-software-center")
    if not os.path.isfile(sudoers_path):
        sudoers_path = "sudoers/50-lupus-software-center"
    if os.path.isfile(sudoers_path):
        luppotools.insinto("/etc/sudoers.d", sudoers_path)

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
