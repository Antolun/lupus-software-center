import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Item {
    id: root

    property string categoryId: "all"
    property string categoryName: ""
    property string categoryIcon: "applications-utilities"
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

        header: Column {
            width: gridView.width
            spacing: 14
            bottomPadding: 10

            Row {
                spacing: 12
                anchors.left: parent.left
                anchors.leftMargin: 7

                Image {
                    source: "qrc:/qml/assets/icons/" + root.categoryIcon + ".svg"
                    width: 28
                    height: 28
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: tr("nav_" + root.categoryId) !== ("nav_" + root.categoryId) ? tr("nav_" + root.categoryId) : root.categoryName
                    color: Theme.textPrimary
                    font.pixelSize: 22
                    font.bold: true
                    font.family: Theme.fontFamily
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 7
                text: tr("all_applications")
                color: Theme.textPrimary
                font.pixelSize: 16
                font.bold: true
                font.family: Theme.fontFamily
            }

            Item {
                visible: root.packagesList.length === 0
                width: parent.width
                height: 100

                Text {
                    anchors.centerIn: parent
                    text: tr("no_packages_in_category")
                    color: Theme.textSecondary
                    font.pixelSize: 14
                    font.family: Theme.fontFamily
                }
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
