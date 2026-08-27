// LupuS Software Center - Backend: Paket veri yapıları ve işlemleri
// Python backend.py'nin Rust karşılığı

use crate::i18n;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use std::process::Command;
use tauri::Emitter;

// ─── Sabitler ──────────────────────────────────────────────────────────────

pub const VERSION: &str = "2.0.1";

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

/// Luppo paket isimlerindeki '-' işaretlerini boşluk ile değiştirir ve her kelimenin ilk harfini büyük yapar.
/// Örnek: "luppo-package-installer" -> "Luppo Package Installer"
pub fn format_luppo_display_name(name: &str) -> String {
    if name.is_empty() {
        return String::new();
    }
    name.split('-')
        .filter(|w| !w.is_empty())
        .map(|word| {
            let mut chars = word.chars();
            match chars.next() {
                None => String::new(),
                Some(first) => {
                    let upper_first: String = first.to_uppercase().collect();
                    upper_first + chars.as_str()
                }
            }
        })
        .collect::<Vec<String>>()
        .join(" ")
}

impl PackageInfo {
    pub fn new(name: &str) -> Self {
        let display = format_luppo_display_name(name);
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
            origin: "Luppo".to_string(),
            screenshots: vec![],
            update_date: String::new(),
            vcs_url: String::new(),
        }
    }
}

// ─── Progress Event ──────────────────────────────────────────────────────────
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressEvent {
    pub package_name: String,
    pub action: String, // "install", "update", "remove"
    pub progress: u8,   // 0-100
    pub status: String, // "downloading", "installing", "configuring", "completed", "error"
    pub message: String,
}

// ─── Search Normalizer ───────────────────────────────────────────────────────
pub fn normalize_for_search(text: &str) -> String {
    let mut normalized = String::with_capacity(text.len());
    for c in text.chars() {
        match c {
            'ç' | 'Ç' => normalized.push('c'),
            'ğ' | 'Ğ' => normalized.push('g'),
            'ı' | 'I' | 'İ' | 'i' => normalized.push('i'),
            'ö' | 'Ö' => normalized.push('o'),
            'ş' | 'Ş' => normalized.push('s'),
            'ü' | 'Ü' => normalized.push('u'),
            'â' | 'Â' => normalized.push('a'),
            'î' | 'Î' => normalized.push('i'),
            'û' | 'Û' => normalized.push('u'),
            other => {
                for lc in other.to_lowercase() {
                    normalized.push(lc);
                }
            }
        }
    }
    normalized
}

// ─── LuppoBackend ──────────────────────────────────────────────────────────

#[derive(Default, Clone)]
pub struct LuppoBackend {
    pub installed_packages: HashMap<String, PackageInfo>,
    pub available_packages: HashMap<String, PackageInfo>,
    pub luppo_available: bool,
    pub flatpak_available: bool,
}

