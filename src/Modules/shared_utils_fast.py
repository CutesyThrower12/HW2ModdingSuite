import os
import zlib


def safe_set_clipboard(page, text):
    """Set clipboard robustly across Flet versions.
    Prefer `page.set_clipboard()` when present, otherwise set `page.clipboard`.
    """
    try:
        if hasattr(page, "set_clipboard") and callable(page.set_clipboard):
            page.set_clipboard(text)
            return True
    except Exception:
        pass
    try:
        page.clipboard = text
        return True
    except Exception:
        return False


# Table-based CRC32 implementation (polynomial 0x04C11DB7, reflected/standard CRC-32)
_crc32_table = None


def _get_crc32_table():
    global _crc32_table
    if _crc32_table is None:
        poly = 0xEDB88320  # reversed 0x04C11DB7
        table = []
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
            table.append(crc & 0xFFFFFFFF)
        _crc32_table = table
    return _crc32_table


def crc32_bytes(data: bytes) -> int:
    """Compute CRC-32 (returns integer).

    Uses standard reflected CRC-32 (initial 0xFFFFFFFF, final XOR 0xFFFFFFFF)
    matching common online calculators that use polynomial 0x04C11DB7.
    For short buffers we use a table-driven pure-Python implementation
    that avoids importing zlib in callers that only need the table-based API.
    """
    table = _get_crc32_table()
    crc = 0xFFFFFFFF
    for b in data:
        crc = (crc >> 8) ^ table[(crc ^ b) & 0xFF]
    return crc ^ 0xFFFFFFFF


def crc32_hex(data: bytes) -> str:
    """Return CRC-32 as 8-digit uppercase hex string."""
    return f"{crc32_bytes(data):08X}"


def crc32_file_fast(path: str, progress_callback=None, chunk_size: int = 64 * 1024 * 1024) -> int:
    """Compute CRC-32 for a file using fast C-backed zlib.

    Strategy:
    - Try an `mmap`-based path first (no extra copies; zlib operates on the buffer
      in C) which is usually the fastest on modern OSes.
    - Fall back to large-buffer chunked reads using `zlib.crc32` with a large
      default chunk size (64 MiB) to minimise Python loop overhead.

    If `progress_callback` is provided it will be called as
    `progress_callback(processed_bytes, total_bytes)` from the worker thread
    to allow a UI to update a progress bar. Returns the CRC as an unsigned
    32-bit integer.
    """
    total = 0
    try:
        total = os.path.getsize(path)
    except Exception:
        total = 0

    # Try mmap path first for maximum speed (no copies)
    try:
        import mmap
        with open(path, "rb") as f:
            try:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            except (ValueError, OSError):
                mm = None
            if mm is not None:
                try:
                    if progress_callback:
                        try:
                            progress_callback(0, total)
                        except Exception:
                            pass
                    # zlib.crc32 accepts any object supporting the buffer protocol
                    crc = zlib.crc32(mm) & 0xFFFFFFFF
                    if progress_callback:
                        try:
                            progress_callback(total, total)
                        except Exception:
                            pass
                    return crc
                finally:
                    try:
                        mm.close()
                    except Exception:
                        pass
    except Exception:
        # mmap may not be available or mapping may fail; fall back
        pass

    # Fallback: chunked reads with a large chunk size to reduce Python overhead
    crc = 0
    processed = 0
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            crc = zlib.crc32(chunk, crc)
            processed += len(chunk)
            if progress_callback:
                try:
                    progress_callback(processed, total)
                except Exception:
                    pass

    return crc & 0xFFFFFFFF
