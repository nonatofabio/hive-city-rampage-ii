# Building & Releasing Hive City Rampage

This document explains how to build distributable packages of the game for Windows, macOS, and Linux.

## Quick Start - Local Build

To test a build locally on your machine:

```bash
./build.sh
```

This script will:
1. Set up a virtual environment (if needed)
2. Install dependencies (pygame, pyinstaller)
3. Clean previous builds
4. Run PyInstaller with the spec file
5. Create an executable in the `dist/` folder

### Testing Your Build

After building, test the executable:

**macOS:**
```bash
open dist/HiveCityRampage.app
```

**Linux:**
```bash
cd dist
./HiveCityRampage
```

**Windows:**
```bash
dist\HiveCityRampage.exe
```

## Automated GitHub Releases

The project uses GitHub Actions to automatically build and release the game for all platforms.

### Creating a Release

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.2.0"  # Increment as needed
   ```

2. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Release v0.2.0"
   ```

3. **Create and push a version tag:**
   ```bash
   git tag v0.2.0
   git push origin main
   git push origin v0.2.0
   ```

4. **Monitor the build:**
   - Go to your repository on GitHub
   - Click the "Actions" tab
   - Watch the "Build and Release" workflow run

5. **Release assets will be automatically created:**
   - `HiveCityRampage-Windows.zip` - Windows executable
   - `HiveCityRampage-macOS.zip` - macOS app bundle
   - `HiveCityRampage-Linux.tar.gz` - Linux executable

### Manual Trigger

You can also manually trigger a build without creating a tag:

1. Go to GitHub Actions tab
2. Select "Build and Release" workflow
3. Click "Run workflow"
4. Choose branch and click "Run workflow"

This will build all platforms but won't create a GitHub release (only triggered by tags).

## Build Configuration

### PyInstaller Spec File

The `hive_city_rampage.spec` file controls how PyInstaller packages the game:

- **Entry point:** `src/pyg/hive_city_rampage.py`
- **Assets:** All files from `src/pyg/assets/` are bundled
- **Console:** Set to `False` for windowed app (no terminal)
- **Output:** Single executable with all dependencies

### Customizing the Build

**Adding an icon:**

1. Create icon files:
   - `assets/icon.ico` for Windows (256x256 recommended)
   - `assets/icon.icns` for macOS (512x512 recommended)
   - `assets/icon.png` for Linux (256x256 recommended)

2. Update `hive_city_rampage.spec`:
   ```python
   exe = EXE(
       ...
       icon='assets/icon.ico',  # Uncomment and set path
   )
   ```

**Excluding unnecessary modules:**

If build size is too large, you can exclude unused modules:

```python
a = Analysis(
    ...
    excludes=['tkinter', 'matplotlib', 'numpy'],  # Example
)
```

## Platform-Specific Notes

### macOS

- First run may show "unidentified developer" warning
- Users need to right-click → Open the first time
- For distribution, consider code signing (requires Apple Developer account)

### Windows

- May trigger SmartScreen warning for unsigned executables
- Consider code signing for production releases
- Builds on Windows require no special SDL setup

### Linux

- Built binary should work on most modern distributions
- Users may need to `chmod +x HiveCityRampage` before running
- SDL2 libraries are bundled with PyInstaller

## Troubleshooting

### Build fails on GitHub Actions

**Check the Actions logs:**
1. Go to Actions tab
2. Click the failed workflow run
3. Expand the failed step to see error details

**Common issues:**
- Missing dependencies: Update `pyproject.toml`
- Asset loading errors: Check file paths in spec file
- Platform-specific bugs: Test locally first with `./build.sh`

### Build succeeds but game crashes

**Test locally first:**
```bash
./build.sh
# Run the built executable to test
```

**Check asset loading:**
- Ensure all assets are in `src/pyg/assets/`
- Verify paths use relative references
- Check PyInstaller spec includes all data files

**Debug mode:**
Edit `hive_city_rampage.spec` and set:
```python
exe = EXE(
    ...
    console=True,  # Shows console for error messages
    debug=True,    # Enables debug output
)
```

### Large build size

PyInstaller bundles Python + pygame + all dependencies. Typical sizes:
- Windows: ~40-60 MB
- macOS: ~45-65 MB
- Linux: ~40-55 MB

To reduce size:
- Use UPX compression (enabled by default)
- Exclude unused modules in spec file
- Use `--strip` flag for Linux builds

## Version Management

Follow semantic versioning:
- **v0.x.x** - Alpha builds (current)
- **v1.0.0** - First stable release
- **v1.1.0** - Minor updates (new features)
- **v1.1.1** - Patch updates (bug fixes)

Mark alpha/beta releases as "pre-release" on GitHub:
- Edit the release after it's created
- Check "Set as a pre-release"
- Or edit `.github/workflows/build-release.yml` to change `prerelease: true`

## Distribution Checklist

Before releasing a new version:

- [ ] Test game functionality locally
- [ ] Update version in `pyproject.toml`
- [ ] Update version in README.md
- [ ] Review CHANGELOG (if you have one)
- [ ] Test local build with `./build.sh`
- [ ] Run game from dist folder to verify
- [ ] Commit all changes
- [ ] Create and push version tag
- [ ] Monitor GitHub Actions build
- [ ] Download and test all platform builds
- [ ] Update release notes if needed
- [ ] Announce release (Discord, social media, etc.)

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pygame Deployment Guide](https://www.pygame.org/wiki/Deployment)
