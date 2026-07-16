# DTLDesktop v1.1-1

Windows desktop configuration manager.

## What?

DTLDesktop saves, compares, and restores desktop icon positions, the detected
monitor configuration, and per-monitor wallpapers. Each detected configuration
is stored separately:

```text
Desktop\
    DualLandscape\
        icons.json
        monitors.json
        wallpaper.json
```

`wallpaper.json` maps each monitor to two wallpapers:

```json
{
  "configuration": "DualLandscape",
  "monitors": [
    {
      "screen": 2,
      "id": "identifier supplied by Windows",
      "wallpaper": {
        "landscape": "Piccovaggia.jpg",
        "portrait": "Division2.jpg"
      }
    }
  ]
}
```

The actual file stores full paths so Windows can find the images.

## Why?

Windows can move desktop icons after a monitor change, when a projector is
connected, or when moving between office and remote work. DTLDesktop restores a
known layout quickly.

## How?

Run `DTLDesktop.exe`, then use:

- `S`: update the configuration selected at startup without asking for a name;
- `A`: apply a complete profile after confirmation;
- `R`: restore icon positions only;
- `T`: simulate restoration without changing anything;
- `D`: diagnose the current configuration;
- `C`: compare the desktop with a profile;
- `F`: select one image for each monitor in the current configuration using
  Windows Explorer; no path needs to be typed;

The command line also supports:

```powershell
DTLDesktop.exe --save
DTLDesktop.exe --apply DualPortrait
DTLDesktop.exe --test DualLandscape
DTLDesktop.exe --restore DualLandscape
DTLDesktop.exe --diagnose
DTLDesktop.exe --auto
```

To restore at every sign-in, add a shortcut to `DTLDesktop.exe --auto` to the
Windows Startup folder.

## Safety

Test mode is strictly read-only. Before an interactive restoration, DTLDesktop
shows the differences and asks for confirmation. Missing icons are skipped and
reported. DTLDesktop does not change monitor resolution or arrangement.

At startup, DTLDesktop selects the configuration that exactly matches the
observed arrangement, such as `DualLandscape` or `DualPortrait`. Select the
images with `F`, then press `S` to update that configuration. After a monitor is
rotated, the other configuration is selected automatically.

The image picker automatically returns to the last folder used, including after
DTLDesktop is closed and started again.

Wallpapers are always applied using the Windows `Fill` mode. No other display
mode is offered. Fill is reapplied after an orientation change even when the
wallpaper file did not change, and is then verified.

## Applying a profile

The `A` action applies a complete desktop state in this order:

1. temporarily capture the current display, wallpapers, and icons;
2. change monitor orientation, resolution, and arrangement as one operation;
3. wait for Windows to stabilize;
4. apply wallpapers using `Fill`;
5. restore icon positions;
6. verify the resulting configuration.

Confirmation is always required before changing the display. If Windows rejects
the new mode or validation fails, DTLDesktop automatically restores the
previous display, wallpapers, and icons.

## Compatibility

- 64-bit Windows 10 or Windows 11;
- Windows Explorer must manage the desktop;
- DTLDesktop must run with the same privilege level as Windows Explorer.

## Build

```powershell
python -m pip install pyinstaller
pyinstaller --clean DTLDesktop.spec
```

The executable is created as `dist\DTLDesktop.exe`.
