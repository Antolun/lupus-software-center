"""
PiSiM – Ayarlar ve Yapılandırma Yönetimi Modülü
Uygulama ayarlarını (~/.config/pisim/settings.json) ve başlangıçta çalıştırma (autostart) işlemlerini yönetir.
"""

import os
import sys
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "pisim"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "com.teknoanka.pisim.desktop"

DEFAULT_SETTINGS = {
    "autostart": False,
    "check_interval_hours": 4,  # 0: Devre dışı, 1, 4, 12, 24 saat
    "close_to_tray": True,
    "auto_install_updates": False,  # Güncellemeleri otomatik indirip kurma
    "language": "en"
}


class SettingsManager:
    @staticmethod
    def load_settings() -> dict:
        """Ayarları JSON dosyasından okur, yoksa varsayılan değerleri döndürür."""
        if not SETTINGS_FILE.exists():
            SettingsManager.save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_SETTINGS.copy()
                merged.update(data)
                return merged
        except Exception as e:
            print(f"Ayarlar okunurken hata oluştu: {e}")
            return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save_settings(settings: dict):
        """Ayarları JSON dosyasına kaydeder."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ayarlar kaydedilirken hata oluştu: {e}")

    @staticmethod
    def is_autostart_enabled() -> bool:
        """Başlangıçta çalıştır masaüstü dosyasının varlığını kontrol eder."""
        return AUTOSTART_FILE.exists()

    @staticmethod
    def set_autostart(enabled: bool):
        """Sistem başlangıcında çalıştırma (.desktop dosyası) özelliğini ayarlar."""
        try:
            if enabled:
                AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
                main_py = os.path.abspath(sys.argv[0])
                executable = sys.executable
                desktop_entry = f"""[Desktop Entry]
Type=Application
Name=PiSiM
Comment=PiSi Market
Exec=pisim --minimized
Icon=pisim
Terminal=false
Categories=System;PackageManager;
X-GNOME-Autostart-enabled=true
StartupNotify=false
"""
                with open(AUTOSTART_FILE, "w", encoding="utf-8") as f:
                    f.write(desktop_entry)
            else:
                if AUTOSTART_FILE.exists():
                    AUTOSTART_FILE.unlink()
        except Exception as e:
            print(f"Başlangıçta çalıştırma ayarı güncellenirken hata: {e}")
