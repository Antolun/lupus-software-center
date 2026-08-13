/* PiSiM – Tauri Frontend Logic (Vanilla JS)
   PyQt6 mainwindow.py & widgets.py mantığı ile %100 birebir entegre */

// ── IPC Helpers ──
const invoke = async (cmd, args = {}) => {
  try {
    if (window.__TAURI_INTERNALS__ && typeof window.__TAURI_INTERNALS__.invoke === 'function') {
      return await window.__TAURI_INTERNALS__.invoke(cmd, args);
    }
    if (window.__TAURI__ && window.__TAURI__.core && typeof window.__TAURI__.core.invoke === 'function') {
      return await window.__TAURI__.core.invoke(cmd, args);
    }
    if (window.__TAURI__ && typeof window.__TAURI__.invoke === 'function') {
      return await window.__TAURI__.invoke(cmd, args);
    }
  } catch (err) {
    console.error(`IPC error on ${cmd}:`, err);
    throw err;
  }
  console.warn('Tauri IPC not found for:', cmd, args);
  return [];
};

// ── State ──
let allPackages = [];
let categories = [];
let currentCategory = 'all';
let historyStack = [];
let currentLanguage = 'tr';
let activeWorkers = new Map(); // pkgName -> { action, progress }
let searchDebounceTimer = null;

