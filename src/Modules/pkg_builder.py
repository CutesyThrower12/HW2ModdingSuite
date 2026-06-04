"""
PKG Builder: Implements proper capack format as per KSoft.Phoenix specification.
Format:
  - Header (22 bytes minimum):
    * 6 bytes: "capack" signature
    * 8 bytes: version (ulong, 2 = UsesAlignment)
    * 8 bytes: file entry count (long)
  - File Entries (for each file):
    * 8 bytes: name length (long)
    * N bytes: name (ASCII string)
    * 8 bytes: offset (long)
    * 8 bytes: size (long)
  - Alignment (if version >= 2):
    * 8 bytes: alignment value (long, default 8)
  - File Data: binary content at specified offsets
"""

import os
import shutil
import struct
import subprocess
import sys


class CaPackageEntry:
    """Represents a single file entry in the package."""
    
    def __init__(self, name, file_path=None, offset=0, size=0):
        """
        Args:
            name: file path/name (str)
            file_path: path to the file on disk (str), if None, size must be provided
            offset: byte offset in file (int)
            size: file size in bytes (int), if 0 and file_path, will be calculated
        """
        self.name = name
        self.file_path = file_path
        self.offset = offset
        self.size = size if size > 0 else (os.path.getsize(file_path) if file_path else 0)
    
    def serialize(self):
        """Serialize entry to bytes."""
        data = b''
        # 8-byte name length
        data += struct.pack('<q', len(self.name))
        # ASCII name string
        data += self.name.encode('ascii')
        # 8-byte offset
        data += struct.pack('<q', self.offset)
        # 8-byte size
        data += struct.pack('<q', self.size)
        return data
    
    def serialized_size(self):
        """Calculate serialized size of this entry."""
        return 8 + len(self.name) + 8 + 8


