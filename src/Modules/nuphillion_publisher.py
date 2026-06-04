import os
import re
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree


DEFAULT_LAUNCHER_REPO = Path(r"C:\Users\Admin\Downloads\Git\NuphillionDev")
GTS_RELATIVE = Path("Packages") / "Microsoft.HoganThreshold_8wekyb3d8bbwe" / "LocalState" / "GTS" / "1_11_2931_2_active"
MANIFEST_NAME = "1_11_2931_2_file_manifest.xml"
LAUNCHER_PKG_NAME = "nuphillionCode.pkg"


@dataclass
class PublishResult:
    modded_patch_zip: Path
    expansion_zip: Path | None
    manifest_source: Path
    pkg_source: Path
    expansion_source: Path | None
    messages: list[str]


def default_gts_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", "")) / GTS_RELATIVE


def _latest_file(paths, label):
    candidates = [Path(path) for path in paths if Path(path).is_file()]
    if not candidates:
        raise FileNotFoundError(f"Could not find {label}.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def find_latest_compiled_output(gts_dir: str | os.PathLike | None = None) -> tuple[Path, Path]:
    gts_path = Path(gts_dir) if gts_dir else default_gts_dir()
    if not gts_path.is_dir():
        raise FileNotFoundError(f"GTS folder does not exist: {gts_path}")

    manifest = _latest_file(gts_path.glob("*file_manifest*.xml"), "a compiled file manifest in the GTS folder")
    pkg = _latest_file(gts_path.glob("*.pkg"), "a compiled .pkg in the GTS folder")
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
        # Keep the manifest usable even if formatting is unusual.
        text = re.sub(r'(new|old)="[^"]+\.pkg"', lambda m: f'{m.group(1)}="{LAUNCHER_PKG_NAME}"', text)
        text = re.sub(r'size="\d+"', f'size="{pkg_path.stat().st_size}"', text)
        text = re.sub(r'time="\d+"', f'time="{int(pkg_path.stat().st_mtime)}"', text)
        return text.encode("utf-8")


def _write_zip_entry_from_file(zip_file: zipfile.ZipFile, source: Path, arcname: str):
    info = zipfile.ZipInfo(arcname.replace("\\", "/"), time.localtime(source.stat().st_mtime)[:6])
    info.compress_type = zipfile.ZIP_DEFLATED
    with source.open("rb") as handle:
        zip_file.writestr(info, handle.read())


def build_modded_patch_zip(manifest_path: Path, pkg_path: Path, output_zip: Path) -> None:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = _rewrite_manifest_for_launcher(manifest_path, pkg_path)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr(MANIFEST_NAME, manifest_bytes)
        _write_zip_entry_from_file(archive, pkg_path, LAUNCHER_PKG_NAME)


def _has_files(path: Path) -> bool:
    return path.is_dir() and any(child.is_file() for child in path.rglob("*"))


def find_expansion_source(
    compiled_source_dir: str | os.PathLike | None = None,
    pkg_path: str | os.PathLike | None = None,
    explicit_source: str | os.PathLike | None = None,
) -> Path | None:
    candidates: list[Path] = []
    if explicit_source:
        candidates.append(Path(explicit_source))

    if compiled_source_dir:
        source_dir = Path(compiled_source_dir)
        candidates.append(source_dir.with_name(source_dir.name + "_loose"))
        candidates.append(source_dir.parent / f"{source_dir.name}_loose")

    if pkg_path:
        pkg = Path(pkg_path)
        candidates.append(pkg.with_name(pkg.stem + "_loose"))

    candidates.extend(
        [
            Path(r"C:\Users\Admin\Downloads\Nuphillion\Workspace\nuphillionExpansion"),
            Path(r"C:\Users\Admin\Downloads\Nuphillion\Workspace\Mockup_loose"),
        ]
    )

    for candidate in candidates:
        if _has_files(candidate):
            return candidate
    return None


def build_expansion_zip(source_dir: Path, output_zip: Path) -> None:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    files = [path for path in source_dir.rglob("*") if path.is_file()]
    if not files:
        raise FileNotFoundError(f"No expansion files found in {source_dir}")

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files, key=lambda item: str(item.relative_to(source_dir)).lower()):
            rel = str(path.relative_to(source_dir)).replace("\\", "/")
            _write_zip_entry_from_file(archive, path, rel)


def publish_to_nuphillion_launcher(
    launcher_repo: str | os.PathLike = DEFAULT_LAUNCHER_REPO,
    gts_dir: str | os.PathLike | None = None,
    compiled_source_dir: str | os.PathLike | None = None,
    expansion_source: str | os.PathLike | None = None,
    rebuild_expansion: bool = True,
) -> PublishResult:
    launcher_path = Path(launcher_repo)
    assets_dir = launcher_path / "Assets"
    if not assets_dir.is_dir():
        raise FileNotFoundError(f"Launcher Assets folder does not exist: {assets_dir}")

    manifest_path, pkg_path = find_latest_compiled_output(gts_dir)
    messages = [f"Using manifest: {manifest_path}", f"Using package: {pkg_path}"]

    modded_zip = assets_dir / "moddedPatch.zip"
    build_modded_patch_zip(manifest_path, pkg_path, modded_zip)
    messages.append(f"Wrote {modded_zip}")

    expansion_zip = assets_dir / "nuphillionExpansion.zip"
    expansion_dir = None
    if rebuild_expansion:
        expansion_dir = find_expansion_source(compiled_source_dir, pkg_path, expansion_source)
        if expansion_dir:
            build_expansion_zip(expansion_dir, expansion_zip)
            messages.append(f"Wrote {expansion_zip} from {expansion_dir}")
        elif expansion_zip.exists():
            messages.append(f"No loose expansion source found; kept existing {expansion_zip}")
        else:
            raise FileNotFoundError("No expansion source found and nuphillionExpansion.zip does not already exist.")
    else:
        messages.append("Skipped nuphillionExpansion.zip rebuild.")

    return PublishResult(
        modded_patch_zip=modded_zip,
        expansion_zip=expansion_zip if expansion_zip.exists() else None,
        manifest_source=manifest_path,
        pkg_source=pkg_path,
        expansion_source=expansion_dir,
        messages=messages,
    )
