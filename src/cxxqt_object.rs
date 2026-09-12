use core::pin::Pin;
use std::sync::{Arc, Mutex};
use cxx_qt::{CxxQtType, Threading};
use cxx_qt_lib::QString;
use crate::backend::{LuppoBackend, PackageInfo};
use crate::settings::{self, AppSettings};
use crate::i18n;

#[derive(serde::Serialize, serde::Deserialize)]
pub struct CategoryInfo {
    pub id: String,
    pub icon: String,
    pub name: String,
    pub count: usize,
}

#[derive(serde::Serialize, serde::Deserialize)]
pub struct ActionResponse {
    pub success: bool,
    pub message: String,
}

#[derive(serde::Serialize, serde::Deserialize)]
pub struct UpdatesResponse {
    pub count: usize,
    pub packages: Vec<String>,
    pub error: String,
}

#[cxx_qt::bridge]
pub mod qobject {
    unsafe extern "C++" {
        include!("cxx-qt-lib/qstring.h");
        type QString = cxx_qt_lib::QString;

        include!("cxx-qt-lib/qguiapplication.h");
        type QGuiApplication = cxx_qt_lib::QGuiApplication;

        include!("src/app_init.h");
        fn create_qapplication() -> UniquePtr<QGuiApplication>;
    }

    extern "RustQt" {
        #[qobject]
        #[qml_element]
        type BackendBridge = super::BackendBridgeRust;

        #[qsignal]
        #[cxx_name = "packageProgress"]
        fn package_progress(
            self: Pin<&mut Self>,
            package_name: QString,
            progress: i32,
            status: QString,
            message: QString,
        );

        #[qsignal]
        #[cxx_name = "updatesChecked"]
        fn updates_checked(self: Pin<&mut Self>, count: i32, packages_json: QString);

        #[qsignal]
        #[cxx_name = "packagesChanged"]
        fn packages_changed(self: Pin<&mut Self>);

        #[qinvokable]
        #[cxx_name = "getAvailablePackages"]
        fn get_available_packages(&self) -> QString;

        #[qinvokable]
        #[cxx_name = "getInstalledPackages"]
        fn get_installed_packages(&self) -> QString;

        #[qinvokable]
        #[cxx_name = "getPackageDetails"]
        fn get_package_details(&self, package_name: &QString) -> QString;

        #[qinvokable]
        #[cxx_name = "getCategories"]
        fn get_categories(&self) -> QString;

        #[qinvokable]
        #[cxx_name = "searchPackages"]
        fn search_packages(&self, query: &QString) -> QString;

        #[qinvokable]
        #[cxx_name = "checkForUpdates"]
        fn check_for_updates(self: Pin<&mut Self>, update_repo: bool) -> QString;

        #[qinvokable]
        #[cxx_name = "updateRepo"]
        fn update_repo(&self) -> QString;

        #[qinvokable]
        #[cxx_name = "getFlatpakInfo"]
        fn get_flatpak_info(&self, app_id: &QString) -> QString;

        #[qinvokable]
        #[cxx_name = "loadSettings"]
        fn load_settings(&self) -> QString;

        #[qinvokable]
        #[cxx_name = "saveSettings"]
        fn save_settings(&self, settings_json: &QString) -> QString;

        #[qinvokable]
        #[cxx_name = "setAutostart"]
        fn set_autostart(&self, enabled: bool) -> QString;

        #[qinvokable]
        #[cxx_name = "installPackage"]
        fn install_package(self: Pin<&mut Self>, package_name: &QString);

        #[qinvokable]
        #[cxx_name = "removePackage"]
        fn remove_package(self: Pin<&mut Self>, package_name: &QString);

        #[qinvokable]
        #[cxx_name = "cancelPackage"]
        fn cancel_package(self: Pin<&mut Self>, package_name: &QString);

        #[qinvokable]
        #[cxx_name = "translateKey"]
        fn translate_key(&self, key: &QString) -> QString;

        #[qinvokable]
        #[cxx_name = "setLanguage"]
        fn set_language(&self, lang: &QString);

        #[qinvokable]
        #[cxx_name = "getAppVersion"]
        fn get_app_version(&self) -> QString;

        #[qinvokable]
        #[cxx_name = "loadPackagesAsync"]
        fn load_packages_async(self: Pin<&mut Self>);
    }

    impl cxx_qt::Threading for BackendBridge {}
}

pub struct BackendBridgeRust {
    backend: Arc<Mutex<LuppoBackend>>,
}

impl Default for BackendBridgeRust {
    fn default() -> Self {
        Self {
            backend: Arc::new(Mutex::new(LuppoBackend::new())),
        }
    }
}

