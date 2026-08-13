// PiSiM - Main entry point

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    let minimized = std::env::args().any(|a| a == "--minimized");
    pisim_lib::run(minimized);
}