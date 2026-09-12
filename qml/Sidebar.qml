import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Rectangle {
    id: root

    property string currentCategory: "all"
    property var categoriesList: []
    property int updatesCount: 0

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal categorySelected(string catId)

    width: 220
    color: Theme.sidebarBg

    Rectangle {
        anchors.right: parent.right
        width: 1
        height: parent.height
        color: Theme.border
    }

    // ── 1. Header ──
    Rectangle {
        id: headerArea
        anchors.top: parent.top
        width: parent.width
        height: 56
        color: Theme.sidebarBg
        z: 2

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1
            color: Theme.border
        }

        Row {
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 14
            spacing: 10
            anchors.verticalCenter: parent.verticalCenter

            Image {
                source: "qrc:/qml/assets/lupus-software-center.png"
                width: 30
                height: 30
                fillMode: Image.PreserveAspectFit
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: tr("software_center")
                color: Theme.textPrimary
                font.pixelSize: 16
                font.bold: true
                font.family: Theme.fontFamily
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    // ── 2. Bottom Section (Updates, Settings, About) ──
    Column {
        id: bottomArea
        anchors.bottom: parent.bottom
        width: parent.width
        padding: 10
        spacing: 2
        z: 2

        // Downloads / Updates Button
        Rectangle {
            width: parent.width - 20
            height: 38
            radius: 10
            readonly property bool isActive: root.currentCategory === "updates"
            color: (updMouse.containsMouse || isActive) ? Theme.border : "transparent"

            Row {
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.right: badgeRect.left
                anchors.rightMargin: 8
                spacing: 10
                anchors.verticalCenter: parent.verticalCenter

                Image {
                    source: "qrc:/qml/assets/icons/download.svg"
                    width: 22
                    height: 22
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: tr("nav_downloads")
                    color: Theme.textPrimary
                    font.pixelSize: 13
                    font.bold: root.currentCategory === "updates"
                    font.family: Theme.fontFamily
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Counter Badge
            Rectangle {
                id: badgeRect
                visible: root.updatesCount > 0
                width: visible ? Math.max(20, badgeText.implicitWidth + 12) : 0
                height: 18
                radius: 9
                color: Theme.accentTeal
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: 12

                Text {
                    id: badgeText
                    anchors.centerIn: parent
                    text: root.updatesCount.toString()
                    color: "#ffffff"
                    font.pixelSize: 11
                    font.bold: true
                    font.family: Theme.fontFamily
                }
            }

            MouseArea {
                id: updMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.categorySelected("updates")
            }
        }

        // Settings Button
        Rectangle {
            width: parent.width - 20
            height: 38
            radius: 10
            readonly property bool isActive: root.currentCategory === "settings"
            color: (setMouse.containsMouse || isActive) ? Theme.border : "transparent"

            Row {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 10
                anchors.verticalCenter: parent.verticalCenter

                Image {
                    source: "qrc:/qml/assets/icons/settings-configure.svg"
                    width: 22
                    height: 22
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: tr("nav_settings")
                    color: Theme.textPrimary
                    font.pixelSize: 13
                    font.bold: root.currentCategory === "settings"
                    font.family: Theme.fontFamily
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            MouseArea {
                id: setMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.categorySelected("settings")
            }
        }

        // About Button
        Rectangle {
            width: parent.width - 20
            height: 38
            radius: 10
            readonly property bool isActive: root.currentCategory === "about"
            color: (abtMouse.containsMouse || isActive) ? Theme.border : "transparent"

            Row {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 10
                anchors.verticalCenter: parent.verticalCenter

                Image {
                    source: "qrc:/qml/assets/icons/help-about.svg"
                    width: 22
                    height: 22
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: tr("nav_about")
                    color: Theme.textPrimary
                    font.pixelSize: 13
                    font.bold: root.currentCategory === "about"
                    font.family: Theme.fontFamily
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            MouseArea {
                id: abtMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.categorySelected("about")
            }
        }
    }

    // ── 3. Bottom Divider ──
    Rectangle {
        id: bottomDivider
        anchors.bottom: bottomArea.top
        width: parent.width
        height: 1
        color: Theme.border
    }

    // ── 4. Scrollable Categories ──
    ScrollView {
        id: categoriesScroll
        anchors.top: headerArea.bottom
        anchors.bottom: bottomDivider.top
        anchors.left: parent.left
        anchors.right: parent.right
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        Column {
            width: categoriesScroll.width
            padding: 10
            spacing: 2

            Repeater {
                model: root.categoriesList

                delegate: Rectangle {
                    id: catBtn
                    width: parent.width - 20
                    height: 38
                    radius: 10
                    readonly property bool isActive: root.currentCategory === modelData.id
                    color: (catMouse.containsMouse || isActive) ? Theme.border : "transparent"

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10
                        anchors.verticalCenter: parent.verticalCenter

                        Image {
                            source: "qrc:/qml/assets/icons/" + (modelData.icon || "plasma-search") + ".svg"
                            width: 22
                            height: 22
                            fillMode: Image.PreserveAspectFit
                            anchors.verticalCenter: parent.verticalCenter
                            scale: catBtn.isActive ? 1.1 : (catMouse.containsMouse ? 1.08 : 1.0)
                            Behavior on scale { NumberAnimation { duration: 150 } }
                        }

                        Text {
                            text: {
                                var key = (modelData.id === "all") ? "nav_discover" : ("nav_" + modelData.id)
                                var loc = tr(key)
                                var label = (loc && loc !== key) ? loc : modelData.name
                                return label + (modelData.count !== undefined ? (" (" + modelData.count + ")") : "")
                            }
                            color: Theme.textPrimary
                            font.pixelSize: 13
                            font.bold: catBtn.isActive
                            font.family: Theme.fontFamily
                            elide: Text.ElideRight
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - 32
                        }
                    }

                    MouseArea {
                        id: catMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.categorySelected(modelData.id)
                    }
                }
            }
        }
    }
}
