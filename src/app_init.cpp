#include "src/app_init.h"
#include <QtWidgets/QApplication>
#include <QtCore/QLoggingCategory>
#include <QtCore/QCoreApplication>
#include <QtDBus/QDBusMessage>
#include <QtDBus/QDBusConnection>

extern "C" void set_application_title(const char* title) {
    if (!title) return;
    QString qTitle = QString::fromUtf8(title);
    QCoreApplication::setApplicationName(qTitle);
    QGuiApplication::setApplicationDisplayName(qTitle);

    // Broadcast NewTitle on D-Bus so StatusNotifierItem listeners (e.g. Plasma system tray)
    // immediately refresh the title shown without hovering
    if (QDBusConnection::sessionBus().isConnected()) {
        QDBusMessage msg = QDBusMessage::createSignal(
            QStringLiteral("/StatusNotifierItem"),
            QStringLiteral("org.kde.StatusNotifierItem"),
            QStringLiteral("NewTitle")
        );
        QDBusConnection::sessionBus().send(msg);
    }
}

// Returns true  → this is the first instance, proceed normally.
// Returns false → a running instance was found; caller should exit.
extern "C" bool acquire_single_instance(bool send_activate) {
    const char* user = getenv("USER");
    std::string path = std::string("/tmp/lupus-software-center-") +
                       (user ? user : "user") + ".sock";

    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return true;   // Can't check → assume first instance

    struct sockaddr_un addr{};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path.c_str(), sizeof(addr.sun_path) - 1);

    bool another_running = (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) == 0);
    if (another_running) {
        if (send_activate) {
            // Send activate signal to the running instance
            const char* msg = "activate";
            send(fd, msg, strlen(msg), 0);
        }
        close(fd);
        return false;
    }
    close(fd);
    return true;   // First instance
}

std::unique_ptr<QGuiApplication> create_qapplication() {
    qputenv("QT_LOGGING_RULES", "kf.iconthemes.warning=false;qt.qpa.wayland.warning=false");
    QLoggingCategory::setFilterRules(QStringLiteral("kf.iconthemes.warning=false\nqt.qpa.wayland.warning=false"));

    static int argc = 1;
    static char arg0[] = "lupus-software-center";
    static char* argv[] = { arg0, nullptr };
    auto app = std::make_unique<QApplication>(argc, argv);
    app->setQuitOnLastWindowClosed(false);
    QGuiApplication::setDesktopFileName(QStringLiteral("lupus-software-center"));
    return app;
}
