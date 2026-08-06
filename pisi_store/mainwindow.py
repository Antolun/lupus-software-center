"""
PiSiM – Ana Pencere ve Tüm Sayfa Görünümleri
LupuS İşletim Sistemi & PiSi Paket Yöneticisi
"""

import os
import re
import threading
from typing import Optional


from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QScrollArea, QGridLayout, QStackedWidget,
    QFrame, QButtonGroup, QApplication, QMessageBox,
    QProgressBar, QComboBox, QGraphicsOpacityEffect, QCheckBox,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QThread, QObject, QTimer,
    QPropertyAnimation, QParallelAnimationGroup, QEasingCurve
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QColor, QFont, QFontDatabase, QDesktopServices,
    QPainter, QPen
)

from .backend import PackageInfo, PisiBackend, LUPUS_CATEGORIES
from .i18n import tr, I18n
from .settings import SettingsManager
from .widgets import (
    ThemeManager, PisiActionButton, PisiInstallWidget, PisiSidebarButton,
    TrendingAppCard, PisiAppCard, PisiStatsBox, PisiToggleRow, ImageViewerDialog,
    load_app_icon, get_kde_icon, APP_ICON_PATH
)


# ──────────────────────────────────────────────
#  Animasyonlu QStackedWidget
# ──────────────────────────────────────────────
class AnimatedStackedWidget(QStackedWidget):
    """Görünümler (sayfalar) arasında yumuşak fade-in/out animasyonlu geçiş sağlar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim_group = None

        

    def setCurrentWidget(self, widget):
        current = self.currentWidget()
        if current == widget or not current or not self.isVisible():
            super().setCurrentWidget(widget)
            return

        eff_current = QGraphicsOpacityEffect(current)
        current.setGraphicsEffect(eff_current)

        eff_next = QGraphicsOpacityEffect(widget)
        eff_next.setOpacity(0.0)
        widget.setGraphicsEffect(eff_next)

        super().setCurrentWidget(widget)

        anim_out = QPropertyAnimation(eff_current, b"opacity")
        anim_out.setDuration(140)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.setEasingCurve(QEasingCurve.Type.OutQuad)

        anim_in = QPropertyAnimation(eff_next, b"opacity")
        anim_in.setDuration(200)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(anim_out)
        self._anim_group.addAnimation(anim_in)

        def _cleanup():
            current.setGraphicsEffect(None)
            widget.setGraphicsEffect(None)

        self._anim_group.finished.connect(_cleanup)
        self._anim_group.start()


# ──────────────────────────────────────────────
#  Arka-Plan Yükleyici Thread  (QThread subclass)
# ──────────────────────────────────────────────
class LoaderThread(QThread):
    progress        = pyqtSignal(int, str)
    finished_load   = pyqtSignal()
    load_error      = pyqtSignal(str)

    def __init__(self, backend: PisiBackend):
        super().__init__()
        self.backend = backend

    def run(self):
        try:
            self.progress.emit(5, tr("loading_prep"))
            self.backend.update_repo_and_sync_cache(
                progress_callback=lambda v, m: self.progress.emit(v, m),
                update_repo=False
            )
            self.progress.emit(25, tr("loading_check_installed"))
            self.backend.get_installed_packages()
            self.progress.emit(45, tr("loading_repo_pkgs"))
            self.backend.load_available_packages(
                progress_callback=lambda v, m: self.progress.emit(
                    45 + int(v * 0.45), m
                )
            )
            if self.backend.is_flatpak_available():
                self.progress.emit(92, tr("loading_flatpak"))
                self.backend._load_flatpaks()
            self.finished_load.emit()
        except Exception as e:
            self.load_error.emit(str(e))


# ──────────────────────────────────────────────
#  Paket Kurma/Kaldırma Worker Thread
# ──────────────────────────────────────────────
class InstallWorker(QThread):
    progress  = pyqtSignal(int)   # 0–100
    finished  = pyqtSignal(bool, str)  # ok, message

    def __init__(self, backend, package_name: str, action: str = "install"):
        super().__init__()
        self.backend = backend
        self.package_name = package_name
        self.action = action  # "install" | "remove"
        self._cancelled = False

    def cancel(self):
        """İndirmeyi iptal et."""
        self._cancelled = True
        if hasattr(self, '_proc') and self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def run(self):
        try:
            # Flatpak paketi mi?
            if self.package_name.startswith("flatpak:"):
                real_id = self.package_name.removeprefix("flatpak:")
                import subprocess
                is_inst = False
                key = f"flatpak:{real_id}"
                if key in self.backend._installed_packages and self.backend._installed_packages[key].installed:
                    is_inst = True

                if self.action == "install":
                    if is_inst:
                        cmd = ["flatpak", "update", "--noninteractive", "--assumeyes", real_id]
                    else:
                        cmd = ["flatpak", "install", "--noninteractive", "--assumeyes", real_id]
                else:
                    cmd = ["flatpak", "uninstall", "--noninteractive", "--assumeyes", real_id]

                self._proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                pct = 0
                import re as _re
                for line in self._proc.stdout:
                    if self._cancelled:
                        self._proc.terminate()
                        try:
                            self._proc.kill()
                        except Exception:
                            pass
                        self.finished.emit(False, tr("cancelled"))
                        return
                    line = line.strip()
                    m = _re.search(r'(\d+)\s*%', line)
                    if m:
                        pct = int(m.group(1))
                        self.progress.emit(min(pct, 99))
                    elif line:
                        pct = min(pct + 2, 95)
                        self.progress.emit(pct)

                self._proc.wait()
                if self._cancelled:
                    self.finished.emit(False, tr("cancelled"))
                    return

                if self._proc.returncode == 0:
                    key = f"flatpak:{real_id}"
                    if self.action == "install":
                        if key in self.backend._available_packages:
                            self.backend._available_packages[key].installed = True
                            self.backend._available_packages[key].has_update = False
                            self.backend._installed_packages[key] = self.backend._available_packages[key]
                        if key in self.backend._installed_packages:
                            self.backend._installed_packages[key].has_update = False
                        self.finished.emit(True, tr("installed_success", name=real_id))
                    else:
                        if key in self.backend._installed_packages:
                            del self.backend._installed_packages[key]
                        if key in self.backend._available_packages:
                            self.backend._available_packages[key].installed = False
                            self.backend._available_packages[key].has_update = False
                        self.finished.emit(True, tr("removed_success", name=real_id))
                else:
                    err = self._proc.stderr.read() if self._proc.stderr else "Flatpak işlemi başarısız oldu"
                    self.finished.emit(False, err)
                return

            # Simulated progress for demo mode (pisi not available)
            if not self.backend.is_pisi_available():
                import time
                for pct in range(0, 101, 10):
                    if self._cancelled:
                        self.finished.emit(False, "İptal edildi")
                        return
                    self.progress.emit(pct)
                    time.sleep(0.05)
                if self.action == "install":
                    ok, msg = self.backend.install_package(self.package_name)
                else:
                    ok, msg = self.backend.remove_package(self.package_name)
                self.finished.emit(ok, msg)
                return

            # Real pisi: run and parse progress from output
            import subprocess
            import os
            use_pkexec = hasattr(os, "geteuid") and os.geteuid() != 0
            base_cmd = ["pkexec", "pisi"] if use_pkexec else ["pisi"]

            if self.action == "install":
                cmd = base_cmd + ["install", "--yes-all", self.package_name]
            else:
                cmd = base_cmd + ["remove", "--yes-all", self.package_name]

            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            pct = 0
            for line in self._proc.stdout:
                if self._cancelled:
                    self._proc.terminate()
                    self.finished.emit(False, tr("cancelled"))
                    return
                line = line.strip()
                import re as _re
                m = _re.search(r'(\d+)\s*%', line)
                if m:
                    pct = int(m.group(1))
                    self.progress.emit(min(pct, 99))
                elif line:
                    pct = min(pct + 2, 95)
                    self.progress.emit(pct)

            self._proc.wait()
            if self._cancelled:
                self.finished.emit(False, tr("cancelled"))
                return
            if self._proc.returncode == 0:
                if self.action == "install":
                    if self.package_name in self.backend._available_packages:
                        self.backend._available_packages[self.package_name].installed = True
                        self.backend._available_packages[self.package_name].has_update = False
                        self.backend._installed_packages[self.package_name] = \
                            self.backend._available_packages[self.package_name]
                    if self.package_name in self.backend._installed_packages:
                        self.backend._installed_packages[self.package_name].has_update = False
                    self.finished.emit(True, tr("installed_success", name=self.package_name))
                else:
                    if self.package_name in self.backend._installed_packages:
                        del self.backend._installed_packages[self.package_name]
                    if self.package_name in self.backend._available_packages:
                        self.backend._available_packages[self.package_name].installed = False
                        self.backend._available_packages[self.package_name].has_update = False
                    self.finished.emit(True, tr("removed_success", name=self.package_name))
            else:
                err = self._proc.stderr.read() if self._proc.stderr else "Bilinmeyen hata"
                self.finished.emit(False, err)
        except Exception as e:
            self.finished.emit(False, str(e))


# ──────────────────────────────────────────────
#  Güncelleme Denetleme Worker Thread
# ──────────────────────────────────────────────
class UpdateCheckThread(QThread):
    progress       = pyqtSignal(int, str)
    finished_check = pyqtSignal(int, list, str)  # count, package_names, error_msg

    def __init__(self, backend: PisiBackend, update_repo: bool = True):
        super().__init__()
        self.backend = backend
        self.update_repo = update_repo

    def run(self):
        try:
            count, pkgs, err = self.backend.check_for_updates(
                progress_callback=lambda v, m: self.progress.emit(v, m),
                update_repo=self.update_repo
            )
            self.finished_check.emit(count, pkgs, err)
        except Exception as e:
            self.finished_check.emit(0, [], str(e))


# ──────────────────────────────────────────────
#  Depo Güncelleme Worker Thread
# ──────────────────────────────────────────────
class UpdateRepoThread(QThread):
    progress        = pyqtSignal(int, str)
    finished_update = pyqtSignal(bool, str)  # success, message

    def __init__(self, backend: PisiBackend):
        super().__init__()
        self.backend = backend

    def run(self):
        try:
            self.backend.update_repo_and_sync_cache(
                progress_callback=lambda v, m: self.progress.emit(v, m),
                update_repo=True
            )
            self.finished_update.emit(True, tr("repo_update_success"))
        except Exception as e:
            self.finished_update.emit(False, str(e))


# ──────────────────────────────────────────────
#  1. Discover (Keşfet) Görünümü
# ──────────────────────────────────────────────
class DiscoverView(QWidget):
    package_clicked = pyqtSignal(str)
    install_clicked = pyqtSignal(str, object)
    remove_clicked  = pyqtSignal(str, object)
    see_all_clicked  = pyqtSignal()
    card_created    = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body.setObjectName("discoverBody")
        lay = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(24)

        # ── Hero Banner ──
        # ── Hero Banner ──
        hero = QFrame()
        hero.setObjectName("heroBannerFrame")
        hero.setFixedHeight(180)
        hero.setStyleSheet("""
            QFrame#heroBannerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e2430, stop:0.6 #282c37, stop:1 #8e244d);
                border-radius: 16px;
                border: none;
            }
        """)
        h_lay = QHBoxLayout(hero)
        h_lay.setContentsMargins(32, 24, 24, 24)

        h_text = QVBoxLayout()
        h_text.setSpacing(6)

        sub = QLabel(tr("hero_subtitle"))
        sub.setStyleSheet("color: #a0a5b5; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; background: transparent; border: none;")
        h_text.addWidget(sub)

        title = QLabel(tr("hero_title"))
        title.setStyleSheet("color: white; font-size: 22px; font-weight: 900; line-height: 1.2; background: transparent; border: none;")
        h_text.addWidget(title)
        h_text.addStretch()

        h_lay.addLayout(h_text)
        h_lay.addStretch()

        nav_box = QHBoxLayout()
        nav_box.setSpacing(6)
        btn_prev = QPushButton("‹")
        btn_next = QPushButton("›")
        for b in (btn_prev, btn_next):
            b.setFixedSize(32, 32)
            b.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.8);
                    color: #1c1c1e;
                    border-radius: 16px;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background: white; }
            """)
            nav_box.addWidget(b)
        h_lay.addLayout(nav_box)

        lay.addWidget(hero)

        # ── Trending Apps ──
        th_box = QHBoxLayout()
        t_title = QLabel(tr("trending_apps"))
        t_title.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800; background: transparent; border: none;")
        th_box.addWidget(t_title)
        th_box.addStretch()

        btn_see_all = QPushButton(tr("see_all"))
        btn_see_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_see_all.setStyleSheet(f"color: {ThemeManager.accent_teal()}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        btn_see_all.clicked.connect(self.see_all_clicked.emit)
        th_box.addWidget(btn_see_all)
        lay.addLayout(th_box)

        self.trend_grid = QGridLayout()
        self.trend_grid.setSpacing(14)
        lay.addLayout(self.trend_grid)

        # ── Editörün Seçimleri ──
        ed_title = QLabel(tr("editors_choice"))
        ed_title.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800; background: transparent; border: none;")
        lay.addWidget(ed_title)

        ed_box = QHBoxLayout()
        ed_box.setSpacing(16)

        for grad in [
            "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a365d, stop:1 #0077b6)",
            "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1b4332, stop:1 #2d6a4f)"
        ]:
            pick = QFrame()
            pick.setObjectName("editorPickFrame")
            pick.setFixedHeight(140)
            pick.setStyleSheet(f"QFrame#editorPickFrame {{ background: {grad}; border-radius: 16px; border: none; }}")
            ed_box.addWidget(pick)

        lay.addLayout(ed_box)
        lay.addStretch()

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def display_packages(self, packages: list[PackageInfo]):
        while self.trend_grid.count():
            it = self.trend_grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        for i, pkg in enumerate(packages[:8]):
            card = TrendingAppCard(rank=i+1, package=pkg, show_delete=False)
            card.clicked.connect(self.package_clicked)
            card.install_clicked.connect(
                lambda name, _card=card: self.install_clicked.emit(name, _card.install_widget)
            )
            card.remove_clicked.connect(
                lambda name, _card=card: self.remove_clicked.emit(name, _card.install_widget)
            )
            self.trend_grid.addWidget(card, i // 2, i % 2)
            self.card_created.emit(card.install_widget)


# ──────────────────────────────────────────────
#  2. Category / List Görünümü (Lazy Loading: 18'er yükleme)
# ──────────────────────────────────────────────
class CategoryView(QWidget):
    package_clicked = pyqtSignal(str)
    install_clicked = pyqtSignal(str, object)
    remove_clicked  = pyqtSignal(str, object)
    card_created    = pyqtSignal(object)
    CHUNK_SIZE = 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_packages: list[PackageInfo] = []
        self._loaded_count = 0
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(18)

        # Başlık ve İkon
        top_box = QHBoxLayout()
        self.cat_icon = QLabel()
        self.cat_icon.setStyleSheet("background: transparent; border: none;")
        top_box.addWidget(self.cat_icon)

        self.cat_title = QLabel("Kategori")
        self.cat_title.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 22px; font-weight: 800; background: transparent; border: none;")
        top_box.addWidget(self.cat_title)
        top_box.addStretch()
        
        lay.addLayout(top_box)

        # Başlık
        sub_box = QHBoxLayout()
        sec_lbl = QLabel(tr("all_applications"))
        sec_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800; background: transparent; border: none;")
        sub_box.addWidget(sec_lbl)
        sub_box.addStretch()
        lay.addLayout(sub_box)

        # 2-Sütunlu Liste Izgarası
        self.grid = QGridLayout()
        self.grid.setSpacing(14)
        lay.addLayout(self.grid)

        lay.addStretch()
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll)

    def _on_scroll(self, value):
        vbar = self.scroll.verticalScrollBar()
        if value >= vbar.maximum() - 150:
            self._load_next_chunk()

    def _animate_card(self, card):
        eff = QGraphicsOpacityEffect(card)
        card.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", card)
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        def _cleanup():
            card.setGraphicsEffect(None)
        anim.finished.connect(_cleanup)
        anim.start()

    def _load_next_chunk(self):
        if self._loaded_count >= len(self._all_packages):
            return

        start = self._loaded_count
        end = min(start + self.CHUNK_SIZE, len(self._all_packages))

        for i in range(start, end):
            pkg = self._all_packages[i]
            card = PisiAppCard(package=pkg, show_delete=False)
            card.clicked.connect(self.package_clicked)
            card.install_clicked.connect(
                lambda name, _card=card: self.install_clicked.emit(name, _card.install_widget)
            )
            card.remove_clicked.connect(
                lambda name, _card=card: self.remove_clicked.emit(name, _card.install_widget)
            )
            self._animate_card(card)
            self.grid.addWidget(card, i // 2, i % 2)
            self.card_created.emit(card.install_widget)

        self._loaded_count = end
        QTimer.singleShot(50, self._check_fill)

    def _check_fill(self):
        if self._loaded_count < len(self._all_packages) and self.scroll.verticalScrollBar().maximum() <= 0:
            self._load_next_chunk()

    def display_category(self, cat_id: str, title: str, icon_name: str, packages: list[PackageInfo]):
        self.cat_title.setText(title)
        ico = get_kde_icon(icon_name)
        if not ico.isNull():
            self.cat_icon.setPixmap(ico.pixmap(32, 32))
        else:
            self.cat_icon.setText("📦")

        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        self._all_packages = list(packages)
        self._loaded_count = 0
        self.scroll.verticalScrollBar().setValue(0)
        self._load_next_chunk()


# ──────────────────────────────────────────────
#  3. Uygulama Detay Görünümü
# ──────────────────────────────────────────────
class AppDetailView(QWidget):
    install_clicked = pyqtSignal(str, object)
    remove_clicked  = pyqtSignal(str, object)
    cancel_clicked  = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.package: Optional[PackageInfo] = None
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        # Top App Info Header
        self._top_box_ref = QHBoxLayout()
        self._top_box_ref.setSpacing(18)

        self.ico_lbl = QLabel()
        self.ico_lbl.setFixedSize(80, 80)
        self.ico_lbl.setStyleSheet("background: transparent; border: none;")
        self._top_box_ref.addWidget(self.ico_lbl)

        info_lay = QVBoxLayout()
        info_lay.setSpacing(4)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_row.setContentsMargins(0, 0, 0, 0)

        self.name_lbl = QLabel()
        self.name_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 22px; font-weight: 800; background: transparent; border: none;")
        name_row.addWidget(self.name_lbl)

        self.flatpak_badge = QLabel("Flatpak")
        self.flatpak_badge.setStyleSheet("""
            QLabel {
                background-color: #1a6fcf;
                color: white;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 800;
                border: none;
            }
        """)
        self.flatpak_badge.setFixedHeight(20)
        self.flatpak_badge.setVisible(False)
        name_row.addWidget(self.flatpak_badge)
        name_row.addStretch()

        info_lay.addLayout(name_row)

        self.sub_lbl = QLabel()
        self.sub_lbl.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 13px; background: transparent; border: none;")
        info_lay.addWidget(self.sub_lbl)

        self.cat_lbl = QLabel()
        self.cat_lbl.setStyleSheet(f"color: {ThemeManager.accent_teal()}; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        info_lay.addWidget(self.cat_lbl)

        self._top_box_ref.addLayout(info_lay)
        self._top_box_ref.addStretch()

        # AppDetailView uses PisiInstallWidget for consistency
        # placeholder — will be set in display_package
        self._detail_install_widget = None

        lay.addLayout(self._top_box_ref)

        # Stats Bar (4 Column Box)
        self.stats_container = QVBoxLayout()
        lay.addLayout(self.stats_container)

        # Screenshot Gallery Container (Dinamik & Yatay Kaydırılabilir)
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setFixedHeight(240)
        self.gallery_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.gallery_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.gallery_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #38383a;
                border-radius: 4px;
            }
        """)

        gallery_widget = QWidget()
        gallery_widget.setStyleSheet("background: transparent;")
        self.gallery_container = QHBoxLayout(gallery_widget)
        self.gallery_container.setContentsMargins(0, 0, 0, 0)
        self.gallery_container.setSpacing(16)
        self.gallery_container.addStretch()

        self.gallery_scroll.setWidget(gallery_widget)
        lay.addWidget(self.gallery_scroll)

        # Hakkında
        ab_title = QLabel(tr("about"))
        ab_title.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800; background: transparent; border: none;")
        lay.addWidget(ab_title)

        self.desc_lbl = QLabel()
        self.desc_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; line-height: 1.5; background: transparent; border: none;")
        self.desc_lbl.setWordWrap(True)
        lay.addWidget(self.desc_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {ThemeManager.border()}; border: none; height: 1px;")
        lay.addWidget(sep)

        # Metadata 2x4 Grid
        self.meta_grid = QGridLayout()
        self.meta_grid.setSpacing(16)
        lay.addLayout(self.meta_grid)

        lay.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)

    def display_package(self, pkg: PackageInfo):
        self.package = pkg
        self.name_lbl.setText(pkg.display_name or pkg.name)
        
        if pkg.is_flatpak:
            origin_name = getattr(pkg, "origin", "Flatpak") or "Flatpak"
            self.flatpak_badge.setText(origin_name)
            self.flatpak_badge.setVisible(True)
        else:
            self.flatpak_badge.setVisible(False)

        self.sub_lbl.setText(pkg.summary)
        self.cat_lbl.setText(pkg.category.capitalize())
        self.desc_lbl.setText(pkg.description or pkg.summary)

        self.ico_lbl.setPixmap(load_app_icon(pkg.icon_path, pkg.icon_name, 80))

        # Rebuild install widget for this package
        if self._detail_install_widget is not None:
            try:
                self._detail_install_widget.setParent(None)
                self._detail_install_widget.deleteLater()
            except Exception:
                pass

        self._detail_install_widget = PisiInstallWidget(pkg, show_percent=True)
        self._detail_install_widget.install_clicked.connect(
            lambda name: self.install_clicked.emit(name, self._detail_install_widget)
        )
        self._detail_install_widget.remove_clicked.connect(
            lambda name: self.remove_clicked.emit(name, self._detail_install_widget)
        )
        self._detail_install_widget.cancel_clicked.connect(
            lambda name: self.cancel_clicked.emit(name) if hasattr(self, 'cancel_clicked') else None
        )
        self._top_box_ref.addWidget(self._detail_install_widget)

        # Stats Bar Update
        while self.stats_container.count():
            it = self.stats_container.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        self.stats_container.addWidget(PisiStatsBox(pkg))

        # Screenshot Gallery Temizle
        while self.gallery_container.count():
            it = self.gallery_container.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        # Eğer Flatpak uygulaması ise FlatHub API'sinden detaylı veri ve fotoğrafları çek
        if pkg.is_flatpak and hasattr(self, "backend"):
            self.desc_lbl.setText(pkg.description or pkg.summary or tr("loading_flathub"))
            def _load_flathub_data():
                info = self.backend.fetch_flathub_info(pkg.name)
                if info:
                    if info.get("summary"):
                        self.sub_lbl.setText(info["summary"])
                    if info.get("description"):
                        clean_desc = re.sub(r'<[^>]+>', '', info["description"]).strip()
                        self.desc_lbl.setText(clean_desc)
                    if info.get("developer"):
                        pkg.developer = info["developer"]
                    if info.get("local_icon"):
                        pkg.icon_path = info["local_icon"]
                        self.ico_lbl.setPixmap(load_app_icon(pkg.icon_path, pkg.icon_name, 80))
                    
                    # FlatHub ekran görüntülerini göster
                    sc_paths = info.get("screenshots", [])
                    if sc_paths:
                        for sc_p in sc_paths[:4]:
                            ss_card = QLabel()
                            ss_card.setFixedHeight(220)
                            ss_card.setCursor(Qt.CursorShape.PointingHandCursor)
                            px = QPixmap(sc_p)
                            if not px.isNull():
                                ss_card.setPixmap(px.scaledToHeight(220, Qt.TransformationMode.SmoothTransformation))
                                ss_card.setStyleSheet("border-radius: 12px; border: 1px solid transparent;")
                                path_copy = sc_p
                                ss_card.mousePressEvent = lambda ev, p=path_copy: self._open_image_viewer(p)
                                self.gallery_container.addWidget(ss_card)
                        self.gallery_container.addStretch()

            QTimer.singleShot(10, _load_flathub_data)
        else:
            # PiSi paketi için fotoğraf galerisi gösterilmez
            self.desc_lbl.setText(pkg.description or pkg.summary or tr("no_description"))

        # Metadata Grid Update
        while self.meta_grid.count():
            it = self.meta_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        origin_title = getattr(pkg, "origin", "Flatpak") if pkg.is_flatpak else tr("lupus_main_repo")
        metas = [
            (tr("version"), pkg.version or "1.0.0"),
            (tr("download_size"), pkg.download_size or "10.1 MB"),
            (tr("required_space"), pkg.installed_size or "32.8 MB"),
            (tr("type"), tr("flatpak_pkg") if pkg.is_flatpak else tr("pisi_pkg")),
            (tr("category"), pkg.category.capitalize()),
            (tr("license"), pkg.license or "GPL"),
            (tr("repo_origin"), origin_title),
            (tr("developer"), pkg.developer or (tr("flathub_community") if pkg.is_flatpak else tr("lupus_community"))),
        ]

        for i, (k, v) in enumerate(metas):
            row = i // 4
            col = i % 4

            box = QVBoxLayout()
            box.setSpacing(4)
            kl = QLabel(k)
            kl.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 12px;")
            box.addWidget(kl)

            vl = QLabel(v)
            vl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; font-weight: 700;")
            box.addWidget(vl)

            w = QWidget()
            w.setLayout(box)
            self.meta_grid.addWidget(w, row, col)

    def _open_image_viewer(self, image_path: str):
        dlg = ImageViewerDialog(image_path, self)
        dlg.exec()

    def _on_action(self):
        """Unused - kept for compat."""
        pass


# ──────────────────────────────────────────────
#  4. Installed Apps Görünümü (Lazy Loading: 18'er yükleme)
# ──────────────────────────────────────────────
class InstalledView(QWidget):
    package_clicked       = pyqtSignal(str)
    install_clicked       = pyqtSignal(str, object)
    remove_clicked        = pyqtSignal(str, object)
    check_updates_clicked = pyqtSignal()
    update_repo_clicked   = pyqtSignal()
    bind_workers_requested = pyqtSignal()
    card_created          = pyqtSignal(object)
    CHUNK_SIZE = 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_packages: list[PackageInfo] = []
        self._loaded_count = 0
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        # Header
        top_box = QHBoxLayout()
        ico = QLabel("⬇")
        ico.setStyleSheet("font-size: 32px;")
        top_box.addWidget(ico)

        t = QLabel(tr("updates_title"))
        t.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 22px; font-weight: 800;")
        top_box.addWidget(t)
        top_box.addStretch()

        self.btn_update_repo = QPushButton(tr("btn_update_repo"))
        self.btn_update_repo.setIcon(QIcon.fromTheme("view-refresh"))
        self.btn_update_repo.setIconSize(QSize(16, 16))
        self.btn_update_repo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update_repo.setFixedHeight(34)
        self.btn_update_repo.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeManager.accent_teal()};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.accent_teal_hover()};
            }}
            QPushButton:disabled {{
                background-color: {ThemeManager.border()};
                color: {ThemeManager.text_secondary()};
            }}
        """)
        self.btn_update_repo.clicked.connect(self.update_repo_clicked.emit)
        top_box.addWidget(self.btn_update_repo)

        self.btn_check_updates = QPushButton(tr("btn_check_updates"))
        self.btn_check_updates.setIcon(QIcon.fromTheme("gtk-refresh"))
        self.btn_check_updates.setIconSize(QSize(16, 16))
        self.btn_check_updates.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check_updates.setFixedHeight(34)
        self.btn_check_updates.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeManager.accent_teal()};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.accent_teal_hover()};
            }}
            QPushButton:disabled {{
                background-color: {ThemeManager.border()};
                color: {ThemeManager.text_secondary()};
            }}
        """)
        self.btn_check_updates.clicked.connect(self.check_updates_clicked.emit)
        top_box.addWidget(self.btn_check_updates)

        lay.addLayout(top_box)

        # Updates Section
        self.upd_header = QLabel(tr("downloads_and_updates", count=0))
        self.upd_header.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800;")
        lay.addWidget(self.upd_header)

        self.upd_grid = QGridLayout()
        self.upd_grid.setSpacing(14)
        lay.addLayout(self.upd_grid)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {ThemeManager.border()}; border: none; height: 1px;")
        lay.addWidget(sep)

        # All Installed Apps Section
        all_box = QHBoxLayout()
        all_lbl = QLabel(tr("all_applications"))
        all_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800;")
        all_box.addWidget(all_lbl)
        all_box.addStretch()
        lay.addLayout(all_box)

        self.inst_grid = QGridLayout()
        self.inst_grid.setSpacing(14)
        lay.addLayout(self.inst_grid)

        lay.addStretch()
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll)

    def _on_scroll(self, value):
        vbar = self.scroll.verticalScrollBar()
        if value >= vbar.maximum() - 150:
            self._load_next_chunk()

    def _animate_card(self, card):
        eff = QGraphicsOpacityEffect(card)
        card.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", card)
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        def _cleanup():
            card.setGraphicsEffect(None)
        anim.finished.connect(_cleanup)
        anim.start()

    def _load_next_chunk(self):
        if self._loaded_count >= len(self._all_packages):
            return

        start = self._loaded_count
        end = min(start + self.CHUNK_SIZE, len(self._all_packages))

        for i in range(start, end):
            pkg = self._all_packages[i]
            card = PisiAppCard(pkg)
            card.clicked.connect(self.package_clicked)
            card.install_clicked.connect(
                lambda name, _card=card: self.install_clicked.emit(name, _card.install_widget)
            )
            card.remove_clicked.connect(
                lambda name, _card=card: self.remove_clicked.emit(name, _card.install_widget)
            )
            self._animate_card(card)
            self.inst_grid.addWidget(card, i // 2, i % 2)
            self.card_created.emit(card.install_widget)

        self._loaded_count = end
        QTimer.singleShot(50, self._check_fill)

    def _check_fill(self):
        if self._loaded_count < len(self._all_packages) and self.scroll.verticalScrollBar().maximum() <= 0:
            self._load_next_chunk()

    def display_installed(self, packages: list[PackageInfo], active_installing_pkgs: list[PackageInfo] = None):
        while self.upd_grid.count():
            it = self.upd_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        while self.inst_grid.count():
            it = self.inst_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        active_installing_pkgs = active_installing_pkgs or []
        updates = [p for p in packages if p.has_update]

        # Hem güncellenecekler hem de o an indirilenler üst bölümde gösterilir
        # Tekrar eden paketleri önle (aktif indirilen paket güncelleme listesinde de olabilir)
        seen_names = set()
        display_top = []
        for p in active_installing_pkgs + updates:
            if p.name not in seen_names:
                seen_names.add(p.name)
                display_top.append(p)
        self.upd_header.setText(tr("downloads_and_updates", count=len(display_top)))

        for i, pkg in enumerate(display_top):
            card = PisiAppCard(pkg)
            card.clicked.connect(self.package_clicked)
            card.install_clicked.connect(
                lambda name, _card=card: self.install_clicked.emit(name, _card.install_widget)
            )
            card.remove_clicked.connect(
                lambda name, _card=card: self.remove_clicked.emit(name, _card.install_widget)
            )
            self.upd_grid.addWidget(card, i // 2, i % 2)
            self.card_created.emit(card.install_widget)
        # Aktif worker'ları 'indirilenler' bölümündeki kartlarla eşleştir
        self.active_installing_pkgs = active_installing_pkgs
        self.bind_workers_requested.emit()

        sorted_packages = sorted(packages, key=lambda p: (p.display_name or p.name).lower())
        self._all_packages = sorted_packages
        self._loaded_count = 0
        self.scroll.verticalScrollBar().setValue(0)
        self._load_next_chunk()


# ──────────────────────────────────────────────
#  5. Arama Sonuçları Görünümü (Lazy Loading: 18'er yükleme)
# ──────────────────────────────────────────────
class SearchResultsView(QWidget):
    package_clicked = pyqtSignal(str)
    install_clicked = pyqtSignal(str, object)
    card_created    = pyqtSignal(object)
    CHUNK_SIZE = 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_gui_apps: list[PackageInfo] = []
        self._all_lib_pkgs: list[PackageInfo] = []
        self._loaded_gui_count = 0
        self._loaded_lib_count = 0
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(18)

        # Header
        top_box = QHBoxLayout()
        ico = QLabel("🔍")
        ico.setStyleSheet("font-size: 28px;")
        top_box.addWidget(ico)

        self.query_title = QLabel(tr("search_results_title"))
        self.query_title.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 20px; font-weight: 800;")
        top_box.addWidget(self.query_title)
        top_box.addStretch()
        lay.addLayout(top_box)

        # Section 1: Tüm Uygulamalar
        apps_hdr = QLabel(tr("all_applications"))
        apps_hdr.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800;")
        lay.addWidget(apps_hdr)

        self.apps_grid = QGridLayout()
        self.apps_grid.setSpacing(14)
        lay.addLayout(self.apps_grid)

        # Section 2: Paketler
        pkgs_hdr = QLabel(tr("packages"))
        pkgs_hdr.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800;")
        lay.addWidget(pkgs_hdr)

        self.pkgs_grid = QGridLayout()
        self.pkgs_grid.setSpacing(14)
        lay.addLayout(self.pkgs_grid)

        lay.addStretch()
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll)

    def _on_scroll(self, value):
        vbar = self.scroll.verticalScrollBar()
        if value >= vbar.maximum() - 150:
            self._load_next_chunk()

    def _animate_card(self, card):
        eff = QGraphicsOpacityEffect(card)
        card.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", card)
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        def _cleanup():
            card.setGraphicsEffect(None)
        anim.finished.connect(_cleanup)
        anim.start()

    def _load_next_chunk(self):
        if self._loaded_gui_count < len(self._all_gui_apps):
            start = self._loaded_gui_count
            end = min(start + self.CHUNK_SIZE, len(self._all_gui_apps))
            for i in range(start, end):
                pkg = self._all_gui_apps[i]
                card = PisiAppCard(pkg, show_delete=False)
                card.clicked.connect(self.package_clicked)
                card.install_clicked.connect(
                    lambda name, _card=card: self.install_clicked.emit(name, _card.install_widget)
                )
                self._animate_card(card)
                self.apps_grid.addWidget(card, i // 2, i % 2)
                self.card_created.emit(card.install_widget)
            self._loaded_gui_count = end
            QTimer.singleShot(50, self._check_fill)
        elif self._loaded_lib_count < len(self._all_lib_pkgs):
            start = self._loaded_lib_count
            end = min(start + self.CHUNK_SIZE, len(self._all_lib_pkgs))
            for i in range(start, end):
                pkg = self._all_lib_pkgs[i]
                card = PisiAppCard(pkg, show_delete=False)
                card.clicked.connect(self.package_clicked)
                card.install_clicked.connect(
                    lambda name, _card=card: self.install_clicked.emit(name, _card.install_widget)
                )
                self._animate_card(card)
                self.pkgs_grid.addWidget(card, i // 2, i % 2)
                self.card_created.emit(card.install_widget)
            self._loaded_lib_count = end
            QTimer.singleShot(50, self._check_fill)

    def _check_fill(self):
        has_more = (self._loaded_gui_count < len(self._all_gui_apps)) or (self._loaded_lib_count < len(self._all_lib_pkgs))
        if has_more and self.scroll.verticalScrollBar().maximum() <= 0:
            self._load_next_chunk()

    def display_results(self, query: str, results: list[PackageInfo]):
        self.query_title.setText(tr("results_for", query=query))

        while self.apps_grid.count():
            it = self.apps_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        while self.pkgs_grid.count():
            it = self.pkgs_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        gui_apps = [p for p in results if p.is_a != "library"]
        lib_pkgs = [p for p in results if p.is_a == "library"]

        if not gui_apps and not lib_pkgs:
            gui_apps = results

        self._all_gui_apps = gui_apps
        self._all_lib_pkgs = lib_pkgs
        self._loaded_gui_count = 0
        self._loaded_lib_count = 0

        self.scroll.verticalScrollBar().setValue(0)
        self._load_next_chunk()




# ──────────────────────────────────────────────
#  Yükleme Ekranı (Loading Overlay)
# ──────────────────────────────────────────────
class LoadingOverlay(QWidget):
    """Paketler arka planda yüklenirken gösterilen tam ekran yükleme ekranı."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60 fps

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(24)

        # Logo
        self._logo_lbl = QLabel()
        self._logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(APP_ICON_PATH):
            pix = QPixmap(APP_ICON_PATH).scaled(
                72, 72,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._logo_lbl.setPixmap(pix)
        else:
            self._logo_lbl.setText("📦")
            self._logo_lbl.setStyleSheet("font-size: 48px;")
        lay.addWidget(self._logo_lbl)

        # Uygulama adı
        app_lbl = QLabel("PiSiM")
        app_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_lbl.setStyleSheet(
            "font-size: 22px; font-weight: 800; "
            f"color: {ThemeManager.text_primary()}; background: transparent;"
        )
        lay.addWidget(app_lbl)

        # Dönen çember (canvas yerine QLabel + unicode spinner)
        self._spinner_lbl = QLabel("◌")
        self._spinner_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner_lbl.setStyleSheet(
            f"font-size: 36px; color: {ThemeManager.accent_teal()}; background: transparent;"
        )
        lay.addWidget(self._spinner_lbl)

        # İlerleme çubuğu
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedSize(320, 6)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background: {ThemeManager.border()};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ThemeManager.accent_teal()}, stop:1 #6c63ff);
                border-radius: 3px;
            }}
        """)
        bar_wrap = QWidget()
        bar_wrap.setStyleSheet("background: transparent;")
        bw = QHBoxLayout(bar_wrap)
        bw.setContentsMargins(0, 0, 0, 0)
        bw.addStretch()
        bw.addWidget(self._bar)
        bw.addStretch()
        lay.addWidget(bar_wrap)

        # Durum mesajı
        self._msg_lbl = QLabel(tr("loading_init"))
        self._msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg_lbl.setStyleSheet(
            f"color: {ThemeManager.text_secondary()}; font-size: 13px; background: transparent;"
        )
        lay.addWidget(self._msg_lbl)

    _SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def _tick(self):
        self._angle = (self._angle + 1) % len(self._SPINNER_FRAMES)
        self._spinner_lbl.setText(self._SPINNER_FRAMES[self._angle])

    def update_progress(self, value: int, message: str):
        self._bar.setValue(max(0, min(100, value)))
        self._msg_lbl.setText(message)

    def stop(self):
        self._timer.stop()


# ──────────────────────────────────────────────
#  Ayarlar Görünümü (SettingsView)
# ──────────────────────────────────────────────
class SettingsView(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager.load_settings()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(24)

        # Header
        title_box = QHBoxLayout()
        ico = QLabel()
        kde_ico = get_kde_icon("applications-other-symbolic")
        if not kde_ico.isNull():
            ico.setPixmap(kde_ico.pixmap(28, 28))
        else:
            ico.setText("⚙️")
            ico.setStyleSheet("font-size: 24px;")
        title_box.addWidget(ico)

        self.title_lbl = QLabel(tr("settings_title"))
        self.title_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 22px; font-weight: 800;")
        title_box.addWidget(self.title_lbl)
        title_box.addStretch()
        lay.addLayout(title_box)

        # Section 1: General & Autostart
        self.lbl_sec1 = self._create_section_label(tr("settings_section_general"))
        lay.addWidget(self.lbl_sec1)

        card1 = self._create_card()
        c1_lay = QVBoxLayout(card1)
        c1_lay.setContentsMargins(20, 16, 20, 16)
        c1_lay.setSpacing(10)

        self.chk_autostart = QCheckBox(tr("settings_autostart"))
        self.chk_autostart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_autostart.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeManager.text_primary()};")
        self.chk_autostart.setChecked(SettingsManager.is_autostart_enabled() or self.settings.get("autostart", False))
        self.chk_autostart.toggled.connect(self._on_changed)
        c1_lay.addWidget(self.chk_autostart)

        self.sub1 = QLabel(tr("settings_autostart_desc"))
        self.sub1.setStyleSheet(f"font-size: 12px; color: {ThemeManager.text_secondary()}; margin-left: 24px;")
        c1_lay.addWidget(self.sub1)

        self.chk_close_to_tray = QCheckBox(tr("settings_close_to_tray"))
        self.chk_close_to_tray.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_close_to_tray.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeManager.text_primary()};")
        self.chk_close_to_tray.setChecked(self.settings.get("close_to_tray", True))
        self.chk_close_to_tray.toggled.connect(self._on_changed)
        c1_lay.addWidget(self.chk_close_to_tray)

        self.sub2 = QLabel(tr("settings_close_to_tray_desc"))
        self.sub2.setStyleSheet(f"font-size: 12px; color: {ThemeManager.text_secondary()}; margin-left: 24px;")
        c1_lay.addWidget(self.sub2)

        lay.addWidget(card1)

        # Section 2: Updates
        self.lbl_sec2 = self._create_section_label(tr("settings_section_updates"))
        lay.addWidget(self.lbl_sec2)

        card2 = self._create_card()
        c2_lay = QVBoxLayout(card2)
        c2_lay.setContentsMargins(20, 16, 20, 16)
        c2_lay.setSpacing(12)

        self.lbl_int = QLabel(tr("settings_auto_check_interval"))
        self.lbl_int.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeManager.text_primary()};")
        c2_lay.addWidget(self.lbl_int)

        self.combo_interval = QComboBox()
        self.combo_interval.setFixedSize(280, 36)
        self.combo_interval.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_interval.setStyleSheet(f"""
            QComboBox {{
                background-color: {ThemeManager.sidebar_bg()};
                color: {ThemeManager.text_primary()};
                border: 1px solid {ThemeManager.border()};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {ThemeManager.text_secondary()};
            }}
        """)
        self._populate_intervals()
        self.combo_interval.currentIndexChanged.connect(self._on_changed)
        c2_lay.addWidget(self.combo_interval)

        self.chk_auto_install = QCheckBox(tr("settings_auto_install_updates"))
        self.chk_auto_install.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_auto_install.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeManager.text_primary()}; margin-top: 6px;")
        self.chk_auto_install.setChecked(self.settings.get("auto_install_updates", False))
        self.chk_auto_install.toggled.connect(self._on_changed)
        c2_lay.addWidget(self.chk_auto_install)

        self.sub_auto_install = QLabel(tr("settings_auto_install_updates_desc"))
        self.sub_auto_install.setStyleSheet(f"font-size: 12px; color: {ThemeManager.text_secondary()}; margin-left: 24px;")
        c2_lay.addWidget(self.sub_auto_install)

        lay.addWidget(card2)

        # Section 3: Language
        self.lbl_sec3 = self._create_section_label(tr("settings_section_language"))
        lay.addWidget(self.lbl_sec3)

        card3 = self._create_card()
        c3_lay = QVBoxLayout(card3)
        c3_lay.setContentsMargins(20, 16, 20, 16)
        c3_lay.setSpacing(12)

        self.lbl_lang = QLabel(tr("settings_language_label"))
        self.lbl_lang.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeManager.text_primary()};")
        c3_lay.addWidget(self.lbl_lang)

        self.combo_lang = QComboBox()
        self.combo_lang.setFixedSize(280, 36)
        self.combo_lang.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_lang.setStyleSheet(f"""
            QComboBox {{
                background-color: {ThemeManager.sidebar_bg()};
                color: {ThemeManager.text_primary()};
                border: 1px solid {ThemeManager.border()};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {ThemeManager.text_secondary()};
            }}
        """)
        self.combo_lang.addItem("Türkçe 🇹🇷", "tr")
        self.combo_lang.addItem("English 🇬🇧", "en")
        curr_lang = self.settings.get("language", I18n.get_lang())
        if curr_lang == "en":
            self.combo_lang.setCurrentIndex(1)
        else:
            self.combo_lang.setCurrentIndex(0)
        self.combo_lang.currentIndexChanged.connect(self._on_changed)
        c3_lay.addWidget(self.combo_lang)

        lay.addWidget(card3)

        # Section 4: Hakkında
        self.lbl_sec4 = self._create_section_label(tr("nav_about"))
        lay.addWidget(self.lbl_sec4)

        card_about = QWidget()
        card_about.setStyleSheet("background: transparent; border: none;")
        ca_lay = QVBoxLayout(card_about)
        ca_lay.setContentsMargins(0, 8, 0, 8)
        ca_lay.setSpacing(14)

        about_top = QHBoxLayout()
        about_icon = QLabel()
        if os.path.exists(APP_ICON_PATH):
            about_icon.setPixmap(QPixmap(APP_ICON_PATH).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            about_icon.setText("📦")
            about_icon.setStyleSheet("font-size: 36px;")
        about_top.addWidget(about_icon)

        about_text_lay = QVBoxLayout()
        self.about_name_lbl = QLabel(tr("about_app_name"))
        self.about_name_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 16px; font-weight: 800;")
        about_text_lay.addWidget(self.about_name_lbl)

        self.about_ver_lbl = QLabel(tr("about_version"))
        self.about_ver_lbl.setStyleSheet(f"""
            background-color: {ThemeManager.accent_teal()};
            color: white;
            padding: 2px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
        """)
        about_text_lay.addWidget(self.about_ver_lbl, 0, Qt.AlignmentFlag.AlignLeft)
        about_top.addLayout(about_text_lay)
        about_top.addStretch()
        ca_lay.addLayout(about_top)


        self.about_desc_lbl = QLabel(tr("about_description"))
        self.about_desc_lbl.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 13px;")
        self.about_desc_lbl.setWordWrap(True)
        ca_lay.addWidget(self.about_desc_lbl)

        self.about_dev_lbl = QLabel(f"🏢 {tr('about_developer')}")
        self.about_dev_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; font-weight: 600;")
        ca_lay.addWidget(self.about_dev_lbl)

        self.about_web_lbl = QLabel(f"🌐 <a href='https://www.teknoanka.com/' style='color:{ThemeManager.accent_teal()}; text-decoration:none;'>www.teknoanka.com</a>")
        self.about_web_lbl.setOpenExternalLinks(True)
        self.about_web_lbl.setStyleSheet("font-size: 13px; font-weight: 600;")
        ca_lay.addWidget(self.about_web_lbl)

        self.about_lic_lbl = QLabel(f"📜 {tr('about_license')}")
        self.about_lic_lbl.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 13px;")
        ca_lay.addWidget(self.about_lic_lbl)

        lay.addWidget(card_about)

        lay.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _populate_intervals(self):
        self.combo_interval.blockSignals(True)
        self.combo_interval.clear()
        interval_map = [
            (0, tr("interval_disabled")),
            (1, tr("interval_1h")),
            (4, tr("interval_4h")),
            (12, tr("interval_12h")),
            (24, tr("interval_24h")),
        ]
        curr_val = self.settings.get("check_interval_hours", 4)
        selected_idx = 2
        for idx, (val, txt) in enumerate(interval_map):
            self.combo_interval.addItem(txt, val)
            if val == curr_val:
                selected_idx = idx
        self.combo_interval.setCurrentIndex(selected_idx)
        self.combo_interval.blockSignals(False)

    def _create_section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {ThemeManager.accent_teal()}; font-size: 13px; font-weight: 800; text-transform: uppercase;")
        return lbl

    def _create_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.sidebar_bg()};
                border: 1px solid {ThemeManager.border()};
                border-radius: 12px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
            QCheckBox {{
                border: none;
                background: transparent;
            }}
        """)
        return card

    def _on_changed(self):
        autostart = self.chk_autostart.isChecked()
        close_to_tray = self.chk_close_to_tray.isChecked()
        auto_install = self.chk_auto_install.isChecked()
        interval = self.combo_interval.currentData()
        lang = self.combo_lang.currentData()

        self.settings["autostart"] = autostart
        self.settings["close_to_tray"] = close_to_tray
        self.settings["auto_install_updates"] = auto_install
        self.settings["check_interval_hours"] = interval if interval is not None else 4
        self.settings["language"] = lang

        SettingsManager.set_autostart(autostart)
        SettingsManager.save_settings(self.settings)
        I18n.set_lang(lang)
        self.settings_changed.emit(self.settings)

    def retranslate_ui(self):
        """Dil değiştiğinde UI metinlerini günceller."""
        self.title_lbl.setText(tr("settings_title"))
        self.lbl_sec1.setText(tr("settings_section_general"))
        self.chk_autostart.setText(tr("settings_autostart"))
        self.sub1.setText(tr("settings_autostart_desc"))
        self.chk_close_to_tray.setText(tr("settings_close_to_tray"))
        self.sub2.setText(tr("settings_close_to_tray_desc"))
        self.lbl_sec2.setText(tr("settings_section_updates"))
        self.lbl_int.setText(tr("settings_auto_check_interval"))
        self._populate_intervals()
        self.chk_auto_install.setText(tr("settings_auto_install_updates"))
        self.sub_auto_install.setText(tr("settings_auto_install_updates_desc"))
        self.lbl_sec3.setText(tr("settings_section_language"))
        self.lbl_lang.setText(tr("settings_language_label"))
        # Hakkında bölümü
        if hasattr(self, 'lbl_sec4'):
            self.lbl_sec4.setText(tr("nav_about"))
        if hasattr(self, 'about_name_lbl'):
            self.about_name_lbl.setText(tr("about_app_name"))
        if hasattr(self, 'about_ver_lbl'):
            self.about_ver_lbl.setText(tr("about_version"))
        if hasattr(self, 'about_desc_lbl'):
            self.about_desc_lbl.setText(tr("about_description"))
        if hasattr(self, 'about_dev_lbl'):
            self.about_dev_lbl.setText(f"🏢 {tr('about_developer')}")
        if hasattr(self, 'about_lic_lbl'):
            self.about_lic_lbl.setText(f"📜 {tr('about_license')}")


