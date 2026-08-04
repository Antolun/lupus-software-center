# 🐺 LupuS PiSiM (PiSi Market)

A modern, high-performance Software Center built with **PyQt6** for the **LupuS Operating System**, supporting native **PiSi** package management and **Flatpak / Flathub** applications.

---

## 🌟 Key Features

- 📦 **Dual Package Engine (PiSi & Flatpak)** - Discover, install, update, and remove both native PiSi packages and Flatpak applications.
- 🎨 **Modern & Adaptive Design** - Auto-detects system dark/light modes, features glassmorphism styling, soft gradients, and smooth page transition animations.
- 🌐 **Multi-Language Support (i18n)** - Supports **English** (default) and **Turkish** (`tr`), with automatic system locale detection.
- ⚡ **Asynchronous Background Processing** - Non-blocking multi-threaded architecture (`QThread`) keeps the UI responsive during package loading, repository syncing, and installations.
- 🔄 **Real-Time Progress & Cancellation** - Live percentage progress bars with smooth shimmer effects and instant installation cancellation without data corruption.
- 🖼️ **Screenshot Gallery & Interactive Viewer** - Fetches high-resolution app screenshots from Flathub API with full-screen zoom, pan, and reset dialog.
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
│   ├── backend.py          # PiSi DB/CLI & Flatpak/Flathub API backend manager
│   ├── mainwindow.py       # Main window & animated views (Discover, Category, Detail, Updates, Search)
│   ├── widgets.py          # UI components (PisiAppCard, TrendingAppCard, PisiInstallWidget, ImageViewerDialog)
│   └── assets/             # Branding icons and image resources
└── README.md               # Project documentation
```

---

## 🛠️ Prerequisites & Installation

### Requirements

- Python 3.10+
- PyQt6
- `flatpak` *(optional, for Flatpak/Flathub support)*
- `pisi` *(optional, for native PiSi package management; fallback demo mode enabled if unavailable)*

### Install Dependencies

```bash
# Via pip
pip install PyQt6

# Or via PiSi package manager on LupuS OS
pisi install python3-pyqt6
```

---

## 🚀 Running the Application

```bash
# Run PiSiM
python3 main.py
```

### Force Language Override (Optional)

```bash
# Force English
LANG=en_US.UTF-8 python3 main.py

# Force Turkish
LANG=tr_TR.UTF-8 python3 main.py
```

---

## 💡 How It Works

1. **Language Detection**: Automatically inspects system locale (`QLocale`, `locale`, `LANG` environment variable). Defaults to **English** unless Turkish is detected.
2. **Backend Sync**: Scans local PiSi database `/var/lib/pisi/index/` and `flatpak remote-ls`.
3. **Flathub Integration**: Uses Flathub API v2 to fetch app descriptions, developer metadata, popularity metrics, and screenshot galleries.
4. **Execution Safety**: Commands needing root privileges execute via `pkexec pisi`.

---

## 📄 License

Developed for the **LupuS Operating System** community by **TeknoAnka**. Licensed under **GPL-3.0**.