// ── i18n Dictionary ──
const i18n = {
  en: {
    nav_discover: "All Applications",
    nav_development: "Development",
    nav_education: "Education",
    nav_enterprise: "Enterprise",
    nav_games: "Games",
    nav_graphics: "Graphics",
    nav_internet: "Internet",
    nav_multimedia: "Multimedia",
    nav_office: "Office",
    nav_system: "System",
    nav_utilities: "Utilities",
    nav_flatpak: "Flatpak",
    nav_updates: "Updates",
    nav_settings: "Settings",
    nav_about: "About",
    all_applications: "All Applications",
    packages: "Packages",
    search_placeholder: "Search applications...",
    search_results_title: "Search Results...",
    results_for: 'Results for "{query}"',
    unknown_developer: "Unknown Developer",
    trending_apps: "Trending Applications",
    editors_choice: "Editor's Choice",
    see_all: "See All",
    about: "About",
    btn_install: "Install",
    btn_update: "Update",
    btn_open: "Open",
    btn_remove: "Remove",
    installed_label: "✓ Installed",
    btn_cancel: "✕ Cancel",
    error_occurred: "Error Occurred",
    btn_update_repo: "Update Repository",
    btn_check_updates: "Check for Updates",
    updating_repo: "Updating...",
    checking_updates: "Checking...",
    hero_subtitle: "LUPUS iDEVICE MOUNTER",
    hero_title: "Discover easy access to\nApple devices!",
    rating: "Rating",
    downloads: "Downloads",
    size: "Size",
    dependencies: "Dependencies",
    version: "Version",
    download_size: "Download Size",
    required_space: "Required Disk Space",
    type: "Type",
    category: "Category",
    license: "License",
    repo_origin: "Repository / Origin",
    developer: "Developer",
    flatpak_pkg: "Flatpak Package",
    pisi_pkg: "PiSi Package",
    lupus_main_repo: "Main Repository",
    lupus_community: "TeknoAnka",
    flathub_community: "FlatHub",
    packager_name: "Packager",
    packager_email: "Packager Email",
    update_date: "Last Update Date",
    homepage: "Website",
    vcs_url: "Source Code",
    no_description: "PiSi package description not available.",
    no_packages_in_category: "No packages found in this category.",
    no_updates_installed: "All your applications are up to date.",
    loading_flathub: "Description loading from FlatHub...",
    downloads_and_updates: "Downloads & Updates ({count})",
    updates_badge: "Updates ({count})",
    updates_title: "Updates",
    update_check_dialog: "Update Check",
    updates_found_msg: "Found updates for {count} applications!",
    system_up_to_date_msg: "Your system is up to date! No updates found.",
    repo_update_dialog: "Repository Update",
    repo_update_success: "PiSi repositories updated successfully!",
    repo_update_error_title: "Repository Update Error",
    repo_update_error_msg: "Error updating repository:\n{message}",
    zoom_in: "Zoom In",
    zoom_out: "Zoom Out",
    reset: "Reset",
    close: "Close",
    loading_app_title: "PiSiM",
    loading_init: "Starting…",
    loading_prep: "Preparing application…",
    loading_check_installed: "Checking installed packages…",
    loading_repo_pkgs: "Loading repository packages…",
    loading_flatpak: "Loading Flatpak applications…",
    loading_cache: "Loaded from cache",
    installed_success: "{name} installed successfully",
    removed_success: "{name} uninstalled successfully",
    cancelled: "Cancelled",
    settings_title: "Settings",
    settings_section_general: "General & Startup",
    settings_autostart: "Run on System Boot",
    settings_autostart_desc: "Automatically start PiSiM in background when system boots",
    settings_close_to_tray: "Run in Background When Closed",
    settings_close_to_tray_desc: "Hide application window to system tray when pressing close button",
    settings_section_updates: "Update Checker Settings",
    settings_auto_check_interval: "Automatic Update Checking Frequency",
    settings_auto_install_updates: "Automatically Install Updates",
    settings_auto_install_updates_desc: "Automatically download and install application updates when available",
    settings_section_language: "Language Options",
    settings_language_label: "Application Language",
    interval_disabled: "Disabled",
    interval_1h: "Every 1 Hour",
    interval_4h: "Every 4 Hours",
    interval_12h: "Every 12 Hours",
    interval_24h: "Daily (Every 24 Hours)",
    tray_open_app: "Open PiSiM",
    tray_check_updates: "Check for Updates",
    tray_exit: "Exit",
    about_title: "About PiSiM",
    about_app_name: "PiSiM - PiSi Market",
    about_version: "Version 2.0.0",
    about_description: "Modern package manager and application store for LupuS.",
    about_developer: "Developed by TeknoAnka",
    about_website: "Visit Website",
    about_license: "License: GNU General Public License v3.0",
  },
  tr: {
    nav_discover: "Tüm Uygulamalar",
    nav_development: "Geliştirme",
    nav_education: "Eğitim",
    nav_enterprise: "Kurumsal",
    nav_games: "Oyunlar",
    nav_graphics: "Grafik",
    nav_internet: "İnternet",
    nav_multimedia: "Multimedya",
    nav_office: "Ofis",
    nav_system: "Sistem",
    nav_utilities: "Araçlar",
    nav_flatpak: "Flatpak",
    nav_updates: "Güncellemeler",
    nav_settings: "Ayarlar",
    nav_about: "Hakkında",
    all_applications: "Tüm Uygulamalar",
    packages: "Paketler",
    search_placeholder: "Uygulama ara...",
    search_results_title: "Arama Sonuçları...",
    results_for: '"{query}" için sonuçlar',
    unknown_developer: "Bilinmeyen Geliştirici",
    trending_apps: "Trend Uygulamalar",
    editors_choice: "Editörün Seçimleri",
    see_all: "Tümünü Gör",
    about: "Hakkında",
    btn_install: "Kur",
    btn_update: "Güncelle",
    btn_open: "Aç",
    btn_remove: "Sil",
    installed_label: "✓ Kuruldu",
    btn_cancel: "✕ İptal",
    error_occurred: "Hata Oluştu",
    btn_update_repo: "Depoyu Güncelle",
    btn_check_updates: "Güncellemeleri Denetle",
    updating_repo: "Güncelleniyor...",
    checking_updates: "Denetleniyor...",
    hero_subtitle: "LUPUS iDEVICE MOUNTER",
    hero_title: "Apple cihazlarına kolay\nerişimi keşfedin!",
    rating: "Puanlama",
    downloads: "İndirme",
    size: "Boyut",
    dependencies: "Bağımlılık",
    version: "Versiyon",
    download_size: "İndirme Boyutu",
    required_space: "Gerekli Disk Alanı",
    type: "Tür",
    category: "Kategori",
    license: "Lisans",
    repo_origin: "Depo / Kaynak",
    developer: "Geliştirici",
    flatpak_pkg: "Flatpak Paketi",
    pisi_pkg: "PiSi Paketi",
    lupus_main_repo: "Ana Depo",
    lupus_community: "TeknoAnka",
    flathub_community: "FlatHub",
    packager_name: "Paketleyici",
    packager_email: "Paketleyici E-Posta",
    update_date: "Son Güncelleme",
    homepage: "Web Sitesi",
    vcs_url: "Kaynak Kod Deposu",
    no_description: "PiSi paket açıklaması mevcut değil.",
    no_packages_in_category: "Bu kategoride henüz paket bulunmuyor.",
    no_updates_installed: "Tüm uygulamalarınız güncel.",
    loading_flathub: "Açıklama FlatHub'dan yükleniyor...",
    downloads_and_updates: "İndirilenler & Güncellemeler ({count})",
    updates_badge: "Güncellemeler ({count})",
    updates_title: "Güncellemeler",
    update_check_dialog: "Güncelleme Kontrolü",
    updates_found_msg: "{count} adet uygulama için güncelleme bulundu!",
    system_up_to_date_msg: "Sisteminiz güncel! Herhangi bir güncelleme bulunamadı.",
    repo_update_dialog: "Depo Güncelleme",
    repo_update_success: "PiSi depoları başarıyla güncellendi!",
    repo_update_error_title: "Depo Güncelleme Hatası",
    repo_update_error_msg: "Depo güncellenirken bir hata oluştu:\n{message}",
    zoom_in: "Büyüt",
    zoom_out: "Küçült",
    reset: "Sıfırla",
    close: "Kapat",
    loading_app_title: "PiSiM",
    loading_init: "Başlatılıyor…",
    loading_prep: "Uygulama hazırlanıyor…",
    loading_check_installed: "Kurulu paketler kontrol ediliyor…",
    loading_repo_pkgs: "Depo paket listesi yükleniyor…",
    loading_flatpak: "Flatpak uygulamaları yükleniyor…",
    loading_cache: "Önbellekten yüklendi",
    installed_success: "{name} başarıyla kuruldu",
    removed_success: "{name} başarıyla kaldırıldı",
    cancelled: "İptal edildi",
    settings_title: "Ayarlar",
    settings_section_general: "Genel ve Başlangıç",
    settings_autostart: "Sistem Açılışında Başlat",
    settings_autostart_desc: "Sistem açıldığında PiSiM arka planda otomatik olarak çalışır",
    settings_close_to_tray: "Kapatıldığında Arka Planda Çalış",
    settings_close_to_tray_desc: "Kapat butonuna basıldığında uygulamayı görev çubuğu tepsisine küçültür",
    settings_section_updates: "Güncelleme Denetleyici Ayarları",
    settings_auto_check_interval: "Otomatik Güncelleme Denetleme Sıklığı",
    settings_auto_install_updates: "Güncellemeleri Otomatik Yükle",
    settings_auto_install_updates_desc: "Yeni güncellemeler bulunduğunda arka planda otomatik olarak indirir ve kurar",
    settings_section_language: "Dil Seçenekleri",
    settings_language_label: "Uygulama Dili",
    interval_disabled: "Devre Dışı",
    interval_1h: "Her 1 Saatte Bir",
    interval_4h: "Her 4 Saatte Bir",
    interval_12h: "Her 12 Saatte Bir",
    interval_24h: "Günde Bir (24 Saat)",
    tray_open_app: "PiSiM'i Aç",
    tray_check_updates: "Güncellemeleri Denetle",
    tray_exit: "Çıkış",
    about_title: "PiSiM Hakkında",
    about_app_name: "PiSiM - PiSi Market",
    about_version: "Sürüm 2.0.0",
    about_description: "LupuS için modern paket yöneticisi ve uygulama mağazası.",
    about_developer: "TeknoAnka tarafından geliştirilmiştir",
    about_website: "Web Sitesini Ziyaret Et",
    about_license: "Lisans: GNU Genel Kamu Lisansı v3.0",
  }
};

