"""Windows Startup helper for Atlas daemon / Chat."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from .paths import repo_root_from_pkg


def startup_script_path() -> Path:
    return repo_root_from_pkg() / "scripts" / "atlas-chat-startup.ps1"


def windows_startup_folder() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def install_autostart(*, url: str = "http://127.0.0.1:8765/") -> dict[str, Any]:
    script = startup_script_path()
    cmd = script.with_suffix(".cmd")
    if not script.exists():
        return {"ok": False, "error": f"missing {script}"}
    if not cmd.exists():
        return {"ok": False, "error": f"missing {cmd}"}
    startup = windows_startup_folder()
    startup.mkdir(parents=True, exist_ok=True)
    dest_cmd = startup / "AtlasChat.cmd"
    dest_cmd.write_text(
        f'@echo off\r\n'
        f'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden '
        f'-File "{script}" -OpenUrl "{url}"\r\n',
        encoding="ascii",
    )
    old_lnk = startup / "AtlasChat.lnk"
    if old_lnk.exists():
        old_lnk.unlink()
    daemon_cmd = startup / "AtlasDaemon.cmd"
    atlas_exe = sys.executable
    daemon_cmd.write_text(
        f'@echo off\r\n'
        f'"{atlas_exe}" -m atlas_memory.cli daemon --host 127.0.0.1 --port 8765\r\n',
        encoding="ascii",
    )
    return {
        "ok": dest_cmd.exists(),
        "shortcut": str(dest_cmd),
        "daemon_shortcut": str(daemon_cmd),
        "script": str(script),
        "stderr": "",
    }


def uninstall_autostart() -> dict[str, Any]:
    startup = windows_startup_folder()
    removed: list[str] = []
    for name in ("AtlasChat.lnk", "AtlasChat.cmd", "AtlasDaemon.cmd"):
        path = startup / name
        if path.exists():
            path.unlink()
            removed.append(str(path))
    return {"ok": True, "removed": removed or None, "message": None if removed else "shortcut not present"}
