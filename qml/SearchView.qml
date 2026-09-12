import QtQuick
import com.antolun.lupus.software.center 1.0
import QtQuick.Controls

Item {
    id: root

    property string searchQuery: ""
    property var rawResults: []
    property var filteredResults: []

    property string currentType: "all"       // "all", "gui", "lib"
    property string currentCategory: "all"
    property string currentSource: "all"     // "all", "luppo", "flatpak"
    property string currentStatus: "all"     // "all", "installed", "not_installed", "updatable"
    property string currentSort: "relevance" // "relevance", "name_asc", "name_desc", "rating", "downloads"

    property int countAll: 0
    property int countGui: 0
    property int countLib: 0

    onRawResultsChanged: updateFilter()

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal appClicked(var pkg)
    signal installClicked(string pkgName)
    signal removeClicked(string pkgName)
    signal cancelClicked(string pkgName)

    function resetFilters() {
        currentType = "all"
        currentCategory = "all"
        currentSource = "all"
        currentStatus = "all"
        currentSort = "relevance"
        updateFilter()
    }

    function updateFilter() {
        if (!rawResults) {
            filteredResults = []
            return
        }

        var list = rawResults.slice()

        // 1. Category
        if (currentCategory !== "all") {
            list = list.filter(function(p) {
                return p.category && p.category.toLowerCase() === currentCategory.toLowerCase()
            })
        }

        // 2. Source
        if (currentSource === "luppo") {
            list = list.filter(function(p) { return !p.is_flatpak })
        } else if (currentSource === "flatpak") {
            list = list.filter(function(p) { return p.is_flatpak })
        }

        // 3. Status
        if (currentStatus === "installed") {
            list = list.filter(function(p) { return p.installed })
        } else if (currentStatus === "not_installed") {
            list = list.filter(function(p) { return !p.installed })
        } else if (currentStatus === "updatable") {
            list = list.filter(function(p) { return p.has_update })
        }

        countAll = list.length
        countGui = list.filter(function(p) { return p.is_a !== "library" }).length
        countLib = list.filter(function(p) { return p.is_a === "library" }).length

        // 4. Type Tab
        if (currentType === "gui") {
            list = list.filter(function(p) { return p.is_a !== "library" })
        } else if (currentType === "lib") {
            list = list.filter(function(p) { return p.is_a === "library" })
        }

        // 5. Sort
        if (currentSort === "name_asc") {
            list.sort(function(a, b) {
                var na = a.display_name || a.name || ""
                var nb = b.display_name || b.name || ""
                return na.localeCompare(nb)
            })
        } else if (currentSort === "name_desc") {
            list.sort(function(a, b) {
                var na = a.display_name || a.name || ""
                var nb = b.display_name || b.name || ""
                return nb.localeCompare(na)
            })
        } else if (currentSort === "rating") {
            list.sort(function(a, b) { return (b.rating || 0) - (a.rating || 0) })
        } else if (currentSort === "downloads") {
            list.sort(function(a, b) { return (b.downloads || 0) - (a.downloads || 0) })
        }

        filteredResults = list
    }

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
            spacing: 18
            bottomPadding: 16

        // Header
        Item {
            width: parent.width
            height: 38

            Row {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                Image {
                    source: "qrc:/qml/assets/icons/edit-find.svg"
                    width: 28
                    height: 28
                    anchors.verticalCenter: parent.verticalCenter
                }

                Column {
                    spacing: 2
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                        text: tr("results_for").replace("{query}", root.searchQuery)
                        color: Theme.textPrimary
                        font.pixelSize: 22
                        font.bold: true
                        font.family: Theme.fontFamily
                    }

                    Text {
                        text: tr("search_results_count").replace("{count}", root.filteredResults.length.toString())
                        color: Theme.textSecondary
                        font.pixelSize: 12
                        font.family: Theme.fontFamily
                    }
                }
            }

            Rectangle {
                visible: root.currentType !== "all" || root.currentCategory !== "all" || root.currentSource !== "all" || root.currentStatus !== "all" || root.currentSort !== "relevance"
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: resetRow.implicitWidth + 20
                height: 30
                radius: 8
                color: resetMouse.containsMouse ? Theme.accentTeal : "#262ba0b5"
                border.color: "#4d2ba0b5"
                border.width: 1

                Row {
                    id: resetRow
                    anchors.centerIn: parent
                    spacing: 6

                    Image {
                        source: "qrc:/qml/assets/icons/view-refresh.svg"
                        width: 14
                        height: 14
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: tr("clear_filters")
                        color: resetMouse.containsMouse ? "#ffffff" : Theme.accentTeal
                        font.pixelSize: 12
                        font.bold: true
                        font.family: Theme.fontFamily
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: resetMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.resetFilters()
                }
            }
        }

        // Search Filter Bar
        Rectangle {
            width: parent.width
            height: filterCol.implicitHeight + 28
            radius: 14
            color: Theme.sidebarBg
            border.color: Theme.border
            border.width: 1

            Column {
                id: filterCol
                anchors.fill: parent
                anchors.margins: 14
                spacing: 12

                // Type Tabs
                Row {
                    width: parent.width
                    spacing: 8

                    Repeater {
                        model: [
                            { id: "all", label: tr("filter_all_types"), count: root.countAll },
                            { id: "gui", label: tr("filter_apps_only"), count: root.countGui },
                            { id: "lib", label: tr("filter_pkgs_only"), count: root.countLib }
                        ]

                        delegate: Rectangle {
                            id: tabBtn
                            height: 32
                            width: tabRow.implicitWidth + 24
                            radius: 16
                            readonly property bool isActive: root.currentType === modelData.id
                            color: isActive ? Theme.accentTeal : (tabMouse.containsMouse ? Theme.border : "transparent")

                            Row {
                                id: tabRow
                                anchors.centerIn: parent
                                spacing: 8

                                Text {
                                    text: modelData.label
                                    color: tabBtn.isActive ? "#ffffff" : Theme.textSecondary
                                    font.pixelSize: 13
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                }

                                Rectangle {
                                    width: countText.implicitWidth + 12
                                    height: 18
                                    radius: 9
                                    color: tabBtn.isActive ? "#4dffffff" : "#33000000"
                                    anchors.verticalCenter: parent.verticalCenter

                                    Text {
                                        id: countText
                                        anchors.centerIn: parent
                                        text: modelData.count.toString()
                                        color: tabBtn.isActive ? "#ffffff" : Theme.textSecondary
                                        font.pixelSize: 11
                                        font.bold: true
                                        font.family: Theme.fontFamily
                                    }
                                }
                            }

                            MouseArea {
                                id: tabMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.currentType = modelData.id
                                    root.updateFilter()
                                }
                            }
                        }
                    }
                }

                // Filter Dropdowns Row
                Flow {
                    width: parent.width
                    spacing: 12

                    // Category
                    Row {
                        spacing: 8
                        Text {
                            text: tr("category")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.bold: true
                            font.family: Theme.fontFamily
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        ComboBox {
                            id: catCombo
                            height: 32
                            model: [
                                { key: "all", text: tr("filter_all_categories") },
                                { key: "development", text: tr("nav_development") },
                                { key: "education", text: tr("nav_education") },
                                { key: "enterprise", text: tr("nav_enterprise") },
                                { key: "games", text: tr("nav_games") },
                                { key: "graphics", text: tr("nav_graphics") },
                                { key: "internet", text: tr("nav_internet") },
                                { key: "multimedia", text: tr("nav_multimedia") },
                                { key: "office", text: tr("nav_office") },
                                { key: "system", text: tr("nav_system") },
                                { key: "utilities", text: tr("nav_utilities") }
                            ]
                            textRole: "text"
                            onActivated: function(index) {
                                root.currentCategory = model[index].key
                                root.updateFilter()
                            }
                        }
                    }

                    // Source
                    Row {
                        spacing: 8
                        Text {
                            text: tr("repo_origin")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.bold: true
                            font.family: Theme.fontFamily
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        ComboBox {
                            height: 32
                            model: [
                                { key: "all", text: tr("filter_all_sources") },
                                { key: "luppo", text: tr("filter_source_luppo") },
                                { key: "flatpak", text: tr("filter_source_flatpak") }
                            ]
                            textRole: "text"
                            onActivated: function(index) {
                                root.currentSource = model[index].key
                                root.updateFilter()
                            }
                        }
                    }

                    // Status
                    Row {
                        spacing: 8
                        Text {
                            text: tr("type")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.bold: true
                            font.family: Theme.fontFamily
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        ComboBox {
                            height: 32
                            model: [
                                { key: "all", text: tr("filter_all_status") },
                                { key: "installed", text: tr("filter_status_installed") },
                                { key: "not_installed", text: tr("filter_status_not_installed") },
                                { key: "updatable", text: tr("filter_status_updatable") }
                            ]
                            textRole: "text"
                            onActivated: function(index) {
                                root.currentStatus = model[index].key
                                root.updateFilter()
                            }
                        }
                    }

                    // Sort
                    Row {
                        spacing: 8
                        Text {
                            text: tr("sort_by")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.bold: true
                            font.family: Theme.fontFamily
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        ComboBox {
                            height: 32
                            model: [
                                { key: "relevance", text: tr("sort_relevance") },
                                { key: "name_asc", text: tr("sort_name_asc") },
                                { key: "name_desc", text: tr("sort_name_desc") },
                                { key: "rating", text: tr("sort_rating") },
                                { key: "downloads", text: tr("sort_downloads") }
                            ]
                            textRole: "text"
                            onActivated: function(index) {
                                root.currentSort = model[index].key
                                root.updateFilter()
                            }
                        }
                    }
                }
            }
        }

        // Empty State
        Rectangle {
            visible: root.filteredResults.length === 0
            width: parent.width
            height: 220
            radius: 16
            color: Theme.sidebarBg
            border.color: Theme.border
            border.width: 1

            Column {
                anchors.centerIn: parent
                spacing: 10
                width: parent.width - 48

                Image {
                    anchors.horizontalCenter: parent.horizontalCenter
                    source: "qrc:/qml/assets/icons/plasma-search.svg"
                    width: 56
                    height: 56
                    opacity: 0.4
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: tr("no_search_results")
                    color: Theme.textPrimary
                    font.pixelSize: 16
                    font.bold: true
                    font.family: Theme.fontFamily
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: tr("no_search_results_hint")
                    color: Theme.textSecondary
                    font.pixelSize: 13
                    font.family: Theme.fontFamily
                }

                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: resetBtnText.implicitWidth + 24
                    height: 32
                    radius: 8
                    color: emptyResetMouse.containsMouse ? Theme.accentTealHover : Theme.accentTeal

                    Text {
                        id: resetBtnText
                        anchors.centerIn: parent
                        text: tr("clear_filters")
                        color: "#ffffff"
                        font.pixelSize: 12
                        font.bold: true
                        font.family: Theme.fontFamily
                    }

                    MouseArea {
                        id: emptyResetMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.resetFilters()
                    }
                }
            }
        }
    }

    model: root.filteredResults

        delegate: Item {
            width: gridView.cellWidth
            height: gridView.cellHeight

            AppCard {
                anchors.fill: parent
                anchors.margins: 7
                pkgData: modelData
                activeWorkersMap: typeof mainWindow !== "undefined" ? mainWindow.activeWorkersMap : ({})
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
