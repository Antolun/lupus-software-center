# LupuS Software Center — Luppo Market

A modern, fast and lightweight package manager and application store for the [LupuS](https://lupus.antolun.com/) operating system, powered by a Rust backend and a Tauri-based web frontend.

LupuS Software Center lets you install, remove and update both native Luppo packages from the official repositories and Flatpak applications from Flathub, all through a clean and responsive interface that matches the look and feel of the original PyQt6 application.

## Features

- **Rust backend** — high-performance, asynchronous and safe management of Luppo and Flatpak packages.
- **Tauri UI** — a 100% pixel-faithful vanilla HTML/CSS/JS interface that replicates the color palette, typography, icons and layout of the PyQt6 frontend.
- **Luppo & Flatpak support** — install, remove and update packages from Luppo repositories as well as Flatpak applications from Flathub.
- **Live search & category filtering** — instantly search packages and browse them by category.
- **System tray icon** — runs in the background and checks for updates.
- **Internationalization (i18n)** — Turkish and English locales.
- **Dark / light theme** — follows the system theme automatically.

## Requirements

- Rust (stable toolchain)
- Tauri prerequisites ([WebKitGTK, etc.](https://v2.tauri.app/start/prerequisites/))
- `luppo` — only needed to build the native `.luppo` package

## Building & Running

### Development mode

```bash
cargo tauri dev
```

### Production build

```bash
cargo tauri build
```

### Building a Luppo package (.luppo)

```bash
make package
```

This compiles the release binary and invokes `build-luppo.sh`, which produces a `lupus-software-center-*.luppo` package in the project root. Alternatively, you can run the steps manually:

```bash
cargo build --release
luppo build lopec.xml --no-sandbox --ignore-dependency
```

### Makefile targets

| Target         | Description                         |
| -------------- | ----------------------------------- |
| `make build`   | Compile the release binary          |
| `make run`     | Run in debug mode                   |
| `make package` | Build the release binary + `.luppo` |
| `make clean`   | Clean the cargo build artifacts     |

## Project Structure

```
├── lupus-software-center/
│    ├── actions.py                      # Luppo package actions (build/handle scripts)
│    ├── build-luppo.sh                  # Script that builds the Rust binary and the .luppo package
│    ├── Makefile                        # Convenience build targets
│    ├── lupus-software-center.desktop   # Desktop entry file
│    ├── lopec.xml                       # Luppo package specification
│    ├── src-tauri/                      # Rust backend: Luppo/Flatpak integration,
│    │   └── src/                        # Tauri IPC commands, system tray, i18n, settings
│    └── ui/                             # Vanilla HTML5, CSS3 and JavaScript frontend + assets
├── luppo/                               # Required (for luppo-core)
```

## License

LupuS Software Center is released under the [GPLv3](LICENSE) license.
