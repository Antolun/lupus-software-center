import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Rectangle {
    id: root

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    property string message: tr("loading_init")
    property real progress: 0.2
    property bool isLoading: true

    color: Theme.bg
    visible: opacity > 0
    opacity: isLoading ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 300 } }

    MouseArea {
        anchors.fill: parent
        // blocks input while loading
    }

    Column {
        anchors.centerIn: parent
        spacing: 20

        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            source: "qrc:/qml/assets/lupus-software-center.png"
            width: 72
            height: 72
            fillMode: Image.PreserveAspectFit
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: tr("loading_app_title")
            color: Theme.textPrimary
            font.pixelSize: 22
            font.bold: true
            font.family: Theme.fontFamily
        }

        // Circular Spinner
        Rectangle {
            id: spinner
            anchors.horizontalCenter: parent.horizontalCenter
            width: 32
            height: 32
            radius: 16
            color: "transparent"
            border.color: Theme.border
            border.width: 3

            Rectangle {
                width: 10
                height: 10
                radius: 5
                color: Theme.accentTeal
                anchors.top: parent.top
                anchors.horizontalCenter: parent.horizontalCenter
            }

            RotationAnimation on rotation {
                loops: Animation.Infinite
                from: 0
                to: 360
                duration: 800
            }
        }

        // Progress Bar
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 320
            height: 6
            radius: 3
            color: Theme.border
            clip: true

            Rectangle {
                height: parent.height
                radius: 3
                color: Theme.accentTeal
                width: parent.width * Math.min(Math.max(root.progress, 0.0), 1.0)
                Behavior on width { NumberAnimation { duration: 300 } }
            }
        }

        // Status message
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.message
            color: Theme.textSecondary
            font.pixelSize: 13
            font.family: Theme.fontFamily
        }
    }
}
