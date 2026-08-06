"""
PiSiM – Tasarım Sistemleri ve Widget Bileşenleri
Sistem Teması Otomatik Algılama & LupuS/PiSi Markalama
"""

import os
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QCheckBox, QApplication,
    QProgressBar, QStackedWidget, QScrollArea, QDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QRectF, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import (
    QPixmap, QIcon, QColor, QPainter, QPainterPath, QFont,
    QBrush, QGuiApplication
)

from .backend import PackageInfo
from .i18n import tr

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
APP_ICON_PATH = os.path.join(ASSETS_DIR, "pisim.png")


def detect_system_dark_mode() -> bool:
    """Sistemin koyu tema (Dark Mode) kullanıp kullanmadığını otomatik algılar."""
    # 1. Qt StyleHints ColorScheme kontrolü
    try:
        app = QGuiApplication.instance()
        if app and hasattr(app.styleHints(), "colorScheme"):
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return True
            elif scheme == Qt.ColorScheme.Light:
                return False
    except Exception:
        pass

    # 2. GNOME / Freedesktop gsettings kontrolü
    try:
        out = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            text=True, stderr=subprocess.DEVNULL, timeout=1
        )
        if "dark" in out.lower():
            return True
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            text=True, stderr=subprocess.DEVNULL, timeout=1
        )
        if "dark" in out.lower():
            return True
    except Exception:
        pass

    # 3. Qt Palette lightness kontrolü
    try:
        app = QApplication.instance()
        if app:
            bg_color = app.palette().color(app.palette().ColorRole.Window)
            return bg_color.lightness() < 128
    except Exception:
        pass

    return False


# ──────────────────────────────────────────────
#  Otomatik Sistem Tema Yönetimi
# ──────────────────────────────────────────────
class ThemeManager:
    """Sistem ayarına göre otomatik koyu/açık tema paleti"""

    @classmethod
    def is_dark(cls) -> bool:
        return detect_system_dark_mode()

    @classmethod
    def bg(cls): return "#18181a" if cls.is_dark() else "#f4f4f6"
    @classmethod
    def sidebar_bg(cls): return "#242426" if cls.is_dark() else "#e8e8ed"
    @classmethod
    def card_bg(cls): return "#29292c" if cls.is_dark() else "#ffffff"
    @classmethod
    def card_hover(cls): return "#343438" if cls.is_dark() else "#f9f9fb"
    @classmethod
    def border(cls): return "#38383a" if cls.is_dark() else "#e3e3e8"
    @classmethod
    def text_primary(cls): return "#ffffff" if cls.is_dark() else "#1c1c1e"
    @classmethod
    def text_secondary(cls): return "#98989d" if cls.is_dark() else "#6c6c70"
    @classmethod
    def accent_teal(cls): return "#2ba0b5"
    @classmethod
    def accent_teal_hover(cls): return "#1e8799"
    @classmethod
    def update_btn_bg(cls): return "#3a3a3c" if cls.is_dark() else "#e0f7fa"
    @classmethod
    def update_btn_text(cls): return "#64b5f6" if cls.is_dark() else "#00838f"
    @classmethod
    def open_btn_bg(cls): return "#3a3a3c" if cls.is_dark() else "#e0f2f1"
    @classmethod
    def open_btn_text(cls): return "#81c784" if cls.is_dark() else "#00695c"


