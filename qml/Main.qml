import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform as Platform
import com.antolun.lupus.software.center 1.0

ApplicationWindow {
    id: mainWindow

    title: "LupuS " + tr("software_center") + " - Luppo Market"
    width: 1400
    height: 820
    minimumWidth: 1000
    minimumHeight: 620
    visible: true
    color: Theme.bg

    // CXX-Qt Backend Bridge
    BackendBridge {
        id: backend

        onPackageProgress: function(pkgName, progress, status, message) {
            var workers = Object.assign({}, mainWindow.activeWorkersMap)
            if (status === "completed" || status === "error") {
                delete workers[pkgName]
                if (status === "completed") {
                    // Instantly toggle installed state in memory for immediate button update
                    var updatedList = mainWindow.allPackages.slice()
                    for (var i = 0; i < updatedList.length; i++) {
                        if (updatedList[i].name === pkgName) {
                            var p = Object.assign({}, updatedList[i])
                            p.installed = !p.installed
                            p.has_update = false
                            updatedList[i] = p
                            break
                        }
                    }
                    mainWindow.allPackages = updatedList

                    if (mainWindow.currentDetailPkg && mainWindow.currentDetailPkg.name === pkgName) {
                        var dp = Object.assign({}, mainWindow.currentDetailPkg)
                        dp.installed = !dp.installed
                        dp.has_update = false
                        mainWindow.currentDetailPkg = dp
                    }

                    // Also update SearchView rawResults so install button updates immediately
                    if (typeof searchView !== "undefined" && searchView.rawResults) {
                        var sResults = searchView.rawResults.slice()
                        for (var si = 0; si < sResults.length; si++) {
                            if (sResults[si].name === pkgName) {
                                var sp = Object.assign({}, sResults[si])
                                sp.installed = !sp.installed
                                sp.has_update = false
                                sResults[si] = sp
                                break
                            }
                        }
                        searchView.rawResults = sResults
                    }
                }
            } else {
                var currentProg = (workers[pkgName] && workers[pkgName].progress !== undefined) ? workers[pkgName].progress : 0
                var newProg = Math.max(currentProg, progress)
                workers[pkgName] = { progress: newProg, status: status, message: message }
            }
            mainWindow.activeWorkersMap = workers
        }

        onUpdatesChecked: function(count, pkgsJson) {
            mainWindow.refreshPackages()
            mainWindow.isCheckingUpdates = false
        }

        onPackagesChanged: {
            mainWindow.refreshPackages()
            if (mainWindow.currentDetailPkg && mainWindow.currentDetailPkg.name) {
                var found = mainWindow.allPackages.find(function(p) {
                    return p.name === mainWindow.currentDetailPkg.name
                })
                if (found) {
                    var updated = Object.assign({}, mainWindow.currentDetailPkg)
                    updated.installed = found.installed
                    updated.has_update = found.has_update
                    updated.version = found.version
                    if (found.download_size) updated.download_size = found.download_size
                    if (found.installed_size) updated.installed_size = found.installed_size
                    mainWindow.currentDetailPkg = updated
                }
            }
            if (loadingOverlay.isLoading) {
                loadingOverlay.progress = 1.0
                initTimer.start()
            }
        }
    }

    // ── Global State ──
    property var allPackages: []
    property var categoriesList: []
    property var activeWorkersMap: ({})
    property var historyStack: []
    property string currentView: "discover"
    property string currentCatId: "all"
    property string currentCatName: tr("nav_discover")
    property string currentCatIcon: "plasma-search"
    property var currentDetailPkg: null
    property var currentScreenshots: []
    property var recentSearchesList: []
    property bool isCheckingUpdates: false
    property var appSettings: ({
        autostart: false,
        close_to_tray: true,
        auto_install_updates: false,
        check_interval_hours: 4,
        language: "tr"
    })

    // Incrementing this property forces QML to re-evaluate all tr() bindings
    property int languageChangeTrigger: 0

    // Helper translation function – reads languageChangeTrigger so bindings refresh on language change
    function tr(key) {
        var _t = mainWindow.languageChangeTrigger  // reactive dependency
        return backend.translateKey(key)
    }

    // ── View Switching ──
    function switchView(viewName, pushHist) {
        if (pushHist && mainWindow.currentView !== viewName) {
            mainWindow.historyStack.push({
                view: mainWindow.currentView,
                catId: mainWindow.currentCatId,
                catName: mainWindow.currentCatName,
                catIcon: mainWindow.currentCatIcon,
                detailPkg: mainWindow.currentDetailPkg
            })
        }
        mainWindow.currentView = viewName
        topbar.canGoBack = mainWindow.historyStack.length > 0
    }

    function goBack() {
        if (mainWindow.historyStack.length > 0) {
            var prev = mainWindow.historyStack.pop()
            mainWindow.currentCatId = prev.catId
            mainWindow.currentCatName = prev.catName
            mainWindow.currentCatIcon = prev.catIcon
            mainWindow.currentDetailPkg = prev.detailPkg
            mainWindow.currentView = prev.view
            topbar.canGoBack = mainWindow.historyStack.length > 0
        }
    }

    // ── Navigation ──
    function selectCategory(catId) {
        mainWindow.currentCatId = catId
        if (catId === "all") {
            switchView("discover", true)
        } else if (catId === "updates") {
            switchView("installed", true)
        } else if (catId === "settings") {
            switchView("settings", true)
        } else if (catId === "about") {
            switchView("about", true)
        } else {
            // Find category info
            var cat = null
            for (var i = 0; i < mainWindow.categoriesList.length; i++) {
                if (mainWindow.categoriesList[i].id === catId) {
                    cat = mainWindow.categoriesList[i]
                    break
                }
            }
            if (cat) {
                mainWindow.currentCatName = cat.name
                mainWindow.currentCatIcon = cat.icon || "applications-utilities"
            }
            switchView("category", true)
        }
    }

    function openDetail(pkg) {
        mainWindow.currentDetailPkg = pkg
        mainWindow.currentScreenshots = []
        switchView("detail", true)

        // Enrich package details from backend
        if (pkg.name) {
            var enrichedJson = backend.getPackageDetails(pkg.name)
            if (enrichedJson && enrichedJson.length > 0) {
                try {
                    var enriched = JSON.parse(enrichedJson)
                    mainWindow.currentDetailPkg = enriched
                } catch (e) {}
            }

            // Flatpak screenshots & metadata from Flathub API
            if (pkg.is_flatpak) {
                var fpJson = backend.getFlatpakInfo(pkg.name)
                if (fpJson && fpJson.length > 0) {
                    try {
                        var fp = JSON.parse(fpJson)

                        // Merge Flathub metadata into currentDetailPkg
                        var merged = Object.assign({}, mainWindow.currentDetailPkg)

                        if (fp.description && fp.description.length > 0) {
                            merged.description = fp.description
                        }
                        if (fp.summary && fp.summary.length > 0 && (!merged.summary || merged.summary.indexOf(" · ") !== -1)) {
                            merged.summary = fp.summary
                        }
                        if (fp.name && fp.name.length > 0) {
                            merged.display_name = fp.name
                        }
                        if (fp.developer_name && fp.developer_name.length > 0) {
                            merged.developer = fp.developer_name
                        } else if (fp.projectLicense && !merged.license) {
                            merged.license = fp.projectLicense
                        }
                        if (fp.homepageUrl && fp.homepageUrl.length > 0) {
                            merged.homepage = fp.homepageUrl
                        }
                        if (fp.projectLicense && fp.projectLicense.length > 0) {
                            merged.license = fp.projectLicense
                        }
                        mainWindow.currentDetailPkg = merged

                        // Screenshots
                        if (fp.screenshots && fp.screenshots.length > 0) {
                            var scList = []
                            for (var s = 0; s < Math.min(fp.screenshots.length, 5); s++) {
                                var sc = fp.screenshots[s]
                                var u = (typeof sc === "string") ? sc : (sc.imgDesktopUrl || sc.imgMobileUrl || sc.thumbUrl)
                                if (u) scList.push(u)
                            }
                            mainWindow.currentScreenshots = scList
                        }
                    } catch (e) {}
                }
            }
        }
    }

    // ── Package Actions ──
    function installPackage(pkgName) {
        var workers = Object.assign({}, mainWindow.activeWorkersMap)
        workers[pkgName] = { progress: 0, status: "starting", message: tr("loading_init") }
        mainWindow.activeWorkersMap = workers
        backend.installPackage(pkgName)
    }

    function removePackage(pkgName) {
        var workers = Object.assign({}, mainWindow.activeWorkersMap)
        workers[pkgName] = { progress: 0, status: "starting", message: tr("loading_init") }
        mainWindow.activeWorkersMap = workers
        backend.removePackage(pkgName)
    }

    function cancelWorker(pkgName) {
        var workers = Object.assign({}, mainWindow.activeWorkersMap)
        delete workers[pkgName]
        mainWindow.activeWorkersMap = workers
        backend.cancelPackage(pkgName)
    }

    function checkForUpdates() {
        mainWindow.isCheckingUpdates = true
        backend.checkForUpdates(true)
    }

    function refreshPackages() {
        var pkgsJson = backend.getAvailablePackages()
        if (pkgsJson && pkgsJson.length > 0) {
            try {
                mainWindow.allPackages = JSON.parse(pkgsJson)
            } catch (e) {}
        }

        var catsJson = backend.getCategories()
        if (catsJson && catsJson.length > 0) {
            try {
                mainWindow.categoriesList = JSON.parse(catsJson)
            } catch (e) {}
        }
    }

    // ── Search Handling ──
    function performSearch(query) {
        if (!query || !query.trim()) {
            if (mainWindow.currentCatId === "all") switchView("discover", false)
            else if (mainWindow.currentCatId === "updates") switchView("installed", false)
            else if (mainWindow.currentCatId === "settings") switchView("settings", false)
            else if (mainWindow.currentCatId === "about") switchView("about", false)
            else switchView("category", false)
            return
        }

        searchView.searchQuery = query.trim()
        var resultsJson = backend.searchPackages(query.trim())
        if (resultsJson && resultsJson.length > 0) {
            try {
                searchView.rawResults = JSON.parse(resultsJson)
            } catch (e) {
                searchView.rawResults = []
            }
        } else {
            searchView.rawResults = []
        }

        // Add to recent searches
        var history = mainWindow.recentSearchesList.filter(function(x) { return x.toLowerCase() !== query.trim().toLowerCase() })
        history.unshift(query.trim())
        if (history.length > 6) history = history.slice(0, 6)
        mainWindow.recentSearchesList = history

        switchView("search", true)
    }

    // ── Settings Save ──
    function saveSettings(newSettings) {
        var langChanged = newSettings.language !== mainWindow.appSettings.language
        mainWindow.appSettings = newSettings
        if (newSettings.theme) {
            Theme.themeMode = newSettings.theme
        }
        backend.saveSettings(JSON.stringify(newSettings))
        backend.setAutostart(newSettings.autostart)
        if (langChanged) {
            // Tell backend the new language so translateKey() returns correct strings
            backend.setLanguage(newSettings.language)
            // Increment trigger to force re-evaluation of all tr() bindings in QML
            mainWindow.languageChangeTrigger += 1
            // Update category name display in new language
            if (mainWindow.currentCatId === "all") {
                mainWindow.currentCatName = tr("nav_discover")
            }
        }
        refreshPackages()
    }

    // ── System Tray Icon ──
    Platform.SystemTrayIcon {
        id: systemTray
        visible: true
        icon.source: "qrc:/qml/assets/lupus-software-center.png"
        tooltip: "LupuS Software Center"

        menu: Platform.Menu {
            Platform.MenuItem {
                text: tr("tray_open_app")
                onTriggered: {
                    mainWindow.show()
                    mainWindow.raise()
                    mainWindow.requestActivate()
                }
            }
            Platform.MenuItem {
                text: tr("tray_check_updates")
                onTriggered: mainWindow.checkForUpdates()
            }
            Platform.MenuSeparator {}
            Platform.MenuItem {
                text: tr("tray_exit")
                onTriggered: Qt.quit()
            }
        }

        onActivated: function(reason) {
            if (reason === Platform.SystemTrayIcon.Trigger) {
                if (mainWindow.visible) mainWindow.hide()
                else {
                    mainWindow.show()
                    mainWindow.raise()
                    mainWindow.requestActivate()
                }
            }
        }
    }

    onClosing: function(close) {
        if (mainWindow.appSettings.close_to_tray) {
            close.accepted = false
            mainWindow.hide()
        }
    }

    // Global keyboard shortcut Ctrl+F
    Shortcut {
        sequences: ["Ctrl+F", "Ctrl+f"]
        onActivated: topbar.focusSearch()
    }

    // ── UI Layout ──
    Row {
        anchors.fill: parent

        // 1. Sidebar (220px fixed)
        Sidebar {
            id: sidebar
            height: parent.height
            currentCategory: mainWindow.currentCatId
            categoriesList: mainWindow.categoriesList
            updatesCount: {
                var c = 0
                for (var i = 0; i < mainWindow.allPackages.length; i++) {
                    if (mainWindow.allPackages[i].has_update) c++
                }
                // Also count active workers (in-progress installs/removals)
                var workers = mainWindow.activeWorkersMap
                for (var key in workers) {
                    if (workers.hasOwnProperty(key)) c++
                }
                return c
            }
            onCategorySelected: function(catId) { mainWindow.selectCategory(catId) }
        }

        // 2. Main Content Area
        Column {
            width: parent.width - 220
            height: parent.height

            // Topbar
            Topbar {
                id: topbar
                width: parent.width
                recentSearches: mainWindow.recentSearchesList
                onBackClicked: mainWindow.goBack()
                onSearchTriggered: function(q) { mainWindow.performSearch(q) }
                onSearchCleared: {
                    if (mainWindow.currentView === "search") {
                        mainWindow.selectCategory(mainWindow.currentCatId)
                    }
                }
                onDeleteSearch: function(q) {
                    mainWindow.recentSearchesList = mainWindow.recentSearchesList.filter(function(x) { return x !== q })
                }
                onClearHistory: {
                    mainWindow.recentSearchesList = []
                }
            }

            // View Stack Container
            Item {
                width: parent.width
                height: parent.height - 56

                // Discover View
                DiscoverView {
                    id: discoverView
                    anchors.fill: parent
                    visible: mainWindow.currentView === "discover"
                    packagesList: mainWindow.allPackages
                    onAppClicked: function(p) { mainWindow.openDetail(p) }
                    onInstallClicked: function(n) { mainWindow.installPackage(n) }
                    onRemoveClicked: function(n) { mainWindow.removePackage(n) }
                    onCancelClicked: function(n) { mainWindow.cancelWorker(n) }
                }

                // Category View
                CategoryView {
                    id: categoryView
                    anchors.fill: parent
                    visible: mainWindow.currentView === "category"
                    categoryId: mainWindow.currentCatId
                    categoryName: mainWindow.currentCatName
                    categoryIcon: mainWindow.currentCatIcon
                    packagesList: {
                        if (mainWindow.currentCatId === "all") return mainWindow.allPackages
                        return mainWindow.allPackages.filter(function(p) {
                            return p.category && p.category.toLowerCase() === mainWindow.currentCatId.toLowerCase()
                        })
                    }
                    onAppClicked: function(p) { mainWindow.openDetail(p) }
                    onInstallClicked: function(n) { mainWindow.installPackage(n) }
                    onRemoveClicked: function(n) { mainWindow.removePackage(n) }
                    onCancelClicked: function(n) { mainWindow.cancelWorker(n) }
                }

                // App Detail View
                DetailView {
                    id: detailView
                    anchors.fill: parent
                    visible: mainWindow.currentView === "detail"
                    pkgData: mainWindow.currentDetailPkg
                    screenshotsList: mainWindow.currentScreenshots
                    onInstallClicked: function(n) { mainWindow.installPackage(n) }
                    onRemoveClicked: function(n) { mainWindow.removePackage(n) }
                    onCancelClicked: function(n) { mainWindow.cancelWorker(n) }
                    onScreenshotClicked: function(u) { imageModal.imageSource = u }
                }

                // Installed & Updates View
                InstalledUpdatesView {
                    id: installedView
                    anchors.fill: parent
                    visible: mainWindow.currentView === "installed"
                    updatesList: mainWindow.allPackages.filter(function(p) { return p.has_update })
                    installedList: mainWindow.allPackages.filter(function(p) { return p.installed })
                    downloadsList: {
                        // Packages currently being installed/updated/removed
                        var workers = mainWindow.activeWorkersMap
                        var result = []
                        for (var k in workers) {
                            if (!workers.hasOwnProperty(k)) continue
                            var pkg = mainWindow.allPackages.find(function(p) { return p.name === k })
                            if (pkg) result.push(pkg)
                        }
                        return result
                    }
                    activeWorkersMap: mainWindow.activeWorkersMap
                    isCheckingUpdates: mainWindow.isCheckingUpdates
                    onAppClicked: function(p) { mainWindow.openDetail(p) }
                    onInstallClicked: function(n) { mainWindow.installPackage(n) }
                    onRemoveClicked: function(n) { mainWindow.removePackage(n) }
                    onCancelClicked: function(n) { mainWindow.cancelWorker(n) }
                    onCheckUpdatesClicked: mainWindow.checkForUpdates()
                }

                // Search Results View
                SearchView {
                    id: searchView
                    anchors.fill: parent
                    visible: mainWindow.currentView === "search"
                    onAppClicked: function(p) { mainWindow.openDetail(p) }
                    onInstallClicked: function(n) { mainWindow.installPackage(n) }
                    onRemoveClicked: function(n) { mainWindow.removePackage(n) }
                    onCancelClicked: function(n) { mainWindow.cancelWorker(n) }
                }

                // Settings View
                SettingsView {
                    id: settingsView
                    anchors.fill: parent
                    visible: mainWindow.currentView === "settings"
                    autostart: mainWindow.appSettings.autostart
                    closeToTray: mainWindow.appSettings.close_to_tray
                    autoInstall: mainWindow.appSettings.auto_install_updates
                    checkInterval: mainWindow.appSettings.check_interval_hours || 4
                    currentLanguage: mainWindow.appSettings.language || "tr"
                    currentTheme: mainWindow.appSettings.theme || "auto"
                    onSettingsChanged: function(s) { mainWindow.saveSettings(s) }
                }

                // About View
                AboutView {
                    id: aboutView
                    anchors.fill: parent
                    visible: mainWindow.currentView === "about"
                }
            }
        }
    }

    // ── Image Zoom Modal ──
    ImageModal {
        id: imageModal
        anchors.fill: parent
        onClosed: imageSource = ""
    }

    // ── Loading Overlay ──
    LoadingOverlay {
        id: loadingOverlay
        anchors.fill: parent
    }

    // ── App Startup Initialization ──
    Component.onCompleted: {
        loadingOverlay.message = tr("loading_prep")
        loadingOverlay.progress = 0.1

        // 1. Load Settings (fast — just reads a small JSON file)
        var sJson = backend.loadSettings()
        if (sJson && sJson.length > 0) {
            try {
                mainWindow.appSettings = JSON.parse(sJson)
                if (mainWindow.appSettings.theme) {
                    Theme.themeMode = mainWindow.appSettings.theme
                }
            } catch (e) {}
        }

        // 2. Load Categories immediately (populated right away in sidebar)
        var catsJson = backend.getCategories()
        if (catsJson && catsJson.length > 0) {
            try {
                mainWindow.categoriesList = JSON.parse(catsJson)
            } catch (e) {}
        }

        loadingOverlay.message = tr("loading_repo_pkgs")
        loadingOverlay.progress = 0.3

        // 3. Defer background package scan to next event loop iteration
        startupTimer.start()
    }

    Timer {
        id: startupTimer
        interval: 50   // one frame — lets Qt render the loading overlay before background load
        onTriggered: {
            loadingOverlay.progress = 0.6
            backend.loadPackagesAsync()
        }
    }

    Timer {
        id: initTimer
        interval: 200
        onTriggered: {
            loadingOverlay.isLoading = false
        }
    }
}
