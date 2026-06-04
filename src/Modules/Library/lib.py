import json
import os
import sys
from functools import lru_cache

def resource_path(relative_path):
    """
    Get absolute path to resource, works in dev (script) and EXE
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = os.path.join(sys._MEIPASS, "Modules", "Library")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

@lru_cache(maxsize=None)
def load_library(filename: str):
    """
    Automatically prepends the folder and resolves the EXE path
    """
    path = resource_path(filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