KDE_CATEGORY_ICON_MAP = {
    "compass": ["applications-all", "system-search", "compass", "preferences-system-search"],
    "all": ["applications-all", "view-grid", "applications-other", "grid"],
    "grid": ["applications-all", "view-grid", "applications-other", "grid"],
    "pisi": ["pisi", "distributor-logo-pisi", "distributor-logo", "system-run", "applications-other"],
    "development": ["applications-development", "code-context", "code"],
    "code": ["applications-development", "code-context", "code"],
    "education": ["applications-education", "applications-science", "book"],
    "book": ["applications-education", "applications-science", "book"],
    "enterprise": ["applications-office", "applications-engineering", "briefcase"],
    "briefcase": ["applications-office", "applications-engineering", "briefcase"],
    "games": ["applications-games", "gamepad"],
    "gamepad": ["applications-games", "gamepad"],
    "graphics": ["applications-graphics", "image"],
    "image": ["applications-graphics", "image"],
    "internet": ["applications-internet", "globe"],
    "globe": ["applications-internet", "globe"],
    "multimedia": ["applications-multimedia", "film"],
    "film": ["applications-multimedia", "film"],
    "office": ["applications-office", "file-text"],
    "file-text": ["applications-office", "file-text"],
    "system": ["applications-system", "preferences-system", "settings"],
    "settings": ["applications-system", "preferences-system", "settings"],
    "utilities": ["applications-utilities", "preferences-other", "tool"],
    "tool": ["applications-utilities", "preferences-other", "tool"],
    "installed": ["system-software-install", "package-installed-updated", "download"],
    "download": ["system-software-install", "package-installed-updated", "download"],
}


def get_kde_icon(icon_name: str) -> QIcon:
    """KDE ikon temalarından (Breeze vb.) kategorinin ikonunu çeker."""
    candidates = KDE_CATEGORY_ICON_MAP.get(icon_name, [icon_name])
    if icon_name not in candidates:
        candidates = list(candidates) + [icon_name]
    for name in candidates:
        ico = QIcon.fromTheme(name)
        if not ico.isNull():
            return ico
    return QIcon.fromTheme("applications-other")


def _is_valid_svg(path: str) -> bool:
    """SVG dosyasının geçerli path verisi içerip içermediğini hızlıca kontrol eder."""
    try:
        with open(path, 'rb') as f:
            content = f.read(4096)
        # Temel SVG etiket kontrolü
        if b'<svg' not in content and b'<SVG' not in content:
            return False
        # Path verisi var mı? (d=" veya d=' içermeli)
        # Bazı ikon SVG'leri sadece <use> veya <image> içerebilir — bunlar da geçerli
        return True
    except Exception:
        return False


def load_app_icon(icon_path: str, icon_name: str = "", size: int = 56) -> QPixmap:
    """Paket ikonunu yükler. Hatalı SVG veya bozuk ikon dosyalarında çökme/uyarı önleyici korumalıdır."""
    try:
        if icon_path and Path(icon_path).exists():
            # SVG dosyaları için geçerlilik kontrolü
            if icon_path.lower().endswith('.svg'):
                if not _is_valid_svg(icon_path):
                    raise ValueError("Geçersiz SVG dosyası")
                # QIcon üzerinden yükle — daha güvenli
                ico = QIcon(icon_path)
                if not ico.isNull():
                    px = ico.pixmap(QSize(size, size))
                    if not px.isNull():
                        return px
                raise ValueError("SVG pixmap boş")
            else:
                px = QPixmap(icon_path)
                if not px.isNull():
                    return px.scaled(size, size,
                                     Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
    except Exception:
        pass

    try:
        if icon_name:
            icon = get_kde_icon(icon_name)
            if not icon.isNull():
                px = icon.pixmap(QSize(size, size))
                if not px.isNull():
                    return px
    except Exception:
        pass

    return _letter_icon(icon_name or "?", size)




def _letter_icon(text: str, size: int) -> QPixmap:
    """Yumuşak renkli harf ikonu üretir."""
    palette = ["#2ba0b5", "#3a86ff", "#833ab4", "#fd5e53", "#2a9d8f", "#e76f51"]
    idx = sum(ord(c) for c in text) % len(palette)
    base = QColor(palette[idx])

    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    path = QPainterPath()
    r = size * 0.22
    path.addRoundedRect(QRectF(1, 1, size - 2, size - 2), r, r)
    p.fillPath(path, QBrush(base))

    font = p.font()
    font.setPixelSize(int(size * 0.44))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor("white"))
    letter = text[0].upper() if text else "?"
    p.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, letter)
    p.end()
    return px


