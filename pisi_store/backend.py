"""
Pisi Store Backend - LupuS İşletim Sistemi ve PiSi Paket Yöneticisi Veri Sağlayıcısı
"""

import subprocess
import os
import xml.etree.ElementTree as ET
import lzma
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

CACHE_DIR = Path.home() / ".cache" / "pisi-store"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

ICON_CACHE_DIR = CACHE_DIR / "icons"
ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)

INDEX_CACHE_FILE = CACHE_DIR / "pisi-index.json"
INDEX_CACHE_TTL = 3600  # 1 saat

# Freedesktop ikonu arama yolları
ICON_SEARCH_PATHS = [
    "/usr/share/icons/hicolor/scalable/apps",
    "/usr/share/icons/hicolor/256x256/apps",
    "/usr/share/icons/hicolor/128x128/apps",
    "/usr/share/icons/hicolor/64x64/apps",
    "/usr/share/icons/hicolor/48x48/apps",
    "/usr/share/icons/hicolor/32x32/apps",
    "/usr/share/icons/Papirus/64x64/apps",
    "/usr/share/icons/Papirus/48x48/apps",
    "/usr/share/icons/Papirus/32x32/apps",
    "/usr/share/pixmaps",
    "/usr/share/icons",
    # Flatpak uygulama ikonları
    "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/64x64/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/48x48/apps",
    os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/scalable/apps"),
    os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/64x64/apps"),
    os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/48x48/apps"),
]

ICON_EXTENSIONS = [".png", ".xpm", ".jpg", ".svg"]


@dataclass
class PackageInfo:
    """Paket bilgisi veri sınıfı"""
    name: str
    display_name: str = ""
    version: str = ""
    release: str = ""
    summary: str = ""
    description: str = ""
    license: str = "GPL-3.0"
    homepage: str = ""
    packager_name: str = "LupuS Topluluğu"
    packager_email: str = "packager@lupus-os.org"
    developer: str = "Özgür Yazılım Geliştiricileri"
    category: str = "utilities"
    component: str = "main"
    is_a: str = "app:gui"
    icon_name: str = ""
    icon_path: str = ""
    installed: bool = False
    has_update: bool = False
    new_version: str = ""
    rating: float = 4.5
    downloads: int = 15200
    download_size: str = "12.4 MB"
    installed_size: str = "38.5 MB"
    dependencies_count: int = 5
    tags: list = field(default_factory=list)
    is_flatpak: bool = False
    origin: str = "Pisi"
    screenshots: list = field(default_factory=list)

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name.capitalize()


from .i18n import tr

# LupuS Store Kategori Eşleştirmeleri
def get_lupus_categories():
    return {
        "all": {"name": tr("nav_discover"), "icon": "plasma-search"},
        "development": {"name": tr("nav_development"), "icon": "applications-development"},
        "education": {"name": tr("nav_education"), "icon": "applications-education"},
        "enterprise": {"name": tr("nav_enterprise"), "icon": "applications-office"},
        "games": {"name": tr("nav_games"), "icon": "applications-games"},
        "graphics": {"name": tr("nav_graphics"), "icon": "applications-graphics"},
        "internet": {"name": tr("nav_internet"), "icon": "applications-internet"},
        "multimedia": {"name": tr("nav_multimedia"), "icon": "applications-multimedia"},
        "office": {"name": tr("nav_office"), "icon": "applications-office"},
        "system": {"name": tr("nav_system"), "icon": "applications-system"},
        "utilities": {"name": tr("nav_utilities"), "icon": "applications-utilities"},
        "flatpak": {"name": tr("nav_flatpak"), "icon": "package-x-generic"},
    }

LUPUS_CATEGORIES = get_lupus_categories()