# ──────────────────────────────────────────────
#  Hakkında Görünümü (AboutView)
# ──────────────────────────────────────────────
class AboutView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(36, 48, 36, 36)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        # Logo
        self.logo_lbl = QLabel()
        if os.path.exists(APP_ICON_PATH):
            self.logo_lbl.setPixmap(QPixmap(APP_ICON_PATH).scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.logo_lbl.setText("📦")
            self.logo_lbl.setStyleSheet("font-size: 72px;")
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.logo_lbl)

        # Title
        self.title_lbl = QLabel(tr("about_app_name"))
        self.title_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 26px; font-weight: 800;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.title_lbl)

        # Version Pill
        self.ver_lbl = QLabel(tr("about_version"))
        self.ver_lbl.setStyleSheet(f"""
            background-color: {ThemeManager.accent_teal()};
            color: white;
            padding: 4px 16px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 700;
        """)
        self.ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.ver_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        # Description
        self.desc_lbl = QLabel(tr("about_description"))
        self.desc_lbl.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 14px; margin-top: 8px;")
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.desc_lbl)

        # Details Card
        card = QFrame()
        card.setFixedWidth(540)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.sidebar_bg()};
                border: 1px solid {ThemeManager.border()};
                border-radius: 14px;
            }}
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(24, 20, 24, 20)
        c_lay.setSpacing(14)

        self.dev_lbl = QLabel(f"🏢 {tr('about_developer')}")
        self.dev_lbl.setStyleSheet(f"color: {ThemeManager.text_primary()}; font-size: 13px; font-weight: 600;")
        c_lay.addWidget(self.dev_lbl)

        self.web_lbl = QLabel(f"🌐 <a href='https://www.teknoanka.com/' style='color:{ThemeManager.accent_teal()}; text-decoration:none;'>www.teknoanka.com</a>")
        self.web_lbl.setOpenExternalLinks(True)
        self.web_lbl.setStyleSheet("font-size: 13px; font-weight: 600;")
        c_lay.addWidget(self.web_lbl)

        self.lic_lbl = QLabel(f"📜 {tr('about_license')}")
        self.lic_lbl.setStyleSheet(f"color: {ThemeManager.text_secondary()}; font-size: 13px;")
        c_lay.addWidget(self.lic_lbl)

        lay.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

        lay.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def retranslate_ui(self):
        """Dil değiştiğinde UI metinlerini günceller."""
        self.title_lbl.setText(tr("about_app_name"))
        self.ver_lbl.setText(tr("about_version"))
        self.desc_lbl.setText(tr("about_description"))
        self.dev_lbl.setText(f"🏢 {tr('about_developer')}")
        self.lic_lbl.setText(f"📜 {tr('about_license')}")


