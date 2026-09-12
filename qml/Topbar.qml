import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Rectangle {
    id: root

    property bool canGoBack: false
    property alias searchText: searchInput.text
    property var recentSearches: []

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal backClicked()
    signal searchTriggered(string query)
    signal searchCleared()
    signal clearHistory()
    signal deleteSearch(string query)

    height: 56
    color: Theme.bg

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: Theme.border
    }

    Row {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 14
        anchors.verticalCenter: parent.verticalCenter

        // ── Back Button ──
        Rectangle {
            id: backBtn
            width: 32
            height: 32
            radius: 16
            color: backMouse.containsMouse ? Theme.border : "transparent"
            visible: root.canGoBack
            anchors.verticalCenter: parent.verticalCenter

            Image {
                anchors.centerIn: parent
                source: "qrc:/qml/assets/icons/go-previous.svg"
                width: 18
                height: 18
            }

            MouseArea {
                id: backMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.backClicked()
            }
        }

        // ── Search Wrap ──
        Item {
            id: searchWrap
            width: Math.min(480, root.width - (root.canGoBack ? 120 : 80))
            height: 36
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                anchors.fill: parent
                radius: 18
                color: Theme.sidebarBg
                border.color: searchInput.activeFocus ? Theme.accentTeal : Theme.border
                border.width: 1

                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 10
                    spacing: 8
                    anchors.verticalCenter: parent.verticalCenter

                    Image {
                        source: "qrc:/qml/assets/icons/edit-find.svg"
                        width: 16
                        height: 16
                        opacity: 0.6
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    TextInput {
                        id: searchInput
                        width: parent.width - 24 - (clearBtn.visible ? 28 : 0)
                        height: parent.height
                        verticalAlignment: TextInput.AlignVCenter
                        color: Theme.textPrimary
                        font.pixelSize: 13
                        font.family: Theme.fontFamily
                        selectByMouse: true
                        clip: true

                        Text {
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            visible: !searchInput.text && !searchInput.inputMethodComposing
                            text: tr("search_placeholder")
                            color: Theme.textSecondary
                            font.pixelSize: 13
                            font.family: Theme.fontFamily
                        }

                        onTextChanged: {
                            searchTimer.restart()
                        }

                        onAccepted: {
                            searchTimer.stop()
                            suggestionsPopup.close()
                            root.searchTriggered(searchInput.text)
                        }

                        onActiveFocusChanged: {
                            if (activeFocus && !searchInput.text.trim()) {
                                suggestionsPopup.open()
                            }
                        }
                    }

                    Rectangle {
                        id: clearBtn
                        visible: searchInput.text.length > 0
                        width: 20
                        height: 20
                        radius: 10
                        color: clearMouse.containsMouse ? "#33ffffff" : "#14ffffff"
                        anchors.verticalCenter: parent.verticalCenter

                        Image {
                            anchors.centerIn: parent
                            source: "qrc:/qml/assets/icons/window-close.svg"
                            width: 12
                            height: 12
                            opacity: 0.8
                        }

                        MouseArea {
                            id: clearMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                searchInput.text = ""
                                searchInput.forceActiveFocus()
                                root.searchCleared()
                                suggestionsPopup.close()
                            }
                        }
                    }
                }
            }

            Timer {
                id: searchTimer
                interval: 250
                repeat: false
                onTriggered: {
                    if (searchInput.text.trim().length > 0) {
                        suggestionsPopup.close()
                        root.searchTriggered(searchInput.text.trim())
                    } else {
                        root.searchCleared()
                    }
                }
            }

            // Suggestions Popover
            Popup {
                id: suggestionsPopup
                y: searchWrap.height + 8
                width: searchWrap.width
                padding: 0
                background: Item {}
                closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                SearchSuggestions {
                    width: parent.width
                    recentSearches: root.recentSearches
                    onSearchSelected: function(query) {
                        searchInput.text = query
                        suggestionsPopup.close()
                        root.searchTriggered(query)
                    }
                    onDeleteSearch: function(query) {
                        root.deleteSearch(query)
                    }
                    onClearHistory: {
                        root.clearHistory()
                    }
                }
            }
        }
    }

    function focusSearch() {
        searchInput.forceActiveFocus()
        searchInput.selectAll()
    }
}