function tr(key, params = {}) {
  let str = (i18n[currentLanguage] && i18n[currentLanguage][key]) || i18n.en[key] || key;
  for (let k in params) {
    str = str.replace(`{${k}}`, params[k]);
  }
  return str;
}

function updateUiLanguage() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = tr(key);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = tr(key);
  });
}

// ── Plasma Breeze SVG Icons Helper ──
const KDE_ICON_MAP = {
  "all": "plasma-search",
  "development": "applications-development",
  "education": "applications-education",
  "enterprise": "applications-office",
  "games": "applications-games",
  "graphics": "applications-graphics",
  "internet": "applications-internet",
  "multimedia": "applications-multimedia",
  "office": "applications-office",
  "system": "applications-system",
  "utilities": "applications-utilities",
  "flatpak": "package-x-generic",
  "updates": "download",
};

function getCategoryIconPath(catId) {
  const iconName = KDE_ICON_MAP[catId] || "applications-utilities";
  return `assets/icons/${iconName}.svg`;
}

function getAppIconSrc(iconPath, isFlatpak) {
  // Backend artık data: URI döndürüyor, direkt kullan
  if (iconPath && iconPath.length > 0) {
    return iconPath;
  }
  // İkon yoksa paket tipine göre varsayılan
  return isFlatpak ? 'assets/icons/package-x-generic.svg' : 'assets/pisi.png';
}

// ── Navigation & View Switching ──
function switchView(viewId, pushHistory = true) {
  const currentActive = document.querySelector('.view-page.active');
  if (currentActive && currentActive.id === viewId) return;

  if (pushHistory && currentActive) {
    historyStack.push(currentActive.id);
  }

  document.querySelectorAll('.view-page').forEach(page => {
    page.classList.remove('active');
  });

  const target = document.getElementById(viewId);
  if (target) {
    target.classList.add('active');
  }

  // Back button visibility
  const backBtn = document.getElementById('btn-nav-back');
  if (historyStack.length > 0) {
    backBtn.style.visibility = 'visible';
  } else {
    backBtn.style.visibility = 'hidden';
  }
}

