import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Rectangle {
    id: root

    property var pkgData: null
    property int rank: 0
    property bool showDelete: true
    property var activeWorkersMap: typeof mainWindow !== "undefined" ? mainWindow.activeWorkersMap : ({})

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal clicked(var pkg)
    signal installClicked(string pkgName)
    signal removeClicked(string pkgName)
    signal cancelClicked(string pkgName)

    height: 72
    radius: 12
    color: cardMouse.containsMouse ? Theme.cardHover : Theme.cardBg
    border.color: Theme.border
    border.width: 1

    Behavior on color { ColorAnimation { duration: 150 } }

    MouseArea {
        id: cardMouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            if (root.pkgData) {
                root.clicked(root.pkgData)
            }
        }
    }

    Row {
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 14
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        spacing: 12

        // Optional rank
        Text {
            visible: root.rank > 0
            text: root.rank.toString()
            anchors.verticalCenter: parent.verticalCenter
            width: 20
            color: Theme.textSecondary
            font.pixelSize: 14
            font.bold: true
            font.family: Theme.fontFamily
        }

        // App Icon
        Rectangle {
            id: iconWrapper
            width: 48
            height: 48
            radius: 8
            color: "transparent"
            clip: true
            anchors.verticalCenter: parent.verticalCenter

            Image {
                id: iconImg
                anchors.fill: parent
                fillMode: Image.PreserveAspectFit
                sourceSize.width: 96
                sourceSize.height: 96
                asynchronous: true
                cache: true

                readonly property string defaultIcon: (root.pkgData && root.pkgData.is_flatpak)
                    ? "qrc:/qml/assets/icons/package-x-generic.svg"
                    : "qrc:/qml/assets/luppo.png"

                source: {
                    if (!root.pkgData) return "qrc:/qml/assets/luppo.png"
                    var ip = root.pkgData.icon_path || ""
                    if (ip.length > 0) {
                        if (ip[0] === "/") return "file://" + ip
                        return ip
                    }
                    return defaultIcon
                }

                onStatusChanged: {
                    if (status === Image.Error && source !== defaultIcon) {
                        source = defaultIcon
                    }
                }
            }
        }

        // App Info (Title & Summary)
        Column {
            id: infoCol
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - (root.rank > 0 ? 32 : 0) - iconWrapper.width - actionWidget.width - 36
            spacing: 3

            Row {
                width: parent.width
                spacing: 6

                Text {
                    id: nameText
                    text: {
                        if (!root.pkgData) return ""
                        if (root.pkgData.display_name && root.pkgData.display_name.length > 0) return root.pkgData.display_name
                        var n = root.pkgData.name || ""
                        return n.split("-").map(function(w) { return w.charAt(0).toUpperCase() + w.slice(1); }).join(" ")
                    }
                    color: Theme.textPrimary
                    font.pixelSize: 13
                    font.bold: true
                    font.family: Theme.fontFamily
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    width: Math.min(implicitWidth, parent.width - (flatpakBadge.visible ? flatpakBadge.width + 6 : 0))
                }

                Rectangle {
                    id: flatpakBadge
                    visible: root.pkgData && root.pkgData.is_flatpak
                    color: Theme.flatpakBadgeBg
                    radius: 4
                    height: 16
                    width: badgeText.implicitWidth + 12
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                        id: badgeText
                        anchors.centerIn: parent
                        text: (root.pkgData && root.pkgData.origin) ? root.pkgData.origin : "Flatpak"
                        color: "#ffffff"
                        font.pixelSize: 9
                        font.bold: true
                        font.family: Theme.fontFamily
                    }
                }
            }

            Text {
                id: summaryText
                width: parent.width
                text: {
                    if (!root.pkgData) return ""
                    return root.pkgData.summary || root.pkgData.category || tr("app_fallback")
                }
                color: Theme.textSecondary
                font.pixelSize: 11
                font.family: Theme.fontFamily
                elide: Text.ElideRight
                maximumLineCount: 1
            }
        }

        // Right Action Widget
        Item {
            id: actionWidget
            width: {
                if (isWorking) return 130
                if (!root.pkgData || !root.pkgData.installed || root.pkgData.has_update) return 96
                return root.showDelete ? 34 : 60
            }
            height: 34
            anchors.verticalCenter: parent.verticalCenter

            readonly property bool isWorking: root.pkgData && activeWorkersMap[root.pkgData.name] !== undefined
            readonly property var workerInfo: isWorking ? activeWorkersMap[root.pkgData.name] : null

            // 1. Progress State
            Column {
                visible: actionWidget.isWorking
                anchors.centerIn: parent
                width: parent.width
                spacing: 3

                Rectangle {
                    width: parent.width
                    height: 6
                    radius: 3
                    color: Theme.border
                    clip: true

                    Rectangle {
                        height: parent.height
                        radius: 3
                        color: Theme.accentTeal
                        width: parent.width * (actionWidget.workerInfo ? (actionWidget.workerInfo.progress / 100.0) : 0.0)
                        Behavior on width { NumberAnimation { duration: 200 } }
                    }
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: tr("btn_cancel")
                    font.pixelSize: 10
                    font.bold: true
                    font.family: Theme.fontFamily
                    color: cancelMouse.containsMouse ? Theme.dangerRed : Theme.textSecondary

                    MouseArea {
                        id: cancelMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (root.pkgData) root.cancelClicked(root.pkgData.name)
                        }
                    }
                }
            }

            // 2. Install Button (Not installed)
            Rectangle {
                visible: !actionWidget.isWorking && root.pkgData && !root.pkgData.installed
                anchors.fill: parent
                radius: 10
                color: installMouse.containsMouse ? Theme.border : Theme.updateBtnBg

                Row {
                    anchors.centerIn: parent
                    spacing: 6
                    Image {
                        source: "qrc:/qml/assets/icons/download.svg"
                        width: 14
                        height: 14
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: tr("btn_install")
                        color: "#ffffff"
                        font.pixelSize: 12
                        font.bold: true
                        font.family: Theme.fontFamily
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: installMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (root.pkgData) root.installClicked(root.pkgData.name)
                    }
                }
            }

            // 3. Update Button (Installed with update)
            Rectangle {
                visible: !actionWidget.isWorking && root.pkgData && root.pkgData.installed && root.pkgData.has_update
                anchors.fill: parent
                radius: 10
                color: updateMouse.containsMouse ? Theme.border : Theme.updateBtnBg

                Row {
                    anchors.centerIn: parent
                    spacing: 6
                    Image {
                        source: "qrc:/qml/assets/icons/view-refresh.svg"
                        width: 14
                        height: 14
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: tr("btn_update")
                        color: Theme.updateBtnText
                        font.pixelSize: 12
                        font.bold: true
                        font.family: Theme.fontFamily
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: updateMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (root.pkgData) root.installClicked(root.pkgData.name)
                    }
                }
            }

            // 4. Delete / Uninstall Button (Installed without update)
            Rectangle {
                visible: !actionWidget.isWorking && root.pkgData && root.pkgData.installed && !root.pkgData.has_update && root.showDelete
                anchors.fill: parent
                color: "transparent"
                radius: 8

                Image {
                    anchors.centerIn: parent
                    source: "qrc:/qml/assets/icons/edit-delete.svg"
                    width: 18
                    height: 18
                    opacity: deleteMouse.containsMouse ? 1.0 : 0.7
                }

                MouseArea {
                    id: deleteMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (root.pkgData) root.removeClicked(root.pkgData.name)
                    }
                }
            }

            // 5. Installed Label (When showDelete is false)
            Text {
                visible: !actionWidget.isWorking && root.pkgData && root.pkgData.installed && !root.pkgData.has_update && !root.showDelete
                anchors.centerIn: parent
                text: tr("installed_label")
                color: Theme.accentTeal
                font.pixelSize: 11
                font.bold: true
                font.family: Theme.fontFamily
            }
        }
    }
}
