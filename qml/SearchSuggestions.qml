import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Rectangle {
    id: root

    property var recentSearches: []

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal searchSelected(string query)
    signal deleteSearch(string query)
    signal clearHistory()

    width: 480
    height: contentCol.implicitHeight + 24
    radius: 12
    color: Theme.sidebarBg
    border.color: Theme.border
    border.width: 1

    Column {
        id: contentCol
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        // Recent searches section
        Column {
            width: parent.width
            spacing: 8
            visible: root.recentSearches && root.recentSearches.length > 0

            Item {
                width: parent.width
                height: recentText.implicitHeight

                Text {
                    id: recentText
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: tr("recent_searches")
                    font.pixelSize: 11
                    font.bold: true
                    font.family: Theme.fontFamily
                    color: Theme.textSecondary
                }

                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: tr("clear_history")
                    font.pixelSize: 11
                    font.bold: true
                    font.family: Theme.fontFamily
                    color: Theme.accentTeal
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.clearHistory()
                    }
                }
            }

            Repeater {
                model: root.recentSearches

                delegate: Rectangle {
                    width: parent.width
                    height: 28
                    radius: 8
                    color: itemMouse.containsMouse ? Theme.cardBg : "transparent"

                    Row {
                        anchors.left: parent.left
                        anchors.right: delText.left
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 8

                        Image {
                            source: "qrc:/qml/assets/icons/plasma-search.svg"
                            width: 14
                            height: 14
                            opacity: 0.5
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: modelData
                            color: Theme.textPrimary
                            font.pixelSize: 13
                            font.family: Theme.fontFamily
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - 24
                            elide: Text.ElideRight
                        }
                    }

                    Text {
                        id: delText
                        text: "✕"
                        color: delMouse.containsMouse ? Theme.dangerRed : Theme.textSecondary
                        font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        z: 2

                        MouseArea {
                            id: delMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.deleteSearch(modelData)
                        }
                    }

                    MouseArea {
                        id: itemMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.searchSelected(modelData)
                    }
                }
            }
        }

        // Popular Searches section
        Column {
            width: parent.width
            spacing: 8

            Text {
                text: tr("quick_filters")
                font.pixelSize: 11
                font.bold: true
                font.family: Theme.fontFamily
                color: Theme.textSecondary
            }

            Flow {
                width: parent.width
                spacing: 6

                Repeater {
                    model: ["geliştirme", "tarayıcı", "multimedya", "oyun", "grafik", "ofis"]

                    delegate: Rectangle {
                        height: 26
                        width: tagText.implicitWidth + 20
                        radius: 12
                        color: tagMouse.containsMouse ? Theme.cardHover : Theme.cardBg
                        border.color: tagMouse.containsMouse ? Theme.accentTeal : Theme.border
                        border.width: 1

                        Text {
                            id: tagText
                            anchors.centerIn: parent
                            text: {
                                var map = {
                                    "geliştirme": tr("nav_development"),
                                    "tarayıcı": tr("nav_internet"),
                                    "multimedya": tr("nav_multimedia"),
                                    "oyun": tr("nav_games"),
                                    "grafik": tr("nav_graphics"),
                                    "ofis": tr("nav_office")
                                }
                                return map[modelData] || modelData
                            }
                            font.pixelSize: 12
                            font.bold: true
                            font.family: Theme.fontFamily
                            color: tagMouse.containsMouse ? Theme.accentTeal : Theme.textPrimary
                        }

                        MouseArea {
                            id: tagMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.searchSelected(modelData)
                        }
                    }
                }
            }
        }
    }
}
