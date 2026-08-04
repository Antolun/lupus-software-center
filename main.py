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

from pisi_store.mainwindow import MainWindow

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "pisi_store", "assets")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PiSiM")
    app.setOrganizationName("TeknoAnka")
    app.setOrganizationDomain("https://www.teknoanka.com/")

    # Uygulama ikonu (assets/pisim.png)
    icon_path = os.path.join(ASSETS_DIR, "pisim.png")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(ASSETS_DIR, "pisi.png")

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        app.setWindowIcon(QIcon.fromTheme("system-software-install"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
