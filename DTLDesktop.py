#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""DTLdesktop - gestionnaire de configurations du bureau Windows."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


VERSION = "v1.1-4"
PROFILE_DIRECTORY = "Desktop"
APP_NAME = "DTLdesktop"
APP_SUITE = "Un outil de la suite NetDTL"
APP_WEBSITE = "www.netdtl.com"
APP_SUBTITLE = "Gestionnaire de configurations du bureau Windows"
LOGO_LINES = (
    "┌─┬─┬─┬─┬─┬─┐",
    "│N│e│t│D│T│L│",
    "└─┴─┴─┴─┴─┴─┘",
)
ANSI_LOGO = "\033[38;2;255;255;255;48;2;2;1;183m"
ANSI_BOLD = "\033[1m"
ANSI_GREEN = "\033[38;2;0;255;0m"
ANSI_RESET = "\033[0m"


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def profiles_dir() -> Path:
    return application_dir() / PROFILE_DIRECTORY


def configure_console_encoding() -> None:
    """Conserve les accents français dans Windows Terminal et les sorties redirigées."""
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except OSError:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def terminal_width() -> int:
    try:
        return max(76, min(shutil.get_terminal_size().columns, 160))
    except OSError:
        return 100


def supports_color() -> bool:
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return False
    if os.name != "nt":
        return os.environ.get("TERM", "").casefold() != "dumb"
    try:
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if handle in (0, -1) or not ctypes.windll.kernel32.GetConsoleMode(
            handle, ctypes.byref(mode)
        ):
            return False
        return bool(ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError, ValueError):
        return False


def brand_header_lines(screen_width: int, color: bool = False) -> list[str]:
    """Construit l'en-tête commun des outils NetDTL."""
    left = (f"{APP_NAME} {VERSION}", APP_SUITE, APP_WEBSITE)
    gap = 3
    logo_width = len(LOGO_LINES[0])
    left_width = max(0, screen_width - logo_width - gap)
    result: list[str] = []
    for index, (text, logo) in enumerate(zip(left, LOGO_LINES)):
        text = text[:left_width]
        padding = " " * (left_width - len(text))
        visible_text = (
            f"{ANSI_BOLD}{text}{ANSI_RESET}{padding}"
            if color and index == 0
            else f"{text}{padding}"
        )
        visible_logo = f"{ANSI_LOGO}{logo}{ANSI_RESET}" if color else logo
        result.append(f"{visible_text}{' ' * gap}{visible_logo}")
    result.extend(("", APP_SUBTITLE, "", "=" * screen_width))
    return result


def show_application_header() -> None:
    clear_screen()
    print("\n".join(brand_header_lines(terminal_width(), supports_color())))


def console_style(value: object, ansi_style: str, color: bool | None = None) -> str:
    """Applique un style ANSI sans polluer les sorties redirigées."""
    enabled = supports_color() if color is None else color
    text = str(value)
    return f"{ansi_style}{text}{ANSI_RESET}" if enabled else text


def green_value(value: object, color: bool | None = None) -> str:
    return console_style(value, ANSI_GREEN, color)


