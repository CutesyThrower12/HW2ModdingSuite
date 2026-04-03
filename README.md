# Halo Wars 2 Modding Suite

A comprehensive collection of tools, scripts, and workflows designed to streamline the creation and management of mods for Halo Wars 2. This suite provides both a user-friendly graphical interface and command-line utilities to handle various aspects of modding, from asset conversion to package building.

## Overview

The Halo Wars 2 Modding Suite is built to support modders in creating custom units, squads, UI elements, entities, and more. It includes builders for different game components, converters for asset formats, and utilities for packaging and validation. Whether you're a beginner following guided workflows or an advanced modder using individual tools, this suite aims to make the modding process efficient and accessible.

Key features include:
- **Guided Workflows**: Step-by-step builders for creating custom units, squads, and other game elements
- **Asset Converters**: Tools for converting between various Halo Wars 2 file formats
- **Package Building**: Utilities to compile mod files into game-ready packages
- **Data Validation**: Tools for analyzing and comparing mod files
- **Performance Profiling**: Scripts to optimize mod building processes

## Installation

### Prerequisites
- Python 3.8 or higher
- Required Python packages (automatically installed via build script)

### Building the Application
1. Clone or download this repository
2. Run `build.bat` to build the executable using PyInstaller
3. The built application will be in the `dist` folder

### Running from Source
1. Install dependencies: `pip install flet flet-video flet-desktop`
2. Run `python mod_tool.py` to launch the GUI application

## Tools and Usage

### Main GUI Application
Launch `mod_tool.py` or the built executable to access the graphical interface with three main sections:

#### Workflows
Guided builders for creating mod components:

##### Unit Builder
Creates unit data files with stats, abilities, and properties.
```bash
# Access via GUI: Home > Workflows > Unit Builder
```
- Define unit code names, display names, and roles
- Set hitpoints, armor types, movement stats
- Configure veterancy levels and damage multipliers

##### Squad Builder
Assembles squad compositions and behaviors.
```bash
# Access via GUI: Home > Workflows > Squad Builder
```
- Define squad members and formations
- Set counters and tactics
- Configure AI behaviors

##### UIENT Builder
Generates UI string entries for in-game text.
```bash
# Access via GUI: Home > Workflows > UIENT Builder
```
- Create localized strings for unit names and descriptions
- Generate XML files for UI integration

##### Entity Builder
Creates Object definitions and links visual assets.
```bash
# Access via GUI: Home > Workflows > Entity Builder
```
- Define 3D model references and animations
- Link visual (.vis) files to game entities

##### Minimap & Decals
Configures minimap icons and battlefield decals.
```bash
# Access via GUI: Home > Workflows > Minimap & Decals
```
- Set unit icons for the minimap
- Define decal appearances

##### Techs Logic
Validates tech trees and upgrade logic.
```bash
# Access via GUI: Home > Workflows > Techs
```
- Ensure compatibility of tech requirements
- Validate upgrade paths

##### Leader Powers
Creates custom leader abilities.
```bash
# Access via GUI: Home > Workflows > Leader Powers
```
- Define power effects and cooldowns
- Set targeting and activation rules

##### Player Colors
Customizes team color schemes.
```bash
# Access via GUI: Home > Workflows > Player Colors
```
- Modify color palettes for different factions
- Preview color changes

##### Packager
Gathers outputs from other builders and creates mod packages.
```bash
# Access via GUI: Home > Workflows > Packager
```
- Compile all mod components into .pkg files
- Generate manifest files for installation

#### Tools
Quick utilities for asset preparation and conversion:

##### DDS/DDX Converter
Rename or batch-edit texture file extensions.
```bash
# Access via GUI: Home > Tools > DDS/DDX
```
- Convert between .dds and .ddx formats
- Batch process texture directories

##### Ancilla (XML to XMB)
Convert editable XML files to binary XMB format.
```bash
# Command line usage:
ancilla.exe input.xml output.xmb
```
- Prepare UI and data files for the game
- Convert mod configuration files

##### Phoenix (XMB to XML)
Convert binary XMB files back to editable XML using Phoenix GUI.
```bash
# Launch via GUI: Home > Tools > Phoenix
# Or run PhxGui.exe directly
```
- Extract and edit game data files
- Handle .ERA archive extraction and rebuilding
- Convert between XMB and XML formats

##### PKG Builder
Compile folders into Halo Wars 2 .pkg package files.
```bash
# Access via GUI: Home > Tools > PKG Builder
# Command line usage:
python -c "from Modules.pkg_builder import build_pkg_from_directory; build_pkg_from_directory('input_folder', 'output.pkg')"
```
- Create mod packages from directory structures
- Supports the capack format specification

##### PFX Color Editor
Launch the particle effects color editor.
```bash
# Access via GUI: Home > Tools > Edit Particle Colors
```
- Modify particle system colors
- Adjust visual effects

##### CRC32 Calculator
Compute CRC32 hashes for files.
```bash
# Access via GUI: Home > Tools > CRC32 Calculator
```
- Verify file integrity
- Generate checksums for mod validation

### Command-Line Scripts

#### analyze_accepted.py
Analyze the structure of .pkg files.
```bash
python analyze_accepted.py
```
- Examine file headers and entry metadata
- Debug package format issues

#### compare_pkg_files.py
Compare two .pkg files to identify differences.
```bash
python compare_pkg_files.py
```
- Diff package contents and structures
- Identify changes between mod versions

#### profile_pkg.py
Profile the performance of package building.
```bash
python profile_pkg.py
```
- Measure build times and bottlenecks
- Optimize large mod packages

#### test_pkg_builder.py
Test the package building functionality.
```bash
python test_pkg_builder.py
```
- Validate package creation with sample data
- Ensure correct file packing and offsets

#### main.py
Command-line interface for basic modding operations.
```bash
python main.py
```
- Interactive prompts for unit creation
- Library suggestions and validation

## File Formats Supported

- **.pkg**: Halo Wars 2 package files (capack format)
- **.xmb/.xml**: Binary/editable game data files
- **.era**: Archive files for game assets
- **.ecf**: Chunk files for materials and effects
- **.dds/.ddx**: Texture formats
- **.vis**: Visual asset files

## Contributing

We welcome contributions to improve the Halo Wars 2 Modding Suite! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with various mod scenarios
5. Submit a pull request with a clear description

### Development Setup
1. Install development dependencies
2. Run tests: `python -m pytest` (if tests are added)
3. Build and test the GUI application
4. Ensure compatibility with different Python versions

## License

This project is provided as-is for the Halo Wars 2 modding community. Please respect the game's terms of service and use mods responsibly.

## Credits

- Created by CutesyThrower12
- Built with Flet for the GUI interface
- Incorporates community tools like Phoenix and Ancilla
- Thanks to the Halo Wars Modding Group Discord for testing and feedback

## Disclaimer

Use these tools at your own risk. Always back up your game files before making changes. Modding may violate game terms of service - proceed responsibly and don't ruin the experience for others.
