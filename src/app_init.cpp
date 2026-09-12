#include "src/app_init.h"
#include <QtWidgets/QApplication>
#include <QtCore/QLoggingCategory>

std::unique_ptr<QGuiApplication> create_qapplication() {
    qputenv("QT_LOGGING_RULES", "kf.iconthemes.warning=false;qt.qpa.wayland.warning=false");
    QLoggingCategory::setFilterRules(QStringLiteral("kf.iconthemes.warning=false\nqt.qpa.wayland.warning=false"));

    static int argc = 1;
    static char arg0[] = "lupus-software-center";
    static char* argv[] = { arg0, nullptr };
    auto app = std::make_unique<QApplication>(argc, argv);
    app->setQuitOnLastWindowClosed(false);
    return app;
}

