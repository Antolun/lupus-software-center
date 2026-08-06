#!/usr/bin/env python3
"""
PiSiM - PiSi Market
Giriş noktası
"""

import sys
import os

# HiDPI desteği
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
# Qt SVG renderer'ının geçersiz path uyarılarını sustur (QApplication'dan ÖNCE ayarlanmalı)
os.environ["QT_LOGGING_RULES"] = "qt.svg=false;qt.svg.warning=false"

# Qt mesaj handler'ı — diğer tüm Qt/pisi import'larından önce kurulmalı
from PyQt6.QtCore import QtMsgType, qInstallMessageHandler


def _qt_message_handler(msg_type, context, message):
    """Qt mesajlarını filtreler — SVG uyarılarını bastırır."""
    cat = (context.category or "").lower()
    if "svg" in cat or "Invalid path data" in message or "path truncated" in message.lower():
        return
    if msg_type in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        print(f"Qt [{msg_type.name}]: {message}", file=sys.stderr)


# Handler'ı en erken noktada kur
qInstallMessageHandler(_qt_message_handler)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from pisi_store.mainwindow import MainWindow
from pisi_store.i18n import tr, I18n
from pisi_store.settings import SettingsManager

# Uygulama kaydetme/dil tercihlerini yükle
_init_settings = SettingsManager.load_settings()
I18n.set_lang(_init_settings.get("language", "tr"))

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "pisi_store", "assets")
SOCKET_NAME = f"pisim_single_instance_{os.getuid() if hasattr(os, 'getuid') else 'default'}"


VERSION = "1.2"

CLI_COMMANDS = {
    "search": ["-s", "--search"],
    "list-installed": ["-l", "--list-installed"],
    "list-updates": ["-u", "--list-updates"],
    "install": ["-i", "--install"],
    "remove": ["-r", "--remove"],
    "update-repo": ["--update-repo"],
    "update-all": ["--update-all"],
}


def print_usage():
    print(tr("cli_usage_title", version=VERSION))
    print()
    print(tr("cli_usage_section"))
    print()
    print(tr("cli_options_section"))
    print()
    print(tr("cli_commands_section"))


