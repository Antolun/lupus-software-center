<div align="center">

<img src="icons/128x128.png" width="96" alt="LupuS Software Center icon"/>

# LupuS Software Center

**A modern, fast and native package manager for the LupuS operating system**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/Rust-1.77%2B-orange.svg)](https://www.rust-lang.org/)
[![Version](https://img.shields.io/badge/Version-2.0.6-green.svg)](lopec.xml)

</div>

---

## Overview

**LupuS Software Center** (also known as *Luppo Market*) is the official graphical package manager for [LupuS Linux](https://antolun.com/lupus). It provides a clean, responsive Qt Quick interface for discovering, installing, updating and removing software from both native **Luppo repositories** and **Flathub**.

The application is built with a **Rust** backend (using the [`luppo-core`](https://github.com/Antolun/luppo) crate and [CXX-Qt](https://github.com/KDAB/cxx-qt)) and a **Qt Quick / QML** frontend, giving it native performance with a modern feel.

---

## Features

| Feature | Description |
|---|---|
| 🚀 **Native performance** | Rust backend with async Tokio runtime |
| 📦 **Luppo & Flatpak** | Install, update and remove packages from Luppo repos and Flathub |
| 🔍 **Live search** | Full-text search with instant results and recent search history |
| 🗂 **Category browsing** | Browse apps by category (Development, Games, Graphics, Office, …) |
| 🌐 **Flathub integration** | Rich metadata, screenshots and descriptions fetched from the Flathub API |
| 🔄 **Background updates** | Automatic update checker with configurable intervals |
| 🔔 **System tray** | Runs silently in the background; shows notifications for available updates |
| 🌍 **i18n** | Full Turkish and English localization; language auto-detected from system locale (POSIX) |
| 🎨 **Theme support** | Auto (follows system), Dark and Light themes |
| ✕ **Cancel support** | In-progress install/remove operations can be cancelled at any time |
| 🔒 **Polkit / udev** | Passwordless package management via polkit rules and udev integration |

---

## Requirements

### Runtime

- LupuS Linux (or any compatible distribution)
- `luppo` CLI tool in `$PATH`
- `flatpak` (optional — Flatpak support is enabled automatically when available)

### Build

- **Rust** ≥ 1.77.2 (stable toolchain)
- **Qt** ≥ 6.5 with Qt Quick / QML support
- **CXX-Qt** 0.10 build dependencies
- [`luppo-core`](https://github.com/Antolun/luppo) source checked out at `../luppo/` relative to this repository

---

## Building & Running

### Clone (with sibling luppo repo)

```bash
git clone https://github.com/Antolun/lupus-software-center
git clone https://github.com/Antolun/luppo   # required for luppo-core
```

Directory layout expected:

```
Projeler/LupuS/
├── lupus-software-center/   ← this repo
└── luppo/                   ← luppo-core dependency
```

### Development

```bash
cargo run
```

### Release build

```bash
cargo build --release
```

### Build a Luppo package (`.luppo`)

```bash
make package
# or manually:
cargo build --release
luppo build lopec.xml --no-sandbox --ignore-dependency
```

### Makefile targets

| Target | Description |
|---|---|
| `make build` | Compile the release binary |
| `make run` | Run in debug mode |
| `make package` | Build release binary + `.luppo` package |
| `make clean` | Clean Cargo build artifacts |

---

## Project Structure

```
lupus-software-center/
├── src/
│   ├── main.rs              # Entry point — loads settings & starts QML engine
│   ├── cxxqt_object.rs      # CXX-Qt bridge: QML ↔ Rust bindings & invokables
│   ├── backend.rs           # Luppo & Flatpak package management logic
│   ├── i18n.rs              # Internationalization (EN / TR), POSIX locale detection
│   └── settings.rs          # Persistent user settings (JSON)
├── qml/
│   ├── Main.qml             # Application window, routing, global state
│   ├── Theme.qml            # Centralized color & typography tokens
│   ├── Sidebar.qml          # Navigation sidebar
│   ├── TopBar.qml           # Search bar and toolbar
│   ├── DiscoverView.qml     # Home / featured apps view
│   ├── CategoryView.qml     # Category package listing
│   ├── DetailView.qml       # Package detail page (screenshots, metadata, actions)
│   ├── SearchView.qml       # Search results with filters and sorting
│   ├── InstalledView.qml    # Installed apps & updates manager
│   ├── SettingsView.qml     # Application settings page
│   └── AboutView.qml        # About / version info page
├── icons/                   # Application icons (16x16 → 256x256)
├── polkit/                  # Polkit action and rules files
├── udev/                    # udev rules for package management
├── sudoers/                 # sudoers drop-in for passwordless operations
├── lopec.xml                # Luppo package specification & changelog
├── lupus-software-center.desktop  # XDG desktop entry
├── resources.qrc            # Qt resource file (embeds QML + assets)
├── build.rs                 # CXX-Qt build script
├── build-luppo.sh           # Helper script to assemble the .luppo package
├── actions.py               # Luppo post-install/remove action hooks
├── Makefile                 # Convenience build targets
└── Cargo.toml               # Rust manifest
```

---

## Screenshots

> _Screenshots will be added in a future update._

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and run `cargo check && cargo test`
4. Commit and push, then open a Pull Request

Please make sure `cargo check` and `cargo test` pass with **0 errors and 0 failures** before submitting.

---

## License

LupuS Software Center is released under the **GNU General Public License v3.0**.  
See the [LICENSE](LICENSE) file for the full text.

---

<div align="center">
Developed with ❤️ by <a href="https://antolun.com">Antolun</a>
</div>