class CaPackageFile:
    """PKG file builder matching KSoft.Phoenix capack format."""
    
    VERSION_ZERO = 0
    VERSION_NO_ALIGNMENT = 1
    VERSION_USES_ALIGNMENT = 2
    
    SIGNATURE = b'capack'
    CURRENT_VERSION = VERSION_USES_ALIGNMENT
    DEFAULT_ALIGNMENT = 8
    
    def __init__(self, version=None, alignment=None):
        """
        Args:
            version: CaPackageVersion enum (default: USES_ALIGNMENT)
            alignment: alignment boundary in bytes (default: 8)
        """
        self.version = version if version is not None else self.CURRENT_VERSION
        self.alignment = alignment if alignment is not None else self.DEFAULT_ALIGNMENT
        self.entries = []  # List of CaPackageEntry
    
    def add_file(self, name, data=None, file_path=None):
        """
        Add a file to the package.
        
        Args:
            name: file path/name (str)
            data: binary content (bytes), if provided
            file_path: path to file on disk, if data not provided
        """
        if data is not None:
            if isinstance(data, str):
                data = data.encode('utf-8')
            entry = CaPackageEntry(name, file_path=None, size=len(data))
            self.entries.append((entry, data))
        elif file_path is not None:
            entry = CaPackageEntry(name, file_path=file_path)
            self.entries.append((entry, None))
        else:
            raise ValueError("Either data or file_path must be provided")
    
    def build(self):
        """
        Build the complete PKG file.
        
        Returns:
            bytes: complete PKG file content
        """
        if not self.entries:
            raise ValueError("No files added to package")
        
        # 1) Calculate header + entries size
        header_size = 6 + 8 + 8  # signature + version + entry count
        
        entries_size = 0
        for entry, _ in self.entries:
            entries_size += entry.serialized_size()
        
        # 2) Calculate offset to first file (after header, entries, and alignment value)
        # If version uses alignment, add 8 bytes for alignment field
        alignment_field_size = 8 if self.version >= self.VERSION_USES_ALIGNMENT else 0
        first_file_absolute_offset = header_size + entries_size + alignment_field_size
        
        # Align first file offset if requested
        if self.version >= self.VERSION_USES_ALIGNMENT and self.alignment > 0:
            remainder = first_file_absolute_offset % self.alignment
            if remainder:
                first_file_absolute_offset += self.alignment - remainder
        
        # 3) Build the output binary
        output = b''
        
        # Header: signature
        output += self.SIGNATURE
        
        # Header: version
        output += struct.pack('<Q', self.version)
        
        # Header: entry count
        output += struct.pack('<q', len(self.entries))
        
        # File entries with RELATIVE offsets (relative to start of first file data)
        current_relative_offset = 0
        serialized_entries = []
        
        for entry, data in self.entries:
            if data is not None:
                entry.size = len(data)
            elif entry.file_path:
                entry.size = os.path.getsize(entry.file_path)
            if self.alignment > 0:
                remainder = current_relative_offset % self.alignment
                if remainder:
                    current_relative_offset += self.alignment - remainder
            entry.offset = current_relative_offset
            serialized_entries.append(entry.serialize())
            current_relative_offset += entry.size
        
        # Write all entries
        for entry_bytes in serialized_entries:
            output += entry_bytes
        
        # Alignment field (if version uses it)
        if self.version >= self.VERSION_USES_ALIGNMENT:
            output += struct.pack('<q', self.alignment)
        
        # Pad to first file offset
        while len(output) < first_file_absolute_offset:
            output += b'\x00'
        
        # Write all file data
        current_relative_offset = 0
        for entry, data in self.entries:
            if current_relative_offset < entry.offset:
                output += b'\x00' * (entry.offset - current_relative_offset)
                current_relative_offset = entry.offset
            if data is not None:
                output += data
                current_relative_offset += len(data)
            elif entry.file_path:
                with open(entry.file_path, 'rb') as f:
                    chunk = f.read()
                    output += chunk
                    current_relative_offset += len(chunk)
        
        return output
    
    def build_to_file(self, output_path):
        """
        Build the PKG file directly to disk without loading all data into memory.
        
        Args:
            output_path: path to output .pkg file (str)
        """
        if not self.entries:
            raise ValueError("No files added to package")
        
        # 1) Calculate header + entries size
        header_size = 6 + 8 + 8  # signature + version + entry count
        
        entries_size = 0
        for entry, _ in self.entries:
            entries_size += entry.serialized_size()
        
        # 2) Calculate offset to first file (after header, entries, and alignment value)
        alignment_field_size = 8 if self.version >= self.VERSION_USES_ALIGNMENT else 0
        first_file_absolute_offset = header_size + entries_size + alignment_field_size
        
        # Align first file offset if requested
        if self.version >= self.VERSION_USES_ALIGNMENT and self.alignment > 0:
            remainder = first_file_absolute_offset % self.alignment
            if remainder:
                first_file_absolute_offset += self.alignment - remainder
        
        # 3) Calculate total file size
        total_size = first_file_absolute_offset
        current_relative_offset = 0
        for entry, _ in self.entries:
            if self.alignment > 0:
                remainder = current_relative_offset % self.alignment
                if remainder:
                    current_relative_offset += self.alignment - remainder
            current_relative_offset += entry.size
        total_size += current_relative_offset
        
        # 4) Create and pre-allocate output file
        with open(output_path, 'wb') as out_f:
            out_f.truncate(total_size)
        
        # 5) Memory-map the output file
        import mmap
        with open(output_path, 'r+b') as out_f:
            mm_out = mmap.mmap(out_f.fileno(), total_size)
            try:
                # 6) Write header
                pos = 0
                mm_out[pos:pos+6] = self.SIGNATURE
                pos += 6
                mm_out[pos:pos+8] = struct.pack('<Q', self.version)
                pos += 8
                mm_out[pos:pos+8] = struct.pack('<q', len(self.entries))
                pos += 8
                
                # 7) Prepare entries with offsets
                current_relative_offset = 0
                for entry, data in self.entries:
                    if data is not None:
                        entry.size = len(data)
                    elif entry.file_path:
                        entry.size = os.path.getsize(entry.file_path)
                    if self.alignment > 0:
                        remainder = current_relative_offset % self.alignment
                        if remainder:
                            current_relative_offset += self.alignment - remainder
                    entry.offset = current_relative_offset
                    current_relative_offset += entry.size
                
                # 8) Write entries
                for entry, _ in self.entries:
                    entry_bytes = entry.serialize()
                    mm_out[pos:pos+len(entry_bytes)] = entry_bytes
                    pos += len(entry_bytes)
                
                # 9) Write alignment field
                if self.version >= self.VERSION_USES_ALIGNMENT:
                    mm_out[pos:pos+8] = struct.pack('<q', self.alignment)
                    pos += 8
                
                # 10) Pad to first file offset (already zeroed by truncate)
                pos = first_file_absolute_offset
                
                # 11) Write file data
                for entry, data in self.entries:
                    pos = first_file_absolute_offset + entry.offset
                    if data is not None:
                        mm_out[pos:pos+len(data)] = data
                    elif entry.file_path:
                        with open(entry.file_path, 'rb') as in_f:
                            mm_in = mmap.mmap(in_f.fileno(), 0, access=mmap.ACCESS_READ)
                            try:
                                mm_out[pos:pos+entry.size] = mm_in[:entry.size]
                            finally:
                                mm_in.close()
            finally:
                mm_out.close()
    
    @staticmethod
    def parse(data):
        """
        Parse an existing PKG file.
        
        Args:
            data: binary content (bytes)
        
        Returns:
            tuple: (CaPackageFile instance, dict of {filename: binary data})
        """
        offset = 0
        
        # Parse signature
        sig = data[offset:offset+6]
        if sig != CaPackageFile.SIGNATURE:
            raise ValueError(f"Invalid PKG signature: {sig}")
        offset += 6
        
        # Parse version
        version = struct.unpack('<Q', data[offset:offset+8])[0]
        offset += 8
        
        if version < CaPackageFile.VERSION_ZERO or version > CaPackageFile.CURRENT_VERSION:
            raise ValueError(f"Unsupported PKG version: {version}")
        
        # Parse entry count
        entry_count = struct.unpack('<q', data[offset:offset+8])[0]
        offset += 8
        
        pkg = CaPackageFile(version=version)
        entries = []
        
        # Parse entries
        for _ in range(entry_count):
            # Name length
            name_len = struct.unpack('<q', data[offset:offset+8])[0]
            offset += 8
            
            # Name
            name = data[offset:offset+name_len].decode('ascii')
            offset += name_len
            
            # Offset (relative to first file data)
            file_offset = struct.unpack('<q', data[offset:offset+8])[0]
            offset += 8
            
            # Size
            file_size = struct.unpack('<q', data[offset:offset+8])[0]
            offset += 8
            
            entries.append((name, file_offset, file_size))
        
        # Parse alignment (if version uses it)
        if version >= CaPackageFile.VERSION_USES_ALIGNMENT:
            pkg.alignment = struct.unpack('<q', data[offset:offset+8])[0]
            offset += 8
        
        if version >= CaPackageFile.VERSION_USES_ALIGNMENT and pkg.alignment > 0:
            remainder = offset % pkg.alignment
            if remainder:
                offset += pkg.alignment - remainder

        # offset now points to start of file data section
        first_file_data_offset = offset

        # Extract file data using relative offsets
        files = {}
        for name, rel_offset, file_size in entries:
            abs_offset = first_file_data_offset + rel_offset
            file_data = data[abs_offset:abs_offset + file_size]
            files[name] = file_data
        
        return pkg, files


