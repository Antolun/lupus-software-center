// LupuS Software Center – Tauri Komutları (Frontend ↔ Backend köprüsü)
// Python mainwindow.py worker thread'lerinin ve backend metodlarının Tauri karşılığı

use tauri::{State, Emitter};
use std::sync::Mutex;
use serde::{Deserialize, Serialize};
use crate::backend::{PackageInfo, LuppoBackend};
use crate::settings::{self, AppSettings};
use crate::i18n;

// ─── Global Backend State ───────────────────────────────────────────────────

pub struct BackendState(pub Mutex<LuppoBackend>);

// ─── Yanıt Türleri ──────────────────────────────────────────────────────────

#[derive(Serialize, Deserialize)]
pub struct ActionResponse {
    pub success: bool,
    pub message: String,
}

#[derive(Serialize, Deserialize)]
pub struct UpdatesResponse {
    pub count: usize,
    pub packages: Vec<String>,
    pub error: String,
}

#[derive(Serialize, Deserialize)]
pub struct CategoryInfo {
    pub id: String,
    pub icon: String,
    pub name: String,
    pub count: usize,
}

// icon_path → base64 data URI dönüştürücü
fn icon_path_to_data_uri(icon_path: &str) -> String {
    if icon_path.is_empty() {
        return String::new();
    }
    if icon_path.starts_with("http://") || icon_path.starts_with("https://") || icon_path.starts_with("data:") {
        return icon_path.to_string();
    }
    match std::fs::read(icon_path) {
        Ok(bytes) => {
            let b64_bytes = {
                let mut output = Vec::new();
                let alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
                for chunk in bytes.chunks(3) {
                    let n = match chunk.len() {
                        1 => (chunk[0] as u32) << 16,
                        2 => ((chunk[0] as u32) << 16) | ((chunk[1] as u32) << 8),
                        _ => ((chunk[0] as u32) << 16) | ((chunk[1] as u32) << 8) | chunk[2] as u32,
                    };
                    output.push(alphabet[((n >> 18) & 63) as usize]);
                    output.push(alphabet[((n >> 12) & 63) as usize]);
                    output.push(if chunk.len() > 1 { alphabet[((n >> 6) & 63) as usize] } else { b'=' });
                    output.push(if chunk.len() > 2 { alphabet[(n & 63) as usize] } else { b'=' });
                }
                output
            };
            let b64_str = String::from_utf8_lossy(&b64_bytes).to_string();
            let mime = if icon_path.ends_with(".svg") { "image/svg+xml" }
                      else if icon_path.ends_with(".png") { "image/png" }
                      else if icon_path.ends_with(".jpg") || icon_path.ends_with(".jpeg") { "image/jpeg" }
                      else { "image/png" };
            format!("data:{};base64,{}", mime, b64_str)
        },
        Err(_) => String::new(),
    }
}

// ─── Komutlar ───────────────────────────────────────────────────────────────

#[tauri::command]
pub async fn get_installed_packages(state: State<'_, BackendState>) -> Result<Vec<PackageInfo>, String> {
    let mut backend = state.0.lock().map_err(|e| e.to_string())?;
    if backend.installed_packages.is_empty() {
        backend.load_installed_packages();
        backend.load_installed_flatpaks();
    }
    let mut pkgs: Vec<PackageInfo> = backend.installed_packages.values().cloned().map(|mut p| {
        if !p.icon_path.is_empty() && !p.icon_path.starts_with("data:") {
            p.icon_path = icon_path_to_data_uri(&p.icon_path);
        }
        p
    }).collect();
    pkgs.sort_by(|a, b| a.display_name.to_lowercase().cmp(&b.display_name.to_lowercase()));
    Ok(pkgs)
}

#[tauri::command]
pub async fn get_available_packages(state: State<'_, BackendState>) -> Result<Vec<PackageInfo>, String> {
    let mut backend = state.0.lock().map_err(|e| e.to_string())?;
    if backend.available_packages.is_empty() {
        if backend.installed_packages.is_empty() {
            backend.load_installed_packages();
            backend.load_installed_flatpaks();
        }
        backend.load_available_packages();
        if backend.flatpak_available {
            backend.load_available_flatpaks();
        }
    }
    let mut pkgs: Vec<PackageInfo> = backend.get_all_packages().into_values().map(|mut p| {
        if !p.icon_path.is_empty() && !p.icon_path.starts_with("data:") {
            p.icon_path = icon_path_to_data_uri(&p.icon_path);
        }
        p
    }).collect();
    pkgs.sort_by(|a, b| a.display_name.to_lowercase().cmp(&b.display_name.to_lowercase()));
    Ok(pkgs)
}

#[tauri::command]
pub async fn get_package_details(package_name: String, state: State<'_, BackendState>) -> Result<PackageInfo, String> {
    let mut backend = state.0.lock().map_err(|e| e.to_string())?;
    let pkg = backend.enrich_package_info(&package_name)
        .ok_or_else(|| i18n::tr("pkg_not_found"))?;
    Ok(pkg)
}

