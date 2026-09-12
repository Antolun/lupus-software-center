import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Rectangle {
    id: root

    property string imageSource: ""
    property real currentScale: 1.0

    signal closed()

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    color: "#d9000000"
    visible: imageSource.length > 0

    MouseArea {
        anchors.fill: parent
        onClicked: root.closed()
    }

    Rectangle {
        width: parent.width * 0.9
        height: parent.height * 0.9
        anchors.centerIn: parent
        radius: 12
        color: Theme.bg
        border.color: Theme.border
        border.width: 1

        MouseArea {
            anchors.fill: parent
            // Prevent closing when clicking modal content
        }

        Column {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            // Toolbar
            Item {
                width: parent.width
                height: 32

                Row {
                    anchors.left: parent.left
                    spacing: 8

                    // Zoom in
                    Rectangle {
                        width: btnZInRow.implicitWidth + 24
                        height: 32
                        radius: 8
                        color: mIn.containsMouse ? Theme.cardHover : Theme.cardBg
                        border.color: Theme.border
                        border.width: 1

                        Row {
                            id: btnZInRow
                            anchors.centerIn: parent
                            spacing: 6
                            Image { source: "qrc:/qml/assets/icons/zoom-in.svg"; width: 16; height: 16; anchors.verticalCenter: parent.verticalCenter }
                            Text { text: tr("zoom_in"); color: Theme.textPrimary; font.pixelSize: 12; font.family: Theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                        }
                        MouseArea {
                            id: mIn
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.currentScale = Math.min(root.currentScale * 1.25, 4.0)
                        }
                    }

                    // Zoom out
                    Rectangle {
                        width: btnZOutRow.implicitWidth + 24
                        height: 32
                        radius: 8
                        color: mOut.containsMouse ? Theme.cardHover : Theme.cardBg
                        border.color: Theme.border
                        border.width: 1

                        Row {
                            id: btnZOutRow
                            anchors.centerIn: parent
                            spacing: 6
                            Image { source: "qrc:/qml/assets/icons/zoom-out.svg"; width: 16; height: 16; anchors.verticalCenter: parent.verticalCenter }
                            Text { text: tr("zoom_out"); color: Theme.textPrimary; font.pixelSize: 12; font.family: Theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                        }
                        MouseArea {
                            id: mOut
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.currentScale = Math.max(root.currentScale / 1.25, 0.4)
                        }
                    }

                    // Reset
                    Rectangle {
                        width: btnZResRow.implicitWidth + 24
                        height: 32
                        radius: 8
                        color: mRes.containsMouse ? Theme.cardHover : Theme.cardBg
                        border.color: Theme.border
                        border.width: 1

                        Row {
                            id: btnZResRow
                            anchors.centerIn: parent
                            spacing: 6
                            Image { source: "qrc:/qml/assets/icons/zoom-original.svg"; width: 16; height: 16; anchors.verticalCenter: parent.verticalCenter }
                            Text { text: tr("reset"); color: Theme.textPrimary; font.pixelSize: 12; font.family: Theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                        }
                        MouseArea {
                            id: mRes
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.currentScale = 1.0
                        }
                    }
                }

                // Close
                Rectangle {
                    anchors.right: parent.right
                    width: btnZCloseRow.implicitWidth + 24
                    height: 32
                    radius: 8
                    color: mClose.containsMouse ? Theme.cardHover : Theme.cardBg
                    border.color: Theme.border
                    border.width: 1

                    Row {
                        id: btnZCloseRow
                        anchors.centerIn: parent
                        spacing: 6
                        Image { source: "qrc:/qml/assets/icons/window-close.svg"; width: 16; height: 16; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: tr("close"); color: Theme.textPrimary; font.pixelSize: 12; font.family: Theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                    }
                    MouseArea {
                        id: mClose
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.closed()
                    }
                }
            }

            // Image Area
            Item {
                width: parent.width
                height: parent.height - 44
                clip: true

                Image {
                    id: targetImg
                    anchors.centerIn: parent
                    source: root.imageSource
                    fillMode: Image.PreserveAspectFit
                    scale: root.currentScale
                    Behavior on scale { NumberAnimation { duration: 150 } }
                }
            }
        }
    }
}
