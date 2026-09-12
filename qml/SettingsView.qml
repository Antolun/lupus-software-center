import QtQuick
import QtQuick.Controls
import com.antolun.lupus.software.center 1.0

ScrollView {
    id: root

    property bool autostart: false
    property bool closeToTray: true
    property bool autoInstall: false
    property int checkInterval: 4
    property string currentLanguage: "tr"
    property string currentTheme: "auto"

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal settingsChanged(var newSettings)

    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical.policy: ScrollBar.AsNeeded

    function emitSave() {
        var s = {
            autostart: chkAutostart.checked,
            close_to_tray: chkCloseToTray.checked,
            auto_install_updates: chkAutoInstall.checked,
            check_interval_hours: intervalCombo.model[intervalCombo.currentIndex].val,
            language: langCombo.model[langCombo.currentIndex].val,
            theme: Theme.themeMode
        }
        root.settingsChanged(s)
    }

    Item {
        width: Math.min(root.width - 48, 880)
        implicitHeight: mainSettingsCol.height + 64
        anchors.horizontalCenter: parent.horizontalCenter

        Column {
            id: mainSettingsCol
            width: parent.width
            topPadding: 28
            bottomPadding: 48
            spacing: 24

            // ══════════════════════════════════════════════════════════════════
            // 1. PAGE HEADER
            // ══════════════════════════════════════════════════════════════════
            Column {
                spacing: 4
                width: parent.width

                Row {
                    spacing: 12
                    Rectangle {
                        width: 40
                        height: 40
                        radius: 10
                        color: Theme.surfaceBg
                        border.color: Theme.border
                        border.width: 1
                        anchors.verticalCenter: parent.verticalCenter

                        Image {
                            source: "qrc:/qml/assets/icons/settings-configure.svg"
                            width: 22
                            height: 22
                            anchors.centerIn: parent
                        }
                    }

                    Text {
                        text: tr("settings_title")
                        color: Theme.textPrimary
                        font.pixelSize: 24
                        font.bold: true
                        font.family: Theme.fontFamily
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }

            // ══════════════════════════════════════════════════════════════════
            // 2. SECTION: APPEARANCE & THEME
            // ══════════════════════════════════════════════════════════════════
            Rectangle {
                width: parent.width
                implicitHeight: themeSecCol.implicitHeight + 36
                radius: 14
                color: Theme.cardBg
                border.color: Theme.border
                border.width: 1

                Column {
                    id: themeSecCol
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 16

                    Column {
                        spacing: 2
                        Text {
                            text: tr("settings_section_appearance")
                            color: Theme.textPrimary
                            font.pixelSize: 15
                            font.bold: true
                            font.family: Theme.fontFamily
                        }
                        Text {
                            text: tr("settings_theme_desc")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.family: Theme.fontFamily
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: Theme.border }

                    Row {
                        width: parent.width
                        spacing: 12

                        // Auto Option
                        Rectangle {
                            width: (parent.width - 24) / 3
                            height: 52
                            radius: 10
                            readonly property bool isSelected: Theme.themeMode === "auto"
                            color: isSelected ? Qt.rgba(Theme.accentTeal.r, Theme.accentTeal.g, Theme.accentTeal.b, 0.15) : (autoOptMouse.containsMouse ? Theme.surfaceBg : "transparent")
                            border.color: isSelected ? Theme.accentTeal : Theme.border
                            border.width: isSelected ? 2 : 1

                            Row {
                                anchors.centerIn: parent
                                spacing: 8
                                Text {
                                    text: "💻"
                                    font.pixelSize: 14
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: tr("theme_auto")
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }

                            MouseArea {
                                id: autoOptMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    Theme.themeMode = "auto"
                                    root.emitSave()
                                }
                            }
                        }

                        // Dark Option
                        Rectangle {
                            width: (parent.width - 24) / 3
                            height: 52
                            radius: 10
                            readonly property bool isSelected: Theme.themeMode === "dark"
                            color: isSelected ? Qt.rgba(Theme.accentTeal.r, Theme.accentTeal.g, Theme.accentTeal.b, 0.15) : (darkOptMouse.containsMouse ? Theme.surfaceBg : "transparent")
                            border.color: isSelected ? Theme.accentTeal : Theme.border
                            border.width: isSelected ? 2 : 1

                            Row {
                                anchors.centerIn: parent
                                spacing: 8
                                Text {
                                    text: "🌙"
                                    font.pixelSize: 14
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: tr("theme_dark")
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }

                            MouseArea {
                                id: darkOptMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    Theme.themeMode = "dark"
                                    root.emitSave()
                                }
                            }
                        }

                        // Light Option
                        Rectangle {
                            width: (parent.width - 24) / 3
                            height: 52
                            radius: 10
                            readonly property bool isSelected: Theme.themeMode === "light"
                            color: isSelected ? Qt.rgba(Theme.accentTeal.r, Theme.accentTeal.g, Theme.accentTeal.b, 0.15) : (lightOptMouse.containsMouse ? Theme.surfaceBg : "transparent")
                            border.color: isSelected ? Theme.accentTeal : Theme.border
                            border.width: isSelected ? 2 : 1

                            Row {
                                anchors.centerIn: parent
                                spacing: 8
                                Text {
                                    text: "☀️"
                                    font.pixelSize: 14
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: tr("theme_light")
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }

                            MouseArea {
                                id: lightOptMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    Theme.themeMode = "light"
                                    root.emitSave()
                                }
                            }
                        }
                    }
                }
            }

            // ══════════════════════════════════════════════════════════════════
            // 3. SECTION: GENERAL & STARTUP
            // ══════════════════════════════════════════════════════════════════
            Rectangle {
                width: parent.width
                implicitHeight: genSecCol.implicitHeight + 36
                radius: 14
                color: Theme.cardBg
                border.color: Theme.border
                border.width: 1

                Column {
                    id: genSecCol
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 16

                    Column {
                        spacing: 2
                        Text {
                            text: tr("settings_section_general")
                            color: Theme.textPrimary
                            font.pixelSize: 15
                            font.bold: true
                            font.family: Theme.fontFamily
                        }
                        Text {
                            text: tr("settings_general_desc")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.family: Theme.fontFamily
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: Theme.border }

                    // Autostart Setting Row
                    Item {
                        width: parent.width
                        height: 44

                        Column {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 3
                            Text {
                                text: tr("settings_autostart")
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                font.bold: true
                                font.family: Theme.fontFamily
                            }
                            Text {
                                text: tr("settings_autostart_desc")
                                color: Theme.textSecondary
                                font.pixelSize: 11
                                font.family: Theme.fontFamily
                            }
                        }

                        CheckBox {
                            id: chkAutostart
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            checked: root.autostart
                            onToggled: root.emitSave()
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: Theme.border }

                    // Close to Tray Setting Row
                    Item {
                        width: parent.width
                        height: 44

                        Column {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 3
                            Text {
                                text: tr("settings_close_to_tray")
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                font.bold: true
                                font.family: Theme.fontFamily
                            }
                            Text {
                                text: tr("settings_close_to_tray_desc")
                                color: Theme.textSecondary
                                font.pixelSize: 11
                                font.family: Theme.fontFamily
                            }
                        }

                        CheckBox {
                            id: chkCloseToTray
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            checked: root.closeToTray
                            onToggled: root.emitSave()
                        }
                    }
                }
            }

            // ══════════════════════════════════════════════════════════════════
            // 4. SECTION: UPDATES
            // ══════════════════════════════════════════════════════════════════
            Rectangle {
                width: parent.width
                implicitHeight: updSecCol.implicitHeight + 36
                radius: 14
                color: Theme.cardBg
                border.color: Theme.border
                border.width: 1

                Column {
                    id: updSecCol
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 16

                    Column {
                        spacing: 2
                        Text {
                            text: tr("settings_section_updates")
                            color: Theme.textPrimary
                            font.pixelSize: 15
                            font.bold: true
                            font.family: Theme.fontFamily
                        }
                        Text {
                            text: tr("settings_updates_desc")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.family: Theme.fontFamily
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: Theme.border }

                    // Check Interval Row
                    Item {
                        width: parent.width
                        height: 44

                        Column {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 3
                            Text {
                                text: tr("settings_auto_check_interval")
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                font.bold: true
                                font.family: Theme.fontFamily
                            }
                        }

                        ComboBox {
                            id: intervalCombo
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            width: 220
                            height: 36
                            model: [
                                { val: 0, text: tr("interval_disabled") },
                                { val: 1, text: tr("interval_1h") },
                                { val: 4, text: tr("interval_4h") },
                                { val: 12, text: tr("interval_12h") },
                                { val: 24, text: tr("interval_24h") }
                            ]
                            textRole: "text"
                            currentIndex: {
                                for (var i = 0; i < model.length; i++) {
                                    if (model[i].val === root.checkInterval) return i;
                                }
                                return 2;
                            }
                            onActivated: root.emitSave()
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: Theme.border }

                    // Auto Install Setting Row
                    Item {
                        width: parent.width
                        height: 44

                        Column {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 3
                            Text {
                                text: tr("settings_auto_install_updates")
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                font.bold: true
                                font.family: Theme.fontFamily
                            }
                            Text {
                                text: tr("settings_auto_install_updates_desc")
                                color: Theme.textSecondary
                                font.pixelSize: 11
                                font.family: Theme.fontFamily
                            }
                        }

                        CheckBox {
                            id: chkAutoInstall
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            checked: root.autoInstall
                            onToggled: root.emitSave()
                        }
                    }
                }
            }

            // ══════════════════════════════════════════════════════════════════
            // 5. SECTION: LANGUAGE
            // ══════════════════════════════════════════════════════════════════
            Rectangle {
                width: parent.width
                implicitHeight: langSecCol.implicitHeight + 36
                radius: 14
                color: Theme.cardBg
                border.color: Theme.border
                border.width: 1

                Column {
                    id: langSecCol
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 16

                    Column {
                        spacing: 2
                        Text {
                            text: tr("settings_section_language")
                            color: Theme.textPrimary
                            font.pixelSize: 15
                            font.bold: true
                            font.family: Theme.fontFamily
                        }
                        Text {
                            text: tr("settings_language_desc")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.family: Theme.fontFamily
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: Theme.border }

                    Item {
                        width: parent.width
                        height: 44

                        Column {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 3
                            Text {
                                text: tr("settings_language_label")
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                font.bold: true
                                font.family: Theme.fontFamily
                            }
                        }

                        ComboBox {
                            id: langCombo
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            width: 220
                            height: 36
                            model: [
                                { val: "tr", text: "Türkçe (TR)" },
                                { val: "en", text: "English (EN)" }
                            ]
                            textRole: "text"
                            currentIndex: root.currentLanguage === "en" ? 1 : 0
                            onActivated: root.emitSave()
                        }
                    }
                }
            }
        }
    }
}
