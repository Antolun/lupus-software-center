// LupuS Software Center - CXX-Qt Main Entry Point

mod backend;
pub mod cxxqt_object;
mod i18n;
mod settings;

use cxx_qt_lib::{QQmlApplicationEngine, QUrl};

fn main() {
    glib::set_application_name("LupuS Software Center");

    // Load user settings and apply language before QML engine starts
    let saved_settings = settings::load_settings();
    i18n::set_lang(&saved_settings.language);

    let mut app = cxxqt_object::qobject::create_qapplication();
    let mut engine = QQmlApplicationEngine::new();

    if let Some(engine) = engine.as_mut() {
        engine.load(&QUrl::from("qrc:/qt/qml/com/antolun/lupus/software/center/qml/Main.qml"));
    }

    if let Some(app) = app.as_mut() {
        app.exec();
    }
}

