import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Item {
    id: root

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    Column {
        anchors.centerIn: parent
        width: Math.min(540, parent.width - 56)
        spacing: 16

        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            source: "qrc:/qml/assets/lupus-software-center.png"
            width: 96
            height: 96
            fillMode: Image.PreserveAspectFit
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: tr("about_app_name")
            color: Theme.textPrimary
            font.pixelSize: 26
            font.bold: true
            font.family: Theme.fontFamily
            horizontalAlignment: Text.AlignHCenter
        }

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            height: 26
            width: verText.implicitWidth + 32
            radius: 12
            color: Theme.accentTeal

            Text {
                id: verText
                anchors.centerIn: parent
                text: tr("about_version")
                color: "#ffffff"
                font.pixelSize: 13
                font.bold: true
                font.family: Theme.fontFamily
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: tr("about_description")
            color: Theme.textSecondary
            font.pixelSize: 14
            font.family: Theme.fontFamily
            horizontalAlignment: Text.AlignHCenter
            width: parent.width
            wrapMode: Text.WordWrap
        }

        Rectangle {
            width: parent.width
            height: cardCol.implicitHeight + 40
            radius: 14
            color: Theme.sidebarBg
            border.color: Theme.border
            border.width: 1

            Column {
                id: cardCol
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                Text {
                    text: tr("about_developer")
                    color: Theme.textPrimary
                    font.pixelSize: 14
                    font.bold: true
                    font.family: Theme.fontFamily
                }

                Text {
                    text: "www.antolun.com"
                    color: Theme.accentTeal
                    font.pixelSize: 14
                    font.bold: true
                    font.family: Theme.fontFamily

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Qt.openUrlExternally("https://www.antolun.com/")
                    }
                }

                Text {
                    text: tr("about_license")
                    color: Theme.textSecondary
                    font.pixelSize: 13
                    font.family: Theme.fontFamily
                }
            }
        }
    }
}