def run_cli_command(cmd: str, params: list[str]):
    """Konsol komutlarını grafik arayüz açmadan terminalde çalıştırır."""
    from pisi_store.backend import PisiBackend

    print(tr("cli_header", version=VERSION) + "\n")
    backend = PisiBackend()

    # komut kısayolu normalization
    if cmd in ("-s", "--search"):
        cmd = "search"
    elif cmd in ("-l", "--list-installed"):
        cmd = "list-installed"
    elif cmd in ("-u", "--list-updates"):
        cmd = "list-updates"
    elif cmd in ("-i", "--install"):
        cmd = "install"
    elif cmd in ("-r", "--remove"):
        cmd = "remove"
    elif cmd == "--update-repo":
        cmd = "update-repo"
    elif cmd == "--update-all":
        cmd = "update-all"

    if cmd == "search":
        query = " ".join(params).strip()
        if not query:
            print(tr("cli_search_error"))
            sys.exit(1)

        print(tr("cli_searching", query=query))
        all_pkgs = backend.get_all_packages()
        results = backend.search_packages(query, all_pkgs)

        if not results:
            print(tr("cli_no_match"))
            return

        print(f"\n{tr('cli_found_packages', count=len(results))}\n")
        c_name = tr("cli_col_name")
        c_ver = tr("cli_col_version")
        c_orig = tr("cli_col_origin")
        c_stat = tr("cli_col_status")
        print(f"{c_name:<32} {c_ver:<12} {c_orig:<10} {c_stat:<20}")
        print("─" * 76)
        for p in results:
            disp_name = p.display_name or p.name
            status = tr("cli_status_installed") if p.installed else tr("cli_status_installable")
            if p.has_update:
                status += tr("cli_status_update_avail")
            origin = p.origin or ("Flatpak" if p.is_flatpak else "Pisi")
            print(f"{disp_name[:30]:<32} {p.version[:10]:<12} {origin:<10} {status:<20}")
            if p.summary:
                print(f"  └─ {p.summary[:70]}")
        print("─" * 76)

    elif cmd == "list-installed":
        print(tr("cli_listing_installed"))
        installed = backend.get_installed_packages()
        if not installed:
            print(tr("cli_no_installed"))
            return

        print(f"\n{tr('cli_installed_packages', count=len(installed))}\n")
        c_name = tr("cli_col_name")
        c_ver = tr("cli_col_version")
        c_orig = tr("cli_col_origin")
        c_upd = tr("cli_col_update")
        print(f"{c_name:<32} {c_ver:<12} {c_orig:<10} {c_upd:<15}")
        print("─" * 70)
        for name, p in sorted(installed.items(), key=lambda x: x[0].lower()):
            disp_name = p.display_name or p.name
            origin = p.origin or ("Flatpak" if p.is_flatpak else "Pisi")
            upd = tr("cli_upd_yes") if p.has_update else tr("cli_upd_no")
            print(f"{disp_name[:30]:<32} {p.version[:10]:<12} {origin:<10} {upd:<15}")
        print("─" * 70)

    elif cmd == "list-updates":
        print(tr("cli_checking_updates"))
        count, pkgs, err = backend.check_for_updates(update_repo=False)
        if err and not pkgs:
            print(tr("cli_err_prefix", msg=err))
            return

        if count == 0:
            print(tr("cli_all_up_to_date"))
            return

        print(f"\n{tr('cli_upgradable_packages', count=count)}\n")
        c_name = tr("cli_col_name")
        c_cver = tr("cli_col_curr_ver")
        c_nver = tr("cli_col_new_ver")
        print(f"{c_name:<35} {c_cver:<15} {c_nver:<15}")
        print("─" * 68)
        all_pkgs = backend.get_all_packages()
        for p_name in pkgs:
            p_info = all_pkgs.get(p_name)
            curr_ver = p_info.version if p_info else "-"
            new_ver = p_info.new_version if p_info and p_info.new_version else "-"
            print(f"{p_name[:33]:<35} {curr_ver:<15} {new_ver:<15}")
        print("─" * 68)

    elif cmd == "install":
        pkg_name = params[0] if params else ""
        if not pkg_name:
            print(tr("cli_install_error"))
            sys.exit(1)

        print(tr("cli_installing", name=pkg_name))
        ok, msg = backend.install_package(pkg_name)
        if ok:
            print(f"✅ {msg}")
        else:
            print(tr("cli_err_prefix", msg=msg))

    elif cmd == "remove":
        pkg_name = params[0] if params else ""
        if not pkg_name:
            print(tr("cli_remove_error"))
            sys.exit(1)

        print(tr("cli_removing", name=pkg_name))
        ok, msg = backend.remove_package(pkg_name)
        if ok:
            print(f"✅ {msg}")
        else:
            print(tr("cli_err_prefix", msg=msg))

    elif cmd == "update-repo":
        print(tr("cli_updating_repo"))
        try:
            backend.update_repo_and_sync_cache(update_repo=True)
            print(tr("cli_repo_update_success"))
        except Exception as e:
            print(tr("cli_err_prefix", msg=str(e)))

    elif cmd == "update-all":
        print(tr("cli_checking_all_updates"))
        count, pkgs, err = backend.check_for_updates(update_repo=True)
        if count == 0:
            print(tr("cli_no_updates_needed"))
            return

        print(tr("cli_updating_count", count=count))
        for pkg_name in pkgs:
            print(tr("cli_updating_item", name=pkg_name))
            ok, msg = backend.install_package(pkg_name)
            if ok:
                print(tr("cli_updated_item_ok", name=pkg_name))
            else:
                print(tr("cli_updated_item_err", name=pkg_name, msg=msg))


def main():
    args = sys.argv[1:]

    # Yardım ve Sürüm kontrolü
    if "-h" in args or "--help" in args:
        print_usage()
        sys.exit(0)

    if "-v" in args or "--version" in args:
        print(f"PiSiM (PiSi Market) v{VERSION}")
        sys.exit(0)

    # CLI komut kontrolü
    if args:
        first = args[0]
        all_cli_flags = [f for flags in CLI_COMMANDS.values() for f in flags] + list(CLI_COMMANDS.keys())
        if first in all_cli_flags:
            run_cli_command(first, args[1:])
            sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("PiSiM")
    app.setOrganizationName("TeknoAnka")
    app.setOrganizationDomain("https://www.teknoanka.com/")

    # Tekil Örnek (Single Instance) Kontrolü
    socket = QLocalSocket()
    socket.connectToServer(SOCKET_NAME)
    if socket.waitForConnected(500):
        # Zaten çalışan bir PiSiM örneği var: Mevcut pencereyi öne getir ve çık
        socket.write(b"SHOW")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        sys.exit(0)

    # Eski kalıntı soket varsa temizle ve dinlemeye başla
    QLocalServer.removeServer(SOCKET_NAME)
    server = QLocalServer()
    server.listen(SOCKET_NAME)

    # Uygulama ikonu (assets/pisim.png)
    icon_path = os.path.join(ASSETS_DIR, "pisim.png")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(ASSETS_DIR, "pisi.png")

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        app.setWindowIcon(QIcon.fromTheme("system-software-install"))

    start_minimized = "--minimized" in args or "-m" in args
    window = MainWindow(start_minimized=start_minimized)

    def _on_new_instance():
        client = server.nextPendingConnection()
        if client:
            client.waitForReadyRead(300)
            client.disconnectFromServer()
        window._show_window()

    server.newConnection.connect(_on_new_instance)

    if not start_minimized:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


