"""Platform abstraction — the only place that may know which OS it is on.

The core (net/game/scheduler/config) must stay OS-agnostic; anything that
differs per platform (paths, UI backend, future cert/ADB plumbing) goes
through a :class:`Platform` implementation chosen by :func:`get_platform`.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlatformPaths:
    """Filesystem locations, resolved per-OS."""

    data_dir: Path        # profiles/, rules.json, settings
    log_dir: Path         # rotating logs

    def profile_path(self, wizard_id: int | str) -> Path:
        return self.data_dir / "profiles" / f"{wizard_id}.json"

    def rules_path(self) -> Path:
        return self.data_dir / "rules.json"


class Platform:
    """Base platform: portable defaults (works on all three OSes)."""

    name = "base"

    def paths(self, app_name: str = "swauto") -> PlatformPaths:
        home = Path.home()
        data = home / f".{app_name}"
        return PlatformPaths(data_dir=data, log_dir=data / "logs")

    def ui_backend(self) -> str:
        """Preferred WebView backend name (informational; UI is pluggable)."""
        return "headless"


class WindowsPlatform(Platform):
    name = "windows"

    def paths(self, app_name: str = "swauto") -> PlatformPaths:
        base = Path.home() / "AppData" / "Local" / app_name
        return PlatformPaths(data_dir=base, log_dir=base / "logs")

    def ui_backend(self) -> str:
        return "webview2"


class MacPlatform(Platform):
    name = "macos"

    def paths(self, app_name: str = "swauto") -> PlatformPaths:
        base = Path.home() / "Library" / "Application Support" / app_name
        return PlatformPaths(data_dir=base, log_dir=Path.home() / "Library" / "Logs" / app_name)

    def ui_backend(self) -> str:
        return "wkwebview"


class LinuxPlatform(Platform):
    name = "linux"

    def paths(self, app_name: str = "swauto") -> PlatformPaths:
        import os
        base = Path(os.environ.get("XDG_DATA_HOME", home_local())) / app_name
        return PlatformPaths(data_dir=base, log_dir=base / "logs")


def home_local() -> Path:
    import os
    return Path(os.environ.get("HOME", str(Path.home()))) / ".local" / "share"


def get_platform() -> Platform:
    if sys.platform.startswith("win"):
        return WindowsPlatform()
    if sys.platform == "darwin":
        return MacPlatform()
    return LinuxPlatform()
