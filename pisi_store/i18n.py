"""
PiSiM – Internationalization (i18n) Module
Supports English (default) and Turkish. Automatically detects system locale.
"""

import os
import locale
from PyQt6.QtCore import QLocale

LANGUAGES = ["en", "tr"]

TRANSLATIONS = {
    "en": {
        # Navigation & Categories
        "nav_discover": "Discover",
        "nav_development": "Development",
        "nav_education": "Education",
        "nav_enterprise": "Enterprise",
        "nav_games": "Games",
        "nav_graphics": "Graphics",
        "nav_internet": "Internet",
        "nav_multimedia": "Multimedia",
        "nav_office": "Office",
        "nav_system": "System",
        "nav_utilities": "Utilities",
        "nav_flatpak": "Flatpak",
        "nav_updates": "Updates",
        "all_applications": "All Applications",
        "packages": "Packages",
        "search_placeholder": "🔍  Search applications...",
        "search_results_title": "Search Results...",
        "results_for": "Results for \"{query}\"",

        "unknown_developer": "Unknown Developer",
        
        # Sections
        "trending_apps": "Trending Applications",
        "editors_choice": "Editor's Choice",
        "see_all": "See All",
        "about": "About",
        
        # Buttons & Actions
        "btn_install": "Install",
        "btn_update": "Update",
        "btn_open": "Open",
        "btn_remove": "Remove",
        "installed_label": "✓ Installed",
        "btn_cancel": "✕ Cancel",
        "error_occurred": "Error Occurred",
        "btn_update_repo": " Update Repository",
        "btn_check_updates": " Check for Updates",
        "updating_repo": " Updating...",
        "checking_updates": " Checking...",

        # Hero Banner
        "hero_subtitle": "LUPUS iDEVICE MOUNTER",
        "hero_title": "Discover easy access to\nApple devices!",

        # App Details & Stats
        "rating": "Rating",
        "downloads": "Downloads",
        "size": "Size",
        "dependencies": "Dependencies",
        "version": "Version",
        "download_size": "Download Size",
        "required_space": "Required Disk Space",
        "type": "Type",
        "category": "Category",
        "license": "License",
        "repo_origin": "Repository / Origin",
        "developer": "Developer",
        "flatpak_pkg": "Flatpak Package",
        "pisi_pkg": "PiSi Package",
        "lupus_main_repo": "Main Repository",
        "lupus_community": "TeknoAnka",
        "flathub_community": "FlatHub",
        "packager_name": "Packager",
        "packager_email": "Packager Email",
        "update_date": "Last Update Date",
        "homepage": "Website",
        "vcs_url": "Source Code",
        "no_description": "PiSi package description not available.",
        "loading_flathub": "Description loading from FlatHub...",

        # Updates Section
        "downloads_and_updates": "Downloads & Updates ({count})",
        "updates_badge": "Updates ({count})",
        "updates_title": "Updates",

        # Dialogs & Messages
        "update_check_dialog": "Update Check",
        "updates_found_msg": "🎉 Found updates for {count} applications!",
        "system_up_to_date_msg": "✅ Your system is up to date! No updates found.",
        "repo_update_dialog": "Repository Update",
        "repo_update_success": "✅ PiSi repositories updated successfully!",
        "repo_update_error_title": "Repository Update Error",
        "repo_update_error_msg": "❌ Error updating repository:\n{message}",

        # Image Viewer Dialog
        "zoom_in": "🔍 +",
        "zoom_out": "🔍 -",
        "reset": "↺ Reset",
        "close": "✕ Close",

        # Loading Overlay
        "loading_app_title": "PiSiM",
        "loading_init": "Starting…",
        "loading_prep": "Preparing application…",
        "loading_check_installed": "Checking installed packages…",
        "loading_repo_pkgs": "Loading repository packages…",
        "loading_flatpak": "Loading Flatpak applications…",
        "loading_cache": "Loaded from cache",
        "loading_pisi_repos": "Loading packages from PiSi repositories…",
        "pisi_index_loaded": "Packages loaded from PiSi repository index.",
        "repo_changes_detected": "Repository changes detected, refreshing cache...",

        # Worker Messages
        "installed_success": "{name} installed successfully",
        "removed_success": "{name} uninstalled successfully",
        "cancelled": "Cancelled",
        "updating_pisi_repos": "Updating PiSi repositories...",
        "checking_updates_progress": "Checking for updates...",
        "checking_flatpak_updates": "Checking Flatpak updates...",
        "update_check_complete": "Update check complete.",

        # Settings & About
        "nav_settings": "Settings",
        "nav_about": "About",
        "settings_title": "Settings",
        "settings_section_general": "General & Startup",
        "settings_autostart": "Run on System Boot",
        "settings_autostart_desc": "Automatically start PiSiM in background when system boots",
        "settings_close_to_tray": "Run in Background When Closed",
        "settings_close_to_tray_desc": "Hide application window to system tray when pressing close button",
        "settings_section_updates": "Update Checker Settings",
        "settings_auto_check_interval": "Automatic Update Checking Frequency",
        "settings_auto_install_updates": "Automatically Install Updates",
        "settings_auto_install_updates_desc": "Automatically download and install application updates when available",
        "settings_section_language": "Language Options",
        "settings_language_label": "Application Language",
        "interval_disabled": "Disabled",
        "interval_1h": "Every 1 Hour",
        "interval_4h": "Every 4 Hours",
        "interval_12h": "Every 12 Hours",
        "interval_24h": "Daily (Every 24 Hours)",
        "tray_open_app": "Open PiSiM",
        "tray_check_updates": "Check for Updates",
        "tray_exit": "Exit",
        "updates_available_tooltip": "PiSiM - {count} updates available!",
        "notif_installing_title": "PiSiM - Installing in Background",
        "notif_installing_body": "{count} package(s) are being installed/updated...",
        "notif_installing_done_title": "PiSiM - Installation Complete",
        "notif_installing_done_body": "{pkg} has been successfully installed.",
        "notif_installing_error_title": "PiSiM - Installation Failed",
        "notif_installing_error_body": "An error occurred while installing {pkg}.",
        "notif_update_available_title": "PiSiM - Updates Available",
        "notif_update_available_body": "{count} application update(s) are ready.",
        "notif_action_run": "Run",
        "about_title": "About PiSiM",
        "about_app_name": "PiSiM - PiSi Market",
        "about_version": "Version 1.2",
        "about_description": "Modern package manager and application store for LupuS.",
        "about_developer": "Developed by TeknoAnka",
        "about_website": "Visit Website",
        "about_license": "License: GNU General Public License v3.0",

        # CLI Messages
        "cli_usage_title": "PiSiM - PiSi Market (v{version})",
        "cli_usage_section": "Usage:\n  pisim [OPTIONS]\n  pisim COMMAND [PARAMETERS]",
        "cli_options_section": "Options:\n  -h, --help                Show this help message\n  -v, --version             Show version information\n  -m, --minimized           Start application in system tray (background)",
        "cli_commands_section": "Console Commands:\n  search, -s <query>        Search for packages\n  list-installed, -l        List installed packages\n  list-updates, -u          List available application updates\n  install, -i <package>     Install specified package (e.g.: pisim install gimp)\n  remove, -r <package>      Remove specified package (e.g.: pisim remove gimp)\n  update-repo               Update package repositories\n  update-all                Download and install all available package updates",
        "cli_header": "📦 PiSiM Console Manager (v{version})",
        "cli_search_error": "❌ Error: You must enter a search query.\n   Usage: pisim search <query>",
        "cli_searching": "🔍 Searching packages for: '{query}'...",
        "cli_no_match": "❌ No matching packages found.",
        "cli_found_packages": "✅ Found Packages ({count}):",
        "cli_col_name": "Package Name",
        "cli_col_version": "Version",
        "cli_col_origin": "Origin",
        "cli_col_status": "Status",
        "cli_status_installed": "✓ Installed",
        "cli_status_installable": "Installable",
        "cli_status_update_avail": " (Update available!)",
        "cli_listing_installed": "📋 Listing Installed Packages...",
        "cli_no_installed": "No installed packages found.",
        "cli_installed_packages": "✅ Installed Packages ({count}):",
        "cli_col_update": "Update",
        "cli_upd_yes": "⬆ Yes!",
        "cli_upd_no": "Up to date",
        "cli_checking_updates": "🔄 Checking Available Updates...",
        "cli_all_up_to_date": "✨ All your packages are up to date!",
        "cli_upgradable_packages": "🚀 Upgradable Packages ({count}):",
        "cli_col_curr_ver": "Current Version",
        "cli_col_new_ver": "New Version",
        "cli_install_error": "❌ Error: Specify package name to install.\n   Usage: pisim install <package_name>",
        "cli_installing": "⬇ Installing package: {name} ...",
        "cli_remove_error": "❌ Error: Specify package name to remove.\n   Usage: pisim remove <package_name>",
        "cli_removing": "🗑 Removing package: {name} ...",
        "cli_updating_repo": "🔄 Updating package repositories...",
        "cli_repo_update_success": "✅ Repositories updated successfully.",
        "cli_checking_all_updates": "🔄 Checking all package updates...",
        "cli_no_updates_needed": "✨ No packages to update, your system is up to date!",
        "cli_updating_count": "📦 Updating {count} package(s)...",
        "cli_updating_item": " -> Updating: {name}",
        "cli_updated_item_ok": "    ✅ {name} updated.",
        "cli_updated_item_err": "    ❌ {name} failed to update: {msg}",
        "cli_err_prefix": "❌ Error: {msg}",
    },
    "tr": {
        # Navigation & Categories
        "nav_discover": "Keşfet",
        "nav_development": "Geliştirme",
        "nav_education": "Eğitim",
        "nav_enterprise": "Kurumsal",
        "nav_games": "Oyunlar",
        "nav_graphics": "Grafik",
        "nav_internet": "İnternet",
        "nav_multimedia": "Multimedya",
        "nav_office": "Ofis",
        "nav_system": "Sistem",
        "nav_utilities": "Araçlar",
        "nav_flatpak": "Flatpak",
        "nav_updates": "Güncellemeler",
        "all_applications": "Tüm Uygulamalar",
        "packages": "Paketler",
        "search_placeholder": "🔍  Uygulama ara...",
        "search_results_title": "Arama Sonuçları...",
        "results_for": "\"{query}\" için sonuçlar",

        "unknown_developer": "Bilinmeyen Geliştirici",

        # Sections
        "trending_apps": "Trend Uygulamalar",
        "editors_choice": "Editörün Seçimleri",
        "see_all": "Tümünü Gör",
        "about": "Hakkında",

        # Buttons & Actions
        "btn_install": "Kur",
        "btn_update": "Güncelle",
        "btn_open": "Aç",
        "btn_remove": "Sil",
        "installed_label": "✓ Kuruldu",
        "btn_cancel": "✕ İptal",
        "error_occurred": "Hata Oluştu",
        "btn_update_repo": " Depoyu Güncelle",
        "btn_check_updates": " Güncellemeleri Denetle",
        "updating_repo": " Güncelleniyor...",
        "checking_updates": " Denetleniyor...",

        # Hero Banner
        "hero_subtitle": "LUPUS iDEVICE MOUNTER",
        "hero_title": "Apple cihazlarına kolay\nerişimi keşfedin!",

        # App Details & Stats
        "rating": "Puanlama",
        "downloads": "İndirme",
        "size": "Boyut",
        "dependencies": "Bağımlılık",
        "version": "Versiyon",
        "download_size": "İndirme Boyutu",
        "required_space": "Gerekli Disk Alanı",
        "type": "Tür",
        "category": "Kategori",
        "license": "Lisans",
        "repo_origin": "Depo / Kaynak",
        "developer": "Geliştirici",
        "flatpak_pkg": "Flatpak Paketi",
        "pisi_pkg": "PiSi Paketi",
        "lupus_main_repo": "Ana Depo",
        "lupus_community": "TeknoAnka",
        "flathub_community": "FlatHub",
        "packager_name": "Paketleyici",
        "packager_email": "Paketleyici E-Posta",
        "update_date": "Son Güncelleme",
        "homepage": "Web Sitesi",
        "vcs_url": "Kaynak Kod Deposu",
        "no_description": "PiSi paket açıklaması mevcut değil.",
        "loading_flathub": "Açıklama FlatHub'dan yükleniyor...",

        # Updates Section
        "downloads_and_updates": "İndirilenler & Güncellemeler ({count})",
        "updates_badge": "Güncellemeler ({count})",
        "updates_title": "Güncellemeler",

        # Dialogs & Messages
        "update_check_dialog": "Güncelleme Kontrolü",
        "updates_found_msg": "🎉 {count} adet uygulama için güncelleme bulundu!",
        "system_up_to_date_msg": "✅ Sisteminiz güncel! Herhangi bir güncelleme bulunamadı.",
        "repo_update_dialog": "Depo Güncelleme",
        "repo_update_success": "✅ PiSi depoları başarıyla güncellendi!",
        "repo_update_error_title": "Depo Güncelleme Hatası",
        "repo_update_error_msg": "❌ Depo güncellenirken bir hata oluştu:\n{message}",

        # Image Viewer Dialog
        "zoom_in": "🔍 +",
        "zoom_out": "🔍 -",
        "reset": "↺ Sıfırla",
        "close": "✕ Kapat",

        # Loading Overlay
        "loading_app_title": "PiSiM",
        "loading_init": "Başlatılıyor…",
        "loading_prep": "Uygulama hazırlanıyor…",
        "loading_check_installed": "Kurulu paketler kontrol ediliyor…",
        "loading_repo_pkgs": "Depo paket listesi yükleniyor…",
        "loading_flatpak": "Flatpak uygulamaları yükleniyor…",
        "loading_cache": "Önbellekten yüklendi",
        "loading_pisi_repos": "PiSi depolarından paketler yükleniyor...",
        "pisi_index_loaded": "PiSi deposu indeksinden paketler yüklendi.",
        "repo_changes_detected": "Depoda değişiklik tespit edildi, önbellek yenileniyor...",

        # Worker Messages
        "installed_success": "{name} başarıyla kuruldu",
        "removed_success": "{name} başarıyla kaldırıldı",
        "cancelled": "İptal edildi",
        "updating_pisi_repos": "PiSi depoları güncelleniyor...",
        "checking_updates_progress": "Güncellemeler kontrol ediliyor...",
        "checking_flatpak_updates": "Flatpak güncellemeleri kontrol ediliyor...",
        "update_check_complete": "Güncelleme kontrolü tamamlandı.",

        # Settings & About
        "nav_settings": "Ayarlar",
        "nav_about": "Hakkında",
        "settings_title": "Ayarlar",
        "settings_section_general": "Genel ve Başlangıç",
        "settings_autostart": "Sistem Açılışında Başlat (Başlangıçta Çalıştır)",
        "settings_autostart_desc": "Sistem açıldığında PiSiM arka planda otomatik olarak çalışır",
        "settings_close_to_tray": "Kapatıldığında Arka Planda Çalış",
        "settings_close_to_tray_desc": "Kapat butonuna basıldığında uygulamayı görev çubuğu tepsisine küçültür",
        "settings_section_updates": "Güncelleme Denetleyici Ayarları",
        "settings_auto_check_interval": "Otomatik Güncelleme Denetleme Sıklığı",
        "settings_auto_install_updates": "Güncellemeleri Otomatik Yükle",
        "settings_auto_install_updates_desc": "Yeni güncellemeler bulunduğunda arka planda otomatik olarak indirir ve kurar",
        "settings_section_language": "Dil Seçenekleri",
        "settings_language_label": "Uygulama Dili",
        "interval_disabled": "Devre Dışı",
        "interval_1h": "Her 1 Saatte Bir",
        "interval_4h": "Her 4 Saatte Bir",
        "interval_12h": "Her 12 Saatte Bir",
        "interval_24h": "Günde Bir (24 Saat)",
        "tray_open_app": "PiSiM'i Aç",
        "tray_check_updates": "Güncellemeleri Denetle",
        "tray_exit": "Çıkış",
        "updates_available_tooltip": "PiSiM - {count} güncelleme mevcut!",
        "notif_installing_title": "PiSiM - Arka Planda Yükleniyor",
        "notif_installing_body": "{count} paket yükleniyor/güncelleniyor...",
        "notif_installing_done_title": "PiSiM - Yükleme Tamamlandı",
        "notif_installing_done_body": "{pkg} başarıyla yüklendi.",
        "notif_installing_error_title": "PiSiM - Yükleme Başarısız",
        "notif_installing_error_body": "{pkg} yüklenirken hata oluştu.",
        "notif_update_available_title": "PiSiM - Güncellemeler Mevcut",
        "notif_update_available_body": "{count} uygulama güncellemesi hazır.",
        "notif_action_run": "Çalıştır",
        "about_title": "PiSiM Hakkında",
        "about_app_name": "PiSiM - PiSi Market",
        "about_version": "Sürüm 1.2",
        "about_description": "LupuS için modern paket yöneticisi ve uygulama mağazası.",
        "about_developer": "TeknoAnka tarafından geliştirilmiştir",
        "about_website": "Web Sitesini Ziyaret Et",
        "about_license": "Lisans: GNU Genel Kamu Lisansı v3.0",

        # CLI Messages
        "cli_usage_title": "PiSiM - PiSi Market (v{version})",
        "cli_usage_section": "Kullanım:\n  pisim [SEÇENEKLER]\n  pisim KOMUT [PARAMETRELER]",
        "cli_options_section": "Seçenekler:\n  -h, --help                Bu yardım mesajını gösterir\n  -v, --version             Sürüm bilgisini gösterir\n  -m, --minimized           Uygulamayı sistem tepsisinde (arka planda) başlatır",
        "cli_commands_section": "Konsol Komutları:\n  search, -s <sorgu>        Paketlerde arama yapar\n  list-installed, -l        Yüklü paketleri listeler\n  list-updates, -u          Mevcut uygulama güncellemelerini listeler\n  install, -i <paket>       Belirtilen paketi kurar (Örn: pisim install gimp)\n  remove, -r <paket>        Belirtilen paketi kaldırır (Örn: pisim remove gimp)\n  update-repo               Paket depolarını günceller\n  update-all                Tüm mevcut paket güncellemelerini indirip kurar",
        "cli_header": "📦 PiSiM Konsol Yöneticisi (v{version})",
        "cli_search_error": "❌ Hata: Arama yapmak için bir kelime girmelisiniz.\n   Kullanım: pisim search <kelime>",
        "cli_searching": "🔍 Paketlerde aranıyor: '{query}'...",
        "cli_no_match": "❌ Eşleşen paket bulunamadı.",
        "cli_found_packages": "✅ Bulunan Paketler ({count}):",
        "cli_col_name": "Paket Adı",
        "cli_col_version": "Sürüm",
        "cli_col_origin": "Kaynak",
        "cli_col_status": "Durum",
        "cli_status_installed": "✓ Yüklü",
        "cli_status_installable": "Kurulabilir",
        "cli_status_update_avail": " (Güncelleme var!)",
        "cli_listing_installed": "📋 Yüklü Paketler Listeleniyor...",
        "cli_no_installed": "Yüklü paket bulunamadı.",
        "cli_installed_packages": "✅ Yüklü Paketler ({count}):",
        "cli_col_update": "Güncelleme",
        "cli_upd_yes": "⬆ Var!",
        "cli_upd_no": "Güncel",
        "cli_checking_updates": "🔄 Mevcut Güncellemeler Denetleniyor...",
        "cli_all_up_to_date": "✨ Tüm paketleriniz güncel!",
        "cli_upgradable_packages": "🚀 Güncellenebilir Paketler ({count}):",
        "cli_col_curr_ver": "Mevcut Sürüm",
        "cli_col_new_ver": "Yeni Sürüm",
        "cli_install_error": "❌ Hata: Kurulacak paket adını belirtin.\n   Kullanım: pisim install <paket_adı>",
        "cli_installing": "⬇ Paket kuruluyor: {name} ...",
        "cli_remove_error": "❌ Hata: Kaldırılacak paket adını belirtin.\n   Kullanım: pisim remove <paket_adı>",
        "cli_removing": "🗑 Paket kaldırılıyor: {name} ...",
        "cli_updating_repo": "🔄 Paket depoları güncelleniyor...",
        "cli_repo_update_success": "✅ Depolar başarıyla güncellendi.",
        "cli_checking_all_updates": "🔄 Tüm paket güncellemeleri kontrol ediliyor...",
        "cli_no_updates_needed": "✨ Güncellenecek paket yok, sisteminiz güncel!",
        "cli_updating_count": "📦 {count} adet paket güncelleniyor...",
        "cli_updating_item": " -> Güncelleniyor: {name}",
        "cli_updated_item_ok": "    ✅ {name} güncellendi.",
        "cli_updated_item_err": "    ❌ {name} güncellenemedi: {msg}",
        "cli_err_prefix": "❌ Hata: {msg}",
    }
}