function goBack() {
  if (historyStack.length > 0) {
    const prevViewId = historyStack.pop();
    switchView(prevViewId, false);
  }
}

// ── Render Card Component ──
function createCardElement(pkg, rank = null, showDelete = true) {
  const card = document.createElement('div');
  card.className = 'app-card';
  card.setAttribute('data-pkg', pkg.name);

  let rankHtml = rank ? `<div class="card-rank">${rank}</div>` : '';
  let badgeHtml = pkg.is_flatpak ? `<span class="flatpak-badge">${pkg.origin || 'Flatpak'}</span>` : '';
  let iconSrc = getAppIconSrc(pkg.icon_path, pkg.is_flatpak);

  const summaryStr = pkg.summary ? (pkg.summary.length > 55 ? pkg.summary.substring(0, 55) + '…' : pkg.summary) : (pkg.category || 'Uygulama');

  card.innerHTML = `
    ${rankHtml}
    <img class="card-icon" src="${iconSrc}" loading="lazy" decoding="async" onerror="this.src='${pkg.is_flatpak ? 'assets/icons/package-x-generic.svg' : 'assets/pisim.png'}'" alt="${pkg.display_name}">
    <div class="card-info">
      <div class="card-title-row">
        <span class="card-name">${pkg.display_name || pkg.name}</span>
        ${badgeHtml}
      </div>
      <span class="card-summary">${summaryStr}</span>
    </div>
    <div class="install-widget" data-pkg="${pkg.name}"></div>
  `;

  // Click handler to open detail view
  card.addEventListener('click', (e) => {
    if (e.target.closest('.install-widget')) return;
    openAppDetail(pkg);
  });

  const widgetContainer = card.querySelector('.install-widget');
  renderInstallWidget(widgetContainer, pkg, showDelete);

  return card;
}

function renderInstallWidget(container, pkg, showDelete = true) {
  if (!container) return;
  container.innerHTML = '';

  if (activeWorkers.has(pkg.name)) {
    const worker = activeWorkers.get(pkg.name);
    container.innerHTML = `
      <div class="progress-wrap">
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: ${worker.progress}%"></div>
        </div>
        <button class="btn-cancel" onclick="cancelWorker('${pkg.name}')">${tr('btn_cancel')}</button>
      </div>
    `;
    return;
  }

  if (!pkg.installed) {
    const btn = document.createElement('button');
    btn.className = 'btn-action install';
    btn.innerHTML = `<img src="assets/icons/download.svg" alt=""><span>${tr('btn_install')}</span>`;
    btn.onclick = (e) => { e.stopPropagation(); startInstall(pkg.name); };
    container.appendChild(btn);
  } else if (pkg.has_update) {
    const btn = document.createElement('button');
    btn.className = 'btn-action update';
    btn.innerHTML = `<img src="assets/icons/view-refresh.svg" alt=""><span>${tr('btn_update')}</span>`;
    btn.onclick = (e) => { e.stopPropagation(); startInstall(pkg.name); };
    container.appendChild(btn);
  } else {
    if (showDelete) {
      const btn = document.createElement('button');
      btn.className = 'btn-delete';
      btn.title = tr('btn_remove');
      btn.innerHTML = `<img src="assets/icons/edit-delete.svg" alt="Sil">`;
      btn.onclick = (e) => { e.stopPropagation(); startRemove(pkg.name); };
      container.appendChild(btn);
    } else {
      const label = document.createElement('span');
      label.className = 'installed-label';
      label.textContent = tr('installed_label');
      container.appendChild(label);
    }
  }
}

// ── Actions: Install / Remove ──
async function startInstall(pkgName) {
  activeWorkers.set(pkgName, { action: 'install', progress: 10 });
  refreshAllWidgets(pkgName);

  let p = 10;
  const timer = setInterval(() => {
    p = Math.min(p + 15, 90);
    if (activeWorkers.has(pkgName)) {
      activeWorkers.get(pkgName).progress = p;
      refreshAllWidgets(pkgName);
    } else {
      clearInterval(timer);
    }
  }, 300);

  try {
    const res = await invoke('install_package', { packageName: pkgName });
    clearInterval(timer);
    activeWorkers.delete(pkgName);

    if (res && res.success) {
      const pkg = allPackages.find(x => x.name === pkgName);
      if (pkg) {
        pkg.installed = true;
        pkg.has_update = false;
      }
    }
    refreshAllWidgets(pkgName);
  } catch (err) {
    clearInterval(timer);
    activeWorkers.delete(pkgName);
    refreshAllWidgets(pkgName);
  }
}

