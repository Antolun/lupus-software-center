// PiSiM - Backend: Paket veri yapıları ve işlemleri
// Python backend.py'nin Rust karşılığı

use crate::i18n;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use std::process::Command;

// ─── Sabitler ──────────────────────────────────────────────────────────────

pub const VERSION: &str = "2.0.0";

pub const ICON_SEARCH_PATHS: &[&str] = &[
    "/usr/share/icons/hicolor/scalable/apps",
    "/usr/share/icons/hicolor/256x256/apps",
    "/usr/share/icons/hicolor/128x128/apps",
    "/usr/share/icons/hicolor/64x64/apps",
    "/usr/share/icons/hicolor/48x48/apps",
    "/usr/share/icons/hicolor/32x32/apps",
    "/usr/share/pixmaps",
    "/usr/share/icons",
    "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/64x64/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/48x48/apps",
];

pub const ICON_EXTENSIONS: &[&str] = &[".png", ".xpm", ".jpg", ".svg"];

// ─── Paket Bilgisi Yapısı ──────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PackageInfo {
    pub name: String,
    pub display_name: String,
    pub version: String,
    pub release: String,
    pub summary: String,
    pub description: String,
    pub license: String,
    pub homepage: String,
    pub packager_name: String,
    pub packager_email: String,
    pub developer: String,
    pub category: String,
    pub component: String,
    pub is_a: String,
    pub icon_name: String,
    pub icon_path: String,
    pub installed: bool,
    pub has_update: bool,
    pub new_version: String,
    pub rating: f32,
    pub downloads: i64,
    pub download_size: String,
    pub installed_size: String,
    pub dependencies_count: i32,
    pub tags: Vec<String>,
    pub is_flatpak: bool,
    pub origin: String,
    pub screenshots: Vec<String>,
    pub update_date: String,
    pub vcs_url: String,
}

impl PackageInfo {
    pub fn new(name: &str) -> Self {
        let display = if name.chars().all(|c| c.is_lowercase() || c.is_numeric() || c == '-' || c == '_') {
            let mut s = name.to_string();
            if let Some(r) = s.get_mut(0..1) {
                r.make_ascii_uppercase();
            }
            s
        } else {
            name.to_string()
        };
        Self {
            name: name.to_string(),
            display_name: display,
            version: String::new(),
            release: String::new(),
            summary: String::new(),
            description: String::new(),
            license: String::new(),
            homepage: String::new(),
            packager_name: String::new(),
            packager_email: String::new(),
            developer: String::new(),
            category: "utilities".to_string(),
            component: "main".to_string(),
            is_a: "app:gui".to_string(),
            icon_name: name.to_string(),
            icon_path: String::new(),
            installed: false,
            has_update: false,
            new_version: String::new(),
            rating: 4.5,
            downloads: 0,
            download_size: String::new(),
            installed_size: String::new(),
            dependencies_count: 0,
            tags: vec![],
            is_flatpak: false,
            origin: "Pisi".to_string(),
            screenshots: vec![],
            update_date: String::new(),
            vcs_url: String::new(),
        }
    }
}

// ─── PisiBackend ──────────────────────────────────────────────────────────

#[derive(Default)]
pub struct PisiBackend {
    pub installed_packages: HashMap<String, PackageInfo>,
    pub available_packages: HashMap<String, PackageInfo>,
    pub pisi_available: bool,
    pub flatpak_available: bool,
}

impl PisiBackend {
    pub fn new() -> Self {
        let pisi_available = check_command_available("pisi");
        let flatpak_available = check_command_available("flatpak");
        let mut backend = Self {
            installed_packages: HashMap::new(),
            available_packages: HashMap::new(),
            pisi_available,
            flatpak_available,
        };
        if pisi_available {
            backend.load_installed_packages();
            backend.load_available_packages();
        }
        if flatpak_available {
            backend.load_installed_flatpaks();
            backend.load_available_flatpaks();
        }
        backend
    }

    pub fn load_installed_packages(&mut self) {
        if !self.pisi_available {
            return;
        }
        let output = Command::new("pisi")
            .arg("list-installed")
            .output();

        if let Ok(out) = output {
            if out.status.success() {
                let text = String::from_utf8_lossy(&out.stdout);
                self.parse_pisi_list_output(&text, true);
            }
        }
    }

