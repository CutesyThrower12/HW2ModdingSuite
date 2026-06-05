from __future__ import annotations

import os
import json
import re
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree


DEFAULT_LAUNCHER_REPO = Path(r"C:\Users\Admin\Downloads\Git\NuphillionDev")
DEFAULT_EXPANSION_SOURCE = Path(r"C:\Users\Admin\Downloads\Nuphillion\Workspace\nuphillionExpansion")
DEFAULT_RELEASE_DOWNLOAD_DIR = Path.home() / "Downloads" / "NuphillionReleases"
GTS_RELATIVE = Path("Packages") / "Microsoft.HoganThreshold_8wekyb3d8bbwe" / "LocalState" / "GTS" / "1_11_2931_2_active"
MANIFEST_NAME = "1_11_2931_2_file_manifest.xml"
LAUNCHER_PKG_NAME = "nuphillionCode.pkg"
GH_CANDIDATES = [
    Path(r"C:\Program Files\GitHub CLI\gh.exe"),
    Path(r"C:\Program Files (x86)\GitHub CLI\gh.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "GitHub CLI" / "gh.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "GitHub CLI" / "gh.exe",
]
CI_WORKFLOW = """name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    runs-on: windows-latest
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          lfs: true

      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: "10.0.x"
          cache: true
          cache-dependency-path: "**/*.csproj"

      - name: Restore dependencies
        run: dotnet restore NuphillionManager.sln --locked-mode false

      - name: Build
        run: dotnet build NuphillionManager.sln -c Release --no-restore
"""
RELEASE_WORKFLOW = """name: Release

on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Release tag. Leave blank to auto-generate vYYYY.MM.DD."
        required: false
        type: string

permissions:
  contents: write

concurrency:
  group: release
  cancel-in-progress: false

jobs:
  release:
    runs-on: windows-latest
    timeout-minutes: 45

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          lfs: true

      - name: Generate tag
        id: tag
        shell: pwsh
        run: |
          if ("${{ inputs.tag }}" -ne "") {
            $tag = "${{ inputs.tag }}"
            echo "tag=$tag" >> $env:GITHUB_OUTPUT
            echo "Using requested tag: $tag"
            exit 0
          }

          $date = Get-Date -Format "yyyy.MM.dd"
          $baseTag = "v$date"
          $counter = 0
          $tag = $baseTag

          while (git tag -l $tag) {
            $counter++
            $tag = "$baseTag.$counter"
          }

          echo "tag=$tag" >> $env:GITHUB_OUTPUT
          echo "Generated tag: $tag"

      - name: Create and push tag
        shell: pwsh
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag ${{ steps.tag.outputs.tag }}
          git push origin ${{ steps.tag.outputs.tag }}

      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: "10.0.x"
          cache: true
          cache-dependency-path: "**/*.csproj"

      - name: Restore dependencies
        run: dotnet restore NuphillionManager.sln --locked-mode false

      - name: Build
        run: dotnet build NuphillionManager/NuphillionManager.csproj -c Release -r win-x64 --self-contained true --no-restore

      - name: Publish self-contained
        run: >
          dotnet publish NuphillionManager/NuphillionManager.csproj
          -c Release
          -r win-x64
          --self-contained true
          --no-restore
          --no-build
          -o artifacts/publish

      - name: Create zip
        shell: pwsh
        run: |
          $zip = "NuphillionManager-${{ steps.tag.outputs.tag }}.zip"
          Compress-Archive -Path artifacts/publish/* -DestinationPath $zip -CompressionLevel Optimal
          echo "zip=$zip" >> $env:GITHUB_ENV

      - name: Upload workflow artifact
        uses: actions/upload-artifact@v4
        with:
          name: NuphillionManager-${{ steps.tag.outputs.tag }}
          path: ${{ env.zip }}
          if-no-files-found: error

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.tag.outputs.tag }}
          files: ${{ env.zip }}
          generate_release_notes: true
"""


@dataclass
class PublishOptions:
    launcher_repo: Path
    gts_dir: Path
    expansion_source: Path
    refresh_modded_patch: bool = True
    refresh_expansion: bool = False
    ensure_lfs: bool = True
    commit_changes: bool = True
    push_changes: bool = False
    commit_message: str = "Publish Nuphillion mod assets"
    initialize_release_workflow: bool = False
    run_release_workflow: bool = False
    download_release_zip: bool = False
    release_download_dir: Path = DEFAULT_RELEASE_DOWNLOAD_DIR


@dataclass
class PublishResult:
    messages: list[str]
    changed_files: list[str]
    commit_hash: str | None = None


ProgressCallback = Callable[[str], None] | None


def _emit(messages: list[str], text: str, progress: ProgressCallback = None) -> None:
    messages.append(text)
    if progress:
        progress(text)


def default_gts_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", "")) / GTS_RELATIVE


def _latest_file(paths, label: str) -> Path:
    candidates = [Path(path) for path in paths if Path(path).is_file()]
    if not candidates:
        raise FileNotFoundError(f"Could not find {label}.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def find_latest_compiled_output(gts_dir: Path) -> tuple[Path, Path]:
    if not gts_dir.is_dir():
        raise FileNotFoundError(f"GTS folder does not exist: {gts_dir}")
    manifest = _latest_file(gts_dir.glob("*file_manifest*.xml"), "a compiled file manifest in the GTS folder")
    pkg = _latest_file(gts_dir.glob("*.pkg"), "a compiled .pkg in the GTS folder")
    return manifest, pkg


def _rewrite_manifest_for_launcher(manifest_path: Path, pkg_path: Path) -> bytes:
    text = manifest_path.read_text(encoding="utf-8-sig")
    try:
        root = ElementTree.fromstring(text)
        for file_node in root.findall(".//file"):
            if file_node.get("new", "").lower().endswith(".pkg"):
                file_node.set("new", LAUNCHER_PKG_NAME)
            if file_node.get("old", "").lower().endswith(".pkg"):
                file_node.set("old", LAUNCHER_PKG_NAME)
            file_node.set("size", str(pkg_path.stat().st_size))
            file_node.set("time", str(int(pkg_path.stat().st_mtime)))
        return ElementTree.tostring(root, encoding="utf-8", xml_declaration=False)
    except Exception:
        text = re.sub(r'(new|old)="[^"]+\.pkg"', lambda m: f'{m.group(1)}="{LAUNCHER_PKG_NAME}"', text)
        text = re.sub(r'size="\d+"', f'size="{pkg_path.stat().st_size}"', text)
        text = re.sub(r'time="\d+"', f'time="{int(pkg_path.stat().st_mtime)}"', text)
        return text.encode("utf-8")


def _write_zip_entry_from_file(zip_file: zipfile.ZipFile, source: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname.replace("\\", "/"), time.localtime(source.stat().st_mtime)[:6])
    info.compress_type = zipfile.ZIP_DEFLATED
    with source.open("rb") as handle:
        zip_file.writestr(info, handle.read())


def build_modded_patch_zip(manifest_path: Path, pkg_path: Path, output_zip: Path, progress: ProgressCallback = None) -> None:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if progress:
        progress("Preparing launcher manifest...")
    manifest_bytes = _rewrite_manifest_for_launcher(manifest_path, pkg_path)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr(MANIFEST_NAME, manifest_bytes)
        if progress:
            progress(f"Compressing {LAUNCHER_PKG_NAME}...")
        _write_zip_entry_from_file(archive, pkg_path, LAUNCHER_PKG_NAME)


def build_expansion_zip(source_dir: Path, output_zip: Path, progress: ProgressCallback = None) -> None:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Expansion source folder does not exist: {source_dir}")

    files = [path for path in source_dir.rglob("*") if path.is_file()]
    if not files:
        raise FileNotFoundError(f"No expansion files found in {source_dir}")

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        sorted_files = sorted(files, key=lambda item: str(item.relative_to(source_dir)).lower())
        total = len(sorted_files)
        for index, path in enumerate(sorted_files, start=1):
            if progress:
                rel = str(path.relative_to(source_dir)).replace("\\", "/")
                progress(f"Compressing expansion file {index}/{total}: {rel}")
            _write_zip_entry_from_file(archive, path, str(path.relative_to(source_dir)))


def _run_command(
    repo: Path,
    command: list[str],
    messages: list[str],
    check: bool = True,
    progress: ProgressCallback = None,
) -> subprocess.CompletedProcess:
    command = _resolve_command(command)
    if progress:
        progress(f"Running: {' '.join(command)}")
    try:
        completed = subprocess.run(command, cwd=repo, text=True, capture_output=True)
    except FileNotFoundError as exc:
        if command and command[0].lower() == "gh":
            raise RuntimeError("GitHub CLI is required for release automation. Install gh, then run 'gh auth login'.") from exc
        raise
    detail = (completed.stdout + completed.stderr).strip()
    if detail:
        _emit(messages, detail, progress)
    if check and completed.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed with exit code {completed.returncode}")
    return completed


def _resolve_command(command: list[str]) -> list[str]:
    if not command:
        return command
    if command[0].lower() != "gh":
        return command
    for candidate in GH_CANDIDATES:
        if candidate.is_file():
            return [str(candidate), *command[1:]]
    return command


def _run_git(repo: Path, args: list[str], messages: list[str], check: bool = True, progress: ProgressCallback = None) -> subprocess.CompletedProcess:
    return _run_command(repo, ["git", *args], messages, check, progress)


def _current_branch(repo: Path, messages: list[str], progress: ProgressCallback = None) -> str:
    completed = _run_git(repo, ["branch", "--show-current"], messages, progress=progress)
    branch = completed.stdout.strip()
    if not branch:
        raise RuntimeError("Launcher repo is in detached HEAD state; cannot push automatically.")
    return branch


def _git_changed_assets(repo: Path) -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "Assets/moddedPatch.zip",
            "Assets/nuphillionExpansion.zip",
            ".gitattributes",
            ".github/workflows/ci.yml",
            ".github/workflows/release.yml",
            "NuphillionManager/NuphillionManager.csproj",
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    return [line[3:].strip() for line in completed.stdout.splitlines() if line.strip()]


def _repo_slug(repo: Path, messages: list[str], progress: ProgressCallback = None) -> str:
    completed = _run_git(repo, ["remote", "get-url", "origin"], messages, progress=progress)
    remote = completed.stdout.strip()
    match = re.search(r"github\.com[:/](?P<slug>[^/]+/[^/.]+)(?:\.git)?$", remote)
    if not match:
        raise RuntimeError(f"Could not infer GitHub repo from origin URL: {remote}")
    return match.group("slug")


def initialize_release_files(repo: Path, messages: list[str], progress: ProgressCallback = None) -> None:
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "ci.yml").write_text(CI_WORKFLOW, encoding="utf-8", newline="\n")
    (workflows / "release.yml").write_text(RELEASE_WORKFLOW, encoding="utf-8", newline="\n")
    csproj = repo / "NuphillionManager" / "NuphillionManager.csproj"
    if csproj.exists():
        text = csproj.read_text(encoding="utf-8-sig")
        text = re.sub(r"\r?\n\s*<LangVersion>default</LangVersion>(?=\r?\n\s*</PropertyGroup>)", "", text, count=1)
        csproj.write_text(text, encoding="utf-8", newline="\n")
    _emit(messages, "Initialized optimized CI and Release workflow files.", progress)


def _ensure_gh(repo: Path, messages: list[str], progress: ProgressCallback = None) -> None:
    _run_command(repo, ["gh", "--version"], messages, progress=progress)
    try:
        _run_command(repo, ["gh", "auth", "status"], messages, progress=progress)
    except RuntimeError as exc:
        raise RuntimeError("GitHub CLI is installed, but it is not authenticated. Run 'gh auth login' and try again.") from exc


def run_release_workflow(repo: Path, messages: list[str], progress: ProgressCallback = None) -> int:
    _ensure_gh(repo, messages, progress)
    slug = _repo_slug(repo, messages, progress)
    branch = _current_branch(repo, messages, progress)
    trigger_time = time.time()
    _run_command(repo, ["gh", "workflow", "run", "release.yml", "--repo", slug, "--ref", branch], messages, progress=progress)
    _emit(messages, "Release workflow queued; waiting for GitHub Actions run...", progress)

    run_id: int | None = None
    for _ in range(24):
        time.sleep(5)
        completed = subprocess.run(
            _resolve_command(["gh", "run", "list", "--repo", slug, "--workflow", "release.yml", "--branch", branch, "--limit", "5", "--json", "databaseId,createdAt,status"]),
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            continue
        runs = json.loads(completed.stdout or "[]")
        for run in runs:
            created_at = run.get("createdAt", "")
            try:
                created_seconds = time.mktime(time.strptime(created_at[:19], "%Y-%m-%dT%H:%M:%S"))
            except Exception:
                created_seconds = trigger_time
            if created_seconds >= trigger_time - 30:
                run_id = int(run["databaseId"])
                break
        if run_id:
            break

    if not run_id:
        raise RuntimeError("Release workflow was queued, but the new run could not be found.")

    _emit(messages, f"Watching release workflow run {run_id}...", progress)
    _run_command(repo, ["gh", "run", "watch", str(run_id), "--repo", slug, "--exit-status"], messages, progress=progress)
    _emit(messages, f"Release workflow completed: run {run_id}", progress)
    return run_id


def download_latest_release_zip(repo: Path, output_dir: Path, messages: list[str], progress: ProgressCallback = None) -> None:
    _ensure_gh(repo, messages, progress)
    slug = _repo_slug(repo, messages, progress)
    output_dir.mkdir(parents=True, exist_ok=True)
    _run_command(
        repo,
        ["gh", "release", "download", "--repo", slug, "--pattern", "NuphillionManager-*.zip", "--dir", str(output_dir), "--clobber"],
        messages,
        progress=progress,
    )
    _emit(messages, f"Downloaded latest release ZIP to {output_dir}.", progress)


def ensure_git_lfs(repo: Path, messages: list[str], progress: ProgressCallback = None) -> None:
    _run_git(repo, ["lfs", "install", "--local"], messages, progress=progress)
    attributes = repo / ".gitattributes"
    wanted = "*.zip filter=lfs diff=lfs merge=lfs -text"
    existing = attributes.read_text(encoding="utf-8") if attributes.exists() else ""
    if wanted not in existing:
        with attributes.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(wanted + "\n")
        _emit(messages, "Updated .gitattributes so ZIP assets use Git LFS.", progress)
    else:
        _emit(messages, "Git LFS tracking for ZIP assets is already configured.", progress)


def commit_and_push(repo: Path, options: PublishOptions, messages: list[str], progress: ProgressCallback = None) -> tuple[list[str], str | None]:
    changed = _git_changed_assets(repo)
    if not changed:
        _emit(messages, "No launcher asset changes detected; commit skipped.", progress)
        return [], None

    stage_paths = [
        "Assets/moddedPatch.zip",
        "Assets/nuphillionExpansion.zip",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        "NuphillionManager/NuphillionManager.csproj",
    ]
    if (repo / ".gitattributes").exists():
        stage_paths.insert(0, ".gitattributes")
    stage_paths = [path for path in stage_paths if (repo / path).exists()]
    _run_git(repo, ["add", *stage_paths], messages, progress=progress)
    _run_git(repo, ["commit", "-m", options.commit_message], messages, progress=progress)
    commit_hash = _run_git(repo, ["rev-parse", "--short", "HEAD"], messages, progress=progress).stdout.strip()
    _emit(messages, f"Committed launcher asset update: {commit_hash}", progress)

    if options.push_changes:
        branch = _current_branch(repo, messages, progress)
        _run_git(repo, ["lfs", "push", "origin", branch], messages, progress=progress)
        _run_git(repo, ["push", "origin", branch], messages, progress=progress)
        _emit(messages, f"Pushed launcher repo to origin/{branch}.", progress)
    else:
        _emit(messages, "Push skipped by toggle.", progress)

    return changed, commit_hash


def publish(options: PublishOptions, progress: ProgressCallback = None) -> PublishResult:
    repo = options.launcher_repo
    assets = repo / "Assets"
    if not assets.is_dir():
        raise FileNotFoundError(f"Launcher Assets folder does not exist: {assets}")

    messages: list[str] = []
    _emit(messages, f"Launcher repo: {repo}", progress)

    if options.ensure_lfs:
        ensure_git_lfs(repo, messages, progress)
    else:
        _emit(messages, "Git LFS setup skipped by toggle.", progress)

    if options.initialize_release_workflow:
        initialize_release_files(repo, messages, progress)
    else:
        _emit(messages, "Release workflow initialization skipped by toggle.", progress)

    if options.refresh_modded_patch:
        manifest, pkg = find_latest_compiled_output(options.gts_dir)
        _emit(messages, f"Using manifest: {manifest}", progress)
        _emit(messages, f"Using package: {pkg}", progress)
        build_modded_patch_zip(manifest, pkg, assets / "moddedPatch.zip", progress)
        _emit(messages, "Refreshed Assets/moddedPatch.zip.", progress)
    else:
        _emit(messages, "Skipped moddedPatch.zip by toggle.", progress)

    if options.refresh_expansion:
        build_expansion_zip(options.expansion_source, assets / "nuphillionExpansion.zip", progress)
        _emit(messages, f"Refreshed Assets/nuphillionExpansion.zip from {options.expansion_source}.", progress)
    else:
        _emit(messages, "Skipped nuphillionExpansion.zip by toggle.", progress)

    changed_files: list[str] = []
    commit_hash = None
    if options.commit_changes:
        changed_files, commit_hash = commit_and_push(repo, options, messages, progress)
    else:
        changed_files = _git_changed_assets(repo)
        _emit(messages, "Commit skipped by toggle.", progress)

    if options.run_release_workflow:
        if changed_files and not options.push_changes:
            raise RuntimeError("Release workflow requires pushed launcher changes. Enable 'Push to GitHub' or run release after pushing.")
        run_release_workflow(repo, messages, progress)
    else:
        _emit(messages, "Release workflow run skipped by toggle.", progress)

    if options.download_release_zip:
        download_latest_release_zip(repo, options.release_download_dir, messages, progress)
    else:
        _emit(messages, "Release ZIP download skipped by toggle.", progress)

    return PublishResult(messages=messages, changed_files=changed_files, commit_hash=commit_hash)
