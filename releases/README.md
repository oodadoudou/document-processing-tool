# Releases Directory

This directory contains the latest release builds of the File Process Tools application.

## Structure

- `latest/` - Contains the most recent release build
  - Format: `File-Process-Tools-Setup-vX.Y.Z.exe`

## Release Process

1. Build the application
2. Move the built file to `releases/latest/` with the correct version naming
3. Create a Git tag for the version
4. Push changes and tag to GitHub

Previous versions can be found in the GitHub Releases section of the repository.

## File Naming Convention

Release files should follow this naming pattern:
- Windows: `File-Process-Tools-Setup-vX.Y.Z.exe`
- macOS: `File-Process-Tools-Setup-vX.Y.Z.dmg`
- Linux: `File-Process-Tools-Setup-vX.Y.Z.AppImage`

Where X.Y.Z represents the semantic version number (e.g., v1.0.0, v1.0.1, etc.)

## Git LFS

This directory is managed by Git LFS (Large File Storage). The following file types are automatically tracked:
- *.exe (Windows installers)
- *.dmg (macOS disk images)
- *.zip (Archive files)
- *.msi (Windows installers)

## Usage

1. Build your release artifacts
2. Place them in the appropriate directory (latest/ or archive/)
3. Commit and push - Git LFS will handle the large files automatically

## Notes

- Keep only necessary release files
- Move older versions to the archive/ directory
- Update version numbers in filenames to match release tags 