async function startRemove(pkgName) {
  activeWorkers.set(pkgName, { action: 'remove', progress: 10 });
  refreshAllWidgets(pkgName);

  let p = 10;
  const timer = setInterval(() => {
    p = Math.min(p + 20, 90);
    if (activeWorkers.has(pkgName)) {
      activeWorkers.get(pkgName).progress = p;
      refreshAllWidgets(pkgName);
    } else {
      clearInterval(timer);
    }
  }, 250);

  try {
    const res = await invoke('remove_package', { packageName: pkgName });
    clearInterval(timer);
    activeWorkers.delete(pkgName);

    if (res && res.success) {
      const pkg = allPackages.find(x => x.name === pkgName);
      if (pkg) {
        pkg.installed = false;
        pkg.has_update = false;
      }
    }
    refreshAllWidgets(pkgName);
  } catch (err) {
    clearInterval(timer);
    activeWorkers.delete(pkgName);
    refreshAllWidgets(pkgName);
  }
}

function cancelWorker(pkgName) {
  activeWorkers.delete(pkgName);
  refreshAllWidgets(pkgName);
}

function refreshAllWidgets(pkgName) {
  document.querySelectorAll(`.install-widget[data-pkg="${pkgName}"]`).forEach(container => {
    const pkg = allPackages.find(x => x.name === pkgName);
    if (pkg) {
      renderInstallWidget(container, pkg, true);
    }
  });
  const detailContainer = document.getElementById('detail-install-container');
  const currentDetailName = document.getElementById('detail-name')?.textContent;
  const pkg = allPackages.find(x => x.name === pkgName);
  if (pkg && (pkg.name === currentDetailName || pkg.display_name === currentDetailName)) {
    renderInstallWidget(detailContainer, pkg, true);
  }
}

// ── Detail View ──
async function openAppDetail(pkg) {
  const detailIconEl = document.getElementById('detail-icon');
  detailIconEl.src = getAppIconSrc(pkg.icon_path, pkg.is_flatpak);
  detailIconEl.onerror = () => { detailIconEl.src = pkg.is_flatpak ? 'assets/icons/package-x-generic.svg' : 'assets/pisim.png'; };
  document.getElementById('detail-name').textContent = pkg.display_name || pkg.name;
  document.getElementById('detail-summary').textContent = pkg.summary || '';
  document.getElementById('detail-category').textContent = (pkg.category || '').toUpperCase();
  document.getElementById('detail-description').textContent = pkg.description || pkg.summary || tr('no_description');

  const badge = document.getElementById('detail-flatpak-badge');
  if (pkg.is_flatpak) {
    badge.textContent = pkg.origin || 'Flatpak';
    badge.style.display = 'inline-flex';
  } else {
    badge.style.display = 'none';
  }

  // Stats
  document.getElementById('stat-rating').textContent = `${(pkg.rating || 4.5).toFixed(1)} ★`;
  document.getElementById('stat-downloads').textContent = (pkg.downloads || 0).toLocaleString();
  document.getElementById('stat-size').textContent = pkg.installed_size || pkg.download_size || '-';
  document.getElementById('stat-deps').textContent = pkg.dependencies_count || 0;

  // Render Install Widget in Detail
  const widgetWrap = document.getElementById('detail-install-container');
  renderInstallWidget(widgetWrap, pkg, true);

  // Gallery
  const gallery = document.getElementById('detail-gallery');
  gallery.innerHTML = '';

  // Metadata Grid builder helper
  const updateMetadataGrid = (p) => {
    const metaGrid = document.getElementById('detail-meta-grid');
    metaGrid.innerHTML = '';
    const metas = [
      [tr('version'), p.version || '1.0.0'],
      [tr('license'), p.license || 'GPL'],
      [tr('type'), p.is_flatpak ? tr('flatpak_pkg') : tr('pisi_pkg')],
      [tr('repo_origin'), p.origin || tr('lupus_main_repo')],
      [tr('category'), (p.category || 'Utilities').toUpperCase()],
      [tr('developer'), p.developer || tr('unknown_developer')],
    ];
    if (p.download_size) metas.push([tr('download_size'), p.download_size]);
    if (p.installed_size) metas.push([tr('required_space'), p.installed_size]);

    metas.forEach(([k, v]) => {
      const item = document.createElement('div');
      item.className = 'meta-item';
      item.innerHTML = `<span class="meta-key">${k}</span><span class="meta-val">${v}</span>`;
      metaGrid.appendChild(item);
    });
  };

  updateMetadataGrid(pkg);

  // Fetch enriched details from backend (PiSi CLI info)
  if (!pkg.is_flatpak) {
    try {
      const enriched = await invoke('get_package_details', { packageName: pkg.name });
      if (enriched) {
        if (enriched.summary) document.getElementById('detail-summary').textContent = enriched.summary;
        if (enriched.description) document.getElementById('detail-description').textContent = enriched.description;
        if (enriched.category) document.getElementById('detail-category').textContent = enriched.category.toUpperCase();
        if (enriched.installed_size || enriched.download_size) {
          document.getElementById('stat-size').textContent = enriched.installed_size || enriched.download_size;
        }
        document.getElementById('stat-deps').textContent = enriched.dependencies_count || 0;
        updateMetadataGrid(enriched);
      }
    } catch (e) {}
  } else {
    // FlatHub info fetch
    try {
      const flathubData = await invoke('get_flatpak_info', { appId: pkg.name });
      if (flathubData) {
        if (flathubData.description) {
          document.getElementById('detail-description').textContent = flathubData.description.replace(/<[^>]+>/g, '').trim();
        }
        if (flathubData.screenshots && flathubData.screenshots.length > 0) {
          gallery.innerHTML = '';
          flathubData.screenshots.slice(0, 4).forEach(sc => {
            const scUrl = typeof sc === 'string' ? sc : (sc.imgDesktopUrl || sc.imgMobileUrl || sc.thumbUrl);
            if (scUrl) {
              const img = document.createElement('img');
              img.className = 'gallery-img';
              img.src = scUrl;
              img.loading = 'lazy';
              img.decoding = 'async';
              img.onclick = () => openImageModal(scUrl);
              gallery.appendChild(img);
            }
          });
        }
      }
    } catch (e) {}
  }

  switchView('view-detail');
}