def colored_input(prompt: str) -> str:
    """Affiche en vert la réponse saisie par l'utilisateur."""
    if not supports_color():
        return input(prompt)
    try:
        return input(f"{prompt}{ANSI_GREEN}")
    finally:
        print(ANSI_RESET, end="", flush=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary.replace(path)


def safe_profile_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", value).strip().rstrip(". ")
    if not value or value in {".", ".."}:
        raise ValueError("Le nom du profil est vide ou invalide.")
    return value[:80]


def orientation(width: int, height: int) -> str:
    if width > height:
        return "Paysage"
    if height > width:
        return "Portrait"
    return "Carré"


def configuration_signature(monitors: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Signature stable, indépendante des noms attribués aux écrans par Windows."""
    items = list(monitors)
    if not items:
        return []
    origin_x = min(int(item["left"]) for item in items)
    origin_y = min(int(item["top"]) for item in items)
    normalized = [
        {
            "x": int(item["left"]) - origin_x,
            "y": int(item["top"]) - origin_y,
            "width": int(item["width"]),
            "height": int(item["height"]),
            "orientation": str(item["orientation"]),
            "primary": bool(item.get("primary", False)),
        }
        for item in items
    ]
    return sorted(normalized, key=lambda item: (item["x"], item["y"], not item["primary"]))


def suggested_profile_name(monitors: list[dict[str, Any]]) -> str:
    count = len(monitors)
    kinds = [item["orientation"] for item in monitors]
    if count == 1:
        return "SingleLandscape" if kinds[0] == "Paysage" else "SinglePortrait"
    prefix = {2: "Dual", 3: "Triple"}.get(count, f"{count}Monitors")
    if len(set(kinds)) == 1:
        return prefix + ("Landscape" if kinds[0] == "Paysage" else "Portrait")
    if "Portrait" in kinds:
        return prefix + "Portrait"
    return prefix + "Mixed"


class DesktopError(RuntimeError):
    pass


if os.name == "nt":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ole32 = ctypes.OleDLL("ole32")
    comdlg32 = ctypes.WinDLL("comdlg32", use_last_error=True)

    MONITORINFOF_PRIMARY = 1
    ENUM_CURRENT_SETTINGS = -1
    DM_POSITION = 0x00000020
    DM_DISPLAYORIENTATION = 0x00000080
    DM_PELSWIDTH = 0x00080000
    DM_PELSHEIGHT = 0x00100000
    CDS_UPDATEREGISTRY = 0x00000001
    CDS_NORESET = 0x10000000
    DISP_CHANGE_SUCCESSFUL = 0
    PROCESS_VM_OPERATION = 0x0008
    PROCESS_VM_READ = 0x0010
    PROCESS_VM_WRITE = 0x0020
    PROCESS_QUERY_INFORMATION = 0x0400
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    MEM_RELEASE = 0x8000
    PAGE_READWRITE = 0x04
    LVM_FIRST = 0x1000
    LVM_GETITEMCOUNT = LVM_FIRST + 4
    LVM_GETITEMPOSITION = LVM_FIRST + 16
    LVM_GETITEMTEXTW = LVM_FIRST + 115
    LVM_SETITEMPOSITION32 = LVM_FIRST + 49
    SPI_GETDESKWALLPAPER = 0x0073
    SPI_SETDESKWALLPAPER = 0x0014
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02
    CLSCTX_ALL = 23
    COINIT_APARTMENTTHREADED = 0x2
    RPC_E_CHANGED_MODE = -2147417850
    OFN_FILEMUSTEXIST = 0x00001000
    OFN_PATHMUSTEXIST = 0x00000800
    OFN_EXPLORER = 0x00080000
    OFN_NOCHANGEDIR = 0x00000008
    DESKTOP_WALLPAPER_POSITION_FILL = 4
    DESKTOP_WALLPAPER_POSITION_FIT = 3

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class POINTL(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
            ("szDevice", wintypes.WCHAR * 32),
        ]

    class _DEVMODE_DISPLAY(ctypes.Structure):
        _fields_ = [
            ("dmPosition", POINTL),
            ("dmDisplayOrientation", wintypes.DWORD),
            ("dmDisplayFixedOutput", wintypes.DWORD),
        ]

    class _DEVMODE_PRINTER(ctypes.Structure):
        _fields_ = [
            ("dmOrientation", ctypes.c_short),
            ("dmPaperSize", ctypes.c_short),
            ("dmPaperLength", ctypes.c_short),
            ("dmPaperWidth", ctypes.c_short),
            ("dmScale", ctypes.c_short),
            ("dmCopies", ctypes.c_short),
            ("dmDefaultSource", ctypes.c_short),
            ("dmPrintQuality", ctypes.c_short),
        ]

    class _DEVMODE_UNION(ctypes.Union):
        _anonymous_ = ("display",)
        _fields_ = [
            ("display", _DEVMODE_DISPLAY),
            ("printer", _DEVMODE_PRINTER),
        ]

    class DEVMODEW(ctypes.Structure):
        _anonymous_ = ("union",)
        _fields_ = [
            ("dmDeviceName", wintypes.WCHAR * 32),
            ("dmSpecVersion", wintypes.WORD),
            ("dmDriverVersion", wintypes.WORD),
            ("dmSize", wintypes.WORD),
            ("dmDriverExtra", wintypes.WORD),
            ("dmFields", wintypes.DWORD),
            ("union", _DEVMODE_UNION),
            ("dmColor", ctypes.c_short),
            ("dmDuplex", ctypes.c_short),
            ("dmYResolution", ctypes.c_short),
            ("dmTTOption", ctypes.c_short),
            ("dmCollate", ctypes.c_short),
            ("dmFormName", wintypes.WCHAR * 32),
            ("dmLogPixels", wintypes.WORD),
            ("dmBitsPerPel", wintypes.DWORD),
            ("dmPelsWidth", wintypes.DWORD),
            ("dmPelsHeight", wintypes.DWORD),
            ("dmDisplayFlags", wintypes.DWORD),
            ("dmDisplayFrequency", wintypes.DWORD),
            ("dmICMMethod", wintypes.DWORD),
            ("dmICMIntent", wintypes.DWORD),
            ("dmMediaType", wintypes.DWORD),
            ("dmDitherType", wintypes.DWORD),
            ("dmReserved1", wintypes.DWORD),
            ("dmReserved2", wintypes.DWORD),
            ("dmPanningWidth", wintypes.DWORD),
            ("dmPanningHeight", wintypes.DWORD),
        ]

    class LVITEMW(ctypes.Structure):
        _fields_ = [
            ("mask", wintypes.UINT),
            ("iItem", ctypes.c_int),
            ("iSubItem", ctypes.c_int),
            ("state", wintypes.UINT),
            ("stateMask", wintypes.UINT),
            ("pszText", ctypes.c_void_p),
            ("cchTextMax", ctypes.c_int),
            ("iImage", ctypes.c_int),
            ("lParam", ctypes.c_void_p),
            ("iIndent", ctypes.c_int),
            ("iGroupId", ctypes.c_int),
            ("cColumns", wintypes.UINT),
            ("puColumns", ctypes.c_void_p),
            ("piColFmt", ctypes.c_void_p),
            ("iGroup", ctypes.c_int),
        ]

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

        @classmethod
        def from_string(cls, value: str) -> "GUID":
            import uuid

            raw = uuid.UUID(value).bytes_le
            return cls.from_buffer_copy(raw)

    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [
            ("lStructSize", wintypes.DWORD),
            ("hwndOwner", wintypes.HWND),
            ("hInstance", wintypes.HINSTANCE),
            ("lpstrFilter", wintypes.LPCWSTR),
            ("lpstrCustomFilter", wintypes.LPWSTR),
            ("nMaxCustFilter", wintypes.DWORD),
            ("nFilterIndex", wintypes.DWORD),
            ("lpstrFile", wintypes.LPWSTR),
            ("nMaxFile", wintypes.DWORD),
            ("lpstrFileTitle", wintypes.LPWSTR),
            ("nMaxFileTitle", wintypes.DWORD),
            ("lpstrInitialDir", wintypes.LPCWSTR),
            ("lpstrTitle", wintypes.LPCWSTR),
            ("Flags", wintypes.DWORD),
            ("nFileOffset", wintypes.WORD),
            ("nFileExtension", wintypes.WORD),
            ("lpstrDefExt", wintypes.LPCWSTR),
            ("lCustData", wintypes.LPARAM),
            ("lpfnHook", ctypes.c_void_p),
            ("lpTemplateName", wintypes.LPCWSTR),
            ("pvReserved", ctypes.c_void_p),
            ("dwReserved", wintypes.DWORD),
            ("FlagsEx", wintypes.DWORD),
        ]

    user32.EnumDisplayMonitors.argtypes = [
        wintypes.HDC,
        ctypes.POINTER(RECT),
        ctypes.c_void_p,
        wintypes.LPARAM,
    ]
    user32.EnumDisplayMonitors.restype = wintypes.BOOL
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFOEXW)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    user32.EnumDisplaySettingsW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(DEVMODEW),
    ]
    user32.EnumDisplaySettingsW.restype = wintypes.BOOL
    user32.ChangeDisplaySettingsExW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(DEVMODEW),
        wintypes.HWND,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    user32.ChangeDisplaySettingsExW.restype = wintypes.LONG
    user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowExW.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = wintypes.LPARAM
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.VirtualAllocEx.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        ctypes.c_size_t,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    kernel32.VirtualAllocEx.restype = ctypes.c_void_p
    kernel32.VirtualFreeEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD]
    kernel32.WriteProcessMemory.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.ReadProcessMemory.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.GetConsoleWindow.argtypes = []
    kernel32.GetConsoleWindow.restype = wintypes.HWND
    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole32.CoInitializeEx.restype = ctypes.c_long
    ole32.CoUninitialize.argtypes = []
    ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(GUID),
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(GUID),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    ole32.CoCreateInstance.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    comdlg32.GetOpenFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
    comdlg32.GetOpenFileNameW.restype = wintypes.BOOL


def choose_wallpaper_file(
    title: str,
    current_path: str = "",
    preferred_directory: str = "",
) -> str | None:
    """Ouvre le sélecteur de fichiers Windows et renvoie l'image choisie."""
    if os.name != "nt":
        raise DesktopError("La sélection des images nécessite Windows.")
    buffer = ctypes.create_unicode_buffer(32768)
    initial_directory = ""
    if preferred_directory and Path(preferred_directory).is_dir():
        initial_directory = preferred_directory
    elif current_path:
        parent = Path(current_path).parent
        if parent.is_dir():
            initial_directory = str(parent)
    dialog = OPENFILENAMEW()
    dialog.lStructSize = ctypes.sizeof(dialog)
    dialog.hwndOwner = kernel32.GetConsoleWindow()
    dialog.lpstrFilter = (
        "Images (*.jpg;*.jpeg;*.png;*.bmp;*.webp)\0"
        "*.jpg;*.jpeg;*.png;*.bmp;*.webp\0"
        "Tous les fichiers (*.*)\0*.*\0\0"
    )
    dialog.nFilterIndex = 1
    dialog.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
    dialog.nMaxFile = len(buffer)
    dialog.lpstrInitialDir = initial_directory or None
    dialog.lpstrTitle = title
    dialog.Flags = (
        OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_EXPLORER | OFN_NOCHANGEDIR
    )
    if not comdlg32.GetOpenFileNameW(ctypes.byref(dialog)):
        return None
    return buffer.value


class DesktopWallpaperAPI:
    """Accès direct à IDesktopWallpaper, inclus dans Windows 8 et versions suivantes."""

    CLSID = "C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD"
    IID = "B92B56A9-8B55-4E14-9A89-0199BBB6F93B"

    def __init__(self) -> None:
        if os.name != "nt":
            raise DesktopError("Les fonds par écran nécessitent Windows.")
        self.interface = ctypes.c_void_p()
        self.must_uninitialize = False
        status = int(ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED))
        if status in (0, 1):
            self.must_uninitialize = True
        elif status != RPC_E_CHANGED_MODE:
            raise DesktopError("Windows n'a pas pu initialiser la gestion des fonds d'écran.")
        clsid = GUID.from_string(self.CLSID)
        iid = GUID.from_string(self.IID)
        status = int(
            ole32.CoCreateInstance(
                ctypes.byref(clsid),
                None,
                CLSCTX_ALL,
                ctypes.byref(iid),
                ctypes.byref(self.interface),
            )
        )
        if status < 0 or not self.interface.value:
            if self.must_uninitialize:
                ole32.CoUninitialize()
                self.must_uninitialize = False
            raise DesktopError("La gestion des fonds distincts par écran n'est pas disponible.")

    def _method(self, index: int, result_type: Any, *argument_types: Any) -> Any:
        table = ctypes.cast(
            self.interface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
        ).contents
        return ctypes.WINFUNCTYPE(
            result_type, ctypes.c_void_p, *argument_types
        )(table[index])

    @staticmethod
    def _check(status: int, action: str) -> None:
        if int(status) < 0:
            raise DesktopError(f"Windows n'a pas pu {action}.")

    def monitor_count(self) -> int:
        count = wintypes.UINT()
        status = self._method(
            6, ctypes.c_long, ctypes.POINTER(wintypes.UINT)
        )(self.interface, ctypes.byref(count))
        self._check(status, "compter les écrans")
        return int(count.value)

    def monitor_id(self, index: int) -> str:
        pointer = ctypes.c_void_p()
        status = self._method(
            5, ctypes.c_long, wintypes.UINT, ctypes.POINTER(ctypes.c_void_p)
        )(self.interface, index, ctypes.byref(pointer))
        self._check(status, "identifier un écran")
        try:
            return ctypes.wstring_at(pointer.value) if pointer.value else ""
        finally:
            if pointer.value:
                ole32.CoTaskMemFree(pointer)

    def monitor_rect(self, monitor_id: str) -> "RECT":
        rect = RECT()
        status = self._method(
            7, ctypes.c_long, wintypes.LPCWSTR, ctypes.POINTER(RECT)
        )(self.interface, monitor_id, ctypes.byref(rect))
        self._check(status, "lire la position d'un écran")
        return rect

    def get_wallpaper(self, monitor_id: str) -> str:
        pointer = ctypes.c_void_p()
        status = self._method(
            4, ctypes.c_long, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)
        )(self.interface, monitor_id, ctypes.byref(pointer))
        self._check(status, "lire un fond d'écran")
        try:
            return ctypes.wstring_at(pointer.value) if pointer.value else ""
        finally:
            if pointer.value:
                ole32.CoTaskMemFree(pointer)

    def set_wallpaper(self, monitor_id: str, path: str) -> None:
        status = self._method(
            3, ctypes.c_long, wintypes.LPCWSTR, wintypes.LPCWSTR
        )(self.interface, monitor_id, path)
        self._check(status, "appliquer un fond d'écran")

    def set_fill_position(self) -> None:
        self.set_position(DESKTOP_WALLPAPER_POSITION_FILL)

    def set_position(self, position: int) -> None:
        status = self._method(8, ctypes.c_long, ctypes.c_int)(
            self.interface, position
        )
        self._check(status, "sélectionner le cadrage du fond d'écran")

    def refresh_position(self, position: int) -> None:
        """Force Windows à recalculer le cadrage après une rotation d'écran."""
        alternate = (
            DESKTOP_WALLPAPER_POSITION_FILL
            if position == DESKTOP_WALLPAPER_POSITION_FIT
            else DESKTOP_WALLPAPER_POSITION_FIT
        )
        self.set_position(alternate)
        self.set_position(position)
        if self.get_position() != position:
            self.set_position(position)
        if self.get_position() != position:
            raise DesktopError("Windows n'a pas conservé le cadrage demandé.")

    def refresh_fill_position(self) -> None:
        self.refresh_position(DESKTOP_WALLPAPER_POSITION_FILL)

    def get_position(self) -> int:
        position = ctypes.c_int()
        status = self._method(
            9, ctypes.c_long, ctypes.POINTER(ctypes.c_int)
        )(self.interface, ctypes.byref(position))
        self._check(status, "vérifier le mode d'affichage du fond")
        return int(position.value)

    def close(self) -> None:
        if self.interface.value:
            self._method(2, wintypes.ULONG)(self.interface)
            self.interface = ctypes.c_void_p()
        if self.must_uninitialize:
            ole32.CoUninitialize()
            self.must_uninitialize = False

    def __enter__(self) -> "DesktopWallpaperAPI":
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        self.close()


