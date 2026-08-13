// PiSiM – Ayarlar Yönetimi
// Python settings.py'nin Rust karşılığı

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub autostart: bool,
    pub check_interval_hours: i32,
    pub close_to_tray: bool,
    pub auto_install_updates: bool,
    pub language: String,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            autostart: false,
            check_interval_hours: 4,
            close_to_tray: true,
            auto_install_updates: false,
            language: "tr".to_string(),
        }
    }
}

fn config_dir() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("/tmp"))
        .join(".config")
        .join("pisim")
}

fn settings_file() -> PathBuf {
    config_dir().join("settings.json")
}

fn autostart_file() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("/tmp"))
        .join(".config")
        .join("autostart")
        .join("com.teknoanka.pisim.desktop")
}

pub fn load_settings() -> AppSettings {
    let file = settings_file();
    let mut settings = if file.exists() {
        if let Ok(content) = std::fs::read_to_string(&file) {
            if let Ok(s) = serde_json::from_str::<AppSettings>(&content) {
                s
            } else {
                AppSettings::default()
            }
        } else {
            AppSettings::default()
        }
    } else {
        let defaults = AppSettings::default();
        let _ = save_settings(&defaults);
        defaults
    };
    if is_autostart_enabled() {
        settings.autostart = true;
    }
    settings
}

pub fn save_settings(settings: &AppSettings) -> Result<(), String> {
    let dir = config_dir();
    std::fs::create_dir_all(&dir)
        .map_err(|e| e.to_string())?;
    let json = serde_json::to_string_pretty(settings)
        .map_err(|e| e.to_string())?;
    std::fs::write(settings_file(), json)
        .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn is_autostart_enabled() -> bool {
    autostart_file().exists()
}

pub fn set_autostart(enabled: bool) -> Result<(), String> {
    let file = autostart_file();
    if enabled {
        let parent = file.parent().unwrap();
        std::fs::create_dir_all(parent)
            .map_err(|e| e.to_string())?;

        let exe = std::env::current_exe()
            .unwrap_or_else(|_| PathBuf::from("pisim"))
            .to_string_lossy()
            .to_string();

        let icon = std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.join("icons/128x128.png")))
            .filter(|p| p.exists())
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|| "pisim".to_string());

        let content = format!(
            "[Desktop Entry]\nType=Application\nName=PiSiM\nComment=PiSi Market\nExec={} --minimized\nIcon={}\nTerminal=false\nCategories=System;PackageManager;\nX-GNOME-Autostart-enabled=true\nStartupNotify=false\n",
            exe, icon
        );
        std::fs::write(&file, content)
            .map_err(|e| e.to_string())?;
    } else {
        if file.exists() {
            std::fs::remove_file(&file)
                .map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}
