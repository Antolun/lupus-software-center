// PiSiM – i18n (Internationalization)
// Python i18n.py'nin Rust karşılığı

use std::collections::HashMap;
use std::sync::OnceLock;

static LANG: OnceLock<std::sync::Mutex<String>> = OnceLock::new();

fn lang_mutex() -> &'static std::sync::Mutex<String> {
    LANG.get_or_init(|| std::sync::Mutex::new(detect_system_lang()))
}

pub fn get_lang() -> String {
    lang_mutex().lock().unwrap().clone()
}

pub fn set_lang(lang: &str) {
    if lang == "en" || lang == "tr" {
        *lang_mutex().lock().unwrap() = lang.to_string();
    }
}

pub fn tr(key: &str) -> String {
    tr_with(key, &[])
}

pub fn tr_with(key: &str, args: &[(&str, &str)]) -> String {
    let lang = get_lang();
    let translations = get_translations();
    let dict = translations.get(lang.as_str())
        .or_else(|| translations.get("en"))
        .cloned()
        .unwrap_or_default();
    
    let mut template = dict.get(key)
        .cloned()
        .unwrap_or_else(|| {
            translations.get("en")
                .and_then(|d| d.get(key))
                .cloned()
                .unwrap_or_else(|| key.to_string())
        });
    
    for (k, v) in args {
        template = template.replace(&format!("{{{}}}", k), v);
    }
    template
}

fn detect_system_lang() -> String {
    let lang_env = std::env::var("LANG").unwrap_or_default().to_lowercase();
    if lang_env.starts_with("tr") {
        return "tr".to_string();
    }
    let lc_all = std::env::var("LC_ALL").unwrap_or_default().to_lowercase();
    if lc_all.starts_with("tr") {
        return "tr".to_string();
    }
    "en".to_string()
}

