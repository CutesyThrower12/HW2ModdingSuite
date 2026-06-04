from __future__ import annotations

import asyncio
from pathlib import Path

import flet as ft

from publisher_core import (
    DEFAULT_EXPANSION_SOURCE,
    DEFAULT_LAUNCHER_REPO,
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


def main(page: ft.Page) -> None:
    page.title = "Nuphillion Publisher"
    page.window_width = 1020
    page.window_height = 760
    page.window_min_width = 900
    page.window_min_height = 640
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#090d12"
    page.padding = 0

    launcher_repo = ft.TextField(label="Nuphillion Launcher repo", value=str(DEFAULT_LAUNCHER_REPO), bgcolor=INPUT_BG, expand=True)
    gts_dir = ft.TextField(label="Compiled GTS output", value=str(default_gts_dir()), bgcolor=INPUT_BG, expand=True)
    expansion_source = ft.TextField(label="Loose expansion source", value=str(DEFAULT_EXPANSION_SOURCE), bgcolor=INPUT_BG, expand=True)
    commit_message = ft.TextField(label="Commit message", value="Publish Nuphillion mod assets", bgcolor=INPUT_BG, expand=True)

    refresh_patch = ft.Checkbox(label="Refresh moddedPatch.zip", value=True)
    refresh_expansion = ft.Checkbox(label="Refresh nuphillionExpansion.zip", value=False)
    ensure_lfs = ft.Checkbox(label="Ensure Git LFS", value=True)
    commit_changes = ft.Checkbox(label="Commit launcher changes", value=True)
    push_changes = ft.Checkbox(label="Push to GitHub", value=False)

    status = ft.Text("Ready", color=TEAL, weight=ft.FontWeight.BOLD)
    progress = ft.ProgressBar(value=0, color=TEAL, bgcolor="#1c2530")
    output = ft.TextField(
        label="Publish log",
        multiline=True,
        min_lines=14,
        max_lines=18,
        value="",
        bgcolor=OUTPUT_BG,
        border_color=BORDER,
        text_size=12,
        read_only=True,
    )

    def pick_folder(target: ft.TextField, title: str) -> None:
        picker = ft.FilePicker(on_result=lambda e: set_folder(target, e.path))
        page.overlay.append(picker)
        page.update()
        picker.get_directory_path(dialog_title=title)

    def set_folder(target: ft.TextField, path: str | None) -> None:
        if path:
            target.value = path
            page.update()

    def log_line(text: str) -> None:
        output.value = (output.value + "\n" + text).strip()
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
        )

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, lambda: publish(options))
            output.value = "\n\n".join(result.messages)
            status.value = "Publish complete"
            progress.value = 1
            page.snack_bar = ft.SnackBar(ft.Text("Nuphillion publish completed."), open=True)
        except Exception as exc:
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
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
        padding=ft.padding.symmetric(horizontal=22, vertical=16),
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Nuphillion Publisher", size=24, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text("Build launcher-ready ZIP assets, commit them cleanly, and keep LFS handled.", size=12, color="white70"),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.ElevatedButton("Publish", icon=ft.icons.ROCKET_LAUNCH, on_click=publish_clicked, bgcolor="#2b73e0", color="white"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    )

    settings = ft.Container(
        bgcolor=CARD_BG,
        border=ft.border.all(1, BORDER),
        border_radius=8,
        padding=18,
        content=ft.Column(
            [
                ft.Text("Paths", size=16, weight=ft.FontWeight.BOLD, color=TEAL),
                folder_row(launcher_repo, "Select NuphillionDev repo"),
                folder_row(gts_dir, "Select compiled GTS output folder"),
                folder_row(expansion_source, "Select loose expansion source folder"),
                ft.Divider(height=18, color=BORDER),
                ft.Text("Publish Toggles", size=16, weight=ft.FontWeight.BOLD, color=TEAL),
                ft.Row([refresh_patch, refresh_expansion], spacing=24),
                ft.Row([ensure_lfs, commit_changes, push_changes], spacing=24),
                commit_message,
            ],
            spacing=10,
        ),
    )

    log_panel = ft.Container(
        bgcolor=CARD_BG,
        border=ft.border.all(1, BORDER),
        border_radius=8,
        padding=18,
        content=ft.Column(
            [
                ft.Row([status], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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
                    padding=ft.padding.all(18),
                    expand=True,
                    content=ft.Column([settings, log_panel], scroll=ft.ScrollMode.AUTO, spacing=16),
                ),
            ],
            expand=True,
            spacing=0,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