impl qobject::BackendBridge {
    pub fn get_available_packages(&self) -> QString {
        let mut backend = match self.rust().backend.lock() {
            Ok(b) => b,
            Err(_e) => return QString::from(&format!("[]")),
        };

        if backend.available_packages.is_empty() {
            if backend.installed_packages.is_empty() {
                backend.load_installed_packages();
                backend.load_installed_flatpaks();
            }
            backend.load_available_packages();
            if backend.flatpak_available {
                backend.load_available_flatpaks();
            }
        }

        let mut pkgs: Vec<PackageInfo> = backend.get_all_packages().into_values().collect();
        pkgs.sort_by(|a, b| a.display_name.to_lowercase().cmp(&b.display_name.to_lowercase()));
        let json = serde_json::to_string(&pkgs).unwrap_or_else(|_| "[]".to_string());
        QString::from(&json)
    }

    pub fn get_installed_packages(&self) -> QString {
        let mut backend = match self.rust().backend.lock() {
            Ok(b) => b,
            Err(_) => return QString::from("[]"),
        };

        if backend.installed_packages.is_empty() {
            backend.load_installed_packages();
            backend.load_installed_flatpaks();
        }

        let mut pkgs: Vec<PackageInfo> = backend.installed_packages.values().cloned().collect();
        pkgs.sort_by(|a, b| a.display_name.to_lowercase().cmp(&b.display_name.to_lowercase()));
        let json = serde_json::to_string(&pkgs).unwrap_or_else(|_| "[]".to_string());
        QString::from(&json)
    }

    pub fn get_package_details(&self, package_name: &QString) -> QString {
        let name = package_name.to_string();
        let mut backend = match self.rust().backend.lock() {
            Ok(b) => b,
            Err(_) => return QString::from("{}"),
        };

        match backend.enrich_package_info(&name) {
            Some(pkg) => {
                let json = serde_json::to_string(&pkg).unwrap_or_else(|_| "{}".to_string());
                QString::from(&json)
            }
            None => QString::from("{}"),
        }
    }

    pub fn get_categories(&self) -> QString {
        let (all, counts) = if let Ok(backend) = self.rust().backend.lock() {
            let all_pkgs = backend.get_all_packages();
            let mut c: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
            for pkg in all_pkgs.values() {
                *c.entry(pkg.category.clone()).or_insert(0) += 1;
            }
            (all_pkgs, c)
        } else {
            (std::collections::HashMap::new(), std::collections::HashMap::new())
        };

        let category_meta: Vec<(&str, &str, &str)> = vec![
            ("all", "plasma-search", "nav_discover"),
            ("development", "applications-development", "nav_development"),
            ("education", "applications-education", "nav_education"),
            ("enterprise", "applications-office", "nav_enterprise"),
            ("games", "applications-games", "nav_games"),
            ("graphics", "applications-graphics", "nav_graphics"),
            ("internet", "applications-internet", "nav_internet"),
            ("multimedia", "applications-multimedia", "nav_multimedia"),
            ("office", "applications-office", "nav_office"),
            ("system", "applications-system", "nav_system"),
            ("utilities", "applications-utilities", "nav_utilities"),
        ];

        let result: Vec<CategoryInfo> = category_meta.iter().map(|(id, icon, name_key)| {
            let count = if *id == "all" {
                all.len()
            } else {
                *counts.get(*id).unwrap_or(&0)
            };
            CategoryInfo {
                id: id.to_string(),
                icon: icon.to_string(),
                name: i18n::tr(name_key),
                count,
            }
        }).collect();

        let json = serde_json::to_string(&result).unwrap_or_else(|_| "[]".to_string());
        QString::from(&json)
    }

    pub fn search_packages(&self, query: &QString) -> QString {
        let q = query.to_string();
        let backend = match self.rust().backend.lock() {
            Ok(b) => b,
            Err(_) => return QString::from("[]"),
        };

        let mut results = backend.search_packages(&q);
        results.sort_by(|a, b| a.display_name.to_lowercase().cmp(&b.display_name.to_lowercase()));
        let json = serde_json::to_string(&results).unwrap_or_else(|_| "[]".to_string());
        QString::from(&json)
    }

