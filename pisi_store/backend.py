"""
Pisi Store Backend - LupuS İşletim Sistemi ve PiSi Paket Yöneticisi Veri Sağlayıcısı
"""

import subprocess
import os
import xml.etree.ElementTree as ET
import glob
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from .i18n import tr

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
    license: str = ""
    homepage: str = ""
    packager_name: str = ""
    packager_email: str = ""
    developer: str = ""
    category: str = ""
    component: str = "main"
    is_a: str = "app:gui"
    icon_name: str = ""
    icon_path: str = ""
    installed: bool = False
    has_update: bool = False
    new_version: str = ""
    rating: float = 4.5
    downloads: int = 0
    download_size: str = ""
    installed_size: str = ""
    dependencies_count: int = 0
    tags: list = field(default_factory=list)
    is_flatpak: bool = False
    origin: str = "Pisi"
    screenshots: list = field(default_factory=list)
    update_date: str = ""
    vcs_url: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name.capitalize() if self.name.islower() else self.name


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
    """PiSi paket yöneticisi ve Flatpak entegrasyonu backend sınıfı"""

    def __init__(self):
        self._installed_packages: dict[str, PackageInfo] = {}
        self._available_packages: dict[str, PackageInfo] = {}
        self._pisi_available = self._check_pisi()
        self._flatpak_available = self._check_flatpak()
        self._flatpak_loaded = False

    def _check_pisi(self) -> bool:
        """Pisi paket yöneticisinin kullanılabilir olup olmadığını kontrol eder."""
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

    def _load_installed_packages(self):
        """Kurulu paketleri pisi CLI üzerinden okur."""
        if not self._pisi_available:
            return
        try:
            result = subprocess.run(
                ["pisi", "list-installed"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0 and result.stdout.strip():
                self._parse_pisi_list_output(result.stdout, installed=True)
        except Exception as e:
            print(f"PiSi list-installed hatası: {e}")

    def fetch_pisi_screenshots(self, pkg_name: str, display_name: str = "") -> list[str]:
        """PiSi paketlerinin temsilî ekran görüntülerini internetten/AppStream'den çeker ve yerel önbelleğe alır."""
        target_query = display_name or pkg_name
        api_url = "https://flathub.org/api/v2/search"
        payload = json.dumps({"query": target_query}).encode("utf-8")
        req = urllib.request.Request(api_url, data=payload, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
            'Content-Type': 'application/json'
        })
        
        sc_urls = []
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode('utf-8'))
                hits = data.get("hits", [])
                best_id = ""
                for h in hits:
                    aid = h.get("app_id", "")
                    aname = h.get("name", "")
                    if pkg_name.lower() in aid.lower() or pkg_name.lower() in aname.lower():
                        best_id = aid
                        break
                if not best_id and hits:
                    best_id = hits[0].get("app_id")
                    
                if best_id:
                    app_url = f"https://flathub.org/api/v2/appstream/{best_id}"
                    app_req = urllib.request.Request(app_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(app_req, timeout=5) as app_r:
                        app_data = json.loads(app_r.read().decode('utf-8'))
                        scs_data = app_data.get("screenshots", [])
                        for sc in scs_data:
                            if isinstance(sc, dict):
                                if sc.get("desktop"):
                                    sc_urls.append(sc.get("desktop"))
                                elif sc.get("sizes") and isinstance(sc.get("sizes"), list):
                                    sizes = sc.get("sizes")
                                    max_url = max(sizes, key=lambda s: int(s.get("width", 0)) if isinstance(s, dict) and str(s.get("width","0")).isdigit() else 0).get("src") if isinstance(sizes[0], dict) else sizes[-1]
                                    if isinstance(max_url, str):
                                        sc_urls.append(max_url)
                                    elif isinstance(sizes[-1], dict) and sizes[-1].get("src"):
                                        sc_urls.append(sizes[-1].get("src"))
                                elif sc.get("src"):
                                    sc_urls.append(sc.get("src"))
                            elif isinstance(sc, str):
                                sc_urls.append(sc)
        except Exception as e:
            print(f"PiSi ekran görüntüsü arama hatası ({pkg_name}): {e}")
            
        local_paths = []
        for sc_url in sc_urls[:4]:
            if not sc_url:
                continue
            try:
                sc_hash = hashlib.md5(sc_url.encode('utf-8')).hexdigest()
                ext = os.path.splitext(sc_url.split('?')[0])[1] or ".png"
                cached_p = ICON_CACHE_DIR / f"sc_pisi_{sc_hash}{ext}"
                if not cached_p.exists():
                    ic_req = urllib.request.Request(sc_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(ic_req, timeout=5) as ic_resp:
                        with open(cached_p, 'wb') as f:
                            f.write(ic_resp.read())
                local_paths.append(str(cached_p))
            except Exception as e:
                print(f"Ekran görüntüsü indirme hatası: {e}")
                
        return local_paths

    def _get_pisi_pspec_map(self) -> dict[str, str]:
        """PisiLinux GitHub depolarındaki pspec.xml dosya yollarının haritasını yükler/önbellekler."""
        map_file = CACHE_DIR / "pisi-pspec-map.json"
        if map_file.exists():
            try:
                import time
                if time.time() - map_file.stat().st_mtime < 86400:  # 24 saat geçerli
                    with open(map_file, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception:
                pass

        pspec_map = {}
        for repo in ["main", "core"]:
            url = f"https://api.github.com/repos/pisilinux/{repo}/git/trees/master?recursive=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req, timeout=6) as r:
                    data = json.loads(r.read().decode('utf-8'))
                    tree = data.get("tree", [])
                    for item in tree:
                        path = item.get("path", "")
                        if path.endswith("pspec.xml"):
                            parts = path.split("/")
                            pkg_name = parts[-2] if len(parts) >= 2 else ""
                            if pkg_name and (pkg_name not in pspec_map or repo in ["main", "core"]):
                                pspec_map[pkg_name] = f"{repo}/master/{path}"
            except Exception as e:
                print(f"Pisi pspec haritası oluşturma hatası ({repo}): {e}")

        if pspec_map:
            try:
                with open(map_file, "w", encoding="utf-8") as f:
                    json.dump(pspec_map, f, ensure_ascii=False)
            except Exception:
                pass

        return pspec_map

    def _fetch_pisi_repo_details(self, pkg_name: str) -> dict[str, str]:
        """PisiLinux GitHub reposundan paketin gerçek pspec.xml verilerini çeker."""
        pspec_map = self._get_pisi_pspec_map()
        rel_path = pspec_map.get(pkg_name)
        if not rel_path:
            return {}

        raw_url = f"https://raw.githubusercontent.com/pisilinux/{rel_path}"
        try:
            req = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                tree = ET.fromstring(resp.read())
                homepage = tree.findtext("Source/Homepage") or ""
                
                updates = tree.findall("History/Update")
                name, email, date = "", "", ""
                if updates:
                    upd = updates[0]
                    name = (upd.findtext("Name") or "").strip()
                    email = (upd.findtext("Email") or "").strip()
                    date = (upd.findtext("Date") or "").strip()

                if not name or "Community" in name or "Admins" in name:
                    packager = tree.find("Source/Packager")
                    if packager is not None:
                        p_name = (packager.findtext("Name") or "").strip()
                        p_email = (packager.findtext("Email") or "").strip()
                        if p_name and "Community" not in p_name:
                            name = p_name
                        if p_email and "admin@" not in p_email:
                            email = p_email

                return {
                    "packager_name": name,
                    "packager_email": email,
                    "update_date": date,
                    "homepage": homepage
                }
        except Exception as e:
            print(f"Pisi repo detay çekme hatası ({pkg_name}): {e}")
        return {}

    def _enrich_pisi_package_info(self, pkg: PackageInfo):
        """pisi info + pisi depo pspec.xml üzerinden paketin ayrıntılarını ve gerçek paketçi verilerini yükler."""
        if not self._pisi_available or pkg.is_flatpak:
            return
        try:
            # --- pisi info ---
            res = subprocess.run(["pisi", "info", pkg.name], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout:
                for line in res.stdout.splitlines():
                    line_str = line.strip()
                    if not line_str or line_str.startswith("Yüklü paket") or "deposunda bulundu" in line_str or line_str.endswith("bulunamadı."):
                        continue
                    if ":" in line_str:
                        parts = line_str.split(":", 1)
                        key_raw = parts[0].strip()
                        val_raw = parts[1].strip()
                        if "İsim" in key_raw or "Name" in key_raw:
                            if "," in val_raw:
                                for sub in val_raw.split(","):
                                    if ":" in sub:
                                        sk, sv = sub.split(":", 1)
                                        sk, sv = sk.strip(), sv.strip()
                                        if ("sürüm" in sk or "version" in sk) and sv:
                                            pkg.version = sv
                                        elif ("yayım" in sk or "release" in sk) and sv:
                                            pkg.release = sv
                        elif "Özet" in key_raw or "Summary" in key_raw:
                            if val_raw and val_raw != "Açıklama yok":
                                pkg.summary = val_raw
                        elif "Açıklama" in key_raw or "Description" in key_raw:
                            if val_raw:
                                pkg.description = val_raw
                        elif "Lisanslar" in key_raw or "Licenses" in key_raw:
                            if val_raw:
                                pkg.license = val_raw
                        elif "Bileşen" in key_raw or "Component" in key_raw:
                            if val_raw:
                                pkg.component = val_raw
                                pkg.category = self._map_to_category(pkg.name, part_of=val_raw, summary=pkg.summary)
                        elif "Bağımlılıkları" in key_raw or "Dependencies" in key_raw:
                            deps = [d for d in val_raw.split() if d]
                            pkg.dependencies_count = len(deps)
                        elif "Mimari" in key_raw or "Architecture" in key_raw:
                            for sub in val_raw.split(","):
                                if "Yerleşik Boyut" in sub or "Installed Size" in sub:
                                    pkg.installed_size = sub.split(":", 1)[1].strip() if ":" in sub else ""
                                elif "Paket Boyutu" in sub or "Package Size" in sub:
                                    pkg.download_size = sub.split(":", 1)[1].strip() if ":" in sub else ""
                        elif "Dağıtım" in key_raw or "Distribution" in key_raw:
                            dist_val = val_raw.split(",")[0].strip()
                            if dist_val:
                                pkg.origin = dist_val
        except Exception as e:
            print(f"Paket detay yükleme hatası ({pkg.name}): {e}")

        # --- Repodan Gerçek Paketleyici, E-Posta, Güncelleme Tarihi ve Anasayfa Verilerini Çek ---
        repo_info = self._fetch_pisi_repo_details(pkg.name)
        if repo_info:
            if repo_info.get("packager_name"):
                pkg.packager_name = repo_info["packager_name"]
            if repo_info.get("packager_email"):
                pkg.packager_email = repo_info["packager_email"]
            if repo_info.get("update_date"):
                pkg.update_date = repo_info["update_date"]
            if repo_info.get("homepage"):
                pkg.homepage = repo_info["homepage"]

        # Fallback: Repodan e-posta/isim alınamadıysa pisi blame kullan
        if not pkg.packager_name or not pkg.packager_email:
            try:
                blame = subprocess.run(["pisi", "blame", pkg.name], capture_output=True, text=True, timeout=10)
                if blame.returncode == 0 and blame.stdout:
                    for line in blame.stdout.splitlines():
                        line_str = line.strip()
                        if ("Yayım Güncelleyen" in line_str or "Updated By" in line_str) and ":" in line_str:
                            val = line_str.split(":", 1)[1].strip()
                            if "<" in val and ">" in val:
                                name_part = val[:val.index("<")].strip()
                                email_part = val[val.index("<")+1:val.index(">")].strip()
                                if name_part and not pkg.packager_name:
                                    pkg.packager_name = name_part
                                if email_part and not pkg.packager_email:
                                    pkg.packager_email = email_part
                            elif val and not pkg.packager_name:
                                pkg.packager_name = val
                        elif ("Güncelleme Tarihi" in line_str or "Update Date" in line_str) and ":" in line_str:
                            date_val = line_str.split(":", 1)[1].strip()
                            if date_val and not pkg.update_date:
                                pkg.update_date = date_val
            except Exception as e:
                print(f"Paket blame yükleme hatası ({pkg.name}): {e}")

        # --- Geliştirici (Developer) Otomatik Çıkarımı ---
        if not pkg.developer:
            url = (pkg.homepage or "").lower()
            comp = (pkg.component or "").lower()
            
            if "mozilla.org" in url:
                pkg.developer = "Mozilla Foundation"
            elif "gnu.org" in url:
                pkg.developer = "GNU Project"
            elif "kde.org" in url or "desktop.kde" in comp or "kde" in comp:
                pkg.developer = "KDE Community"
            elif "gnome.org" in url or "desktop.gnome" in comp or "gnome" in comp:
                pkg.developer = "GNOME Project"
            elif "xfce.org" in url or "desktop.xfce" in comp:
                pkg.developer = "Xfce Development Team"
            elif "videolan.org" in url:
                pkg.developer = "VideoLAN Project"
            elif "python.org" in url:
                pkg.developer = "Python Software Foundation"
            elif "freedesktop.org" in url:
                pkg.developer = "Freedesktop.org"
            elif "kernel.org" in url:
                pkg.developer = "Linux Kernel Organization"
            elif "apache.org" in url:
                pkg.developer = "Apache Software Foundation"
            elif "qt.io" in url:
                pkg.developer = "The Qt Company"
            elif pkg.homepage:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(pkg.homepage)
                    netloc = parsed.netloc or parsed.path.split('/')[0]
                    if netloc.startswith("www."):
                        netloc = netloc[4:]
                    if "github.com/" in pkg.homepage:
                        parts = parsed.path.strip('/').split('/')
                        if len(parts) >= 1 and parts[0]:
                            pkg.developer = f"GitHub ({parts[0]})"
                    elif "gitlab.com/" in pkg.homepage:
                        parts = parsed.path.strip('/').split('/')
                        if len(parts) >= 1 and parts[0]:
                            pkg.developer = f"GitLab ({parts[0]})"
                    elif netloc:
                        pkg.developer = netloc.capitalize()
                except Exception:
                    pass
            
            if not pkg.developer and pkg.packager_name:
                pkg.developer = pkg.packager_name
            if not pkg.developer:
                pkg.developer = "Pisi Linux Topluluğu"

    def _parse_pisi_list_output(self, output: str, installed: bool = False):
        lines = output.strip().splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("Depodaki") or line_str.startswith("Total"):
                continue
            if line_str.startswith("🌐"):
                line_str = line_str[1:].strip()

            if " - " in line_str:
                parts = line_str.split(" - ", 1)
                name = parts[0].strip()
                summary_or_ver = parts[1].strip()
                if not name:
                    continue
                version = ""
                summary = ""
                if summary_or_ver.startswith("v"):
                    version = summary_or_ver[1:].strip()
                else:
                    summary = summary_or_ver
            else:
                parts = line_str.split()
                if not parts:
                    continue
                name = parts[0].strip()
                version = ""
                if len(parts) > 1 and parts[1].startswith("v"):
                    version = parts[1][1:].strip()
                summary = ""

            icon_path = self._find_icon(name)
            category = self._map_to_category(name, summary=summary)
            pkg = PackageInfo(
                name=name,
                display_name=name.capitalize() if name.islower() else name,
                version=version,
                summary=summary,
                category=category,
                icon_name=name,
                icon_path=icon_path,
                installed=installed
            )

            if installed:
                self._installed_packages[name] = pkg
            else:
                self._available_packages[name] = pkg

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
        """Çok dilli XML etiketlerinden tercih edilen dildeki metni döndürür."""
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
        index_files = (
            glob.glob("/var/lib/pisi/index/**/*.xml", recursive=True)
            + glob.glob("/var/cache/pisi/**/*.xml", recursive=True)
        )
        index_files = [f for f in index_files if f.endswith(".xml")]
        if not index_files:
            return False

        loaded_count = 0
        for idx_file in index_files:
            try:
                tree = ET.parse(idx_file)
                root = tree.getroot()
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
                    installed_size_raw = (p.findtext("InstalledSize") or "Undefined").strip()
                    download_size_raw = (p.findtext("PackageSize") or "Undefined").strip()

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
                ["pisi", "list-available"],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                self._parse_pisi_list_output(result.stdout, installed=False)
                for pkg in self._available_packages.values():
                    if not pkg.icon_path:
                        pkg.icon_path = self._find_icon(pkg.icon_name or pkg.name)
        except Exception as e:
            print(f"PiSi depo paket yükleme hatası: {e}")

    def _run_pisi_cmd(self, pisi_args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Pisi komutunu çalıştırır (gerektiğinde pkexec ile)."""
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd = ["pisi"] + pisi_args
        else:
            cmd = ["pkexec", "pisi"] + pisi_args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def update_repo_and_sync_cache(self, progress_callback=None, update_repo=True) -> bool:
        """Pisi paket deposunu günceller ve önbelleği yeniler."""
        if progress_callback:
            if update_repo:
                progress_callback(5, "PiSi depoları güncelleniyor...")
            else:
                progress_callback(5, "Önbellek kontrol ediliyor...")

        if update_repo:
            try:
                self._run_pisi_cmd(["update-repo"], timeout=60)
            except Exception as e:
                print(f"Pisi depo güncelleme hatası: {e}")

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
                result = subprocess.run(
                    ["pisi", "list-upgrades"], capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.splitlines():
                        line_str = line.strip()
                        if not line_str or line_str.startswith("Sistem") or line_str.startswith("System") or line_str.startswith("Tüm"):
                            continue
                        if line_str.startswith("🌐"):
                            line_str = line_str[1:].strip()
                        parts = line_str.split(" - ", 1) if " - " in line_str else line_str.split()
                        pkg_name = parts[0].strip()
                        if pkg_name and pkg_name not in upgradable_names:
                            upgradable_names.append(pkg_name)
                            if pkg_name in self._installed_packages:
                                self._installed_packages[pkg_name].has_update = True
                            if pkg_name in self._available_packages:
                                self._available_packages[pkg_name].has_update = True
            except Exception as e:
                print(f"Pisi CLI list-upgrades hatası: {e}")

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
        """Önbellek geçerli mi kontrol eder."""
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

            loaded = 0
            for pkg_data in data:
                # Sadece gerçek pisi deposundan gelen paketleri yükle
                if pkg_data.get("_source") != "pisi_repo":
                    continue
                pkg_data.pop("_source", None)
                pkg_data["is_flatpak"] = False
                # PackageInfo'da olmayan field varsa temizle
                valid_fields = {f.name for f in PackageInfo.__dataclass_fields__.values()}
                pkg_data = {k: v for k, v in pkg_data.items() if k in valid_fields}
                pkg = PackageInfo(**pkg_data)
                self._available_packages[pkg.name] = pkg
                loaded += 1

            return loaded > 0
        except Exception:
            return False

    def _save_index_to_cache(self):
        try:
            data = []
            for pkg in self._available_packages.values():
                if pkg.is_flatpak:
                    continue
                d = dict(pkg.__dict__)
                d["_source"] = "pisi_repo"  # gerçek repo markeri
                data.append(d)
            with open(INDEX_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Önbellek kaydetme hatası: {e}")

    # --- Flatpak Yönetimi ---

    def _load_flatpaks(self):
        """Sistemde kurulu ve depodaki Flatpak uygulamalarını yükler."""
        if not self._flatpak_available:
            return
        self._load_installed_flatpaks()
        if not self._flatpak_loaded:
            self._load_available_flatpaks()
            self._flatpak_loaded = True

    def _load_installed_flatpaks(self):
        """Kurulu Flatpak uygulamalarını ve bileşenlerini listeler."""
        try:
            result = subprocess.run(
                ["flatpak", "list", "--columns=application,name,version,branch,origin,ref"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0 or not result.stdout.strip():
                return
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("\t")]
                if not parts:
                    continue
                app_id = parts[0]
                if not app_id and len(parts) > 5 and "/" in parts[5]:
                    ref_parts = parts[5].split("/")
                    if len(ref_parts) >= 2:
                        app_id = ref_parts[1]
                if not app_id:
                    continue
                display_name = parts[1] if len(parts) > 1 and parts[1] else app_id
                version = parts[2] if len(parts) > 2 and parts[2] else (parts[3] if len(parts) > 3 else "")
                origin = parts[4].capitalize() if len(parts) > 4 and parts[4] else "FlatHub"
                key = f"flatpak:{app_id}"
                icon_name = app_id.split(".")[-1].lower() if app_id else "flatpak"
                icon_path = self._find_flatpak_icon(app_id) if app_id else ""
                cat = self._get_flatpak_category(app_id) if app_id else "utilities"
                pkg = PackageInfo(
                    name=key,
                    display_name=display_name,
                    version=version,
                    summary=f"{origin} · {app_id}",
                    description=f"{display_name} ({app_id}) Flatpak ({origin}) aracılığıyla kurulmuştur.",
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

    def check_flatpak_updates(self) -> list[str]:
        """Güncellenebilir Flatpak uygulamalarını döndürür."""
        if not self._flatpak_available:
            return []
        try:
            result = subprocess.run(
                ["flatpak", "remote-ls", "--updates", "--columns=application,name,version,branch,origin,ref"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0 or not result.stdout.strip():
                return []
            upgradable = []
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("\t")]
                if not parts:
                    continue
                app_id = parts[0]
                if not app_id and len(parts) > 5 and "/" in parts[5]:
                    ref_parts = parts[5].split("/")
                    if len(ref_parts) >= 2:
                        app_id = ref_parts[1]
                if not app_id:
                    continue
                key = f"flatpak:{app_id}"
                upgradable.append(key)

                display_name = parts[1] if len(parts) > 1 and parts[1] else app_id
                version = parts[2] if len(parts) > 2 and parts[2] else (parts[3] if len(parts) > 3 else "")
                origin = parts[4].capitalize() if len(parts) > 4 and parts[4] else "FlatHub"

                if key not in self._installed_packages:
                    icon_name = app_id.split(".")[-1].lower() if app_id else "flatpak"
                    icon_path = self._find_flatpak_icon(app_id) if app_id else ""
                    cat = self._get_flatpak_category(app_id) if app_id else "utilities"
                    pkg = PackageInfo(
                        name=key,
                        display_name=display_name,
                        version=version,
                        summary=f"{origin} · {app_id}",
                        description=f"{display_name} ({app_id}) Flatpak ({origin}) aracılığıyla kurulmuştur.",
                        category=cat,
                        icon_name=icon_name,
                        icon_path=icon_path,
                        installed=True,
                        has_update=True,
                        is_flatpak=True,
                        origin=origin
                    )
                    self._installed_packages[key] = pkg
                else:
                    self._installed_packages[key].has_update = True

                if key in self._available_packages:
                    self._available_packages[key].has_update = True
            return upgradable
        except Exception as e:
            print(f"Flatpak güncelleme kontrolü hatası: {e}")
            return []

    def _fetch_flathub_popularity(self) -> dict[str, tuple[int, int, str]]:
        """FlatHub API'sinden popülerlik verilerini çeker."""
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
            print(f"FlatHub popülerlik listesi alma hatası: {e}")
        return popular_info

    def _get_or_download_flathub_icon(self, icon_url: str) -> str:
        """FlatHub ikon URL'sini yerel önbelleğe indirir."""
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

    def _fetch_flatpak_sizes(self, app_id: str) -> tuple[str, str]:
        """Flatpak uygulamasının indirme ve kurulu boyutunu flatpak CLI ile çeker."""
        real_id = app_id.removeprefix("flatpak:")
        dl_size, inst_size = "", ""
        try:
            res = subprocess.run(["flatpak", "remote-info", "flathub", real_id], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout:
                for line in res.stdout.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k_lower, v_val = k.strip().lower(), v.strip()
                        if "ndirme" in k_lower or "download" in k_lower:
                            dl_size = v_val
                        elif "kurulu" in k_lower or "installed" in k_lower:
                            inst_size = v_val
        except Exception:
            pass
        return dl_size, inst_size

    def _load_available_flatpaks(self):
        """Flatpak depolarındaki uygulamaları listeler."""
        try:
            result = subprocess.run(
                ["flatpak", "remote-ls", "--app", "--columns=application,name,version,origin,download-size,installed-size"],
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
                display_name = parts[1] if len(parts) > 1 and parts[1] else app_id
                version = parts[2] if len(parts) > 2 else ""
                origin = parts[3].capitalize() if len(parts) > 3 and parts[3] else "FlatHub"
                dl_size = parts[4] if len(parts) > 4 else ""
                inst_size = parts[5] if len(parts) > 5 else ""

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
                    downloads=downloads,
                    download_size=dl_size,
                    installed_size=inst_size
                )
                flatpak_pkgs.append((rank, pkg))

            flatpak_pkgs.sort(key=lambda x: x[0])

            for _, pkg in flatpak_pkgs:
                self._available_packages[pkg.name] = pkg

        except Exception as e:
            print(f"Flatpak depo listesi hatası: {e}")

    def fetch_flathub_info(self, app_id: str) -> dict:
        """FlatHub API (v2) ve flatpak CLI üzerinden uygulamanın ikon, açıklama, boyutlar ve görsellerini indirir."""
        real_id = app_id.removeprefix("flatpak:")
        dl_size, inst_size = self._fetch_flatpak_sizes(real_id)

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
                            if sc.get("desktop"):
                                screenshots.append(sc.get("desktop"))
                            elif sc.get("sizes") and isinstance(sc.get("sizes"), list):
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

                    # Ek meta alanlar
                    project_license = data.get("project_license", "")
                    urls_data = data.get("urls") or {}
                    homepage = urls_data.get("homepage", "")
                    vcs_browser = urls_data.get("vcs_browser", "")
                    categories = data.get("categories") or []
                    if isinstance(categories, list):
                        categories_str = ", ".join(categories[:4])
                    else:
                        categories_str = str(categories)

                    return {
                        "icon_url": icon_url,
                        "local_icon": local_icon,
                        "summary": summary,
                        "description": description,
                        "developer": developer,
                        "screenshots": local_screenshots,
                        "license": project_license,
                        "homepage": homepage,
                        "vcs_url": vcs_browser,
                        "categories": categories_str,
                        "download_size": dl_size,
                        "installed_size": inst_size,
                    }
        except Exception as e:
            print(f"FlatHub API hatası ({real_id}): {e}")

        return {
            "download_size": dl_size,
            "installed_size": inst_size,
        }

    def _find_flatpak_icon(self, app_id: str) -> str:
        """Flatpak uygulama ikonunu sistemde arar."""
        icon_dirs = [
            "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
            "/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps",
            "/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps",
            "/var/lib/flatpak/exports/share/icons/hicolor/64x64/apps",
            os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/scalable/apps"),
            os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/64x64/apps"),
        ]
        for d in icon_dirs:
            for ext in ICON_EXTENSIONS:
                p = os.path.join(d, app_id + ext)
                if os.path.exists(p):
                    return p
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
        """Flatpak uygulaması kurar."""
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
        """Flatpak uygulaması kaldırır."""
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

    # --- Genel API Metodları ---

    def get_installed_packages(self) -> dict[str, PackageInfo]:
        if self._installed_packages:
            self._load_flatpaks()
            return self._installed_packages
        self._load_installed_packages()
        self._load_flatpaks()
        return self._installed_packages

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
        if package_name.startswith("flatpak:"):
            return self.install_flatpak(package_name)

        if not self._pisi_available:
            return False, "pisi komutu sistemde bulunamadı"

        try:
            result = self._run_pisi_cmd(["install", "-y", package_name], timeout=300)
            if result.returncode == 0:
                if package_name in self._available_packages:
                    self._available_packages[package_name].installed = True
                    self._installed_packages[package_name] = self._available_packages[package_name]
                return True, f"{package_name} başarıyla kuruldu"
            else:
                err_msg = result.stderr or result.stdout or "Kurulum başarısız oldu"
                return False, err_msg
        except Exception as e:
            return False, str(e)

    def remove_package(self, package_name: str) -> tuple[bool, str]:
        if package_name.startswith("flatpak:"):
            return self.remove_flatpak(package_name)

        if not self._pisi_available:
            return False, "pisi komutu sistemde bulunamadı"

        try:
            result = self._run_pisi_cmd(["remove", "-y", package_name], timeout=300)
            if result.returncode == 0:
                if package_name in self._installed_packages:
                    del self._installed_packages[package_name]
                if package_name in self._available_packages:
                    self._available_packages[package_name].installed = False
                return True, f"{package_name} başarıyla kaldırıldı"
            else:
                err_msg = result.stderr or result.stdout or "Kaldırma başarısız oldu"
                return False, err_msg
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
        pkg = self._installed_packages.get(package_name) or self._available_packages.get(package_name)
        if pkg and not pkg.is_flatpak and self._pisi_available and (
            not pkg.description or not pkg.license or not pkg.packager_name
        ):
            self._enrich_pisi_package_info(pkg)
        return pkg
