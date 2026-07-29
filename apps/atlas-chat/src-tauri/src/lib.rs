use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

use tauri::Manager;

fn daemon_already_up() -> bool {
    // Best-effort TCP check via std — avoid extra deps
    std::net::TcpStream::connect_timeout(
        &"127.0.0.1:8765".parse().unwrap(),
        Duration::from_millis(400),
    )
    .is_ok()
}

fn spawn_daemon() {
    if daemon_already_up() {
        eprintln!("atlas daemon already on :8765");
        return;
    }
    // Prefer `atlas daemon`, fall back to python -m
    let launched = Command::new("atlas")
        .args(["daemon", "--host", "127.0.0.1", "--port", "8765"])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .ok()
        .or_else(|| {
            Command::new("py")
                .args([
                    "-3",
                    "-m",
                    "atlas_memory.cli",
                    "daemon",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8765",
                ])
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .ok()
        })
        .or_else(|| {
            Command::new("python")
                .args([
                    "-m",
                    "atlas_memory.cli",
                    "daemon",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8765",
                ])
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .ok()
        });
    if launched.is_some() {
        eprintln!("atlas daemon spawn requested");
        thread::sleep(Duration::from_millis(600));
    } else {
        eprintln!("atlas daemon not found — run: atlas daemon");
    }
}

#[tauri::command]
fn daemon_status() -> serde_json::Value {
    let up = daemon_already_up();
    serde_json::json!({ "ok": up, "url": "http://127.0.0.1:8765/" })
}

#[tauri::command]
fn ensure_daemon() -> serde_json::Value {
    spawn_daemon();
    let up = daemon_already_up();
    serde_json::json!({ "ok": up, "url": "http://127.0.0.1:8765/" })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            spawn_daemon();
            let _ = app;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![daemon_status, ensure_daemon])
        .run(tauri::generate_context!())
        .expect("error while running Atlas Chat");
}
