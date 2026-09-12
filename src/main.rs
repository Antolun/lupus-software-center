// LupuS Software Center - CXX-Qt Main Entry Point

mod backend;
pub mod cxxqt_object;
mod i18n;
mod settings;

use cxx_qt_lib::{QQmlApplicationEngine, QUrl};

static IS_MINIMIZED: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

pub fn is_start_minimized() -> bool {
    IS_MINIMIZED.load(std::sync::atomic::Ordering::Relaxed)
}

// Link directly to the C++ functions via FFI
extern "C" {
    fn acquire_single_instance(send_activate: bool) -> bool;
    fn set_application_title(title: *const std::ffi::c_char);
}

fn main() {
    let start_minimized = std::env::args().any(|a| a == "--minimized" || a == "-m");
    IS_MINIMIZED.store(start_minimized, std::sync::atomic::Ordering::Relaxed);

    // ── Single instance guard ──────────────────────────────────────────────
    // If another instance is running:
    // - Without --minimized: send "activate" to raise its window and exit
    // - With --minimized: do not send "activate", just exit cleanly
    let is_first = unsafe { acquire_single_instance(!start_minimized) };
    if !is_first {
        std::process::exit(0);
    }

    // ── Load user settings & set language before QML engine starts ─────────
    let saved_settings = settings::load_settings();
    i18n::set_lang(&saved_settings.language);

    let app_title = format!("LupuS {}", i18n::tr("software_center"));
    glib::set_application_name(&app_title);

    // Set initial application name before creating QApplication
    if let Ok(c_title) = std::ffi::CString::new(app_title.clone()) {
        unsafe { set_application_title(c_title.as_ptr()); }
    }

    let mut app = cxxqt_object::qobject::create_qapplication();

    // Re-apply to ensure QApplication instance has the localized name and display name set
    if let Ok(c_title) = std::ffi::CString::new(app_title) {
        unsafe { set_application_title(c_title.as_ptr()); }
    }

    let mut engine = QQmlApplicationEngine::new();

    if let Some(engine) = engine.as_mut() {
        engine.load(&QUrl::from("qrc:/qt/qml/com/antolun/lupus/software/center/qml/Main.qml"));
    }

    if let Some(app) = app.as_mut() {
        app.exec();
    }
}
