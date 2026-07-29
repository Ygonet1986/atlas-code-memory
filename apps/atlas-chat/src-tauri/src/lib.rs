use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // Sidecar expected: `atlas life serve` on 8765 (started externally or via shell).
            let _ = app;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Atlas Chat");
}
