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
        
        # Sections
        "trending_apps": "Trending Applications",
        "editors_choice": "Editor's Choice",
        "see_all": "See All",
        "suggest_app": "+ Suggest App",
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
        "lupus_main_repo": "LupuS Main Repository",
        "lupus_community": "LupuS Community",
        "flathub_community": "FlatHub Community",
        "no_description": "PiSi package description not available.",
        "loading_flathub": "Description loading from Flathub...",

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

        # Sections
        "trending_apps": "Trend Uygulamalar",
        "editors_choice": "Editörün Seçimleri",
        "see_all": "Tümünü Gör",
        "suggest_app": "+ Uygulama Öner",
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
        "flatpak_pkg": "Flatpak Paket",
        "pisi_pkg": "PiSi Paket",
        "lupus_main_repo": "LupuS Ana Depo",
        "lupus_community": "LupuS Topluluğu",
        "flathub_community": "FlatHub Topluluğu",
        "no_description": "PiSi paket açıklaması mevcut değil.",
        "loading_flathub": "Açıklama Flathub'dan yükleniyor...",

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