@dataclass
class RemoteMemory:
    process: Any
    address: int
    size: int

    @classmethod
    def allocate(cls, process: Any, size: int) -> "RemoteMemory":
        address = kernel32.VirtualAllocEx(
            process, None, size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE
        )
        if not address:
            raise DesktopError("Windows n'a pas permis de lire la liste des icônes.")
        return cls(process, int(address), size)

    def write(self, value: ctypes.Structure) -> None:
        written = ctypes.c_size_t()
        if not kernel32.WriteProcessMemory(
            self.process,
            self.address,
            ctypes.byref(value),
            ctypes.sizeof(value),
            ctypes.byref(written),
        ):
            raise DesktopError("Impossible de préparer la lecture des icônes.")

    def read_bytes(self, size: int | None = None) -> bytes:
        length = size or self.size
        data = ctypes.create_string_buffer(length)
        read = ctypes.c_size_t()
        if not kernel32.ReadProcessMemory(
            self.process, self.address, data, length, ctypes.byref(read)
        ):
            raise DesktopError("Impossible de lire les informations d'une icône.")
        return data.raw[: read.value]

    def close(self) -> None:
        if self.address:
            kernel32.VirtualFreeEx(self.process, self.address, 0, MEM_RELEASE)
            self.address = 0


class WindowsDesktop:
    def _require_windows(self) -> None:
        if os.name != "nt":
            raise DesktopError("DTLdesktop fonctionne uniquement sous Windows.")

    def _read_display_mode(self, device: str) -> dict[str, Any]:
        mode = DEVMODEW()
        mode.dmSize = ctypes.sizeof(DEVMODEW)
        if not user32.EnumDisplaySettingsW(
            device, ENUM_CURRENT_SETTINGS, ctypes.byref(mode)
        ):
            raise DesktopError(f"Impossible de lire le mode d'affichage de {device}.")
        return {
            "device": device,
            "left": int(mode.dmPosition.x),
            "top": int(mode.dmPosition.y),
            "width": int(mode.dmPelsWidth),
            "height": int(mode.dmPelsHeight),
            "rotation": int(mode.dmDisplayOrientation),
            "frequency": int(mode.dmDisplayFrequency),
        }

    def display_modes(self) -> list[dict[str, Any]]:
        return [
            self._read_display_mode(str(monitor["device"]))
            for monitor in self.monitors()
        ]

    def set_display_modes(self, modes: list[dict[str, Any]]) -> None:
        self._require_windows()
        if not modes:
            raise DesktopError("Le profil ne contient aucun mode d'affichage.")
        for target in modes:
            device = str(target.get("device", ""))
            if not device:
                raise DesktopError("Un écran du profil ne possède pas d'identifiant Windows.")
            mode = DEVMODEW()
            mode.dmSize = ctypes.sizeof(DEVMODEW)
            if not user32.EnumDisplaySettingsW(
                device, ENUM_CURRENT_SETTINGS, ctypes.byref(mode)
            ):
                raise DesktopError(f"L'écran {device} n'est pas disponible.")
            mode.dmPosition.x = int(target.get("left", mode.dmPosition.x))
            mode.dmPosition.y = int(target.get("top", mode.dmPosition.y))
            mode.dmPelsWidth = int(target["width"])
            mode.dmPelsHeight = int(target["height"])
            if "rotation" in target:
                rotation = int(target["rotation"])
            else:
                rotation = (
                    1
                    if str(target.get("orientation", "")).casefold() == "portrait"
                    else 0
                )
            mode.dmDisplayOrientation = rotation
            mode.dmFields = (
                DM_POSITION
                | DM_DISPLAYORIENTATION
                | DM_PELSWIDTH
                | DM_PELSHEIGHT
            )
            status = int(
                user32.ChangeDisplaySettingsExW(
                    device,
                    ctypes.byref(mode),
                    None,
                    CDS_UPDATEREGISTRY | CDS_NORESET,
                    None,
                )
            )
            if status != DISP_CHANGE_SUCCESSFUL:
                raise DesktopError(
                    f"Windows a refusé le mode d'affichage de {device} (code {status})."
                )
        status = int(user32.ChangeDisplaySettingsExW(None, None, None, 0, None))
        if status != DISP_CHANGE_SUCCESSFUL:
            raise DesktopError(
                f"Windows n'a pas pu appliquer la configuration (code {status})."
            )

    def wait_for_configuration(
        self, signature: list[dict[str, Any]], timeout: float = 10.0
    ) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if configuration_signature(self.monitors()) == signature:
                return True
            time.sleep(0.5)
        return False

    def monitors(self) -> list[dict[str, Any]]:
        self._require_windows()
        result: list[dict[str, Any]] = []
        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM
        )

        def collect(handle: int, _hdc: int, _rect: Any, _data: int) -> bool:
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(info)
            if user32.GetMonitorInfoW(handle, ctypes.byref(info)):
                rect = info.rcMonitor
                width, height = rect.right - rect.left, rect.bottom - rect.top
                display_mode = self._read_display_mode(info.szDevice)
                result.append(
                    {
                        "device": info.szDevice,
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                        "width": width,
                        "height": height,
                        "orientation": orientation(width, height),
                        "rotation": display_mode["rotation"],
                        "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                    }
                )
            return True

        callback = callback_type(collect)
        if not user32.EnumDisplayMonitors(None, None, callback, 0):
            raise DesktopError("Windows n'a retourné aucun écran.")
        result = sorted(result, key=lambda item: (item["left"], item["top"]))
        try:
            with DesktopWallpaperAPI() as wallpapers:
                by_rect: dict[tuple[int, int, int, int], tuple[str, str]] = {}
                for index in range(wallpapers.monitor_count()):
                    monitor_id = wallpapers.monitor_id(index)
                    rect = wallpapers.monitor_rect(monitor_id)
                    by_rect[(rect.left, rect.top, rect.right, rect.bottom)] = (
                        monitor_id,
                        wallpapers.get_wallpaper(monitor_id),
                    )
                for monitor in result:
                    key = (
                        monitor["left"],
                        monitor["top"],
                        monitor["right"],
                        monitor["bottom"],
                    )
                    monitor_id, wallpaper = by_rect.get(
                        key, (str(monitor["device"]), "")
                    )
                    monitor["id"] = monitor_id
                    monitor["wallpaper"] = wallpaper
        except DesktopError:
            fallback = self._global_wallpaper()
            for monitor in result:
                monitor["id"] = str(monitor["device"])
                monitor["wallpaper"] = fallback.get("path", "")
        return result

    def _list_view(self) -> int:
        self._require_windows()
        found: list[int] = []
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def inspect(window: int, _data: int) -> bool:
            shell_view = user32.FindWindowExW(window, None, "SHELLDLL_DefView", None)
            if shell_view:
                list_view = user32.FindWindowExW(shell_view, None, "SysListView32", None)
                if list_view:
                    found.append(int(list_view))
                    return False
            return True

        callback = callback_type(inspect)
        user32.EnumWindows(callback, 0)
        if not found:
            raise DesktopError(
                "Le bureau Windows est introuvable. Redémarrez l'Explorateur Windows puis réessayez."
            )
        return found[0]

    def _open_explorer(self, list_view: int) -> Any:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(list_view, ctypes.byref(pid))
        process = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE,
            False,
            pid.value,
        )
        if not process:
            raise DesktopError(
                "Accès aux icônes refusé. Lancez DTLdesktop avec le même niveau de droits "
                "que l'Explorateur Windows."
            )
        return process

    def icons(self) -> list[dict[str, Any]]:
        list_view = self._list_view()
        process = self._open_explorer(list_view)
        item_memory = text_memory = point_memory = None
        try:
            count = int(user32.SendMessageW(list_view, LVM_GETITEMCOUNT, 0, 0))
            text_bytes = 1024
            item_memory = RemoteMemory.allocate(process, ctypes.sizeof(LVITEMW))
            text_memory = RemoteMemory.allocate(process, text_bytes)
            point_memory = RemoteMemory.allocate(process, ctypes.sizeof(POINT))
            icons: list[dict[str, Any]] = []
            occurrences: dict[str, int] = {}
            for index in range(count):
                item = LVITEMW()
                item.iSubItem = 0
                item.pszText = text_memory.address
                item.cchTextMax = text_bytes // ctypes.sizeof(wintypes.WCHAR)
                item_memory.write(item)
                user32.SendMessageW(list_view, LVM_GETITEMTEXTW, index, item_memory.address)
                raw_name = text_memory.read_bytes(text_bytes)
                name = raw_name.decode("utf-16-le", errors="replace").split("\0", 1)[0]
                user32.SendMessageW(list_view, LVM_GETITEMPOSITION, index, point_memory.address)
                raw_point = point_memory.read_bytes(ctypes.sizeof(POINT))
                point = POINT.from_buffer_copy(raw_point)
                occurrence = occurrences.get(name, 0)
                occurrences[name] = occurrence + 1
                icons.append(
                    {
                        "name": name,
                        "occurrence": occurrence,
                        "x": int(point.x),
                        "y": int(point.y),
                    }
                )
            return icons
        finally:
            for memory in (point_memory, text_memory, item_memory):
                if memory:
                    memory.close()
            kernel32.CloseHandle(process)

    def restore_icons(self, saved: list[dict[str, Any]]) -> dict[str, Any]:
        current = self.icons()
        indexes: dict[tuple[str, int], int] = {
            (item["name"], int(item.get("occurrence", 0))): index
            for index, item in enumerate(current)
        }
        list_view = self._list_view()
        process = self._open_explorer(list_view)
        point_memory = None
        restored = 0
        missing: list[str] = []
        try:
            point_memory = RemoteMemory.allocate(process, ctypes.sizeof(POINT))
            for item in saved:
                key = (str(item["name"]), int(item.get("occurrence", 0)))
                index = indexes.get(key)
                if index is None:
                    missing.append(str(item["name"]))
                    continue
                point = POINT(int(item["x"]), int(item["y"]))
                point_memory.write(point)
                user32.SendMessageW(
                    list_view, LVM_SETITEMPOSITION32, index, point_memory.address
                )
                restored += 1
            return {"restored": restored, "missing": missing, "current_count": len(current)}
        finally:
            if point_memory:
                point_memory.close()
            kernel32.CloseHandle(process)

    def _global_wallpaper(self) -> dict[str, Any]:
        self._require_windows()
        buffer = ctypes.create_unicode_buffer(32768)
        user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, len(buffer), buffer, 0)
        style = ""
        tile = ""
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
                style = str(winreg.QueryValueEx(key, "WallpaperStyle")[0])
                tile = str(winreg.QueryValueEx(key, "TileWallpaper")[0])
        except OSError:
            pass
        return {"path": buffer.value, "style": style, "tile": tile}

    def wallpaper(self) -> dict[str, Any]:
        monitors = self.monitors()
        return {
            "monitors": [
                {
                    "id": item.get("id", item["device"]),
                    "device": item["device"],
                    "screen": index,
                    "orientation": item["orientation"],
                    "wallpaper": item.get("wallpaper", ""),
                }
                for index, item in enumerate(monitors, 1)
            ],
            **self._global_wallpaper(),
        }

    def ensure_wallpaper_position(
        self, position: int = DESKTOP_WALLPAPER_POSITION_FILL
    ) -> None:
        with DesktopWallpaperAPI() as wallpapers:
            wallpapers.refresh_position(position)

    def ensure_wallpaper_fill(self) -> None:
        self.ensure_wallpaper_position(DESKTOP_WALLPAPER_POSITION_FILL)

    def wallpaper_position(self) -> int:
        with DesktopWallpaperAPI() as wallpapers:
            return wallpapers.get_position()

    def apply_wallpapers(
        self,
        assignments: list[dict[str, str]],
        position: int = DESKTOP_WALLPAPER_POSITION_FILL,
    ) -> dict[str, Any]:
        applied = 0
        missing: list[str] = []
        valid: list[dict[str, str]] = []
        for assignment in assignments:
            path = str(assignment.get("path", ""))
            if not path or not Path(path).is_file():
                missing.append(path or "(non défini)")
            else:
                valid.append(assignment)
        if not valid:
            return {"applied": 0, "missing": missing}
        try:
            with DesktopWallpaperAPI() as wallpapers:
                for assignment in valid:
                    wallpapers.set_wallpaper(str(assignment["id"]), str(assignment["path"]))
                    applied += 1
                wallpapers.refresh_position(position)
        except DesktopError:
            if len({item["path"] for item in valid}) == 1:
                if self.restore_wallpaper({"path": valid[0]["path"]}):
                    applied = len(valid)
                    self.ensure_wallpaper_position(position)
            else:
                raise
        return {"applied": applied, "missing": missing}

    def restore_wallpaper(self, saved: dict[str, Any]) -> bool:
        """Compatibilité avec les profils v1 qui contenaient un fond global."""
        path = str(saved.get("path", ""))
        if not path or not Path(path).is_file():
            return False
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "10")
                winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        except OSError:
            pass
        return bool(
            user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                path,
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
            )
        )


