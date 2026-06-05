from __future__ import annotations

import asyncio
import os
import queue
import sys
from pathlib import Path

import flet as ft

from publisher_core import (
    DEFAULT_EXPANSION_SOURCE,
    DEFAULT_LAUNCHER_REPO,
    DEFAULT_RELEASE_DOWNLOAD_DIR,
    PublishOptions,
    default_gts_dir,
    publish,
)

if not hasattr(ft, "icons"):
    class _Icons:
        def __getattr__(self, name: str) -> str:
            return name.lower()
    ft.icons = _Icons()


TEAL = "#a0cafd"
PANEL_BG = "#0f1720"
CARD_BG = "#151822"
INPUT_BG = "#1a1a1a"
OUTPUT_BG = "#0b0f14"
BORDER = "#263445"
APP_USER_MODEL_ID = "CutesyThrower12.NuphillionPublisher"


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def set_private_flet_view_path() -> None:
    base_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    flet_view = base_dir / "flet_view"
    if (flet_view / "flet.exe").is_file():
        os.environ["FLET_VIEW_PATH"] = str(flet_view)


def main(page: ft.Page) -> None:
    set_windows_app_id()
    page.title = "Nuphillion Publisher"
    page.window_width = 1220
    page.window_height = 820
    page.window_min_width = 1040
    page.window_min_height = 640
    page.theme_mode = "dark"
    page.bgcolor = "#090d12"
    page.padding = 0

    launcher_repo = ft.TextField(label="Nuphillion Launcher repo", value=str(DEFAULT_LAUNCHER_REPO), bgcolor=INPUT_BG, expand=True)
    gts_dir = ft.TextField(label="Compiled GTS output", value=str(default_gts_dir()), bgcolor=INPUT_BG, expand=True)
    expansion_source = ft.TextField(label="Loose expansion source", value=str(DEFAULT_EXPANSION_SOURCE), bgcolor=INPUT_BG, expand=True)
    release_download_dir = ft.TextField(label="Release ZIP download folder", value=str(DEFAULT_RELEASE_DOWNLOAD_DIR), bgcolor=INPUT_BG, expand=True)
    commit_message = ft.TextField(label="Commit message", value="Publish Nuphillion mod assets", bgcolor=INPUT_BG, expand=True)

    refresh_patch = ft.Checkbox(label="Refresh moddedPatch.zip", value=True)
    refresh_expansion = ft.Checkbox(label="Refresh nuphillionExpansion.zip", value=False)
    initialize_release = ft.Checkbox(label="Initialize/update Release workflow", value=False)
    run_release = ft.Checkbox(label="Run GitHub Release workflow", value=False)
    download_release = ft.Checkbox(label="Download release ZIP after workflow", value=False)
    ensure_lfs = ft.Checkbox(label="Ensure Git LFS", value=True)
    commit_changes = ft.Checkbox(label="Commit launcher changes", value=True)
    push_changes = ft.Checkbox(label="Push to GitHub", value=False)

    status = ft.Text("Ready", color=TEAL, weight="bold")
    progress = ft.ProgressBar(value=0, color=TEAL, bgcolor="#1c2530")
    output = ft.TextField(
        label="Publish log",
        multiline=True,
        min_lines=18,
        max_lines=24,
        value="",
        bgcolor=OUTPUT_BG,
        border_color=BORDER,
        text_size=12,
        read_only=True,
        expand=True,
    )

    def pick_folder(target: ft.TextField, title: str) -> None:
        try:
            from tkinter import Tk, filedialog

            root = Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            start_dir = target.value if target.value and Path(target.value).exists() else str(Path.home())
            path = filedialog.askdirectory(title=title, initialdir=start_dir)
            root.destroy()
            set_folder(target, path)
        except Exception as exc:
            log_line(f"Browse failed: {exc}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Browse failed: {exc}"), open=True)
            page.update()

    def set_folder(target: ft.TextField, path: str | None) -> None:
        if path:
            target.value = path
            page.update()

    def log_line(text: str) -> None:
        output.value = (output.value + "\n" + text).strip()
        page.update()

    def drain_log(log_queue: queue.Queue[str]) -> None:
        changed = False
        while True:
            try:
                line = log_queue.get_nowait()
            except queue.Empty:
                break
            output.value = (output.value + "\n" + line).strip()
            changed = True
        if changed:
            page.update()

    async def run_publish(_=None) -> None:
        output.value = ""
        status.value = "Publishing..."
        progress.value = None
        page.update()

        options = PublishOptions(
            launcher_repo=Path(launcher_repo.value.strip()),
            gts_dir=Path(gts_dir.value.strip()),
            expansion_source=Path(expansion_source.value.strip()),
            refresh_modded_patch=bool(refresh_patch.value),
            refresh_expansion=bool(refresh_expansion.value),
            ensure_lfs=bool(ensure_lfs.value),
            commit_changes=bool(commit_changes.value),
            push_changes=bool(push_changes.value),
            commit_message=commit_message.value.strip() or "Publish Nuphillion mod assets",
            initialize_release_workflow=bool(initialize_release.value),
            run_release_workflow=bool(run_release.value),
            download_release_zip=bool(download_release.value),
            release_download_dir=Path(release_download_dir.value.strip()),
        )

        log_queue: queue.Queue[str] = queue.Queue()

        try:
            loop = asyncio.get_running_loop()
            future = loop.run_in_executor(None, lambda: publish(options, progress=log_queue.put))
            while not future.done():
                drain_log(log_queue)
                await asyncio.sleep(0.12)
            result = await future
            drain_log(log_queue)
            status.value = "Publish complete"
            progress.value = 1
            page.snack_bar = ft.SnackBar(ft.Text("Nuphillion publish completed."), open=True)
        except Exception as exc:
            drain_log(log_queue)
            status.value = "Publish failed"
            progress.value = 0
            log_line(f"ERROR: {exc}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Publish failed: {exc}"), open=True)
        page.update()

    def publish_clicked(e=None) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(run_publish(e))
        else:
            asyncio.run(run_publish(e))

    def folder_row(field: ft.TextField, title: str) -> ft.Row:
        return ft.Row(
            [
                field,
                ft.ElevatedButton("Browse", on_click=lambda _: pick_folder(field, title), bgcolor="#1f5fbf", color="white"),
            ],
            spacing=10,
        )

    header = ft.Container(
        bgcolor="#121922",
        padding=18,
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Nuphillion Publisher", size=24, weight="bold", color="white"),
                        ft.Text("Build launcher-ready ZIP assets, commit them cleanly, and keep LFS handled.", size=12, color="white70"),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.ElevatedButton("Publish", icon="rocket_launch", on_click=publish_clicked, bgcolor="#2b73e0", color="white"),
            ],
            alignment="spaceBetween",
        ),
    )

    settings = ft.Container(
        bgcolor=CARD_BG,
        border_radius=8,
        padding=18,
        content=ft.Column(
            [
                ft.Text("Paths", size=16, weight="bold", color=TEAL),
                folder_row(launcher_repo, "Select NuphillionDev repo"),
                folder_row(gts_dir, "Select compiled GTS output folder"),
                folder_row(expansion_source, "Select loose expansion source folder"),
                folder_row(release_download_dir, "Select release ZIP download folder"),
                ft.Divider(height=18, color=BORDER),
                ft.Text("Publish Toggles", size=16, weight="bold", color=TEAL),
                ft.Row([refresh_patch, refresh_expansion], spacing=24),
                ft.Row([ensure_lfs, commit_changes, push_changes], spacing=24),
                ft.Divider(height=18, color=BORDER),
                ft.Text("Release Automation", size=16, weight="bold", color=TEAL),
                ft.Row([initialize_release, run_release, download_release], spacing=24),
                commit_message,
            ],
            spacing=10,
        ),
    )

    log_panel = ft.Container(
        bgcolor=CARD_BG,
        border_radius=8,
        padding=18,
        content=ft.Column(
            [
                ft.Row([status], alignment="spaceBetween"),
                progress,
                output,
            ],
            spacing=12,
        ),
    )

    page.add(
        ft.Column(
            [
                header,
                ft.Container(
                    padding=18,
                    expand=True,
                    content=ft.Column([settings, log_panel], scroll="auto", spacing=16),
                ),
            ],
            expand=True,
            spacing=0,
        )
    )


if __name__ == "__main__":
    set_windows_app_id()
    set_private_flet_view_path()
    ft.app(target=main)
