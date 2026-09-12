use cxx_qt_build::{CxxQtBuilder, QmlFile, QmlModule};

fn main() {
    let builder = CxxQtBuilder::new_qml_module(
        QmlModule::new("com.antolun.lupus.software.center")
            .qml_file("qml/Main.qml")
            .qml_file(QmlFile::from("qml/Theme.qml").singleton(true))
            .qml_file("qml/AppCard.qml")
            .qml_file("qml/Sidebar.qml")
            .qml_file("qml/Topbar.qml")
            .qml_file("qml/SearchSuggestions.qml")
            .qml_file("qml/DiscoverView.qml")
            .qml_file("qml/CategoryView.qml")
            .qml_file("qml/InstalledUpdatesView.qml")
            .qml_file("qml/SearchView.qml")
            .qml_file("qml/DetailView.qml")
            .qml_file("qml/SettingsView.qml")
            .qml_file("qml/AboutView.qml")
            .qml_file("qml/ImageModal.qml")
            .qml_file("qml/LoadingOverlay.qml"),
    )
    .qt_module("Network")
    .qt_module("Quick")
    .qt_module("QuickControls2")
    .qt_module("Svg")
    .qt_module("Widgets")
    .qrc("resources.qrc")
    .files(["src/cxxqt_object.rs"])
    .cpp_file("src/app_init.cpp");

    let builder = unsafe {
        builder.cc_builder(|cc| {
            cc.flag_if_supported("-Wno-sfinae-incomplete");
        })
    };

    builder.build();
}
