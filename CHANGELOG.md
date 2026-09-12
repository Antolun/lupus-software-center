# Changelog

All notable changes to **LupuS Software Center** are documented in this file.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [2.0.6] — 2026-09-12

### Added
- **Single-instance application guard** — prevents opening duplicate instances using a per-user Unix domain socket (`/tmp/lupus-software-center-$USER.sock`); subsequent launches without `--minimized` raise and activate the existing window
- **`--minimized` / `-m` startup argument** — launches the application directly into the system tray without displaying the main window on screen (used by system autostart)
- **System tray title & tooltip localization** — tray item name and tooltip dynamically display `"LupuS Yazılım Merkezi"` (TR) or `"LupuS Software Center"` (EN) based on locale; emits `NewTitle` D-Bus signal (`org.kde.StatusNotifierItem.NewTitle`) on runtime language changes for immediate updates in KDE Plasma and other desktop trays
- `isStartMinimized` QML invokable on `BackendBridge`
- `setLanguage` QML invokable on `BackendBridge` — language can now be changed at runtime without restart
- `detect_system_lang()` made `pub` and POSIX-compliant: checks `LANGUAGE` → `LC_ALL` → `LC_MESSAGES` → `LANG` in order (supports colon-separated `LANGUAGE` lists, e.g. `en_US:en`)
- `languageChangeTrigger` reactive property in `Main.qml` — forces re-evaluation of all `tr()` bindings immediately when the language setting is changed
- `saveSettings()` in `Main.qml` now calls `backend.setLanguage()` and increments `languageChangeTrigger` on language change
- Startup language initialization in `main.rs`: `settings::load_settings()` + `i18n::set_lang()` are called before the QML engine starts

### Fixed
- **"Run in Background When Closed" (`close_to_tray`) setting had no effect** — closing the window now properly calls `Qt.quit()` to exit the application when the setting is unchecked, and hides to tray when checked
- **System tray displaying raw binary name `lupus-software-center`** — application name (`QCoreApplication::setApplicationName`) and display name (`QGuiApplication::setApplicationDisplayName`) are now correctly initialized with the localized application title
- **Settings language change leaving parts of the UI in Turkish** — all QML text bindings are now reactive and refresh instantly on language switch
- `detect_system_lang()` was ignoring the `LANGUAGE` environment variable (used by KDE/GNOME to set UI language) and relying only on `LANG`; this caused the app to start in Turkish even when the desktop was set to English
- Default language in `AppSettings` was hardcoded to `"tr"` — now uses `detect_system_lang()` to respect the system locale on first run
- `cancel_package`, `install_package` and `remove_package` completion/cancel messages were hardcoded Turkish strings — replaced with `i18n::tr()` calls
- Flatpak progress bar stuck at 0% — `parse_flatpak_progress` rewritten to correctly map download/deploy phases to 0–100% range
- Install/Remove button color on the detail page now syncs with the active color scheme accent (`Theme.accentTeal`) instead of a hardcoded blue

### Removed
- Star rating card from the package detail page (`DetailView.qml`)

---

## [2.0.5] — 2026-08-27

### Changed
- Search engine overhaul: improved relevance ranking and full-text matching across package name, summary and description fields

---

## [2.0.4] — 2026-08-22

### Added
- udev rules (`udev/`) for passwordless package management
- Polkit action and rules (`polkit/`) for privilege escalation without password prompts
- sudoers drop-in (`sudoers/`) for seamless sudo integration
- Revamped auto-updater: background update checking now works for both Luppo and Flatpak packages with configurable intervals

---

## [2.0.3] — 2026-08-22

### Removed
- Standalone `luppo` CLI wrapper removed from the backend; package operations now go through `luppo-core` crate APIs directly

---

## [2.0.2] — 2026-08-21

### Added
- `format_luppo_display_name()` utility: converts raw package IDs (e.g. `my-pkg-name`) into human-readable display names (`My Pkg Name`)

---

## [2.0.1] — 2026-08-15

### Added
- Luppo package builder (`build-luppo.sh`, `lopec.xml`, `actions.py`) replacing the old Pisi build system

### Removed
- Pisi package builder support

---

## [2.0.0] — 2026-08-13

### Added
- Full Rust + CXX-Qt rewrite of the original Python/PyQt6 application
- Native Qt Quick / QML frontend with dark/light/auto theme support
- Asynchronous Luppo and Flatpak package management via Tokio runtime
- Flathub API integration for rich package metadata and screenshots
- System tray icon with update notifications
- Turkish and English i18n support
- Persistent user settings (JSON) with autostart, tray, update interval and theme options
- Category-based browsing (Development, Education, Games, Graphics, Internet, Multimedia, Office, System, Utilities)
- Live search with recent search history
- Background update checker with configurable polling intervals
