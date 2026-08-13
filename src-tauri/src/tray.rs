// PiSiM – Sistem Tepsisi (System Tray)
// Python MainWindow._setup_system_tray()'ın Rust karşılığı

use crate::i18n;

use tauri::{
    App,
    Emitter,
    Manager,
    menu::{Menu, MenuItem},
    tray::{MouseButton, TrayIconBuilder, TrayIconEvent},
};

pub fn setup_tray(app: &mut App) -> Result<(), Box<dyn std::error::Error>> {
    let open_item = MenuItem::with_id(app, "open", i18n::tr("tray_open_app"), true, None::<&str>)?;
    let check_item = MenuItem::with_id(app, "check_updates", i18n::tr("tray_check_updates"), true, None::<&str>)?;
    let quit_item = MenuItem::with_id(app, "quit", i18n::tr("tray_exit"), true, None::<&str>)?;

    let menu = Menu::with_items(app, &[&open_item, &check_item, &quit_item])?;

    let _tray = TrayIconBuilder::with_id("pisim-tray")
        .icon(app.default_window_icon().unwrap().clone())
        .tooltip("PiSiM")
        .title("PiSiM")
        .menu(&menu)
        .on_menu_event(move |app, event| {
            match event.id.as_ref() {
                "open" => {
                    if let Some(win) = app.get_webview_window("main") {
                        let _ = win.show();
                        let _ = win.set_focus();
                    }
                }
                "check_updates" => {
                    // Frontend'e güncelleme kontrolü tetikle
                    if let Some(win) = app.get_webview_window("main") {
                        let _ = win.emit("tray-check-updates", ());
                    }
                }
                "quit" => {
                    app.exit(0);
                }
                _ => {}
            }
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click { button: MouseButton::Left, .. } = event {
                let app = tray.app_handle();
                if let Some(win) = app.get_webview_window("main") {
                    if win.is_visible().unwrap_or(false) {
                        let _ = win.hide();
                    } else {
                        let _ = win.show();
                        let _ = win.set_focus();
                    }
                }
            }
        })
        .build(app)?;

    Ok(())
}
