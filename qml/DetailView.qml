import QtQuick
import QtQuick.Controls
import com.antolun.lupus.software.center 1.0

ScrollView {
    id: root

    property var pkgData: null
    property var screenshotsList: []
    property var activeWorkersMap: typeof mainWindow !== "undefined" ? mainWindow.activeWorkersMap : ({})

    function tr(key) {
        return typeof mainWindow !== "undefined" && mainWindow.tr ? mainWindow.tr(key) : key
    }

    signal installClicked(string pkgName)
    signal removeClicked(string pkgName)
    signal cancelClicked(string pkgName)
    signal screenshotClicked(string imageUrl)

    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical.policy: ScrollBar.AsNeeded

    // Centered Content Container
    Item {
        width: Math.min(root.width - 48, 1000)
        implicitHeight: mainCol.height + 64
        anchors.horizontalCenter: parent.horizontalCenter

        Column {
            id: mainCol
            width: parent.width
            topPadding: 24
            bottomPadding: 48
            spacing: 24

            // ══════════════════════════════════════════════════════════════════════
            // 1. HERO HEADER CARD
            // ══════════════════════════════════════════════════════════════════════
            Rectangle {
                width: parent.width
                implicitHeight: heroContentRow.implicitHeight + 48
                radius: 16
                color: Theme.cardBg
                border.color: Theme.border
                border.width: 1

                Item {
                    id: heroContentRow
                    anchors.fill: parent
                    anchors.margins: 24
                    implicitHeight: Math.max(heroLeftRow.implicitHeight, actionBox.implicitHeight)

                    // Left Side: Icon + Titles
                    Row {
                        id: heroLeftRow
                        anchors.left: parent.left
                        anchors.right: actionBox.left
                        anchors.rightMargin: 20
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 20

                        // App Icon Box
                        Rectangle {
                            width: 88
                            height: 88
                            radius: 18
                            color: Theme.surfaceBg
                            border.color: Theme.border
                            border.width: 1
                            clip: true
                            anchors.verticalCenter: parent.verticalCenter

                            Image {
                                id: detailIconImg
                                anchors.centerIn: parent
                                width: 72
                                height: 72
                                fillMode: Image.PreserveAspectFit
                                sourceSize.width: 144
                                sourceSize.height: 144
                                asynchronous: true
                                cache: true

                                readonly property string defaultIcon: (root.pkgData && root.pkgData.is_flatpak)
                                    ? "qrc:/qml/assets/icons/package-x-generic.svg"
                                    : "qrc:/qml/assets/luppo.png"

                                source: {
                                    if (!root.pkgData) return "qrc:/qml/assets/luppo.png"
                                    var ip = root.pkgData.icon_path || ""
                                    if (ip.length > 0) {
                                        if (ip[0] === "/") return "file://" + ip
                                        return ip
                                    }
                                    return defaultIcon
                                }

                                onStatusChanged: {
                                    if (status === Image.Error && source !== defaultIcon) {
                                        source = defaultIcon
                                    }
                                }
                            }
                        }

                        // App Meta Column
                        Column {
                            width: parent.width - 108
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 6

                            // Title & Origin Badge
                            Row {
                                spacing: 10
                                width: parent.width

                                Text {
                                    text: {
                                        if (!root.pkgData) return ""
                                        if (root.pkgData.display_name && root.pkgData.display_name.length > 0) return root.pkgData.display_name
                                        var n = root.pkgData.name || ""
                                        return n.split("-").map(function(w) { return w.charAt(0).toUpperCase() + w.slice(1); }).join(" ")
                                    }
                                    color: Theme.textPrimary
                                    font.pixelSize: 22
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    elide: Text.ElideRight
                                    maximumLineCount: 1
                                }

                                // Origin Badge (Flathub or Luppo)
                                Rectangle {
                                    radius: 6
                                    height: 22
                                    width: originBadgeText.implicitWidth + 14
                                    anchors.verticalCenter: parent.verticalCenter
                                    color: (root.pkgData && root.pkgData.is_flatpak) ? "#2b3990" : Theme.accentTeal

                                    Text {
                                        id: originBadgeText
                                        anchors.centerIn: parent
                                        text: (root.pkgData && root.pkgData.origin) ? root.pkgData.origin : (root.pkgData && root.pkgData.is_flatpak ? "Flathub" : "Luppo")
                                        color: "#ffffff"
                                        font.pixelSize: 10
                                        font.bold: true
                                        font.family: Theme.fontFamily
                                    }
                                }

                                // Category Pill
                                Rectangle {
                                    visible: root.pkgData && root.pkgData.category && root.pkgData.category.length > 0
                                    radius: 6
                                    height: 22
                                    width: catPillText.implicitWidth + 12
                                    anchors.verticalCenter: parent.verticalCenter
                                    color: "transparent"
                                    border.color: Theme.border
                                    border.width: 1

                                    Text {
                                        id: catPillText
                                        anchors.centerIn: parent
                                        text: {
                                            if (!root.pkgData || !root.pkgData.category) return ""
                                            var c = root.pkgData.category.toLowerCase()
                                            return tr("nav_" + c) !== ("nav_" + c) ? tr("nav_" + c) : root.pkgData.category
                                        }
                                        color: Theme.accentTeal
                                        font.pixelSize: 10
                                        font.bold: true
                                        font.family: Theme.fontFamily
                                    }
                                }
                            }

                            // Developer / Author
                            Text {
                                text: root.pkgData && root.pkgData.developer ? root.pkgData.developer : tr("unknown_developer")
                                color: Theme.textSecondary
                                font.pixelSize: 13
                                font.family: Theme.fontFamily
                            }

                            // Summary / Tagline
                            Text {
                                text: root.pkgData ? (root.pkgData.summary || "") : ""
                                color: Theme.textSecondary
                                font.pixelSize: 13
                                font.family: Theme.fontFamily
                                width: parent.width
                                wrapMode: Text.WordWrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                            }
                        }
                    }

                    // Right Side: Action Box (Install, Update, Remove, Progress)
                    Item {
                        id: actionBox
                        width: 150
                        implicitHeight: 56
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter

                        readonly property bool isWorking: root.pkgData && activeWorkersMap[root.pkgData.name] !== undefined
                        readonly property var workerInfo: isWorking ? activeWorkersMap[root.pkgData.name] : null

                        // ── Working Progress State ──
                        Column {
                            visible: actionBox.isWorking
                            anchors.centerIn: parent
                            width: parent.width
                            spacing: 6

                            Item {
                                width: parent.width
                                height: 18

                                Text {
                                    anchors.left: parent.left
                                    text: {
                                        if (!actionBox.workerInfo) return tr("loading_init")
                                        var pct = actionBox.workerInfo.progress || 0
                                        var st = actionBox.workerInfo.status || ""
                                        if (st === "installing") return pct + "% (" + tr("status_installing") + ")"
                                        if (st === "removing") return pct + "% (" + tr("status_removing") + ")"
                                        return pct + "%"
                                    }
                                    font.pixelSize: 11
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    color: Theme.accentTeal
                                    anchors.verticalCenter: parent.verticalCenter
                                }

                                Text {
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: tr("btn_cancel")
                                    font.pixelSize: 11
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    color: cancelDetailMouse.containsMouse ? Theme.dangerRed : Theme.textSecondary

                                    MouseArea {
                                        id: cancelDetailMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            if (root.pkgData) root.cancelClicked(root.pkgData.name)
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                width: parent.width
                                height: 7
                                radius: 4
                                color: Theme.surfaceBg
                                border.color: Theme.border
                                border.width: 1
                                clip: true

                                Rectangle {
                                    height: parent.height
                                    radius: 4
                                    color: Theme.accentTeal
                                    width: parent.width * (actionBox.workerInfo ? Math.min(1.0, Math.max(0.0, actionBox.workerInfo.progress / 100.0)) : 0.0)
                                    Behavior on width { NumberAnimation { duration: 180 } }
                                }
                            }
                        }

                        // ── Install Button ──
                        Rectangle {
                            visible: !actionBox.isWorking && root.pkgData && !root.pkgData.installed
                            anchors.centerIn: parent
                            width: 140
                            height: 42
                            radius: 10
                            color: insDMouse.containsMouse ? Theme.border : Theme.updateBtnBg

                            Row {
                                anchors.centerIn: parent
                                spacing: 8
                                Image {
                                    source: "qrc:/qml/assets/icons/download.svg"
                                    width: 16
                                    height: 16
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: tr("btn_install")
                                    color: Theme.buttonPrimaryText
                                    font.pixelSize: 13
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }

                            MouseArea {
                                id: insDMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (root.pkgData) root.installClicked(root.pkgData.name)
                                }
                            }
                        }

                        // ── Update Button ──
                        Rectangle {
                            visible: !actionBox.isWorking && root.pkgData && root.pkgData.installed && root.pkgData.has_update
                            anchors.centerIn: parent
                            width: 140
                            height: 42
                            radius: 10
                            color: updDMouse.containsMouse ? Theme.buttonPrimaryHover : Theme.buttonPrimaryBg

                            Row {
                                anchors.centerIn: parent
                                spacing: 8
                                Image {
                                    source: "qrc:/qml/assets/icons/view-refresh.svg"
                                    width: 16
                                    height: 16
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: tr("btn_update")
                                    color: Theme.buttonPrimaryText
                                    font.pixelSize: 13
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }

                            MouseArea {
                                id: updDMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (root.pkgData) root.installClicked(root.pkgData.name)
                                }
                            }
                        }

                        // ── Remove Button ──
                        Rectangle {
                            visible: !actionBox.isWorking && root.pkgData && root.pkgData.installed && !root.pkgData.has_update
                            anchors.centerIn: parent
                            width: 140
                            height: 42
                            radius: 10
                            color: remDMouse.containsMouse ? "#33ef4444" : Theme.buttonSecondaryBg
                            border.color: remDMouse.containsMouse ? Theme.dangerRed : Theme.border
                            border.width: 1

                            Row {
                                anchors.centerIn: parent
                                spacing: 8
                                Image {
                                    source: "qrc:/qml/assets/icons/edit-delete.svg"
                                    width: 16
                                    height: 16
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: tr("btn_remove")
                                    color: remDMouse.containsMouse ? Theme.dangerRed : Theme.buttonSecondaryText
                                    font.pixelSize: 13
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }

                            MouseArea {
                                id: remDMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (root.pkgData) root.removeClicked(root.pkgData.name)
                                }
                            }
                        }
                    }
                }
            }

            // ══════════════════════════════════════════════════════════════════════
            // 2. QUICK STATS RIBBON (4 INDEPENDENT CARDS)
            // ══════════════════════════════════════════════════════════════════════
            Row {
                width: parent.width
                spacing: 12

                // Card 1: Size
                Rectangle {
                    width: (parent.width - 24) / 3
                    height: 68
                    radius: 12
                    color: Theme.cardBg
                    border.color: Theme.border
                    border.width: 1

                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: tr("size")
                            font.pixelSize: 11
                            font.family: Theme.fontFamily
                            color: Theme.textSecondary
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: root.pkgData ? (root.pkgData.installed_size || root.pkgData.download_size || "-") : "-"
                            font.pixelSize: 14
                            font.bold: true
                            font.family: Theme.fontFamily
                            color: Theme.textPrimary
                        }
                    }
                }

                // Card 2: Package Type & Sandbox
                Rectangle {
                    width: (parent.width - 24) / 3
                    height: 68
                    radius: 12
                    color: Theme.cardBg
                    border.color: Theme.border
                    border.width: 1

                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: tr("type")
                            font.pixelSize: 11
                            font.family: Theme.fontFamily
                            color: Theme.textSecondary
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: root.pkgData && root.pkgData.is_flatpak ? tr("flatpak_pkg") : tr("luppo_pkg")
                            font.pixelSize: 14
                            font.bold: true
                            font.family: Theme.fontFamily
                            color: Theme.accentTeal
                        }
                    }
                }

                // Card 3: Version
                Rectangle {
                    width: (parent.width - 24) / 3
                    height: 68
                    radius: 12
                    color: Theme.cardBg
                    border.color: Theme.border
                    border.width: 1

                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: tr("version")
                            font.pixelSize: 11
                            font.family: Theme.fontFamily
                            color: Theme.textSecondary
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: root.pkgData && root.pkgData.version ? root.pkgData.version : "1.0.0"
                            font.pixelSize: 14
                            font.bold: true
                            font.family: Theme.fontFamily
                            color: Theme.textPrimary
                            elide: Text.ElideRight
                            maximumLineCount: 1
                        }
                    }
                }
            }

            // ══════════════════════════════════════════════════════════════════════
            // 3. SCREENSHOTS GALLERY
            // ══════════════════════════════════════════════════════════════════════
            Column {
                visible: root.screenshotsList && root.screenshotsList.length > 0
                width: parent.width
                spacing: 12

                Text {
                    text: tr("screenshots")
                    color: Theme.textPrimary
                    font.pixelSize: 16
                    font.bold: true
                    font.family: Theme.fontFamily
                }

                ScrollView {
                    width: parent.width
                    height: 228
                    clip: true
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOff
                    ScrollBar.horizontal.policy: ScrollBar.AsNeeded

                    Row {
                        spacing: 14
                        height: 216

                        Repeater {
                            model: root.screenshotsList

                            delegate: Rectangle {
                                width: 340
                                height: 216
                                radius: 12
                                color: Theme.cardBg
                                border.color: shotMouse.containsMouse ? Theme.accentTeal : Theme.border
                                border.width: shotMouse.containsMouse ? 2 : 1
                                clip: true

                                Image {
                                    anchors.fill: parent
                                    source: modelData
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                }

                                MouseArea {
                                    id: shotMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.screenshotClicked(modelData)
                                }
                            }
                        }
                    }
                }
            }

            // ══════════════════════════════════════════════════════════════════════
            // 4. ABOUT & DESCRIPTION CARD
            // ══════════════════════════════════════════════════════════════════════
            Column {
                width: parent.width
                spacing: 10

                Text {
                    text: tr("about")
                    color: Theme.textPrimary
                    font.pixelSize: 16
                    font.bold: true
                    font.family: Theme.fontFamily
                }

                Rectangle {
                    width: parent.width
                    implicitHeight: descText.implicitHeight + 40
                    radius: 14
                    color: Theme.cardBg
                    border.color: Theme.border
                    border.width: 1

                    Text {
                        id: descText
                        anchors.fill: parent
                        anchors.margins: 20
                        text: root.pkgData ? (root.pkgData.description || root.pkgData.summary || tr("no_description")) : ""
                        color: Theme.textPrimary
                        font.pixelSize: 13
                        font.family: Theme.fontFamily
                        lineHeight: 1.55
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // ══════════════════════════════════════════════════════════════════════
            // 5. TECHNICAL DETAILS CARD
            // ══════════════════════════════════════════════════════════════════════
            Column {
                width: parent.width
                spacing: 10

                Text {
                    text: tr("technical_details")
                    color: Theme.textPrimary
                    font.pixelSize: 16
                    font.bold: true
                    font.family: Theme.fontFamily
                }

                Rectangle {
                    width: parent.width
                    implicitHeight: techGrid.implicitHeight + 40
                    radius: 14
                    color: Theme.cardBg
                    border.color: Theme.border
                    border.width: 1

                    Grid {
                        id: techGrid
                        anchors.fill: parent
                        anchors.margins: 20
                        columns: parent.width > 640 ? 3 : 2
                        rowSpacing: 16
                        columnSpacing: 20

                        // Version
                        Column {
                            spacing: 3
                            Text { text: tr("version"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text { text: root.pkgData ? (root.pkgData.version || "1.0.0") : "-"; color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.family: Theme.fontFamily }
                        }

                        // License
                        Column {
                            spacing: 3
                            Text { text: tr("license"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text { text: root.pkgData ? (root.pkgData.license || "GPL") : "-"; color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.family: Theme.fontFamily }
                        }

                        // Type
                        Column {
                            spacing: 3
                            Text { text: tr("type"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text { text: root.pkgData && root.pkgData.is_flatpak ? tr("flatpak_pkg") : tr("luppo_pkg"); color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.family: Theme.fontFamily }
                        }

                        // Repo / Origin
                        Column {
                            spacing: 3
                            Text { text: tr("repo_origin"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text { text: root.pkgData ? (root.pkgData.origin || tr("lupus_main_repo")) : "-"; color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.family: Theme.fontFamily }
                        }

                        // Category
                        Column {
                            spacing: 3
                            Text { text: tr("category"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text {
                                text: {
                                    if (!root.pkgData || !root.pkgData.category) return "-"
                                    var c = root.pkgData.category.toLowerCase()
                                    return tr("nav_" + c) !== ("nav_" + c) ? tr("nav_" + c) : root.pkgData.category
                                }
                                color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.family: Theme.fontFamily
                            }
                        }

                        // Developer
                        Column {
                            spacing: 3
                            Text { text: tr("developer"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text { text: root.pkgData ? (root.pkgData.developer || tr("unknown_developer")) : "-"; color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.family: Theme.fontFamily }
                        }

                        // Download Size
                        Column {
                            visible: root.pkgData && root.pkgData.download_size
                            spacing: 3
                            Text { text: tr("download_size"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text { text: root.pkgData ? (root.pkgData.download_size || "-") : "-"; color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.family: Theme.fontFamily }
                        }

                        // Required Space
                        Column {
                            visible: root.pkgData && root.pkgData.installed_size
                            spacing: 3
                            Text { text: tr("required_space"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text { text: root.pkgData ? (root.pkgData.installed_size || "-") : "-"; color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.family: Theme.fontFamily }
                        }

                        // Homepage Website Link
                        Column {
                            visible: root.pkgData && root.pkgData.homepage && root.pkgData.homepage.length > 0
                            spacing: 3
                            Text { text: tr("homepage"); color: Theme.textSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                            Text {
                                text: tr("visit_website")
                                color: Theme.accentTeal
                                font.pixelSize: 13
                                font.bold: true
                                font.underline: homeMouse.containsMouse
                                font.family: Theme.fontFamily

                                MouseArea {
                                    id: homeMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (root.pkgData && root.pkgData.homepage) {
                                            Qt.openUrlExternally(root.pkgData.homepage)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
