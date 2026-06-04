"""Compatibility wrapper for CRC utilities.

This module exposes `safe_set_clipboard`, `crc32_bytes`, `crc32_hex`, and
`crc32_file_fast`. The optimized implementations live in
`Modules.shared_utils_fast`; import from there when available so the rest of
the codebase can continue importing `Modules.shared_utils` as before.
"""

try:
    # Prefer the fast, clean implementation we added.
    from Modules.shared_utils_fast import (
        safe_set_clipboard,
        crc32_bytes,
        crc32_hex,
        crc32_file_fast,
    )
except Exception:
    # Fall back to minimal local implementations if the fast module can't be
    # imported for any reason. These are small and correct but not optimized.
    import os
    import zlib

    def safe_set_clipboard(page, text):
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


    # Simple table-based CRC
    _crc32_table = None

    def _get_crc32_table():
        nonlocal_table = globals()
        global _crc32_table
        if _crc32_table is None:
            poly = 0xEDB88320
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
        table = _get_crc32_table()
        crc = 0xFFFFFFFF
        for b in data:
            crc = (crc >> 8) ^ table[(crc ^ b) & 0xFF]
        return crc ^ 0xFFFFFFFF


    def crc32_hex(data: bytes) -> str:
        return f"{crc32_bytes(data):08X}"


    def crc32_file_fast(path: str, progress_callback=None, chunk_size: int = 8 * 1024 * 1024) -> int:
        total = 0
        try:
            total = os.path.getsize(path)
        except Exception:
            total = 0
        crc = 0
        processed = 0
        with open(path, 'rb') as fh:
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