def _project_root_candidates():
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(sys._MEIPASS)
    here = os.path.abspath(os.path.dirname(__file__))
    candidates.append(os.path.abspath(os.path.join(here, "..", "..")))
    candidates.append(os.getcwd())
    return candidates


def _find_fast_packager():
    exe_name = "hw2pkg.exe" if os.name == "nt" else "hw2pkg"
    for root in _project_root_candidates():
        candidate = os.path.join(root, "tools", "HW2Packager", exe_name)
        if os.path.exists(candidate):
            return candidate
        candidate = os.path.join(root, "tools", "HW2Packager", "target", "release", exe_name)
        if os.path.exists(candidate):
            return candidate
    return None


def _build_with_fast_packager(source_dir, output_path, embed_streaming_videos=False, include_loose_xml=False):
    packager = _find_fast_packager()
    if not packager:
        return False

    creationflags = 0
    startupinfo = None
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        except Exception:
            startupinfo = None

    command = [packager, "package", source_dir, "-o", output_path]
    if embed_streaming_videos:
        command.append("--embed-streaming-videos")
    if include_loose_xml:
        command.append("--include-loose-xml")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        creationflags=creationflags,
        startupinfo=startupinfo,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "Fast packager failed").strip()
        raise RuntimeError(message)
    message = (result.stderr or result.stdout).strip()
    if message:
        print(message)
    return os.path.exists(output_path)


def _normalize_manifest_path(value):
    value = value.strip().lstrip("\ufeff")
    if not value or value.startswith("#") or value.startswith("//"):
        return None
    if value.lower() == "v2":
        return None
    normalized = value.lstrip("\\/").replace("/", "\\").lower()
    return normalized or None