fn get_translations() -> HashMap<&'static str, HashMap<&'static str, String>> {
    let mut map = HashMap::new();
    
    let mut en = HashMap::new();
    en.insert("nav_discover", "Discover".into());
    en.insert("nav_development", "Development".into());
    en.insert("nav_education", "Education".into());
    en.insert("nav_enterprise", "Enterprise".into());
    en.insert("nav_games", "Games".into());
    en.insert("nav_graphics", "Graphics".into());
    en.insert("nav_internet", "Internet".into());
    en.insert("nav_multimedia", "Multimedia".into());
    en.insert("nav_office", "Office".into());
    en.insert("nav_system", "System".into());
    en.insert("nav_utilities", "Utilities".into());
    en.insert("nav_flatpak", "Flatpak".into());
    en.insert("nav_updates", "Updates".into());
    en.insert("nav_settings", "Settings".into());
    en.insert("nav_about", "About".into());
    en.insert("all_applications", "All Applications".into());
    en.insert("packages", "Packages".into());
    en.insert("search_placeholder", "🔍  Search applications...".into());
    en.insert("search_results_title", "Search Results...".into());
    en.insert("results_for", "Results for \"{query}\"".into());
    en.insert("unknown_developer", "Unknown Developer".into());
    en.insert("trending_apps", "Trending Applications".into());
    en.insert("editors_choice", "Editor's Choice".into());
    en.insert("see_all", "See All".into());
    en.insert("about", "About".into());
    en.insert("btn_install", "Install".into());
    en.insert("btn_update", "Update".into());
    en.insert("btn_open", "Open".into());
    en.insert("btn_remove", "Remove".into());
    en.insert("installed_label", "✓ Installed".into());
    en.insert("btn_cancel", "✕ Cancel".into());
    en.insert("error_occurred", "Error Occurred".into());
    en.insert("btn_update_repo", " Update Repository".into());
    en.insert("btn_check_updates", " Check for Updates".into());
    en.insert("updating_repo", " Updating...".into());
    en.insert("checking_updates", " Checking...".into());
    en.insert("hero_subtitle", "LUPUS iDEVICE MOUNTER".into());
    en.insert("hero_title", "Discover easy access to\nApple devices!".into());
    en.insert("rating", "Rating".into());
    en.insert("downloads", "Downloads".into());
    en.insert("size", "Size".into());
    en.insert("dependencies", "Dependencies".into());
    en.insert("version", "Version".into());
    en.insert("download_size", "Download Size".into());
    en.insert("required_space", "Required Disk Space".into());
    en.insert("type", "Type".into());
    en.insert("category", "Category".into());
    en.insert("license", "License".into());
    en.insert("repo_origin", "Repository / Origin".into());
    en.insert("developer", "Developer".into());
    en.insert("flatpak_pkg", "Flatpak Package".into());
    en.insert("pisi_pkg", "PiSi Package".into());
    en.insert("lupus_main_repo", "Main Repository".into());
    en.insert("lupus_community", "Antolun".into());
    en.insert("flathub_community", "FlatHub".into());
    en.insert("packager_name", "Packager".into());
    en.insert("packager_email", "Packager Email".into());
    en.insert("update_date", "Last Update Date".into());
    en.insert("homepage", "Website".into());
    en.insert("vcs_url", "Source Code".into());
    en.insert("no_description", "PiSi package description not available.".into());
    en.insert("no_packages_in_category", "No packages found in this category.".into());
    en.insert("no_updates_installed", "All your applications are up to date.".into());
    en.insert("settings_saved", "Settings saved".into());
    en.insert("autostart_updated", "Autostart setting updated".into());
    en.insert("repo_update_error", "Repository could not be updated".into());
    en.insert("flathub_fetch_failed", "FlatHub request failed".into());
    en.insert("pkg_not_found", "Package not found".into());
    en.insert("pisi_missing", "pisi command not found".into());
    en.insert("loading_flathub", "Description loading from FlatHub...".into());
    en.insert("downloads_and_updates", "Downloads & Updates ({count})".into());
    en.insert("updates_badge", "Updates ({count})".into());
    en.insert("updates_title", "Updates".into());
    en.insert("update_check_dialog", "Update Check".into());
    en.insert("updates_found_msg", "🎉 Found updates for {count} applications!".into());
    en.insert("system_up_to_date_msg", "✅ Your system is up to date! No updates found.".into());
    en.insert("repo_update_dialog", "Repository Update".into());
    en.insert("repo_update_success", "✅ PiSi repositories updated successfully!".into());
    en.insert("repo_update_error_title", "Repository Update Error".into());
    en.insert("repo_update_error_msg", "❌ Error updating repository:\n{message}".into());
    en.insert("zoom_in", "🔍 +".into());
    en.insert("zoom_out", "🔍 -".into());
    en.insert("reset", "↺ Reset".into());
    en.insert("close", "✕ Close".into());
    en.insert("loading_app_title", "PiSiM".into());
    en.insert("loading_init", "Starting…".into());
    en.insert("loading_prep", "Preparing application…".into());
    en.insert("loading_check_installed", "Checking installed packages…".into());
    en.insert("loading_repo_pkgs", "Loading repository packages…".into());
    en.insert("loading_flatpak", "Loading Flatpak applications…".into());
    en.insert("loading_cache", "Loaded from cache".into());
    en.insert("loading_pisi_repos", "Loading packages from PiSi repositories…".into());
    en.insert("pisi_index_loaded", "Packages loaded from PiSi repository index.".into());
    en.insert("installed_success", "{name} installed successfully".into());
    en.insert("removed_success", "{name} uninstalled successfully".into());
    en.insert("cancelled", "Cancelled".into());
    en.insert("settings_title", "Settings".into());
    en.insert("settings_section_general", "General & Startup".into());
    en.insert("settings_autostart", "Run on System Boot".into());
    en.insert("settings_autostart_desc", "Automatically start PiSiM in background when system boots".into());
    en.insert("settings_close_to_tray", "Run in Background When Closed".into());
    en.insert("settings_close_to_tray_desc", "Hide application window to system tray when pressing close button".into());
    en.insert("settings_section_updates", "Update Checker Settings".into());
    en.insert("settings_auto_check_interval", "Automatic Update Checking Frequency".into());
    en.insert("settings_auto_install_updates", "Automatically Install Updates".into());
    en.insert("settings_auto_install_updates_desc", "Automatically download and install application updates when available".into());
    en.insert("settings_section_language", "Language Options".into());
    en.insert("settings_language_label", "Application Language".into());
    en.insert("interval_disabled", "Disabled".into());
    en.insert("interval_1h", "Every 1 Hour".into());
    en.insert("interval_4h", "Every 4 Hours".into());
    en.insert("interval_12h", "Every 12 Hours".into());
    en.insert("interval_24h", "Daily (Every 24 Hours)".into());
    en.insert("tray_open_app", "Open PiSiM".into());
    en.insert("tray_check_updates", "Check for Updates".into());
    en.insert("tray_exit", "Exit".into());
    en.insert("about_title", "About PiSiM".into());
    en.insert("about_app_name", "PiSiM - PiSi Market".into());
    en.insert("about_version", "Version 2.0.0".into());
    en.insert("about_description", "Modern package manager and application store for LupuS.".into());
    en.insert("about_developer", "Developed by Antolun".into());
    en.insert("about_website", "Visit Website".into());
    en.insert("about_license", "License: GNU General Public License v3.0".into());

    let mut tr_map = HashMap::new();
    tr_map.insert("nav_discover", "Keşfet".into());
    tr_map.insert("nav_development", "Geliştirme".into());
    tr_map.insert("nav_education", "Eğitim".into());
    tr_map.insert("nav_enterprise", "Kurumsal".into());
    tr_map.insert("nav_games", "Oyunlar".into());
    tr_map.insert("nav_graphics", "Grafik".into());
    tr_map.insert("nav_internet", "İnternet".into());
    tr_map.insert("nav_multimedia", "Multimedya".into());
    tr_map.insert("nav_office", "Ofis".into());
    tr_map.insert("nav_system", "Sistem".into());
    tr_map.insert("nav_utilities", "Araçlar".into());
    tr_map.insert("nav_flatpak", "Flatpak".into());
    tr_map.insert("nav_updates", "Güncellemeler".into());
    tr_map.insert("nav_settings", "Ayarlar".into());
    tr_map.insert("nav_about", "Hakkında".into());
    tr_map.insert("all_applications", "Tüm Uygulamalar".into());
    tr_map.insert("packages", "Paketler".into());
    tr_map.insert("search_placeholder", "🔍  Uygulama ara...".into());
    tr_map.insert("search_results_title", "Arama Sonuçları...".into());
    tr_map.insert("results_for", "\"{query}\" için sonuçlar".into());
    tr_map.insert("unknown_developer", "Bilinmeyen Geliştirici".into());
    tr_map.insert("trending_apps", "Trend Uygulamalar".into());
    tr_map.insert("editors_choice", "Editörün Seçimleri".into());
    tr_map.insert("see_all", "Tümünü Gör".into());
    tr_map.insert("about", "Hakkında".into());
    tr_map.insert("btn_install", "Kur".into());
    tr_map.insert("btn_update", "Güncelle".into());
    tr_map.insert("btn_open", "Aç".into());
    tr_map.insert("btn_remove", "Sil".into());
    tr_map.insert("installed_label", "✓ Kuruldu".into());
    tr_map.insert("btn_cancel", "✕ İptal".into());
    tr_map.insert("error_occurred", "Hata Oluştu".into());
    tr_map.insert("btn_update_repo", " Depoyu Güncelle".into());
    tr_map.insert("btn_check_updates", " Güncellemeleri Denetle".into());
    tr_map.insert("updating_repo", " Güncelleniyor...".into());
    tr_map.insert("checking_updates", " Denetleniyor...".into());
    tr_map.insert("hero_subtitle", "LUPUS iDEVICE MOUNTER".into());
    tr_map.insert("hero_title", "Apple cihazlarına kolay\nerişimi keşfedin!".into());
    tr_map.insert("rating", "Puanlama".into());
    tr_map.insert("downloads", "İndirme".into());
    tr_map.insert("size", "Boyut".into());
    tr_map.insert("dependencies", "Bağımlılık".into());
    tr_map.insert("version", "Versiyon".into());
    tr_map.insert("download_size", "İndirme Boyutu".into());
    tr_map.insert("required_space", "Gerekli Disk Alanı".into());
    tr_map.insert("type", "Tür".into());
    tr_map.insert("category", "Kategori".into());
    tr_map.insert("license", "Lisans".into());
    tr_map.insert("repo_origin", "Depo / Kaynak".into());
    tr_map.insert("developer", "Geliştirici".into());
    tr_map.insert("flatpak_pkg", "Flatpak Paketi".into());
    tr_map.insert("pisi_pkg", "PiSi Paketi".into());
    tr_map.insert("lupus_main_repo", "Ana Depo".into());
    tr_map.insert("lupus_community", "Antolun".into());
    tr_map.insert("flathub_community", "FlatHub".into());
    tr_map.insert("packager_name", "Paketleyici".into());
    tr_map.insert("packager_email", "Paketleyici E-Posta".into());
    tr_map.insert("update_date", "Son Güncelleme".into());
    tr_map.insert("homepage", "Web Sitesi".into());
    tr_map.insert("vcs_url", "Kaynak Kod Deposu".into());
    tr_map.insert("no_description", "PiSi paket açıklaması mevcut değil.".into());
    tr_map.insert("no_packages_in_category", "Bu kategoride henüz paket bulunmuyor.".into());
    tr_map.insert("no_updates_installed", "Tüm uygulamalarınız güncel.".into());
    tr_map.insert("settings_saved", "Ayarlar kaydedildi".into());
    tr_map.insert("autostart_updated", "Başlangıç ayarı güncellendi".into());
    tr_map.insert("repo_update_error", "Depo güncellenemedi".into());
    tr_map.insert("flathub_fetch_failed", "FlatHub API isteği başarısız".into());
    tr_map.insert("pkg_not_found", "Paket bulunamadı".into());
    tr_map.insert("pisi_missing", "pisi komutu bulunamadı".into());
    tr_map.insert("loading_flathub", "Açıklama FlatHub'dan yükleniyor...".into());
    tr_map.insert("downloads_and_updates", "İndirilenler & Güncellemeler ({count})".into());
    tr_map.insert("updates_badge", "Güncellemeler ({count})".into());
    tr_map.insert("updates_title", "Güncellemeler".into());
    tr_map.insert("update_check_dialog", "Güncelleme Kontrolü".into());
    tr_map.insert("updates_found_msg", "🎉 {count} adet uygulama için güncelleme bulundu!".into());
    tr_map.insert("system_up_to_date_msg", "✅ Sisteminiz güncel! Herhangi bir güncelleme bulunamadı.".into());
    tr_map.insert("repo_update_success", "✅ PiSi depoları başarıyla güncellendi!".into());
    tr_map.insert("zoom_in", "🔍 +".into());
    tr_map.insert("zoom_out", "🔍 -".into());
    tr_map.insert("reset", "↺ Sıfırla".into());
    tr_map.insert("close", "✕ Kapat".into());
    tr_map.insert("loading_app_title", "PiSiM".into());
    tr_map.insert("loading_init", "Başlatılıyor…".into());
    tr_map.insert("loading_prep", "Uygulama hazırlanıyor…".into());
    tr_map.insert("loading_check_installed", "Kurulu paketler kontrol ediliyor…".into());
    tr_map.insert("loading_repo_pkgs", "Depo paket listesi yükleniyor…".into());
    tr_map.insert("loading_flatpak", "Flatpak uygulamaları yükleniyor…".into());
    tr_map.insert("loading_cache", "Önbellekten yüklendi".into());
    tr_map.insert("installed_success", "{name} başarıyla kuruldu".into());
    tr_map.insert("removed_success", "{name} başarıyla kaldırıldı".into());
    tr_map.insert("cancelled", "İptal edildi".into());
    tr_map.insert("settings_title", "Ayarlar".into());
    tr_map.insert("settings_section_general", "Genel ve Başlangıç".into());
    tr_map.insert("settings_autostart", "Sistem Açılışında Başlat".into());
    tr_map.insert("settings_autostart_desc", "Sistem açıldığında PiSiM arka planda otomatik olarak çalışır".into());
    tr_map.insert("settings_close_to_tray", "Kapatıldığında Arka Planda Çalış".into());
    tr_map.insert("settings_close_to_tray_desc", "Kapat butonuna basıldığında uygulamayı görev çubuğu tepsisine küçültür".into());
    tr_map.insert("settings_section_updates", "Güncelleme Denetleyici Ayarları".into());
    tr_map.insert("settings_auto_check_interval", "Otomatik Güncelleme Denetleme Sıklığı".into());
    tr_map.insert("settings_auto_install_updates", "Güncellemeleri Otomatik Yükle".into());
    tr_map.insert("settings_auto_install_updates_desc", "Yeni güncellemeler bulunduğunda arka planda otomatik olarak indirir ve kurar".into());
    tr_map.insert("settings_section_language", "Dil Seçenekleri".into());
    tr_map.insert("settings_language_label", "Uygulama Dili".into());
    tr_map.insert("interval_disabled", "Devre Dışı".into());
    tr_map.insert("interval_1h", "Her 1 Saatte Bir".into());
    tr_map.insert("interval_4h", "Her 4 Saatte Bir".into());
    tr_map.insert("interval_12h", "Her 12 Saatte Bir".into());
    tr_map.insert("interval_24h", "Günde Bir (24 Saat)".into());
    tr_map.insert("tray_open_app", "PiSiM'i Aç".into());
    tr_map.insert("tray_check_updates", "Güncellemeleri Denetle".into());
    tr_map.insert("tray_exit", "Çıkış".into());
    tr_map.insert("about_title", "PiSiM Hakkında".into());
    tr_map.insert("about_app_name", "PiSiM - PiSi Market".into());
    tr_map.insert("about_version", "Sürüm 2.0.0".into());
    tr_map.insert("about_description", "LupuS için modern paket yöneticisi ve uygulama mağazası.".into());
    tr_map.insert("about_developer", "Antolun tarafından geliştirilmiştir".into());
    tr_map.insert("about_website", "Web Sitesini Ziyaret Et".into());
    tr_map.insert("about_license", "Lisans: GNU Genel Kamu Lisansı v3.0".into());

    map.insert("en", en);
    map.insert("tr", tr_map);
    map
}