# ──────────────────────────────────────────────
#  PiSiM Market Ana Pencere (MainWindow)
# ──────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self, start_minimized: bool = False):
        super().__init__()
        self.settings = SettingsManager.load_settings()
        self.start_minimized = start_minimized
        self._is_quitting = False

        # Dil ayarını uygula
        I18n.set_lang(self.settings.get("language", "tr"))

        self.backend = PisiBackend()
        self._all_packages: list[PackageInfo] = []
        self._history_stack: list[str] = []

        self.setWindowTitle("PiSiM")
        self.setMinimumSize(1400, 820)

        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        self._load_fonts()
        self._build_ui()
        self.apply_theme()

        self._setup_system_tray()
        self._setup_auto_update_timer()

        QTimer.singleShot(100, self._start_load)

    def _load_fonts(self):
        for path in [
            "/usr/share/fonts/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/noto/NotoSans-Bold.ttf",
        ]:
            QFontDatabase.addApplicationFont(path)

    def apply_theme(self):
        """Sisteme göre otomatik temayı uygular"""
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {ThemeManager.bg()}; }}
            QWidget {{ color: {ThemeManager.text_primary()}; font-family: 'Noto Sans', 'Segoe UI', sans-serif; }}
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {ThemeManager.border()}; border-radius: 4px; }}
        """)

        self.sidebar.setStyleSheet(f"QFrame {{ background-color: {ThemeManager.sidebar_bg()}; border-right: 1px solid {ThemeManager.border()}; }}")
        self.topbar.setStyleSheet(f"QFrame {{ background-color: {ThemeManager.bg()}; border-bottom: 1px solid {ThemeManager.border()}; }}")
        if hasattr(self, "header_frame"):
            self.header_frame.setStyleSheet(f"QFrame {{ background-color: {ThemeManager.sidebar_bg()}; border-bottom: 1px solid {ThemeManager.border()}; }}")
        if hasattr(self, "sidebar_sep"):
            self.sidebar_sep.setStyleSheet(f"background-color: {ThemeManager.border()}; border: none;")

        if hasattr(self, "btn_header_settings"):
            self.btn_header_settings.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                    color: {ThemeManager.text_primary()};
                    font-size: 18px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.border()};
                }}
                QPushButton:pressed {{
                    background-color: {ThemeManager.accent_teal()}22;
                }}
            """)

        for btn in self.sidebar_buttons.values():
            btn.update_style()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        hl = QHBoxLayout(root)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)

        # ── Sol Menü (Sidebar) ──
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        sb_lay = QVBoxLayout(self.sidebar)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)

        # ── Sabit Logo Header ──────────────────────────────
        self.header_frame = QFrame()
        self.header_frame.setObjectName("sidebarHeader")
        self.header_frame.setFixedHeight(56)
        header_lay = QHBoxLayout(self.header_frame)
        header_lay.setContentsMargins(14, 0, 14, 0)
        header_lay.setSpacing(10)

        ico_lbl = QLabel()
        if os.path.exists(APP_ICON_PATH):
            ico_lbl.setPixmap(
                QPixmap(APP_ICON_PATH).scaled(
                    30, 30,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            ico_lbl.setText("📦")
        ico_lbl.setStyleSheet("background: transparent; border: none;")
        header_lay.addWidget(ico_lbl)

        title_lbl = QLabel("PiSiM")
        title_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 800; border: none; background: transparent;"
        )
        header_lay.addWidget(title_lbl)
        header_lay.addStretch()
        sb_lay.addWidget(self.header_frame)

        # ── Kaydırılabilir Kategoriler Bölümü ──────────────
        scroll_w = QWidget()
        scroll_w.setStyleSheet("background: transparent;")
        self.sb_lay = QVBoxLayout(scroll_w)
        self.sb_lay.setContentsMargins(10, 8, 10, 8)
        self.sb_lay.setSpacing(2)

        # Sidebar Buttons Group
        self.nav_grp = QButtonGroup(self)
        self.sidebar_buttons = {}

        # İlk olarak Tüm Uygulamalar butonunu koy
        for cat_id, icon_name, label in [
            ("all", "plasma-search", tr("nav_discover")),
        ]:
            btn = PisiSidebarButton(icon_name=icon_name, label=label, cat_id=cat_id)
            if cat_id == "all":
                btn.setChecked(True)
            cat_id_copy = cat_id
            btn.clicked.connect(lambda _, c=cat_id_copy: self._nav_category(c))
            self.nav_grp.addButton(btn)
            self.sidebar_buttons[cat_id] = btn
            self.sb_lay.addWidget(btn)

        self.sb_lay.addStretch()
        sb_lay.addWidget(scroll_w, 1)

        # ── Ayrıştırıcı Çizgi ve En Alttaki Butonlar ──
        self.sidebar_sep = QFrame()
        self.sidebar_sep.setFrameShape(QFrame.Shape.HLine)
        self.sidebar_sep.setFixedHeight(1)
        self.sidebar_sep.setStyleSheet(f"background-color: {ThemeManager.border()}; border: none;")
        sb_lay.addWidget(self.sidebar_sep)

        bottom_w = QWidget()
        bottom_w.setStyleSheet("background: transparent;")
        b_lay = QVBoxLayout(bottom_w)
        b_lay.setContentsMargins(10, 6, 10, 8)
        b_lay.setSpacing(2)

        btn_installed = PisiSidebarButton(
            icon_name="system-software-install", label=tr("nav_updates"), cat_id="installed"
        )
        btn_installed.clicked.connect(lambda _, c="installed": self._nav_category(c))
        self.nav_grp.addButton(btn_installed)
        self.sidebar_buttons["installed"] = btn_installed
        b_lay.addWidget(btn_installed)

        sb_lay.addWidget(bottom_w)

        hl.addWidget(self.sidebar)

        # ── Sağ İçerik Bölgesi ──
        right_w = QWidget()
        r_lay = QVBoxLayout(right_w)
        r_lay.setContentsMargins(0, 0, 0, 0)
        r_lay.setSpacing(0)

        # Üst Navigasyon Çubuğu
        self.topbar = QFrame()
        self.topbar.setFixedHeight(56)
        tb_lay = QHBoxLayout(self.topbar)
        tb_lay.setContentsMargins(20, 0, 20, 0)
        tb_lay.setSpacing(12)

        # Geri Butonu
        btn_back = QPushButton("‹")
        btn_back.setFixedSize(32, 32)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(f"QPushButton {{ background: transparent; color: {ThemeManager.text_primary()}; border: none; font-size: 20px; font-weight: bold; }}")
        btn_back.clicked.connect(self._go_back)
        tb_lay.addWidget(btn_back)

        tb_lay.addStretch()

        # Arama Kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("search_placeholder"))
        self.search_input.setFixedSize(360, 36)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ThemeManager.sidebar_bg()};
                color: {ThemeManager.text_primary()};
                border: none;
                border-radius: 10px;
                padding: 0 14px;
                font-size: 13px;
            }}
        """)
        tb_lay.addWidget(self.search_input)

        tb_lay.addStretch()

        # Ayarlar İkon Butonu (sağ üst köşe)
        self.btn_header_settings = QPushButton()
        kde_settings_ico = get_kde_icon("applications-other-symbolic")
        if not kde_settings_ico.isNull():
            self.btn_header_settings.setIcon(kde_settings_ico)
            self.btn_header_settings.setIconSize(QSize(22, 22))
        else:
            self.btn_header_settings.setText("⚙")
        self.btn_header_settings.setFixedSize(36, 36)
        self.btn_header_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_header_settings.setToolTip(tr("nav_settings"))
        self.btn_header_settings.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
                color: {ThemeManager.text_primary()};
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.border()};
            }}
            QPushButton:pressed {{
                background-color: {ThemeManager.accent_teal()}22;
            }}
        """)
        self.btn_header_settings.clicked.connect(lambda: self._nav_category("settings"))
        tb_lay.addWidget(self.btn_header_settings)

        r_lay.addWidget(self.topbar)

        # Stacked Views (Animasyonlu Geçişler)
        self.stack = AnimatedStackedWidget()

        # Yükleme ekranı — ilk gösterilecek widget
        self.v_loading = LoadingOverlay()
        self.stack.addWidget(self.v_loading)
        self.stack.setCurrentWidget(self.v_loading)

        self.v_category = CategoryView()
        self.v_category.package_clicked.connect(self._show_detail)
        self.v_category.install_clicked.connect(self._install)
        self.v_category.remove_clicked.connect(self._remove)
        self.v_category.card_created.connect(self._bind_install_widget)
        self.stack.addWidget(self.v_category)

        self.v_detail = AppDetailView()
        self.v_detail.backend = self.backend
        self.v_detail.install_clicked.connect(self._install)
        self.v_detail.remove_clicked.connect(self._remove)
        self.stack.addWidget(self.v_detail)

        self.v_installed = InstalledView()
        self.v_installed.package_clicked.connect(self._show_detail)
        self.v_installed.install_clicked.connect(self._install)
        self.v_installed.remove_clicked.connect(self._remove)
        self.v_installed.check_updates_clicked.connect(self._check_for_updates)
        self.v_installed.update_repo_clicked.connect(self._update_repository)
        self.v_installed.bind_workers_requested.connect(self._bind_workers_to_installing_view)
        self.v_installed.card_created.connect(self._bind_install_widget)
        self.stack.addWidget(self.v_installed)

        self.v_search = SearchResultsView()
        self.v_search.package_clicked.connect(self._show_detail)
        self.v_search.install_clicked.connect(self._install)
        self.v_search.card_created.connect(self._bind_install_widget)
        self.stack.addWidget(self.v_search)

        self.v_settings = SettingsView()
        self.v_settings.settings_changed.connect(self._on_settings_changed)
        self.stack.addWidget(self.v_settings)

        self.v_about = AboutView()
        self.stack.addWidget(self.v_about)

        r_lay.addWidget(self.stack)
        hl.addWidget(right_w)

    def _setup_system_tray(self):
        """Sistem tepsisi simgesi ve arka planda çalışma işlevlerini kurar."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_menu = QMenu(self)
        self.tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {ThemeManager.sidebar_bg()};
                color: {ThemeManager.text_primary()};
                border: 1px solid {ThemeManager.border()};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {ThemeManager.accent_teal()};
                color: white;
            }}
        """)

        self.action_open = self.tray_menu.addAction(tr("tray_open_app"))
        self.action_open.triggered.connect(self._show_window)

        self.action_check = self.tray_menu.addAction(tr("tray_check_updates"))
        self.action_check.triggered.connect(lambda: self._check_for_updates(switch_view=True))

        self.tray_menu.addSeparator()

        self.action_quit = self.tray_menu.addAction(tr("tray_exit"))
        self.action_quit.triggered.connect(self._force_quit)

        ico = self._create_tray_icon(has_updates=False)
        self.tray_icon = QSystemTrayIcon(ico, self)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        self._update_tray_visibility()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._show_window()

    def _show_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _force_quit(self):
        self._is_quitting = True
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        if not getattr(self, '_is_quitting', False) and self.settings.get("close_to_tray", True):
            event.ignore()
            self.hide()
        else:
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            event.accept()

    def _send_kde_notification(self, pkg_name: str, pkg_info=None, ok: bool = True):
        """KDE Plasma freedesktop bildirimi gönderir. Başarılı kurulumda 'Çalıştır' butonu içerir."""
        import subprocess
        import threading

        # Paket simgesini bul: öncelik icon_path, sonra icon_name, sonra icon
        icon_path = APP_ICON_PATH
        if pkg_info:
            if getattr(pkg_info, 'icon_path', None) and os.path.exists(pkg_info.icon_path):
                icon_path = pkg_info.icon_path
            elif getattr(pkg_info, 'icon_name', None):
                icon_path = pkg_info.icon_name
            elif getattr(pkg_info, 'icon', None):
                candidate = pkg_info.icon
                if os.path.isabs(candidate) and os.path.exists(candidate):
                    icon_path = candidate

        # Temiz uygulama adını belirle (kaynak ön takısı veya ham paket kimliği yerine)
        app_title_name = ""
        if pkg_info and getattr(pkg_info, 'display_name', None):
            app_title_name = pkg_info.display_name
        if not app_title_name:
            raw_clean = pkg_name.removeprefix("flatpak:")
            if "." in raw_clean:
                parts = [p for p in raw_clean.split(".") if p]
                if parts:
                    app_title_name = parts[-1]
            if not app_title_name:
                app_title_name = raw_clean

        title = tr("notif_installing_done_title") if ok else tr("notif_installing_error_title")
        body  = tr("notif_installing_done_body", pkg=app_title_name) if ok \
                else tr("notif_installing_error_body", pkg=app_title_name)

        def _worker():
            try:
                cmd = [
                    "notify-send",
                    "--app-name=PiSiM",
                    "--urgency=normal",
                    f"--icon={icon_path}",
                ]
                if ok:
                    # libnotify 0.7.9+ → --action: bildirime buton ekler
                    cmd += ["--action", f"run={tr('notif_action_run')}"]
                cmd += [title, body]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,   # kullanıcının tıklaması için bekle
                )
                # notify-send, tıklanan action id'yi stdout'a yazar
                if ok and result.stdout.strip() == "run":
                    self._launch_package(pkg_name, pkg_info)
            except Exception:
                # notify-send yoksa sessizce atla
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _launch_package(self, pkg_name: str, pkg_info=None):
        """Paketi çalıştırmayı dener."""
        import subprocess
        real_name = pkg_name.removeprefix("flatpak:") if pkg_name.startswith("flatpak:") else pkg_name

        # 1. Flatpak ise flatpak run ile başlat
        if pkg_name.startswith("flatpak:"):
            try:
                subprocess.Popen(["flatpak", "run", real_name])
                return
            except Exception:
                pass

        # 2. /usr/share/applications içinden desktop dosyası bul
        import glob
        desktop_candidates = glob.glob(f"/usr/share/applications/*{real_name.lower()}*.desktop")
        if desktop_candidates:
            try:
                subprocess.Popen(["xdg-open", desktop_candidates[0]])
                return
            except Exception:
                pass

        # 3. PATH'ta aynı isimle çalıştır
        try:
            subprocess.Popen([real_name])
        except Exception:
            pass

    def _create_tray_icon(self, has_updates: bool = False) -> QIcon:
        """Sistem tepsisi simgesini oluşturur. Güncelleme varsa sol alt köşesine güncelleme simgesi çizer."""
        if os.path.exists(APP_ICON_PATH):
            base_pixmap = QPixmap(APP_ICON_PATH)
        else:
            base_icon = QIcon.fromTheme("system-software-install")
            base_pixmap = base_icon.pixmap(48, 48)

        if not has_updates:
            return QIcon(base_pixmap)

        size = base_pixmap.size()
        if size.isEmpty() or size.width() < 16:
            size = QSize(48, 48)

        result_pixmap = QPixmap(size)
        result_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, base_pixmap)

        # Sol alt köşe rozeti (Bottom-left badge)
        w, h = size.width(), size.height()
        badge_size = max(16, int(w * 0.45))

        bx = 0
        by = h - badge_size

        # Koyu çerçeveli dairesel rozet
        painter.setPen(QPen(QColor("#18181a"), 2))
        painter.setBrush(QColor("#2ba0b5"))
        painter.drawEllipse(bx, by, badge_size, badge_size)

        # Beyaz ok simgesi (Yukarı yönlü ok)
        painter.setPen(QPen(QColor("#ffffff"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        cx = bx + badge_size / 2.0
        cy = by + badge_size / 2.0
        arrow_h = badge_size * 0.45

        # Dikey gövde
        painter.drawLine(int(cx), int(cy + arrow_h * 0.4), int(cx), int(cy - arrow_h * 0.4))
        # Ok başı
        painter.drawLine(int(cx - arrow_h * 0.35), int(cy - arrow_h * 0.1), int(cx), int(cy - arrow_h * 0.4))
        painter.drawLine(int(cx + arrow_h * 0.35), int(cy - arrow_h * 0.1), int(cx), int(cy - arrow_h * 0.4))

        painter.end()
        return QIcon(result_pixmap)

    def _update_tray_visibility(self):
        if not hasattr(self, 'tray_icon') or not self.tray_icon:
            return
        upd_count = len([p for p in self._all_packages if p.has_update])
        has_updates = (upd_count > 0)

        self.tray_icon.setIcon(self._create_tray_icon(has_updates))
        if has_updates:
            self.tray_icon.setToolTip(tr("updates_available_tooltip", count=upd_count))
        else:
            self.tray_icon.setToolTip("PiSiM")
        self.tray_icon.show()

    def _setup_auto_update_timer(self):
        if not hasattr(self, 'auto_update_timer'):
            self.auto_update_timer = QTimer(self)
            self.auto_update_timer.timeout.connect(lambda: self._check_for_updates(switch_view=False))

        hours = self.settings.get("check_interval_hours", 4)
        if hours > 0:
            ms = hours * 3600 * 1000
            self.auto_update_timer.setInterval(ms)
            self.auto_update_timer.start()
        else:
            self.auto_update_timer.stop()

    def _on_settings_changed(self, new_settings: dict):
        self.settings = new_settings
        self._setup_auto_update_timer()
        self._update_tray_visibility()
        if self.settings.get("auto_install_updates", False):
            self._auto_install_all_updates()
        self._retranslate_ui()

    def _retranslate_ui(self):
        if "all" in self.sidebar_buttons:
            self.sidebar_buttons["all"].txt_lbl.setText(tr("nav_discover"))
        if "installed" in self.sidebar_buttons:
            self._update_sidebar_update_badge()
        if hasattr(self, 'btn_header_settings'):
            self.btn_header_settings.setToolTip(tr("nav_settings"))

        if hasattr(self, 'action_open'):
            self.action_open.setText(tr("tray_open_app"))
        if hasattr(self, 'action_check'):
            self.action_check.setText(tr("tray_check_updates"))
        if hasattr(self, 'action_quit'):
            self.action_quit.setText(tr("tray_exit"))

        if hasattr(self, 'search_input'):
            self.search_input.setPlaceholderText(tr("search_placeholder"))

        if hasattr(self, 'v_settings'):
            self.v_settings.retranslate_ui()
        if hasattr(self, 'v_about'):
            self.v_about.retranslate_ui()

    def _start_load(self):
        # Her zaman arka planda yükle — UI donmasın
        self.stack.setCurrentWidget(self.v_loading)
        self.loader_thread = LoaderThread(self.backend)
        self.loader_thread.progress.connect(
            lambda v, m: self.v_loading.update_progress(v, m)
        )
        self.loader_thread.finished_load.connect(self._on_loaded)
        self.loader_thread.load_error.connect(self._on_load_error)
        self.loader_thread.start()

    def _on_load_error(self, message: str):
        self.v_loading.stop()
        self.v_loading.update_progress(0, f"Hata: {message}")

    def _rebuild_sidebar(self):
        """Repo'dan yüklenen kategorilere göre sidebar'ı dinamik olarak yeniden oluşturur."""
        # Mevcut butonları kaldır (all hariç)
        for cat_id in list(self.sidebar_buttons.keys()):
            if cat_id not in ("all", "installed"):
                btn = self.sidebar_buttons.pop(cat_id)
                self.nav_grp.removeButton(btn)
                btn.setParent(None)
                btn.deleteLater()

        # Stretch öğesini de kaldır (son öğe)
        while self.sb_lay.count() > 0:
            item = self.sb_lay.itemAt(self.sb_lay.count() - 1)
            if item and item.spacerItem():
                self.sb_lay.removeItem(item)
                break

        # all butonu zaten var, yeni kategorileri ekle
        categories_from_repo = self.backend.get_categories_info()
        for cat_id, icon_name, label in categories_from_repo:
            if cat_id in ("all", "installed"):
                continue  # bunlar zaten ekli
            btn = PisiSidebarButton(icon_name=icon_name, label=label, cat_id=cat_id)
            cat_id_copy = cat_id
            btn.clicked.connect(lambda _, c=cat_id_copy: self._nav_category(c))
            self.nav_grp.addButton(btn)
            self.sidebar_buttons[cat_id] = btn
            self.sb_lay.addWidget(btn)

        self.sb_lay.addStretch()
        self.apply_theme()

    def _on_loaded(self):
        self.v_loading.stop()
        self._all_packages = list(self.backend.get_all_packages().values())
        self._rebuild_sidebar()
        if "all" in self.sidebar_buttons:
            self.sidebar_buttons["all"].setChecked(True)
        self._update_sidebar_update_badge()
        self._nav_category("all")
        # Başlangıçta güncellemeleri otomatik denetle
        QTimer.singleShot(500, lambda: self._check_for_updates(switch_view=False))

    def _update_sidebar_update_badge(self):
        upd_count = len([p for p in self._all_packages if p.has_update])
        active_download_count = 0
        if hasattr(self, '_workers'):
            active_download_count = len([w for w in self._workers if getattr(w, 'action', '') == "install"])
        total_count = upd_count + active_download_count

        if "installed" in self.sidebar_buttons:
            if total_count > 0:
                self.sidebar_buttons["installed"].txt_lbl.setText(tr("updates_badge", count=total_count))
            else:
                self.sidebar_buttons["installed"].txt_lbl.setText(tr("nav_updates"))

        self._update_tray_visibility()

    def _nav_category(self, cat_id: str):
        if cat_id in self.sidebar_buttons:
            self.sidebar_buttons[cat_id].setChecked(True)

        if cat_id == "installed":
            installed = [p for p in self._all_packages if p.installed]
            # Aktif indirilen worker paketlerini de ekle (installed=True MUTATE ETMEDEN)
            active_pkgs = []
            if hasattr(self, '_workers'):
                for w in self._workers:
                    if getattr(w, 'action', '') == "install":
                        p_info = self.backend.get_package_info(w.package_name)
                        if not p_info:
                            p_info = next((p for p in self._all_packages if p.name == w.package_name), None)
                        if p_info and p_info not in active_pkgs:
                            active_pkgs.append(p_info)
            self._update_sidebar_update_badge()
            self.v_installed.display_installed(installed, active_installing_pkgs=active_pkgs)
            self._switch_view("installed")
        elif cat_id == "settings":
            self._switch_view("settings")
        elif cat_id == "about":
            self._switch_view("about")
        elif not self._all_packages:
            pass  # henüz yüklenmedi
        else:
            # Kategori adını ve ikonunu repodaki veya LUPUS_CATEGORIES'den al
            cat_info = LUPUS_CATEGORIES.get(cat_id, {"name": cat_id.capitalize(), "icon": "applications-other"})
            # Eğer sidebar buton etiketinden daha iyi bilgi alınabilirse kullan
            if cat_id in self.sidebar_buttons:
                label = self.sidebar_buttons[cat_id].txt_lbl.text()
                # Parantez içindeki sayıyı çıkar: "Geliştirme (33)" -> "Geliştirme"
                clean = re.sub(r'\s*\(\d+\)\s*$', '', label).strip()
                cat_info["name"] = clean

            if cat_id == "all":
                pkgs = [p for p in self._all_packages if not p.is_flatpak]
            elif cat_id == "flatpak":
                pkgs = [p for p in self._all_packages if p.is_flatpak]
            else:
                pkgs = [p for p in self._all_packages if p.category == cat_id and not p.is_flatpak]

            # Paketleri alfabetik sıraya koy (display_name veya name)
            pkgs = sorted(pkgs, key=lambda p: (p.display_name or p.name).lower())

            self.v_category.display_category(cat_id, cat_info["name"], cat_info["icon"], pkgs)
            self._switch_view("category")

    def _switch_view(self, view_name: str):
        self._history_stack.append(view_name)
        if view_name == "category": self.stack.setCurrentWidget(self.v_category)
        elif view_name == "detail": self.stack.setCurrentWidget(self.v_detail)
        elif view_name == "installed": self.stack.setCurrentWidget(self.v_installed)
        elif view_name == "search": self.stack.setCurrentWidget(self.v_search)
        elif view_name == "settings": self.stack.setCurrentWidget(self.v_settings)
        elif view_name == "about": self.stack.setCurrentWidget(self.v_about)

    def _show_detail(self, package_name: str):
        pkg = self.backend.get_package_info(package_name)
        if pkg:
            self.v_detail.display_package(pkg)
            if hasattr(self.v_detail, '_detail_install_widget') and self.v_detail._detail_install_widget:
                self._bind_install_widget(self.v_detail._detail_install_widget)
            self._switch_view("detail")

    def _on_search(self, query: str):
        if not query.strip():
            self._nav_category("all")
            return
        results = self.backend.search_packages(query, self.backend.get_all_packages())
        self.v_search.display_results(query, results)
        self._switch_view("search")

    def _cancel_install(self, package_name: str):
        """Verilen paketi indiren worker'ı iptal et."""
        if not hasattr(self, '_workers'):
            return
        for w in list(self._workers):
            if w.package_name == package_name:
                w.cancel()
                break

    def _bind_install_widget(self, iw: "PisiInstallWidget"):
        """Verilen PisiInstallWidget bileşenini eğer paketi şu an yükleniyorsa aktif worker'a bağlar."""
        if not iw or not hasattr(iw, 'package') or not iw.package:
            return
        pkg_name = iw.package.name
        worker = next((w for w in getattr(self, '_workers', []) if w.package_name == pkg_name), None)
        if worker:
            last_pct = getattr(worker, '_last_progress', 0)
            iw.start_progress()
            iw.set_progress(last_pct)
            try:
                worker.progress.disconnect(iw.set_progress)
            except Exception:
                pass
            worker.progress.connect(iw.set_progress)
            try:
                iw.cancel_clicked.disconnect(self._cancel_install)
            except Exception:
                pass
            iw.cancel_clicked.connect(self._cancel_install)
        else:
            if getattr(iw, '_prog_row', None) and iw._prog_row.isVisible():
                iw._restore_buttons()

    def _bind_workers_to_installing_view(self):
        """İndirilenler bölümündeki kartların install_widget'larını aktif worker'lara bağlar."""
        if not hasattr(self, '_workers'):
            return
        grid = self.v_installed.upd_grid
        for i in range(grid.count()):
            item = grid.itemAt(i)
            if not item:
                continue
            card = item.widget()
            if card is None:
                continue
            iw = getattr(card, 'install_widget', None)
            if iw:
                self._bind_install_widget(iw)

    def _install(self, package_name: str, install_widget: "PisiInstallWidget" = None):
        """Başlat kurma işlemini arka plan thread'inde."""
        worker = InstallWorker(self.backend, package_name, action="install")

        if install_widget:
            install_widget.start_progress()
            try:
                worker.progress.disconnect(install_widget.set_progress)
            except Exception:
                pass
            worker.progress.connect(install_widget.set_progress)
            try:
                install_widget.cancel_clicked.disconnect(self._cancel_install)
            except Exception:
                pass
            install_widget.cancel_clicked.connect(self._cancel_install)

        worker.progress.connect(lambda v, w=worker: setattr(w, '_last_progress', v))
        pkg_obj = self.backend.get_package_info(package_name)
        was_installed = pkg_obj.installed if pkg_obj else False

        def _on_done(ok: bool, msg: str):
            if hasattr(self, '_workers') and worker in self._workers:
                self._workers.remove(worker)

            is_cancelled = getattr(worker, '_cancelled', False) or msg == "İptal edildi"

            if install_widget:
                try:
                    if ok:
                        install_widget.package.installed = True
                        install_widget.package.has_update = False
                        install_widget.finish_progress()
                    elif is_cancelled:
                        if pkg_obj and not was_installed:
                            pkg_obj.installed = False
                        install_widget._restore_buttons()
                    else:
                        if pkg_obj and not was_installed:
                            pkg_obj.installed = False
                        install_widget.show_error()
                except RuntimeError:
                    pass

            if hasattr(self.v_detail, '_detail_install_widget') and \
               self.v_detail._detail_install_widget is not None and \
               hasattr(self.v_detail, 'package') and \
               getattr(self.v_detail.package, 'name', None) == package_name:
                try:
                    diw = self.v_detail._detail_install_widget
                    if ok:
                        diw.package.installed = True
                        diw.package.has_update = False
                        diw.finish_progress()
                    elif is_cancelled:
                        if pkg_obj and not was_installed:
                            pkg_obj.installed = False
                        diw._restore_buttons()
                    else:
                        if pkg_obj and not was_installed:
                            pkg_obj.installed = False
                        diw.show_error()
                except RuntimeError:
                    pass

            if ok and pkg_obj:
                pkg_obj.installed = True
                pkg_obj.has_update = False
            elif not ok and pkg_obj:
                if not was_installed:
                    pkg_obj.installed = False

            # KDE Plasma bildirimi: yalnızca pencere gizliyse gönder
            if not self.isVisible() and not is_cancelled:
                self._send_kde_notification(package_name, pkg_obj, ok=ok)

            self._update_all_views()

        if not hasattr(self, '_workers'):
            self._workers = []
        self._workers.append(worker)
        worker.finished.connect(_on_done)
        worker.start()
        self._update_all_views()

    def _remove(self, package_name: str, install_widget: "PisiInstallWidget" = None):
        """Başlat kaldırma işlemini arka plan thread'inde."""
        worker = InstallWorker(self.backend, package_name, action="remove")

        if install_widget:
            install_widget.start_progress()
            try:
                worker.progress.disconnect(install_widget.set_progress)
            except Exception:
                pass
            worker.progress.connect(install_widget.set_progress)
            try:
                install_widget.cancel_clicked.disconnect(self._cancel_install)
            except Exception:
                pass
            install_widget.cancel_clicked.connect(self._cancel_install)

        worker.progress.connect(lambda v, w=worker: setattr(w, '_last_progress', v))

        pkg_obj = self.backend.get_package_info(package_name)

        def _on_done(ok: bool, msg: str):
            if hasattr(self, '_workers') and worker in self._workers:
                self._workers.remove(worker)

            if install_widget:
                try:
                    if ok:
                        install_widget.package.installed = False
                        install_widget.package.has_update = False
                        install_widget.finish_progress()
                    else:
                        install_widget.show_error()
                except RuntimeError:
                    pass
            if ok and pkg_obj:
                pkg_obj.installed = False
                pkg_obj.has_update = False

            self._update_all_views()

        if not hasattr(self, '_workers'):
            self._workers = []
        self._workers.append(worker)
        worker.finished.connect(_on_done)
        worker.start()
        self._update_all_views()

    def _update_all_views(self):
        self._all_packages = list(self.backend.get_all_packages().values())

        # Çalışmakta olan kurulum worker'larının paketlerini topla
        active_pkgs = []
        if hasattr(self, '_workers'):
            for w in self._workers:
                if getattr(w, 'action', '') == "install":
                    p_info = self.backend.get_package_info(w.package_name)
                    if not p_info:
                        p_info = next((p for p in self._all_packages if p.name == w.package_name), None)
                    if p_info and p_info not in active_pkgs:
                        active_pkgs.append(p_info)

        installed = [p for p in self._all_packages if p.installed]

        self.v_installed.display_installed(installed, active_installing_pkgs=active_pkgs)
        self._update_sidebar_update_badge()

    def _check_for_updates(self, switch_view: bool = False):
        """PiSi depolarını güncellemeden paket güncellemelerini denetler."""
        if hasattr(self, '_checking_updates') and self._checking_updates:
            return
        self._checking_updates = True

        if hasattr(self.v_installed, 'btn_check_updates'):
            self.v_installed.btn_check_updates.setEnabled(False)
            self.v_installed.btn_check_updates.setText(tr("checking_updates"))

        self.update_check_thread = UpdateCheckThread(self.backend, update_repo=False)

        def _on_done(count: int, pkgs: list, err: str):
            self._checking_updates = False
            if hasattr(self.v_installed, 'btn_check_updates'):
                self.v_installed.btn_check_updates.setEnabled(True)
                self.v_installed.btn_check_updates.setText(tr("btn_check_updates"))

            self._all_packages = list(self.backend.get_all_packages().values())
            self._update_all_views()
            if switch_view:
                self._switch_view("installed")
                if "installed" in self.sidebar_buttons:
                    self.sidebar_buttons["installed"].setChecked(True)

            # Otomatik güncelleme aktifse güncellemeleri indirip kur
            if count > 0:
                if self.settings.get("auto_install_updates", False):
                    self._auto_install_all_updates()
                elif not self.isVisible():
                    if hasattr(self, 'tray_icon') and self.tray_icon and QSystemTrayIcon.supportsMessages():
                        self.tray_icon.show()
                        self.tray_icon.showMessage(
                            tr("notif_update_available_title"),
                            tr("notif_update_available_body", count=count),
                            QSystemTrayIcon.MessageIcon.Information,
                            8000,
                        )

        self.update_check_thread.finished_check.connect(_on_done)
        self.update_check_thread.start()

    def _auto_install_all_updates(self):
        """Otomatik güncelleme aktif ise mevcut tüm güncellemeleri arka planda kurar."""
        if not self.settings.get("auto_install_updates", False):
            return
        upd_packages = [p for p in self._all_packages if p.has_update]
        for pkg in upd_packages:
            active_workers = getattr(self, '_workers', [])
            if not any(getattr(w, 'package_name', '') == pkg.name for w in active_workers):
                self._install(pkg.name)

    def _update_repository(self):
        """PiSi depolarını günceller."""
        if hasattr(self, '_updating_repo') and self._updating_repo:
            return
        self._updating_repo = True

        if hasattr(self.v_installed, 'btn_update_repo'):
            self.v_installed.btn_update_repo.setEnabled(False)
            self.v_installed.btn_update_repo.setText(tr("updating_repo"))

        self.update_repo_thread = UpdateRepoThread(self.backend)

        def _on_done(success: bool, message: str):
            self._updating_repo = False
            if hasattr(self.v_installed, 'btn_update_repo'):
                self.v_installed.btn_update_repo.setEnabled(True)
                self.v_installed.btn_update_repo.setText(tr("btn_update_repo"))

            if success:
                QMessageBox.information(
                    self,
                    tr("repo_update_dialog"),
                    tr("repo_update_success")
                )
                self._check_for_updates()
            else:
                QMessageBox.critical(
                    self,
                    tr("repo_update_error_title"),
                    tr("repo_update_error_msg", message=message)
                )

        self.update_repo_thread.finished_update.connect(_on_done)
        self.update_repo_thread.start()

    def _go_back(self):
        if len(self._history_stack) > 1:
            self._history_stack.pop()
            prev = self._history_stack[-1]
            self._switch_view(prev)