impl LuppoBackend {
    pub fn new() -> Self {
        let luppo_available = check_command_available("luppo");
        let flatpak_available = check_command_available("flatpak");
        let mut backend = Self {
            installed_packages: HashMap::new(),
            available_packages: HashMap::new(),
            luppo_available,
            flatpak_available,
        };
        if luppo_available {
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
        if !self.luppo_available {
            return;
        }
        if let Ok(db) = open_luppo_db() {
            if let Ok(installed) = db.list_installed_packages() {
                for pkg in installed {
                    let name = pkg.name.clone();
                    let display_name = format_luppo_display_name(&name);
                    let icon_path = find_icon(&name);
                    let summary = if !pkg.description.is_empty() {
                        pkg.description.clone()
                    } else {
                        String::new()
                    };
                    let category = map_to_category(&name, "", &summary);
                    let mut info = PackageInfo::new(&name);
                    info.display_name = display_name;
                    info.version = pkg.version.clone();
                    info.release = pkg.release.to_string();
                    info.summary = summary;
                    info.description = pkg.description.clone();
                    info.license = pkg.licenses.join(", ");
                    info.homepage = pkg.homepage.unwrap_or_default();
                    info.category = category;
                    info.icon_name = name.clone();
                    info.icon_path = icon_path;
                    info.installed = true;
                    info.installed_size = format_bytes(pkg.total_size);
                    info.developer = if let Some(p) = pkg.packager {
                        p.name
                    } else {
                        detect_developer(&name, &info.homepage, &info.component)
                    };
                    self.installed_packages.insert(name, info);
                }
            }
        }
    }

    pub fn load_available_packages(&mut self) {
        if self.luppo_available {
            if let Ok(db) = open_luppo_db() {
                if let Ok(available) = db.list_available_packages() {
                    for pkg in available {
                        let name = pkg.name.clone();
                        let display_name = format_luppo_display_name(&name);
                        let icon_path = find_icon(&name);
                        let summary = pkg.get_summary();
                        let description = pkg.get_description();
                        let category = map_to_category(&name, &pkg.partof, &summary);
                        let mut info = PackageInfo::new(&name);
                        info.display_name = display_name;
                        info.version = pkg.latest_version().to_string();
                        info.release = pkg.release.to_string();
                        info.summary = summary;
                        info.description = description;
                        info.license = pkg.licenses.join(", ");
                        info.category = category;
                        info.component = pkg.partof.clone();
                        info.icon_name = name.clone();
                        info.icon_path = icon_path;
                        info.installed = self.installed_packages.contains_key(&name);
                        info.download_size = format_bytes(pkg.package_size);
                        info.installed_size = format_bytes(pkg.installed_size);
                        info.dependencies_count = pkg
                            .runtime_dependencies
                            .as_ref()
                            .map(|r| r.dependencies.len() as i32)
                            .unwrap_or(0);
                        info.developer = detect_developer(&name, &info.homepage, &info.component);
                        self.available_packages.insert(name, info);
                    }
                }
            }
        }
        // Update installed packages with enriched summary/description if needed
        let installed_names: Vec<String> = self.installed_packages.keys().cloned().collect();
        for name in installed_names {
            if let Some(avail) = self.available_packages.get(&name) {
                if let Some(inst) = self.installed_packages.get_mut(&name) {
                    if inst.summary.is_empty() {
                        inst.summary = avail.summary.clone();
                    }
                    if inst.description.is_empty() {
                        inst.description = avail.description.clone();
                    }
                    if inst.category == "utilities" && avail.category != "utilities" {
                        inst.category = avail.category.clone();
                    }
                    if inst.component.is_empty() {
                        inst.component = avail.component.clone();
                    }
                }
            }
            if let Some(avail_pkg) = self.available_packages.get_mut(&name) {
                avail_pkg.installed = true;
            }
        }
    }

    pub fn enrich_package_info(&mut self, pkg_name: &str) -> Option<PackageInfo> {
        if pkg_name.starts_with("flatpak:") {
            return self.get_all_packages().get(pkg_name).cloned();
        }

        let mut pkg = self.get_all_packages().get(pkg_name).cloned().unwrap_or_else(|| PackageInfo::new(pkg_name));

        if self.luppo_available {
            if let Ok(db) = open_luppo_db() {
                if let Ok(Some(remote)) = db.get_available_package(pkg_name) {
                    pkg.version = remote.latest_version().to_string();
                    pkg.release = remote.release.to_string();
                    let sum = remote.get_summary();
                    if !sum.is_empty() { pkg.summary = sum; }
                    let desc = remote.get_description();
                    if !desc.is_empty() { pkg.description = desc; }
                    if !remote.licenses.is_empty() { pkg.license = remote.licenses.join(", "); }
                    if !remote.partof.is_empty() {
                        pkg.component = remote.partof.clone();
                        pkg.category = map_to_category(&pkg.name, &remote.partof, &pkg.summary);
                    }
                    if let Some(deps) = &remote.runtime_dependencies {
                        pkg.dependencies_count = deps.dependencies.len() as i32;
                    }
                    if remote.package_size > 0 {
                        pkg.download_size = format_bytes(remote.package_size);
                    }
                    if remote.installed_size > 0 {
                        pkg.installed_size = format_bytes(remote.installed_size);
                    }
                }
                if let Ok(Some(inst)) = db.get_installed_package(pkg_name) {
                    pkg.version = inst.version.clone();
                    pkg.release = inst.release.to_string();
                    if !inst.description.is_empty() {
                        pkg.description = inst.description.clone();
                        if pkg.summary.is_empty() { pkg.summary = inst.description.clone(); }
                    }
                    if !inst.licenses.is_empty() { pkg.license = inst.licenses.join(", "); }
                    if inst.total_size > 0 {
                        pkg.installed_size = format_bytes(inst.total_size);
                    }
                    if let Some(hp) = inst.homepage {
                        pkg.homepage = hp;
                    }
                    if let Some(p) = inst.packager {
                        pkg.developer = p.name;
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
                    pkg.developer = extract_flatpak_developer(app_id);
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
            .args(["remote-ls", /* "--app" */ "--columns=application,name,version,origin,download-size,installed-size"])
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
                    pkg.developer = extract_flatpak_developer(app_id);
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
        let raw_q = query.trim();
        if raw_q.is_empty() {
            return vec![];
        }
        let q_norm = normalize_for_search(raw_q);
        let tokens: Vec<&str> = q_norm.split_whitespace().collect();
        if tokens.is_empty() {
            return vec![];
        }

        let all = self.get_all_packages();
        let mut results: Vec<(i32, PackageInfo)> = vec![];

        for pkg in all.values() {
            let name_norm = normalize_for_search(&pkg.name);
            let display_norm = normalize_for_search(&pkg.display_name);
            let summary_norm = normalize_for_search(&pkg.summary);
            let desc_norm = normalize_for_search(&pkg.description);
            let cat_norm = normalize_for_search(&pkg.category);
            let dev_norm = normalize_for_search(&pkg.developer);

            // Tüm token'ların paket bilgilerinde eşleştiğini doğrula (AND logic)
            let mut matches_all_tokens = true;
            let mut total_score = 0i32;

            // Tam ad veya görünen ad tam eşleşmesi (büyük alaka bonusu)
            if name_norm == q_norm || display_norm == q_norm {
                total_score += 120;
            } else if name_norm.starts_with(&q_norm) || display_norm.starts_with(&q_norm) {
                total_score += 70;
            } else if display_norm.contains(&q_norm) {
                total_score += 40;
            } else if name_norm.contains(&q_norm) {
                total_score += 30;
            }

            for &token in &tokens {
                let mut token_matched = false;
                let mut token_score = 0i32;

                // İsme göre eşleşme
                if display_norm == token || name_norm == token {
                    token_score += 50;
                    token_matched = true;
                } else if display_norm.starts_with(token) || name_norm.starts_with(token) {
                    token_score += 35;
                    token_matched = true;
                } else if display_norm.split_whitespace().any(|w| w.starts_with(token)) {
                    // Kelime başlangıcı (örn: "Visual Studio Code" -> "code")
                    token_score += 30;
                    token_matched = true;
                } else if display_norm.contains(token) {
                    token_score += 20;
                    token_matched = true;
                } else if name_norm.contains(token) {
                    token_score += 15;
                    token_matched = true;
                }

                // Kategoriye göre eşleşme
                if cat_norm == token {
                    token_score += 25;
                    token_matched = true;
                } else if cat_norm.contains(token) {
                    token_score += 15;
                    token_matched = true;
                }

                // Geliştiriciye göre eşleşme
                if dev_norm.contains(token) {
                    token_score += 15;
                    token_matched = true;
                }

                // Özet (summary) eşleşmesi
                if summary_norm.split_whitespace().any(|w| w.starts_with(token)) {
                    token_score += 15;
                    token_matched = true;
                } else if summary_norm.contains(token) {
                    token_score += 10;
                    token_matched = true;
                }

                // Açıklama (description) eşleşmesi
                if desc_norm.contains(token) {
                    token_score += 5;
                    token_matched = true;
                }

                if !token_matched {
                    matches_all_tokens = false;
                    break;
                }

                total_score += token_score;
            }

            if matches_all_tokens && total_score > 0 {
                // Kurulu olanlara veya yüksek puanlılara alaka takviyesi
                if pkg.installed {
                    total_score += 3;
                }
                if pkg.rating > 4.0 {
                    total_score += 2;
                }
                results.push((total_score, pkg.clone()));
            }
        }

        results.sort_by(|a, b| {
            b.0.cmp(&a.0).then_with(|| a.1.display_name.to_lowercase().cmp(&b.1.display_name.to_lowercase()))
        });

        results.into_iter().map(|(_, p)| p).collect()
    }

    pub fn is_package_installed(&self, pkg_name: &str) -> bool {
        if let Some(pkg) = self.installed_packages.get(pkg_name) {
            if pkg.installed {
                return true;
            }
        }
        if let Some(pkg) = self.available_packages.get(pkg_name) {
            if pkg.installed || pkg.has_update {
                return true;
            }
        }
        false
    }

    pub fn is_package_upgradable(&self, pkg_name: &str) -> bool {
        if let Some(pkg) = self.installed_packages.get(pkg_name) {
            if pkg.has_update {
                return true;
            }
        }
        if let Some(pkg) = self.available_packages.get(pkg_name) {
            if pkg.has_update {
                return true;
            }
        }
        false
    }

    pub fn install_package(&self, pkg_name: &str) -> (bool, String) {
        let is_installed = self.is_package_installed(pkg_name);
        let is_upgradable = self.is_package_upgradable(pkg_name);
        let is_upgrade = is_installed || is_upgradable;
        if pkg_name.starts_with("flatpak:") {
            let real_id = pkg_name.trim_start_matches("flatpak:");
            let cmd = if is_upgrade {
                vec!["update", "--noninteractive", "--assumeyes", real_id]
            } else {
                vec!["install", "--noninteractive", "--assumeyes", real_id]
            };
            return run_flatpak_cmd(&cmd);
        }
        if !self.luppo_available {
            return (false, i18n::tr("luppo_missing"));
        }
        let action = if is_upgrade { "upgrade" } else { "install" };
        run_luppo_cmd(&[action, "-y", pkg_name])
    }

    // ─── Async Install/Remove with Progress ──────────────────────────────────

    pub async fn install_package_with_progress<F>(
        &self,
        pkg_name: &str,
        app_handle: &tauri::AppHandle,
        on_progress: F,
    ) -> (bool, String)
    where
        F: FnMut(ProgressEvent) + Send + 'static,
    {
        let is_installed = self.is_package_installed(pkg_name);
        let is_upgradable = self.is_package_upgradable(pkg_name);
        let is_upgrade = is_installed || is_upgradable;
        if pkg_name.starts_with("flatpak:") {
            let action = if is_upgrade { "update" } else { "install" };
            return self.run_flatpak_with_progress(pkg_name, action, app_handle, on_progress).await;
        }
        if !self.luppo_available {
            return (false, i18n::tr("luppo_missing"));
        }
        let action_cmd = if is_upgrade { "upgrade" } else { "install" };
        let action_name = if is_upgrade { "update" } else { "install" };
        self.run_luppo_with_progress(&[action_cmd, "-y", pkg_name], action_name, pkg_name, app_handle, on_progress).await
    }

    pub async fn remove_package_with_progress<F>(
        &self,
        pkg_name: &str,
        app_handle: &tauri::AppHandle,
        on_progress: F,
    ) -> (bool, String)
    where
        F: FnMut(ProgressEvent) + Send + 'static,
    {
        if pkg_name.starts_with("flatpak:") {
            return self.run_flatpak_with_progress(pkg_name, "remove", app_handle, on_progress).await;
        }
        if !self.luppo_available {
            return (false, i18n::tr("luppo_missing"));
        }
        self.run_luppo_with_progress(&["remove", "-y", pkg_name], "remove", pkg_name, app_handle, on_progress).await
    }

    async fn run_luppo_with_progress<F>(
        &self,
        args: &[&str],
        action: &str,
        pkg_name: &str,
        app_handle: &tauri::AppHandle,
        on_progress: F,
    ) -> (bool, String)
    where
        F: FnMut(ProgressEvent) + Send + 'static,
    {
        let mut cmd = build_root_command("luppo");
        cmd.args(args)
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped());

        let mut child = match cmd.spawn() {
            Ok(c) => c,
            Err(e) => return (false, e.to_string()),
        };

        let stdout = child.stdout.take().expect("stdout not captured");
        let stderr = child.stderr.take().expect("stderr not captured");

        use std::sync::{Arc, Mutex};
        let pkg_name_owned = pkg_name.to_string();
        let action_owned = action.to_string();
        let app_handle_clone = app_handle.clone();

        // Wrap on_progress in Arc<Mutex> so both closures can share it
        let on_progress = Arc::new(Mutex::new(on_progress));
        let on_progress_stderr = Arc::clone(&on_progress);

        // Spawn task to read stdout
        let stdout_task = tokio::task::spawn_blocking(move || {
            read_output_lines(stdout, |line| {
                let event = parse_luppo_progress(line, &pkg_name_owned, &action_owned);
                if let Some(e) = event {
                    if let Ok(mut cb) = on_progress.lock() { cb(e.clone()); }
                    let _ = app_handle_clone.emit("package-progress", &e);
                }
            });
        });

        // Spawn task to read stderr
        let pkg_name_stderr = pkg_name.to_string();
        let action_stderr = action.to_string();
        let app_handle_stderr = app_handle.clone();
        let stderr_task = tokio::task::spawn_blocking(move || {
            read_output_lines(stderr, |line| {
                let event = parse_luppo_progress(line, &pkg_name_stderr, &action_stderr);
                if let Some(e) = event {
                    if let Ok(mut cb) = on_progress_stderr.lock() { cb(e.clone()); }
                    let _ = app_handle_stderr.emit("package-progress", &e);
                }
            });
        });

        let _ = tokio::join!(stdout_task, stderr_task);

        let status = match child.wait() {
            Ok(s) => s,
            Err(e) => return (false, e.to_string()),
        };
        if status.success() {
            let _ = app_handle.emit("package-progress", &ProgressEvent {
                package_name: pkg_name.to_string(),
                action: action.to_string(),
                progress: 100,
                status: "completed".to_string(),
                message: "İşlem tamamlandı".to_string(),
            });
            (true, "Başarılı".to_string())
        } else {
            let _ = app_handle.emit("package-progress", &ProgressEvent {
                package_name: pkg_name.to_string(),
                action: action.to_string(),
                progress: 0,
                status: "error".to_string(),
                message: "İşlem başarısız oldu".to_string(),
            });
            (false, "Başarısız".to_string())
        }
    }

    async fn run_flatpak_with_progress<F>(
        &self,
        pkg_name: &str,
        action: &str, // "install", "update", "remove"
        app_handle: &tauri::AppHandle,
        on_progress: F,
    ) -> (bool, String)
    where
        F: FnMut(ProgressEvent) + Send + 'static,
    {
        let real_id = pkg_name.trim_start_matches("flatpak:").to_string();
        let flatpak_cmd = match action {
            "update" => "update",
            "remove" => "uninstall",
            _ => "install",
        };
        let args: Vec<String> = vec![
            flatpak_cmd.to_string(),
            "--noninteractive".to_string(),
            "--assumeyes".to_string(),
            real_id,
        ];

        let mut cmd = Command::new("flatpak");
        cmd.args(&args)
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped());

        let mut child = match cmd.spawn() {
            Ok(c) => c,
            Err(e) => return (false, e.to_string()),
        };

        let stdout = child.stdout.take().expect("stdout not captured");
        let stderr = child.stderr.take().expect("stderr not captured");

        use std::sync::{Arc, Mutex};
        let pkg_name_owned = pkg_name.to_string();
        let action_owned = action.to_string();
        let app_handle_clone = app_handle.clone();

        // Wrap on_progress in Arc<Mutex> so both closures can share it
        let on_progress = Arc::new(Mutex::new(on_progress));
        let on_progress_stderr = Arc::clone(&on_progress);

        let stdout_task = tokio::task::spawn_blocking(move || {
            read_output_lines(stdout, |line| {
                let event = parse_flatpak_progress(line, &pkg_name_owned, &action_owned);
                if let Some(e) = event {
                    if let Ok(mut cb) = on_progress.lock() { cb(e.clone()); }
                    let _ = app_handle_clone.emit("package-progress", &e);
                }
            });
        });

        let pkg_name_stderr = pkg_name.to_string();
        let action_stderr = action.to_string();
        let app_handle_stderr = app_handle.clone();
        let stderr_task = tokio::task::spawn_blocking(move || {
            read_output_lines(stderr, |line| {
                let event = parse_flatpak_progress(line, &pkg_name_stderr, &action_stderr);
                if let Some(e) = event {
                    if let Ok(mut cb) = on_progress_stderr.lock() { cb(e.clone()); }
                    let _ = app_handle_stderr.emit("package-progress", &e);
                }
            });
        });

        let _ = tokio::join!(stdout_task, stderr_task);

        let status = match child.wait() {
            Ok(s) => s,
            Err(e) => return (false, e.to_string()),
        };
        if status.success() {
            let _ = app_handle.emit("package-progress", &ProgressEvent {
                package_name: pkg_name.to_string(),
                action: action.to_string(),
                progress: 100,
                status: "completed".to_string(),
                message: "İşlem tamamlandı".to_string(),
            });
            (true, "Başarılı".to_string())
        } else {
            let _ = app_handle.emit("package-progress", &ProgressEvent {
                package_name: pkg_name.to_string(),
                action: action.to_string(),
                progress: 0,
                status: "error".to_string(),
                message: "İşlem başarısız oldu".to_string(),
            });
            (false, "Başarısız".to_string())
        }
    }

    #[allow(dead_code)]
    pub fn parse_luppo_upgrades_output(&self, text: &str) -> Vec<String> {
        let mut upgradable = Vec::new();
        for raw_line in text.lines() {
            let line = raw_line.trim();
            if line.is_empty() {
                continue;
            }

            let lower = line.to_lowercase();
            // Ignore system / informational / header / footer lines
            if lower.starts_with("sistem")
                || lower.starts_with("güncellen")
                || lower.starts_with("guncellen")
                || lower.starts_with("güncelle")
                || lower.starts_with("guncelle")
                || lower.starts_with("toplam")
                || lower.starts_with("tüm")
                || lower.starts_with("tum")
                || lower.starts_with("depo")
                || lower.starts_with("mevcut")
                || lower.starts_with("kaynak")
                || lower.starts_with("uyarı")
                || lower.starts_with("uyari")
                || lower.starts_with("hata")
                || lower.starts_with("warning")
                || lower.starts_with("error")
                || lower.starts_with('[')
                || lower.starts_with('*')
                || lower.starts_with('-')
            {
                continue;
            }

            // Extract package name (first part before " - " or first whitespace token)
            let token = if let Some(idx) = line.find(" - ") {
                &line[..idx]
            } else {
                line
            };
            let token = token.split_whitespace().next().unwrap_or("");
            let name = token.trim_matches(|c: char| c == '(' || c == ')' || c == '[' || c == ']' || c == ':' || c == ',');

            if name.is_empty() {
                continue;
            }

            let name_lower = name.to_lowercase();
            if name_lower == "güncellenebilir"
                || name_lower == "guncellenebilir"
                || name_lower == "toplam"
                || name_lower == "güncellemek"
                || name_lower == "guncellemek"
                || name_lower == "sistem"
                || name_lower == "depo"
                || name_lower == "paket"
                || name_lower == "paketler"
            {
                continue;
            }

            // Validate that the name is a real package (in installed/available or valid package name syntax)
            let is_installed = self.installed_packages.contains_key(name);
            let is_available = self.available_packages.contains_key(name);
            let is_valid_name = name.chars().all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_' || c == '.' || c == '+');

            let valid = if !self.installed_packages.is_empty() || !self.available_packages.is_empty() {
                is_installed || is_available
            } else {
                is_valid_name
            };

            if valid && !upgradable.contains(&name.to_string()) {
                upgradable.push(name.to_string());
            }
        }
        upgradable
    }

    pub fn check_for_updates(&mut self, update_repo: bool) -> (usize, Vec<String>, String) {
        let mut upgradable: Vec<String> = vec![];
        let error_msg = String::new();

        // 1. Reset all previous has_update flags so stale or invalid flags don't persist
        for p in self.installed_packages.values_mut() {
            p.has_update = false;
        }
        for p in self.available_packages.values_mut() {
            p.has_update = false;
        }

        // 2. Ensure installed packages are loaded so we can properly flag them
        if self.installed_packages.is_empty() {
            if self.luppo_available {
                self.load_installed_packages();
            }
            if self.flatpak_available {
                self.load_installed_flatpaks();
            }
        }

        // 3. Update repo if requested
        if update_repo && self.luppo_available {
            let _ = run_luppo_cmd(&["update-repo"]);
        }

        // 4. Luppo updates via Rust database API (language independent)
        if self.luppo_available {
            if let Ok(db) = open_luppo_db() {
                if let Ok(installed) = db.list_installed_packages() {
                    if let Ok(available) = db.list_available_packages() {
                        for inst in installed {
                            if let Some(remote) = available.iter().find(|p| p.name == inst.name) {
                                let version_changed = remote.latest_version() != inst.version;
                                let release_changed = remote.release != inst.release;
                                let hash_changed = !remote.package_hash.is_empty() && remote.package_hash != inst.package_hash;

                                if version_changed || release_changed || hash_changed {
                                    let name = inst.name.clone();
                                    if !upgradable.contains(&name) {
                                        upgradable.push(name.clone());
                                        if let Some(p) = self.installed_packages.get_mut(&name) {
                                            p.has_update = true;
                                            p.new_version = remote.latest_version().to_string();
                                        }
                                        if let Some(p) = self.available_packages.get_mut(&name) {
                                            p.has_update = true;
                                            p.new_version = remote.latest_version().to_string();
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // 5. Flatpak updates
        if self.flatpak_available {
            match Command::new("flatpak")
                .args(["remote-ls", "--updates", "--columns=application"])
                .output() {
                Ok(out) if out.status.success() => {
                    let text = String::from_utf8_lossy(&out.stdout);
                    for line in text.lines() {
                        let app_id = line.trim();
                        if app_id.is_empty() || app_id.starts_with("error") || app_id.starts_with("Warning") {
                            continue;
                        }
                        let key = format!("flatpak:{}", app_id);
                        if !upgradable.contains(&key) {
                            upgradable.push(key.clone());
                            if let Some(p) = self.installed_packages.get_mut(&key) {
                                p.has_update = true;
                            }
                            if let Some(p) = self.available_packages.get_mut(&key) {
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
        if !self.luppo_available { return false; }
        run_luppo_cmd(&["update-repo"]).0
    }
}

// ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────

pub fn format_bytes(bytes: u64) -> String {
    if bytes == 0 {
        return String::new();
    }
    const KB: u64 = 1024;
    const MB: u64 = KB * 1024;
    const GB: u64 = MB * 1024;

    if bytes >= GB {
        format!("{:.1} GB", bytes as f64 / GB as f64)
    } else if bytes >= MB {
        format!("{:.1} MB", bytes as f64 / MB as f64)
    } else if bytes >= KB {
        format!("{:.1} KB", bytes as f64 / KB as f64)
    } else {
        format!("{} B", bytes)
    }
}

pub fn open_luppo_db() -> Result<luppo_core::database::LuppoDatabase, String> {
    let config = luppo_core::config::Config::load(None);
    let original_db_path = config.directories.lib_dir.join("db");
    if !original_db_path.exists() {
        return Err("Luppo veritabanı bulunamadı".to_string());
    }

    let is_root = unsafe { libc::geteuid() == 0 };
    let db_path = if !is_root {
        let uid = unsafe { libc::geteuid() };
        let temp_db = std::env::temp_dir().join(format!("luppo-db-swcenter-{}", uid));
        let _ = copy_dir_all(&original_db_path, &temp_db);
        temp_db
    } else {
        original_db_path
    };

    luppo_core::database::LuppoDatabase::open(db_path)
        .map_err(|e| format!("Luppo veritabanı açılamadı: {}", e))
}

fn copy_dir_all(src: impl AsRef<Path>, dst: impl AsRef<Path>) -> std::io::Result<()> {
    let src = src.as_ref();
    let dst = dst.as_ref();
    std::fs::create_dir_all(dst)?;
    if let Ok(entries) = std::fs::read_dir(src) {
        for entry in entries.flatten() {
            let ty = entry.file_type()?;
            let dest_path = dst.join(entry.file_name());
            if ty.is_dir() {
                copy_dir_all(entry.path(), dest_path)?;
            } else {
                let _ = std::fs::copy(entry.path(), dest_path);
            }
        }
    }
    Ok(())
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

pub fn extract_flatpak_developer(app_id: &str) -> String {
    let lower = app_id.to_lowercase();
    if lower.contains("mozilla") { return "Mozilla".into(); }
    if lower.contains("discord") { return "Discord Inc.".into(); }
    if lower.contains("spotify") { return "Spotify".into(); }
    if lower.contains("valvesoftware") || lower.contains("steam") { return "Valve Software".into(); }
    if lower.contains("videolan") || lower.contains("vlc") { return "VideoLAN".into(); }
    if lower.contains("gimp") { return "GIMP Development Team".into(); }
    if lower.contains("blender") { return "Blender Foundation".into(); }
    if lower.contains("inkscape") { return "Inkscape Community".into(); }
    if lower.contains("kde.") || lower.starts_with("org.kde") { return "KDE Community".into(); }
    if lower.contains("gnome.") || lower.starts_with("org.gnome") { return "GNOME Project".into(); }
    if lower.contains("telegram") { return "Telegram FZ-LLC".into(); }
    if lower.contains("obsproject") { return "OBS Project".into(); }
    if lower.contains("microsoft") || lower.contains("visualstudio") { return "Microsoft".into(); }
    if lower.contains("jetbrains") { return "JetBrains".into(); }
    if lower.contains("google") || lower.contains("chromium") { return "Google".into(); }
    if lower.contains("libreoffice") || lower.contains("documentfoundation") { return "The Document Foundation".into(); }
    if lower.contains("audacity") { return "Audacity Team".into(); }
    if lower.contains("kodi") { return "XBMC Foundation".into(); }
    if lower.contains("github") {
        let parts: Vec<&str> = app_id.split('.').collect();
        if parts.len() >= 3 && parts[1].eq_ignore_ascii_case("github") {
            return capitalize(parts[2]);
        }
    }
    if lower.contains("gitlab") {
        let parts: Vec<&str> = app_id.split('.').collect();
        if parts.len() >= 3 && parts[1].eq_ignore_ascii_case("gitlab") {
            return capitalize(parts[2]);
        }
    }
    let parts: Vec<&str> = app_id.split('.').collect();
    if parts.len() >= 2 {
        let vendor = parts[1];
        if !vendor.is_empty() && vendor != "github" && vendor != "gitlab" {
            return capitalize(vendor);
        }
    }
    String::new()
}

fn search_appstream_icons(app_id: &str) -> Option<String> {
    let roots = [
        "/var/lib/flatpak/appstream",
        "/usr/share/flatpak/appstream",
    ];
    let home = std::env::var("HOME").unwrap_or_default();
    let user_root = format!("{}/.local/share/flatpak/appstream", home);

    let mut all_roots: Vec<&str> = roots.to_vec();
    if !home.is_empty() {
        all_roots.push(&user_root);
    }

    for root in all_roots {
        let root_path = Path::new(root);
        if !root_path.exists() { continue; }
        if let Ok(arch_entries) = std::fs::read_dir(root_path) {
            for repo in arch_entries.flatten() {
                let repo_path = repo.path();
                if !repo_path.is_dir() { continue; }
                if let Ok(sub_entries) = std::fs::read_dir(&repo_path) {
                    for arch in sub_entries.flatten() {
                        let arch_path = arch.path();
                        if !arch_path.is_dir() { continue; }
                        if let Ok(hash_entries) = std::fs::read_dir(&arch_path) {
                            for hash in hash_entries.flatten() {
                                let hash_path = hash.path();
                                if !hash_path.is_dir() { continue; }
                                for size in ["128x128", "64x64", "scalable", "256x256", "512x512"] {
                                    let icons_dir = hash_path.join("icons").join(size);
                                    for ext in [".png", ".svg", ".xpm", ".jpg"] {
                                        let file = icons_dir.join(format!("{}{}", app_id, ext));
                                        if file.exists() {
                                            return Some(file.to_string_lossy().to_string());
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    None
}

pub fn find_flatpak_icon(app_id: &str) -> String {
    let home = std::env::var("HOME").unwrap_or_default();
    let dirs = [
        "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps".to_string(),
        "/var/lib/flatpak/exports/share/icons/hicolor/512x512/apps".to_string(),
        "/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps".to_string(),
        "/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps".to_string(),
        "/var/lib/flatpak/exports/share/icons/hicolor/64x64/apps".to_string(),
        format!("{}/.local/share/flatpak/exports/share/icons/hicolor/scalable/apps", home),
        format!("{}/.local/share/flatpak/exports/share/icons/hicolor/128x128/apps", home),
        format!("{}/.local/share/flatpak/exports/share/icons/hicolor/64x64/apps", home),
    ];
    for dir in &dirs {
        for ext in ICON_EXTENSIONS {
            let p = format!("{}/{}{}", dir, app_id, ext);
            if Path::new(&p).exists() {
                return p;
            }
        }
    }

    if let Some(appstream_icon) = search_appstream_icons(app_id) {
        return appstream_icon;
    }

    let short = app_id.split('.').last().unwrap_or(app_id);
    let sys_icon = find_icon(short);
    if !sys_icon.is_empty() {
        return sys_icon;
    }

    // Flathub online fallback URL
    format!("https://dl.flathub.org/media/icons/128x128/{}.png", app_id)
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
        || ["htop", "neofetch", "gparted", "system", "kernel", "driver", "lupus", "luppo", "luppo-driver-installer", "luppo-package-installer", "luppo-converter", "aerosky", "auratask", "boot", "grub", "systemd", "udev", "dbus", "util-linux", "coreutils", "desktop", "plasma", "gnome", "xfce", "kde", "qt", "gtk", "xorg", "wayland", "mesa", "nvidia", "amd", "intel", "vulkan", "firmware", "disk", "auth", "pam", "sudo"].iter().any(|x| n.contains(x)) {
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
    if n.contains("lupus") || n.contains("luppo") || n.contains("auratask") || n.contains("aerosky") {
        return "Antolun".into();
    }
    if !homepage.is_empty() {
        if let Some(host) = homepage.trim_start_matches("https://").trim_start_matches("http://").split('/').next() {
            let clean_host = host.trim_start_matches("www.");
            return clean_host.to_string();
        }
    }
    "Bilinmeyen Geliştirici".into()
}

fn capitalize(s: &str) -> String {
    let mut c = s.chars();
    match c.next() {
        None => String::new(),
        Some(f) => f.to_uppercase().collect::<String>() + c.as_str(),
    }
}

fn build_root_command(binary: &str) -> Command {
    let is_root = unsafe { libc::geteuid() == 0 };
    if is_root {
        return Command::new(binary);
    }
    // Sudoers NOPASSWD kuralı tanımlıysa şifresiz sudo kullan
    let sudo_check = Command::new("sudo").args(["-n", "true"]).output();
    if let Ok(ref out) = sudo_check {
        if out.status.success() {
            let mut cmd = Command::new("sudo");
            cmd.arg("-n").arg(binary);
            return cmd;
        }
    }
    // Polkit kuralları / policy üzerinden pkexec kullan
    let mut cmd = Command::new("pkexec");
    cmd.arg(binary);
    cmd
}

fn run_luppo_cmd(args: &[&str]) -> (bool, String) {
    let mut cmd = build_root_command("luppo");
    cmd.args(args);
    match cmd.output() {
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

// ─── Progress Parsing & Realtime Stream Reading ────────────────────────────

fn read_output_lines<R: std::io::Read>(mut reader: R, mut callback: impl FnMut(&str)) {
    let mut buf = [0u8; 256];
    let mut line_buf = Vec::new();
    while let Ok(n) = reader.read(&mut buf) {
        if n == 0 {
            break;
        }
        for &b in &buf[..n] {
            if b == b'\n' || b == b'\r' {
                if !line_buf.is_empty() {
                    let s = String::from_utf8_lossy(&line_buf);
                    let trimmed = s.trim();
                    if !trimmed.is_empty() {
                        callback(trimmed);
                    }
                    line_buf.clear();
                }
            } else {
                line_buf.push(b);
            }
        }
    }
    if !line_buf.is_empty() {
        let s = String::from_utf8_lossy(&line_buf);
        let trimmed = s.trim();
        if !trimmed.is_empty() {
            callback(trimmed);
        }
    }
}

fn extract_percentage_or_ratio(line: &str) -> Option<u8> {
    // 1. Check for percentage tokens (e.g. 45%, %45, [45%], (45%), 45.2%, etc.)
    let words: Vec<&str> = line.split_whitespace().collect();
    for (i, word) in words.iter().enumerate() {
        let clean = word.trim_matches(|c: char| c == '(' || c == ')' || c == '[' || c == ']' || c == '{' || c == '}' || c == ',' || c == ':');
        
        if clean.starts_with('%') {
            let num_part = clean.trim_start_matches('%').trim_end_matches(|c: char| !c.is_ascii_digit() && c != '.');
            if let Ok(val) = num_part.parse::<f32>() {
                return Some(val.round().clamp(0.0, 100.0) as u8);
            }
        } else if clean.ends_with('%') {
            let num_part = clean.trim_end_matches('%').trim_start_matches(|c: char| !c.is_ascii_digit() && c != '.');
            if let Ok(val) = num_part.parse::<f32>() {
                return Some(val.round().clamp(0.0, 100.0) as u8);
            }
        } else if *word == "%" && i > 0 {
            let prev = words[i - 1].trim_matches(|c: char| !c.is_ascii_digit() && c != '.');
            if let Ok(val) = prev.parse::<f32>() {
                return Some(val.round().clamp(0.0, 100.0) as u8);
            }
        } else if *word == "%" && i + 1 < words.len() {
            let next = words[i + 1].trim_matches(|c: char| !c.is_ascii_digit() && c != '.');
            if let Ok(val) = next.parse::<f32>() {
                return Some(val.round().clamp(0.0, 100.0) as u8);
            }
        }
    }

    // 2. Check for ratio: e.g. "12.4 MB / 25.0 MB" or "12.4M / 25.0M" or "12.4 / 25.0"
    if let Some(slash_idx) = line.find('/') {
        let before = &line[..slash_idx];
        let after = &line[slash_idx + 1..];

        let before_num = before.split_whitespace().rev().find_map(|w| {
            let clean = w.trim_matches(|c: char| !c.is_ascii_digit() && c != '.');
            clean.parse::<f32>().ok()
        });

        let after_num = after.split_whitespace().find_map(|w| {
            let clean = w.trim_matches(|c: char| !c.is_ascii_digit() && c != '.');
            clean.parse::<f32>().ok()
        });

        if let (Some(cur), Some(tot)) = (before_num, after_num) {
            if tot > 0.0 && cur <= tot {
                let pct = ((cur / tot) * 100.0).round().clamp(0.0, 100.0) as u8;
                return Some(pct);
            }
        }
    }

    // 3. Step counts e.g. [1/4]
    for part in line.split(|c| c == '[' || c == ']' || c == '(' || c == ')') {
        let part = part.trim();
        if let Some(slash) = part.find('/') {
            let cur_s = part[..slash].trim();
            let tot_s = part[slash + 1..].trim();
            if let (Ok(cur), Ok(tot)) = (cur_s.parse::<f32>(), tot_s.parse::<f32>()) {
                if tot > 0.0 && cur <= tot {
                    let pct = ((cur / tot) * 100.0).round().clamp(0.0, 100.0) as u8;
                    return Some(pct);
                }
            }
        }
    }

    None
}

fn parse_luppo_progress(line: &str, pkg_name: &str, action: &str) -> Option<ProgressEvent> {
    let line = line.trim();
    if line.is_empty() {
        return None;
    }

    let lower = line.to_lowercase();
    let parsed_progress = extract_percentage_or_ratio(line);

    let (progress, status) = if let Some(p) = parsed_progress {
        let st = if p >= 100 {
            "completed"
        } else if lower.contains("kurul") || lower.contains("install") {
            "installing"
        } else if lower.contains("güncellen") || lower.contains("upgrade") || lower.contains("update") {
            "updating"
        } else if lower.contains("yapılandır") || lower.contains("configur") {
            "configuring"
        } else {
            "downloading"
        };
        (p, st)
    } else if lower.contains("tamamlandı") || lower.contains("complete") || lower.contains("başarılı") {
        (100, "completed")
    } else if lower.contains("yapılandır") || lower.contains("configur") {
        (90, "configuring")
    } else if lower.contains("güncellen") || lower.contains("upgrade") || lower.contains("update") {
        (70, "updating")
    } else if lower.contains("kurul") || lower.contains("install") {
        (70, "installing")
    } else if lower.contains("paketler açılıyor") || lower.contains("extract") || lower.contains("unpack") {
        (50, "extracting")
    } else if lower.contains("indir") || lower.contains("download") || lower.contains("alınıyor") {
        (15, "downloading")
    } else if lower.contains("kaldır") || lower.contains("remove") || lower.contains("uninstall") {
        (50, "removing")
    } else {
        return None;
    };

    Some(ProgressEvent {
        package_name: pkg_name.to_string(),
        action: action.to_string(),
        progress,
        status: status.to_string(),
        message: line.to_string(),
    })
}

fn parse_flatpak_progress(line: &str, pkg_name: &str, action: &str) -> Option<ProgressEvent> {
    let line = line.trim();
    if line.is_empty() {
        return None;
    }

    let lower = line.to_lowercase();
    let parsed_progress = extract_percentage_or_ratio(line);

    let (progress, status) = if let Some(p) = parsed_progress {
        let st = if p >= 100 {
            "completed"
        } else if lower.contains("update") || lower.contains("güncellen") || lower.contains("upgrade") {
            "updating"
        } else if lower.contains("install") || lower.contains("kur") {
            "installing"
        } else {
            "downloading"
        };
        (p, st)
    } else if lower.contains("complete") || lower.contains("tamamlandı") {
        (100, "completed")
    } else if lower.contains("update") || lower.contains("güncellen") || lower.contains("upgrade") {
        (75, "updating")
    } else if lower.contains("install") || lower.contains("kurul") {
        (75, "installing")
    } else if lower.contains("download") || lower.contains("indir") {
        (20, "downloading")
    } else if lower.contains("uninstall") || lower.contains("kaldır") {
        (50, "removing")
    } else {
        return None;
    };

    Some(ProgressEvent {
        package_name: pkg_name.to_string(),
        action: action.to_string(),
        progress,
        status: status.to_string(),
        message: line.to_string(),
    })
}

extern "C" {
    fn geteuid() -> u32;
}
mod libc {
    pub unsafe fn geteuid() -> u32 {
        super::geteuid()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_luppo_display_name() {
        assert_eq!(format_luppo_display_name("luppo-package-installer"), "Luppo Package Installer");
        assert_eq!(format_luppo_display_name("luppo-driver-installer"), "Luppo Driver Installer");
        assert_eq!(format_luppo_display_name("luppo-converter"), "Luppo Converter");
        assert_eq!(format_luppo_display_name("plasma-desktop"), "Plasma Desktop");
        assert_eq!(format_luppo_display_name("gnome-calculator"), "Gnome Calculator");
        assert_eq!(format_luppo_display_name("visual-studio-code"), "Visual Studio Code");
        assert_eq!(format_luppo_display_name("vlc"), "Vlc");
        assert_eq!(format_luppo_display_name("gparted"), "Gparted");
        assert_eq!(format_luppo_display_name("aerosky"), "Aerosky");
        assert_eq!(format_luppo_display_name("7-zip"), "7 Zip");
        assert_eq!(format_luppo_display_name(""), "");
        assert_eq!(format_luppo_display_name("---"), "");
        assert_eq!(format_luppo_display_name("-foo-bar-"), "Foo Bar");
    }

    #[test]
    fn test_package_info_new() {
        let pkg = PackageInfo::new("luppo-package-installer");
        assert_eq!(pkg.name, "luppo-package-installer");
        assert_eq!(pkg.display_name, "Luppo Package Installer");
        assert_eq!(pkg.origin, "Luppo");
    }

    #[test]
    fn test_parse_luppo_upgrades_output() {
        let mut backend = LuppoBackend::default();
        let mut pkg = PackageInfo::new("lupus-software-center");
        pkg.installed = true;
        backend.installed_packages.insert("lupus-software-center".to_string(), pkg);

        let output = r#"
Güncellenebilir Paketler:
lupus-software-center                 - LupuS Software Center - Luppo Market
Toplam 1 paket güncellenebilir.
Güncellemek için 'luppo upgrade' veya 'luppo up' komutunu kullanabilirsiniz.
"#;
        let upgrades = backend.parse_luppo_upgrades_output(output);
        assert_eq!(upgrades, vec!["lupus-software-center"]);

        let empty_output = "Sistem tamamen güncel.\n";
        let empty_upgrades = backend.parse_luppo_upgrades_output(empty_output);
        assert!(empty_upgrades.is_empty());
    }
}

