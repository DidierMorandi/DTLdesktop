# DTLdesktop v1.1-5

Windows desktop configuration manager.

## What?

DTLdesktop saves, compares, and restores desktop icon positions, the detected
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
connected, or when moving between office and remote work. DTLdesktop restores a
known layout quickly.

## How?

Run `DTLdesktop.exe`, then use:

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
DTLdesktop.exe --save
DTLdesktop.exe --apply DualPortrait
DTLdesktop.exe --test DualLandscape
DTLdesktop.exe --restore DualLandscape
DTLdesktop.exe --diagnose
DTLdesktop.exe --auto
```

To restore at every sign-in, add a shortcut to `DTLdesktop.exe --auto` to the
Windows Startup folder.

## Safety

Test mode is strictly read-only. Before an interactive restoration, DTLdesktop
shows the differences and asks for confirmation. Missing icons are skipped and
reported. DTLdesktop does not change monitor resolution or arrangement.

At startup, DTLdesktop selects the configuration that exactly matches the
observed arrangement, such as `DualLandscape` or `DualPortrait`. Select the
images with `F`, then press `S` to update that configuration. After a monitor is
rotated, the other configuration is selected automatically.

The image picker automatically returns to the last folder used, including after
DTLdesktop is closed and started again.

Wallpapers are always applied using the Windows `Fill` mode. No other display
mode is offered. After an orientation change, DTLdesktop reapplies every
wallpaper even when its file path did not change, preventing Windows from
keeping the bitmap calculated for the previous orientation.

## Applying a profile

The `A` action applies a complete desktop state in this order:

1. temporarily capture the current display, wallpapers, and icons;
2. change monitor orientation, resolution, and arrangement as one operation;
3. wait for Windows to stabilize;
4. reapply every wallpaper using `Fill`;
5. restore icon positions;
6. verify the resulting configuration.

Confirmation is always required before changing the display. If Windows rejects
the new mode or validation fails, DTLdesktop automatically restores the
previous display, wallpapers, and icons.

## Compatibility

- 64-bit Windows 10 or Windows 11;
- Windows Explorer must manage the desktop;
- DTLdesktop must run with the same privilege level as Windows Explorer.

## Build

```powershell
python -m pip install pyinstaller
pyinstaller --clean DTLdesktop.spec
```

The executable is created as `dist\DTLdesktop.exe`.
