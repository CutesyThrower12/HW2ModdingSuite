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
- Optionally initializes the NuphillionDev `Release` GitHub Actions workflow.
- Optionally runs the release workflow and downloads `NuphillionManager-*.zip`.

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
dist\Nuphillion Publisher\Nuphillion Publisher.exe
```

## Release Automation

Release workflow actions use the GitHub CLI:

```powershell
gh auth login
```

Enable these toggles in the app as needed:

- `Initialize/update Release workflow` writes the optimized `ci.yml` and
  `release.yml` files into the launcher repo.
- `Run GitHub Release workflow` queues `release.yml`, waits for the run to
  finish, and reports progress in the log.
- `Download release ZIP after workflow` downloads the newest
  `NuphillionManager-*.zip` release asset to the selected folder.

If you publish new launcher assets and want the release to contain them, keep
`Push to GitHub` enabled before running the release workflow.
