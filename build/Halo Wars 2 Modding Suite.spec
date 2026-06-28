# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Bundle flet_desktop package files + its DLLs/binaries
fd_datas = collect_data_files("flet_desktop")
fd_bins = collect_dynamic_libs("flet_desktop")

a = Analysis(
    ['src\\mod_tool.py'],
    pathex=['src'],
    binaries=fd_bins,
    datas=[
        ('assets\\background.png', 'assets'),
        ('assets\\icon.ico', 'assets'),
        ('assets\\intro.mp4', 'assets'),
        ('src\\Modules\\Library', 'Modules\\Library'),
        ('src\\Modules', 'Modules'),
        ('src\\pfx_editor_pyside.py', '.'),
        ('src\\player_colors_pyside.py', '.'),
        ('src\\triggerscript_editor.py', '.'),
        ('src\\triggerscript_parser.py', '.'),
        ('tools', 'tools'),
    ] + fd_datas,
    hiddenimports=[
        'flet_desktop',
        'pfx_editor_pyside',
        'player_colors_pyside',
        'triggerscript_editor',
        'triggerscript_parser',
        'hw2_ai_editor.main',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtDesigner',
    ],
    noarchive=False,
    optimize=2,  # release
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Halo Wars 2 Modding Suite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,       # faster local builds; larger exe is worth the iteration speed
    console=False,   # no console window
    icon='assets\\icon.ico',
    version='build\\version_info.txt',
)
