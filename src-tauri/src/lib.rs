// LupuS Software Center - Rust Backend
// Tüm paket yönetimi, Flatpak entegrasyonu ve sistem komutları burada

mod backend;
mod i18n;
mod settings;
mod commands;
mod tray;

use std::sync::Mutex;
use tauri::Manager;

pub fn run(minimized: bool) {
    // Tepsi (StatusNotifierItem) başlığı g_get_application_name()'den türetilir;
    // aksi halde binary adı ("lupus-software-center") görünür.
    glib::set_application_name("LupuS Software Center");

    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(win) = app.get_webview_window("main") {
                let _ = win.show();
                let _ = win.set_focus();
            }
        }))
        .plugin(
            tauri_plugin_log::Builder::new()
                .level(log::LevelFilter::Info)
                .level_for("reqwest", log::LevelFilter::Warn)
                .level_for("hyper", log::LevelFilter::Warn)
                .level_for("hyper_util", log::LevelFilter::Warn)
                .build(),
        )
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_fs::init())
        .setup(move |app| {
            // BackendState initialize
            app.manage(commands::BackendState(Mutex::new(backend::LuppoBackend::new())));
            // Tray icon kurulumu
            tray::setup_tray(app)?;
            // Arka plan güncelleme denetleyicisi
            start_background_services(app.handle());
            // --minimized ile başlatıldıysa pencereyi gizle
            if minimized {
                if let Some(win) = app.get_webview_window("main") {
                    let _ = win.hide();
                }
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            // Kapatma → tepsiye küçült (ayar aktifse)
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let settings = settings::load_settings();
                if settings.close_to_tray {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_installed_packages,
            commands::get_available_packages,
            commands::get_package_details,
            commands::install_package,
            commands::remove_package,
            commands::search_packages,
            commands::check_for_updates,
            commands::update_repo,
            commands::get_flatpak_info,
            commands::load_settings,
            commands::save_settings,
            commands::set_autostart,
            commands::get_luppo_available,
            commands::get_flatpak_available,
            commands::get_categories,
            commands::get_icon_path,
            commands::get_icon_base64,
            commands::get_app_version,
            commands::open_external,
        ])
        .run(tauri::generate_context!())
        .expect("LupuS Software Center başlatılamadı");
}

// ─── Arka Plan Servisleri (Otomatik Güncelleme Denetleyici) ─────────────────

fn start_background_services(app: &tauri::AppHandle) {
    let app_handle = app.clone();

    tauri::async_runtime::spawn(async move {
        // Başlangıçtan kısa süre sonra ilk kontrol (rozeti doldurur)
        tokio::time::sleep(std::time::Duration::from_secs(15)).await;
        run_update_check(&app_handle, false).await;

        loop {
            let interval = settings::load_settings().check_interval_hours;
            if interval <= 0 {
                // Ayar kapalı; 1 saat sonra tekrar bak (ayar değişikliğini yakala)
                tokio::time::sleep(std::time::Duration::from_secs(3600)).await;
                continue;
            }
            tokio::time::sleep(std::time::Duration::from_secs(interval as u64 * 3600)).await;
            run_update_check(&app_handle, false).await;
        }
    });
}

async fn run_update_check(app: &tauri::AppHandle, update_repo: bool) {
    use tauri::Emitter;

    let state = app.state::<commands::BackendState>();
    let (count, packages, _error) = {
        let mut backend = state.0.lock().unwrap();
        backend.check_for_updates(update_repo)
    };

    let settings = settings::load_settings();
    let mut auto_installed = Vec::new();
    let mut final_count = count;
    if settings.auto_install_updates && count > 0 {
        for pkg in &packages {
            let (success, _msg) = {
                let backend = state.0.lock().unwrap();
                backend.install_package(pkg)
            };
            if success {
                auto_installed.push(pkg.clone());
            }
        }
        // Kurulum sonrası kalan güncelleme sayısını yeniden hesapla
        if !auto_installed.is_empty() {
            let (remaining, _, _) = {
                let mut backend = state.0.lock().unwrap();
                backend.check_for_updates(false)
            };
            final_count = remaining;
        }
    }

    let _ = app.emit_to(
        "main",
        "updates-checked",
        serde_json::json!({
            "count": final_count,
            "packages": packages,
            "auto_installed": auto_installed,
        }),
    );
}