pub fn is_self_package(pkg_name: &str) -> bool {
    let name = pkg_name.trim_start_matches("flatpak:").to_lowercase();
    name == "lupus-software-center" || name == env!("CARGO_PKG_NAME")
}

pub fn restart_app(app_handle: &tauri::AppHandle) {
    log::info!("Kendini güncelleme sonrası uygulama yeniden başlatılıyor...");
    
    std::thread::sleep(std::time::Duration::from_millis(500));

    let mut restarted = false;

    if let Ok(exe) = std::env::current_exe() {
        let exe_str = exe.to_string_lossy();
        let target_exe = if exe_str.ends_with(" (deleted)") {
            std::path::PathBuf::from(exe_str.trim_end_matches(" (deleted)"))
        } else {
            exe.clone()
        };

        if target_exe.exists() {
            let args: Vec<String> = std::env::args().skip(1).collect();
            if let Ok(_) = std::process::Command::new(&target_exe).args(&args).spawn() {
                restarted = true;
            }
        }
    }

    if !restarted {
        if std::path::Path::new("/usr/bin/lupus-software-center").exists() {
            let args: Vec<String> = std::env::args().skip(1).collect();
            if let Ok(_) = std::process::Command::new("/usr/bin/lupus-software-center").args(&args).spawn() {
                restarted = true;
            }
        }
    }

    if restarted {
        app_handle.exit(0);
    } else {
        app_handle.restart();
    }
}

#[tauri::command]
pub async fn install_package(
    package_name: String,
    state: State<'_, BackendState>,
    app_handle: tauri::AppHandle,
) -> Result<ActionResponse, String> {
    let pkg_name = package_name.clone();
    let app_handle_cb = app_handle.clone();
    let is_self = is_self_package(&pkg_name);

    // Clone the backend out of the lock so we don't hold MutexGuard across .await
    let backend_clone = {
        let backend = state.0.lock().map_err(|e| e.to_string())?;
        backend.clone()
    };

    let (success, message) = backend_clone.install_package_with_progress(&pkg_name, &app_handle, move |event| {
        let _ = app_handle_cb.emit("package-progress", &event);
    }).await;

    if success {
        let mut backend = state.0.lock().map_err(|e| e.to_string())?;
        if let Some(pkg) = backend.available_packages.get_mut(&pkg_name) {
            pkg.installed = true;
            pkg.has_update = false;
        }
        if let Some(pkg) = backend.installed_packages.get_mut(&pkg_name) {
            pkg.has_update = false;
        } else if let Some(pkg) = backend.available_packages.get(&pkg_name).cloned() {
            backend.installed_packages.insert(pkg_name.clone(), pkg);
        }
    }

    if success && is_self {
        let app_handle_restart = app_handle.clone();
        tokio::spawn(async move {
            tokio::time::sleep(std::time::Duration::from_millis(800)).await;
            restart_app(&app_handle_restart);
        });
    }

    Ok(ActionResponse { success, message })
}

#[tauri::command]
pub async fn remove_package(
    package_name: String,
    state: State<'_, BackendState>,
    app_handle: tauri::AppHandle,
) -> Result<ActionResponse, String> {
    let pkg_name = package_name.clone();
    let app_handle_cb = app_handle.clone();

    // Clone the backend out of the lock so we don't hold MutexGuard across .await
    let backend_clone = {
        let backend = state.0.lock().map_err(|e| e.to_string())?;
        backend.clone()
    };

    let (success, message) = backend_clone.remove_package_with_progress(&pkg_name, &app_handle, move |event| {
        let _ = app_handle_cb.emit("package-progress", &event);
    }).await;

    if success {
        let mut backend = state.0.lock().map_err(|e| e.to_string())?;
        backend.installed_packages.remove(&pkg_name);
        if let Some(pkg) = backend.available_packages.get_mut(&pkg_name) {
            pkg.installed = false;
            pkg.has_update = false;
        }
    }

    Ok(ActionResponse { success, message })
}

#[tauri::command]
pub async fn search_packages(query: String, state: State<'_, BackendState>) -> Result<Vec<PackageInfo>, String> {
    let backend = state.0.lock().map_err(|e| e.to_string())?;
    let mut results = backend.search_packages(&query).into_iter().map(|mut p| {
        if !p.icon_path.is_empty() && !p.icon_path.starts_with("data:") {
            p.icon_path = icon_path_to_data_uri(&p.icon_path);
        }
        p
    }).collect::<Vec<_>>();
    results.sort_by(|a, b| a.display_name.to_lowercase().cmp(&b.display_name.to_lowercase()));
    Ok(results)
}

#[tauri::command]
pub async fn check_for_updates(update_repo: bool, state: State<'_, BackendState>) -> Result<UpdatesResponse, String> {
    let mut backend = state.0.lock().map_err(|e| e.to_string())?;
    let (count, packages, error) = backend.check_for_updates(update_repo);
    Ok(UpdatesResponse { count, packages, error })
}

#[tauri::command]
pub async fn update_repo(state: State<'_, BackendState>) -> Result<ActionResponse, String> {
    let backend = state.0.lock().map_err(|e| e.to_string())?;
    let success = backend.update_repo();
    let message = if success {
        i18n::tr("repo_update_success")
    } else {
        i18n::tr("repo_update_error")
    };
    Ok(ActionResponse { success, message })
}

