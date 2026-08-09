# PiSiM (PiSi Market)

A modern, high-performance Software Center built with **PyQt6** for the **LupuS Operating System**, supporting native **PiSi** package management and **Flatpak / FlatHub** applications.

---

## 🌟 Key Features

- 📦 **Dual Package Engine (PiSi & Flatpak)** - Discover, install, update, and remove both native PiSi packages and Flatpak applications.
- 🎨 **Modern & Adaptive Design** - Auto-detects system dark/light modes, features glassmorphism styling, soft gradients, and smooth page transition animations.
- 🌐 **Multi-Language Support (i18n)** - Supports **English** (default) and **Turkish** (`tr`), with automatic system locale detection.
- ⚡ **Asynchronous Background Processing** - Non-blocking multi-threaded architecture (`QThread`) keeps the UI responsive during package loading, repository syncing, and installations.
- 🔄 **Real-Time Progress & Cancellation** - Live percentage progress bars with smooth shimmer effects and instant installation cancellation without data corruption.
- 🖼️ **Screenshot Gallery & Interactive Viewer** - Fetches high-resolution app screenshots from FlatHub API with full-screen zoom, pan, and reset dialog.
- 🔍 **Instant Search & Categorization** - Search applications by name, summary, or description across categories (Development, Games, Internet, Multimedia, Graphics, Office, System, Utilities).
- 💾 **Smart Caching Engine** - Fast repository indexing and icon caching system (`~/.cache/pisi-store/`).
- 🔒 **Secure Authorization** - Safe installation and removal using `pkexec` when root privileges are required.

---

## 📁 Project Architecture

```
pisim/
├── main.py                 # Application entry point & Qt warning filters
├── pisi_store/
│   ├── __init__.py         # Package initialization
│   ├── i18n.py             # Internationalization module (EN/TR auto-detection)
│   ├── backend.py          # PiSi DB/CLI & Flatpak/FlatHub API backend manager
│   ├── mainwindow.py       # Main window & animated views (Discover, Category, Detail, Updates, Search)
│   ├── settings.py         # Application settings functions
│   ├── widgets.py          # UI components (PisiAppCard, TrendingAppCard, PisiInstallWidget, ImageViewerDialog)
│   └── assets/             # Branding icons and image resources
├── actions.py              # PiSi package build actions
├── build-pisi.sh           # PiSi package build script
├── Makefile                # Build and run commands
├── pspec.xml               # PiSi package specification
├── com.teknoanka.pisim.desktop           # Desktop menu entry
├── LICENSE                 # License
└── README.md               # Project documentation
```

---

## 🛠️ Prerequisites & Installation

### Requirements

- Python 3.10+
- PyQt6
- `flatpak` *(optional, for Flatpak/FlatHub support)*
- `pisi`

### Install Dependencies

```bash
# Via pip
pip3 install PyQt6
```

---

## 🚀 Run & Package Application

### Run Directly
```bash
python3 main.py
# or
make run
```

### Build PiSi Package (.pisi)
```bash
sudo ./build-pisi.sh
# or
sudo make package
```

### Install Built PiSi Package
```bash
sudo pisi install pisim-*.pisi
```

---

## 💡 How It Works

1. **Language Detection**: Automatically inspects system locale (`QLocale`, `locale`, `LANG` environment variable). Defaults to **English** unless Turkish is detected.
2. **Backend Sync**: Scans local PiSi database `/var/lib/pisi/index/` and `flatpak remote-ls`.
3. **FlatHub Integration**: Uses FlatHub API v2 to fetch app descriptions, developer metadata, popularity metrics, and screenshot galleries.
4. **Execution Safety**: Commands needing root privileges execute via `pkexec pisi`.

---

## 📄 License

Developed for the **LupuS Operating System** community by **TeknoAnka**. Licensed under **GPL-3.0**.