    pub fn load_available_packages(&mut self) {
        if self.pisi_available {
            let output = Command::new("pisi")
                .arg("list-available")
                .output();
            if let Ok(out) = output {
                if out.status.success() {
                    let text = String::from_utf8_lossy(&out.stdout);
                    self.parse_pisi_list_output(&text, false);
                }
            }
        }
        // Kurulu paketleri güncelle
        let installed_names: Vec<String> = self.installed_packages.keys().cloned().collect();
        for name in installed_names {
            if let Some(pkg) = self.available_packages.get_mut(&name) {
                pkg.installed = true;
            }
        }
    }

    fn parse_pisi_list_output(&mut self, text: &str, installed: bool) {
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with("Depodaki") || line.starts_with("Total") {
                continue;
            }
            let line = line.trim_start_matches('🌐').trim();
            let (name, version, summary) = if let Some(idx) = line.find(" - ") {
                let name = line[..idx].trim().to_string();
                let rest = line[idx + 3..].trim();
                if rest.starts_with('v') {
                    (name, rest[1..].trim().to_string(), String::new())
                } else {
                    (name, String::new(), rest.to_string())
                }
            } else {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.is_empty() { continue; }
                let name = parts[0].to_string();
                let ver = if parts.len() > 1 && parts[1].starts_with('v') {
                    parts[1][1..].to_string()
                } else {
                    String::new()
                };
                (name, ver, String::new())
            };

            if name.is_empty() { continue; }
            let cat = map_to_category(&name, "", &summary);
            let icon_p = find_icon(&name);
            let mut pkg = PackageInfo::new(&name);
            pkg.version = version;
            pkg.summary = summary;
            pkg.category = cat;
            pkg.icon_path = icon_p;
            pkg.installed = installed;

            if installed {
                self.installed_packages.insert(name, pkg);
            } else {
                self.available_packages.insert(name, pkg);
            }
        }
    }

    pub fn enrich_package_info(&mut self, pkg_name: &str) -> Option<PackageInfo> {
        if pkg_name.starts_with("flatpak:") {
            return self.get_all_packages().get(pkg_name).cloned();
        }

        let mut pkg = self.get_all_packages().get(pkg_name).cloned().unwrap_or_else(|| PackageInfo::new(pkg_name));

        if self.pisi_available {
            if let Ok(out) = Command::new("pisi").args(["info", pkg_name]).output() {
                if out.status.success() {
                    let text = String::from_utf8_lossy(&out.stdout);
                    for line in text.lines() {
                        let l = line.trim();
                        if l.is_empty() || l.starts_with("Yüklü paket") || l.contains("deposunda bulundu") || l.ends_with("bulunamadı.") {
                            continue;
                        }
                        if let Some((k, v)) = l.split_once(':') {
                            let key = k.trim();
                            let val = v.trim();
                            if key.contains("İsim") || key.contains("Name") {
                                // "aerosky, sürüm: 2.0.0, yayım: 0"
                                for part in val.split(',') {
                                    if part.contains("sürüm:") || part.contains("version:") {
                                        if let Some((_, ver)) = part.split_once(':') {
                                            pkg.version = ver.trim().to_string();
                                        }
                                    }
                                }
                            } else if (key.contains("Özet") || key.contains("Summary")) && val != "Açıklama yok" && !val.is_empty() {
                                pkg.summary = val.to_string();
                            } else if key.contains("Açıklama") || key.contains("Description") {
                                pkg.description = val.to_string();
                            } else if key.contains("Lisanslar") || key.contains("Licenses") {
                                pkg.license = val.to_string();
                            } else if key.contains("Bileşen") || key.contains("Component") {
                                pkg.component = val.to_string();
                                pkg.category = map_to_category(&pkg.name, val, &pkg.summary);
                            } else if key.contains("Bağımlılıkları") || key.contains("Dependencies") {
                                let deps: Vec<&str> = val.split_whitespace().collect();
                                pkg.dependencies_count = deps.len() as i32;
                            } else if key.contains("Yerleşik Boyut") || key.contains("Installed Size") {
                                pkg.installed_size = val.to_string();
                            } else if key.contains("Paket Boyutu") || key.contains("Package Size") {
                                pkg.download_size = val.to_string();
                            }
                        }
                    }
                }
            }
        }

        if pkg.summary.is_empty() && !pkg.description.is_empty() {
            pkg.summary = if pkg.description.len() > 80 {
                format!("{}…", &pkg.description[..80])
            } else {
                pkg.description.clone()
            };
        }

        if pkg.developer.is_empty() {
            pkg.developer = detect_developer(&pkg.name, &pkg.homepage, &pkg.component);
        }

        if pkg.icon_path.is_empty() {
            pkg.icon_path = find_icon(&pkg.name);
        }

        // Cache update
        if let Some(p) = self.available_packages.get_mut(pkg_name) {
            *p = pkg.clone();
        }
        if let Some(p) = self.installed_packages.get_mut(pkg_name) {
            *p = pkg.clone();
        }

        Some(pkg)
    }

    pub fn load_installed_flatpaks(&mut self) {
        if !self.flatpak_available {
            return;
        }
        let output = Command::new("flatpak")
            .args(["list", "--columns=application,name,version,branch,origin,ref"])
            .output();

        if let Ok(out) = output {
            if out.status.success() {
                let text = String::from_utf8_lossy(&out.stdout);
                for line in text.lines() {
                    let parts: Vec<&str> = line.split('\t').map(|s| s.trim()).collect();
                    if parts.is_empty() { continue; }
                    let app_id = parts[0];
                    if app_id.is_empty() { continue; }
                    let display_name = parts.get(1).filter(|s| !s.is_empty()).unwrap_or(&app_id);
                    let version = parts.get(2).filter(|s| !s.is_empty())
                        .or_else(|| parts.get(3).filter(|s| !s.is_empty()))
                        .unwrap_or(&"");
                    let origin = parts.get(4).filter(|s| !s.is_empty()).unwrap_or(&"FlatHub");
                    let key = format!("flatpak:{}", app_id);
                    let icon_name = app_id.split('.').last().unwrap_or(app_id).to_lowercase();
                    let icon_path = find_flatpak_icon(app_id);
                    let cat = get_flatpak_category(app_id);

                    let mut pkg = PackageInfo::new(&key);
                    pkg.display_name = display_name.to_string();
                    pkg.version = version.to_string();
                    pkg.summary = format!("{} · {}", origin, app_id);
                    pkg.description = format!("{} ({}) Flatpak ({}) aracılığıyla kurulmuştur.", display_name, app_id, origin);
                    pkg.category = cat;
                    pkg.icon_name = icon_name;
                    pkg.icon_path = icon_path;
                    pkg.installed = true;
                    pkg.is_flatpak = true;
                    pkg.origin = capitalize(origin);
                    self.installed_packages.insert(key, pkg);
                }
            }
        }
    }

    pub fn load_available_flatpaks(&mut self) {
        if !self.flatpak_available {
            return;
        }
        let output = Command::new("flatpak")
            .args(["remote-ls", "--app", "--columns=application,name,version,origin,download-size,installed-size"])
            .output();

        if let Ok(out) = output {
            if out.status.success() {
                let text = String::from_utf8_lossy(&out.stdout);
                for line in text.lines() {
                    let parts: Vec<&str> = line.split('\t').map(|s| s.trim()).collect();
                    if parts.is_empty() { continue; }
                    let app_id = parts[0];
                    if app_id.is_empty() { continue; }
                    let display_name = parts.get(1).filter(|s| !s.is_empty()).unwrap_or(&app_id);
                    let version = parts.get(2).unwrap_or(&"");
                    let origin = parts.get(3).filter(|s| !s.is_empty()).unwrap_or(&"FlatHub");
                    let dl_size = parts.get(4).unwrap_or(&"");
                    let inst_size = parts.get(5).unwrap_or(&"");

                    let key = format!("flatpak:{}", app_id);
                    if self.available_packages.contains_key(&key) { continue; }
                    let icon_name = app_id.split('.').last().unwrap_or(app_id).to_lowercase();
                    let icon_path = find_flatpak_icon(app_id);
                    let cat = get_flatpak_category(app_id);

                    let mut pkg = PackageInfo::new(&key);
                    pkg.display_name = display_name.to_string();
                    pkg.version = version.to_string();
                    pkg.summary = format!("{} · {}", origin, app_id);
                    pkg.description = format!("{} uygulaması Flatpak ({}) ile kurulabilir.", display_name, origin);
                    pkg.category = cat;
                    pkg.icon_name = icon_name;
                    pkg.icon_path = icon_path;
                    pkg.installed = false;
                    pkg.is_flatpak = true;
                    pkg.origin = capitalize(origin);
                    pkg.download_size = dl_size.to_string();
                    pkg.installed_size = inst_size.to_string();
                    self.available_packages.insert(key, pkg);
                }
            }
        }
    }

    pub fn get_all_packages(&self) -> HashMap<String, PackageInfo> {
        let mut merged = self.available_packages.clone();
        for (k, v) in &self.installed_packages {
            if let Some(pkg) = merged.get_mut(k) {
                pkg.installed = true;
                pkg.has_update = v.has_update;
                if !v.new_version.is_empty() {
                    pkg.new_version = v.new_version.clone();
                }
            } else {
                merged.insert(k.clone(), v.clone());
            }
        }
        merged
    }

    pub fn search_packages(&self, query: &str) -> Vec<PackageInfo> {
        let q = query.to_lowercase();
        let all = self.get_all_packages();
        let mut results: Vec<(i32, PackageInfo)> = vec![];
        for pkg in all.values() {
            let mut score = 0i32;
            if pkg.name.to_lowercase() == q || pkg.display_name.to_lowercase() == q {
                score += 10;
            } else if pkg.name.to_lowercase().starts_with(&q) || pkg.display_name.to_lowercase().starts_with(&q) {
                score += 5;
            } else if pkg.name.to_lowercase().contains(&q) || pkg.display_name.to_lowercase().contains(&q) {
                score += 3;
            }
            if pkg.summary.to_lowercase().contains(&q) {
                score += 2;
            }
            if pkg.description.to_lowercase().contains(&q) {
                score += 1;
            }
            if score > 0 {
                results.push((score, pkg.clone()));
            }
        }
        results.sort_by(|a, b| b.0.cmp(&a.0));
        results.into_iter().map(|(_, p)| p).collect()
    }

    pub fn install_package(&self, pkg_name: &str) -> (bool, String) {
        if pkg_name.starts_with("flatpak:") {
            let real_id = pkg_name.trim_start_matches("flatpak:");
            let is_installed = self.installed_packages.contains_key(pkg_name);
            let cmd = if is_installed {
                vec!["update", "--noninteractive", "--assumeyes", real_id]
            } else {
                vec!["install", "--noninteractive", "--assumeyes", real_id]
            };
            return run_flatpak_cmd(&cmd);
        }
        if !self.pisi_available {
            return (false, i18n::tr("pisi_missing"));
        }
        run_pisi_cmd(&["install", "-y", pkg_name])
    }

    pub fn remove_package(&self, pkg_name: &str) -> (bool, String) {
        if pkg_name.starts_with("flatpak:") {
            let real_id = pkg_name.trim_start_matches("flatpak:");
            return run_flatpak_cmd(&["uninstall", "--noninteractive", "--assumeyes", real_id]);
        }
        if !self.pisi_available {
            return (false, i18n::tr("pisi_missing"));
        }
        run_pisi_cmd(&["remove", "-y", pkg_name])
    }

    pub fn check_for_updates(&mut self, update_repo: bool) -> (usize, Vec<String>, String) {
        let mut upgradable: Vec<String> = vec![];
        let mut error_msg = String::new();

        if update_repo && self.pisi_available {
            let _ = run_pisi_cmd(&["update-repo"]);
        }

        if self.pisi_available {
            match Command::new("pisi").arg("list-upgrades").output() {
                Ok(out) if out.status.success() => {
                    let text = String::from_utf8_lossy(&out.stdout);
                    for line in text.lines() {
                        let line = line.trim();
                        if line.is_empty() || line.starts_with("Sistem") || line.starts_with("Tüm") { continue; }
                        let name = line.split(" - ").next().unwrap_or(line).split_whitespace().next().unwrap_or("").to_string();
                        if !name.is_empty() && !upgradable.contains(&name) {
                            upgradable.push(name.clone());
                            if let Some(p) = self.installed_packages.get_mut(&name) {
                                p.has_update = true;
                            }
                            if let Some(p) = self.available_packages.get_mut(&name) {
                                p.has_update = true;
                            }
                        }
                    }
                }
                Err(e) => {
                    error_msg = e.to_string();
                }
                _ => {}
            }
        }

        if self.flatpak_available {
            match Command::new("flatpak")
                .args(["remote-ls", "--updates", "--columns=application"])
                .output() {
                Ok(out) if out.status.success() => {
                    let text = String::from_utf8_lossy(&out.stdout);
                    for line in text.lines() {
                        let app_id = line.trim();
                        if app_id.is_empty() { continue; }
                        let key = format!("flatpak:{}", app_id);
                        if !upgradable.contains(&key) {
                            upgradable.push(key.clone());
                            if let Some(p) = self.installed_packages.get_mut(&key) {
                                p.has_update = true;
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        (upgradable.len(), upgradable, error_msg)
    }

    pub fn update_repo(&self) -> bool {
        if !self.pisi_available { return false; }
        run_pisi_cmd(&["update-repo"]).0
    }
}

// ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────

pub fn check_command_available(cmd: &str) -> bool {
    Command::new(cmd)
        .arg("--version")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

pub fn find_icon(icon_name: &str) -> String {
    if icon_name.is_empty() { return String::new(); }
    for base in ICON_SEARCH_PATHS {
        for ext in ICON_EXTENSIONS {
            let p = format!("{}/{}{}", base, icon_name, ext);
            if Path::new(&p).exists() {
                return p;
            }
        }
    }
    if let Some(home) = dirs::home_dir() {
        let flatpak_dirs = [
            home.join(".local/share/flatpak/exports/share/icons/hicolor/scalable/apps"),
            home.join(".local/share/flatpak/exports/share/icons/hicolor/64x64/apps"),
            home.join(".local/share/flatpak/exports/share/icons/hicolor/48x48/apps"),
        ];
        for dir in &flatpak_dirs {
            for ext in ICON_EXTENSIONS {
                let p = dir.join(format!("{}{}", icon_name, ext));
                if p.exists() {
                    return p.to_string_lossy().to_string();
                }
            }
        }
    }
    String::new()
}

pub fn find_flatpak_icon(app_id: &str) -> String {
    let dirs = [
        "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
        "/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps",
        "/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps",
        "/var/lib/flatpak/exports/share/icons/hicolor/64x64/apps",
    ];
    for dir in &dirs {
        for ext in ICON_EXTENSIONS {
            let p = format!("{}/{}{}", dir, app_id, ext);
            if Path::new(&p).exists() {
                return p;
            }
        }
    }
    let short = app_id.split('.').last().unwrap_or(app_id);
    find_icon(short)
}

pub fn map_to_category(name: &str, part_of: &str, summary: &str) -> String {
    let p = part_of.to_lowercase();
    let n = name.to_lowercase();
    let s = summary.to_lowercase();

    // 1. Development
    if ["devel", "code", "prog", "editor", "ide", "git", "compiler", "header", "sdk"].iter().any(|x| p.contains(x))
        || ["code", "studio", "atom", "antigravity", "ide", "rust", "python", "gcc", "llvm", "clang", "cmake", "ninja", "meson", "gdb", "valgrind", "git", "-devel", "-headers", "lib"].iter().any(|x| n.contains(x)) {
        return "development".into();
    }
    // 2. Games
    if ["game", "arcade", "emulator", "puzzle", "rpg", "strategy", "board"].iter().any(|x| p.contains(x))
        || ["game", "steam", "craft", "kart", "tux", "chess", "minesweeper", "snake", "tictactoe", "play", "emu", "86box", "retro", "doom", "quake", "scummvm", "minetest"].iter().any(|x| n.contains(x)) {
        return "games".into();
    }
    // 3. Graphics
    if ["graph", "image", "draw", "pdf", "photo", "paint", "font"].iter().any(|x| p.contains(x))
        || ["gimp", "inkscape", "krita", "image", "photo", "draw", "blender", "font", "svg", "png", "jpeg", "canvas", "theme", "icon", "wallpaper"].iter().any(|x| n.contains(x)) {
        return "graphics".into();
    }
    // 4. Multimedia
    if ["sound", "video", "tv", "media", "audio", "music", "codec"].iter().any(|x| p.contains(x))
        || ["vlc", "player", "music", "video", "obs", "sound", "ffmpeg", "mpv", "gstreamer", "alsa", "pulse", "pipewire", "jack", "flac", "vorbis", "opus", "mp3", "kodi", "audacity"].iter().any(|x| n.contains(x)) {
        return "multimedia".into();
    }
    // 5. Internet
    if ["net", "web", "browser", "mail", "conn", "remote", "network", "wifi"].iter().any(|x| p.contains(x))
        || ["chrome", "firefox", "desk", "browser", "telegram", "discord", "network", "wifi", "torrent", "ftp", "ssh", "curl", "wget", "dns", "vpn", "thunderbird", "chat", "irc"].iter().any(|x| n.contains(x)) {
        return "internet".into();
    }
    // 6. Office
    if ["office", "word", "calc", "writer", "document", "print"].iter().any(|x| p.contains(x))
        || ["office", "libreoffice", "doc", "pdf", "calc", "writer", "sheet", "word", "excel", "epub", "reader", "cups", "scan", "calendar", "notes", "tex", "latex"].iter().any(|x| n.contains(x)) {
        return "office".into();
    }
    // 7. Education
    if ["science", "edu", "elec", "school", "math", "learn"].iter().any(|x| p.contains(x))
        || ["arduino", "math", "science", "geo", "astronomy", "physics", "chem", "bio", "stat", "octave", "kaptan", "tutor", "typing"].iter().any(|x| n.contains(x)) {
        return "education".into();
    }
    // 8. Enterprise
    if ["enterprise", "server", "database", "cloud", "corp"].iter().any(|x| p.contains(x))
        || ["server", "cloud", "docker", "container", "kubernetes", "database", "sql", "postgres", "mysql", "mariadb", "redis", "mongodb", "ldap", "samba", "nfs", "nginx", "apache", "caddy"].iter().any(|x| n.contains(x)) {
        return "enterprise".into();
    }
    // 9. System
    if ["system", "admin", "base", "kernel", "root", "driver", "security"].iter().any(|x| p.contains(x))
        || ["htop", "neofetch", "gparted", "system", "kernel", "driver", "lupus", "pisi", "pisidi", "pisipi", "deb2pisi", "aerosky", "auratask", "boot", "grub", "systemd", "udev", "dbus", "util-linux", "coreutils", "desktop", "plasma", "gnome", "xfce", "kde", "qt", "gtk", "xorg", "wayland", "mesa", "nvidia", "amd", "intel", "vulkan", "firmware", "disk", "auth", "pam", "sudo"].iter().any(|x| n.contains(x)) {
        return "system".into();
    }

    if ["game", "oyun"].iter().any(|x| s.contains(x)) { return "games".into(); }
    if ["devel", "kod", "geliştirme", "programlama"].iter().any(|x| s.contains(x)) { return "development".into(); }
    if ["ses", "video", "müzik", "çalar"].iter().any(|x| s.contains(x)) { return "multimedia".into(); }
    if ["resim", "fotoğraf", "çizim", "grafik"].iter().any(|x| s.contains(x)) { return "graphics".into(); }
    if ["internet", "tarayıcı", "ağ", "web"].iter().any(|x| s.contains(x)) { return "internet".into(); }
    if ["ofis", "belge", "yazı"].iter().any(|x| s.contains(x)) { return "office".into(); }
    if ["eğitim", "öğrenim", "bilim"].iter().any(|x| s.contains(x)) { return "education".into(); }
    if ["sistem", "yönetim", "araç"].iter().any(|x| s.contains(x)) { return "system".into(); }

    "utilities".into()
}

pub fn get_flatpak_category(app_id: &str) -> String {
    let lower = app_id.to_lowercase();
    if ["game","chess","tux","minetest","openarena","steam","craft"].iter().any(|k| lower.contains(k)) {
        return "games".into();
    }
    if ["code","studio","ide","builder","eclipse","rust","python","git"].iter().any(|k| lower.contains(k)) {
        return "development".into();
    }
    if ["video","audio","media","vlc","kodi","spotify","rhythmbox","music","player"].iter().any(|k| lower.contains(k)) {
        return "multimedia".into();
    }
    if ["chrome","firefox","browser","telegram","signal","discord","thunderbird","mail","chat"].iter().any(|k| lower.contains(k)) {
        return "internet".into();
    }
    if ["gimp","inkscape","krita","darktable","blender","photo","draw"].iter().any(|k| lower.contains(k)) {
        return "graphics".into();
    }
    if ["office","writer","calc","impress","libreoffice","onlyoffice","pdf"].iter().any(|k| lower.contains(k)) {
        return "office".into();
    }
    if ["edu","learn","school","math","science","tutor"].iter().any(|k| lower.contains(k)) {
        return "education".into();
    }
    if ["system","manager","monitor","tweaks","settings","disk","htop"].iter().any(|k| lower.contains(k)) {
        return "system".into();
    }
    "utilities".into()
}

fn detect_developer(name: &str, homepage: &str, component: &str) -> String {
    let n = name.to_lowercase();
    let u = homepage.to_lowercase();
    let c = component.to_lowercase();

    if u.contains("mozilla.org") || n.contains("firefox") || n.contains("thunderbird") {
        return "Mozilla Foundation".into();
    }
    if u.contains("gnu.org") || n.starts_with("gnu") {
        return "GNU Project".into();
    }
    if u.contains("kde.org") || c.contains("kde") || n.starts_with("k") && (n.contains("plasma") || n.contains("kaptan")) {
        return "KDE Community".into();
    }
    if u.contains("gnome.org") || c.contains("gnome") {
        return "GNOME Project".into();
    }
    if u.contains("xfce.org") || c.contains("xfce") {
        return "Xfce Development Team".into();
    }
    if u.contains("videolan.org") || n.contains("vlc") {
        return "VideoLAN Project".into();
    }
    if n.contains("lupus") || n.contains("pisi") || n.contains("auratask") || n.contains("aerosky") {
        return "Antolun".into();
    }
    if !homepage.is_empty() {
        if let Some(host) = homepage.trim_start_matches("https://").trim_start_matches("http://").split('/').next() {
            let clean_host = host.trim_start_matches("www.");
            return clean_host.to_string();
        }
    }
    "Pisi Linux Topluluğu".into()
}

fn capitalize(s: &str) -> String {
    let mut c = s.chars();
    match c.next() {
        None => String::new(),
        Some(f) => f.to_uppercase().collect::<String>() + c.as_str(),
    }
}

fn run_pisi_cmd(args: &[&str]) -> (bool, String) {
    let is_root = unsafe { libc::geteuid() == 0 };
    let output = if is_root {
        Command::new("pisi").args(args).output()
    } else {
        Command::new("pkexec").arg("pisi").args(args).output()
    };
    match output {
        Ok(out) => {
            if out.status.success() {
                (true, String::from_utf8_lossy(&out.stdout).to_string())
            } else {
                (false, String::from_utf8_lossy(&out.stderr).to_string())
            }
        }
        Err(e) => (false, e.to_string()),
    }
}

fn run_flatpak_cmd(args: &[&str]) -> (bool, String) {
    match Command::new("flatpak").args(args).output() {
        Ok(out) => {
            if out.status.success() {
                (true, String::from_utf8_lossy(&out.stdout).to_string())
            } else {
                (false, String::from_utf8_lossy(&out.stderr).to_string())
            }
        }
        Err(e) => (false, e.to_string()),
    }
}

extern "C" {
    fn geteuid() -> u32;
}
mod libc {
    pub unsafe fn geteuid() -> u32 {
        super::geteuid()
    }
}
