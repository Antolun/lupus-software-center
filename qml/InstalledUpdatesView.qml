import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Item {
    id: root

    property var updatesList: []
    property var installedList: []
    property var downloadsList: []
    property var activeWorkersMap: ({})
    property bool isCheckingUpdates: false

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal appClicked(var pkg)
    signal installClicked(string pkgName)
    signal removeClicked(string pkgName)
    signal cancelClicked(string pkgName)
    signal checkUpdatesClicked()

    GridView {
        id: gridView
        anchors.fill: parent
        anchors.leftMargin: 21
        anchors.rightMargin: 21
        anchors.topMargin: 16
        anchors.bottomMargin: 16
        clip: true

        cellWidth: width > 900 ? width / 2 : width
        cellHeight: 86

        header: Column {
            width: gridView.width
            spacing: 16
            bottomPadding: 10

            // ── Header Row ──
            Item {
                width: parent.width
                height: 36

                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 7
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 12

                    Image {
                        source: "qrc:/qml/assets/icons/download.svg"
                        width: 28
                        height: 28
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: tr("updates_title")
                        color: Theme.textPrimary
                        font.pixelSize: 22
                        font.bold: true
                        font.family: Theme.fontFamily
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Rectangle {
                    anchors.right: parent.right
                    anchors.rightMargin: 7
                    anchors.verticalCenter: parent.verticalCenter
                    width: checkRow.implicitWidth + 28
                    height: 34
                    radius: 10
                    color: checkMouse.containsMouse ? Theme.border : Theme.updateBtnBg

                    Row {
                        id: checkRow
                        anchors.centerIn: parent
                        spacing: 6

                        Image {
                            source: "qrc:/qml/assets/icons/view-refresh.svg"
                            width: 16
                            height: 16
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: root.isCheckingUpdates ? tr("checking_updates") : tr("btn_check_updates")
                            color: "#ffffff"
                            font.pixelSize: 12
                            font.bold: true
                            font.family: Theme.fontFamily
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }

                    MouseArea {
                        id: checkMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !root.isCheckingUpdates
                        onClicked: root.checkUpdatesClicked()
                    }
                }
            }

            // ── Active Downloads Section ──
            Column {
                visible: root.downloadsList.length > 0
                width: parent.width
                spacing: 10

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 7
                    text: tr("nav_downloads") + " (" + root.downloadsList.length + ")"
                    color: Theme.accentTeal
                    font.pixelSize: 15
                    font.bold: true
                    font.family: Theme.fontFamily
                }

                Repeater {
                    model: root.downloadsList
                    delegate: Item {
                        width: parent.width
                        height: 72
                        AppCard {
                            anchors.fill: parent
                            anchors.margins: 7
                            pkgData: modelData
                            activeWorkersMap: root.activeWorkersMap
                            showDelete: false
                            onClicked: function(p) { root.appClicked(p) }
                            onInstallClicked: function(name) { root.installClicked(name) }
                            onRemoveClicked: function(name) { root.removeClicked(name) }
                            onCancelClicked: function(name) { root.cancelClicked(name) }
                        }
                    }
                }

                Rectangle {
                    width: parent.width - 14
                    anchors.horizontalCenter: parent.horizontalCenter
                    height: 1
                    color: Theme.border
                }
            }

            // ── Updates Subtitle ──
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 7
                text: tr("downloads_and_updates").replace("{count}", root.updatesList.length.toString())
                color: Theme.textPrimary
                font.pixelSize: 16
                font.bold: true
                font.family: Theme.fontFamily
            }

            // ── Updates Empty Message ──
            Item {
                visible: root.updatesList.length === 0
                width: parent.width
                height: 30

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 7
                    anchors.verticalCenter: parent.verticalCenter
                    text: tr("no_updates_installed")
                    color: Theme.textSecondary
                    font.pixelSize: 13
                    font.family: Theme.fontFamily
                }
            }

            // ── Updates Grid (if any) ──
            Grid {
                visible: root.updatesList.length > 0
                width: parent.width
                columns: parent.width > 900 ? 2 : 1
                spacing: 14

                Repeater {
                    model: root.updatesList

                    delegate: Item {
                        width: parent.columns > 1 ? (parent.width - 14) / 2 : parent.width
                        height: 72

                        AppCard {
                            anchors.fill: parent
                            pkgData: modelData
                            showDelete: true
                            onClicked: function(p) { root.appClicked(p) }
                            onInstallClicked: function(name) { root.installClicked(name) }
                            onRemoveClicked: function(name) { root.removeClicked(name) }
                            onCancelClicked: function(name) { root.cancelClicked(name) }
                        }
                    }
                }
            }

            // ── Divider Line ──
            Rectangle {
                width: parent.width - 14
                anchors.horizontalCenter: parent.horizontalCenter
                height: 1
                color: Theme.border
            }

            // ── Installed Section Header ──
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 7
                text: tr("all_applications")
                color: Theme.textPrimary
                font.pixelSize: 16
                font.bold: true
                font.family: Theme.fontFamily
            }
        }

        // Virtualized Installed List
        model: root.installedList

        delegate: Item {
            width: gridView.cellWidth
            height: gridView.cellHeight

            AppCard {
                anchors.fill: parent
                anchors.margins: 7
                pkgData: modelData
                showDelete: true
                onClicked: function(p) { root.appClicked(p) }
                onInstallClicked: function(name) { root.installClicked(name) }
                onRemoveClicked: function(name) { root.removeClicked(name) }
                onCancelClicked: function(name) { root.cancelClicked(name) }
            }
        }

        ScrollBar.vertical: ScrollBar {}
    }
}