def _manifest_filter(source_dir):
    manifest_path = os.path.join(source_dir, "file_manifest.txt")
    if not os.path.isfile(manifest_path):
        return None

    allowed = set()
    with open(manifest_path, "r", encoding="utf-8-sig", errors="replace") as manifest:
        for line in manifest:
            normalized = _normalize_manifest_path(line)
            if normalized:
                allowed.add(normalized)
                allowed.add("data\\" + normalized)
                if normalized.endswith((".xml", ".pfx", ".tactics")):
                    compiled = normalized + ".xmb"
                    allowed.add(compiled)
                    allowed.add("data\\" + compiled)
    return allowed


def _package_source_root(source_dir, allowed_paths=None):
    return source_dir


def _is_streaming_video(path):
    return os.path.splitext(path)[1].lower() in (".bk2", ".bik")


def _loose_output_root(output_path):
    folder = os.path.splitext(os.path.basename(output_path))[0] + "_loose"
    return os.path.join(os.path.dirname(output_path) or ".", folder)


def _copy_streaming_sidecars(output_path, streaming_files):
    if not streaming_files:
        return None

    loose_root = _loose_output_root(output_path)
    for full_path, rel_path in streaming_files:
        destination = os.path.join(loose_root, *rel_path.replace("/", "\\").split("\\"))
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(full_path, destination)
    return loose_root


def _is_loose_editable_xml(path):
    return os.path.splitext(path)[1].lower() == ".xml"


def _should_package_relpath(rel_path, full_path=None, allowed_paths=None, include_loose_xml=False):
    normalized = rel_path.replace("/", "\\").lower()
    if not include_loose_xml and full_path and _is_loose_editable_xml(full_path):
        return False
    if allowed_paths is not None:
        return normalized in allowed_paths
    if normalized == "file_manifest.txt":
        return False
    if (
        normalized == "data.pkg"
        or normalized == "workspace.code-workspace"
        or normalized.endswith(".code-workspace")
        or normalized.startswith("_tmp")
    ):
        return False
    return normalized.startswith("data\\")


def build_pkg_from_directory(
    source_dir,
    output_path,
    progress_callback=None,
    prefer_fast_packager=True,
    embed_streaming_videos=False,
    include_loose_xml=False,
):
    """
    Build a PKG file from a directory recursively.
    
    Args:
        source_dir: root directory to package (str)
        output_path: destination .pkg file (str)
        progress_callback: optional callable(current, total) for progress updates
    
    Returns:
        bool: True if successful
    """
    try:
        if prefer_fast_packager:
            try:
                ok = _build_with_fast_packager(
                    source_dir,
                    output_path,
                    embed_streaming_videos=embed_streaming_videos,
                    include_loose_xml=include_loose_xml,
                )
                if ok:
                    if progress_callback:
                        progress_callback(1, 1)
                    return True
            except Exception as ex:
                print(f"Fast packager unavailable; falling back to Python packager: {ex}")

        allowed_paths = _manifest_filter(source_dir)
        package_root = _package_source_root(source_dir, allowed_paths)

        # Collect all files
        files = []
        streaming_files = []
        for root, dirs, filenames in os.walk(package_root):
            for fn in filenames:
                full_path = os.path.join(root, fn)
                rel_path = os.path.relpath(full_path, package_root)
                if not _should_package_relpath(
                    rel_path,
                    full_path=full_path,
                    allowed_paths=allowed_paths,
                    include_loose_xml=include_loose_xml,
                ):
                    continue
                if _is_streaming_video(full_path) and not embed_streaming_videos:
                    streaming_files.append((full_path, rel_path))
                    continue
                files.append((full_path, rel_path))
        
        loose_root = _copy_streaming_sidecars(output_path, streaming_files)
        if loose_root:
            print(
                f"Wrote {len(streaming_files)} loose streaming video file(s) to {loose_root}. "
                "Deploy these loose files with the package; Halo Wars 2 crashes when frontend videos are embedded in capack."
            )

        if not files:
            raise ValueError("No files found in directory")

        files.sort(key=lambda item: ("\\" + item[1].replace("/", "\\")).lower())
        
        # Create package
        pkg = CaPackageFile()
        
        for i, (full_path, rel_path) in enumerate(files, 1):
            # Use backslashes in package names and add leading backslash
            pkg_name = '\\' + rel_path.replace('/', '\\')
            pkg.add_file(pkg_name, file_path=full_path)
            
            if progress_callback:
                try:
                    progress_callback(i, len(files))
                except Exception:
                    pass
        
        # Build and write directly to file
        pkg.build_to_file(output_path)
        
        return True
    
    except Exception as e:
        print(f"Error building PKG: {e}")
        return False
