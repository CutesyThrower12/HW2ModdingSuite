# Halo Wars 2 Modding Suite

A collection of tools and workflows for Halo Wars 2 modding, including guided builders, package utilities, asset conversion helpers, player-color editing, and a particle color editor.

## Overview

The suite is built to help modders create custom units, squads, UI entries, entities, tech logic, leader powers, minimap data, player colors, and packaged mod outputs. It includes a graphical interface for common workflows plus utility code for package building and file conversion.

Key features include:
- Guided workflows for common Halo Wars 2 mod data
- Package building utilities for `.pkg` output
- XMB/XML conversion workflows through bundled tools
- Player color and particle color editing
- CRC32 and support utilities for validation
- Tactics-system research in `All_Tactics_Summary`

## Installation

### Prerequisites

- Python 3.8 or higher
- Required Python packages: `flet`, `flet-video`, `flet-desktop`, `PySide6`

### Building The Application

1. Clone or download this repository.
2. Run `build.bat`.
3. The built application is copied to `dist/`.

### Running From Source

```bash
pip install flet flet-video flet-desktop PySide6
python src/mod_tool.py
```

## Project Layout

- `src/` - Python source files and the `Modules` package
- `assets/` - images, icon, and intro video used by the app
- `tools/` - bundled external utilities such as Phoenix and Ancilla
- `scripts/` - build helper scripts
- `build/` - PyInstaller spec and build cache area
- `dist/` - compiled executable output, ignored by Git
- `All_Tactics_Summary` - tactics-system analysis from the GitHub repo history
- `unecessary/` - local review folder for temp/cache/helper files, ignored by Git

## Main GUI

Launch `src/mod_tool.py` or the built executable in `dist/`.

### Workflows

- Unit Builder
- Squad Builder
- UIENT Builder
- Entity Builder
- Minimap & Decals
- Techs Logic
- Leader Powers
- Player Colors
- Packager

### Tools

- DDS/DDX conversion helpers
- Ancilla XML-to-XMB conversion
- Phoenix XMB/XML and ERA tooling
- PKG Builder
- Particle Editor
- CRC32 Calculator

## Command-Line Usage

Package builder example:

```bat
set PYTHONPATH=src
python -c "from Modules.pkg_builder import build_pkg_from_directory; build_pkg_from_directory('input_folder', 'output.pkg')"
```

Basic command-line unit/object helper:

```bash
python src/main.py
```

Older package-analysis, comparison, profiling, and test helper scripts were moved to `unecessary/test_helpers/` during local cleanup. They are kept there for review before deletion and are not tracked by Git.

## Supported File Formats

- `.pkg` - Halo Wars 2 package files
- `.xmb` / `.xml` - binary/editable game data files
- `.era` - archive files for game assets
- `.ecf` - chunk files for materials and effects
- `.dds` / `.ddx` - texture formats
- `.vis` - visual asset files
- `.pfx` - particle effect XML files

## License

This project is provided as-is for the Halo Wars 2 modding community. Please respect the game's terms of service and use mods responsibly.

## Credits

- Created by CutesyThrower12
- Built with Flet and PySide6
- Incorporates community tools like Phoenix and Ancilla
- Thanks to the Halo Wars Modding Group Discord for testing and feedback

## Disclaimer

Use these tools at your own risk. Always back up your game files before changing them. Modding may violate game terms of service, so proceed responsibly.