# ──────────────────────────────────────────────
#  Aksiyon Butonu (Turkuaz Pill Button)
# ──────────────────────────────────────────────
class PisiActionButton(QPushButton):
    """PiSi Market standart turkuaz/cyan buton bileşeni"""

    def __init__(self, text: str = "Kur", status: str = "install", parent=None):
        super().__init__(text, parent)
        self.status = status
        self.setFixedHeight(34)
        self.setFixedWidth(88)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()

    def update_style(self):
        if self.status == "install":
            self.setText(tr("btn_install"))
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeManager.accent_teal()};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.accent_teal_hover()};
                }}
            """)
        elif self.status == "update":
            self.setText(tr("btn_update"))
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeManager.update_btn_bg()};
                    color: {ThemeManager.update_btn_text()};
                    border: none;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
            """)
        elif self.status == "open":
            self.setText(tr("btn_open"))
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeManager.open_btn_bg()};
                    color: {ThemeManager.open_btn_text()};
                    border: none;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 700;
                }}
            """)
        elif self.status == "disabled":
            self.setText("🚫")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeManager.border()};
                    color: {ThemeManager.text_secondary()};
                    border: none;
                    border-radius: 10px;
                    font-size: 12px;
                }}
            """)
        elif self.status == "delete":
            self.setText(tr("btn_remove"))
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #3d1a1a;
                    color: #ef4444;
                    border: 1px solid #5a2a2a;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: #ef4444;
                    color: white;
                }}
            """)


# ──────────────────────────────────────────────
#  Yükleme/Durum Bileşeni (Progress + Butonlar)
# ──────────────────────────────────────────────
class PisiInstallWidget(QWidget):
    """Install/Update/Delete butonlarını, indirme progressbarını ve hata
    mesajını tek bir bileşende yönetir."""

    install_clicked = pyqtSignal(str)   # paket adı
    remove_clicked  = pyqtSignal(str)   # paket adı
    cancel_clicked  = pyqtSignal(str)   # paket adı

    def __init__(self, package, parent=None, show_percent: bool = False, show_delete: bool = True):
        super().__init__(parent)
        self.package = package
        self._show_percent = show_percent
        self._show_delete = show_delete
        self._anim_timer = None
        self._shimmer_offset = 0
        self._current_progress = 0
        self._pending_worker_bind = None  # worker bağlama için
        self._build()

    def _build(self):
        self.setFixedWidth(200)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(3)

        # ── Buton satırı ──
        self._btn_row = QWidget()
        btn_lay = QHBoxLayout(self._btn_row)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        btn_lay.setSpacing(6)

        self._btn_install = PisiActionButton(status="install")
        self._btn_install.clicked.connect(
            lambda: self.install_clicked.emit(self.package.name)
        )

        self._btn_update = PisiActionButton(status="update")
        self._btn_update.clicked.connect(
            lambda: self.install_clicked.emit(self.package.name)
        )

        self._btn_delete = QPushButton("🗑")
        self._btn_delete.setFixedSize(34, 34)
        self._btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_delete.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ThemeManager.text_secondary()};
                border: none;
                font-size: 15px;
            }}
            QPushButton:hover {{
                color: #ef4444;
            }}
        """)
        self._btn_delete.clicked.connect(
            lambda: self.remove_clicked.emit(self.package.name)
        )

        # "Kuruldu" etiketi — show_delete=False olduğunda çöp kutusu yerine gösterilir
        self._lbl_installed = QLabel(tr("installed_label"))
        self._lbl_installed.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self._lbl_installed.setStyleSheet(
            f"color: {ThemeManager.accent_teal()}; font-size: 11px; font-weight: 700;"
            " background: transparent; border: none; padding-right: 2px;"
        )

        btn_lay.addStretch()
        btn_lay.addWidget(self._btn_install)
        btn_lay.addWidget(self._btn_update)
        btn_lay.addWidget(self._btn_delete)
        btn_lay.addWidget(self._lbl_installed)
        root.addWidget(self._btn_row)

        # ── Progress satırı (gizli başlar) ──
        self._prog_row = QWidget()
        self._prog_row.hide()
        prog_lay = QVBoxLayout(self._prog_row)
        prog_lay.setContentsMargins(0, 0, 0, 0)
        prog_lay.setSpacing(2)

        # Yüzde etiketi — sadece show_percent=True ise oluşturulur
        if self._show_percent:
            self._pct_lbl = QLabel("0%")
            self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._pct_lbl.setStyleSheet(
                f"color: {ThemeManager.accent_teal()}; font-size: 11px; font-weight: 700;"
                " background: transparent; border: none;"
            )
            prog_lay.addWidget(self._pct_lbl)
        else:
            self._pct_lbl = None

        # Progress bar
        self._pbar = QProgressBar()
        self._pbar.setRange(0, 100)
        self._pbar.setValue(0)
        self._pbar.setFixedHeight(6)
        self._pbar.setTextVisible(False)
        self._apply_pbar_style(0.0)
        prog_lay.addWidget(self._pbar)

        # İptal butonu
        self._btn_cancel = QPushButton(tr("btn_cancel"))
        self._btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_cancel.setFixedHeight(22)
        self._btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ThemeManager.text_secondary()};
                border: none;
                font-size: 10px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: #ef4444;
            }}
        """)
        self._btn_cancel.clicked.connect(lambda: self.cancel_clicked.emit(self.package.name))
        prog_lay.addWidget(self._btn_cancel)

        root.addWidget(self._prog_row)

        # ── Hata etiketi (gizli başlar) ──
        self._err_lbl = QLabel(tr("error_occurred"))
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err_lbl.setStyleSheet(
            "color: #ef4444; font-size: 11px; font-weight: 700;"
            " background: transparent; border: none;"
        )
        self._err_lbl.hide()
        root.addWidget(self._err_lbl)

        self.refresh_state()

    def _apply_pbar_style(self, shimmer_pos: float):
        """Progress bar stilini shimmer pozisyonuna göre günceller."""
        s = max(0.0, shimmer_pos - 0.25)
        e = min(1.0, shimmer_pos + 0.25)
        mid = (s + e) / 2.0
        try:
            self._pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {ThemeManager.border()};
                    border-radius: 3px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {ThemeManager.accent_teal()},
                        stop:{s:.3f} {ThemeManager.accent_teal()},
                        stop:{mid:.3f} #7ff4ff,
                        stop:{e:.3f} {ThemeManager.accent_teal()},
                        stop:1 {ThemeManager.accent_teal()}
                    );
                    border-radius: 3px;
                }}
            """)
        except RuntimeError:
            pass

    def refresh_state(self):
        """Paketin güncel durumuna göre butonları göster/gizle."""
        installed = self.package.installed
        has_update = self.package.has_update

        self._btn_install.setVisible(not installed)
        self._btn_update.setVisible(installed and has_update)

        if self._show_delete:
            # Normal mod: çöp kutusu butonu göster, "Kuruldu" etiketi gizle
            self._btn_delete.setVisible(installed and not has_update)
            self._lbl_installed.setVisible(False)
        else:
            # Kategori modu: çöp kutusu gizle, kuruluysa "Kuruldu" etiketi göster
            self._btn_delete.setVisible(False)
            self._lbl_installed.setVisible(installed and not has_update)

        if installed and not has_update:
            self.setFixedWidth(80 if not self._show_delete else 50)
        elif installed and has_update:
            self.setFixedWidth(140)
        else:
            self.setFixedWidth(100)

    # ── Progress animasyon timer ──

    def _start_shimmer(self):
        """Progress bar'da kayma shimmer animasyonu başlatır."""
        if self._anim_timer is not None:
            return
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(25)  # ~40 fps
        self._anim_timer.timeout.connect(self._shimmer_step)
        self._shimmer_offset = 0
        self._anim_timer.start()

    def _shimmer_step(self):
        try:
            self._shimmer_offset = (self._shimmer_offset + 3) % 100
            pos = self._shimmer_offset / 100.0
            self._apply_pbar_style(pos)
        except RuntimeError:
            self._stop_shimmer()

    def _stop_shimmer(self):
        if self._anim_timer:
            try:
                self._anim_timer.stop()
            except RuntimeError:
                pass
            self._anim_timer = None
        # Sabit stile dön
        self._apply_pbar_style(0.5)

    # ── Dışarıdan çağrılan metodlar ──

    def start_progress(self):
        """İndirme başladığında buton → progress bar."""
        try:
            self._err_lbl.hide()
            self._btn_row.hide()
            self._prog_row.show()
            self._pbar.setValue(0)
            self._current_progress = 0
            if self._pct_lbl:
                self._pct_lbl.setText("0%")
            self.setFixedWidth(160)
            self._start_shimmer()
        except RuntimeError:
            pass

    def set_progress(self, value: int):
        """0–100 arası progress değeri — animasyonu kesintisiz devam ettirir."""
        try:
            clamped = max(0, min(100, value))
            self._current_progress = clamped
            self._pbar.setValue(clamped)
            if self._pct_lbl:
                self._pct_lbl.setText(f"{clamped}%")
            # İlk progress gelince eğer shimmer yoksa başlat
            if self._anim_timer is None and self._prog_row.isVisible():
                self._start_shimmer()
        except RuntimeError:
            pass

    def finish_progress(self):
        """Başarılı tamamlanma: state'i güncelle ve butonlara dön."""
        try:
            self._stop_shimmer()
            self._pbar.setValue(100)
            if self._pct_lbl:
                self._pct_lbl.setText("100%")
            QTimer.singleShot(500, self._restore_buttons)
        except RuntimeError:
            pass

    def show_error(self):
        """Hata durumunda progress → buton + kırmızı hata etiketi."""
        try:
            self._stop_shimmer()
            self._prog_row.hide()
            self._btn_row.show()
            self._err_lbl.show()
            self.refresh_state()
            QTimer.singleShot(4000, self._err_lbl.hide)
        except RuntimeError:
            pass

    def _restore_buttons(self):
        try:
            self._stop_shimmer()
            self._prog_row.hide()
            self._btn_row.show()
            self.refresh_state()
        except RuntimeError:
            pass


