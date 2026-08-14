# PiSiM — PiSi Market

A modern, fast and lightweight package manager and application store for the [LupuS](https://lupus.antolun.com/) operating system, powered by a Rust backend and a Tauri-based web frontend.

PiSiM lets you install, remove and update both native PiSi packages from the official repositories and Flatpak applications from Flathub, all through a clean and responsive interface that matches the look and feel of the original PyQt6 application.

## Features

- **Rust backend** — high-performance, asynchronous and safe management of PiSi and Flatpak packages.
- **Tauri UI** — a 100% pixel-faithful vanilla HTML/CSS/JS interface that replicates the color palette, typography, icons and layout of the PyQt6 frontend.
- **PiSi & Flatpak support** — install, remove and update packages from PiSi repositories as well as Flatpak applications from Flathub.
- **Live search & category filtering** — instantly search packages and browse them by category.
- **System tray icon** — runs in the background and checks for updates.
- **Internationalization (i18n)** — Turkish and English locales.
- **Dark / light theme** — follows the system theme automatically.

## Requirements

- Rust (stable toolchain)
- Tauri prerequisites ([WebKitGTK, etc.](https://v2.tauri.app/start/prerequisites/))
- `pisi` — only needed to build the native `.pisi` package

## Building & Running

### Development mode

```bash
cargo tauri dev
```

### Production build

```bash
cargo tauri build
```

### Building a PiSi package (.pisi)

```bash
make package
```

This compiles the release binary and invokes `build-pisi.sh`, which produces a `pisim-*.pisi` package in the project root. Alternatively, you can run the steps manually:

```bash
cargo build --release
pisi build pspec.xml --no-sandbox --ignore-dependency
```

### Makefile targets

| Target         | Description                        |
| -------------- | ---------------------------------- |
| `make build`   | Compile the release binary         |
| `make run`     | Run in debug mode                  |
| `make package` | Build the release binary + `.pisi` |
| `make clean`   | Clean the cargo build artifacts    |

## Project Structure

```
├── actions.py          # PiSi package actions (build/handle scripts)
├── build-pisi.sh       # Script that builds the Rust binary and the .pisi package
├── Makefile            # Convenience build targets
├── pisim.desktop       # Desktop entry file
├── pspec.xml           # PiSi package specification
├── src-tauri/          # Rust backend: PiSi/Flatpak integration,
│   └── src/            #   Tauri IPC commands, system tray, i18n, settings
└── ui/                 # Vanilla HTML5, CSS3 and JavaScript frontend + assets
```

## License

PiSiM is released under the [GPLv3](LICENSE) license.
