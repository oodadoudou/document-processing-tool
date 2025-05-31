# Releases

This directory contains release artifacts for the File Process Tools application.

## Directory Structure

```
releases/
├── latest/          # Latest release builds
├── archive/         # Previous release builds
└── README.md        # This file
```

## File Naming Convention

Release files should follow this naming pattern:
- Windows: `File-Process-Tools-Setup-vX.Y.Z.exe`
- macOS: `File-Process-Tools-vX.Y.Z.dmg`

Where X.Y.Z represents the semantic version number (e.g., v1.0.0).

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