# ──────────────────────────────────────────────
#  Sidebar Butonu
# ──────────────────────────────────────────────
class PisiSidebarButton(QPushButton):
    """Sol menü navigasyon butonu"""

    def __init__(self, icon_name: str, label: str, cat_id: str, parent=None):
        super().__init__(parent)
        self.cat_id = cat_id
        self.setCheckable(True)
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self.ico_lbl = QLabel()
        self.ico_lbl.setStyleSheet("background: transparent; border: none;")
        ico = get_kde_icon(icon_name)
        if not ico.isNull():
            self.ico_lbl.setPixmap(ico.pixmap(20, 20))
        else:
            self.ico_lbl.setText("🔹")
        layout.addWidget(self.ico_lbl)

        self.txt_lbl = QLabel(label)
        self.txt_lbl.setStyleSheet("font-size: 13px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(self.txt_lbl)
        layout.addStretch()

        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.border()};
                border: none;
            }}
            QPushButton:checked {{
                background-color: {ThemeManager.border()};
                border: none;
            }}
        """)
        if self.isChecked():
            self.txt_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; font-weight: 800; background: transparent; border: none;")
        else:
            self.txt_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; font-weight: 600; background: transparent; border: none;")


# ──────────────────────────────────────────────
#  Trend Uygulama Satır Kartı
# ──────────────────────────────────────────────
class TrendingAppCard(QFrame):
    clicked         = pyqtSignal(str)
    install_clicked = pyqtSignal(str)
    remove_clicked  = pyqtSignal(str)

    def __init__(self, rank: int, package: PackageInfo, parent=None, show_delete: bool = True):
        super().__init__(parent)
        self.rank = rank
        self.package = package
        self._show_delete = show_delete
        self.setFixedHeight(68)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    def _build(self):
        self.setObjectName("TrendingAppCard")
        self.setStyleSheet(f"""
            QFrame#TrendingAppCard {{
                background-color: {ThemeManager.card_bg()};
                border-radius: 12px;
                border: 1px solid {ThemeManager.border()};
            }}
            QFrame#TrendingAppCard:hover {{
                background-color: {ThemeManager.card_hover()};
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(12)

        rank_lbl = QLabel(str(self.rank))
        rank_lbl.setFixedWidth(20)
        rank_lbl.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 14px; font-weight: 700; background: transparent; border: none;")
        lay.addWidget(rank_lbl)

        ico = QLabel()
        ico.setFixedSize(44, 44)
        ico.setStyleSheet("background: transparent; border: none;")
        ico.setPixmap(load_app_icon(self.package.icon_path, self.package.icon_name, 44))
        lay.addWidget(ico)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(0, 0, 0, 0)

        title = QLabel(self.package.display_name or self.package.name)
        title.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; font-weight: 700; background: transparent; border: none;")
        info.addWidget(title)

        sub = QLabel(self.package.summary or self.package.category)
        sub.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 11px; background: transparent; border: none;")
        info.addWidget(sub)

        lay.addLayout(info)
        lay.addStretch()

        self.install_widget = PisiInstallWidget(self.package, show_delete=self._show_delete)
        self.install_widget.install_clicked.connect(self.install_clicked)
        self.install_widget.remove_clicked.connect(self.remove_clicked)
        lay.addWidget(self.install_widget)

        # Gölge ve Hover Animasyonu
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(8)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(2)
        self.shadow.setColor(QColor(0, 0, 0, 45 if ThemeManager.is_dark() else 20))
        self.setGraphicsEffect(self.shadow)

    def enterEvent(self, ev):
        super().enterEvent(ev)
        try:
            if hasattr(self, "shadow") and self.shadow:
                self.anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
                self.anim.setDuration(160)
                self.anim.setStartValue(self.shadow.blurRadius())
                self.anim.setEndValue(20)
                self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.anim.start()
        except RuntimeError:
            pass

    def leaveEvent(self, ev):
        super().leaveEvent(ev)
        try:
            if hasattr(self, "shadow") and self.shadow:
                self.anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
                self.anim.setDuration(160)
                self.anim.setStartValue(self.shadow.blurRadius())
                self.anim.setEndValue(8)
                self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.anim.start()
        except RuntimeError:
            pass

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.package.name)
        super().mousePressEvent(ev)


