# Nuphillion Publisher

Standalone helper for publishing Halo Wars 2 Modding Suite output into the
Nuphillion Launcher Alpha asset ZIPs.

## What it does

- Builds `Assets/moddedPatch.zip` from the latest GTS `file_manifest.xml` and
  `.pkg`.
- Optionally rebuilds `Assets/nuphillionExpansion.zip` from a loose expansion
  folder.
- Ensures launcher ZIPs are tracked through Git LFS.
- Optionally commits and pushes the launcher repo after publishing.

## Defaults

- Launcher repo: `C:\Users\Admin\Downloads\Git\NuphillionDev`
- GTS output:
  `%LOCALAPPDATA%\Packages\Microsoft.HoganThreshold_8wekyb3d8bbwe\LocalState\GTS\1_11_2931_2_active`
- Expansion source:
  `C:\Users\Admin\Downloads\Nuphillion\Workspace\nuphillionExpansion`

## Build

Run:

```bat
build.bat
```

The executable is written to:

```text
dist\Nuphillion Publisher.exe
```