#[tauri::command]
pub async fn get_flatpak_info(app_id: String) -> Result<serde_json::Value, String> {
    let real_id = app_id.trim_start_matches("flatpak:");
    let url = format!("https://flathub.org/api/v2/appstream/{}", real_id);
    
    let result = tokio::task::spawn_blocking(move || {
        reqwest::blocking::Client::builder()
            .user_agent("Mozilla/5.0 (X11; Linux x86_64)")
            .timeout(std::time::Duration::from_secs(8))
            .build()
            .ok()?
            .get(&url)
            .send()
            .ok()?
            .json::<serde_json::Value>()
            .ok()
    }).await.map_err(|e| e.to_string())?;
    
    result.ok_or_else(|| i18n::tr("flathub_fetch_failed"))
}

#[tauri::command]
pub async fn load_settings() -> Result<AppSettings, String> {
    let settings = settings::load_settings();
    i18n::set_lang(&settings.language);
    Ok(settings)
}

#[tauri::command]
pub async fn save_settings(new_settings: AppSettings) -> Result<ActionResponse, String> {
    i18n::set_lang(&new_settings.language);
    match settings::save_settings(&new_settings) {
        Ok(()) => Ok(ActionResponse {
            success: true,
            message: i18n::tr("settings_saved"),
        }),
        Err(e) => Ok(ActionResponse {
            success: false,
            message: e,
        }),
    }
}

#[tauri::command]
pub async fn set_autostart(enabled: bool) -> Result<ActionResponse, String> {
    match settings::set_autostart(enabled) {
        Ok(()) => Ok(ActionResponse {
            success: true,
            message: i18n::tr("autostart_updated"),
        }),
        Err(e) => Ok(ActionResponse {
            success: false,
            message: e,
        }),
    }
}

#[tauri::command]
pub async fn get_luppo_available(state: State<'_, BackendState>) -> Result<bool, String> {
    let backend = state.0.lock().map_err(|e| e.to_string())?;
    Ok(backend.luppo_available)
}

#[tauri::command]
pub async fn get_flatpak_available(state: State<'_, BackendState>) -> Result<bool, String> {
    let backend = state.0.lock().map_err(|e| e.to_string())?;
    Ok(backend.flatpak_available)
}

#[tauri::command]
pub async fn get_categories(state: State<'_, BackendState>) -> Result<Vec<CategoryInfo>, String> {
    let mut backend = state.0.lock().map_err(|e| e.to_string())?;
    if backend.available_packages.is_empty() {
        if backend.installed_packages.is_empty() {
            backend.load_installed_packages();
            backend.load_installed_flatpaks();
        }
        backend.load_available_packages();
        if backend.flatpak_available {
            backend.load_available_flatpaks();
        }
    }

    let all = backend.get_all_packages();
    let mut counts: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
    for pkg in all.values() {
        *counts.entry(pkg.category.clone()).or_insert(0) += 1;
    }

    let category_meta: Vec<(&str, &str, &str)> = vec![
        ("all", "plasma-search", "nav_discover"),
        ("development", "applications-development", "nav_development"),
        ("education", "applications-education", "nav_education"),
        ("enterprise", "applications-office", "nav_enterprise"),
        ("games", "applications-games", "nav_games"),
        ("graphics", "applications-graphics", "nav_graphics"),
        ("internet", "applications-internet", "nav_internet"),
        ("multimedia", "applications-multimedia", "nav_multimedia"),
        ("office", "applications-office", "nav_office"),
        ("system", "applications-system", "nav_system"),
        ("utilities", "applications-utilities", "nav_utilities"),
    ];

    let mut result: Vec<CategoryInfo> = category_meta.iter().map(|(id, icon, name_key)| {
        let count = if *id == "all" {
            all.len()
        } else {
            *counts.get(*id).unwrap_or(&0)
        };
        CategoryInfo {
            id: id.to_string(),
            icon: icon.to_string(),
            name: i18n::tr(name_key),
            count,
        }
    }).collect();

    // Updates kategorisi
    let update_count = backend.installed_packages.values().filter(|p| p.has_update).count();
    result.push(CategoryInfo {
        id: "updates".to_string(),
        icon: "view-refresh".to_string(),
        name: i18n::tr("nav_downloads"),
        count: update_count,
    });

    Ok(result)
}

#[tauri::command]
pub async fn get_icon_path(icon_name: String) -> Result<String, String> {
    Ok(crate::backend::find_icon(&icon_name))
}

#[tauri::command]
pub async fn get_icon_base64(icon_path: String) -> Result<String, String> {
    Ok(icon_path_to_data_uri(&icon_path))
}

#[tauri::command]
pub async fn get_app_version() -> Result<String, String> {
    Ok(crate::backend::VERSION.to_string())
}

#[tauri::command]
pub async fn open_external(url: String) -> Result<(), String> {
    std::process::Command::new("xdg-open")
        .arg(&url)
        .spawn()
        .map(|_| ())
        .map_err(|e| e.to_string())
}