# ──────────────────────────────────────────────
#  Uygulama Liste Kartı
# ──────────────────────────────────────────────
class PisiAppCard(QFrame):
    clicked         = pyqtSignal(str)
    install_clicked = pyqtSignal(str)
    remove_clicked  = pyqtSignal(str)

    def __init__(self, package: PackageInfo, parent=None, show_delete: bool = True):
        super().__init__(parent)
        self.package = package
        self._show_delete = show_delete
        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    def _build(self):
        self.setObjectName("PisiAppCard")
        self.setStyleSheet(f"""
            QFrame#PisiAppCard {{
                background-color: {ThemeManager.card_bg()};
                border-radius: 12px;
                border: 1px solid {ThemeManager.border()};
            }}
            QFrame#PisiAppCard:hover {{
                background-color: {ThemeManager.card_hover()};
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(12)

        ico = QLabel()
        ico.setFixedSize(48, 48)
        ico.setStyleSheet("background: transparent; border: none;")
        ico.setPixmap(load_app_icon(self.package.icon_path, self.package.icon_name, 48))
        lay.addWidget(ico)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(0, 0, 0, 0)

        # Üst satır: uygulama adı + flatpak etiketi
        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        name_row.setContentsMargins(0, 0, 0, 0)

        nm = QLabel(self.package.display_name or self.package.name)
        nm.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; font-weight: 700; background: transparent; border: none;")
        name_row.addWidget(nm)

        if self.package.is_flatpak:
            origin_name = getattr(self.package, "origin", "Flatpak") or "Flatpak"
            badge = QLabel(origin_name)
            badge.setStyleSheet("""
                QLabel {
                    background-color: #1a6fcf;
                    color: white;
                    border-radius: 4px;
                    padding: 1px 6px;
                    font-size: 9px;
                    font-weight: 800;
                    border: none;
                }
            """)
            badge.setFixedHeight(16)
            name_row.addWidget(badge)

        name_row.addStretch()
        info.addLayout(name_row)

        sumtxt = (self.package.summary[:55] + "…" if len(self.package.summary) > 55 else self.package.summary)
        sm = QLabel(sumtxt)
        sm.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 11px; background: transparent; border: none;")

        # Gölge ve Hover Animasyonu
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(8)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(2)
        self.shadow.setColor(QColor(0, 0, 0, 45 if ThemeManager.is_dark() else 20))
        self.setGraphicsEffect(self.shadow)

        info.addWidget(sm)

        lay.addLayout(info)
        lay.addStretch()

        self.install_widget = PisiInstallWidget(self.package, show_delete=self._show_delete)
        self.install_widget.install_clicked.connect(self.install_clicked)
        self.install_widget.remove_clicked.connect(self.remove_clicked)
        lay.addWidget(self.install_widget)

    def enterEvent(self, ev):
        super().enterEvent(ev)
        try:
            if hasattr(self, "shadow") and self.shadow:
                self.anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
                self.anim.setDuration(160)
                self.anim.setStartValue(self.shadow.blurRadius())
                self.anim.setEndValue(20)
                self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.anim.start()
        except RuntimeError:
            pass

    def leaveEvent(self, ev):
        super().leaveEvent(ev)
        try:
            if hasattr(self, "shadow") and self.shadow:
                self.anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
                self.anim.setDuration(160)
                self.anim.setStartValue(self.shadow.blurRadius())
                self.anim.setEndValue(8)
                self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.anim.start()
        except RuntimeError:
            pass

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.package.name)
        super().mousePressEvent(ev)


# ──────────────────────────────────────────────
#  4'lü İstatistik Kutusu
# ──────────────────────────────────────────────
class PisiStatsBox(QFrame):
    def __init__(self, package: PackageInfo, parent=None):
        super().__init__(parent)
        self.package = package
        self.setObjectName("PisiStatsBox")
        self.setStyleSheet(f"""
            QFrame#PisiStatsBox {{
                background-color: {ThemeManager.card_bg()};
                border-radius: 12px;
                border: 1px solid {ThemeManager.border()};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 12, 0, 12)

        stats = [
            (tr("rating"), f"{package.rating:.1f} ★"),
            (tr("downloads"), f"{package.downloads:,}"),
            (tr("size"), package.installed_size or "32.8 MB"),
            (tr("dependencies"), str(package.dependencies_count)),
        ]

        for i, (title, val) in enumerate(stats):
            box = QVBoxLayout()
            box.setSpacing(4)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)

            t = QLabel(title)
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 11px; background: transparent; border: none;")
            box.addWidget(t)

            v = QLabel(val)
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 14px; font-weight: 800; background: transparent; border: none;")
            box.addWidget(v)

            lay.addLayout(box)

            if i < len(stats) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"background-color: {ThemeManager.border()}; border: none;")
                lay.addWidget(sep)