    pub fn check_for_updates(self: Pin<&mut Self>, update_repo: bool) -> QString {
        let qt_thread = self.qt_thread();
        let backend_arc = self.rust().backend.clone();

        std::thread::spawn(move || {
            let (count, packages, _error) = {
                let mut backend = backend_arc.lock().unwrap();
                backend.check_for_updates(update_repo)
            };

            let pkgs_json = serde_json::to_string(&packages).unwrap_or_else(|_| "[]".to_string());
            let pkgs_qstr = QString::from(&pkgs_json);

            qt_thread.queue(move |mut qobj| {
                qobj.as_mut().updates_checked(count as i32, pkgs_qstr);
            }).ok();
        });

        let resp = UpdatesResponse { count: 0, packages: vec![], error: String::new() };
        QString::from(&serde_json::to_string(&resp).unwrap())
    }

    pub fn update_repo(&self) -> QString {
        let backend = match self.rust().backend.lock() {
            Ok(b) => b,
            Err(e) => {
                let r = ActionResponse { success: false, message: e.to_string() };
                return QString::from(&serde_json::to_string(&r).unwrap());
            }
        };

        let success = backend.update_repo();
        let message = if success {
            i18n::tr("repo_update_success")
        } else {
            i18n::tr("repo_update_error")
        };
        let r = ActionResponse { success, message };
        QString::from(&serde_json::to_string(&r).unwrap())
    }

    pub fn get_flatpak_info(&self, app_id: &QString) -> QString {
        let id_str = app_id.to_string();
        let real_id = id_str.trim_start_matches("flatpak:").to_string();
        let url = format!("https://flathub.org/api/v2/appstream/{}", real_id);

        let result = match reqwest::blocking::Client::builder()
            .user_agent("Mozilla/5.0 (X11; Linux x86_64)")
            .timeout(std::time::Duration::from_secs(8))
            .build()
        {
            Ok(client) => match client.get(&url).send() {
                Ok(resp) => resp.text().unwrap_or_else(|_| "{}".to_string()),
                Err(_) => "{}".to_string(),
            },
            Err(_) => "{}".to_string(),
        };

        QString::from(&result)
    }

    pub fn load_settings(&self) -> QString {
        let s = settings::load_settings();
        i18n::set_lang(&s.language);
        let json = serde_json::to_string(&s).unwrap_or_else(|_| "{}".to_string());
        QString::from(&json)
    }

    pub fn save_settings(&self, settings_json: &QString) -> QString {
        let json_str = settings_json.to_string();
        let s: AppSettings = match serde_json::from_str(&json_str) {
            Ok(val) => val,
            Err(e) => {
                let r = ActionResponse { success: false, message: e.to_string() };
                return QString::from(&serde_json::to_string(&r).unwrap());
            }
        };

        i18n::set_lang(&s.language);
        match settings::save_settings(&s) {
            Ok(()) => {
                let r = ActionResponse { success: true, message: i18n::tr("settings_saved") };
                QString::from(&serde_json::to_string(&r).unwrap())
            }
            Err(e) => {
                let r = ActionResponse { success: false, message: e };
                QString::from(&serde_json::to_string(&r).unwrap())
            }
        }
    }

    pub fn set_autostart(&self, enabled: bool) -> QString {
        match settings::set_autostart(enabled) {
            Ok(()) => {
                let r = ActionResponse { success: true, message: i18n::tr("autostart_updated") };
                QString::from(&serde_json::to_string(&r).unwrap())
            }
            Err(e) => {
                let r = ActionResponse { success: false, message: e };
                QString::from(&serde_json::to_string(&r).unwrap())
            }
        }
    }

    pub fn install_package(self: Pin<&mut Self>, package_name: &QString) {
        let pkg_name = package_name.to_string();
        let qt_thread = self.qt_thread();
        let backend_arc = self.rust().backend.clone();

        std::thread::spawn(move || {
            let rt = tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .unwrap();

            rt.block_on(async {
                let backend_clone = {
                    let backend = backend_arc.lock().unwrap();
                    backend.clone()
                };

                let qt_thread_progress = qt_thread.clone();

                let (success, _msg) = backend_clone.install_package_with_progress(&pkg_name, move |event| {
                    let qt = qt_thread_progress.clone();
                    let pkg_qstr = QString::from(&event.package_name);
                    let status_qstr = QString::from(&event.status);
                    let msg_qstr = QString::from(&event.message);
                    let prog = event.progress as i32;

                    qt.queue(move |mut qobj| {
                        qobj.as_mut().package_progress(pkg_qstr, prog, status_qstr, msg_qstr);
                    }).ok();
                }).await;

                if success {
                    let mut backend = backend_arc.lock().unwrap();
                    if let Some(pkg) = backend.available_packages.get_mut(&pkg_name) {
                        pkg.installed = true;
                        pkg.has_update = false;
                    }
                    if let Some(pkg) = backend.installed_packages.get_mut(&pkg_name) {
                        pkg.has_update = false;
                    } else if let Some(pkg) = backend.available_packages.get(&pkg_name).cloned() {
                        backend.installed_packages.insert(pkg_name.clone(), pkg);
                    }
                }

                let is_self = {
                    let name = pkg_name.trim_start_matches("flatpak:").to_lowercase();
                    name == "lupus-software-center" || name == env!("CARGO_PKG_NAME")
                };

                qt_thread.queue(move |mut qobj| {
                    let done_msg = if success { QString::from(&i18n::tr("status_completed")) } else { QString::from(&i18n::tr("status_error")) };
                    let status_msg = if success { QString::from("completed") } else { QString::from("error") };
                    qobj.as_mut().package_progress(QString::from(&pkg_name), 100, status_msg, done_msg);
                    qobj.as_mut().packages_changed();
                }).ok();

                if success && is_self {
                    std::thread::sleep(std::time::Duration::from_millis(800));
                    restart_application();
                }
            });
        });
    }

