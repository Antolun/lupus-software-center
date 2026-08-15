// LupuS Software Center - Main entry point

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    let minimized = std::env::args().any(|a| a == "--minimized");
    lupus_software_center_lib::run(minimized);
}