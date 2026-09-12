pragma Singleton
import QtQuick

Item {
    id: root
    visible: false

    // System palette detection from host OS (KDE Plasma / GNOME / XFCE)
    SystemPalette {
        id: sysPalette
        colorGroup: SystemPalette.Active
    }

    // Theme mode: "auto" (system default), "dark", "light"
    property string themeMode: "auto"

    // Detect system dark mode via Qt.styleHints (Qt 6.5+) and SystemPalette window luminance
    readonly property bool systemIsDark: {
        try {
            if (typeof Qt !== "undefined" && Qt.styleHints) {
                var cs = Qt.styleHints.colorScheme
                if (cs === Qt.Dark) return true
                if (cs === Qt.Light) return false
            }
        } catch (e) {}

        // Fallback: check luminance of active system window color
        try {
            var c = Qt.color(sysPalette.window)
            var lum = (c.r * 0.299 + c.g * 0.587 + c.b * 0.114)
            return lum < 0.5
        } catch (e2) {}

        return true
    }

    readonly property bool isDark: {
        if (themeMode === "dark") return true
        if (themeMode === "light") return false
        return systemIsDark
    }

    // Backgrounds: adaptive to host system's palette
    readonly property color bg: {
        if (themeMode === "auto") return sysPalette.window
        return isDark ? "#18181a" : "#f5f6f8"
    }

    readonly property color sidebarBg: {
        if (themeMode === "auto") {
            return isDark ? Qt.darker(sysPalette.window, 1.08) : Qt.darker(sysPalette.window, 1.04)
        }
        return isDark ? "#242426" : "#eaecf0"
    }

    readonly property color cardBg: {
        if (themeMode === "auto") return sysPalette.base
        return isDark ? "#29292c" : "#ffffff"
    }

    readonly property color cardHover: {
        if (themeMode === "auto") {
            return isDark ? Qt.lighter(sysPalette.base, 1.15) : Qt.darker(sysPalette.base, 1.04)
        }
        return isDark ? "#343438" : "#f0f2f5"
    }

    readonly property color border: {
        if (themeMode === "auto") {
            return isDark ? Qt.lighter(sysPalette.window, 1.35) : Qt.darker(sysPalette.window, 1.15)
        }
        return isDark ? "#38383a" : "#d8dce2"
    }

    // Typography: uses system text color
    readonly property color textPrimary: {
        if (themeMode === "auto") return sysPalette.text
        return isDark ? "#ffffff" : "#1a1c1e"
    }

    readonly property color textSecondary: {
        if (themeMode === "auto") {
            var t = Qt.color(sysPalette.text)
            return Qt.rgba(t.r, t.g, t.b, 0.65)
        }
        return isDark ? "#98989d" : "#5e6470"
    }

    // Accent: uses host system's chosen highlight color (e.g. user's KDE/GNOME accent color)
    readonly property color accentTeal: {
        if (themeMode === "auto" && sysPalette.highlight) {
            return sysPalette.highlight
        }
        return "#2ba0b5"
    }
    readonly property color accentTealHover: Qt.darker(accentTeal, 1.15)

    // Action buttons & badges
    readonly property color updateBtnBg: isDark ? Qt.lighter(cardBg, 1.25) : "#e8f0fe"
    readonly property color updateBtnText: isDark ? accentTeal : "#1973e8"
    readonly property color openBtnBg: isDark ? "#23392a" : "#e6f4ea"
    readonly property color openBtnText: isDark ? "#81c784" : "#188038"
    readonly property color flatpakBadgeBg: "#1a6fcf"
    readonly property color dangerRed: isDark ? "#ef4444" : "#d93025"

    // System color scheme button properties (for detail page and cards)
    readonly property color buttonPrimaryBg: accentTeal
    readonly property color buttonPrimaryHover: accentTealHover
    readonly property color buttonPrimaryText: "#ffffff"

    readonly property color buttonSecondaryBg: isDark ? Qt.lighter(cardBg, 1.12) : sysPalette.button
    readonly property color buttonSecondaryHover: isDark ? Qt.lighter(cardBg, 1.25) : Qt.darker(sysPalette.button, 1.08)
    readonly property color buttonSecondaryText: isDark ? "#ffffff" : sysPalette.buttonText

    // Install button accent (synced with theme color scheme)
    readonly property color accentBlue: buttonPrimaryBg
    readonly property color accentBlueHover: buttonPrimaryHover
    readonly property color accentGreenHover: Qt.darker(updateBtnBg, 1.10)

    // Surface for card interiors (slightly lighter than cardBg)
    readonly property color surfaceBg: {
        if (themeMode === "auto") return isDark ? Qt.lighter(sysPalette.base, 1.12) : Qt.darker(sysPalette.base, 1.04)
        return isDark ? "#303034" : "#f0f2f5"
    }

    readonly property string fontFamily: "Noto Sans, Segoe UI, sans-serif"
}