// ── Views Rendering ──
function renderDiscoverView() {
  renderLazyGrid('discover-all-grid', () => allPackages, false);
}

// ── Lazy Loading (Infinite Scroll) ──
const lazyObservers = new Map();

function resetLazyGrid(gridId) {
  const obs = lazyObservers.get(gridId);
  if (obs) {
    obs.disconnect();
    lazyObservers.delete(gridId);
  }
}

function renderLazyGrid(gridId, getItems, showDelete, batchSize = 30) {
  const grid = document.getElementById(gridId);
  resetLazyGrid(gridId);
  grid.innerHTML = '';

  const items = getItems();
  if (items.length === 0) return;

  const view = grid.closest('.view-page');
  const sentinel = document.createElement('div');
  sentinel.className = 'lazy-sentinel';
  grid.appendChild(sentinel);

  let index = 0;
  const loadMore = () => {
    const next = items.slice(index, index + batchSize);
    next.forEach(pkg => grid.insertBefore(createCardElement(pkg, null, showDelete), sentinel));
    index += next.length;
    sentinel.style.display = index >= items.length ? 'none' : 'flex';
  };
  loadMore();

  const obs = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) loadMore();
  }, { root: view, rootMargin: '400px' });
  obs.observe(sentinel);
  lazyObservers.set(gridId, obs);
}

function renderCategoryView(catId) {
  const catTitleEl = document.getElementById('cat-header-title');
  const catIconEl = document.getElementById('cat-header-icon');
  catIconEl.src = getCategoryIconPath(catId);
  catTitleEl.textContent = tr(`nav_${catId}`) || catId.toUpperCase();

  const grid = document.getElementById('category-grid');
  grid.innerHTML = '';

  let filtered = [];
  if (catId === 'all') {
    filtered = allPackages;
  } else {
    filtered = allPackages.filter(p => p.category && p.category.toLowerCase() === catId.toLowerCase());
  }

  if (filtered.length === 0) {
    resetLazyGrid('category-grid');
    grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 32px; text-align: center; color: var(--text-secondary); font-size: 14px;">${tr('no_packages_in_category')}</div>`;
    return;
  }

  renderLazyGrid('category-grid', () => filtered, false);
}

function renderInstalledView() {
  const updatesGrid = document.getElementById('updates-grid');
  updatesGrid.innerHTML = '';

  const updates = allPackages.filter(p => p.has_update);
  document.getElementById('updates-section-title').textContent = tr('downloads_and_updates', { count: updates.length });

  if (updates.length === 0) {
    updatesGrid.innerHTML = `<div style="grid-column: 1 / -1; padding: 16px; color: var(--text-secondary); font-size: 13px;">${tr('no_updates_installed')}</div>`;
  } else {
    updates.forEach(pkg => {
      updatesGrid.appendChild(createCardElement(pkg, null, true));
    });
  }

  const installed = allPackages.filter(p => p.installed);
  renderLazyGrid('installed-grid', () => installed, true);
}

