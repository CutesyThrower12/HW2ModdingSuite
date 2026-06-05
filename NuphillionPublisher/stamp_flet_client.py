from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: stamp_flet_client.py <target-dir> <icon.ico> <version_info.txt>")
        return 2

    target_dir = Path(sys.argv[1])
    icon_path = Path(sys.argv[2])
    version_path = Path(sys.argv[3])

    import flet_desktop
    from PyInstaller import config
    from PyInstaller.utils.win32 import icon, versioninfo

    cache_dir = flet_desktop.ensure_client_cached()
    source_dir = Path(cache_dir) / "flet"
    source_exe = source_dir / "flet.exe"
    if not source_exe.is_file():
        raise FileNotFoundError(f"Flet client executable not found: {source_exe}")

    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)

    target_exe = target_dir / "flet.exe"
    config.CONF["workpath"] = str(target_dir.parent / "_icon_work")
    if icon_path.is_file():
        icon.CopyIcons(str(target_exe), str(icon_path))
    if version_path.is_file():
        info = versioninfo.load_version_info_from_text_file(str(version_path))
        versioninfo.write_version_info_to_executable(str(target_exe), info)

    print(f"Stamped private Flet client: {target_exe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