# ──────────────────────────────────────────────
#  Ayarlar Switch Bileşeni
# ──────────────────────────────────────────────
class PisiToggleRow(QFrame):
    toggled = pyqtSignal(bool)

    def __init__(self, title: str, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("PisiToggleRow")
        self.setStyleSheet(f"""
            QFrame#PisiToggleRow {{
                background-color: {ThemeManager.card_bg()};
                border-radius: 12px;
                border: 1px solid {ThemeManager.border()};
            }}
        """)
        self.setFixedHeight(56)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        lay.addWidget(lbl)
        lay.addStretch()

        self.switch = QCheckBox()
        self.switch.setChecked(checked)
        self.switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.switch.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 44px;
                height: 24px;
                border-radius: 12px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {ThemeManager.border()};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ThemeManager.accent_teal()};
            }}
        """)
        self.switch.toggled.connect(self.toggled)
        lay.addWidget(self.switch)


# ──────────────────────────────────────────────
#  Ekran Görüntüsü Büyütme/Küçültme Diyaloğu (Modal)
# ──────────────────────────────────────────────
from PyQt6.QtWidgets import QDialog

class ImageViewerDialog(QDialog):
    """Ekran görüntülerini tam ekrana yakın büyütüp fare tekerleği veya butonlarla yakınlaştırıp uzaklaştırma diyaloğu."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.scale_factor = 1.0
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ThemeManager.bg()};
                border: 1px solid {ThemeManager.border()};
                border-radius: 12px;
            }}
        """)
        self._drag_pos = None
        self._build_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        # Üst Araç Çubuğu (Yakınlaştır, Uzaklaştır, Sıfırla, Kapat)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_zoom_in = QPushButton(tr("zoom_in"))
        btn_zoom_out = QPushButton(tr("zoom_out"))
        btn_reset = QPushButton(tr("reset"))
        btn_close = QPushButton(tr("close"))

        for b in (btn_zoom_in, btn_zoom_out, btn_reset, btn_close):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeManager.card_bg()};
                    color: {ThemeManager.text_primary()};
                    border: 1px solid {ThemeManager.border()};
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.card_hover()};
                }}
            """)

        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_zoom_out.clicked.connect(self.zoom_out)
        btn_reset.clicked.connect(self.reset_zoom)
        btn_close.clicked.connect(self.accept)

        toolbar.addWidget(btn_zoom_in)
        toolbar.addWidget(btn_zoom_out)
        toolbar.addWidget(btn_reset)
        toolbar.addStretch()
        toolbar.addWidget(btn_close)
        lay.addLayout(toolbar)

        # Görsel İçeriği Gösteren Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("background: transparent;")

        self.original_pixmap = QPixmap(self.image_path)
        self.scroll_area.setWidget(self.img_label)
        lay.addWidget(self.scroll_area)

        self.update_image()

    def update_image(self):
        if self.original_pixmap.isNull():
            return
        # Pencere alanına göre başlangıç ölçeği
        area_size = self.scroll_area.size()
        base_w = area_size.width() - 40 if area_size.width() > 100 else 900
        base_h = area_size.height() - 40 if area_size.height() > 100 else 600

        target_pixmap = self.original_pixmap.scaled(
            base_w, base_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        w = int(target_pixmap.width() * self.scale_factor)
        h = int(target_pixmap.height() * self.scale_factor)

        scaled_pix = self.original_pixmap.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.img_label.setPixmap(scaled_pix)

    def zoom_in(self):
        if self.scale_factor < 3.0:
            self.scale_factor *= 1.2
            self.update_image()

    def zoom_out(self):
        if self.scale_factor > 0.3:
            self.scale_factor /= 1.2
            self.update_image()

    def reset_zoom(self):
        self.scale_factor = 1.0
        self.update_image()

    def wheelEvent(self, event):
        # Fare tekerleği ile büyütüp küçültme
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()


