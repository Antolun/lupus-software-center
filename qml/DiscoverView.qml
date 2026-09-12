import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Item {
    id: root

    property var packagesList: []

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal appClicked(var pkg)
    signal installClicked(string pkgName)
    signal removeClicked(string pkgName)
    signal cancelClicked(string pkgName)

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

        header: Item {
            width: gridView.width
            height: 48

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 7
                anchors.verticalCenter: parent.verticalCenter
                text: tr("nav_discover")
                color: Theme.textPrimary
                font.pixelSize: 22
                font.bold: true
                font.family: Theme.fontFamily
            }
        }

        model: root.packagesList

        delegate: Item {
            width: gridView.cellWidth
            height: gridView.cellHeight

            AppCard {
                anchors.fill: parent
                anchors.margins: 7
                pkgData: modelData
                showDelete: false
                onClicked: function(p) { root.appClicked(p) }
                onInstallClicked: function(name) { root.installClicked(name) }
                onRemoveClicked: function(name) { root.removeClicked(name) }
                onCancelClicked: function(name) { root.cancelClicked(name) }
            }
        }

        ScrollBar.vertical: ScrollBar {}
    }
}