// ── Search Handling ──
async function handleSearch(query) {
  if (!query || !query.trim()) {
    if (currentCategory === 'all') {
      switchView('view-discover');
    } else {
      switchView('view-category');
    }
    return;
  }
  const results = await invoke('search_packages', { query: query.trim() });
  document.getElementById('search-results-title').textContent = tr('results_for', { query });

  const guiApps = results.filter(p => p.is_a !== 'library');
  const libPkgs = results.filter(p => p.is_a === 'library');

  renderLazyGrid('search-apps-grid', () => (guiApps.length > 0 ? guiApps : results), false);
  renderLazyGrid('search-pkgs-grid', () => libPkgs, false);

  switchView('view-search');
}

// ── Sidebar Categories Initialization ──
function renderSidebarCategories(cats) {
  categories = cats || [];
  const navContainer = document.getElementById('sidebar-nav');
  navContainer.innerHTML = '';

  let updatesCount = 0;

  categories.forEach(cat => {
    if (cat.id === 'updates') {
      updatesCount = cat.count;
      return;
    }
    const btn = document.createElement('button');
    btn.className = `sidebar-btn ${cat.id === currentCategory ? 'active' : ''}`;
    btn.setAttribute('data-cat', cat.id);
    btn.innerHTML = `
      <img src="${getCategoryIconPath(cat.id)}" class="sidebar-icon-img" alt="${cat.name}">
      <span class="btn-text">${cat.name} (${cat.count})</span>
    `;
    btn.onclick = () => onNavClick(cat.id);
    navContainer.appendChild(btn);
  });

  updateSidebarUpdatesBadge(updatesCount);
}

function updateSidebarUpdatesBadge(count) {
  const badge = document.getElementById('sidebar-updates-badge');
  if (!badge) return;
  badge.textContent = count;
  badge.style.display = count > 0 ? 'inline-flex' : 'none';
}