    pub fn remove_package(self: Pin<&mut Self>, package_name: &QString) {
        let pkg_name = package_name.to_string();
        let qt_thread = self.qt_thread();
        let backend_arc = self.rust().backend.clone();

        std::thread::spawn(move || {
            let rt = tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .unwrap();

            rt.block_on(async {
                let backend_clone = {
                    let backend = backend_arc.lock().unwrap();
                    backend.clone()
                };

                let qt_thread_progress = qt_thread.clone();

                let (success, _msg) = backend_clone.remove_package_with_progress(&pkg_name, move |event| {
                    let qt = qt_thread_progress.clone();
                    let pkg_qstr = QString::from(&event.package_name);
                    let status_qstr = QString::from(&event.status);
                    let msg_qstr = QString::from(&event.message);
                    let prog = event.progress as i32;

                    qt.queue(move |mut qobj| {
                        qobj.as_mut().package_progress(pkg_qstr, prog, status_qstr, msg_qstr);
                    }).ok();
                }).await;

                if success {
                    let mut backend = backend_arc.lock().unwrap();
                    backend.installed_packages.remove(&pkg_name);
                    if let Some(pkg) = backend.available_packages.get_mut(&pkg_name) {
                        pkg.installed = false;
                        pkg.has_update = false;
                    }
                }

                qt_thread.queue(move |mut qobj| {
                    let done_msg = if success { QString::from(&i18n::tr("status_completed")) } else { QString::from(&i18n::tr("status_error")) };
                    let status_msg = if success { QString::from("completed") } else { QString::from("error") };
                    qobj.as_mut().package_progress(QString::from(&pkg_name), 100, status_msg, done_msg);
                    qobj.as_mut().packages_changed();
                }).ok();
            });
        });
    }

    pub fn cancel_package(self: Pin<&mut Self>, package_name: &QString) {
        let pkg = package_name.to_string();
        crate::backend::cancel_process(&pkg);
        self.package_progress(
            package_name.clone(),
            0,
            QString::from("error"),
            QString::from(&i18n::tr("status_cancelled")),
        );
    }

    pub fn translate_key(&self, key: &QString) -> QString {
        let k = key.to_string();
        QString::from(&i18n::tr(&k))
    }

    pub fn set_language(&self, lang: &QString) {
        let l = lang.to_string();
        i18n::set_lang(&l);
    }

    pub fn get_app_version(&self) -> QString {
        QString::from(crate::backend::VERSION)
    }

    pub fn load_packages_async(self: Pin<&mut Self>) {
        let qt_thread = self.qt_thread();
        let backend_arc = self.rust().backend.clone();

        std::thread::spawn(move || {
            let mut temp_backend = {
                match backend_arc.lock() {
                    Ok(guard) => guard.clone(),
                    Err(_) => return,
                }
            };

            if temp_backend.installed_packages.is_empty() {
                temp_backend.load_installed_packages();
                temp_backend.load_installed_flatpaks();
            }
            if temp_backend.available_packages.is_empty() {
                temp_backend.load_available_packages();
                if temp_backend.flatpak_available {
                    temp_backend.load_available_flatpaks();
                }
            }

            if let Ok(mut backend) = backend_arc.lock() {
                *backend = temp_backend;
            }

            qt_thread.queue(move |mut qobj| {
                qobj.as_mut().packages_changed();
            }).ok();
        });
    }
}

fn restart_application() {
    if let Ok(exe) = std::env::current_exe() {
        let args: Vec<String> = std::env::args().skip(1).collect();
        let _ = std::process::Command::new(exe).args(&args).spawn();
        std::process::exit(0);
    }
}