class PisiBackend:
    """PiSi paket yöneticisi ile etkileşim sınıfı"""

    def __init__(self):
        self._installed_packages: dict[str, PackageInfo] = {}
        self._available_packages: dict[str, PackageInfo] = {}
        self._pisi_available = self._check_pisi()
        self._flatpak_available = self._check_flatpak()
        self._flatpak_loaded = False

    def _check_pisi(self) -> bool:
        """Pisi paket yöneticisinin kullanılabilir olup olmadığını kontrol eder.
        CLI komutu Python sürüm uyumsuzluğu nedeniyle çalışmayabilir,
        bu yüzden doğrudan XML index dosyasını da kontrol eder."""
        # Önce doğrudan index XML dosyasını kontrol et
        import glob as _glob
        index_files = _glob.glob("/var/lib/pisi/index/**/*.xml", recursive=True)
        if index_files:
            return True
        # Sonra CLI'yi dene
        try:
            result = subprocess.run(
                ["pisi", "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_pisi_available(self) -> bool:
        return self._pisi_available

    def _check_flatpak(self) -> bool:
        """Sistemde flatpak yüklü olup olmadığını kontrol eder."""
        try:
            result = subprocess.run(
                ["flatpak", "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_flatpak_available(self) -> bool:
        return self._flatpak_available

    def _flatpak_category_map(self, categories_str: str) -> str:
        """Flatpak AppStream kategorisini dahili kategori kimliğine dönüştürür."""
        mapping = {
            "AudioVideo": "multimedia",
            "Audio": "multimedia",
            "Video": "multimedia",
            "Development": "development",
            "Education": "education",
            "Game": "games",
            "Graphics": "graphics",
            "Network": "internet",
            "Office": "office",
            "Science": "education",
            "System": "system",
            "Utility": "utilities",
        }
        for part in categories_str.split(";"):
            part = part.strip()
            if part in mapping:
                return mapping[part]
        return "utilities"

    def _load_flatpaks(self):
        """Sistemde kurulu ve depodaki Flatpak uygulamalarını yükler."""
        if not self._flatpak_available:
            return
        self._load_installed_flatpaks()
        if not self._flatpak_loaded:
            self._load_available_flatpaks()
            self._flatpak_loaded = True

    def _load_installed_flatpaks(self):
        """Kurulu Flatpak uygulamalarını listeler."""
        try:
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application,name,version,branch,origin"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0 or not result.stdout.strip():
                return
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("\t")]
                if len(parts) < 2:
                    continue
                app_id = parts[0]
                display_name = parts[1] if len(parts) > 1 else app_id
                version = parts[2] if len(parts) > 2 else ""
                origin = parts[4].capitalize() if len(parts) > 4 and parts[4] else "FlatHub"
                key = f"flatpak:{app_id}"
                icon_name = app_id.split(".")[-1].lower()
                icon_path = self._find_flatpak_icon(app_id)
                cat = self._get_flatpak_category(app_id)
                pkg = PackageInfo(
                    name=key,
                    display_name=display_name,
                    version=version,
                    summary=f"{origin} · {app_id}",
                    description=f"{display_name} uygulaması Flatpak ({origin}) aracılığıyla kurulmuştur.",
                    category=cat,
                    icon_name=icon_name,
                    icon_path=icon_path,
                    installed=True,
                    is_flatpak=True,
                    origin=origin
                )
                self._installed_packages[key] = pkg
        except Exception as e:
            print(f"Flatpak kurulu paket listesi hatası: {e}")

    def _fetch_flathub_popularity(self) -> dict[str, tuple[int, int, str]]:
        """Flathub API'sinden popülerlik (sıralama, son ayki indirilme sayısı ve ikon URL'si) verilerini çeker."""
        popular_info = {}
        try:
            url = "https://flathub.org/api/v2/collection/popular?page=1&per_page=250"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    hits = data.get("hits", [])
                    for idx, item in enumerate(hits):
                        app_id = item.get("app_id")
                        installs = item.get("installs_last_month", 0)
                        icon_url = item.get("icon", "")
                        if app_id:
                            popular_info[app_id] = (idx + 1, installs, icon_url)
        except Exception as e:
            print(f"Flathub popülerlik listesi alma hatası: {e}")
        return popular_info

    def _get_or_download_flathub_icon(self, icon_url: str) -> str:
        """Flathub ikon URL'sini yerel önbelleğe indirir ve dosya yolunu döndürür."""
        if not icon_url:
            return ""
        try:
            icon_hash = hashlib.md5(icon_url.encode('utf-8')).hexdigest()
            ext = os.path.splitext(icon_url.split('?')[0])[1] or ".png"
            cached_path = ICON_CACHE_DIR / f"{icon_hash}{ext}"
            if not cached_path.exists():
                ic_req = urllib.request.Request(icon_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(ic_req, timeout=5) as ic_resp:
                    with open(cached_path, 'wb') as f:
                        f.write(ic_resp.read())
            return str(cached_path)
        except Exception:
            return ""

    def _load_available_flatpaks(self):
        """Flatpak remote'larındaki mevcut uygulamaları listeler ve Flathub popülerliğine göre sıralar."""
        try:
            result = subprocess.run(
                ["flatpak", "remote-ls", "--app", "--columns=application,name,version,origin"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0 or not result.stdout.strip():
                return

            pop_info = self._fetch_flathub_popularity()
            flatpak_pkgs = []

            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("\t")]
                if len(parts) < 1:
                    continue
                app_id = parts[0]
                display_name = parts[1] if len(parts) > 1 else app_id
                version = parts[2] if len(parts) > 2 else ""
                origin = parts[3].capitalize() if len(parts) > 3 and parts[3] else "FlatHub"
                key = f"flatpak:{app_id}"
                if key in self._available_packages:
                    continue
                icon_name = app_id.split(".")[-1].lower()
                icon_path = self._find_flatpak_icon(app_id)
                cat = self._get_flatpak_category(app_id)

                pop_tuple = pop_info.get(app_id)
                if pop_tuple:
                    rank, downloads, icon_url = pop_tuple
                    if icon_url:
                        icon_path = self._get_or_download_flathub_icon(icon_url)
                else:
                    rank, downloads = 9999, 0

                pkg = PackageInfo(
                    name=key,
                    display_name=display_name,
                    version=version,
                    summary=f"{origin} · {app_id}",
                    description=f"{display_name} uygulaması Flatpak ({origin}) ile kurulabilir.",
                    category=cat,
                    icon_name=icon_name,
                    icon_path=icon_path,
                    installed=False,
                    is_flatpak=True,
                    origin=origin,
                    downloads=downloads
                )
                flatpak_pkgs.append((rank, pkg))

            # Flathub popülerlik sıralamasına göre diz (önce popüler olanlar, rank 1..N)
            flatpak_pkgs.sort(key=lambda x: x[0])

            for _, pkg in flatpak_pkgs:
                self._available_packages[pkg.name] = pkg

        except Exception as e:
            print(f"Flatpak depo listesi hatası: {e}")

    def fetch_flathub_info(self, app_id: str) -> dict:
        """FlatHub API (v2) üzerinden uygulamanın ikon, açıklama ve ekran görüntülerini indirir."""
        real_id = app_id.removeprefix("flatpak:")
        api_url = f"https://flathub.org/api/v2/appstream/{real_id}"
        req = urllib.request.Request(
            api_url,
            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    icon_url = data.get("icon")
                    summary = data.get("summary")
                    description = data.get("description")
                    developer = data.get("developer_name")
                    screenshots_data = data.get("screenshots", [])

                    screenshots = []
                    for sc in screenshots_data:
                        if isinstance(sc, dict):
                            # Öncelik 1: Orijinal/Desktop yüksek çözünürlüklü görsel
                            if sc.get("desktop"):
                                screenshots.append(sc.get("desktop"))
                            elif sc.get("sizes") and isinstance(sc.get("sizes"), list):
                                # Öncelik 2: En büyük boyutu seç (genellikle son eleman)
                                sizes = sc.get("sizes")
                                max_size_url = max(sizes, key=lambda s: s.get("width", 0) if isinstance(s, dict) else 0).get("src") if isinstance(sizes[0], dict) else sizes[-1]
                                if isinstance(max_size_url, str):
                                    screenshots.append(max_size_url)
                                elif isinstance(sizes[-1], dict) and sizes[-1].get("src"):
                                    screenshots.append(sizes[-1].get("src"))
                            elif sc.get("src"):
                                screenshots.append(sc.get("src"))
                        elif isinstance(sc, str):
                            screenshots.append(sc)

                    local_screenshots = []
                    for sc_url in screenshots[:4]:
                        if not sc_url:
                            continue
                        try:
                            sc_hash = hashlib.md5(sc_url.encode('utf-8')).hexdigest()
                            sc_ext = os.path.splitext(sc_url.split('?')[0])[1] or ".png"
                            cached_sc_path = ICON_CACHE_DIR / f"sc_{sc_hash}{sc_ext}"
                            if not cached_sc_path.exists():
                                sc_req = urllib.request.Request(sc_url, headers={'User-Agent': 'Mozilla/5.0'})
                                with urllib.request.urlopen(sc_req, timeout=5) as sc_resp:
                                    with open(cached_sc_path, 'wb') as f:
                                        f.write(sc_resp.read())
                            local_screenshots.append(str(cached_sc_path))
                        except Exception as e:
                            print(f"Ekran görüntüsü indirme hatası: {e}")

                    local_icon = ""
                    if icon_url:
                        icon_hash = hashlib.md5(icon_url.encode('utf-8')).hexdigest()
                        ext = os.path.splitext(icon_url.split('?')[0])[1] or ".png"
                        cached_path = ICON_CACHE_DIR / f"{icon_hash}{ext}"
                        if not cached_path.exists():
                            ic_req = urllib.request.Request(icon_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(ic_req, timeout=5) as ic_resp:
                                with open(cached_path, 'wb') as f:
                                    f.write(ic_resp.read())
                        local_icon = str(cached_path)

                    return {
                        "icon_url": icon_url,
                        "local_icon": local_icon,
                        "summary": summary,
                        "description": description,
                        "developer": developer,
                        "screenshots": local_screenshots
                    }
        except Exception as e:
            print(f"FlatHub API hatası ({real_id}): {e}")
        return {}

    def _find_flatpak_icon(self, app_id: str) -> str:
        """Flatpak uygulama ikonunu sistemde arar."""
        icon_dirs = [
            f"/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
            f"/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps",
            f"/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps",
            f"/var/lib/flatpak/exports/share/icons/hicolor/64x64/apps",
            os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/scalable/apps"),
            os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/64x64/apps"),
        ]
        for d in icon_dirs:
            for ext in ICON_EXTENSIONS:
                p = os.path.join(d, app_id + ext)
                if os.path.exists(p):
                    return p
        # Fallback: app name kısmı
        short = app_id.split(".")[-1]
        return self._find_icon(short)

    def _get_flatpak_category(self, app_id: str) -> str:
        """Flatpak uygulama ID'sinden kategori tahmini yapar."""
        lower = app_id.lower()
        if any(k in lower for k in ["game", "chess", "tux", "minetest", "openarena"]):
            return "games"
        if any(k in lower for k in ["code", "studio", "ide", "builder", "eclipse"]):
            return "development"
        if any(k in lower for k in ["video", "audio", "media", "vlc", "kodi", "spotify", "rhythmbox", "clementine"]):
            return "multimedia"
        if any(k in lower for k in ["chrome", "firefox", "browser", "telegram", "signal", "discord", "thunderbird"]):
            return "internet"
        if any(k in lower for k in ["gimp", "inkscape", "krita", "darktable", "rawtherapee"]):
            return "graphics"
        if any(k in lower for k in ["office", "writer", "calc", "impress", "libreoffice", "onlyoffice"]):
            return "office"
        if any(k in lower for k in ["edu", "learn", "school", "math", "science"]):
            return "education"
        if any(k in lower for k in ["system", "manager", "monitor", "tweaks", "settings"]):
            return "system"
        return "utilities"

    def install_flatpak(self, app_id: str) -> tuple[bool, str]:
        """Flatpak uygulaması kurar. app_id 'flatpak:<ID>' formatındadır."""
        real_id = app_id.removeprefix("flatpak:")
        try:
            result = subprocess.run(
                ["flatpak", "install", "--noninteractive", "--assumeyes", real_id],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                key = f"flatpak:{real_id}"
                if key in self._available_packages:
                    self._available_packages[key].installed = True
                    self._installed_packages[key] = self._available_packages[key]
                return True, f"{real_id} başarıyla kuruldu"
            else:
                return False, result.stderr or "Flatpak kurulum başarısız"
        except Exception as e:
            return False, str(e)

    def remove_flatpak(self, app_id: str) -> tuple[bool, str]:
        """Flatpak uygulaması kaldırır. app_id 'flatpak:<ID>' formatındadır."""
        real_id = app_id.removeprefix("flatpak:")
        try:
            result = subprocess.run(
                ["flatpak", "uninstall", "--noninteractive", "--assumeyes", real_id],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                key = f"flatpak:{real_id}"
                if key in self._installed_packages:
                    del self._installed_packages[key]
                if key in self._available_packages:
                    self._available_packages[key].installed = False
                return True, f"{real_id} başarıyla kaldırıldı"
            else:
                return False, result.stderr or "Flatpak kaldırma başarısız"
        except Exception as e:
            return False, str(e)

    def check_flatpak_updates(self) -> list[str]:
        """Güncellenebilir Flatpak uygulamalarını döndürür."""
        if not self._flatpak_available:
            return []
        try:
            result = subprocess.run(
                ["flatpak", "remote-ls", "--updates", "--app", "--columns=application"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return []
            upgradable = []
            for line in result.stdout.strip().splitlines():
                app_id = line.strip()
                if app_id:
                    key = f"flatpak:{app_id}"
                    upgradable.append(key)
                    if key in self._installed_packages:
                        self._installed_packages[key].has_update = True
                    if key in self._available_packages:
                        self._available_packages[key].has_update = True
            return upgradable
        except Exception as e:
            print(f"Flatpak güncelleme kontrolü hatası: {e}")
            return []

    def get_installed_packages(self) -> dict[str, PackageInfo]:
        if self._installed_packages:
            self._load_flatpaks()
            return self._installed_packages
        self._load_installed_packages()
        self._load_flatpaks()
        return self._installed_packages

    def _load_installed_packages(self):
        """Kurulu paketleri pisi veritabanından okur."""
        # Önce pisi Python API'si ile dene
        if self._load_installed_from_pisi_db():
            return
        # CLI dene (Python 3.14 ile kırık olabilir, ama deneyelim)
        try:
            result = subprocess.run(
                ["pisi", "list-installed", "--long"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0 and result.stdout.strip():
                self._parse_pisi_list_output(result.stdout, installed=True)
                return
        except Exception as e:
            print(f"PiSi list-installed hatası: {e}")
        # Kurulu paket bulunamadı — _available_packages'ı kirletmemek için
        # burada demo yükleme yapmıyoruz; demo yalnızca available_packages boşsa çalışır.

    def _load_installed_from_pisi_db(self) -> bool:
        """pisi Python API'si üzerinden kurulu paket listesini çeker."""
        try:
            import pisi.db.installdb as idb
            import pisi.db.packagedb as pdb
            install_db = idb.InstallDB()
            package_db = pdb.PackageDB()
            installed_names = list(install_db.list_installed())
            if not installed_names:
                return False
            for name in installed_names:
                try:
                    pkg_obj = install_db.get_package(name)
                    summary = getattr(pkg_obj, 'summary', '') or ''
                    description = getattr(pkg_obj, 'description', '') or ''
                    version = ''
                    hist = getattr(pkg_obj, 'history', None)
                    if hist:
                        upd = hist[0] if hist else None
                        if upd:
                            version = getattr(upd, 'version', '') or ''
                    part_of = getattr(pkg_obj, 'partOf', '') or ''
                    icon = getattr(pkg_obj, 'icon', '') or ''
                    cat = self._map_to_category(name, part_of=part_of, summary=str(summary))
                    icon_path = self._find_icon(str(icon) if icon else name)
                    pkg = PackageInfo(
                        name=name,
                        display_name=name.capitalize() if name.islower() else name,
                        summary=str(summary)[:120] if summary else '',
                        description=str(description) if description else '',
                        version=str(version) if version else '',
                        category=cat,
                        icon_name=str(icon) if icon else name,
                        icon_path=icon_path,
                        installed=True,
                    )
                    self._installed_packages[name] = pkg
                except Exception as e:
                    print(f"Paket bilgisi alınamadı ({name}): {e}")
            return len(self._installed_packages) > 0
        except Exception as e:
            print(f"Pisi InstallDB hatası: {e}")
            return False

    def _parse_pisi_list_output(self, output: str, installed: bool = False):
        lines = output.strip().split("\n")
        current_pkg = None

        for line in lines:
            if not line.strip():
                continue

            if line.startswith(" ") or line.startswith("\t"):
                if current_pkg:
                    stripped = line.strip()
                    if stripped.startswith("Summary:"):
                        current_pkg.summary = stripped.replace("Summary:", "").strip()
                    elif stripped.startswith("Description:"):
                        current_pkg.description = stripped.replace("Description:", "").strip()
            else:
                parts = line.split(" - ", 1)
                if parts:
                    name = parts[0].strip()
                    if name:
                        current_pkg = PackageInfo(name=name)
                        if len(parts) > 1:
                            current_pkg.version = parts[1].strip()
                        current_pkg.installed = installed
                        current_pkg.icon_path = self._find_icon(name)
                        current_pkg.category = self._map_to_category(name)

                        if installed:
                            self._installed_packages[name] = current_pkg
                        else:
                            self._available_packages[name] = current_pkg

    def _map_to_category(self, name: str, part_of: str = "", summary: str = "") -> str:
        p = (part_of or "").lower()
        n = (name or "").lower()
        s = (summary or "").lower()

        if any(x in p for x in ["devel", "code", "prog", "editor", "ide", "git"]) or any(x in n for x in ["code", "studio", "atom", "antigravity", "ide"]):
            return "development"
        if any(x in p for x in ["net", "web", "browser", "mail", "conn", "remote"]) or any(x in n for x in ["chrome", "firefox", "desk", "browser", "telegram"]):
            return "internet"
        if any(x in p for x in ["sound", "video", "tv", "media", "audio"]) or any(x in n for x in ["vlc", "player", "music", "video", "obs"]):
            return "multimedia"
        if any(x in p for x in ["graph", "image", "draw", "pdf"]) or any(x in n for x in ["gimp", "inkscape", "krita", "image"]):
            return "graphics"
        if any(x in p for x in ["game"]) or any(x in n for x in ["game", "steam", "craft", "kart", "tux"]):
            return "games"
        if any(x in p for x in ["office", "word", "calc", "writer"]) or any(x in n for x in ["office", "pdf", "calc"]):
            return "office"
        if any(x in p for x in ["science", "edu", "elec"]) or any(x in n for x in ["arduino", "math"]):
            return "education"
        if any(x in p for x in ["system", "admin", "base", "kernel", "root"]) or any(x in n for x in ["htop", "neofetch", "gparted"]):
            return "system"

        return "utilities"

    def _find_icon(self, icon_name: str) -> str:
        if not icon_name:
            return ""

        for search_path in ICON_SEARCH_PATHS:
            for ext in ICON_EXTENSIONS:
                icon_file = Path(search_path) / f"{icon_name}{ext}"
                if icon_file.exists():
                    return str(icon_file)

        return ""

    def _get_multilang_text(self, element, tag: str, preferred_lang: str = "tr") -> str:
        """Çok dilli XML etiketlerinden tercih edilen dildeki metni döndürür.
        Yoksa İngilizce'yi, o da yoksa ilk bulunanı döndürür."""
        XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
        values = {}
        for child in element:
            if child.tag == tag:
                lang = child.attrib.get(XML_LANG, child.attrib.get("lang", "en"))
                text = (child.text or "").strip()
                if text:
                    values[lang] = text
        return values.get(preferred_lang) or values.get("en") or next(iter(values.values()), "")

    def _load_from_pisi_repo_index(self) -> bool:
        """PiSi deposu indeks XML dosyalarından paketleri ve kategorileri okur."""
        import glob
        import xml.etree.ElementTree as ET

        index_files = (
            glob.glob("/var/lib/pisi/index/**/*.xml", recursive=True)
            + glob.glob("/var/cache/pisi/**/*.xml", recursive=True)
        )
        # Yalnızca gerçek indeks dosyalarını al (.sha1sum vb. hariç)
        index_files = [f for f in index_files if f.endswith(".xml")]
        if not index_files:
            return False

        loaded_count = 0
        for idx_file in index_files:
            try:
                tree = ET.parse(idx_file)
                root = tree.getroot()
                # Paketler root'un doğrudan çocukları olarak da gelebilir
                packages = [c for c in root if c.tag == "Package"]
                if not packages:
                    packages = root.findall(".//Package")

                for p in packages:
                    name = (p.findtext("Name") or "").strip()
                    if not name:
                        continue

                    summary = self._get_multilang_text(p, "Summary")
                    desc = self._get_multilang_text(p, "Description")
                    part_of = (p.findtext("PartOf") or "").strip()
                    icon = (p.findtext("Icon") or "").strip()
                    license_str = (p.findtext("License") or "").strip()
                    installed_size_raw = (p.findtext("InstalledSize") or "0").strip()
                    download_size_raw = (p.findtext("PackageSize") or "0").strip()

                    def _to_mb(raw: str) -> str:
                        try:
                            val = int(raw)
                            if val > 0:
                                mb = round(val / (1024 * 1024), 1)
                                return f"{mb} MB"
                        except (ValueError, TypeError):
                            pass
                        return ""

                    inst_size_str = _to_mb(installed_size_raw)
                    dl_size_str = _to_mb(download_size_raw)

                    version = "1.0.0"
                    hist = p.find("History")
                    if hist is not None:
                        upd = hist.find("Update")
                        if upd is not None:
                            version = (upd.findtext("Version") or "1.0.0").strip()

                    # Bağımlılık sayısını hesapla
                    deps_el = p.find("RuntimeDependencies")
                    dep_count = len(list(deps_el)) if deps_el is not None else 0

                    cat = self._map_to_category(name, part_of=part_of, summary=summary)
                    icon_path = self._find_icon(icon or name)

                    pkg = PackageInfo(
                        name=name,
                        display_name=name.capitalize() if name.islower() else name,
                        summary=summary or desc[:80],
                        description=desc or summary,
                        version=version,
                        category=cat,
                        icon_name=icon or name,
                        icon_path=icon_path,
                        installed_size=inst_size_str,
                        download_size=dl_size_str,
                        license=license_str,
                        dependencies_count=dep_count,
                    )
                    self._available_packages[name] = pkg
                    loaded_count += 1
            except Exception as e:
                print(f"Index XML okuma hatası {idx_file}: {e}")

        return loaded_count > 0

    def load_available_packages(self, progress_callback=None) -> dict[str, PackageInfo]:
        has_pisi_pkgs = any(not pkg.is_flatpak for pkg in self._available_packages.values())
        if has_pisi_pkgs:
            return self._available_packages

        if self._load_index_from_cache():
            if progress_callback:
                progress_callback(100, "Önbellekten yüklendi")
            return self._available_packages

        if self._pisi_available:
            if progress_callback:
                progress_callback(20, "PiSi depolarından paketler yükleniyor...")
            self._load_from_pisi_available(progress_callback)

        if not self._available_packages:
            self._load_demo_packages()

        for name in self._available_packages:
            if name in self._installed_packages:
                self._available_packages[name].installed = True

        self._save_index_to_cache()
        return self._available_packages

    def _load_from_pisi_available(self, progress_callback=None):
        if self._load_from_pisi_repo_index():
            if progress_callback:
                progress_callback(90, "PiSi deposu indeksinden paketler yüklendi.")
            return

        try:
            result = subprocess.run(
                ["pisi", "list-available", "--long"],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                self._parse_pisi_list_output(result.stdout, installed=False)
                for pkg in self._available_packages.values():
                    if not pkg.icon_path:
                        pkg.icon_path = self._find_icon(pkg.icon_name or pkg.name)
            else:
                self._load_demo_packages()

        except Exception as e:
            print(f"Paket yükleme hatası: {e}")
            self._load_demo_packages()

    def _run_pisi_cmd(self, pisi_args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Pisi komutunu çalıştırır. Eğer uygulama root yetkisiyle çalışıyorsa (euid == 0)
        pkexec kullanmadan doğrudan çalıştırır, aksi takdirde pkexec kullanır."""
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd = ["pisi"] + pisi_args
        else:
            cmd = ["pkexec", "pisi"] + pisi_args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def update_repo_and_sync_cache(self, progress_callback=None, update_repo=True) -> bool:
        """Pisi paket yöneticisinin deposunu günceller ve eğer sistemdeki depo
        indekslerinde herhangi bir değişiklik varsa uygulamanın önbelleğini silerek yeniler."""
        if progress_callback:
            if update_repo:
                progress_callback(5, "PiSi depoları güncelleniyor...")
            else:
                progress_callback(5, "Önbellek kontrol ediliyor...")

        # 1. pisi update-repo komutunu çalıştır
        if update_repo:
            try:
                self._run_pisi_cmd(["update-repo"], timeout=25)
            except Exception as e:
                print(f"Pisi depo güncelleme hatası: {e}")

        # 2. Sistemdeki repo xml dosyalarının değiştirilme zamanlarını kontrol et
        import glob
        index_files = (
            glob.glob("/var/lib/pisi/index/**/*.xml", recursive=True)
            + glob.glob("/var/cache/pisi/**/*.xml", recursive=True)
        )
        index_files = [f for f in index_files if f.endswith(".xml")]

        cache_needs_refresh = False
        if not INDEX_CACHE_FILE.exists():
            cache_needs_refresh = True
        elif index_files:
            cache_mtime = INDEX_CACHE_FILE.stat().st_mtime
            for f in index_files:
                try:
                    if os.path.getmtime(f) > cache_mtime:
                        cache_needs_refresh = True
                        break
                except OSError:
                    pass

        # 3. Eğer sistem deposunda güncelleme varsa önbelleği temizle ki yeniden yüklensin
        if cache_needs_refresh and INDEX_CACHE_FILE.exists():
            if progress_callback:
                progress_callback(15, "Depoda değişiklik tespit edildi, önbellek yenileniyor...")
            try:
                INDEX_CACHE_FILE.unlink()
            except Exception as e:
                print(f"Önbellek silme hatası: {e}")

        return cache_needs_refresh

    def check_for_updates(self, progress_callback=None, update_repo=True) -> tuple[int, list[str], str]:
        """Pisi depolarını günceller ve güncellenebilir paketleri tespit eder."""
        error_msg = ""
        upgradable_names = []

        if update_repo:
            if progress_callback:
                progress_callback(10, "PiSi depoları güncelleniyor...")

            if self._pisi_available:
                try:
                    res = self._run_pisi_cmd(["update-repo"], timeout=60)
                    if res.returncode != 0 and res.stderr:
                        print(f"pisi update-repo uyarısı: {res.stderr}")
                except Exception as e:
                    error_msg = str(e)
                    print(f"Pisi update-repo hatası: {e}")

        if progress_callback:
            progress_callback(50, "Güncellemeler kontrol ediliyor...")

        if self._pisi_available:
            try:
                import pisi.db.installdb as idb
                import pisi.db.packagedb as pdb
                install_db = idb.InstallDB()
                package_db = pdb.PackageDB()
                for name in install_db.list_installed():
                    if package_db.has_package(name):
                        try:
                            inst_v, inst_r = install_db.get_version(name)
                            repo_v, repo_r = package_db.get_version(name)
                            if int(repo_r) > int(inst_r):
                                upgradable_names.append(name)
                                if name in self._installed_packages:
                                    self._installed_packages[name].has_update = True
                                    self._installed_packages[name].new_version = repo_v
                                if name in self._available_packages:
                                    self._available_packages[name].has_update = True
                                    self._available_packages[name].new_version = repo_v
                        except (ValueError, TypeError, Exception):
                            pass
            except Exception as e:
                print(f"Pisi DB update check hatası: {e}")

            try:
                result = subprocess.run(
                    ["pisi", "list-upgrades"], capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.splitlines():
                        line = line.strip()
                        if line and " - " in line and not line.startswith("Yükseltilecek"):
                            parts = line.split(" - ", 1)
                            pkg_name = parts[0].strip()
                            if pkg_name not in upgradable_names:
                                upgradable_names.append(pkg_name)
                                if pkg_name in self._installed_packages:
                                    self._installed_packages[pkg_name].has_update = True
                                if pkg_name in self._available_packages:
                                    self._available_packages[pkg_name].has_update = True
            except Exception as e:
                print(f"Pisi CLI list-upgrades hatası: {e}")
        else:
            # Demo modu simülasyonu
            installed_pkgs = [p for p in self._installed_packages.values() if p.installed]
            if installed_pkgs:
                targets = installed_pkgs[:2]
                for p in targets:
                    p.has_update = True
                    if p.name not in upgradable_names:
                        upgradable_names.append(p.name)

        # Flatpak güncellemelerini de kontrol et
        if self._flatpak_available:
            if progress_callback:
                progress_callback(90, "Flatpak güncellemeleri kontrol ediliyor...")
            flatpak_updates = self.check_flatpak_updates()
            for key in flatpak_updates:
                if key not in upgradable_names:
                    upgradable_names.append(key)

        if progress_callback:
            progress_callback(100, "Güncelleme kontrolü tamamlandı.")

        return len(upgradable_names), upgradable_names, error_msg

    def is_cache_valid(self) -> bool:
        """Önbellek geçerli mi kontrol eder (TTL süresi dolmamış ve dosya var)."""
        if not INDEX_CACHE_FILE.exists():
            return False
        import time
        file_age = time.time() - INDEX_CACHE_FILE.stat().st_mtime
        return file_age <= INDEX_CACHE_TTL

    def _load_index_from_cache(self) -> bool:
        if not INDEX_CACHE_FILE.exists():
            return False

        import time
        file_age = time.time() - INDEX_CACHE_FILE.stat().st_mtime
        if file_age > INDEX_CACHE_TTL:
            return False

        try:
            with open(INDEX_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            for pkg_data in data:
                # Önbellekteki PiSi paketlerinin is_flatpak değerini temin et
                pkg_data["is_flatpak"] = False
                pkg = PackageInfo(**pkg_data)
                self._available_packages[pkg.name] = pkg

            return len(self._available_packages) > 0
        except Exception:
            return False

    def _save_index_to_cache(self):
        try:
            # Sadece PiSi paketlerini önbelleğe kaydet
            data = [pkg.__dict__ for pkg in self._available_packages.values() if not pkg.is_flatpak]
            with open(INDEX_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Önbellek kaydetme hatası: {e}")

    def _load_demo_packages(self):
        """LupuS PiSiM varsayılan paket listesi"""
        demo = [
            PackageInfo(
                name="google-chrome",
                display_name="Google Chrome",
                version="120.0.6099.109",
                summary="Web Tarayıcısı",
                description="Google Chrome, web ortamını daha hızlı, daha kolay ve daha güvenli hale getirmek için geliştirilmiş modern bir tarayıcıdır.",
                category="internet",
                rating=4.8, downloads=89200, download_size="92.4 MB", installed_size="280 MB",
                has_update=True, new_version="121.0.6167.85",
                icon_name="google-chrome", icon_path=self._find_icon("google-chrome")
            ),
            PackageInfo(
                name="minetest",
                display_name="Minetest",
                version="5.8.0",
                summary="Minecraft Benzeri Blok Oyunu",
                description="Minetest, sonsuz dünyalara sahip açık kaynaklı bir blok oyunu ve oyun motorudur. Kendi dünyanızı kurun ve arkadaşlarınızla oynayın.",
                category="games",
                rating=4.3, downloads=19308, download_size="10.1 MB", installed_size="32.8 MB",
                dependencies_count=13, developer="LupuS Oyun Ekibi",
                icon_name="minetest", icon_path=self._find_icon("minetest")
            ),
            PackageInfo(
                name="wine",
                display_name="Wine",
                version="9.0",
                summary="Windows Uygulamaları Çalıştırıcısı",
                description="Wine, Windows uygulamalarını LupuS işletim sisteminde doğrudan çalıştırmanızı sağlayan uyumluluk katmanıdır.",
                category="utilities",
                rating=4.6, downloads=42100, download_size="48.2 MB", installed_size="190 MB",
                icon_name="wine", icon_path=self._find_icon("wine")
            ),
            PackageInfo(
                name="gameplay-football",
                display_name="Gameplay Football",
                version="0.8.2",
                summary="Futbol Oyunu",
                description="Gameplay Football, fizik tabanlı kontroller sunan 3D açık kaynaklı eğlenceli bir futbol simülasyonudur.",
                category="games",
                rating=4.1, downloads=11400, download_size="65.0 MB", installed_size="140 MB",
                icon_name="applications-games", icon_path=self._find_icon("applications-games")
            ),
            PackageInfo(
                name="supertuxkart",
                display_name="SuperTuxKart",
                version="1.4",
                summary="3D Kart Yarış Oyunu",
                description="SuperTuxKart, farklı pistler ve karakterler içeren eğlenceli açık kaynaklı 3D kart yarış oyunudur.",
                category="games",
                rating=4.7, downloads=31200, download_size="620 MB", installed_size="1.2 GB",
                icon_name="supertuxkart", icon_path=self._find_icon("supertuxkart")
            ),
            PackageInfo(
                name="steam",
                display_name="Steam",
                version="1.0.0.78",
                summary="Dijital Oyun Mağazası",
                description="Steam, Valve tarafından geliştirilen dünyanın en geniş dijital oyun kütüphanesi ve oyuncu topluluğudur.",
                category="games",
                rating=4.9, downloads=128000, download_size="14.2 MB", installed_size="45 MB",
                icon_name="steam", icon_path=self._find_icon("steam")
            ),
            PackageInfo(
                name="firefox",
                display_name="Mozilla Firefox",
                version="121.0",
                summary="Özgür Web Tarayıcısı",
                description="Mozilla Firefox, gizlilik odaklı, hızlı ve tamamen özelleştirilebilir açık kaynaklı web tarayıcısıdır.",
                category="internet",
                rating=4.8, downloads=105000, download_size="78.5 MB", installed_size="230 MB",
                icon_name="firefox", icon_path=self._find_icon("firefox")
            ),
            PackageInfo(
                name="brave",
                display_name="Brave Browser",
                version="1.61.101",
                summary="Gizlilik Odaklı Web Tarayıcısı",
                description="Brave, reklamları ve izleyicileri otomatik engelleyen ultra hızlı bir web tarayıcısıdır.",
                category="internet",
                rating=4.7, downloads=54000, download_size="95.0 MB", installed_size="290 MB",
                icon_name="brave-browser", icon_path=self._find_icon("brave-browser")
            ),
            PackageInfo(
                name="vlc",
                display_name="VLC Media Player",
                version="3.0.20",
                summary="Çok Amaçlı Medya Oynatıcı",
                description="VLC, tüm medya formatlarını ve akış protokollerini ek kodek gerektirmeden oynatan ücretsiz bir medya istemcisidir.",
                category="multimedia",
                rating=4.9, downloads=142000, download_size="38.0 MB", installed_size="110 MB",
                icon_name="vlc", icon_path=self._find_icon("vlc")
            ),
            PackageInfo(
                name="gimp",
                display_name="GIMP",
                version="2.10.36",
                summary="Görüntü Düzenleme Programı",
                description="GIMP, fotoğraf rötuşlama, resim bileşimi ve görsel oluşturma için kullanılan açık kaynaklı grafik editörüdür.",
                category="graphics",
                rating=4.7, downloads=68000, download_size="145 MB", installed_size="420 MB",
                icon_name="gimp", icon_path=self._find_icon("gimp")
            ),
            PackageInfo(
                name="libreoffice",
                display_name="LibreOffice",
                version="7.6.4",
                summary="Gelişmiş Ofis Paketi",
                description="Kelime işlemci, tablo düzenleyici, sunum hazırlayıcı ve veritabanı içeren güçlü açık kaynaklı ofis paketi.",
                category="office",
                rating=4.8, downloads=98000, download_size="240 MB", installed_size="680 MB",
                icon_name="libreoffice-startcenter", icon_path=self._find_icon("libreoffice-startcenter")
            ),
            PackageInfo(
                name="vscode",
                display_name="Visual Studio Code",
                version="1.85.2",
                summary="Kod Editörü",
                description="Gelişmiş eklenti desteği, Git entegrasyonu ve IntelliSense ile donatılmış modern kod geliştirme ortamı.",
                category="development",
                rating=4.9, downloads=115000, download_size="88.0 MB", installed_size="310 MB",
                icon_name="com.visualstudio.code", icon_path=self._find_icon("com.visualstudio.code")
            ),
            PackageInfo(
                name="thunderbird",
                display_name="Mozilla Thunderbird",
                version="115.6.0",
                summary="E-posta İstemcisi",
                description="E-posta, takvim ve kişileri tek bir yerde güvenle yönetmenizi sağlayan masaüstü istemcisi.",
                category="internet",
                rating=4.5, downloads=34000, download_size="64.0 MB", installed_size="180 MB",
                icon_name="thunderbird", icon_path=self._find_icon("thunderbird")
            ),
            PackageInfo(
                name="filezilla",
                display_name="FileZilla",
                version="3.66.4",
                summary="FTP/SFTP İstemcisi",
                description="Dosya transferi için kullanılan güvenilir ve hızlı grafik arayüzlü FTP istemcisi.",
                category="internet",
                rating=4.6, downloads=28000, download_size="18.5 MB", installed_size="52 MB",
                icon_name="filezilla", icon_path=self._find_icon("filezilla")
            ),
            PackageInfo(
                name="obs-studio",
                display_name="OBS Studio",
                version="30.0.2",
                summary="Ekran Kayıt ve Canlı Yayın Programı",
                description="Yüksek kalitede ekran kaydı yapabileceğiniz ve canlı yayınlar gerçekleştirebileceğiniz profesyonel yazılım.",
                category="multimedia",
                rating=4.9, downloads=76000, download_size="110 MB", installed_size="340 MB",
                icon_name="com.obsproject.Studio", icon_path=self._find_icon("com.obsproject.Studio")
            ),
            PackageInfo(
                name="kdenlive",
                display_name="Kdenlive",
                version="23.08.4",
                summary="Çok Parçalı Video Editörü",
                description="Video kurgulama, özel efekt ekleme ve ses senkronizasyonu sağlayan profesyonel video editörü.",
                category="multimedia",
                rating=4.6, downloads=29000, download_size="125 MB", installed_size="390 MB",
                icon_name="kdenlive", icon_path=self._find_icon("kdenlive")
            ),
            PackageInfo(
                name="blender",
                display_name="Blender",
                version="4.0.2",
                summary="3D Modelleme ve Animasyon",
                description="3D modelleme, kaplama, animasyon ve render için kullanılan dünya standartlarında açık kaynak yazılım.",
                category="graphics",
                rating=4.9, downloads=64000, download_size="310 MB", installed_size="890 MB",
                icon_name="blender", icon_path=self._find_icon("blender")
            ),
            PackageInfo(
                name="gparted",
                display_name="GParted",
                version="1.5.0",
                summary="Disk Bölümleme Aracı",
                description="Sabit disklerinizi biçimlendirme, bölümleme ve boyutlandırma işlemlerini grafik ortamda yönetin.",
                category="system",
                rating=4.7, downloads=48000, download_size="12.0 MB", installed_size="36 MB",
                icon_name="gparted", icon_path=self._find_icon("gparted")
            ),
            PackageInfo(
                name="htop",
                display_name="htop",
                version="3.3.0",
                summary="Terminal Süreç Takip Aracı",
                description="Sistem işlemcisi, bellek kullanımı ve çalışan süreçleri anlık olarak izleyen terminal aracı.",
                category="system",
                rating=4.8, downloads=52000, download_size="1.8 MB", installed_size="5.2 MB",
                icon_name="htop", icon_path=self._find_icon("htop")
            ),
        ]

        for pkg in demo:
            self._available_packages[pkg.name] = pkg

        for name in ["google-chrome", "firefox", "vlc", "libreoffice", "htop"]:
            if name in self._available_packages:
                self._available_packages[name].installed = True
                self._installed_packages[name] = self._available_packages[name]

    def get_categories(self) -> dict[str, list[str]]:
        categories = {}
        for name, pkg in self._available_packages.items():
            cat = pkg.category or "utilities"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)
        return categories

    def get_categories_info(self) -> list[tuple[str, str, str]]:
        """PiSi deposundaki paketlerden dinamik olarak kategorileri üretir."""
        if not self._available_packages:
            self.load_available_packages()

        category_counts = {}
        for pkg in self._available_packages.values():
            if pkg.is_flatpak:
                continue
            cat = pkg.category or "utilities"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        result = [
            ("all", "plasma-search", tr("nav_discover")),
        ]

        category_meta = {
            "development": ("applications-development", tr("nav_development")),
            "internet": ("applications-internet", tr("nav_internet")),
            "multimedia": ("applications-multimedia", tr("nav_multimedia")),
            "graphics": ("applications-graphics", tr("nav_graphics")),
            "games": ("applications-games", tr("nav_games")),
            "office": ("applications-office", tr("nav_office")),
            "education": ("applications-education", tr("nav_education")),
            "system": ("applications-system", tr("nav_system")),
            "utilities": ("applications-utilities", tr("nav_utilities")),
        }

        for cat_id, count in category_counts.items():
            icon_name, name = category_meta.get(cat_id, ("applications-other", cat_id.capitalize()))
            result.append((cat_id, icon_name, f"{name} ({count})"))

        # Flatpak kategorisini ekle (eğer flatpak varsa ve paket varsa)
        if self._flatpak_available:
            flatpak_count = sum(1 for p in self._available_packages.values() if p.is_flatpak)
            if flatpak_count > 0:
                result.append(("flatpak", "package-x-generic", f"Flatpak ({flatpak_count})"))

        return result



    def get_all_packages(self) -> dict[str, PackageInfo]:
        merged = dict(self._available_packages)
        for k, v in self._installed_packages.items():
            if k in merged:
                merged[k].installed = True
                merged[k].has_update = v.has_update
                if v.new_version:
                    merged[k].new_version = v.new_version
            else:
                merged[k] = v
        return merged

    def install_package(self, package_name: str) -> tuple[bool, str]:
        if not self._pisi_available:
            if package_name in self._available_packages:
                self._available_packages[package_name].installed = True
                self._available_packages[package_name].has_update = False
                self._installed_packages[package_name] = self._available_packages[package_name]
            return True, f"{package_name} başarıyla kuruldu (Demo)"

        try:
            result = self._run_pisi_cmd(["install", "--yes-all", package_name], timeout=300)
            if result.returncode == 0:
                if package_name in self._available_packages:
                    self._available_packages[package_name].installed = True
                    self._installed_packages[package_name] = self._available_packages[package_name]
                return True, f"{package_name} başarıyla kuruldu"
            else:
                return False, result.stderr or "Kurulum başarısız oldu"
        except Exception as e:
            return False, str(e)

    def remove_package(self, package_name: str) -> tuple[bool, str]:
        if not self._pisi_available:
            if package_name in self._installed_packages:
                del self._installed_packages[package_name]
            if package_name in self._available_packages:
                self._available_packages[package_name].installed = False
            return True, f"{package_name} başarıyla kaldırıldı (Demo)"

        try:
            result = self._run_pisi_cmd(["remove", "--yes-all", package_name], timeout=300)
            if result.returncode == 0:
                if package_name in self._installed_packages:
                    del self._installed_packages[package_name]
                if package_name in self._available_packages:
                    self._available_packages[package_name].installed = False
                return True, f"{package_name} başarıyla kaldırıldı"
            else:
                return False, result.stderr or "Kaldırma başarısız oldu"
        except Exception as e:
            return False, str(e)

    def search_packages(self, query: str, packages: dict = None) -> list[PackageInfo]:
        if packages is None:
            packages = self.get_all_packages()
        q = query.lower().strip()
        results = []
        for pkg in packages.values():
            score = 0
            if q in pkg.name.lower() or q in pkg.display_name.lower():
                score += 3
            if q in pkg.summary.lower():
                score += 2
            if q in pkg.description.lower():
                score += 1
            if score > 0:
                results.append((score, pkg))
        results.sort(key=lambda x: x[0], reverse=True)
        return [pkg for _, pkg in results]

    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        if package_name in self._installed_packages:
            return self._installed_packages[package_name]
        if package_name in self._available_packages:
            return self._available_packages[package_name]
        return None