function onNavClick(catId) {
  document.querySelectorAll('.sidebar-btn').forEach(btn => {
    if (btn.getAttribute('data-cat') === catId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  currentCategory = catId;
  if (catId === 'all') {
    renderDiscoverView();
    switchView('view-discover');
  } else if (catId === 'updates') {
    renderInstalledView();
    switchView('view-installed');
  } else if (catId === 'settings') {
    switchView('view-settings');
  } else if (catId === 'about') {
    switchView('view-about');
  } else {
    renderCategoryView(catId);
    switchView('view-category');
  }
}

// ── Image Viewer Modal ──
let modalScale = 1.0;
function openImageModal(src) {
  const modal = document.getElementById('image-modal');
  const img = document.getElementById('modal-target-img');
  img.src = src;
  modalScale = 1.0;
  img.style.transform = `scale(${modalScale})`;
  modal.classList.add('active');
}

function closeImageModal() {
  document.getElementById('image-modal').classList.remove('active');
}

// ── Settings Save Helper ──
async function saveCurrentSettings() {
  const newSettings = {
    autostart: document.getElementById('setting-autostart').checked,
    check_interval_hours: parseInt(document.getElementById('setting-interval').value) || 4,
    close_to_tray: document.getElementById('setting-close-to-tray').checked,
    auto_install_updates: document.getElementById('setting-auto-install').checked,
    language: document.getElementById('setting-language').value,
  };
  currentLanguage = newSettings.language;
  updateUiLanguage();
  await invoke('save_settings', { newSettings });
  await invoke('set_autostart', { enabled: newSettings.autostart });

  // Kategori isimlerini yeni dilde yeniden çek ve sidebarda güncelle
  try {
    const cats = await invoke('get_categories');
    renderSidebarCategories(cats);
  } catch (e) {
    console.error('Category refresh failed:', e);
  }
}

// ── App Initialization ──
async function initApp() {
  const overlay = document.getElementById('loading-overlay');
  const msgEl = document.getElementById('loading-msg');
  const fillEl = document.getElementById('loading-bar-fill');

  msgEl.textContent = tr('loading_prep');
  fillEl.style.width = '20%';

  try {
    // 1. Load Settings
    const settings = await invoke('load_settings');
    if (settings) {
      currentLanguage = settings.language || 'tr';
      document.getElementById('setting-autostart').checked = !!settings.autostart;
      document.getElementById('setting-close-to-tray').checked = settings.close_to_tray !== false;
      document.getElementById('setting-auto-install').checked = !!settings.auto_install_updates;
      document.getElementById('setting-interval').value = String(settings.check_interval_hours || 4);
      document.getElementById('setting-language').value = currentLanguage;
      updateUiLanguage();
    }

    msgEl.textContent = tr('loading_repo_pkgs');
    fillEl.style.width = '60%';

    // 2. Fetch Packages & Categories concurrently
    const [cats, pkgs] = await Promise.all([
      invoke('get_categories'),
      invoke('get_available_packages')
    ]);

    allPackages = pkgs || [];
    renderSidebarCategories(cats);

    msgEl.textContent = tr('loading_cache');
    fillEl.style.width = '90%';

    // 3. Render Discover
    renderDiscoverView();

    fillEl.style.width = '100%';
    setTimeout(() => {
      overlay.classList.add('hidden');
    }, 250);

  } catch (err) {
    console.error('Initialization error:', err);
    msgEl.textContent = tr('error_occurred') + ': ' + err;
  }
}

// ── Event Listeners ──
function on(id, event, fn) {
  const el = document.getElementById(id);
  if (el) el.addEventListener(event, fn);
}

document.addEventListener('DOMContentLoaded', () => {
  initApp();

  // Navigation back
  on('btn-nav-back', 'click', goBack);

  // Sidebar bottom buttons (Settings & About)
  document.querySelectorAll('.sidebar-bottom .sidebar-btn').forEach(btn => {
    const cat = btn.getAttribute('data-cat');
    if (cat) {
      btn.onclick = () => onNavClick(cat);
    }
  });

  // Search Input (Real-time debounced & Enter key)
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.oninput = () => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        handleSearch(searchInput.value);
      }, 250);
    };
    searchInput.onkeydown = (e) => {
      if (e.key === 'Enter') {
        clearTimeout(searchDebounceTimer);
        handleSearch(searchInput.value);
      }
    };
  }

  // Topbar Settings button
  on('btn-topbar-settings', 'click', () => onNavClick('settings'));

  // Modal events
  on('btn-modal-close', 'click', closeImageModal);
  on('btn-zoom-in', 'click', () => {
    modalScale = Math.min(modalScale * 1.2, 3.0);
    document.getElementById('modal-target-img').style.transform = `scale(${modalScale})`;
  });
  on('btn-zoom-out', 'click', () => {
    modalScale = Math.max(modalScale / 1.2, 0.3);
    document.getElementById('modal-target-img').style.transform = `scale(${modalScale})`;
  });
  on('btn-zoom-reset', 'click', () => {
    modalScale = 1.0;
    document.getElementById('modal-target-img').style.transform = `scale(${modalScale})`;
  });

  // Settings change listeners
  on('setting-autostart', 'change', saveCurrentSettings);
  on('setting-close-to-tray', 'change', saveCurrentSettings);
  on('setting-auto-install', 'change', saveCurrentSettings);
  on('setting-interval', 'change', saveCurrentSettings);
  on('setting-language', 'change', saveCurrentSettings);

  // Update repo button
  on('btn-update-repo', 'click', async () => {
    const btn = document.getElementById('btn-update-repo');
    btn.disabled = true;
    btn.textContent = tr('updating_repo');
    try {
      const res = await invoke('update_repo');
      alert(res.message);
    } catch (e) {
      alert(tr('error_occurred') + ': ' + e);
    }
    btn.disabled = false;
    btn.textContent = tr('btn_update_repo');
  });

  // Check updates button
  on('btn-check-updates', 'click', async () => {
    const btn = document.getElementById('btn-check-updates');
    btn.disabled = true;
    btn.textContent = tr('checking_updates');
    try {
      const res = await invoke('check_for_updates', { updateRepo: true });
      updateSidebarUpdatesBadge(res.count);
      if (res.count > 0) {
        alert(tr('updates_found_msg', { count: res.count }));
      } else {
        alert(tr('system_up_to_date_msg'));
      }
      renderInstalledView();
    } catch (e) {
      alert(tr('error_occurred') + ': ' + e);
    }
    btn.disabled = false;
    btn.textContent = tr('btn_check_updates');
  });

  // Backend events (updates-checked / tray-check-updates)
  const listen = (event, handler) => {
    if (window.__TAURI__ && window.__TAURI__.event && window.__TAURI__.event.listen) {
      window.__TAURI__.event.listen(event, (e) => handler(e.payload));
    }
  };

  listen('updates-checked', (payload) => {
    if (payload && typeof payload.count === 'number') {
      updateSidebarUpdatesBadge(payload.count);
      if (currentCategory === 'updates') {
        renderInstalledView();
      }
    }
  });

  listen('tray-check-updates', async () => {
    try {
      const res = await invoke('check_for_updates', { updateRepo: false });
      updateSidebarUpdatesBadge(res.count);
      if (currentCategory === 'updates') {
        renderInstalledView();
      }
    } catch (e) {
      console.error('Tray update check failed:', e);
    }
  });
});