class I18n:
    _current_lang = "en"  # Default is English

    @classmethod
    def init(cls):
        """Auto-detect system language. Defaults to English ('en') unless system language is Turkish ('tr')."""
        try:
            sys_locale = QLocale.system().name().lower()
            if sys_locale.startswith("tr"):
                cls._current_lang = "tr"
                return
        except Exception:
            pass

        try:
            default_loc = locale.getdefaultlocale()[0] or ""
            if default_loc.lower().startswith("tr"):
                cls._current_lang = "tr"
                return
        except Exception:
            pass

        try:
            lang_env = os.environ.get("LANG", "").lower()
            if lang_env.startswith("tr"):
                cls._current_lang = "tr"
                return
        except Exception:
            pass

        cls._current_lang = "en"

    @classmethod
    def get_lang(cls) -> str:
        return cls._current_lang

    @classmethod
    def set_lang(cls, lang: str):
        if lang in LANGUAGES:
            cls._current_lang = lang

    @classmethod
    def tr(cls, key: str, **kwargs) -> str:
        lang_dict = TRANSLATIONS.get(cls._current_lang, TRANSLATIONS["en"])
        template = lang_dict.get(key) or TRANSLATIONS["en"].get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template

# Initialize on module import
I18n.init()
tr = I18n.tr