def orientation_rule_key(value: str) -> str:
    return "portrait" if value.casefold().startswith("portrait") else "landscape"


def wallpaper_position_for_monitors(monitors: list[dict[str, Any]]) -> int:
    """Le mode Windows reste Remplir ; les portraits sont préparés en amont."""
    return DESKTOP_WALLPAPER_POSITION_FILL


def comparable_path(value: str) -> str:
    return os.path.normcase(os.path.abspath(value)) if value else ""


def profile_matches_monitors(
    saved: dict[str, Any], current: list[dict[str, Any]]
) -> bool:
    saved_items = saved.get("monitors", [])
    saved_ids = {str(item.get("id", "")) for item in saved_items if item.get("id")}
    current_ids = {str(item.get("id", "")) for item in current if item.get("id")}
    if saved_ids and current_ids and len(saved_ids) == len(saved_items) == len(current_ids):
        return saved_ids == current_ids
    return saved.get("signature") == configuration_signature(current)


class DesktopManager:
    def __init__(self, desktop: WindowsDesktop | None = None, root: Path | None = None):
        self.desktop = desktop or WindowsDesktop()
        self.root = root or profiles_dir()

    def list_profiles(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(
            directory.name
            for directory in self.root.iterdir()
            if directory.is_dir()
            and (directory / "monitors.json").is_file()
            and (directory / "icons.json").is_file()
        )

    def settings(self) -> dict[str, Any]:
        try:
            value = read_json(self.root / "settings.json")
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def write_settings(self, **changes: Any) -> None:
        value = self.settings()
        value.update(
            {
                "format": 1,
                "tool": "DTLdesktop",
                "version": VERSION,
                **changes,
            }
        )
        write_json(self.root / "settings.json", value)

    def active_profile(self) -> str | None:
        name = str(self.settings().get("active_profile", ""))
        return name if name in self.list_profiles() else None

    def set_active_profile(self, name: str) -> None:
        self.write_settings(active_profile=safe_profile_name(name))

    def last_image_directory(self) -> str:
        directory = str(self.settings().get("last_image_directory", ""))
        return directory if directory and Path(directory).is_dir() else ""

    def set_last_image_directory(self, image_path: str) -> None:
        directory = Path(image_path).parent
        if directory.is_dir():
            self.write_settings(last_image_directory=str(directory))

    @staticmethod
    def _find_wallpaper_rule(
        wallpaper: dict[str, Any], monitor: dict[str, Any], index: int
    ) -> dict[str, Any] | None:
        rules = wallpaper.get("monitors", [])
        monitor_id = str(monitor.get("id", ""))
        device = str(monitor.get("device", ""))
        for rule in rules:
            if monitor_id and str(rule.get("id", "")) == monitor_id:
                return rule
        for rule in rules:
            if device and str(rule.get("device", "")) == device:
                return rule
        for rule in rules:
            if int(rule.get("screen", 0) or 0) == index:
                return rule
        return None

    def _wallpaper_document(
        self,
        name: str,
        monitors: list[dict[str, Any]],
        previous: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        previous = previous or {}
        old_global = str(previous.get("path", ""))
        rules: list[dict[str, Any]] = []
        for index, monitor in enumerate(monitors, 1):
            old_rule = self._find_wallpaper_rule(previous, monitor, index) or {}
            old_values = old_rule.get("wallpaper", {})
            if not isinstance(old_values, dict):
                old_values = {}
            current = str(monitor.get("wallpaper", "") or old_global)
            key = orientation_rule_key(str(monitor["orientation"]))
            landscape = str(old_values.get("landscape", "") or old_global or current)
            portrait = str(old_values.get("portrait", "") or old_global or current)
            if current:
                if key == "landscape":
                    landscape = current
                else:
                    portrait = current
            rules.append(
                {
                    "screen": index,
                    "id": str(monitor.get("id", monitor["device"])),
                    "device": str(monitor["device"]),
                    "wallpaper": {
                        "landscape": landscape,
                        "portrait": portrait,
                    },
                }
            )
        return {
            "format": 2,
            "tool": "DTLdesktop",
            "version": VERSION,
            "configuration": name,
            "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "monitors": rules,
        }

    def save(self, name: str) -> dict[str, Any]:
        name = safe_profile_name(name)
        monitors = self.desktop.monitors()
        icons = self.desktop.icons()
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        profile = self.root / name
        previous_wallpaper = None
        try:
            previous_wallpaper = read_json(profile / "wallpaper.json")
        except (OSError, json.JSONDecodeError):
            pass
        write_json(
            profile / "monitors.json",
            {
                "format": 1,
                "tool": "DTLdesktop",
                "version": VERSION,
                "saved_at": now,
                "signature": configuration_signature(monitors),
                "monitors": monitors,
            },
        )
        write_json(
            profile / "icons.json",
            {
                "format": 1,
                "tool": "DTLdesktop",
                "version": VERSION,
                "saved_at": now,
                "icons": icons,
            },
        )
        write_json(
            profile / "wallpaper.json",
            self._wallpaper_document(name, monitors, previous_wallpaper),
        )
        self.set_active_profile(name)
        return {"profile": name, "monitors": len(monitors), "icons": len(icons), "path": profile}

    def load(self, name: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        profile = self.root / safe_profile_name(name)
        try:
            return (
                read_json(profile / "monitors.json"),
                read_json(profile / "icons.json"),
                read_json(profile / "wallpaper.json"),
            )
        except (OSError, json.JSONDecodeError, KeyError) as error:
            raise DesktopError(f"Le profil « {name} » est incomplet ou illisible.") from error

    def compare(self, name: str) -> dict[str, Any]:
        saved_monitors, saved_icons, _wallpaper = self.load(name)
        current_monitors = self.desktop.monitors()
        current_icons = self.desktop.icons()
        saved_by_key = {
            (item["name"], int(item.get("occurrence", 0))): item
            for item in saved_icons.get("icons", [])
        }
        current_by_key = {
            (item["name"], int(item.get("occurrence", 0))): item for item in current_icons
        }
        moved = []
        for key in saved_by_key.keys() & current_by_key.keys():
            before, now = saved_by_key[key], current_by_key[key]
            if (int(before["x"]), int(before["y"])) != (int(now["x"]), int(now["y"])):
                moved.append(
                    {
                        "name": key[0],
                        "from": [int(now["x"]), int(now["y"])],
                        "to": [int(before["x"]), int(before["y"])],
                    }
                )
        return {
            "profile": name,
            "monitors_match": saved_monitors.get("signature")
            == configuration_signature(current_monitors),
            "moved": sorted(moved, key=lambda item: item["name"].casefold()),
            "missing": sorted(key[0] for key in saved_by_key.keys() - current_by_key.keys()),
            "new": sorted(key[0] for key in current_by_key.keys() - saved_by_key.keys()),
            "wallpapers": self.wallpaper_diagnostic(name, current_monitors),
        }

    def wallpaper_diagnostic(
        self, name: str, current_monitors: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        _saved_monitors, _icons, wallpaper = self.load(name)
        current = current_monitors or self.desktop.monitors()
        result: list[dict[str, Any]] = []
        for index, monitor in enumerate(current, 1):
            rule = self._find_wallpaper_rule(wallpaper, monitor, index)
            if rule and isinstance(rule.get("wallpaper"), dict):
                values = rule["wallpaper"]
                expected = str(values.get(orientation_rule_key(monitor["orientation"]), ""))
            else:
                expected = str(wallpaper.get("path", ""))
            observed = str(monitor.get("wallpaper", ""))
            result.append(
                {
                    "screen": index,
                    "id": str(monitor.get("id", monitor["device"])),
                    "resolution": f"{monitor['width']}x{monitor['height']}",
                    "orientation": monitor["orientation"],
                    "expected": expected,
                    "observed": observed,
                    "conform": comparable_path(expected) == comparable_path(observed),
                }
            )
        return result

    def apply_expected_wallpapers(self, name: str) -> dict[str, Any]:
        saved_monitors, _icons, _wallpaper = self.load(name)
        position = wallpaper_position_for_monitors(saved_monitors.get("monitors", []))
        current = self.desktop.monitors()
        diagnostic = self.wallpaper_diagnostic(name, current)
        assignments = [
            {"id": item["id"], "path": item["expected"]}
            for item in diagnostic
            if item["expected"]
        ]
        if not assignments:
            self.desktop.ensure_wallpaper_position(position)
            return {"applied": 0, "missing": []}
        return self.desktop.apply_wallpapers(assignments, position)

    def configure_wallpapers(
        self, name: str, screen: int, landscape: str, portrait: str
    ) -> None:
        saved_monitors, _icons, wallpaper = self.load(name)
        current = self.desktop.monitors()
        if not 1 <= screen <= len(current):
            raise ValueError("Le numéro d'écran est invalide.")
        for path in (landscape, portrait):
            if path and not Path(path).is_file():
                raise ValueError(f"Le fichier est introuvable : {path}")
        if int(wallpaper.get("format", 1)) < 2:
            wallpaper = self._wallpaper_document(name, current, wallpaper)
        monitor = current[screen - 1]
        rule = self._find_wallpaper_rule(wallpaper, monitor, screen)
        if rule is None:
            wallpaper = self._wallpaper_document(name, current, wallpaper)
            rule = self._find_wallpaper_rule(wallpaper, monitor, screen)
        if rule is None:
            raise DesktopError("Impossible d'associer le fond d'écran au moniteur.")
        rule["wallpaper"] = {"landscape": landscape, "portrait": portrait}
        wallpaper["version"] = VERSION
        wallpaper["configuration"] = name
        wallpaper["saved_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        write_json(self.root / name / "wallpaper.json", wallpaper)
        saved_monitors.update(
            {
                "version": VERSION,
                "saved_at": wallpaper["saved_at"],
                "signature": configuration_signature(current),
                "monitors": current,
            }
        )
        write_json(self.root / name / "monitors.json", saved_monitors)
        self.set_active_profile(name)

    def restore(self, name: str) -> dict[str, Any]:
        monitors, icons, _wallpaper = self.load(name)
        match = profile_matches_monitors(monitors, self.desktop.monitors())
        result = self.desktop.restore_icons(icons.get("icons", []))
        wallpaper_result = self.apply_expected_wallpapers(name)
        self.set_active_profile(name)
        result.update(
            {
                "profile": name,
                "monitors_match": match,
                "wallpaper_restored": wallpaper_result["applied"],
                "wallpaper_missing": wallpaper_result["missing"],
            }
        )
        return result

    def restore_icons_only(self, name: str) -> dict[str, Any]:
        _monitors, icons, _wallpaper = self.load(name)
        result = self.desktop.restore_icons(icons.get("icons", []))
        result["profile"] = name
        return result

    def display_change_count(self, name: str) -> int:
        saved_monitors, _icons, _wallpaper = self.load(name)
        current = {
            str(item["device"]): item for item in self.desktop.monitors()
        }
        changed = 0
        for target in saved_monitors.get("monitors", []):
            now = current.get(str(target.get("device", "")))
            if now is None:
                changed += 1
                continue
            target_rotation = int(
                target.get(
                    "rotation",
                    1
                    if str(target.get("orientation", "")).casefold() == "portrait"
                    else 0,
                )
            )
            if (
                int(now.get("rotation", 0)) != target_rotation
                or int(now["width"]) != int(target["width"])
                or int(now["height"]) != int(target["height"])
                or int(now["left"]) != int(target["left"])
                or int(now["top"]) != int(target["top"])
            ):
                changed += 1
        return changed

    def apply_profile(self, name: str) -> dict[str, Any]:
        saved_monitors, saved_icons, _wallpaper = self.load(name)
        target_modes = saved_monitors.get("monitors", [])
        target_signature = saved_monitors.get(
            "signature", configuration_signature(target_modes)
        )
        previous_monitors = self.desktop.monitors()
        previous_signature = configuration_signature(previous_monitors)
        previous_modes = self.desktop.display_modes()
        previous_icons = self.desktop.icons()
        previous_position = self.desktop.wallpaper_position()
        previous_wallpapers = [
            {
                "id": str(item.get("id", item["device"])),
                "path": str(item.get("wallpaper", "")),
            }
            for item in previous_monitors
            if item.get("wallpaper")
        ]
        display_changed = previous_signature != target_signature
        try:
            if display_changed:
                self.desktop.set_display_modes(target_modes)
                if not self.desktop.wait_for_configuration(target_signature):
                    raise DesktopError(
                        "La nouvelle orientation n'a pas été confirmée par Windows."
                    )
                time.sleep(1.0)

            wallpaper_result = self.apply_expected_wallpapers(name)
            icon_result = self.desktop.restore_icons(saved_icons.get("icons", []))
            current = self.desktop.monitors()
            display_valid = configuration_signature(current) == target_signature
            wallpaper_status = self.wallpaper_diagnostic(name, current)
            wallpaper_valid = all(item["conform"] for item in wallpaper_status)
            expected_position = wallpaper_position_for_monitors(target_modes)
            framing_valid = self.desktop.wallpaper_position() == expected_position
            if not display_valid or not wallpaper_valid or not framing_valid:
                details = []
                if not display_valid:
                    details.append("orientation ou résolution non conforme")
                if not wallpaper_valid:
                    details.append("fond d'écran non conforme")
                if not framing_valid:
                    details.append("cadrage du fond d'écran non conforme")
                raise DesktopError(", ".join(details))
            self.set_active_profile(name)
            return {
                "profile": name,
                "display_changed": display_changed,
                "wallpapers": wallpaper_result["applied"],
                "icons": icon_result["restored"],
                "missing_icons": icon_result["missing"],
            }
        except Exception as error:
            rollback_ok = True
            try:
                self.desktop.set_display_modes(previous_modes)
                rollback_ok = self.desktop.wait_for_configuration(previous_signature)
                if previous_wallpapers:
                    self.desktop.apply_wallpapers(previous_wallpapers, previous_position)
                self.desktop.restore_icons(previous_icons)
            except Exception:
                rollback_ok = False
            status = (
                "La configuration précédente a été restaurée."
                if rollback_ok
                else "Le retour automatique n'a pas pu être entièrement validé."
            )
            raise DesktopError(
                f"La nouvelle configuration n'a pas pu être validée : {error} {status}"
            ) from error

    def recognized_profile(self) -> str | None:
        current = self.desktop.monitors()
        active = self.active_profile()
        profiles = self.list_profiles()
        exact: list[str] = []
        compatible: list[str] = []
        current_signature = configuration_signature(current)
        for name in profiles:
            try:
                monitors, _icons, _wallpaper = self.load(name)
            except DesktopError:
                continue
            if monitors.get("signature") == current_signature:
                exact.append(name)
            elif profile_matches_monitors(monitors, current):
                compatible.append(name)
        if exact:
            orientation_name = suggested_profile_name(current)
            if orientation_name in exact:
                return orientation_name
            return active if active in exact else exact[0]
        if compatible:
            return active if active in compatible else compatible[0]
        return None


def print_configuration(monitors: list[dict[str, Any]]) -> None:
    color = supports_color()
    title = console_style("Configuration détectée", ANSI_BOLD, color)
    print(f"\n{title}\n")
    for index, monitor in enumerate(monitors, 1):
        primary = " (principal)" if monitor.get("primary") else ""
        print(f"Moniteur {index}{primary}")
        print(green_value(f"{monitor['width']}x{monitor['height']}", color))
        print(green_value(monitor["orientation"], color))
        print()
    ordered = sorted(range(len(monitors)), key=lambda i: (monitors[i]["left"], monitors[i]["top"]))
    print("Disposition")
    print(green_value(" | ".join(str(index + 1) for index in ordered), color))


def print_comparison(result: dict[str, Any]) -> None:
    print(f"\nProfil : {result['profile']}")
    print("Écrans : " + ("identiques" if result["monitors_match"] else "différents"))
    print(f"Icônes déplacées : {len(result['moved'])}")
    print(f"Icônes absentes : {len(result['missing'])}")
    print(f"Nouvelles icônes : {len(result['new'])}")
    wallpaper_differences = sum(
        1 for item in result.get("wallpapers", []) if not item["conform"]
    )
    print(f"Fonds d'écran incohérents : {wallpaper_differences}")
    if result["moved"] or wallpaper_differences:
        print("\nRestauration possible, sans modification effectuée.")
    elif not result["missing"] and not result["new"]:
        print("\nDifférence : aucune")


def wallpaper_name(path: str) -> str:
    return Path(path).name if path else "(non défini)"


def print_wallpaper_diagnostic(items: list[dict[str, Any]]) -> None:
    print("\nDiagnostic des fonds d'écran")
    for item in items:
        print("\n" + "-" * min(65, terminal_width()))
        print(f"\nÉcran {item['screen']}")
        print(f"{item['resolution']} {str(item['orientation']).casefold()}")
        print(f"\nFond :\n{wallpaper_name(item['observed'])}")
        if item["conform"]:
            print("\n✓ conforme")
        else:
            print("\n⚠ fond d'écran incohérent")
            print(f"\nAttendu :\n{wallpaper_name(item['expected'])}")
            print(f"\nObservé :\n{wallpaper_name(item['observed'])}")


def choose_profile(manager: DesktopManager, prompt: str) -> str | None:
    profiles = manager.list_profiles()
    if not profiles:
        print("\nAucun profil enregistré.")
        return None
    print()
    for index, profile in enumerate(profiles, 1):
        print(f"{index}. {profile}")
    answer = colored_input(f"\n{prompt} [1-{len(profiles)}] : ").strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(profiles):
        print("Choix annulé.")
        return None
    return profiles[int(answer) - 1]


def configure_wallpapers_interactive(manager: DesktopManager) -> None:
    profile = choose_profile(manager, "Profil à configurer")
    if not profile:
        return
    monitors = manager.desktop.monitors()
    _saved_monitors, _icons, wallpaper = manager.load(profile)
    print(f"\nConfiguration : {profile}\n")
    for index, monitor in enumerate(monitors, 1):
        print(f"{index}. Écran {index} — {monitor['width']}x{monitor['height']} "
              f"{str(monitor['orientation']).casefold()}")
    answer = colored_input(f"\nÉcran à configurer [1-{len(monitors)}] : ").strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(monitors):
        print("Configuration annulée.")
        return
    screen = int(answer)
    monitor = monitors[screen - 1]
    rule = manager._find_wallpaper_rule(wallpaper, monitor, screen) or {}
    values = rule.get("wallpaper", {}) if isinstance(rule.get("wallpaper"), dict) else {}
    global_default = str(wallpaper.get("path", monitor.get("wallpaper", "")))
    landscape = str(values.get("landscape", global_default))
    portrait = str(values.get("portrait", global_default))
    last_directory = manager.last_image_directory()
    print(f"\nÉcran {screen}")
    print("\nSélectionnez maintenant le fond paysage dans l'Explorateur Windows.")
    selected_landscape = choose_wallpaper_file(
        f"DTLdesktop — Fond paysage de l'écran {screen}",
        landscape,
        last_directory,
    )
    new_landscape = selected_landscape or landscape
    if selected_landscape:
        manager.set_last_image_directory(selected_landscape)
        last_directory = str(Path(selected_landscape).parent)
        print(f"Fond paysage : {wallpaper_name(new_landscape)}")
    else:
        print("Sélection annulée : le fond paysage actuel est conservé.")

    print("\nSélectionnez maintenant le fond portrait dans l'Explorateur Windows.")
    selected_portrait = choose_wallpaper_file(
        f"DTLdesktop — Fond portrait de l'écran {screen}",
        portrait,
        last_directory,
    )
    new_portrait = selected_portrait or portrait
    if selected_portrait:
        manager.set_last_image_directory(selected_portrait)
        print(f"Fond portrait : {wallpaper_name(new_portrait)}")
    else:
        print("Sélection annulée : le fond portrait actuel est conservé.")
    manager.configure_wallpapers(profile, screen, new_landscape, new_portrait)
    print("\nRègles enregistrées.")
    print(f"Paysage : {wallpaper_name(new_landscape)}")
    print(f"Portrait : {wallpaper_name(new_portrait)}")


def select_current_wallpapers_interactive(
    manager: DesktopManager,
    monitors: list[dict[str, Any]],
    configuration: str,
) -> None:
    print(f"\nConfiguration sélectionnée : {green_value(configuration)}")
    print("Choisissez le fond de chaque écran.")
    last_directory = manager.last_image_directory()
    assignments: list[dict[str, str]] = []
    for index, monitor in enumerate(monitors, 1):
        current = str(monitor.get("wallpaper", ""))
        selected = choose_wallpaper_file(
            f"DTLdesktop — {configuration} — Fond de l'écran {index}",
            current,
            last_directory,
        )
        if selected:
            manager.set_last_image_directory(selected)
            last_directory = str(Path(selected).parent)
            assignments.append(
                {
                    "id": str(monitor.get("id", monitor["device"])),
                    "path": selected,
                }
            )
            print(f"Écran {index} : {wallpaper_name(selected)}")
        else:
            print(f"Écran {index} : sélection annulée, fond actuel conservé.")
    if not assignments:
        print("\nAucun fond n'a été modifié.")
        return
    position = wallpaper_position_for_monitors(monitors)
    result = manager.desktop.apply_wallpapers(assignments, position)
    print(f"\n{result['applied']} fond(s) appliqué(s).")
    print(f"Appuyez sur S pour enregistrer « {configuration} ».")


def interactive(manager: DesktopManager) -> int:
    show_application_header()
    try:
        monitors = manager.desktop.monitors()
        print_configuration(monitors)
        recognized = manager.recognized_profile()
        selected_profile = recognized or suggested_profile_name(monitors)
        if recognized:
            print(f"\nConfiguration sélectionnée : {green_value(selected_profile)}")
        else:
            print("\nNouvelle configuration")
            print(f"Configuration sélectionnée : {green_value(selected_profile)}")
        while True:
            print("\n[A] Appliquer un profil")
            print("[S] Sauvegarder le profil actuel")
            print("[R] Restaurer les icônes  [D] Diagnostiquer")
            print("[T] Tester                [C] Comparer")
            print("[F] Choisir les fonds     [Q] Quitter")
            choice = colored_input("\nVotre choix : ").strip().upper()
            if choice == "Q":
                return 0
            if choice == "S":
                result = manager.save(selected_profile)
                print(
                    f"\nConfiguration « {result['profile']} » enregistrée : "
                    f"{result['icons']} icône(s), {result['monitors']} écran(s)."
                )
            elif choice in {"T", "C"}:
                profile = choose_profile(manager, "Profil à tester")
                if profile:
                    print("\nSimulation — aucune modification")
                    print_comparison(manager.compare(profile))
            elif choice == "D":
                current = manager.desktop.monitors()
                print_configuration(current)
                profile = selected_profile if selected_profile in manager.list_profiles() else None
                if profile:
                    print(f"\nConfiguration reconnue : {profile}")
                    diagnostic = manager.wallpaper_diagnostic(profile, current)
                    print_wallpaper_diagnostic(diagnostic)
                    if any(not item["conform"] for item in diagnostic):
                        if colored_input("\nCorriger les fonds d'écran ? O/N : ").strip().upper() == "O":
                            result = manager.apply_expected_wallpapers(profile)
                            print(f"\n{result['applied']} fond(s) d'écran corrigé(s).")
                else:
                    print("\nNouvelle configuration")
                    print("Voulez-vous créer un nouveau profil ? Utilisez S.")
            elif choice == "F":
                select_current_wallpapers_interactive(
                    manager, manager.desktop.monitors(), selected_profile
                )
            elif choice == "R":
                profile = choose_profile(manager, "Profil dont les icônes seront restaurées")
                if profile:
                    preview = manager.compare(profile)
                    print_comparison(preview)
                    if colored_input("\nConfirmer la restauration ? O/N : ").strip().upper() == "O":
                        result = manager.restore_icons_only(profile)
                        selected_profile = profile
                        print(f"\n{result['restored']} icône(s) restaurée(s).")
                        if result["missing"]:
                            print(f"{len(result['missing'])} icône(s) du profil sont absentes.")
                    else:
                        print("Restauration annulée.")
            elif choice == "A":
                profile = choose_profile(manager, "Profil à appliquer")
                if profile:
                    changes = manager.display_change_count(profile)
                    print(
                        f"\nLe profil « {profile} » va modifier l'orientation "
                        f"ou la disposition de {changes} écran(s)."
                    )
                    if colored_input("\nContinuer ? O/N : ").strip().upper() == "O":
                        try:
                            print("\nApplication du profil en cours…")
                            result = manager.apply_profile(profile)
                            selected_profile = profile
                            print(f"\nProfil « {profile} » appliqué et vérifié.")
                            print(
                                f"{result['wallpapers']} fond(s) et "
                                f"{result['icons']} icône(s) restaurés."
                            )
                        except DesktopError as error:
                            print(f"\nErreur : {error}")
                    else:
                        print("Application annulée.")
            else:
                print("Choix non reconnu.")
    except (DesktopError, OSError, ValueError) as error:
        print(f"\nErreur : {error}", file=sys.stderr)
        return 1


def run_auto(manager: DesktopManager) -> int:
    try:
        profile = manager.recognized_profile()
        if not profile:
            print("Nouvelle configuration : aucun profil compatible.")
            return 2
        print(f"Configuration reconnue : {profile}")
        result = manager.apply_profile(profile)
        print(
            f"Restauration automatique : {result['icons']} icône(s), "
            f"{result['wallpapers']} fond(s) d'écran."
        )
        return 0
    except (DesktopError, OSError, ValueError) as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestionnaire de configurations du bureau Windows")
    parser.add_argument("--auto", action="store_true", help="restaure le profil reconnu")
    parser.add_argument(
        "--save",
        action="store_true",
        help="enregistre la configuration détectée sans demander de nom",
    )
    parser.add_argument("--restore", metavar="PROFIL", help="restaure un profil")
    parser.add_argument(
        "--apply",
        metavar="PROFIL",
        help="applique orientation, résolution, fonds et icônes d'un profil",
    )
    parser.add_argument("--test", metavar="PROFIL", help="simule une restauration")
    parser.add_argument("--diagnose", action="store_true", help="affiche la configuration détectée")
    parser.add_argument("--version", action="version", version=f"DTLdesktop {VERSION}")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_console_encoding()
    args = build_parser().parse_args(argv)
    manager = DesktopManager()
    try:
        if args.auto:
            return run_auto(manager)
        if args.save:
            monitors = manager.desktop.monitors()
            selected = manager.recognized_profile() or suggested_profile_name(monitors)
            result = manager.save(selected)
            print(
                f"Configuration « {result['profile']} » enregistrée "
                f"({result['icons']} icône(s))."
            )
            return 0
        if args.restore:
            result = manager.restore_icons_only(args.restore)
            print(f"{result['restored']} icône(s) restaurée(s).")
            return 0
        if args.apply:
            result = manager.apply_profile(args.apply)
            print(
                f"Profil « {result['profile']} » appliqué : "
                f"{result['wallpapers']} fond(s), {result['icons']} icône(s)."
            )
            return 0
        if args.test:
            print("Simulation — aucune modification")
            print_comparison(manager.compare(args.test))
            return 0
        if args.diagnose:
            current = manager.desktop.monitors()
            print_configuration(current)
            profile = manager.recognized_profile()
            if profile:
                print(f"\nConfiguration reconnue : {profile}")
                print_wallpaper_diagnostic(manager.wallpaper_diagnostic(profile, current))
            else:
                print("\nNouvelle configuration")
            return 0
        return interactive(manager)
    except (DesktopError, OSError, ValueError) as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
