import tkinter as tk
from tkinter import colorchooser, ttk, simpledialog
import ctypes
from ctypes import wintypes
MISSING_PACKAGES = []
try:
    import mss
except Exception:
    mss = None
    MISSING_PACKAGES.append("mss")
import math
import time
import datetime
import json
import os
import sys
import threading
import random
import subprocess
try:
    import cv2
except Exception:
    cv2 = None
    MISSING_PACKAGES.append("opencv-python")
try:
    import numpy as np
except Exception:
    np = None
    MISSING_PACKAGES.append("numpy")

def get_refresh_hz():
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        hz = int(ctypes.windll.gdi32.GetDeviceCaps(hdc, 116))
        ctypes.windll.user32.ReleaseDC(0, hdc)
        if hz < 30:
            hz = 60
        return max(30, min(360, hz))
    except Exception:
        return 60


REFRESH_HZ = get_refresh_hz()
FRAME_DT = 1.0 / float(REFRESH_HZ)

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
LWA_COLORKEY = 0x00000001
LWA_ALPHA = 0x00000002
WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011

VK_INSERT = 0x2D
VK_HOME = 0x24
VK_END = 0x23
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_DELETE = 0x2E

KEY_CODE_BY_NAME = {
    "LBUTTON": 0x01, "RBUTTON": 0x02, "MBUTTON": 0x04,
    "XBUTTON1": 0x05, "XBUTTON2": 0x06,
    "BACKSPACE": 0x08, "TAB": 0x09, "ENTER": 0x0D,
    "SHIFT": 0x10, "CTRL": 0x11, "ALT": 0x12, "CAPSLOCK": 0x14,
    "ESC": 0x1B, "SPACE": 0x20,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22, "END": 0x23, "HOME": 0x24,
    "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
    "PRINTSCREEN": 0x2C, "INSERT": 0x2D, "DELETE": 0x2E,
    "LWIN": 0x5B, "RWIN": 0x5C, "APPS": 0x5D,
    "NUM0": 0x60, "NUM1": 0x61, "NUM2": 0x62, "NUM3": 0x63, "NUM4": 0x64,
    "NUM5": 0x65, "NUM6": 0x66, "NUM7": 0x67, "NUM8": 0x68, "NUM9": 0x69,
    "NUM*": 0x6A, "NUM+": 0x6B, "NUM-": 0x6D, "NUM.": 0x6E, "NUM/": 0x6F,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "F13": 0x7C, "F14": 0x7D, "F15": 0x7E, "F16": 0x7F,
    "F17": 0x80, "F18": 0x81, "F19": 0x82, "F20": 0x83,
    "F21": 0x84, "F22": 0x85, "F23": 0x86, "F24": 0x87,
    "NUMLOCK": 0x90, "SCROLLLOCK": 0x91,
    "LSHIFT": 0xA0, "RSHIFT": 0xA1, "LCTRL": 0xA2, "RCTRL": 0xA3,
    "LALT": 0xA4, "RALT": 0xA5,
    ";": 0xBA, "=": 0xBB, ",": 0xBC, "-": 0xBD, ".": 0xBE, "/": 0xBF, "`": 0xC0,
    "[": 0xDB, "\\": 0xDC, "]": 0xDD, "'": 0xDE,
}
for _i, _ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    KEY_CODE_BY_NAME[_ch] = 0x41 + _i
for _i in range(10):
    KEY_CODE_BY_NAME[str(_i)] = 0x30 + _i
KEY_NAME_BY_CODE = {v: k for k, v in KEY_CODE_BY_NAME.items()}
KEY_NAME_BY_CODE[0x10] = "SHIFT"
KEY_NAME_BY_CODE[0x11] = "CTRL"
KEY_NAME_BY_CODE[0x12] = "ALT"

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(_BASE_DIR, "nautical_configs")
CONFIG_PATH = os.path.join(_BASE_DIR, "nautical_config.json")
PLAYTIME_PATH = os.path.join(CONFIG_DIR, "playtime.json")
STARTUP_REG_NAME = "NauticalUI"
APP_VERSION = "1.0.0"
UPDATE_URL = "https://raw.githubusercontent.com/NauticalHazard/NauticalUI/main/NauticalUI.py"


def _version_tuple(v):
    import re
    return tuple(int(x) for x in re.findall(r"\d+", str(v)))


def _fetch_remote_update():
    import re
    import urllib.request
    req = urllib.request.Request(UPDATE_URL, headers={"User-Agent": "NauticalUI-Updater"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    text = data.decode("utf-8")
    m = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', text, re.M)
    return data, text, (m.group(1) if m else None)

def load_show_console_pref():
    try:
        if os.path.isfile(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return bool(data.get("show_console", False))
    except Exception:
        pass
    return False

def set_console_visible(visible):
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            return False
        hwnd = int(hwnd)
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if visible:
            style = (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            user32.ShowWindow(hwnd, 5)
        else:
            style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            user32.ShowWindow(hwnd, 0)
        return True
    except Exception:
        return False

def hide_console_window():
    set_console_visible(False)

INSTANCE_MUTEX = "Local\\NauticalUI_Singleton"
INSTANCE_SHOW_EVENT = "Local\\NauticalUI_Show"
ERROR_ALREADY_EXISTS = 183

def _instance_handles():
    k32 = ctypes.windll.kernel32
    k32.CreateMutexW.restype = wintypes.HANDLE
    k32.CreateEventW.restype = wintypes.HANDLE
    mutex = k32.CreateMutexW(None, False, INSTANCE_MUTEX)
    already = k32.GetLastError() == ERROR_ALREADY_EXISTS
    event = k32.CreateEventW(None, True, False, INSTANCE_SHOW_EVENT)
    return mutex, event, already

def request_existing_instance_show():
    k32 = ctypes.windll.kernel32
    k32.CreateEventW.restype = wintypes.HANDLE
    event = k32.CreateEventW(None, True, False, INSTANCE_SHOW_EVENT)
    if event:
        k32.SetEvent(event)
    return True

def relaunch_detached():
    if os.name != "nt":
        return False
    if "--detached" in sys.argv or os.environ.get("NAUTICAL_DETACHED") == "1":
        return False
    script = os.path.abspath(__file__)
    exe = sys.executable
    wexe = exe.lower().replace("python.exe", "pythonw.exe")
    if wexe != exe.lower() and os.path.isfile(wexe):
        exe = exe[:-len("python.exe")] + "pythonw.exe" if exe.lower().endswith("python.exe") else wexe
    flags = 0x00000008 | 0x00000200 | 0x08000000
    env = os.environ.copy()
    env["NAUTICAL_DETACHED"] = "1"
    args = [exe, script, "--detached"]
    try:
        subprocess.Popen(args, env=env, close_fds=True, creationflags=flags)
        return True
    except Exception:
        return False

IDLE_PRIORITY_CLASS = 0x00000040
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
NORMAL_PRIORITY_CLASS = 0x00000020
ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
HIGH_PRIORITY_CLASS = 0x00000080

CPU_PRIORITY_MAP = {
    "Low": IDLE_PRIORITY_CLASS,
    "Below Normal": BELOW_NORMAL_PRIORITY_CLASS,
    "Normal": NORMAL_PRIORITY_CLASS,
    "Above Normal": ABOVE_NORMAL_PRIORITY_CLASS,
    "High": HIGH_PRIORITY_CLASS,
}

def apply_cpu_priority(name):
    value = CPU_PRIORITY_MAP.get(str(name), NORMAL_PRIORITY_CLASS)
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetCurrentProcess()
        return bool(kernel32.SetPriorityClass(handle, int(value)))
    except Exception:
        return False

def _pythonw_executable():

    import sys
    exe = sys.executable or ""
    lower = exe.lower()
    if lower.endswith("python.exe"):
        cand = exe[:-10] + "pythonw.exe"
        if os.path.isfile(cand):
            return cand
    return exe

def is_start_with_windows_enabled():
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        ) as key:
            winreg.QueryValueEx(key, STARTUP_REG_NAME)
            return True
    except OSError:
        return False
    except Exception:
        return False

def set_start_with_windows(enabled):
    import winreg
    script = os.path.abspath(__file__)
    pyw = _pythonw_executable()
    cmd = f'"{pyw}" "{script}"'
    path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
    ) as key:
        if enabled:
            winreg.SetValueEx(key, STARTUP_REG_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, STARTUP_REG_NAME)
            except FileNotFoundError:
                pass
            except OSError:
                pass

C_BG = "#000000"
C_CARD = "#10151c"
C_CARD2 = "#181e28"
C_ACCENT = "#3b9eff"
C_ACCENT_DIM = "#2a7acc"
C_TEXT = "#e8eef7"
C_MUTED = "#7d8799"
C_TRACK = "#252c3a"
C_BORDER = "#222833"
C_SUCCESS = "#3dd68c"
C_DANGER = "#ff6b6b"

UI_TEXT = "#ffffff"
UI_MUTED = "#ffffff"

THEMES = {
    "Default": {
        "bg": "#000000", "card": "#2a2a2a", "card2": "#363636",
        "accent": "#a6a6a6", "accent_dim": "#858585",
        "text": "#ffffff", "muted": "#b0b0b0",
        "track": "#474747", "border": "#525252",
        "success": "#3dd68c", "danger": "#ff6b6b",
        "title": "#ffffff",
    },
    "Ocean": {
        "bg": "#07090d", "card": "#10151c", "card2": "#181e28",
        "accent": "#3b9eff", "accent_dim": "#2a7acc",
        "text": "#e8eef7", "muted": "#7d8799",
        "track": "#252c3a", "border": "#222833",
        "success": "#3dd68c", "danger": "#ff6b6b",
    },
    "Crimson": {
        "bg": "#120505", "card": "#1f0a0a", "card2": "#2e1010",
        "accent": "#ff1a1a", "accent_dim": "#cc0000",
        "text": "#ffe8e8", "muted": "#b07070",
        "track": "#4a1515", "border": "#3d1212",
        "success": "#3dd68c", "danger": "#ff4444",
    },
    "Matrix": {
        "bg": "#050a05", "card": "#0a140a", "card2": "#0f1c0f",
        "accent": "#00b84a", "accent_dim": "#00963c",
        "text": "#e8ffe8", "muted": "#5a9a5a",
        "track": "#153a15", "border": "#123d12",
        "success": "#3dd68c", "danger": "#ff6b6b",
    },
    "Cherry Blossom": {
        "bg": "#12080d", "card": "#1a0e14", "card2": "#2a1620",
        "accent": "#ff7eb3", "accent_dim": "#e85a96",
        "text": "#ffe8f2", "muted": "#c0809a",
        "track": "#4a2035", "border": "#3d1a2c",
        "success": "#3dd68c", "danger": "#ff6b6b",
    },
    "Void": {
        "bg": "#07060b", "card": "#100e16", "card2": "#18151f",
        "accent": "#8b5cf6", "accent_dim": "#6d28d9",
        "text": "#eee8ff", "muted": "#7a7290",
        "track": "#2a2040", "border": "#221c30",
        "success": "#3dd68c", "danger": "#ff6b6b",
    },
}

def _mix_rgb(a, b, amt):
    a = parse_rgb(a)
    b = parse_rgb(b)
    return tuple(int(a[i] * (1.0 - amt) + b[i] * amt) for i in range(3))

def build_custom_theme(bg, fg):
    bg = parse_rgb(bg, (28, 28, 28))
    fg = parse_rgb(fg, (255, 26, 26))
    card2 = _mix_rgb(bg, (255, 255, 255), 0.08)
    track = _mix_rgb(bg, (255, 255, 255), 0.16)
    border = _mix_rgb(bg, (255, 255, 255), 0.20)
    dim = tuple(max(0, min(255, int(c * 0.72))) for c in fg)
    return {
        "bg": "#000000",
        "card": rgb_hex(bg),
        "card2": rgb_hex(card2),
        "accent": rgb_hex(fg),
        "accent_dim": rgb_hex(dim),
        "text": "#ffffff",
        "muted": "#ffffff",
        "track": rgb_hex(track),
        "border": rgb_hex(border),
        "success": "#3dd68c",
        "danger": "#ff6b6b",
    }

def _set_theme_globals(theme_name, custom=None):
    global C_BG, C_CARD, C_CARD2, C_ACCENT, C_ACCENT_DIM
    global C_TEXT, C_MUTED, C_TRACK, C_BORDER, C_SUCCESS, C_DANGER
    if theme_name == "Custom":
        t = custom or build_custom_theme((32, 32, 32), (255, 26, 26))
    else:
        t = THEMES.get(theme_name) or THEMES["Ocean"]
    C_BG = "#000000"
    C_CARD = t["card"]
    C_CARD2 = t["card2"]
    C_ACCENT = t["accent"]
    C_ACCENT_DIM = t["accent_dim"]
    C_TEXT = t["text"]
    C_MUTED = t["muted"]
    C_TRACK = t["track"]
    C_BORDER = t["border"]
    C_SUCCESS = t["success"]
    C_DANGER = t["danger"]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_cursor_pos():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def move_mouse(dx, dy):
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)

def click_left():
    user32 = ctypes.windll.user32
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def mouse_left_down():
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

def mouse_left_up():
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def move_cursor_to_position(target_x, target_y, current_x, current_y, factor=1.0, scale=1.0, method="Relative"):
    factor = max(0.0, min(1.0, float(factor)))
    scale = max(0.1, float(scale))
    dx = (target_x - current_x) * factor * scale
    dy = (target_y - current_y) * factor * scale
    mx, my = int(round(dx)), int(round(dy))
    if mx == 0 and my == 0 and (abs(dx) > 0.01 or abs(dy) > 0.01):
        mx = 1 if dx > 0 else (-1 if dx < 0 else 0)
        my = 1 if dy > 0 else (-1 if dy < 0 else 0)
        if abs(dx) >= abs(dy):
            my = 0 if abs(dx) > abs(dy) * 2 else my
        else:
            mx = 0 if abs(dy) > abs(dx) * 2 else mx
    if mx or my:
        move_mouse(mx, my)

_user32 = ctypes.windll.user32
_GetAsyncKeyState = _user32.GetAsyncKeyState
try:
    _MORPH_KERNEL = np.ones((3, 3), np.uint8)
except Exception:
    _MORPH_KERNEL = None
_NAMED_RGB = {
    "white": (255, 255, 255), "red": (255, 0, 0), "lime": (0, 255, 0),
    "blue": (0, 0, 255), "black": (0, 0, 0), "green": (0, 255, 0),
}


def parse_rgb(value, default=(255, 255, 255)):
    try:
        if isinstance(value, (tuple, list)) and len(value) >= 3:
            return (
                max(0, min(255, int(value[0]))),
                max(0, min(255, int(value[1]))),
                max(0, min(255, int(value[2]))),
            )
        s = str(value).strip().lower()
        if s in _NAMED_RGB:
            return _NAMED_RGB[s]
        if s.startswith("#") and len(s) == 7:
            return int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16)
        parts = s.replace(" ", "").split(",")
        if len(parts) == 3:
            return (
                max(0, min(255, int(parts[0]))),
                max(0, min(255, int(parts[1]))),
                max(0, min(255, int(parts[2]))),
            )
    except Exception:
        pass
    return default


def rgb_hex(rgb):
    r, g, b = parse_rgb(rgb)
    return "#%02x%02x%02x" % (r, g, b)


def rgb_text(rgb):
    r, g, b = parse_rgb(rgb)
    return "%d, %d, %d" % (r, g, b)

def get_key_state(key_code):
    return _GetAsyncKeyState(key_code)

def precompute_color_ranges(target_colors, tolerance):
    ranges = []
    t = int(tolerance)
    for color in target_colors or ():
        lower = np.array(
            [max(0, int(color[0]) - t), max(0, int(color[1]) - t), max(0, int(color[2]) - t)],
            dtype=np.uint8,
        )
        upper = np.array(
            [min(255, int(color[0]) + t), min(255, int(color[1]) + t), min(255, int(color[2]) + t)],
            dtype=np.uint8,
        )
        ranges.append((lower, upper))
    return ranges

def build_color_mask(img, target_colors, tolerance, ranges=None):
    if ranges is None:
        ranges = precompute_color_ranges(target_colors, tolerance)
    mask = None
    for lower, upper in ranges:
        m = cv2.inRange(img, lower, upper)
        mask = m if mask is None else cv2.bitwise_or(mask, m)
    return mask

def select_priority_mask(mask, img_rgb, priority, target_colors, min_area=12, last_xy=None):
    if not priority or priority == "none":
        return mask
    if mask is None or not np.any(mask):
        return mask
    try:
        m = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _MORPH_KERNEL, iterations=1)
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    except Exception:
        return mask
    usable = []
    for cnt in contours:
        if cv2.contourArea(cnt) >= min_area:
            usable.append(cnt)
    if not usable:
        return mask
    if len(usable) == 1:
        out = np.zeros_like(mask)
        cv2.drawContours(out, [usable[0]], -1, 255, -1)
        return out

    h, w = mask.shape[:2]
    cx, cy = w * 0.5, h * 0.5
    colors = list(target_colors) if target_colors else []
    blobs = []
    for cnt in usable:
        moments = cv2.moments(cnt)
        if moments["m00"] <= 0:
            continue
        bx = moments["m10"] / moments["m00"]
        by = moments["m01"] / moments["m00"]
        if priority == "match" and img_rgb is not None:
            blob = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(blob, [cnt], -1, 255, -1)
            pixels = img_rgb[blob > 0]
            if pixels.size == 0:
                continue
            mean = pixels.mean(axis=0)
            if colors:
                score = min(
                    float((mean[0]-c[0])**2 + (mean[1]-c[1])**2 + (mean[2]-c[2])**2)
                    for c in colors
                )
            else:
                score = (bx - cx) ** 2 + (by - cy) ** 2
        else:
            score = (bx - cx) ** 2 + (by - cy) ** 2
        blobs.append((score, bx, by, cnt))
    if not blobs:
        return mask

    best_cnt = None
    if priority == "crosshair" and last_xy is not None:
        stick = max(36.0, 0.32 * float(min(w, h)))
        stick_sq = stick * stick
        lx, ly = float(last_xy[0]), float(last_xy[1])
        near_d = None
        for score, bx, by, cnt in blobs:
            d = (bx - lx) ** 2 + (by - ly) ** 2
            if d <= stick_sq and (near_d is None or d < near_d):
                near_d = d
                best_cnt = cnt
    if best_cnt is None:
        blobs.sort(key=lambda it: it[0])
        best_cnt = blobs[0][3]

    out = np.zeros_like(mask)
    cv2.drawContours(out, [best_cnt], -1, 255, -1)
    return out

def target_from_mask(mask, bbox, aim_point="center", edge_bias=0.0):
    ys, xs = np.where(mask > 0)
    if xs.size == 0:
        return None

    cx = bbox["width"] * 0.5
    cy = bbox["height"] * 0.5
    center_ax = float(xs.mean())
    center_ay = float(ys.mean())

    if aim_point == "edge":
        dx = xs.astype(np.float64) - cx
        dy = ys.astype(np.float64) - cy
        dist_sq = dx * dx + dy * dy
        i = int(np.argmin(dist_sq))
        edge_ax = float(xs[i])
        edge_ay = float(ys[i])
        t = max(0.0, min(1.0, float(edge_bias) / 10.0))
        ax = edge_ax + (center_ax - edge_ax) * t
        ay = edge_ay + (center_ay - edge_ay) * t
    elif aim_point == "head":
        y_min = float(ys.min())
        y_max = float(ys.max())
        height = max(1.0, y_max - y_min)
        band_h = max(4.0, height * 0.22)
        y_lo = y_min
        y_hi = y_min + band_h
        band = (ys >= y_lo) & (ys <= y_hi)
        if not np.any(band):
            y_hi = y_min + max(4.0, height / 3.0)
            band = (ys >= y_lo) & (ys <= y_hi)
        if np.any(band):
            ax = float(xs[band].mean())
            ay = float(ys[band].mean())
        else:
            ax = float(xs.mean())
            ay = y_min + min(8.0, height * 0.15)
    else:
        ax = center_ax
        ay = center_ay

    return (int(ax + bbox["left"]), int(ay + bbox["top"]))

def blob_bounding_boxes(mask, min_area=12, merge_gap=16, pad=4):
    try:
        m = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _MORPH_KERNEL, iterations=1)
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    except Exception:
        return []
    boxes = []
    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        boxes.append([x - pad, y - pad, x + w + pad, y + h + pad])
    if not boxes:
        return []
    merged = True
    while merged:
        merged = False
        out = []
        used = [False] * len(boxes)
        for i, a in enumerate(boxes):
            if used[i]:
                continue
            ax1, ay1, ax2, ay2 = a
            for j in range(i + 1, len(boxes)):
                if used[j]:
                    continue
                bx1, by1, bx2, by2 = boxes[j]
                if (ax1 - merge_gap <= bx2 and ax2 + merge_gap >= bx1 and
                        ay1 - merge_gap <= by2 and ay2 + merge_gap >= by1):
                    ax1, ay1 = min(ax1, bx1), min(ay1, by1)
                    ax2, ay2 = max(ax2, bx2), max(ay2, by2)
                    used[j] = True
                    merged = True
            used[i] = True
            out.append((ax1, ay1, ax2, ay2))
        boxes = [list(b) for b in out]
    return [tuple(b) for b in boxes]

class ColorTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry("760x510")
        self.root.configure(bg="#000000", highlightthickness=0, bd=0)
        try:
            self.root["highlightthickness"] = 0
        except Exception:
            pass
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.target_colors = []
        self.tracking = False
        self.aimbot_enabled = True
        self.ui_visible = True
        self.always_on_top = True
        self.start_with_windows = bool(is_start_with_windows_enabled())
        self.minimize_to_tray = True
        self.cpu_priority = "Normal"
        self.show_console = bool(load_show_console_pref())
        self.playtime_seconds = 0.0
        self.first_used = ""
        self.last_used = ""
        self.session_count = 0
        self._session_start = time.time()
        self._play_accounted = self._session_start
        self._play_flush_t = time.time()
        self._load_playtime_file()
        self.streamproof = True
        self.dark_background = True
        self.listening_keybind = False
        self.listening_trigger_keybind = False
        self.listening_ui_toggle = False
        self.listening_kill_keybind = False
        self._insert_was_down = False
        self._hotkey_arm_until = 0.0
        self._pulse_state = False

        self.aim_hz = 520
        self.trigger_hz = 520
        self.overlay_hz = 60
        self.interval = 1.0 / 520.0
        self.tolerance = 50
        self.scan_size = 240
        self.scan_res = 1.0
        self.smoothness = 0.0
        self.sensitivity = 10.0
        self.mouse_scale = 1.0
        self.shaky_enabled = False
        self.shaky_aim = 10.0
        self.shaky_speed = 5.0
        self.offset_enabled = False
        self.offset_y = 0.0
        self.offset_x = 0.0
        self.triggerbot_enabled = False
        self.recoil_enabled = False
        self.recoil_strength = 2.0
        self.trigger_key_name = "XBUTTON5"
        self.trigger_scan_size = 4
        self.trigger_reaction_ms = 0.0
        self.trigger_interval_ms = 50.0
        self.trigger_release_ms = 0.0
        self.trigger_key_mode = "Hold"
        self.trigger_fire_mode = "Click on Color"
        self.menu_opacity = 1.0
        self.theme = "Default"
        self.custom_bg = (31, 10, 10)
        self.custom_fg = (255, 26, 26)
        self.circle_color = "white"
        self.lock_color = "red"
        self.lock_indicator = False
        self.trigger_indicator = False
        self.lock_ind_idle = (255, 255, 255)
        self.lock_ind_on = (255, 0, 0)
        self.trig_ind_idle = (255, 255, 255)
        self.trig_ind_on = (0, 255, 0)
        self._ind_lock_on = False
        self._ind_trig_on = False
        self.lock_ind_pos = "Top Right"
        self.trig_ind_pos = "Top Left"
        self.fov_thickness = 1
        self.fov_opacity = 1.0
        self.aim_key_mode = "Toggle"
        self.show_fov = True
        self.fov_mode = "Follow Cursor"
        self.fov_shape = "Circle"
        self.esp_enabled = False
        self.debug_view_enabled = False
        self.esp_preview_enabled = False
        self._debug_frame = None
        self._debug_lock = threading.Lock()
        self._debug_win = None
        self._debug_label = None
        self._debug_photo = None
        self.esp_color = "white"
        self.box_thickness = 1
        self.player_box_shape = "Box"
        self.corner_length = 8
        self.tracers_enabled = False
        self.tracer_thickness = 1
        self.tracers_origin = "Cursor"

        self._worker = None
        self._worker_stop = threading.Event()
        self._colors_lock = threading.Lock()
        self._hot_colors = []
        self._hot_tolerance = 50
        self._hot_scan = 250
        self._hot_scan_res = 1.0
        self._hot_aim_point = "center"
        self._hot_edge_bias = 0.0
        self._hot_target_priority = "none"
        self._hot_aimbot = True
        self._hot_key = 0x05
        self._hot_smooth = 0.0
        self._hot_sens = 5.0
        self._hot_mouse_scale = 1.0
        self._hot_shaky_enabled = False
        self._hot_shaky_aim = 10.0
        self._hot_shaky_speed = 5.0
        self._hot_offset_enabled = False
        self._hot_offset_y = 0.0
        self._hot_offset_x = 0.0
        self._hot_triggerbot = False
        self._hot_trigger_key = 0x06
        self._hot_trigger_scan = 4
        self._hot_trigger_reaction = 0.0
        self._hot_trigger_interval = 50.0
        self._hot_trigger_release = 0.0
        self._hot_trigger_key_mode = "Hold"
        self._hot_trigger_fire_mode = "Click on Color"
        self._hot_aim_key_mode = "Toggle"
        self._hot_show_fov = True
        self._hot_fov_mode = "Follow Cursor"
        self._hot_esp = False
        self._hot_debug_view = False
        self._hot_esp_color = "white"
        self._hot_box_thickness = 1
        self._hot_player_box_shape = "Box"
        self._hot_corner_length = 8
        self._hot_tracers = False
        self._hot_tracer_thickness = 1
        self._hot_tracers_origin = "Center"
        self._esp_box_ids = []
        self._fov_corner_ids = []
        self._tracer_ids = []
        self._last_esp_t = 0.0
        self._last_status_t = 0.0
        self._last_status_text = ""
        self._last_overlay_t = 0.0
        self._hot_aim_hz = 520
        self._hot_trigger_hz = 520
        self._hot_overlay_hz = 60

        self.keybind_var = tk.StringVar(value="XBUTTON1")
        self.trigger_keybind_var = tk.StringVar(value="XBUTTON2")
        self.trigger_scan_var = tk.DoubleVar(value=4.0)
        self.recoil_strength_var = tk.DoubleVar(value=2.0)
        self.trigger_reaction_var = tk.DoubleVar(value=0.0)
        self.trigger_interval_var = tk.DoubleVar(value=50.0)
        self.trigger_release_var = tk.DoubleVar(value=0.0)
        self.trigger_key_mode_var = tk.StringVar(value="Hold")
        self.trigger_fire_mode_var = tk.StringVar(value="Click on Color")
        self.ui_toggle_var = tk.StringVar(value="INSERT")
        self.kill_key_var = tk.StringVar(value="None")
        self.scan_size_var = tk.DoubleVar(value=self.scan_size)
        self.scan_res_var = tk.DoubleVar(value=1.0)
        self.tolerance_var = tk.DoubleVar(value=self.tolerance)
        self.smoothness_var = tk.DoubleVar(value=self.smoothness)
        self.sensitivity_var = tk.DoubleVar(value=self.sensitivity)
        self.mouse_scale_var = tk.DoubleVar(value=self.mouse_scale)
        self.shaky_aim_var = tk.DoubleVar(value=10.0)
        self.shaky_speed_var = tk.DoubleVar(value=5.0)
        self.offset_y_var = tk.DoubleVar(value=0.0)
        self.offset_x_var = tk.DoubleVar(value=0.0)
        self.opacity_var = tk.DoubleVar(value=self.menu_opacity)
        self.menu_scale = 100.0
        self.menu_scale_var = tk.DoubleVar(value=100.0)
        self.theme_var = tk.StringVar(value=self.theme)
        self.lock_ind_pos_var = tk.StringVar(value=getattr(self, "lock_ind_pos", "Top Right"))
        self.trig_ind_pos_var = tk.StringVar(value=getattr(self, "trig_ind_pos", "Top Left"))
        self.aim_point_var = tk.StringVar(value="Center")
        self.edge_bias = 0.0
        self.edge_bias_var = tk.DoubleVar(value=0.0)
        self.target_priority_var = tk.StringVar(value="None")
        self.circle_color_var = tk.StringVar(value="white")
        self.xhair_enabled = False
        self.xhair_mode = "Follow Cursor"
        self.xhair_opacity = 1.0
        self.xhair_bars = False
        self.xhair_bar_len = 10.0
        self.xhair_bar_width = 2.0
        self.xhair_bar_gap = 3.0
        self.xhair_bar_color = (255, 255, 255)
        self.xhair_dot = False
        self.xhair_dot_size = 2.0
        self.xhair_dot_color = (255, 255, 255)
        self.xhair_dot_shape = "Rounded"
        self.xhair_outline = False
        self.xhair_outline_thick = 1.0
        self.xhair_outline_color = (255, 255, 255)
        self.xhair_mode_var = tk.StringVar(value="Follow Cursor")
        self.xhair_opacity_var = tk.DoubleVar(value=1.0)
        self.xhair_bar_len_var = tk.DoubleVar(value=10.0)
        self.xhair_bar_width_var = tk.DoubleVar(value=2.0)
        self.xhair_bar_gap_var = tk.DoubleVar(value=3.0)
        self.xhair_dot_size_var = tk.DoubleVar(value=2.0)
        self.xhair_dot_shape_var = tk.StringVar(value="Rounded")
        self.xhair_outline_thick_var = tk.DoubleVar(value=1.0)
        self.lock_color_var = tk.StringVar(value="red")
        self.fov_thickness_var = tk.DoubleVar(value=1)
        self.fov_opacity_var = tk.DoubleVar(value=1.0)
        self.aim_hz_var = tk.DoubleVar(value=520)
        self.trigger_hz_var = tk.DoubleVar(value=520)
        self.overlay_hz_var = tk.DoubleVar(value=60)
        self.esp_color_var = tk.StringVar(value="white")
        self.box_thickness_var = tk.DoubleVar(value=1)
        self.tracer_thickness_var = tk.DoubleVar(value=1)
        self.tracers_origin_var = tk.StringVar(value="Cursor")
        self.aim_key_mode_var = tk.StringVar(value="Toggle")
        self.fov_mode_var = tk.StringVar(value="Follow Cursor")
        self.fov_shape_var = tk.StringVar(value="Circle")
        self.player_box_shape_var = tk.StringVar(value="Box")
        self.corner_length_var = tk.DoubleVar(value=8)
        self.config_name_var = tk.StringVar(value="")
        self.cpu_priority_var = tk.StringVar(value="Normal")
        self.active_tab = tk.StringVar(value="Aimbot")

        self._setup_styles()
        self.create_widgets()
        self.make_draggable()
        self.create_overlay()
        self._show_tab("Aimbot")
        self._apply_opacity()
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
        except Exception:
            pass
        self.load_config(silent=True)
        try:
            self.root.after(300, self._start_playtime)
        except Exception:
            pass
        try:
            apply_cpu_priority(getattr(self, "cpu_priority", "Normal"))
        except Exception:
            pass
        self.apply_theme(getattr(self, "theme", "Ocean"), rebuild=True)
        self._poll_insert()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(150, self.start)

    def _on_close(self):
        if getattr(self, "minimize_to_tray", True):
            self._park_to_tray()
        else:
            self._quit_app()

    def _park_to_tray(self):
        self._tray_parked = True
        self.ui_visible = False
        try:
            self.stop()
        except Exception:
            pass
        try:
            self._start_tray()
        except Exception:
            pass
        try:
            self.root.withdraw()
        except Exception:
            pass
        try:
            self._set_status("Idle", C_MUTED)
        except Exception:
            pass

    def _resume_from_tray(self):
        self._tray_parked = False
        self.ui_visible = True
        try:
            self._stop_tray()
        except Exception:
            pass
        try:
            self.root.deiconify()
            self.root.lift()
            self._apply_topmost()
            self._apply_opacity()
        except Exception:
            pass
        try:
            if not getattr(self, "tracking", False):
                self.start()
        except Exception:
            pass

    def _tray_show(self):
        self._resume_from_tray()

    def _tray_hide(self):
        self._park_to_tray()

    def _start_update(self):
        if getattr(self, "_updating", False):
            return
        if getattr(sys, "frozen", False):
            self._set_status("Update only works when running NauticalUI.py", C_DANGER)
            return
        self._updating = True
        self._set_status("Checking for updates...", C_ACCENT)
        threading.Thread(target=self._update_worker, daemon=True).start()

    def _update_worker(self):
        import ast as _ast

        def post(msg, color):
            try:
                self.root.after(0, lambda: self._set_status(msg, color))
            except Exception:
                pass

        try:
            data, text, remote = _fetch_remote_update()
            if not remote:
                post("Repo copy has no APP_VERSION", C_DANGER)
                return
            if _version_tuple(remote) == _version_tuple(APP_VERSION):
                post("Up to date (v%s)" % APP_VERSION, C_SUCCESS)
                return
            if _version_tuple(remote) < _version_tuple(APP_VERSION):
                post("Local v%s is newer than repo v%s" % (APP_VERSION, remote), C_MUTED)
                return
            _ast.parse(text)
            if "class ColorTrackerGUI" not in text:
                post("Update rejected: downloaded file looks wrong", C_DANGER)
                return
            script = os.path.abspath(__file__)
            tmp = script + ".new"
            with open(tmp, "wb") as f:
                f.write(data)
            try:
                import shutil
                shutil.copy2(script, script + ".bak")
            except Exception:
                pass
            os.replace(tmp, script)
            post("Updated to v%s, restarting..." % remote, C_SUCCESS)
            self.root.after(1200, self._restart_app)
        except Exception as e:
            post("Update failed: %s" % (str(e)[:60] or type(e).__name__), C_DANGER)
        finally:
            self._updating = False

    def _check_update_banner(self):
        if getattr(sys, "frozen", False):
            return

        def work():
            try:
                _data, _text, remote = _fetch_remote_update()
                if remote and _version_tuple(remote) > _version_tuple(APP_VERSION):
                    self.root.after(0, lambda: self._show_update_banner(remote))
            except Exception:
                pass

        threading.Thread(target=work, daemon=True).start()

    def _show_update_banner(self, version):
        if getattr(self, "_update_bar", None) is not None:
            return
        bar = tk.Frame(self.card, bg="#3a1010", highlightthickness=1, highlightbackground="#ff4444", cursor="hand2")
        bar.pack(fill="x", padx=10, pady=(4, 4), before=self.scroll_canvas.master)
        lbl = tk.Label(
            bar,
            text="Update available (v%s) - click here to update" % version,
            bg="#3a1010", fg="#ff8080",
            font=("Segoe UI", 9, "bold"),
            wraplength=560, justify="left", cursor="hand2",
        )
        lbl.pack(anchor="w", padx=10, pady=8)
        for w in (bar, lbl):
            w.bind("<Button-1>", lambda e: self._start_update())
        self._update_bar = bar

    def _restart_app(self):
        code = (
            "import ctypes,sys,subprocess,os\n"
            "pid=int(sys.argv[1])\n"
            "h=ctypes.windll.kernel32.OpenProcess(0x00100000,False,pid)\n"
            "if h: ctypes.windll.kernel32.WaitForSingleObject(h,15000)\n"
            "env=os.environ.copy()\n"
            "env.pop('NAUTICAL_DETACHED',None)\n"
            "subprocess.Popen([sys.argv[2],sys.argv[3]],env=env,close_fds=True,creationflags=0x08000208)\n"
        )
        try:
            subprocess.Popen(
                [sys.executable, "-c", code, str(os.getpid()), sys.executable, os.path.abspath(__file__)],
                close_fds=True, creationflags=0x08000208,
            )
        except Exception:
            self._set_status("Updated. Restart NauticalUI manually", C_ACCENT)
            return
        self._quit_app()
        os._exit(0)

    def _quit_app(self):
        try:
            self._playtime_closing = True
            self._flush_playtime(force=True)
        except Exception:
            pass
        try:
            icon = getattr(self, "_tray", None)
            if icon is not None:
                icon.stop()
        except Exception:
            pass
        self._tray = None
        try:
            self.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _stop_tray(self):
        icon = getattr(self, "_tray", None)
        self._tray = None
        if icon is None:
            return
        try:
            icon.stop()
        except Exception:
            pass

    def _start_tray(self):
        if not getattr(self, "minimize_to_tray", True):
            self._stop_tray()
            return
        if getattr(self, "_tray", None) is not None:
            return
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            try:
                self._set_status("Tray: pip install pystray pillow", C_MUTED)
            except Exception:
                pass
            return
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            from PIL import ImageFont
            font = None
            for fp in (
                r"C:\Windows\Fonts\seguiemj.ttf",
                r"C:\Windows\Fonts\SegoeUIEmoji.ttf",
            ):
                if os.path.isfile(fp):
                    font = ImageFont.truetype(fp, 118)
                    break
            if font is not None:
                try:
                    draw.text((-6, -16), "\U0001F440", font=font, embedded_color=True)
                except TypeError:
                    draw.text((-6, -16), "\U0001F440", font=font)
            else:
                raise RuntimeError("no emoji font")
        except Exception:
            draw.ellipse((4, 28, 60, 100), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=3)
            draw.ellipse((68, 28, 124, 100), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=3)
            draw.ellipse((18, 48, 42, 80), fill=(40, 40, 40, 255))
            draw.ellipse((82, 48, 106, 80), fill=(40, 40, 40, 255))
        menu = pystray.Menu(
            pystray.MenuItem("Show", lambda: self.root.after(0, self._tray_show), default=True),
            pystray.MenuItem("Hide", lambda: self.root.after(0, self._tray_hide)),
            pystray.MenuItem("Exit", lambda: self.root.after(0, self._quit_app)),
        )
        self._tray = pystray.Icon("NauticalUI", img, "NauticalUI", menu)
        threading.Thread(target=self._tray.run, name="tray", daemon=True).start()

    def _clear_combobox_selection(self, event=None):
        try:
            w = event.widget if event is not None else None
            if w is None:
                return
            w.selection_clear()
            try:
                w.icursor(tk.END)
            except Exception:
                pass
        except Exception:
            pass

    def _setup_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Accent.Horizontal.TScale",
            background=C_CARD,
            troughcolor=C_TRACK,
            bordercolor=C_TRACK,
            lightcolor=C_ACCENT,
            darkcolor=C_ACCENT,
            sliderthickness=14,
        )
        field_bg = "#0c0e12"
        style.configure(
            "TCombobox",
            fieldbackground=field_bg,
            background=field_bg,
            foreground="#ffffff",
            arrowcolor=C_ACCENT,
            bordercolor=C_ACCENT,
            lightcolor=field_bg,
            darkcolor=field_bg,
            borderwidth=1,
            insertcolor="#ffffff",
            padding=(10, 7),
            relief="flat",
            selectbackground=field_bg,
            selectforeground="#ffffff",
        )
        try:
            style.configure("TCombobox", focusthickness=0, focuscolor=field_bg)
        except Exception:
            pass
        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", field_bg),
                ("focus", field_bg),
                ("active", field_bg),
            ],
            foreground=[
                ("readonly", "#ffffff"),
                ("focus", "#ffffff"),
                ("disabled", "#666666"),
            ],
            background=[
                ("readonly", field_bg),
                ("active", field_bg),
            ],
            arrowcolor=[
                ("readonly", C_ACCENT),
                ("active", C_ACCENT),
                ("pressed", C_ACCENT_DIM),
            ],
            bordercolor=[
                ("focus", C_ACCENT),
                ("active", C_ACCENT),
                ("readonly", C_ACCENT),
                ("!focus", C_ACCENT),
            ],
            lightcolor=[
                ("focus", field_bg),
                ("active", field_bg),
                ("readonly", field_bg),
                ("!focus", field_bg),
            ],
            darkcolor=[
                ("focus", field_bg),
                ("active", field_bg),
                ("readonly", field_bg),
                ("!focus", field_bg),
            ],
            selectbackground=[
                ("readonly", field_bg),
                ("focus", field_bg),
                ("active", field_bg),
            ],
            selectforeground=[
                ("readonly", "#ffffff"),
                ("focus", "#ffffff"),
                ("active", "#ffffff"),
            ],
        )
        try:
            self.root.option_add("*TCombobox*Listbox.background", field_bg)
            self.root.option_add("*TCombobox*Listbox.foreground", "#ffffff")
            self.root.option_add("*TCombobox*Listbox.selectBackground", C_ACCENT)
            self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
            self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))
            self.root.option_add("*TCombobox*Listbox.relief", "flat")
            self.root.option_add("*TCombobox*Listbox.borderWidth", 0)
        except Exception:
            pass
        try:
            self.root.bind_class("TCombobox", "<<ComboboxSelected>>", self._clear_combobox_selection, add="+")
            self.root.bind_class("TCombobox", "<FocusIn>", self._clear_combobox_selection, add="+")
        except Exception:
            pass

    def create_overlay(self):
        self._overlay_key = "#ff00ff"
        self._overlay_key_bgr = 0x00FF00FF
        self.overlay = tk.Toplevel(self.root)
        self.overlay.withdraw()
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        try:
            self.overlay.wm_attributes("-transparentcolor", self._overlay_key)
        except Exception:
            pass
        self.overlay.configure(bg=self._overlay_key)
        size = max(50, int(self.scan_size))
        self.overlay.geometry(f"{size}x{size}+100+100")
        self.canvas = tk.Canvas(
            self.overlay, width=size, height=size,
            bg=self._overlay_key, highlightthickness=0, bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        pad = 3
        thick = int(max(1, min(5, float(getattr(self, "fov_thickness", 2)))))
        col = "lime"
        self.circle_id = self.canvas.create_oval(
            pad, pad, size - pad, size - pad,
            outline=col, width=thick, fill="",
        )
        self.fov_rect_id = self.canvas.create_rectangle(
            pad, pad, size - pad, size - pad,
            outline=col, width=thick, fill="", state="hidden",
        )
        if hasattr(self, "circle_color_var"):
            try:
                self.circle_color = self.circle_color_var.get() or "lime"
                self.canvas.itemconfig(self.circle_id, outline=self.circle_color)
                self.canvas.itemconfig(self.fov_rect_id, outline=self.circle_color)
            except Exception:
                pass

    def _overlay_hwnd(self):
        try:
            self.overlay.update_idletasks()
            wid = self.overlay.winfo_id()
            hwnd = ctypes.windll.user32.GetParent(wid)
            if not hwnd:
                hwnd = wid
            return int(hwnd)
        except Exception:
            return 0

    def _make_overlay_clickthrough(self):
        try:
            hwnd = self._overlay_hwnd()
            if not hwnd:
                return
            user32 = ctypes.windll.user32
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            )
            alpha = int(max(0.15, min(1.0, float(getattr(self, "fov_opacity", 1.0)))) * 255)
            user32.SetLayeredWindowAttributes(
                hwnd, self._overlay_key_bgr, alpha, LWA_COLORKEY | LWA_ALPHA
            )
        except Exception:
            pass

    def update_overlay_size(self):
        try:
            size = max(50, int(self.scan_size))
            if size % 2:
                size += 1
            self.overlay.geometry(f"{size}x{size}")
            self.canvas.config(width=size, height=size)
            pad = 3
            self.canvas.coords(self.circle_id, pad, pad, size - pad, size - pad)
            if hasattr(self, "fov_rect_id"):
                self.canvas.coords(self.fov_rect_id, pad, pad, size - pad, size - pad)
            self._draw_fov_corners(size, pad)
            self._apply_fov_shape_draw()
            self._reposition_overlay()
        except Exception:
            pass

    def _reposition_overlay(self):
        try:
            mode = self.fov_mode_var.get() if hasattr(self, "fov_mode_var") else getattr(self, "fov_mode", "Follow Cursor")
            if mode == "Centered":
                sw = ctypes.windll.user32.GetSystemMetrics(0)
                sh = ctypes.windll.user32.GetSystemMetrics(1)
                self.update_overlay_position(sw // 2, sh // 2)
            else:
                cx, cy = get_cursor_pos()
                self.update_overlay_position(cx, cy)
        except Exception:
            pass

    def _draw_fov_corners(self, size=None, pad=None):
        try:
            if size is None:
                size = max(50, int(self.scan_size))
            if pad is None:
                pad = max(1, int(getattr(self, "fov_thickness", 2)))
            cl = 10
            x1, y1, x2, y2 = pad, pad, size - pad, size - pad
            segs = (
                (x1, y1, x1 + cl, y1), (x1, y1, x1, y1 + cl),
                (x2 - cl, y1, x2, y1), (x2, y1, x2, y1 + cl),
                (x1, y2, x1 + cl, y2), (x1, y2 - cl, x1, y2),
                (x2 - cl, y2, x2, y2), (x2, y2 - cl, x2, y2),
            )
            col = getattr(self, "circle_color", "lime")
            thick = max(1, int(getattr(self, "fov_thickness", 2)))
            ids = list(getattr(self, "_fov_corner_ids", []))
            if len(ids) != 8:
                for i in ids:
                    try:
                        self.canvas.delete(i)
                    except Exception:
                        pass
                self._fov_corner_ids = []
                for a, b, c, d in segs:
                    self._fov_corner_ids.append(
                        self.canvas.create_line(
                            a, b, c, d, fill=col, width=thick, tags=("fov_corner",),
                        )
                    )
            else:
                for i, (a, b, c, d) in enumerate(segs):
                    try:
                        self.canvas.coords(ids[i], a, b, c, d)
                        self.canvas.itemconfig(ids[i], fill=col, width=thick)
                    except Exception:
                        pass
        except Exception:
            pass

    def _apply_fov_shape_draw(self):
        try:
            show = bool(getattr(self, "show_fov", True))
            col = getattr(self, "circle_color", "lime")
            thick = max(1, int(getattr(self, "fov_thickness", 2)))
            shape = getattr(self, "fov_shape", "Circle")
            if hasattr(self, "fov_shape_var"):
                shape = self.fov_shape_var.get() or shape
            self.canvas.itemconfig(
                self.circle_id, outline=col, width=thick, fill="",
                state="normal" if (show and shape == "Circle") else "hidden",
            )
            if hasattr(self, "fov_rect_id"):
                self.canvas.itemconfig(
                    self.fov_rect_id, outline=col, width=thick, fill="",
                    state="normal" if (show and shape == "Box") else "hidden",
                )
            if not getattr(self, "_fov_corner_ids", None):
                self._draw_fov_corners()
            for i in getattr(self, "_fov_corner_ids", []):
                try:
                    self.canvas.itemconfig(
                        i, fill=col, width=thick,
                        state="normal" if (show and shape == "Corners") else "hidden",
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def update_overlay_position(self, x, y):
        try:
            size = max(50, int(self.scan_size))
            if size % 2:
                size += 1
            left = int(x) - size // 2
            top = int(y) - size // 2
            self.overlay.geometry("%dx%d+%d+%d" % (size, size, left, top))
        except Exception:
            pass

    def show_overlay(self):
        try:
            self.update_overlay_size()
            self.overlay.deiconify()
            self.overlay.attributes("-topmost", True)
            self.overlay.lift()
            circ_state = "normal" if getattr(self, "show_fov", True) else "hidden"
            self.canvas.itemconfigure(self.circle_id, state=circ_state)
            self.overlay.update()
            self._make_overlay_clickthrough()
            self.root.after(50, self._make_overlay_clickthrough)
            if getattr(self, "streamproof", False):
                self.root.after(60, self._apply_streamproof)
        except Exception:
            pass

    def hide_overlay(self):
        try:
            self.overlay.withdraw()
        except Exception:
            pass
        try:
            if getattr(self, "xhair_overlay", None) is not None:
                self.xhair_overlay.withdraw()
        except Exception:
            pass

    def create_widgets(self):
        self.rim = tk.Frame(
            self.root, bg="#000000",
            highlightthickness=4, highlightbackground="#000000", highlightcolor="#000000",
            bd=0,
        )
        self.rim.pack(fill="both", expand=True)

        self.outer = tk.Frame(self.rim, bg="#000000", highlightthickness=0, bd=0)
        self.outer.pack(fill="both", expand=True, padx=1, pady=1)

        self.sidebar = tk.Frame(self.outer, bg="#000000", width=128, highlightthickness=0, bd=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.title_bar = tk.Frame(self.sidebar, bg="#000000", height=40)
        self.title_bar.pack(fill="x", padx=10, pady=(14, 8))
        self.title_bar.pack_propagate(False)
        self.title_label = tk.Label(
            self.title_bar, text="NauticalUI V2", bg="#000000",
            fg=THEMES.get(getattr(self, "theme", ""), {}).get("title", C_ACCENT),
            font=("Segoe UI", 11, "bold"),
        )
        self.title_label.pack(side="left", anchor="w")

        self.root.bind_all("<Button-1>", self._on_global_click, add="+")

        self.tab_buttons = {}
        self.tab_rows = {}
        for name in ("Aimbot", "Visuals", "Capture", "Keybinds", "Config"):
            row = tk.Frame(self.sidebar, bg="#000000", cursor="hand2")
            row.pack(fill="x", padx=8, pady=2)
            accent = tk.Frame(row, bg="#000000", width=3)
            accent.pack(side="left", fill="y")
            btn = tk.Label(
                row, text=name, bg="#000000", fg="#888888",
                font=("Segoe UI", 10, "bold"), anchor="w", padx=10, pady=8, cursor="hand2",
            )
            btn.pack(side="left", fill="x", expand=True)
            for w in (row, btn, accent):
                w.bind("<Button-1>", lambda e, n=name: self._show_tab(n))
                w.bind("<Enter>", lambda e, n=name: self._tab_hover_name(n, True))
                w.bind("<Leave>", lambda e, n=name: self._tab_hover_name(n, False))
            self.tab_buttons[name] = btn
            self.tab_rows[name] = (row, accent, btn)

        self.side_div = tk.Frame(self.outer, bg="#2a2a2a", width=1, highlightthickness=0, bd=0)
        self.side_div.pack(side="left", fill="y")

        self.card = tk.Frame(self.outer, bg=C_CARD, highlightthickness=0, bd=0)
        self.card.pack(side="left", fill="both", expand=True)

        self.top_bar = tk.Frame(self.card, bg=C_CARD, height=28, highlightthickness=0, bd=0)
        self.top_bar.pack(fill="x", padx=10, pady=0)
        self.top_bar.pack_propagate(False)
        self.close_btn = tk.Label(
            self.top_bar, text="✕", bg=C_CARD, fg="#ff0000",
            font=("Segoe UI", 11), cursor="hand2",
        )
        self.close_btn.pack(side="right", pady=4)
        self.close_btn.bind("<Button-1>", lambda e: self._on_close())
        try:
            self._show_missing_banner()
        except Exception:
            pass
        self.root.after(2500, self._check_update_banner)
        scroll_wrap = tk.Frame(self.card, bg=C_CARD, highlightthickness=0, bd=0)
        scroll_wrap.pack(fill="both", expand=True, padx=12, pady=0)

        self.scroll_canvas = tk.Canvas(
            scroll_wrap, bg=C_CARD, highlightthickness=0, bd=0
        )
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.scroll_canvas.configure(yscrollcommand=lambda *a: None)

        self.content = tk.Frame(self.scroll_canvas, bg=C_CARD)
        self._content_window = self.scroll_canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )

        self.content.bind("<Configure>", self._on_content_configure)
        self.scroll_canvas.bind("<Configure>", self._on_scroll_canvas_configure)
        self.scroll_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._bind_combobox_wheel_block()

        self.tab_frames = {}
        self._col_canvases = []
        self._sections = []
        self._build_aim_tab()
        self._build_visuals_tab()
        self._build_capture_tab()
        self._build_keybinds_tab()
        self._build_config_tab()

        self.foot = tk.Frame(self.card, bg=C_CARD, height=18, highlightthickness=0, bd=0)
        self.foot.pack(fill="x", padx=4, pady=0)
        self.foot.pack_propagate(False)

        self.resize_grip = tk.Canvas(
            self.foot,
            width=16,
            height=16,
            bg=C_CARD,
            highlightthickness=0,
            bd=0,
            cursor="size_nw_se",
        )
        self.resize_grip.pack(side="right", padx=0, pady=1)
        self._draw_resize_grip()
        self.resize_grip.bind("<Button-1>", self._resize_start)
        self.resize_grip.bind("<B1-Motion>", self._resize_drag)
        self.resize_grip.bind("<ButtonRelease-1>", self._resize_stop)

    def _draw_resize_grip(self, hover=False):
        g = self.resize_grip
        g.delete("all")
        color = C_ACCENT
        for i, offset in enumerate((4, 8, 12)):
            x0 = offset
            y0 = 16
            x1 = 16
            y1 = offset
            g.create_line(x0, y0, x1, y1, fill=color, width=1)

    def _on_content_configure(self, event=None):
        self._refresh_scroll()

    def _on_scroll_canvas_configure(self, event=None):
        try:
            self.scroll_canvas.itemconfigure(self._content_window, width=event.width)
        except Exception:
            pass
        self._fit_split_tab()

    def _refresh_scroll(self):
        try:
            self.scroll_canvas.update_idletasks()
            bbox = self.scroll_canvas.bbox("all")
            if bbox:
                self.scroll_canvas.configure(scrollregion=bbox)
        except Exception:
            pass

    def _on_mousewheel(self, event):
        try:
            if self.root.winfo_containing(event.x_root, event.y_root) is None:
                return
        except Exception:
            pass
        raw = event.delta if event.delta else 0
        if raw == 0:
            return
        steps = max(1, abs(int(raw // 120))) if abs(raw) >= 120 else 1
        direction = -1 if raw > 0 else 1
        x, y = event.x_root, event.y_root
        for cv in getattr(self, "_col_canvases", []):
            try:
                if not cv.winfo_ismapped():
                    continue
                cx, cy = cv.winfo_rootx(), cv.winfo_rooty()
                if cx <= x <= cx + cv.winfo_width() and cy <= y <= cy + cv.winfo_height():
                    self._smooth_scroll(cv, direction * steps)
                    return "break"
            except Exception:
                pass
        try:
            self._smooth_scroll(self.scroll_canvas, direction * steps)
        except Exception:
            pass

    def _smooth_scroll(self, canvas, ticks):
        if canvas is None or not ticks:
            return
        try:
            first, last = canvas.yview()
        except Exception:
            return
        page = max(0.02, float(last) - float(first))
        try:
            bbox = canvas.bbox("all") or (0, 0, 0, 1)
            total = max(1.0, float(bbox[3] - bbox[1]))
            view = max(1.0, float(canvas.winfo_height()))
            max_top = max(0.0, 1.0 - min(1.0, view / total))
        except Exception:
            max_top = max(0.0, 1.0 - page)
        if not hasattr(self, "_scroll_anim"):
            self._scroll_anim = {}
        key = id(canvas)
        anim = self._scroll_anim.get(key)
        if anim is None:
            anim = {"target": float(first), "running": False}
            self._scroll_anim[key] = anim
        anim["target"] = max(0.0, min(max_top, float(anim["target"]) + ticks * page * 0.14))
        if anim["target"] <= 0.002:
            anim["target"] = 0.0
            try:
                canvas.yview_moveto(0.0)
            except Exception:
                pass
            if ticks < 0:
                anim["running"] = False
                return
        if anim["running"]:
            return
        anim["running"] = True

        def tick():
            try:
                cur = float(canvas.yview()[0])
            except Exception:
                anim["running"] = False
                return
            dest = float(anim["target"])
            if dest <= 0.002:
                dest = 0.0
                anim["target"] = 0.0
            dist = dest - cur
            if abs(dist) < 0.0008 or dest == 0.0 and cur < 0.01:
                try:
                    canvas.yview_moveto(dest)
                except Exception:
                    pass
                anim["running"] = False
                return
            try:
                canvas.yview_moveto(cur + dist * 0.12)
            except Exception:
                anim["running"] = False
                return
            self.root.after(8, tick)

        tick()

    def _combobox_mousewheel(self, event):
        self._on_mousewheel(event)
        return "break"

    def _bind_combobox_wheel_block(self):
        try:
            self.root.bind_class("TCombobox", "<MouseWheel>", self._combobox_mousewheel)
            self.root.bind_class("TCombobox", "<Button-4>", self._combobox_mousewheel)
            self.root.bind_class("TCombobox", "<Button-5>", self._combobox_mousewheel)
        except Exception:
            pass

    def _resize_start(self, event):
        self._resizing = True
        self._rz_mx = event.x_root
        self._rz_my = event.y_root
        self._rz_w = self.root.winfo_width()
        self._rz_h = self.root.winfo_height()

    def _resize_drag(self, event):
        if not getattr(self, "_resizing", False):
            return
        dw = event.x_root - self._rz_mx
        dh = event.y_root - self._rz_my
        nw = max(560, int(self._rz_w + dw))
        nh = max(420, int(self._rz_h + dh))
        self.root.geometry(f"{nw}x{nh}")
        self._refresh_scroll()

    def _resize_stop(self, event):
        self._resizing = False
        self._refresh_scroll()

    def _section(self, parent, title, start_open=True):
        card = tk.Frame(
            parent, bg=C_CARD2,
            highlightthickness=1, highlightbackground=C_BORDER, highlightcolor=C_BORDER,
            bd=0,
        )
        card.pack(fill="x", pady=(0, 8))
        def _sec_hover(on):
            try:
                card.configure(highlightbackground=C_ACCENT if on else C_BORDER)
            except Exception:
                pass
        def _ptr_in_card(ex, ey):
            try:
                w = self.root.winfo_containing(ex, ey)
                while w is not None:
                    if w is card:
                        return True
                    w = w.master
            except Exception:
                pass
            return False
        card.bind("<Enter>", lambda e: _sec_hover(True))
        card.bind("<Leave>", lambda e: (_sec_hover(False) if not _ptr_in_card(e.x_root, e.y_root) else None))

        head = tk.Frame(card, bg=C_CARD2, height=30)
        head.pack(fill="x", padx=10, pady=(4, 2))
        head.pack_propagate(False)
        tk.Label(
            head, text=title, bg=C_CARD2, fg=UI_TEXT,
            font=("Segoe UI", 9, "bold"),
        ).place(x=0, rely=0.5, anchor="w")
        btn = tk.Label(
            head, text="-", bg=C_CARD2, fg=UI_TEXT,
            font=("Segoe UI", 16, "bold"), cursor="hand2",
        )
        btn.place(relx=1.0, rely=0.5, y=-3, anchor="e")

        body = tk.Frame(card, bg=C_CARD2, highlightthickness=0, bd=0)
        body.pack(fill="x", padx=10, pady=(0, 8))
        body._section_card = card
        body._section_title = title
        body._section_open = bool(start_open)
        tabn = self.active_tab.get() if hasattr(self, "active_tab") else ""
        if not hasattr(self, "_sections"):
            self._sections = []
        self._sections.append({"title": title, "card": card, "tab": tabn, "parent": parent})

        def _set_open(open_):
            body._section_open = bool(open_)
            if body._section_open:
                body.pack(fill="x", padx=10, pady=(0, 8))
                btn.configure(text="-")
            else:
                body.pack_forget()
                btn.configure(text="+")
            try:
                self._refresh_scroll()
            except Exception:
                pass

        body._set_open = _set_open
        def _toggle(_e=None):
            _set_open(not body._section_open)

        btn.bind("<Button-1>", _toggle)
        if not start_open:
            _set_open(False)
        return body


    def _slider_row(self, parent, label, variable, from_, to, command, fmt="{:.0f}", snap=None):
        row = tk.Frame(parent, bg=C_CARD2, highlightthickness=0, bd=0)
        row.pack(fill="x", pady=(0, 6))
        top = tk.Frame(row, bg=C_CARD2, highlightthickness=0, bd=0)
        top.pack(fill="x")
        tk.Label(top, text=label, bg=C_CARD2, fg=UI_TEXT, font=("Segoe UI", 9)).pack(side="left")
        val = tk.Entry(
            top, bg="#0c0c0c", fg=UI_TEXT, insertbackground=UI_TEXT,
            relief="flat", font=("Segoe UI", 9), width=7, justify="right",
            highlightthickness=1, highlightbackground=C_BORDER, highlightcolor=C_ACCENT,
            bd=0,
        )
        val.insert(0, fmt.format(variable.get()))
        val.pack(side="right", ipady=1, ipadx=2, pady=0)

        height = 16
        canvas = tk.Canvas(
            row, height=height, bg=C_CARD2,
            highlightthickness=0, bd=0, borderwidth=0, relief="flat",
            cursor="hand2",
        )
        canvas.pack(fill="x", pady=(4, 0))
        canvas._is_slider = True

        if snap is None:
            if ".2f" in fmt:
                snap = 0.01
            elif ".1f" in fmt:
                snap = 0.1
            else:
                snap = 1
        state = {"dragging": False, "vis": None, "anim": False}

        def _frac():
            lo, hi = float(from_), float(to)
            if hi == lo:
                return 0.0
            return max(0.0, min(1.0, (float(variable.get()) - lo) / (hi - lo)))

        def _draw(_event=None):
            canvas.delete("all")
            w = max(canvas.winfo_width(), 2)
            canvas.create_rectangle(0, 0, w, height, fill=C_CARD2, outline="")
            mid = height // 2
            pad = 8
            ty0, ty1 = mid - 2, mid + 2
            canvas.create_oval(pad, ty0, pad + 4, ty1, fill=C_TRACK, outline=C_TRACK)
            canvas.create_oval(w - pad - 4, ty0, w - pad, ty1, fill=C_TRACK, outline=C_TRACK)
            canvas.create_rectangle(pad + 2, ty0, w - pad - 2, ty1, fill=C_TRACK, outline="")
            target = _frac()
            if state["vis"] is None:
                state["vis"] = target
            fx = pad + float(state["vis"]) * max(0, (w - 2 * pad))
            if fx > pad + 1:
                canvas.create_oval(pad, ty0, pad + 4, ty1, fill=C_ACCENT, outline=C_ACCENT)
                canvas.create_rectangle(pad + 2, ty0, fx, ty1, fill=C_ACCENT, outline="")
            r = 6
            canvas.create_oval(
                fx - r, mid - r, fx + r, mid + r,
                fill="#ffffff", outline="#ffffff", width=0,
            )

        def _set_from_x(x):
            w = max(canvas.winfo_width(), 2)
            pad = 7
            lo, hi = float(from_), float(to)
            t = 0.0 if w <= 2 * pad else max(0.0, min(1.0, (x - pad) / (w - 2 * pad)))
            value = lo + t * (hi - lo)
            if snap:
                s = float(snap)
                value = round(value / s) * s
                value = max(lo, min(hi, value))
            variable.set(value)
            try:
                s = fmt.format(float(value))
                if val.get() != s:
                    val.delete(0, tk.END)
                    val.insert(0, s)
            except Exception:
                pass
            if command:
                command(value)
            _glide()

        def _glide():
            target = _frac()
            if state["vis"] is None:
                state["vis"] = target
            if abs(float(state["vis"]) - target) < 0.002:
                state["vis"] = target
                state["anim"] = False
                _draw()
                return
            state["vis"] = float(state["vis"]) + (target - float(state["vis"])) * 0.22
            state["anim"] = True
            _draw()
            canvas.after(12, _glide)

        def on_press(e):
            state["dragging"] = True
            _set_from_x(e.x)

        def on_drag(e):
            if state["dragging"]:
                _set_from_x(e.x)

        def on_release(e):
            state["dragging"] = False
            _glide()

        canvas.bind("<Button-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        canvas.bind("<Configure>", lambda e: _draw())

        def _on_var(*_):
            try:
                if val.focus_get() is val:
                    return
                s = fmt.format(float(variable.get()))
                if val.get() != s:
                    val.delete(0, tk.END)
                    val.insert(0, s)
            except Exception:
                pass
            _draw()

        def _commit_entry(_event=None):
            try:
                raw = val.get().strip().replace(",", ".")
                value = float(raw)
            except Exception:
                try:
                    val.delete(0, tk.END)
                    val.insert(0, fmt.format(float(variable.get())))
                except Exception:
                    pass
                return "break"
            lo, hi = float(from_), float(to)
            value = max(lo, min(hi, value))
            if snap:
                s = float(snap)
                value = round(value / s) * s
                value = max(lo, min(hi, value))
            variable.set(value)
            try:
                val.delete(0, tk.END)
                val.insert(0, fmt.format(value))
            except Exception:
                pass
            if command:
                command(value)
            _glide()
            return "break"

        val.bind("<Return>", _commit_entry)
        val.bind("<FocusOut>", _commit_entry)

        try:
            variable.trace_add("write", lambda *_: _on_var())
        except Exception:
            try:
                variable.trace("w", lambda *_: _on_var())
            except Exception:
                pass

        canvas.after(10, _draw)
        return canvas, val

    def _close_open_combo(self):
        pop = getattr(self, "_combo_pop", None)
        self._combo_pop = None
        self._combo_anchor = None
        if pop is None:
            return
        try:
            pop.grab_release()
        except Exception:
            pass
        try:
            pop.destroy()
        except Exception:
            pass

    def _combo(self, parent, variable, values, command=None, on_delete=None):
        wrap = tk.Frame(parent, bg="#0c0c0c", highlightthickness=1, highlightbackground=C_ACCENT, highlightcolor=C_ACCENT)
        lab = tk.Label(wrap, textvariable=variable, bg="#0c0c0c", fg=UI_TEXT, anchor="w", font=("Segoe UI", 9), padx=8, pady=5)
        lab.pack(side="left", fill="x", expand=True)
        chev = tk.Label(wrap, text="▾", bg="#0c0c0c", fg=UI_TEXT, font=("Segoe UI", 16, "bold"), padx=10)
        chev.pack(side="right")
        state = {"values": list(values)}

        def _pick(val):
            variable.set(val)
            self._close_open_combo()
            if command:
                try:
                    command()
                except TypeError:
                    command(None)

        def _open(_e=None):
            if getattr(self, "_combo_anchor", None) is wrap and getattr(self, "_combo_pop", None):
                self._close_open_combo()
                return
            self._close_open_combo()
            vals = list(state["values"])
            pop = tk.Toplevel(self.root)
            pop.overrideredirect(True)
            pop.attributes("-topmost", True)
            pop.configure(bg="#0c0c0c")
            wrap.update_idletasks()
            x = wrap.winfo_rootx()
            y = wrap.winfo_rooty() + wrap.winfo_height() + 1
            wd = max(wrap.winfo_width(), 80)
            inner = tk.Frame(pop, bg="#0c0c0c", highlightthickness=1, highlightbackground=C_ACCENT)
            inner.pack(fill="both", expand=True)
            if not vals:
                tk.Label(inner, text="None", bg="#0c0c0c", fg="#666666", anchor="w", padx=8, pady=6, font=("Segoe UI", 9)).pack(fill="x")
            def _paint(r, i, xb, on):
                bg = "#1a1a1a" if on else "#0c0c0c"
                r.configure(bg=bg)
                i.configure(bg=bg)
                if xb is not None:
                    xb.configure(bg=bg)
            for val in vals:
                row = tk.Frame(inner, bg="#0c0c0c")
                row.pack(fill="x")
                item = tk.Label(row, text=val, bg="#0c0c0c", fg=UI_TEXT, anchor="w", padx=8, pady=5, cursor="hand2", font=("Segoe UI", 9))
                item.pack(side="left", fill="x", expand=True)
                xbtn = None
                if on_delete:
                    xbtn = tk.Label(row, text="x", bg="#0c0c0c", fg="#ff0000", font=("Segoe UI", 11, "bold"), padx=8, cursor="hand2")
                    xbtn.pack(side="right")
                    xbtn.bind("<Button-1>", lambda e, v=val: (on_delete(v), self._close_open_combo()))
                item.bind("<Button-1>", lambda e, v=val: _pick(v))
                row.bind("<Button-1>", lambda e, v=val: _pick(v))
                for wdg in (row, item, xbtn):
                    if wdg is None:
                        continue
                    wdg.bind("<Enter>", lambda e, r=row, i=item, xb=xbtn: _paint(r, i, xb, True))
                    wdg.bind("<Leave>", lambda e, r=row, i=item, xb=xbtn: _paint(r, i, xb, False))
            pop.update_idletasks()
            pop.geometry(f"{wd}x{inner.winfo_reqheight()}+{x}+{y}")
            try:
                self._streamproof_widget(pop)
            except Exception:
                pass
            pop.lift()
            try:
                hwnd = self._hwnd_from_widget(pop)
                if hwnd:
                    ctypes.windll.user32.SetWindowPos(int(hwnd), -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
            except Exception:
                pass
            self._combo_pop = pop
            self._combo_anchor = wrap
            pop.bind("<Escape>", lambda e: self._close_open_combo())

        wrap.set_values = lambda vals: state.update({"values": list(vals)})
        wrap.close_menu = self._close_open_combo
        wrap.bind("<Button-1>", _open)
        lab.bind("<Button-1>", _open)
        chev.bind("<Button-1>", _open)
        return wrap

    def _toggle_row(self, parent, label, get_state, set_state):
        row = tk.Frame(parent, bg=C_CARD2, highlightthickness=0, bd=0)
        row.pack(fill="x", pady=(0, 6))
        tk.Label(row, text=label, bg=C_CARD2, fg=UI_TEXT, font=("Segoe UI", 9)).pack(
            side="left", pady=0
        )
        tw, th = 40, 20
        cv = tk.Canvas(
            row, width=tw, height=th, bg=C_CARD2,
            highlightthickness=0, bd=0, borderwidth=0, relief="flat",
            cursor="hand2",
        )
        cv.pack(side="right", pady=0)
        cv._is_slider = True

        def _draw():
            cv.delete("all")
            cv.create_rectangle(0, 0, tw, th, fill=C_CARD2, outline="")
            on = bool(get_state())
            track = C_ACCENT if on else "#48484e"
            r = th
            cv.create_oval(0, 0, r, th, fill=track, outline=track)
            cv.create_oval(tw - r, 0, tw, th, fill=track, outline=track)
            cv.create_rectangle(th // 2, 0, tw - th // 2, th, fill=track, outline="")
            inset = 2
            kd = th - inset * 2
            if on:
                kx0 = tw - inset - kd
            else:
                kx0 = inset
            ky0 = inset
            cv.create_oval(
                kx0, ky0, kx0 + kd, ky0 + kd,
                fill="#ffffff", outline="#ffffff",
            )

        def _click(_e=None):
            set_state(not get_state())
            _draw()

        cv.bind("<Button-1>", _click)
        _draw()
        return cv, _draw


    def _make_scroll_col(self, parent):
        wrap = tk.Frame(parent, bg=C_CARD, highlightthickness=0, bd=0)
        cv = tk.Canvas(wrap, bg=C_CARD, highlightthickness=0, bd=0)
        cv.pack(fill="both", expand=True)
        inner = tk.Frame(cv, bg=C_CARD)
        win = cv.create_window((0, 0), window=inner, anchor="nw")
        tk.Frame(inner, bg=C_CARD, height=6).pack(fill="x")

        def _inner(_e=None):
            try:
                cv.coords(win, 0, 0)
                inner.update_idletasks()
                ih = max(inner.winfo_reqheight(), cv.winfo_height())
                iw = max(inner.winfo_reqwidth(), cv.winfo_width())
                cv.itemconfigure(win, width=max(1, cv.winfo_width()))
                cv.configure(scrollregion=(0, 0, iw, ih + 8))
            except Exception:
                pass

        def _canvas(e):
            try:
                cv.itemconfigure(win, width=max(1, e.width))
            except Exception:
                pass
            _inner()

        inner.bind("<Configure>", _inner)
        cv.bind("<Configure>", _canvas)
        if not hasattr(self, "_col_canvases"):
            self._col_canvases = []
        self._col_canvases.append(cv)
        wrap._col_canvas = cv
        wrap._col_inner = inner
        return wrap, inner

    def _fit_split_tab(self):
        try:
            h = max(1, int(self.scroll_canvas.winfo_height()))
            w = max(1, int(self.scroll_canvas.winfo_width()))
            name = self.active_tab.get() if hasattr(self, "active_tab") else ""
            fr = self.tab_frames.get(name) if hasattr(self, "tab_frames") else None
            if fr is not None:
                fr.pack_propagate(False)
                fr.configure(width=w, height=h)
            self.scroll_canvas.configure(scrollregion=(0, 0, w, h))
        except Exception:
            pass

    def _tab_hover_name(self, name, entering):
        if not hasattr(self, "tab_rows") or name not in self.tab_rows:
            return
        row, accent, btn = self.tab_rows[name]
        active = hasattr(self, "active_tab") and self.active_tab.get() == name
        if active:
            return
        bg = "#1a1a1a" if entering else "#000000"
        row.configure(bg=bg)
        btn.configure(bg=bg, fg="#ffffff" if entering else "#888888")
        accent.configure(bg="#000000")

    def _style_tabs(self):
        if not hasattr(self, "tab_rows"):
            return
        cur = self.active_tab.get() if hasattr(self, "active_tab") else ""
        for name, (row, accent, btn) in self.tab_rows.items():
            on = name == cur
            bg = "#1a1a1a" if on else "#000000"
            row.configure(bg=bg)
            btn.configure(bg=bg, fg="#ffffff" if on else "#888888")
            accent.configure(bg=C_ACCENT if on else "#000000")

    def _on_global_click(self, event):
        pop = getattr(self, "_combo_pop", None)
        if pop is not None:
            try:
                if event.widget.winfo_toplevel() is pop:
                    return
                cur = event.widget
                anchor = getattr(self, "_combo_anchor", None)
                while cur is not None:
                    if cur is anchor:
                        return
                    cur = getattr(cur, "master", None)
            except Exception:
                pass
            self._close_open_combo()
        w = event.widget
        protect = (
        )
        cur = w
        while cur is not None:
            if cur in protect:
                return
            try:
                cls = cur.winfo_class()
                if cls in ("Entry", "TEntry", "Text", "TCombobox", "Listbox", "Combobox"):
                    return
                if cur.winfo_toplevel() is not self.root:
                    return
            except Exception:
                pass
            cur = getattr(cur, "master", None)
        try:
            self.root.focus_set()
        except Exception:
            pass

    def _pill(self, parent, text, command, accent=False):
        btn = tk.Label(
            parent, text=text, bg=C_ACCENT, fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            pady=9, cursor="hand2",
        )
        btn.pack(fill="x", pady=(0, 6))

        def enter(e, b=btn):
            b.configure(bg=C_ACCENT_DIM)

        def leave(e, b=btn):
            b.configure(bg=C_ACCENT)

        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)
        btn.bind("<Button-1>", lambda e: command())
        return btn

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.pack_forget()

    def _show_tab(self, name):
        self.active_tab.set(name)
        self._style_tabs()
        self._clear_content()
        self.tab_frames[name].pack(fill="both", expand=True)
        self.root.after_idle(self._fit_split_tab)

    def _build_aim_tab(self):
        frame = tk.Frame(self.content, bg=C_CARD)
        self.tab_frames["Aimbot"] = frame

        cols = tk.Frame(frame, bg=C_CARD)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1, uniform="aimcols")
        cols.columnconfigure(1, weight=0)
        cols.columnconfigure(2, weight=1, uniform="aimcols")
        cols.rowconfigure(0, weight=1)

        left_wrap, left = self._make_scroll_col(cols)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tk.Frame(cols, bg=C_BORDER, width=1).grid(row=0, column=1, sticky="ns", padx=4)
        right_wrap, right = self._make_scroll_col(cols)
        right_wrap.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        aim_body = self._section(left, "AIM")

        self.aimbot_toggle_canvas, self._redraw_aimbot_toggle = self._toggle_row(
            aim_body, "Aimbot",
            get_state=lambda: self.aimbot_enabled,
            set_state=lambda v: self._set_aimbot(v),
        )

        self.aimbot_settings_frame = tk.Frame(aim_body, bg=C_CARD2)
        if self.aimbot_enabled:
            self.aimbot_settings_frame.pack(fill="x")

        aim_row = tk.Frame(self.aimbot_settings_frame, bg=C_CARD2)
        aim_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            aim_row, text="Aim Point", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.aim_point_menu = self._combo(aim_row, self.aim_point_var, ["Center", "Edge", "Head"], command=self._on_aim_point_change)
        self.aim_point_menu.pack(fill="x", pady=(2, 0))

        self.edge_bias_frame = tk.Frame(self.aimbot_settings_frame, bg=C_CARD2)
        self.edge_bias_slider, self.edge_bias_label = self._slider_row(
            self.edge_bias_frame, "Edge → Center", self.edge_bias_var, 0, 10,
            self.on_edge_bias_change, fmt="{:.0f}", snap=1,
        )

        pri_row = tk.Frame(self.aimbot_settings_frame, bg=C_CARD2)
        pri_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            pri_row, text="Target Priority", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.target_priority_menu = self._combo(pri_row, self.target_priority_var, ["None", "Closest to Crosshair", "Closest Match"], command=self._sync_hot_params)
        self.target_priority_menu.pack(fill="x", pady=(2, 0))

        km_row = tk.Frame(self.aimbot_settings_frame, bg=C_CARD2)
        km_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            km_row, text="Aim Key Mode", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.aim_key_mode_menu = self._combo(km_row, self.aim_key_mode_var, ["Hold", "Toggle"], command=self._sync_hot_params)
        self.aim_key_mode_menu.pack(fill="x", pady=(2, 0))

        self.smooth_slider, self.smooth_label = self._slider_row(
            self.aimbot_settings_frame, "Smoothness", self.smoothness_var, 0, 10,
            self.on_smoothness_change, fmt="{:.1f}", snap=0.5,
        )
        self.sens_slider, self.sens_label = self._slider_row(
            self.aimbot_settings_frame, "Sensitivity", self.sensitivity_var, 1, 10,
            self.on_sensitivity_change, fmt="{:.0f}",
        )
        self.mouse_scale_slider, self.mouse_scale_label = self._slider_row(
            self.aimbot_settings_frame, "Mouse Scale", self.mouse_scale_var, 1.0, 10.0,
            self.on_mouse_scale_change, fmt="{:.1f}",
        )

        self.aim_master_extras = tk.Frame(aim_body, bg=C_CARD2)
        self.aim_master_extras.pack(fill="x")

        self.trigger_toggle_canvas, self._redraw_trigger_toggle = self._toggle_row(
            self.aim_master_extras, "Triggerbot",
            get_state=lambda: self.triggerbot_enabled,
            set_state=lambda v: self._set_triggerbot(v),
        )
        self.trigger_frame = tk.Frame(self.aim_master_extras, bg=C_CARD2)
        tkm_row = tk.Frame(self.trigger_frame, bg=C_CARD2)
        tkm_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            tkm_row, text="Trigger Key Mode", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.trigger_key_mode_menu = self._combo(tkm_row, self.trigger_key_mode_var, ["Hold", "Toggle"], command=self._sync_hot_params)
        self.trigger_key_mode_menu.pack(fill="x", pady=(2, 0))
        tfm_row = tk.Frame(self.trigger_frame, bg=C_CARD2)
        tfm_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            tfm_row, text="Trigger Mode", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.trigger_fire_mode_menu = self._combo(
            tfm_row, self.trigger_fire_mode_var,
            ["Click on Color", "Hold while on Color"],
            command=lambda: (self._apply_trigger_fire_visibility(), self._sync_hot_params()),
        )
        self.trigger_fire_mode_menu.pack(fill="x", pady=(2, 0))
        self.trigger_scan_slider, self.trigger_scan_label = self._slider_row(
            self.trigger_frame, "Scan Area (px)", self.trigger_scan_var, 1, 100,
            self.on_trigger_scan_change, fmt="{:.0f}", snap=1,
        )
        self.trigger_reaction_slider, self.trigger_reaction_label = self._slider_row(
            self.trigger_frame, "Reaction Delay (ms)", self.trigger_reaction_var, 0, 200,
            self.on_trigger_reaction_change, fmt="{:.0f}", snap=1,
        )
        self.trigger_click_frame = tk.Frame(self.trigger_frame, bg=C_CARD2)
        self.trigger_interval_slider, self.trigger_interval_label = self._slider_row(
            self.trigger_click_frame, "Click Interval (ms)", self.trigger_interval_var, 0, 500,
            self.on_trigger_interval_change, fmt="{:.0f}", snap=1,
        )
        self.trigger_release_slider, self.trigger_release_label = self._slider_row(
            self.trigger_click_frame, "Release Time (ms)", self.trigger_release_var, 0, 500,
            self.on_trigger_release_change, fmt="{:.0f}", snap=1,
        )

        self.recoil_toggle_canvas, self._redraw_recoil_toggle = self._toggle_row(
            self.aim_master_extras, "Recoil Control",
            get_state=lambda: self.recoil_enabled,
            set_state=lambda v: self._set_recoil_enabled(v),
        )
        self.recoil_frame = tk.Frame(self.aim_master_extras, bg=C_CARD2)
        self.recoil_strength_slider, self.recoil_strength_label = self._slider_row(
            self.recoil_frame, "Recoil Strength", self.recoil_strength_var, 0, 15,
            self.on_recoil_strength_change, fmt="{:.0f}", snap=1,
        )

        self.shaky_toggle_canvas, self._redraw_shaky_toggle = self._toggle_row(
            self.aimbot_settings_frame, "Shaky Aim",
            get_state=lambda: self.shaky_enabled,
            set_state=lambda v: self._set_shaky_enabled(v),
        )
        self.shaky_frame = tk.Frame(self.aimbot_settings_frame, bg=C_CARD2)
        self.shaky_aim_slider, self.shaky_aim_label = self._slider_row(
            self.shaky_frame, "Shaky Amount", self.shaky_aim_var, 0, 50,
            self.on_shaky_aim_change, fmt="{:.0f}",
        )
        self.shaky_speed_slider, self.shaky_speed_label = self._slider_row(
            self.shaky_frame, "Shaky Speed", self.shaky_speed_var, 0, 10,
            self.on_shaky_speed_change, fmt="{:.0f}",
        )

        self.offset_toggle_canvas, self._redraw_offset_toggle = self._toggle_row(
            self.aimbot_settings_frame, "Aim Offset",
            get_state=lambda: self.offset_enabled,
            set_state=lambda v: self._set_offset_enabled(v),
        )
        self.offset_frame = tk.Frame(self.aimbot_settings_frame, bg=C_CARD2)
        self.offset_y_slider, self.offset_y_label = self._slider_row(
            self.offset_frame, "Offset Up", self.offset_y_var, -50, 50,
            self.on_offset_y_change, fmt="{:.0f}", snap=1,
        )
        self.offset_x_slider, self.offset_x_label = self._slider_row(
            self.offset_frame, "Offset Right", self.offset_x_var, -50, 50,
            self.on_offset_x_change, fmt="{:.0f}", snap=1,
        )

        self._apply_aimbot_settings_visibility()
        self._apply_feature_frames()
        try:
            self._apply_edge_bias_visibility()
        except Exception:
            pass
        try:
            self._apply_trigger_fire_visibility()
        except Exception:
            pass

        fov_body = self._section(right, "FOV")
        self.fov_toggle_canvas, self._redraw_fov_toggle = self._toggle_row(
            fov_body, "Show FOV",
            get_state=lambda: self.show_fov,
            set_state=lambda v: self._set_show_fov(v),
        )
        fm_row = tk.Frame(fov_body, bg=C_CARD2)
        fm_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            fm_row, text="FOV Mode", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.fov_mode_menu = self._combo(fm_row, self.fov_mode_var, ["Follow Cursor", "Centered"], command=self._sync_hot_params)
        self.fov_mode_menu.pack(fill="x", pady=(2, 0))

        fs_row = tk.Frame(fov_body, bg=C_CARD2)
        fs_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            fs_row, text="FOV Shape", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.fov_shape_menu = self._combo(fs_row, self.fov_shape_var, ["Circle", "Box", "Corners"], command=self.on_fov_shape_change)
        self.fov_shape_menu.pack(fill="x", pady=(2, 0))

        self.scan_slider, self.scan_size_label = self._slider_row(
            fov_body, "FOV Size", self.scan_size_var, 50, 500, self.on_scan_size_change
        )
        self.fov_thickness_slider, self.fov_thickness_label = self._slider_row(
            fov_body, "FOV Thickness", self.fov_thickness_var, 1, 5,
            self.on_fov_thickness_change, fmt="{:.0f}", snap=1,
        )
        self.fov_opacity_slider, self.fov_opacity_label = self._slider_row(
            fov_body, "FOV Opacity", self.fov_opacity_var, 0.20, 1.0,
            self.on_fov_opacity_change, fmt="{:.2f}",
        )
        self._standard_color_row(fov_body, "Circle Color", "circle")
        self._standard_color_row(fov_body, "Lock Color", "lock")


    def _show_missing_banner(self):
        missing = list(globals().get("MISSING_PACKAGES") or [])
        if not missing:
            return
        names = ", ".join(missing)
        bar = tk.Frame(self.card, bg="#3a1010", highlightthickness=1, highlightbackground="#ff4444")
        bar.pack(fill="x", padx=10, pady=(4, 4))
        tk.Label(
            bar,
            text=f"Please install {names}",
            bg="#3a1010", fg="#ff8080",
            font=("Segoe UI", 9, "bold"),
            wraplength=560, justify="left",
        ).pack(anchor="w", padx=10, pady=8)

    def _build_visuals_tab(self):
        frame = tk.Frame(self.content, bg=C_CARD)
        self.tab_frames["Visuals"] = frame

        cols = tk.Frame(frame, bg=C_CARD)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1, uniform="viscols")
        cols.columnconfigure(1, weight=0)
        cols.columnconfigure(2, weight=1, uniform="viscols")
        cols.rowconfigure(0, weight=1)

        left_wrap, left = self._make_scroll_col(cols)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tk.Frame(cols, bg=C_BORDER, width=1).grid(row=0, column=1, sticky="ns", padx=4)
        right_wrap, right = self._make_scroll_col(cols)
        right_wrap.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        ui_body = self._section(left, "UI")
        tk.Label(
            ui_body, text="UI Theme", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.theme_menu = self._combo(
            ui_body, self.theme_var, list(THEMES.keys()) + ["Custom"], command=self.on_theme_change
        )
        self.theme_menu.pack(fill="x", pady=(2, 8))
        self.custom_theme_frame = tk.Frame(ui_body, bg=C_CARD2)
        self._standard_color_row(self.custom_theme_frame, "Background", "theme_bg")
        self._standard_color_row(self.custom_theme_frame, "Foreground", "theme_fg")
        self._apply_custom_theme_visibility()
        self.menu_scale_slider, self.menu_scale_label = self._slider_row(
            ui_body, "Menu Scale", self.menu_scale_var, 50, 200,
            self.on_menu_scale_change, fmt="{:.0f}", snap=1,
        )
        self.opacity_slider, self.opacity_label = self._slider_row(
            ui_body, "Menu Opacity", self.opacity_var, 0.40, 1.0,
            self.on_opacity_change, fmt="{:.2f}",
        )

        self.streamproof_toggle_canvas, self._redraw_streamproof_toggle = self._toggle_row(
            ui_body, "Streamproof",
            get_state=lambda: self.streamproof,
            set_state=lambda v: self._set_streamproof(v),
        )
        self.aot_toggle_canvas, self._redraw_aot_toggle = self._toggle_row(
            ui_body, "Always On Top",
            get_state=lambda: self.always_on_top,
            set_state=lambda v: self._set_always_on_top(v),
        )
        self.dark_bg_toggle_canvas, self._redraw_dark_bg_toggle = self._toggle_row(
            ui_body, "Dark Background",
            get_state=lambda: self.dark_background,
            set_state=lambda v: self._set_dark_background(v),
        )
        self.lock_ind_toggle, self._redraw_lock_ind = self._toggle_row(
            ui_body, "Lock Indicator",
            get_state=lambda: self.lock_indicator,
            set_state=lambda v: self._set_lock_indicator(v),
        )
        self.lock_ind_frame = tk.Frame(ui_body, bg=C_CARD2)
        pos_l = tk.Frame(self.lock_ind_frame, bg=C_CARD2)
        pos_l.pack(fill="x", pady=(0, 8))
        tk.Label(pos_l, text="Position", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self.lock_ind_pos_menu = self._combo(
            pos_l, self.lock_ind_pos_var,
            ["Top Right", "Top Left", "Bottom Right", "Bottom Left"],
            command=self._on_indicator_pos,
        )
        self.lock_ind_pos_menu.pack(fill="x", pady=(2, 0))
        self._standard_color_row(self.lock_ind_frame, "Idle", "lock_ind_idle")
        self._standard_color_row(self.lock_ind_frame, "On", "lock_ind_on")
        self.trig_ind_toggle, self._redraw_trig_ind = self._toggle_row(
            ui_body, "Triggerbot Indicator",
            get_state=lambda: self.trigger_indicator,
            set_state=lambda v: self._set_trigger_indicator(v),
        )
        self.trig_ind_frame = tk.Frame(ui_body, bg=C_CARD2)
        pos_t = tk.Frame(self.trig_ind_frame, bg=C_CARD2)
        pos_t.pack(fill="x", pady=(0, 8))
        tk.Label(pos_t, text="Position", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self.trig_ind_pos_menu = self._combo(
            pos_t, self.trig_ind_pos_var,
            ["Top Right", "Top Left", "Bottom Right", "Bottom Left"],
            command=self._on_indicator_pos,
        )
        self.trig_ind_pos_menu.pack(fill="x", pady=(2, 0))
        self._standard_color_row(self.trig_ind_frame, "Idle", "trig_ind_idle")
        self._standard_color_row(self.trig_ind_frame, "On", "trig_ind_on")
        self._apply_indicator_frames()
        det_body = self._section(right, "DETECTION")
        self._standard_color_row(det_body, "Player Color", "esp")

        self.esp_toggle_canvas, self._redraw_esp_toggle = self._toggle_row(
            det_body, "Player Boxes",
            get_state=lambda: self.esp_enabled,
            set_state=lambda v: self._set_esp(v),
        )
        self.box_thickness_frame = tk.Frame(det_body, bg=C_CARD2)
        self.box_thickness_slider, self.box_thickness_label = self._slider_row(
            self.box_thickness_frame, "Box Thickness", self.box_thickness_var, 1, 5,
            self.on_box_thickness_change, fmt="{:.0f}", snap=1,
        )
        pbs_row = tk.Frame(self.box_thickness_frame, bg=C_CARD2)
        pbs_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            pbs_row, text="Player Box Shape", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.player_box_shape_menu = self._combo(pbs_row, self.player_box_shape_var, ["Box", "Corners"], command=self.on_player_box_shape_change)
        self.player_box_shape_menu.pack(fill="x", pady=(2, 0))
        self.corner_length_frame = tk.Frame(self.box_thickness_frame, bg=C_CARD2)
        self.corner_length_slider, self.corner_length_label = self._slider_row(
            self.corner_length_frame, "Corner Length", self.corner_length_var, 2, 40,
            self.on_corner_length_change, fmt="{:.0f}", snap=1,
        )
        self.tracers_toggle_canvas, self._redraw_tracers_toggle = self._toggle_row(
            det_body, "Player Tracers",
            get_state=lambda: self.tracers_enabled,
            set_state=lambda v: self._set_tracers(v),
        )
        self.tracer_thickness_frame = tk.Frame(det_body, bg=C_CARD2)
        self.tracer_thickness_slider, self.tracer_thickness_label = self._slider_row(
            self.tracer_thickness_frame, "Tracer Thickness", self.tracer_thickness_var, 1, 5,
            self.on_tracer_thickness_change, fmt="{:.0f}", snap=1,
        )
        to_row = tk.Frame(self.tracer_thickness_frame, bg=C_CARD2)
        to_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            to_row, text="Tracers Origin", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.tracers_origin_menu = self._combo(
            to_row, self.tracers_origin_var, ["Center", "Cursor", "Bottom"],
            command=lambda: (self._sync_hot_params(), self._draw_esp_preview()),
        )
        self.tracers_origin_menu.pack(fill="x", pady=(2, 0))

        self.esp_preview_toggle_canvas, self._redraw_esp_preview_toggle = self._toggle_row(
            det_body, "ESP Preview",
            get_state=lambda: self.esp_preview_enabled,
            set_state=lambda v: self._set_esp_preview(v),
        )
        self.esp_preview_frame = tk.Frame(det_body, bg=C_CARD2)
        self.esp_preview_canvas = tk.Canvas(
            self.esp_preview_frame, width=110, height=140, bg="#0a0a0a",
            highlightthickness=1, highlightbackground=C_BORDER, bd=0,
        )
        self.esp_preview_canvas.pack(anchor="w", pady=(0, 8))
        self.esp_preview_canvas.bind("<Configure>", lambda e: self._draw_esp_preview())

        self.debug_view_toggle_canvas, self._redraw_debug_view_toggle = self._toggle_row(
            det_body, "Show Detection View",
            get_state=lambda: self.debug_view_enabled,
            set_state=lambda v: self._set_debug_view(v),
        )

        xh_body = self._section(right, "CROSSHAIRS")
        self.xhair_toggle_canvas, self._redraw_xhair_toggle = self._toggle_row(
            xh_body, "Crosshair",
            get_state=lambda: self.xhair_enabled,
            set_state=lambda v: self._set_xhair(v),
        )
        self.xhair_settings = tk.Frame(xh_body, bg=C_CARD2)
        self.xhair_opacity_slider, self.xhair_opacity_label = self._slider_row(
            self.xhair_settings, "Opacity", self.xhair_opacity_var, 0.15, 1.0,
            self.on_xhair_opacity_change, fmt="{:.2f}",
        )
        xm_row = tk.Frame(self.xhair_settings, bg=C_CARD2)
        xm_row.pack(fill="x", pady=(0, 8))
        tk.Label(xm_row, text="Position", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self.xhair_mode_menu = self._combo(xm_row, self.xhair_mode_var, ["Follow Cursor", "Centered"], command=self._on_xhair_mode)
        self.xhair_mode_menu.pack(fill="x", pady=(2, 0))
        self.xhair_bars_toggle_canvas, self._redraw_xhair_bars_toggle = self._toggle_row(
            self.xhair_settings, "Bars",
            get_state=lambda: self.xhair_bars,
            set_state=lambda v: self._set_xhair_bars(v),
        )
        self.xhair_bars_frame = tk.Frame(self.xhair_settings, bg=C_CARD2)
        self._slider_row(self.xhair_bars_frame, "Bar Length", self.xhair_bar_len_var, 2, 40, self.on_xhair_style_change, fmt="{:.0f}", snap=1)
        self._slider_row(self.xhair_bars_frame, "Bar Width", self.xhair_bar_width_var, 1, 8, self.on_xhair_style_change, fmt="{:.0f}", snap=1)
        self._slider_row(self.xhair_bars_frame, "Bar Gap", self.xhair_bar_gap_var, 0, 20, self.on_xhair_style_change, fmt="{:.0f}", snap=1)
        self._xhair_rgb_row(self.xhair_bars_frame, "Bar Color", "bar")
        self.xhair_dot_toggle_canvas, self._redraw_xhair_dot_toggle = self._toggle_row(
            self.xhair_settings, "Dot",
            get_state=lambda: self.xhair_dot,
            set_state=lambda v: self._set_xhair_dot(v),
        )
        self.xhair_dot_frame = tk.Frame(self.xhair_settings, bg=C_CARD2)
        self._slider_row(self.xhair_dot_frame, "Dot Size", self.xhair_dot_size_var, 1, 8, self.on_xhair_style_change, fmt="{:.0f}", snap=1)
        self._xhair_rgb_row(self.xhair_dot_frame, "Dot Color", "dot")
        ds = tk.Frame(self.xhair_dot_frame, bg=C_CARD2)
        ds.pack(fill="x", pady=(0, 8))
        tk.Label(ds, text="Dot Shape", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self.xhair_dot_shape_menu = self._combo(ds, self.xhair_dot_shape_var, ["Square", "Rounded"], command=self.on_xhair_style_change)
        self.xhair_dot_shape_menu.pack(fill="x", pady=(2, 0))
        self.xhair_outline_toggle_canvas, self._redraw_xhair_outline_toggle = self._toggle_row(
            self.xhair_settings, "Outline",
            get_state=lambda: self.xhair_outline,
            set_state=lambda v: self._set_xhair_outline(v),
        )
        self.xhair_outline_frame = tk.Frame(self.xhair_settings, bg=C_CARD2)
        self._slider_row(self.xhair_outline_frame, "Outline Thickness", self.xhair_outline_thick_var, 1, 5, self.on_xhair_style_change, fmt="{:.0f}", snap=1)
        self._xhair_rgb_row(self.xhair_outline_frame, "Outline Color", "outline")
        try:
            self._apply_xhair_frames()
        except Exception:
            pass

    def _build_capture_tab(self):
        frame = tk.Frame(self.content, bg=C_CARD)
        self.tab_frames["Capture"] = frame

        cols = tk.Frame(frame, bg=C_CARD)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1, uniform="viscols")
        cols.columnconfigure(1, weight=0)
        cols.columnconfigure(2, weight=1, uniform="viscols")
        cols.rowconfigure(0, weight=1)

        left_wrap, left = self._make_scroll_col(cols)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tk.Frame(cols, bg=C_BORDER, width=1).grid(row=0, column=1, sticky="ns", padx=4)
        right_wrap, right = self._make_scroll_col(cols)
        right_wrap.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        colors_body = self._section(left, "TARGET COLORS")
        self.tolerance_slider, self.tolerance_label = self._slider_row(
            colors_body, "Color Tolerance", self.tolerance_var, 0, 100, self.on_tolerance_change
        )
        self.color_entries = []
        self.color_labels = []
        self.color_row_frames = []
        self.colors_list_frame = tk.Frame(colors_body, bg=C_CARD2)
        self.colors_btns_frame = tk.Frame(colors_body, bg=C_CARD2)
        self.colors_btns_frame.pack(fill="x", pady=(0, 4))
        self._pill(self.colors_btns_frame, "Add Color", self.add_color_picker)
        self._pill(self.colors_btns_frame, "Add Color From Screen", self.add_color_from_screen)
        self._pill(self.colors_btns_frame, "Clear All Colors", self.clear_colors)
        try:
            self._rebuild_color_rows()
        except Exception:
            pass

        scan_body = self._section(right, "SCAN RESOLUTION")
        self.scan_res_slider, self.scan_res_label = self._slider_row(
            scan_body, "Scan Resolution", self.scan_res_var, 0.25, 1.0,
            self.on_scan_res_change, fmt="{:.2f}", snap=0.05,
        )

        rates_body = self._section(right, "RATES")
        self._slider_row(rates_body, "Aim Hz", self.aim_hz_var, 10, 520, self._on_hz_change, fmt="{:.0f}", snap=1)
        self._slider_row(rates_body, "Triggerbot Hz", self.trigger_hz_var, 10, 520, self._on_hz_change, fmt="{:.0f}", snap=1)
        self._slider_row(rates_body, "Overlay Hz", self.overlay_hz_var, 10, 520, self._on_hz_change, fmt="{:.0f}", snap=1)

    def _build_keybinds_tab(self):
        frame = tk.Frame(self.content, bg=C_CARD)
        self.tab_frames["Keybinds"] = frame

        cols = tk.Frame(frame, bg=C_CARD)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1, uniform="kbcols")
        cols.columnconfigure(1, weight=0)
        cols.columnconfigure(2, weight=1, uniform="kbcols")
        cols.rowconfigure(0, weight=1)

        left_wrap, left = self._make_scroll_col(cols)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tk.Frame(cols, bg=C_BORDER, width=1).grid(row=0, column=1, sticky="ns", padx=4)
        right_wrap, right = self._make_scroll_col(cols)
        right_wrap.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        aimkb_body = self._section(left, "AIM")
        tk.Label(
            aimkb_body, text="Aim Keybind", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        aim_row = tk.Frame(aimkb_body, bg=C_CARD2)
        aim_row.pack(fill="x", pady=(2, 10))
        self.keybind_display = tk.Label(
            aim_row, textvariable=self.keybind_var, bg=C_CARD2, fg=UI_TEXT,
            font=("Segoe UI", 10, "bold"), pady=6, cursor="hand2",
        )
        self.keybind_display.pack(side="left", fill="x", expand=True)
        self.keybind_display.bind("<Button-1>", lambda e: self.start_keybind_listen())
        self._keybind_clear_btn(aim_row, lambda: self._unbind_keybind("aim"))

        tk.Label(
            aimkb_body, text="Triggerbot Keybind", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        trg_row = tk.Frame(aimkb_body, bg=C_CARD2)
        trg_row.pack(fill="x", pady=(2, 10))
        self.trigger_keybind_display = tk.Label(
            trg_row, textvariable=self.trigger_keybind_var, bg=C_CARD2, fg=UI_TEXT,
            font=("Segoe UI", 10, "bold"), pady=6, cursor="hand2",
        )
        self.trigger_keybind_display.pack(side="left", fill="x", expand=True)
        self.trigger_keybind_display.bind("<Button-1>", lambda e: self.start_trigger_keybind_listen())
        self._keybind_clear_btn(trg_row, lambda: self._unbind_keybind("trigger"))

        menukb_body = self._section(right, "MENU")
        tk.Label(
            menukb_body, text="UI Toggle Key", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        ui_row = tk.Frame(menukb_body, bg=C_CARD2)
        ui_row.pack(fill="x", pady=(2, 10))
        self.ui_toggle_display = tk.Label(
            ui_row, textvariable=self.ui_toggle_var, bg=C_CARD2, fg=UI_TEXT,
            font=("Segoe UI", 10, "bold"), pady=6, cursor="hand2",
        )
        self.ui_toggle_display.pack(side="left", fill="x", expand=True)
        self.ui_toggle_display.bind("<Button-1>", lambda e: self.start_ui_toggle_listen())
        self._keybind_clear_btn(ui_row, lambda: self._unbind_keybind("ui"))

        tk.Label(
            menukb_body, text="Kill (close app)", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        kill_row = tk.Frame(menukb_body, bg=C_CARD2)
        kill_row.pack(fill="x", pady=(2, 10))
        self.kill_key_display = tk.Label(
            kill_row, textvariable=self.kill_key_var, bg=C_CARD2, fg=UI_TEXT,
            font=("Segoe UI", 10, "bold"), pady=6, cursor="hand2",
        )
        self.kill_key_display.pack(side="left", fill="x", expand=True)
        self.kill_key_display.bind("<Button-1>", lambda e: self.start_kill_keybind_listen())
        self._keybind_clear_btn(kill_row, lambda: self._unbind_keybind("kill"))


    def _fmt_duration(self, seconds):
        seconds = max(0, int(seconds))
        d, rem = divmod(seconds, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        parts = []
        if d:
            parts.append(f"{d}d")
        if h or d:
            parts.append(f"{h}h")
        if m or h or d:
            parts.append(f"{m}m")
        parts.append(f"{s}s")
        return " ".join(parts)

    def _fmt_when(self, stamp):
        if not stamp:
            return "—"
        try:
            dt = datetime.datetime.fromisoformat(stamp)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            delta = max(0, int((datetime.datetime.now() - dt).total_seconds()))
        except Exception:
            return "—"
        months, rem = divmod(delta, 30 * 86400)
        days, rem = divmod(rem, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        parts = []
        if months:
            parts.append(f"{months} month" + ("s" if months != 1 else ""))
        if days:
            parts.append(f"{days} day" + ("s" if days != 1 else ""))
        if hours:
            parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
        if minutes:
            parts.append(f"{minutes} minute" + ("s" if minutes != 1 else ""))
        if seconds or not parts:
            parts.append(f"{seconds} second" + ("s" if seconds != 1 else ""))
        return ", ".join(parts) + " ago"

    def _session_elapsed(self):
        try:
            return max(0.0, time.time() - float(getattr(self, "_session_start", time.time())))
        except Exception:
            return 0.0

    def _refresh_playtime_labels(self):
        total = float(getattr(self, "playtime_seconds", 0.0)) + self._session_elapsed()
        last = getattr(self, "_last_used_text", None)
        if last is None:
            last = f"Last used: {self._fmt_when(getattr(self, '_last_used_shown', ''))}"
            self._last_used_text = last
        for attr, text in (
            ("playtime_total_label", f"Total: {self._fmt_duration(total)}"),
            ("playtime_session_label", f"This session: {self._fmt_duration(self._session_elapsed())}"),
            ("playtime_last_label", last),
        ):
            lab = getattr(self, attr, None)
            if lab is None:
                continue
            try:
                lab.configure(text=text)
            except Exception:
                pass

    def _load_playtime_file(self):
        for path in (PLAYTIME_PATH, CONFIG_PATH):
            try:
                if not os.path.isfile(path):
                    continue
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                sec = float(data.get("playtime_seconds") or 0)
                if sec > float(getattr(self, "playtime_seconds", 0.0)):
                    self.playtime_seconds = sec
                if data.get("first_used") and not getattr(self, "first_used", ""):
                    self.first_used = str(data.get("first_used"))
                if data.get("last_used") and not getattr(self, "last_used", ""):
                    self.last_used = str(data.get("last_used"))
                try:
                    self.session_count = max(int(getattr(self, "session_count", 0)), int(data.get("session_count") or 0))
                except Exception:
                    pass
            except Exception:
                pass

    def _flush_playtime(self, force=False):
        now = time.time()
        last = float(getattr(self, "_play_accounted", getattr(self, "_session_start", now)))
        delta = max(0.0, now - last)
        self.playtime_seconds = float(getattr(self, "playtime_seconds", 0.0)) + delta
        self._play_accounted = now
        stamp = datetime.datetime.now().replace(microsecond=0).isoformat()
        if not getattr(self, "first_used", ""):
            self.first_used = stamp
        closing = bool(getattr(self, "_playtime_closing", False))
        if closing:
            self.last_used = stamp
        if force or now - float(getattr(self, "_play_flush_t", 0)) >= 60:
            self._play_flush_t = now
            payload = {
                "playtime_seconds": float(self.playtime_seconds),
                "first_used": getattr(self, "first_used", ""),
                "last_used": getattr(self, "last_used", ""),
                "session_count": int(getattr(self, "session_count", 0)),
            }
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(PLAYTIME_PATH, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
            except Exception:
                pass
            try:
                if os.path.isfile(CONFIG_PATH):
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f) or {}
                    data.update(payload)
                    if not closing:
                        data.pop("last_used", None)
                        data["last_used"] = getattr(self, "_last_used_shown", None) or data.get("last_used") or payload.get("last_used")
                    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
            except Exception:
                pass
        self._refresh_playtime_labels()

    def _tick_playtime(self):
        try:
            self._refresh_playtime_labels()
            if time.time() - float(getattr(self, "_play_flush_t", 0)) >= 60:
                self._flush_playtime(force=True)
        except Exception:
            pass
        try:
            self.root.after(1000, self._tick_playtime)
        except Exception:
            pass

    def _start_playtime(self):
        if getattr(self, "_playtime_started", False):
            self._refresh_playtime_labels()
            return
        self._playtime_started = True
        self.session_count = int(getattr(self, "session_count", 0)) + 1
        if not getattr(self, "_last_used_shown", None):
            self._last_used_shown = str(getattr(self, "last_used", "") or "")
        self._last_used_text = f"Last used: {self._fmt_when(self._last_used_shown)}"
        if not getattr(self, "first_used", ""):
            self.first_used = datetime.datetime.now().replace(microsecond=0).isoformat()
        self._refresh_playtime_labels()
        self._flush_playtime(force=True)
        self.root.after(1000, self._tick_playtime)

    def _build_config_tab(self):
        frame = tk.Frame(self.content, bg=C_CARD)
        self.tab_frames["Config"] = frame

        cols = tk.Frame(frame, bg=C_CARD)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1, uniform="cfgcols")
        cols.columnconfigure(1, weight=0)
        cols.columnconfigure(2, weight=1, uniform="cfgcols")
        cols.rowconfigure(0, weight=1)

        left_wrap, left = self._make_scroll_col(cols)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tk.Frame(cols, bg=C_BORDER, width=1).grid(row=0, column=1, sticky="ns", padx=4)
        right_wrap, right = self._make_scroll_col(cols)
        right_wrap.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        saved_body = self._section(left, "SAVED CONFIGS")
        tk.Label(saved_body, text="Select config", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self.config_list = self._combo(
            saved_body, self.config_name_var, [],
            command=self.load_selected_config,
            on_delete=self._delete_named_config,
        )
        self.config_list.pack(fill="x", pady=(2, 8))
        tk.Label(
            saved_body,
            text=f"Configs folder:\n{CONFIG_DIR}",
            bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8),
            justify="left", wraplength=220,
        ).pack(anchor="w", pady=(12, 0))

        system_body = self._section(left, "SYSTEM")
        self.startup_toggle_canvas, self._redraw_startup_toggle = self._toggle_row(
            system_body, "Open on next startup",
            get_state=lambda: self.start_with_windows,
            set_state=lambda v: self._set_start_with_windows(v),
        )
        self.tray_toggle_canvas, self._redraw_tray_toggle = self._toggle_row(
            system_body, "Minimize to tray",
            get_state=lambda: self.minimize_to_tray,
            set_state=lambda v: self._set_minimize_to_tray(v),
        )
        self.console_toggle_canvas, self._redraw_console_toggle = self._toggle_row(
            system_body, "Show console",
            get_state=lambda: self.show_console,
            set_state=lambda v: self._set_show_console(v),
        )
        pri_row = tk.Frame(system_body, bg=C_CARD2)
        pri_row.pack(fill="x", pady=(10, 0))
        tk.Label(
            pri_row, text="CPU Priority", bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")
        self.cpu_priority_menu = self._combo(pri_row, self.cpu_priority_var, ["Low", "Below Normal", "Normal", "Above Normal", "High"], command=self._set_cpu_priority)
        self.cpu_priority_menu.pack(fill="x", pady=(2, 0))
        actions_body = self._section(right, "ACTIONS")
        self._pill(actions_body, "Save Current", self.save_config_as, accent=True)
        self._pill(actions_body, "Reset to Defaults", self.reset_defaults, accent=False)
        self._pill(actions_body, "Update NauticalUI", self._start_update, accent=False)

        play_body = self._section(right, "PLAYTIME")
        self.playtime_total_label = tk.Label(play_body, text="Total: 0m", bg=C_CARD2, fg=UI_TEXT, font=("Segoe UI", 9), anchor="w")
        self.playtime_total_label.pack(fill="x", pady=(0, 4))
        self.playtime_session_label = tk.Label(play_body, text="This session: 0m", bg=C_CARD2, fg=UI_TEXT, font=("Segoe UI", 9), anchor="w")
        self.playtime_session_label.pack(fill="x", pady=(0, 4))
        self.playtime_last_label = tk.Label(play_body, text="Last used: —", bg=C_CARD2, fg=UI_TEXT, font=("Segoe UI", 9), anchor="w")
        self.playtime_last_label.pack(fill="x")

        self.root.after(100, self.refresh_config_list)

    def _arm_hotkeys(self, seconds=0.5):
        until = time.perf_counter() + float(seconds)
        self._hotkey_arm_until = until
        self._kill_arm_at = until
        self._insert_was_down = True
        self._kill_was_down = True

    def _keybind_clear_btn(self, parent, command):
        btn = tk.Label(
            parent, text="×", bg=C_CARD2, fg=C_DANGER,
            font=("Segoe UI", 16, "bold"), padx=10, pady=2, cursor="hand2",
        )
        btn.pack(side="right", padx=(6, 0))
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e, b=btn: b.configure(fg="#ff4444"))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(fg=C_DANGER))
        return btn

    def _unbind_keybind(self, which):
        if which == "aim":
            self.keybind_var.set("None")
            self.listening_keybind = False
            try:
                self.keybind_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._sync_hot_params()
            self._arm_hotkeys()
            self._set_status("Aim keybind unbound", C_MUTED)
        elif which == "trigger":
            self.trigger_keybind_var.set("None")
            self.trigger_key_name = "None"
            self.listening_trigger_keybind = False
            try:
                if hasattr(self, "trigger_keybind_display"):
                    self.trigger_keybind_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._sync_hot_params()
            self._arm_hotkeys()
            self._set_status("Trigger keybind unbound", C_MUTED)
        elif which == "ui":
            self.ui_toggle_var.set("None")
            self.listening_ui_toggle = False
            try:
                self.ui_toggle_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._arm_hotkeys()
            self._set_status("UI toggle unbound", C_MUTED)
        elif which == "kill":
            self.kill_key_var.set("None")
            self.listening_kill_keybind = False
            try:
                self.kill_key_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._arm_hotkeys()
            self._set_status("Kill keybind unbound", C_MUTED)

    def start_keybind_listen(self):
        if self.listening_keybind or getattr(self, "listening_ui_toggle", False) or getattr(self, "listening_trigger_keybind", False) or getattr(self, "listening_kill_keybind", False):
            return
        self.listening_keybind = True
        self.keybind_display.configure(fg=C_ACCENT)
        self._set_status("Keybind in 1s… (ESC cancel)", C_ACCENT)
        self.root.after(1000, self._begin_keybind_poll)

    def _begin_keybind_poll(self):
        if not self.listening_keybind:
            return
        self._set_status("Press any key / mouse button (ESC cancel)…", C_ACCENT)
        self.root.after(30, self._poll_keybind_listen)

    def start_trigger_keybind_listen(self):
        if self.listening_keybind or getattr(self, "listening_ui_toggle", False) or getattr(self, "listening_trigger_keybind", False) or getattr(self, "listening_kill_keybind", False):
            return
        self.listening_trigger_keybind = True
        if hasattr(self, "trigger_keybind_display"):
            self.trigger_keybind_display.configure(fg=C_ACCENT)
        self._set_status("Trigger key in 1s… (ESC cancel)", C_ACCENT)
        self.root.after(1000, self._begin_trigger_keybind_poll)

    def _begin_trigger_keybind_poll(self):
        if not getattr(self, "listening_trigger_keybind", False):
            return
        self._set_status("Press triggerbot key (ESC cancel)…", C_ACCENT)
        self.root.after(30, self._poll_trigger_keybind_listen)

    def start_ui_toggle_listen(self):
        if self.listening_keybind or getattr(self, "listening_ui_toggle", False) or getattr(self, "listening_trigger_keybind", False) or getattr(self, "listening_kill_keybind", False):
            return
        self.listening_ui_toggle = True
        self.ui_toggle_display.configure(fg=C_ACCENT)
        self._set_status("UI toggle in 1s… (ESC cancel)", C_ACCENT)
        self.root.after(1000, self._begin_ui_toggle_poll)

    def _begin_ui_toggle_poll(self):
        if not getattr(self, "listening_ui_toggle", False):
            return
        self._set_status("Press a key for UI toggle (ESC cancel)…", C_ACCENT)
        self.root.after(30, self._poll_ui_toggle_listen)

    def _scan_pressed_key(self):
        if get_key_state(0x1B) & 0x8000:
            return "CANCEL"
        priority = (
            0x01, 0x02, 0x04, 0x05, 0x06,
        )
        for code in priority:
            if get_key_state(code) & 0x8000:
                return KEY_NAME_BY_CODE.get(code, f"VK_{code:02X}")
        for name, code in KEY_CODE_BY_NAME.items():
            if code == 0x1B:
                continue
            if get_key_state(code) & 0x8000:
                return name
        for code in range(0x01, 0xFF):
            if code == 0x1B:
                continue
            if get_key_state(code) & 0x8000:
                return KEY_NAME_BY_CODE.get(code, f"VK_{code:02X}")
        return None

    def _poll_keybind_listen(self):
        if not self.listening_keybind:
            return
        name = self._scan_pressed_key()
        if name == "CANCEL":
            self.listening_keybind = False
            try:
                self.keybind_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._set_status("Keybind cancelled", C_MUTED)
            return
        if name:
            self._finish_keybind(name)
            return
        self.root.after(30, self._poll_keybind_listen)

    def _poll_trigger_keybind_listen(self):
        if not getattr(self, "listening_trigger_keybind", False):
            return
        name = self._scan_pressed_key()
        if name == "CANCEL":
            self.listening_trigger_keybind = False
            try:
                if hasattr(self, "trigger_keybind_display"):
                    self.trigger_keybind_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._set_status("Trigger keybind cancelled", C_MUTED)
            return
        if name:
            self.trigger_keybind_var.set(name)
            self.trigger_key_name = name
            self.listening_trigger_keybind = False
            try:
                if hasattr(self, "trigger_keybind_display"):
                    self.trigger_keybind_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._sync_hot_params()
            self._arm_hotkeys()
            self._set_status(f"Trigger key: {name}", C_SUCCESS)
            return
        self.root.after(30, self._poll_trigger_keybind_listen)

    def _poll_ui_toggle_listen(self):
        if not getattr(self, "listening_ui_toggle", False):
            return
        name = self._scan_pressed_key()
        if name == "CANCEL":
            self.listening_ui_toggle = False
            try:
                self.ui_toggle_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._set_status("UI toggle cancelled", C_MUTED)
            return
        if name:
            self.ui_toggle_var.set(name)
            self.listening_ui_toggle = False
            try:
                self.ui_toggle_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._arm_hotkeys()
            self._set_status(f"UI toggle: {name}", C_SUCCESS)
            return
        self.root.after(30, self._poll_ui_toggle_listen)

    def start_kill_keybind_listen(self):
        if self.listening_keybind or getattr(self, "listening_ui_toggle", False) or getattr(self, "listening_trigger_keybind", False) or getattr(self, "listening_kill_keybind", False):
            return
        self.listening_kill_keybind = True
        try:
            self.kill_key_display.configure(fg=C_ACCENT)
        except Exception:
            pass
        self._set_status("Kill key in 1s… (ESC cancel)", C_ACCENT)
        self.root.after(1000, self._begin_kill_keybind_poll)

    def _begin_kill_keybind_poll(self):
        if not getattr(self, "listening_kill_keybind", False):
            return
        self._set_status("Press kill key (ESC cancel)…", C_ACCENT)
        self.root.after(30, self._poll_kill_keybind_listen)

    def _poll_kill_keybind_listen(self):
        if not getattr(self, "listening_kill_keybind", False):
            return
        name = self._scan_pressed_key()
        if name == "CANCEL":
            self.listening_kill_keybind = False
            try:
                self.kill_key_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._set_status("Kill keybind cancelled", C_MUTED)
            return
        if name:
            self.kill_key_var.set(name)
            self.listening_kill_keybind = False
            self._arm_hotkeys()
            try:
                self.kill_key_display.configure(fg=UI_TEXT)
            except Exception:
                pass
            self._set_status(f"Kill key: {name}", C_SUCCESS)
            return
        self.root.after(30, self._poll_kill_keybind_listen)

    def _finish_keybind(self, name):
        self.listening_keybind = False
        self.keybind_var.set(name)
        self.keybind_display.configure(fg=C_TEXT)
        self._sync_hot_params()
        self._arm_hotkeys()
        self._set_status(f"Aim keybind set: {name}", C_SUCCESS)

    def _poll_insert(self):
        code = self.get_key_code(self.ui_toggle_var.get())
        if not code:
            self.root.after(50, self._poll_insert)
            return
        down = bool(get_key_state(code) & 0x8000)
        if getattr(self, "listening_keybind", False) or getattr(self, "listening_ui_toggle", False) or getattr(self, "listening_trigger_keybind", False) or getattr(self, "listening_kill_keybind", False):
            self._insert_was_down = down
            self._kill_was_down = True
            self.root.after(40, self._poll_insert)
            return
        ev = getattr(self, "_show_event", None)
        if ev:
            try:
                if ctypes.windll.kernel32.WaitForSingleObject(ev, 0) == 0:
                    ctypes.windll.kernel32.ResetEvent(ev)
                    self._resume_from_tray()
            except Exception:
                pass
        if down and not self._insert_was_down:
            self.toggle_ui()
        self._insert_was_down = down

        kcode = self.get_key_code(self.kill_key_var.get()) if hasattr(self, "kill_key_var") else 0
        kdown = bool(kcode and (get_key_state(kcode) & 0x8000))
        armed = time.perf_counter() >= float(getattr(self, "_kill_arm_at", 0))
        if armed and kdown and not getattr(self, "_kill_was_down", False):
            self._on_close()
            return
        self._kill_was_down = kdown
        self.root.after(40, self._poll_insert)

    def toggle_ui(self):
        if getattr(self, "_tray_parked", False):
            self._resume_from_tray()
            return
        self.ui_visible = not self.ui_visible
        if self.ui_visible:
            self.root.deiconify()
            self._apply_topmost()
            self._apply_opacity()
        else:
            self.root.withdraw()

    def _hwnd_from_widget(self, widget):
        try:
            widget.update_idletasks()
            wid = int(widget.winfo_id())
            hwnd = ctypes.windll.user32.GetParent(wid)
            return int(hwnd or wid)
        except Exception:
            return 0

    def _streamproof_widget(self, widget):
        if widget is None:
            return
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return
        affinity = WDA_EXCLUDEFROMCAPTURE if getattr(self, "streamproof", False) else WDA_NONE
        hwnd = self._hwnd_from_widget(widget)
        if not hwnd:
            return
        try:
            ctypes.windll.user32.SetWindowDisplayAffinity(int(hwnd), int(affinity))
        except Exception:
            pass

    def _apply_streamproof(self):
        widgets = [getattr(self, "root", None)]
        if hasattr(self, "overlay"):
            widgets.append(self.overlay)
        if getattr(self, "xhair_overlay", None) is not None:
            widgets.append(self.xhair_overlay)
        if getattr(self, "_debug_win", None) is not None:
            widgets.append(self._debug_win)
        if getattr(self, "_picker_win", None) is not None:
            widgets.append(self._picker_win)
        for w in widgets:
            self._streamproof_widget(w)

    def _set_streamproof(self, value):
        self.streamproof = bool(value)
        self._apply_streamproof()
        if hasattr(self, "_redraw_streamproof_toggle"):
            try:
                self._redraw_streamproof_toggle()
            except Exception:
                pass
        self._set_status(
            "Streamproof ON" if self.streamproof else "Streamproof OFF",
            C_ACCENT if self.streamproof else C_MUTED,
        )

    def _set_cpu_priority(self, name=None):
        if name is None and hasattr(self, "cpu_priority_var"):
            name = self.cpu_priority_var.get()
        name = str(name or "Normal")
        if name not in CPU_PRIORITY_MAP:
            name = "Normal"
        self.cpu_priority = name
        if hasattr(self, "cpu_priority_var"):
            try:
                self.cpu_priority_var.set(name)
            except Exception:
                pass
        ok = apply_cpu_priority(name)
        try:
            if ok:
                self._set_status(f"CPU priority: {name}", C_ACCENT)
            else:
                self._set_status("CPU priority failed", C_DANGER)
        except Exception:
            pass

    def _set_start_with_windows(self, value):
        self.start_with_windows = bool(value)
        try:
            set_start_with_windows(self.start_with_windows)
            self.start_with_windows = bool(is_start_with_windows_enabled())
            if self.start_with_windows:
                self._set_status("Open on next startup ON", C_ACCENT)
            else:
                self._set_status("Open on next startup OFF", C_MUTED)
        except Exception as e:
            self.start_with_windows = bool(is_start_with_windows_enabled())
            try:
                self._set_status("Startup toggle failed: %s" % e, C_DANGER)
            except Exception:
                pass
        if hasattr(self, "_redraw_startup_toggle"):
            try:
                self._redraw_startup_toggle()
            except Exception:
                pass

    def _set_show_console(self, value):
        self.show_console = bool(value)
        try:
            set_console_visible(self.show_console)
        except Exception:
            pass
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.get_config_dict(), f, indent=2)
        except Exception:
            pass
        if hasattr(self, "_redraw_console_toggle"):
            try:
                self._redraw_console_toggle()
            except Exception:
                pass
        self._set_status("Show console ON" if self.show_console else "Show console OFF", C_ACCENT if self.show_console else C_MUTED)

    def _set_minimize_to_tray(self, value):
        self.minimize_to_tray = bool(value)
        if not self.minimize_to_tray:
            if getattr(self, "_tray_parked", False):
                self._resume_from_tray()
            self._stop_tray()
        if hasattr(self, "_redraw_tray_toggle"):
            try:
                self._redraw_tray_toggle()
            except Exception:
                pass
        self._set_status(
            "Minimize to tray ON" if self.minimize_to_tray else "Minimize to tray OFF",
            C_ACCENT if self.minimize_to_tray else C_MUTED,
        )

    def _set_always_on_top(self, value):
        self.always_on_top = bool(value)
        self._apply_topmost()
        if hasattr(self, "_redraw_aot_toggle"):
            try:
                self._redraw_aot_toggle()
            except Exception:
                pass

    def _content_bg(self):
        if getattr(self, "dark_background", False):
            return "#1c1c1c"
        return C_CARD

    def _set_dark_background(self, value):
        self.dark_background = bool(value)
        try:
            self.apply_theme(getattr(self, "theme", "Ocean"), rebuild=True)
        except Exception:
            self._apply_content_background()
        if hasattr(self, "_redraw_dark_bg_toggle"):
            try:
                self._redraw_dark_bg_toggle()
            except Exception:
                pass

    def _apply_content_background(self):
        bg = self._content_bg()
        try:
            if hasattr(self, "card"):
                self.card.configure(bg=bg)
            if hasattr(self, "top_bar"):
                self.top_bar.configure(bg=bg)
            if hasattr(self, "close_btn"):
                self.close_btn.configure(bg=bg, fg="#ff0000")
            if hasattr(self, "foot"):
                self.foot.configure(bg=bg)
            if hasattr(self, "scroll_canvas"):
                self.scroll_canvas.configure(bg=bg)
            if hasattr(self, "content"):
                self.content.configure(bg=bg)
            if hasattr(self, "resize_grip"):
                self.resize_grip.configure(bg=bg)
        except Exception:
            pass

    def _apply_topmost(self):
        try:
            self.root.attributes("-topmost", bool(self.always_on_top))
            if self.always_on_top:
                self.root.lift()
        except Exception:
            pass

    def _apply_opacity(self):
        try:
            self.root.attributes("-alpha", float(self.menu_opacity))
        except Exception:
            pass

    def _set_status(self, text, fg=C_TEXT):
        now = time.perf_counter()
        if text == self._last_status_text and (now - self._last_status_t) < 0.12:
            return
        self._last_status_t = now
        self._last_status_text = text

    def get_config_dict(self):
        return {
            "keybind": self.keybind_var.get(),
            "ui_toggle_key": self.ui_toggle_var.get(),
            "kill_key": self.kill_key_var.get() if hasattr(self, "kill_key_var") else "None",
            "aim_point": self.aim_point_var.get(),
            "edge_bias": float(getattr(self, "edge_bias", 0)),
            "target_priority": self.target_priority_var.get() if hasattr(self, "target_priority_var") else "None",
            "aim_key_mode": self.aim_key_mode_var.get(),
            "show_fov": bool(self.show_fov),
            "fov_mode": self.fov_mode_var.get() if hasattr(self, "fov_mode_var") else getattr(self, "fov_mode", "Follow Cursor"),
            "fov_shape": self.fov_shape_var.get() if hasattr(self, "fov_shape_var") else getattr(self, "fov_shape", "Circle"),
            "player_box_shape": self.player_box_shape_var.get() if hasattr(self, "player_box_shape_var") else getattr(self, "player_box_shape", "Box"),
            "corner_length": int(getattr(self, "corner_length", 8)),
            "esp_enabled": bool(getattr(self, "esp_enabled", False)),
            "debug_view_enabled": bool(getattr(self, "debug_view_enabled", False)),
            "esp_preview_enabled": bool(getattr(self, "esp_preview_enabled", False)),
            "esp_color": getattr(self, "esp_color", "white"),
            "box_thickness": int(getattr(self, "box_thickness", 1)),
            "tracers_enabled": bool(getattr(self, "tracers_enabled", False)),
            "tracer_thickness": int(getattr(self, "tracer_thickness", 1)),
            "tracers_origin": self.tracers_origin_var.get() if hasattr(self, "tracers_origin_var") else getattr(self, "tracers_origin", "Center"),
            "scan_size": int(self.scan_size),
            "scan_res": float(getattr(self, "scan_res", 1.0)),
            "tolerance": int(self.tolerance),
            "smoothness": float(self.smoothness),
            "sensitivity": float(self.sensitivity),
            "mouse_scale": float(self.mouse_scale),
            "shaky_aim": float(getattr(self, "shaky_aim", 10)),
            "shaky_speed": float(getattr(self, "shaky_speed", 5)),
            "offset_enabled": bool(getattr(self, "offset_enabled", False)),
            "offset_y": float(getattr(self, "offset_y", 0)),
            "offset_x": float(getattr(self, "offset_x", 0)),
            "triggerbot_enabled": bool(getattr(self, "triggerbot_enabled", False)),
            "recoil_enabled": bool(getattr(self, "recoil_enabled", False)),
            "recoil_strength": float(getattr(self, "recoil_strength", 2.0)),
            "trigger_scan_size": int(getattr(self, "trigger_scan_size", 4)),
            "trigger_keybind": self.trigger_keybind_var.get() if hasattr(self, "trigger_keybind_var") else getattr(self, "trigger_key_name", "XBUTTON5"),
            "trigger_reaction_ms": float(getattr(self, "trigger_reaction_ms", 0)),
            "trigger_interval_ms": float(getattr(self, "trigger_interval_ms", 50)),
            "trigger_release_ms": float(getattr(self, "trigger_release_ms", 0)),
            "trigger_key_mode": (
                self.trigger_key_mode_var.get()
                if hasattr(self, "trigger_key_mode_var")
                else getattr(self, "trigger_key_mode", "Hold")
            ),
            "trigger_fire_mode": (
                self.trigger_fire_mode_var.get()
                if hasattr(self, "trigger_fire_mode_var")
                else getattr(self, "trigger_fire_mode", "Click on Color")
            ),
            "menu_opacity": float(self.menu_opacity),
            "theme": getattr(self, "theme", "Ocean"),
            "custom_bg": list(parse_rgb(getattr(self, "custom_bg", (31, 10, 10)))),
            "custom_fg": list(parse_rgb(getattr(self, "custom_fg", (255, 26, 26)))),
            "circle_color": self.circle_color_var.get(),
            "lock_color": self.lock_color_var.get() if hasattr(self, "lock_color_var") else self.lock_color,
            "lock_indicator": bool(getattr(self, "lock_indicator", False)),
            "trigger_indicator": bool(getattr(self, "trigger_indicator", False)),
            "lock_ind_idle": list(parse_rgb(getattr(self, "lock_ind_idle", (255, 255, 255)))),
            "lock_ind_on": list(parse_rgb(getattr(self, "lock_ind_on", (255, 0, 0)))),
            "trig_ind_idle": list(parse_rgb(getattr(self, "trig_ind_idle", (255, 255, 255)))),
            "trig_ind_on": list(parse_rgb(getattr(self, "trig_ind_on", (0, 255, 0)))),
            "lock_ind_pos": getattr(self, "lock_ind_pos_var", None).get() if hasattr(self, "lock_ind_pos_var") else getattr(self, "lock_ind_pos", "Top Right"),
            "trig_ind_pos": getattr(self, "trig_ind_pos_var", None).get() if hasattr(self, "trig_ind_pos_var") else getattr(self, "trig_ind_pos", "Top Left"),
            "fov_thickness": int(getattr(self, "fov_thickness", 2)),
            "fov_opacity": float(getattr(self, "fov_opacity", 1.0)),
            "target_colors": [list(c) for c in self.target_colors],
            "xhair_enabled": bool(getattr(self, "xhair_enabled", False)),
            "xhair_mode": self.xhair_mode_var.get() if hasattr(self, "xhair_mode_var") else getattr(self, "xhair_mode", "Follow Cursor"),
            "xhair_opacity": float(getattr(self, "xhair_opacity", 1.0)),
            "xhair_bars": bool(getattr(self, "xhair_bars", False)),
            "xhair_bar_len": float(getattr(self, "xhair_bar_len", 10)),
            "xhair_bar_width": float(getattr(self, "xhair_bar_width", 2)),
            "xhair_bar_gap": float(getattr(self, "xhair_bar_gap", 3)),
            "xhair_bar_color": list(parse_rgb(getattr(self, "xhair_bar_color", (255, 255, 255)))),
            "xhair_dot": bool(getattr(self, "xhair_dot", False)),
            "xhair_dot_size": float(getattr(self, "xhair_dot_size", 2)),
            "xhair_dot_color": list(parse_rgb(getattr(self, "xhair_dot_color", (255, 255, 255)))),
            "xhair_dot_shape": self.xhair_dot_shape_var.get() if hasattr(self, "xhair_dot_shape_var") else getattr(self, "xhair_dot_shape", "Rounded"),
            "xhair_outline": bool(getattr(self, "xhair_outline", False)),
            "xhair_outline_thick": float(getattr(self, "xhair_outline_thick", 1)),
            "xhair_outline_color": list(parse_rgb(getattr(self, "xhair_outline_color", (255, 255, 255)))),
            "always_on_top": bool(self.always_on_top),
            "start_with_windows": bool(getattr(self, "start_with_windows", False)),
            "minimize_to_tray": bool(getattr(self, "minimize_to_tray", True)),
            "cpu_priority": getattr(self, "cpu_priority_var", None).get() if hasattr(self, "cpu_priority_var") else getattr(self, "cpu_priority", "Normal"),
            "show_console": bool(getattr(self, "show_console", False)),
            "streamproof": bool(getattr(self, "streamproof", False)),
            "dark_background": bool(getattr(self, "dark_background", False)),
            "ui_width": int(self.root.winfo_width()),
            "ui_height": int(self.root.winfo_height()),
            "aim_hz": int(getattr(self, "aim_hz", 520)),
            "trigger_hz": int(getattr(self, "trigger_hz", 520)),
            "overlay_hz": int(getattr(self, "overlay_hz", 520)),
            "playtime_seconds": float(getattr(self, "playtime_seconds", 0.0)),
            "first_used": str(getattr(self, "first_used", "") or ""),
            "last_used": str(getattr(self, "last_used", "") or ""),
            "session_count": int(getattr(self, "session_count", 0)),
        }

    def apply_config_dict(self, data):
        self.keybind_var.set(data.get("keybind", "XBUTTON1"))
        self.ui_toggle_var.set(data.get("ui_toggle_key", "INSERT"))
        if hasattr(self, "kill_key_var"):
            self.kill_key_var.set(data.get("kill_key", "None"))
        self.aim_point_var.set(data.get("aim_point", "Center"))
        self.edge_bias = max(0.0, min(10.0, float(data.get("edge_bias", 0))))
        if hasattr(self, "edge_bias_var"):
            self.edge_bias_var.set(self.edge_bias)
        tp = data.get("target_priority", "None")
        if tp not in ("None", "Closest to Crosshair", "Closest Match"):
            tp = "None"
        if hasattr(self, "target_priority_var"):
            self.target_priority_var.set(tp)
        self.aim_key_mode_var.set(data.get("aim_key_mode", "Toggle"))
        self.show_fov = bool(data.get("show_fov", True))
        fm = data.get("fov_mode", "Follow Cursor")
        if fm not in ("Follow Cursor", "Centered"):
            fm = "Follow Cursor"
        self.fov_mode = fm
        if hasattr(self, "fov_mode_var"):
            self.fov_mode_var.set(fm)
        fs = data.get("fov_shape", "Circle")
        if fs not in ("Circle", "Box"):
            fs = "Circle"
        self.fov_shape = fs
        if hasattr(self, "fov_shape_var"):
            self.fov_shape_var.set(fs)
        pbs = data.get("player_box_shape", "Box")
        if pbs not in ("Box", "Corners"):
            pbs = "Box"
        self.player_box_shape = pbs
        if hasattr(self, "player_box_shape_var"):
            self.player_box_shape_var.set(pbs)
        self.corner_length = max(2, min(40, int(data.get("corner_length", 8))))
        if hasattr(self, "corner_length_var"):
            self.corner_length_var.set(self.corner_length)
        self.esp_enabled = bool(data.get("esp_enabled", False))
        self.debug_view_enabled = bool(data.get("debug_view_enabled", False))
        self.esp_preview_enabled = bool(data.get("esp_preview_enabled", False))
        self.box_thickness = max(1, min(5, int(data.get("box_thickness", 1))))
        self.tracers_enabled = bool(data.get("tracers_enabled", False))
        self.tracer_thickness = max(1, min(5, int(data.get("tracer_thickness", 1))))
        to = data.get("tracers_origin", "Cursor")
        if to not in ("Center", "Cursor", "Bottom"):
            to = "Center"
        self.tracers_origin = to
        if hasattr(self, "tracers_origin_var"):
            self.tracers_origin_var.set(to)
        if hasattr(self, "esp_color_var"):
            self.esp_color_var.set(data.get("esp_color", "lime"))
            self.esp_color = self.esp_color_var.get()
        if hasattr(self, "box_thickness_var"):
            self.box_thickness_var.set(self.box_thickness)
        if hasattr(self, "tracer_thickness_var"):
            self.tracer_thickness_var.set(self.tracer_thickness)
        try:
            self._apply_detection_frames()
        except Exception:
            pass
        self._apply_fov_visibility()
        self.scan_size = int(data.get("scan_size", 240))
        self.scan_res = max(0.25, min(1.0, float(data.get("scan_res", 1.0))))
        self.tolerance = int(data.get("tolerance", 50))
        self.smoothness = round(float(data.get("smoothness", 0)) * 2) / 2.0
        self.sensitivity = float(data.get("sensitivity", 10))
        self.mouse_scale = float(data.get("mouse_scale", 1.0))
        self.shaky_enabled = bool(data.get("shaky_enabled", False))
        self.shaky_aim = float(data.get("shaky_aim", 10))
        self.shaky_speed = float(data.get("shaky_speed", 5))
        self.offset_enabled = bool(data.get("offset_enabled", False))
        self.offset_y = float(data.get("offset_y", 0))
        self.offset_x = float(data.get("offset_x", 0))
        self.aimbot_enabled = bool(data.get("aimbot_enabled", True))

        self.triggerbot_enabled = bool(data.get("triggerbot_enabled", False))
        self.recoil_enabled = bool(data.get("recoil_enabled", False))
        self.recoil_strength = float(data.get("recoil_strength", 2.0))
        if hasattr(self, "recoil_strength_var"):
            self.recoil_strength_var.set(self.recoil_strength)
        self.trigger_scan_size = max(1, min(100, int(data.get("trigger_scan_size", 4))))
        self.trigger_key_name = data.get("trigger_keybind", "XBUTTON2")
        self.trigger_reaction_ms = max(0.0, min(200.0, float(data.get("trigger_reaction_ms", 0))))
        self.trigger_interval_ms = max(0.0, min(500.0, float(data.get("trigger_interval_ms", 50))))
        self.trigger_release_ms = max(0.0, min(500.0, float(data.get("trigger_release_ms", 0))))
        tkm = str(data.get("trigger_key_mode", "Hold"))
        if tkm not in ("Hold", "Toggle"):
            tkm = "Hold"
        self.trigger_key_mode = tkm
        if hasattr(self, "trigger_key_mode_var"):
            self.trigger_key_mode_var.set(tkm)
        tfm = str(data.get("trigger_fire_mode", "Click on Color"))
        if tfm not in ("Click on Color", "Hold while on Color"):
            tfm = "Click on Color"
        self.trigger_fire_mode = tfm
        if hasattr(self, "trigger_fire_mode_var"):
            self.trigger_fire_mode_var.set(tfm)
        self.menu_opacity = float(data.get("menu_opacity", 1.0))
        theme = data.get("theme", "Default")
        if theme != "Custom" and theme not in THEMES:
            theme = "Ocean"
        self.theme = theme
        try:
            self.custom_bg = parse_rgb(data.get("custom_bg", getattr(self, "custom_bg", (31, 10, 10))))
            self.custom_fg = parse_rgb(data.get("custom_fg", getattr(self, "custom_fg", (255, 26, 26))))
        except Exception:
            pass
        if hasattr(self, "theme_var"):
            self.theme_var.set(theme)
        self.circle_color_var.set(data.get("circle_color", "white"))
        self.circle_color = self.circle_color_var.get()
        self.xhair_enabled = bool(data.get("xhair_enabled", False))
        self.xhair_mode = data.get("xhair_mode", "Follow Cursor")
        if self.xhair_mode not in ("Follow Cursor", "Centered"):
            self.xhair_mode = "Follow Cursor"
        self.xhair_opacity = float(data.get("xhair_opacity", 1.0))
        self.xhair_bars = bool(data.get("xhair_bars", False))
        self.xhair_bar_len = float(data.get("xhair_bar_len", 10))
        self.xhair_bar_width = float(data.get("xhair_bar_width", 2))
        self.xhair_bar_gap = float(data.get("xhair_bar_gap", 3))
        self.xhair_bar_color = parse_rgb(data.get("xhair_bar_color", (255, 255, 255)))
        self.xhair_dot = bool(data.get("xhair_dot", False))
        self.xhair_dot_size = float(data.get("xhair_dot_size", 2))
        self.xhair_dot_color = parse_rgb(data.get("xhair_dot_color", (255, 255, 255)))
        self.xhair_dot_shape = data.get("xhair_dot_shape", "Rounded")
        self.xhair_outline = bool(data.get("xhair_outline", False))
        self.xhair_outline_thick = float(data.get("xhair_outline_thick", 1))
        self.xhair_outline_color = parse_rgb(data.get("xhair_outline_color", (255, 255, 255)))
        for name, val in (
            ("xhair_mode_var", self.xhair_mode),
            ("xhair_opacity_var", self.xhair_opacity),
            ("xhair_bar_len_var", self.xhair_bar_len),
            ("xhair_bar_width_var", self.xhair_bar_width),
            ("xhair_bar_gap_var", self.xhair_bar_gap),
            ("xhair_dot_size_var", self.xhair_dot_size),
            ("xhair_dot_shape_var", self.xhair_dot_shape),
            ("xhair_outline_thick_var", self.xhair_outline_thick),
        ):
            if hasattr(self, name):
                try:
                    getattr(self, name).set(val)
                except Exception:
                    pass
        try:
            self._apply_xhair_frames()
            self._refresh_xhair_color_rows()
            self._redraw_xhair()
        except Exception:
            pass
        self.lock_color_var.set(data.get("lock_color", "red"))
        self.lock_color = self.lock_color_var.get()
        self.lock_indicator = bool(data.get("lock_indicator", False))
        self.trigger_indicator = bool(data.get("trigger_indicator", False))
        self.lock_ind_idle = parse_rgb(data.get("lock_ind_idle", (255, 255, 255)))
        self.lock_ind_on = parse_rgb(data.get("lock_ind_on", (255, 0, 0)))
        self.trig_ind_idle = parse_rgb(data.get("trig_ind_idle", (255, 255, 255)))
        self.trig_ind_on = parse_rgb(data.get("trig_ind_on", (0, 255, 0)))
        self.lock_ind_pos = data.get("lock_ind_pos", "Top Right")
        self.trig_ind_pos = data.get("trig_ind_pos", "Top Left")
        if self.lock_ind_pos not in ("Top Right", "Top Left", "Bottom Right", "Bottom Left"):
            self.lock_ind_pos = "Top Right"
        if self.trig_ind_pos not in ("Top Right", "Top Left", "Bottom Right", "Bottom Left"):
            self.trig_ind_pos = "Top Left"
        if hasattr(self, "lock_ind_pos_var"):
            self.lock_ind_pos_var.set(self.lock_ind_pos)
        if hasattr(self, "trig_ind_pos_var"):
            self.trig_ind_pos_var.set(self.trig_ind_pos)
        self.fov_thickness = max(1, min(5, int(data.get("fov_thickness", 1))))
        self.fov_opacity = max(0.2, min(1.0, float(data.get("fov_opacity", 1.0))))
        self.always_on_top = bool(data.get("always_on_top", True))
        want_startup = bool(data.get("start_with_windows", is_start_with_windows_enabled()))
        try:
            set_start_with_windows(want_startup)
        except Exception:
            pass
        self.start_with_windows = bool(is_start_with_windows_enabled())
        self.minimize_to_tray = bool(data.get("minimize_to_tray", True))
        if hasattr(self, "_redraw_tray_toggle"):
            try:
                self._redraw_tray_toggle()
            except Exception:
                pass
        try:
            if not self.minimize_to_tray:
                self._stop_tray()
        except Exception:
            pass
        cp = str(data.get("cpu_priority", "Normal"))
        if cp not in CPU_PRIORITY_MAP:
            cp = "Normal"
        self.cpu_priority = cp
        if hasattr(self, "cpu_priority_var"):
            self.cpu_priority_var.set(cp)
        try:
            apply_cpu_priority(cp)
        except Exception:
            pass
        self.show_console = bool(data.get("show_console", False))
        try:
            set_console_visible(self.show_console)
        except Exception:
            pass
        try:
            if "playtime_seconds" in data:
                incoming = float(data.get("playtime_seconds") or 0)
                if incoming > 0:
                    self.playtime_seconds = max(float(getattr(self, "playtime_seconds", 0.0)), incoming)
        except Exception:
            pass
        if data.get("first_used") and not getattr(self, "first_used", ""):
            self.first_used = str(data.get("first_used"))
        if data.get("last_used"):
            self.last_used = str(data.get("last_used"))
            if not getattr(self, "_last_used_shown", ""):
                self._last_used_shown = self.last_used
        try:
            self.session_count = max(int(getattr(self, "session_count", 0)), int(data.get("session_count", 0) or 0))
        except Exception:
            pass
        def _hz(key, default=520):
            try:
                return max(10, min(520, int(round(float(data.get(key, default))))))
            except Exception:
                return default
        self.aim_hz = _hz("aim_hz")
        self.trigger_hz = _hz("trigger_hz")
        self.overlay_hz = _hz("overlay_hz", 60)
        if hasattr(self, "aim_hz_var"):
            self.aim_hz_var.set(self.aim_hz)
        if hasattr(self, "trigger_hz_var"):
            self.trigger_hz_var.set(self.trigger_hz)
        if hasattr(self, "overlay_hz_var"):
            self.overlay_hz_var.set(self.overlay_hz)
        self.streamproof = bool(data.get("streamproof", True))
        self.dark_background = bool(data.get("dark_background", True))
        self._apply_topmost()
        try:
            self._apply_streamproof()
        except Exception:
            pass
        try:
            self._apply_content_background()
        except Exception:
            pass
        try:
            w = int(data.get("ui_width", 0))
            h = int(data.get("ui_height", 0))
            if w >= 560 and h >= 420:
                x, y = self.root.winfo_x(), self.root.winfo_y()
                self.root.geometry(f"{w}x{h}+{x}+{y}")
                self.root.after_idle(self._refresh_scroll)
        except Exception:
            pass

        self.scan_size_var.set(self.scan_size)
        if hasattr(self, "scan_res_var"):
            self.scan_res_var.set(getattr(self, "scan_res", 1.0))
        self.tolerance_var.set(self.tolerance)
        self.smoothness_var.set(self.smoothness)
        self.sensitivity_var.set(self.sensitivity)
        self.mouse_scale_var.set(self.mouse_scale)
        if hasattr(self, "shaky_aim_var"):
            self.shaky_aim_var.set(getattr(self, "shaky_aim", 10))
        if hasattr(self, "shaky_speed_var"):
            self.shaky_speed_var.set(getattr(self, "shaky_speed", 5))
        if hasattr(self, "offset_y_var"):
            self.offset_y_var.set(getattr(self, "offset_y", 0))
        if hasattr(self, "offset_x_var"):
            self.offset_x_var.set(getattr(self, "offset_x", 0))

        if hasattr(self, "trigger_keybind_var"):
            self.trigger_keybind_var.set(getattr(self, "trigger_key_name", "XBUTTON5"))
        if hasattr(self, "trigger_scan_var"):
            self.trigger_scan_var.set(getattr(self, "trigger_scan_size", 4))
        if hasattr(self, "trigger_reaction_var"):
            self.trigger_reaction_var.set(getattr(self, "trigger_reaction_ms", 0))
        if hasattr(self, "trigger_interval_var"):
            self.trigger_interval_var.set(getattr(self, "trigger_interval_ms", 50))
        if hasattr(self, "trigger_release_var"):
            self.trigger_release_var.set(getattr(self, "trigger_release_ms", 0))
        if hasattr(self, "trigger_key_mode_var"):
            self.trigger_key_mode_var.set(getattr(self, "trigger_key_mode", "Hold"))
        if hasattr(self, "trigger_fire_mode_var"):
            self.trigger_fire_mode_var.set(getattr(self, "trigger_fire_mode", "Click on Color"))
        self.opacity_var.set(self.menu_opacity)
        try:
            self.menu_scale = max(50.0, min(200.0, float(data.get("menu_scale", 100))))
        except Exception:
            self.menu_scale = 100.0
        if hasattr(self, "menu_scale_var"):
            self.menu_scale_var.set(self.menu_scale)
        try:
            self._apply_menu_scale(rebuild=False)
        except Exception:
            pass
        try:
            self._apply_feature_frames()
        except Exception:
            pass
        if hasattr(self, "fov_thickness_var"):
            self.fov_thickness_var.set(self.fov_thickness)
        if hasattr(self, "fov_opacity_var"):
            self.fov_opacity_var.set(self.fov_opacity)

        def _set_entry(w, s):
            if w is None:
                return
            try:
                w.delete(0, tk.END)
                w.insert(0, s)
            except Exception:
                try:
                    w.config(text=s)
                except Exception:
                    pass

        _set_entry(getattr(self, "scan_size_label", None), f"{self.scan_size:.0f}")
        _set_entry(getattr(self, "scan_res_label", None), f"{getattr(self, 'scan_res', 1.0):.2f}")
        _set_entry(getattr(self, "tolerance_label", None), f"{self.tolerance:.0f}")
        _set_entry(getattr(self, "smooth_label", None), f"{self.smoothness:.1f}")
        _set_entry(getattr(self, "sens_label", None), f"{self.sensitivity:.0f}")
        _set_entry(getattr(self, "mouse_scale_label", None), f"{self.mouse_scale:.1f}")
        _set_entry(getattr(self, "shaky_aim_label", None), f"{getattr(self, 'shaky_aim', 10):.0f}")
        _set_entry(getattr(self, "shaky_speed_label", None), f"{getattr(self, 'shaky_speed', 5):.0f}")
        _set_entry(getattr(self, "offset_y_label", None), f"{getattr(self, 'offset_y', 0):.0f}")
        _set_entry(getattr(self, "offset_x_label", None), f"{getattr(self, 'offset_x', 0):.0f}")
        _set_entry(getattr(self, "trigger_scan_label", None), f"{getattr(self, 'trigger_scan_size', 4):.0f}")
        _set_entry(getattr(self, "trigger_reaction_label", None), f"{getattr(self, 'trigger_reaction_ms', 0):.0f}")
        _set_entry(getattr(self, "trigger_interval_label", None), f"{getattr(self, 'trigger_interval_ms', 50):.0f}")
        _set_entry(getattr(self, "trigger_release_label", None), f"{getattr(self, 'trigger_release_ms', 0):.0f}")
        _set_entry(getattr(self, "opacity_label", None), f"{self.menu_opacity:.2f}")
        _set_entry(getattr(self, "fov_thickness_label", None), f"{self.fov_thickness:.0f}")
        _set_entry(getattr(self, "fov_opacity_label", None), f"{self.fov_opacity:.2f}")

        self.target_colors = [tuple(c) for c in data.get("target_colors", [])]
        try:
            self._rebuild_color_rows()
        except Exception:
            pass

        self.update_overlay_size()
        self._apply_opacity()
        self._sync_hot_params()
        self.apply_theme(self.theme, rebuild=True)

    def refresh_config_list(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            names = sorted(
                f[:-5] for f in os.listdir(CONFIG_DIR) if f.lower().endswith(".json") and f.lower() != "playtime.json"
            )
        except Exception:
            names = []
        if names and self.config_name_var.get() not in names:
            self.config_name_var.set(names[0] if names else "")
        if hasattr(self, "config_list") and hasattr(self.config_list, "set_values"):
            self.config_list.set_values(names)

    def save_config_as(self):
        name = simpledialog.askstring("Save Config", "Config name:", parent=self.root)
        if not name:
            return
        safe = "".join(c for c in name.strip() if c.isalnum() or c in ("-", "_", " ")).strip()
        safe = safe.replace(" ", "_")
        if not safe:
            self._set_status("Invalid name", C_DANGER)
            return
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            path = os.path.join(CONFIG_DIR, safe + ".json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.get_config_dict(), f, indent=2)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.get_config_dict(), f, indent=2)
            self.config_name_var.set(safe)
            self.refresh_config_list()
            self._set_status(f"Saved config: {safe}", C_SUCCESS)
        except Exception as e:
            self._set_status(f"Save failed: {e}", C_DANGER)

    def _delete_named_config(self, name):
        if not name:
            return
        self.config_name_var.set(name)
        self.delete_selected_config()

    def load_selected_config(self):

        name = self.config_name_var.get().strip()
        if not name:
            self._set_status("No config selected", C_MUTED)
            return
        path = os.path.join(CONFIG_DIR, name + ".json")
        if not os.path.exists(path):
            self._set_status("Config not found", C_DANGER)
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.apply_config_dict(data)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._set_status(f"Loaded: {name}", C_SUCCESS)
        except Exception as e:
            self._set_status(f"Load failed: {e}", C_DANGER)

    def delete_selected_config(self):
        name = self.config_name_var.get().strip()
        if not name:
            return
        path = os.path.join(CONFIG_DIR, name + ".json")
        try:
            if os.path.exists(path):
                os.remove(path)
            self.config_name_var.set("")
            self.refresh_config_list()
            self._set_status(f"Deleted: {name}", C_MUTED)
        except Exception as e:
            self._set_status(f"Delete failed: {e}", C_DANGER)

    def load_config(self, silent=False):
        path = CONFIG_PATH
        if not os.path.exists(path):
            if not silent:
                self._set_status("No config file found", C_MUTED)
            self.refresh_config_list()
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.apply_config_dict(data)
            if not silent:
                self._set_status("Config loaded", C_SUCCESS)
        except Exception as e:
            if not silent:
                self._set_status(f"Load failed: {e}", C_DANGER)
        self.refresh_config_list()

    def reset_defaults(self):
        self.apply_config_dict({
            "keybind": "XBUTTON1",
            "ui_toggle_key": "INSERT",
            "kill_key": "None",
            "aim_point": "Center",
            "edge_bias": 0.0,
            "target_priority": "None",
            "aim_key_mode": "Toggle",
            "show_fov": True,
            "fov_mode": "Follow Cursor",
            "fov_shape": "Circle",
            "player_box_shape": "Box",
            "corner_length": 8,
            "esp_enabled": False,
            "debug_view_enabled": False,
            "esp_preview_enabled": False,
            "esp_color": "white",
            "box_thickness": 1,
            "tracers_enabled": False,
            "tracer_thickness": 1,
            "tracers_origin": "Cursor",
            "scan_size": 240,
            "scan_res": 1.0,
            "tolerance": 50,
            "smoothness": 0.0,
            "sensitivity": 10.0,
            "mouse_scale": 1.0,
            "shaky_enabled": False,
            "shaky_aim": 10.0,
            "shaky_speed": 5.0,
            "offset_enabled": False,
            "offset_y": 0.0,
            "offset_x": 0.0,
            "aimbot_enabled": True,
            "triggerbot_enabled": False,
            "recoil_enabled": False,
            "recoil_strength": 2.0,
            "trigger_scan_size": 4,
            "trigger_keybind": "XBUTTON2",
            "trigger_reaction_ms": 0.0,
            "trigger_interval_ms": 50.0,
            "trigger_release_ms": 0.0,
            "trigger_key_mode": "Hold",
            "trigger_fire_mode": "Click on Color",
            "menu_opacity": 1.0,
            "menu_scale": 100.0,
            "theme": "Default",
            "circle_color": "white",
            "lock_indicator": False,
            "trigger_indicator": False,
            "lock_ind_idle": [255, 255, 255],
            "lock_ind_on": [255, 0, 0],
            "trig_ind_idle": [255, 255, 255],
            "trig_ind_on": [0, 255, 0],
            "lock_ind_pos": "Top Right",
            "trig_ind_pos": "Top Left",
            "lock_color": "red",
            "fov_thickness": 1,
            "fov_opacity": 1.0,
            "target_colors": [],
            "xhair_enabled": False,
            "xhair_mode": "Follow Cursor",
            "xhair_opacity": 1.0,
            "xhair_bars": False,
            "xhair_bar_len": 10.0,
            "xhair_bar_width": 2.0,
            "xhair_bar_gap": 3.0,
            "xhair_bar_color": [255, 255, 255],
            "xhair_dot": False,
            "xhair_dot_size": 2.0,
            "xhair_dot_color": [255, 255, 255],
            "xhair_dot_shape": "Rounded",
            "xhair_outline": False,
            "xhair_outline_thick": 1.0,
            "xhair_outline_color": [255, 255, 255],
            "always_on_top": True,
            "start_with_windows": False,
            "minimize_to_tray": True,
            "cpu_priority": "Normal",
            "show_console": False,
            "streamproof": True,
            "dark_background": True,
            "ui_width": 760,
            "ui_height": 510,
            "aim_hz": 520,
            "trigger_hz": 520,
            "overlay_hz": 60,
        })
        self._set_status("Defaults restored", C_MUTED)

    def add_color_picker(self):
        if len(getattr(self, "target_colors", [])) >= 16:
            self._set_status("Max 16 colors", C_DANGER)
            return
        c = self._ask_basic_color((255, 255, 255))
        if not c:
            return
        self.target_colors.append(tuple(int(x) for x in c))
        self._rebuild_color_rows()
        self._sync_hot_params()
        self._set_status(f"Added color {self.target_colors[-1]}", C_SUCCESS)

    def add_color_from_screen(self):
        if getattr(self, "_picking_screen", False):
            return
        if len(getattr(self, "target_colors", [])) >= 16:
            self._set_status("Max 16 colors", C_DANGER)
            return
        self._picking_screen = True
        self._picking_slot = -1
        self._pick_wait_release = True
        self._set_status("Click anywhere on screen to add color (Esc cancel)", C_ACCENT)
        self.root.after(30, self._poll_screen_pick)

    def pick_color(self, i):
        cur = (255, 255, 255)
        try:
            cur = tuple(self.target_colors[i])
        except Exception:
            pass
        c = self._ask_basic_color(cur)
        if not c:
            return
        self._apply_color_slot(i, tuple(int(x) for x in c))

    def _commit_target_rgb(self, i):
        try:
            txt = self.color_entries[i].get()
            rgb = parse_rgb(txt)
        except Exception:
            return
        self._apply_color_slot(i, rgb)

    def _poll_screen_pick(self):
        if not getattr(self, "_picking_screen", False):
            return
        try:
            if get_key_state(0x1B) & 0x8000:
                self._picking_screen = False
                self._set_status("Color pick cancelled", C_MUTED)
                return
            down = bool(get_key_state(0x01) & 0x8000)
            if self._pick_wait_release:
                if not down:
                    self._pick_wait_release = False
                self.root.after(20, self._poll_screen_pick)
                return
            if down:
                x, y = get_cursor_pos()
                self._picking_screen = False
                try:
                    with mss.mss() as sct:
                        shot = sct.grab({"left": int(x), "top": int(y), "width": 1, "height": 1})
                        b, g, r = int(shot.raw[0]), int(shot.raw[1]), int(shot.raw[2])
                except Exception as ex:
                    self._set_status(f"Pick failed: {ex}", C_DANGER)
                    return
                slot = int(getattr(self, "_picking_slot", -1))
                if slot < 0:
                    self.target_colors.append((r, g, b))
                    self._rebuild_color_rows()
                    self._sync_hot_params()
                    self._set_status(f"Added {r}, {g}, {b}", C_SUCCESS)
                else:
                    self._apply_color_slot(slot, (r, g, b))
                    self._set_status(f"Picked {r}, {g}, {b}", C_SUCCESS)
                return
        except Exception as ex:
            self._picking_screen = False
            self._set_status(f"Pick error: {ex}", C_DANGER)
            return
        self.root.after(20, self._poll_screen_pick)

    def _apply_color_slot(self, i, c):
        c = tuple(int(x) for x in c)
        while len(self.target_colors) <= i:
            self.target_colors.append(c)
        self.target_colors[i] = c
        try:
            if i < len(self.color_entries):
                self.color_entries[i].delete(0, tk.END)
                self.color_entries[i].insert(0, f"{c[0]}, {c[1]}, {c[2]}")
            if i < len(self.color_labels):
                self.color_labels[i].configure(bg=f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}")
        except Exception:
            pass
        self._sync_hot_params()

    def _remove_color_at(self, i):
        try:
            if 0 <= i < len(self.target_colors):
                self.target_colors.pop(i)
        except Exception:
            pass
        self._rebuild_color_rows()
        self._sync_hot_params()
        self._set_status("Color removed", C_MUTED)

    def _rebuild_color_rows(self):
        parent = getattr(self, "colors_list_frame", None)
        if parent is None:
            return
        for fr in list(getattr(self, "color_row_frames", [])):
            try:
                fr.destroy()
            except Exception:
                pass
        self.color_row_frames = []
        self.color_entries = []
        self.color_labels = []
        colors = list(getattr(self, "target_colors", []) or [])
        try:
            parent.pack_forget()
        except Exception:
            pass
        if not colors:
            try:
                self._refresh_scroll()
            except Exception:
                pass
            return
        try:
            btns = getattr(self, "colors_btns_frame", None)
            if btns is not None:
                parent.pack(fill="x", pady=(4, 8), before=btns)
            else:
                parent.pack(fill="x", pady=(4, 8))
        except Exception:
            try:
                parent.pack(fill="x", pady=(4, 8))
            except Exception:
                pass
        for i, c in enumerate(colors):
            c = tuple(int(x) for x in c[:3])
            row = tk.Frame(parent, bg=C_CARD2)
            row.pack(fill="x", pady=3)
            tk.Label(
                row, text=f"{i + 1}", bg=C_CARD2, fg=UI_MUTED,
                font=("Segoe UI", 9), width=2,
            ).pack(side="left", padx=(4, 4), pady=6)
            e = tk.Entry(
                row, width=14, bg=C_CARD2, fg=UI_TEXT, insertbackground=C_TEXT,
                relief="flat", font=("Segoe UI", 9),
            )
            e.insert(0, f"{c[0]}, {c[1]}, {c[2]}")
            e.pack(side="left", padx=4, pady=6, ipady=3)
            e.bind("<FocusOut>", lambda _e, i=i: self._commit_target_rgb(i))
            e.bind("<Return>", lambda _e, i=i: self._commit_target_rgb(i))
            self.color_entries.append(e)
            swatch = tk.Label(row, width=3, bg=f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}", relief="flat")
            swatch.pack(side="left", padx=6, pady=6, ipady=6)
            self.color_labels.append(swatch)
            pick = tk.Label(
                row, text="Pick", bg=C_ACCENT, fg="#ffffff",
                font=("Segoe UI", 8, "bold"), padx=8, pady=3, cursor="hand2",
            )
            rem = tk.Label(
                row, text="×", bg=C_CARD2, fg=C_DANGER,
                font=("Segoe UI", 16, "bold"), padx=10, cursor="hand2",
            )
            rem.pack(side="right", padx=4)
            pick.pack(side="right", padx=4)
            pick.bind("<Button-1>", lambda e, i=i: self.pick_color(i))
            rem.bind("<Button-1>", lambda e, i=i: self._remove_color_at(i))
            self.color_row_frames.append(row)
        try:
            parent.update_idletasks()
            self._refresh_scroll()
        except Exception:
            pass

    def clear_colors(self):

        self.target_colors = []
        self._rebuild_color_rows()
        self._sync_hot_params()
        self._set_status("Colors cleared", C_MUTED)

    def _on_hz_change(self, value=None):
        def clamp(var, name):
            try:
                hz = max(10, min(520, int(round(float(var.get())))))
            except Exception:
                hz = 520
            setattr(self, name, hz)
        clamp(self.aim_hz_var, "aim_hz")
        clamp(self.trigger_hz_var, "trigger_hz")
        clamp(self.overlay_hz_var, "overlay_hz")
        self._sync_hot_params()

    def on_scan_size_change(self, value):

        size = int(float(value))
        if size % 2 != 0:
            size += 1
        self.scan_size = size
        if hasattr(self, "overlay"):
            self.update_overlay_size()
        self._sync_hot_params()

    def on_tolerance_change(self, value):
        self.tolerance = int(float(value))
        self._sync_hot_params()

    def on_smoothness_change(self, value):
        self.smoothness = round(float(value) * 2) / 2.0
        self._sync_hot_params()

    def on_scan_res_change(self, value):
        self.scan_res = max(0.25, min(1.0, float(value)))
        self._sync_hot_params()

    def on_sensitivity_change(self, value):
        self.sensitivity = float(value)
        self._sync_hot_params()

    def on_mouse_scale_change(self, value):
        self.mouse_scale = float(value)
        self._sync_hot_params()

    def on_shaky_aim_change(self, value):
        self.shaky_aim = float(value)
        self._sync_hot_params()

    def on_shaky_speed_change(self, value):
        self.shaky_speed = float(value)
        self._sync_hot_params()

    def on_offset_y_change(self, value):
        self.offset_y = max(-50.0, min(50.0, float(value)))
        self._sync_hot_params()

    def on_offset_x_change(self, value):
        self.offset_x = max(-50.0, min(50.0, float(value)))
        self._sync_hot_params()

    def _apply_feature_frames(self):
        pairs = (
            (getattr(self, "shaky_enabled", False), getattr(self, "shaky_frame", None), getattr(self, "shaky_toggle_canvas", None)),
            (getattr(self, "offset_enabled", False), getattr(self, "offset_frame", None), getattr(self, "offset_toggle_canvas", None)),
            (getattr(self, "triggerbot_enabled", False), getattr(self, "trigger_frame", None), getattr(self, "trigger_toggle_canvas", None)),
            (getattr(self, "recoil_enabled", False), getattr(self, "recoil_frame", None), getattr(self, "recoil_toggle_canvas", None)),
        )
        for enabled, frame, canvas in pairs:
            if frame is None:
                continue
            try:
                frame.pack_forget()
            except Exception:
                pass
            if enabled:
                try:
                    anchor = canvas.master if canvas is not None else None
                    if anchor is not None:
                        frame.pack(fill="x", after=anchor)
                    else:
                        frame.pack(fill="x")
                except Exception:
                    try:
                        frame.pack(fill="x")
                    except Exception:
                        pass
        for redraw in (
            "_redraw_shaky_toggle",
            "_redraw_trigger_toggle",
            "_redraw_recoil_toggle",
        ):
            fn = getattr(self, redraw, None)
            if fn:
                try:
                    fn()
                except Exception:
                    pass
        try:
            self._refresh_scroll()
        except Exception:
            pass

    def _on_aim_point_change(self, event=None):
        self._apply_edge_bias_visibility()
        self._sync_hot_params()

    def _apply_edge_bias_visibility(self):
        frame = getattr(self, "edge_bias_frame", None)
        if frame is None:
            return
        try:
            frame.pack_forget()
        except Exception:
            pass
        ap = self.aim_point_var.get() if hasattr(self, "aim_point_var") else "Center"
        if ap == "Edge":
            try:
                aim_row = None
                if hasattr(self, "aim_point_menu"):
                    aim_row = self.aim_point_menu.master
                if aim_row is not None:
                    frame.pack(fill="x", pady=(0, 10), after=aim_row)
                else:
                    frame.pack(fill="x", pady=(0, 10))
            except Exception:
                try:
                    frame.pack(fill="x", pady=(0, 10))
                except Exception:
                    pass
        try:
            self._refresh_scroll()
        except Exception:
            pass

    def on_edge_bias_change(self, value):
        self.edge_bias = max(0.0, min(10.0, float(value)))
        self._sync_hot_params()

    def _set_shaky_enabled(self, value):
        self.shaky_enabled = bool(value)
        self._apply_feature_frames()
        self._sync_hot_params()

    def _set_offset_enabled(self, value):
        self.offset_enabled = bool(value)
        self._apply_feature_frames()
        self._sync_hot_params()

    def _set_aimbot(self, value):
        self.aimbot_enabled = bool(value)
        self._apply_aimbot_settings_visibility()
        self._sync_hot_params()
        if hasattr(self, "_redraw_aimbot_toggle"):
            try:
                self._redraw_aimbot_toggle()
            except Exception:
                pass

    def _apply_aimbot_settings_visibility(self):
        frame = getattr(self, "aimbot_settings_frame", None)
        extras = getattr(self, "aim_master_extras", None)
        if frame is not None:
            try:
                frame.pack_forget()
            except Exception:
                pass
        if extras is not None:
            try:
                extras.pack_forget()
            except Exception:
                pass
        if frame is not None and getattr(self, "aimbot_enabled", True):
            try:
                frame.pack(fill="x")
            except Exception:
                pass
            try:
                self._apply_feature_frames()
            except Exception:
                pass
        if extras is not None:
            try:
                extras.pack(fill="x")
            except Exception:
                pass
            try:
                self._apply_feature_frames()
            except Exception:
                pass
        try:
            self._refresh_scroll()
        except Exception:
            pass

    def _set_recoil_enabled(self, value):
        self.recoil_enabled = bool(value)
        self._apply_feature_frames()
        self._sync_hot_params()
        if hasattr(self, "_redraw_recoil_toggle"):
            try:
                self._redraw_recoil_toggle()
            except Exception:
                pass

    def on_recoil_strength_change(self, value):
        self.recoil_strength = max(0.0, min(15.0, float(value)))
        self._sync_hot_params()

    def _set_triggerbot(self, value):
        self.triggerbot_enabled = bool(value)
        self._apply_feature_frames()
        try:
            self._apply_trigger_fire_visibility()
        except Exception:
            pass
        self._sync_hot_params()
        if hasattr(self, "_redraw_trigger_toggle"):
            try:
                self._redraw_trigger_toggle()
            except Exception:
                pass

    def _apply_trigger_fire_visibility(self):
        frame = getattr(self, "trigger_click_frame", None)
        if frame is None:
            return
        mode = ""
        if hasattr(self, "trigger_fire_mode_var"):
            mode = str(self.trigger_fire_mode_var.get() or "")
        try:
            frame.pack_forget()
        except Exception:
            pass
        if mode.strip().lower() != "hold while on color":
            try:
                frame.pack(fill="x")
            except Exception:
                pass

    def on_trigger_scan_change(self, value):
        self.trigger_scan_size = max(1, min(100, int(float(value))))
        self._sync_hot_params()

    def on_trigger_reaction_change(self, value):
        self.trigger_reaction_ms = max(0.0, min(200.0, float(value)))
        self._sync_hot_params()

    def on_trigger_interval_change(self, value):
        self.trigger_interval_ms = max(0.0, min(500.0, float(value)))
        self._sync_hot_params()

    def on_trigger_release_change(self, value):
        self.trigger_release_ms = max(0.0, min(500.0, float(value)))
        self._sync_hot_params()

    def _set_show_fov(self, value):
        self.show_fov = bool(value)
        self._apply_fov_visibility()
        self._sync_hot_params()
        if hasattr(self, "_redraw_fov_toggle"):
            try:
                self._redraw_fov_toggle()
            except Exception:
                pass

    def _apply_detection_frames(self):
        pairs = (
            (getattr(self, "esp_enabled", False), getattr(self, "box_thickness_frame", None), getattr(self, "esp_toggle_canvas", None)),
            (getattr(self, "tracers_enabled", False), getattr(self, "tracer_thickness_frame", None), getattr(self, "tracers_toggle_canvas", None)),
            (getattr(self, "esp_preview_enabled", False), getattr(self, "esp_preview_frame", None), getattr(self, "esp_preview_toggle_canvas", None)),
        )
        for enabled, frame, canvas in pairs:
            if frame is None:
                continue
            try:
                frame.pack_forget()
            except Exception:
                pass
            if enabled:
                try:
                    anchor = canvas.master if canvas is not None else None
                    if anchor is not None:
                        frame.pack(fill="x", after=anchor)
                    else:
                        frame.pack(fill="x")
                except Exception:
                    try:
                        frame.pack(fill="x")
                    except Exception:
                        pass
        try:
            self._apply_corner_length_visibility()
        except Exception:
            pass
        try:
            self._refresh_scroll()
        except Exception:
            pass

    def _set_esp_preview(self, value):
        self.esp_preview_enabled = bool(value)
        try:
            self._apply_detection_frames()
        except Exception:
            pass
        if self.esp_preview_enabled:
            try:
                self.root.after(20, self._draw_esp_preview)
            except Exception:
                pass
        if hasattr(self, "_redraw_esp_preview_toggle"):
            try:
                self._redraw_esp_preview_toggle()
            except Exception:
                pass

    def _draw_esp_preview(self):
        cv = getattr(self, "esp_preview_canvas", None)
        if cv is None or not getattr(self, "esp_preview_enabled", False):
            return
        try:
            cv.delete("all")
            w = max(int(cv.winfo_width()), 2)
            h = max(int(cv.winfo_height()), 2)
            cv.create_rectangle(0, 0, w, h, fill="#0a0a0a", outline="")
            color = self.esp_color_var.get() if hasattr(self, "esp_color_var") else getattr(self, "esp_color", "white")
            try:
                tw = int(float(self.box_thickness_var.get())) if hasattr(self, "box_thickness_var") else int(getattr(self, "box_thickness", 1))
            except Exception:
                tw = 1
            tw = max(1, min(5, tw))
            shape = self.player_box_shape_var.get() if hasattr(self, "player_box_shape_var") else getattr(self, "player_box_shape", "Box")
            try:
                cl = int(float(self.corner_length_var.get())) if hasattr(self, "corner_length_var") else int(getattr(self, "corner_length", 8))
            except Exception:
                cl = 8
            bw, bh = max(32, int(w * 0.40)), max(56, int(h * 0.58))
            x1 = (w - bw) // 2
            y1 = max(10, int(h * 0.12))
            x2, y2 = x1 + bw, y1 + bh
            if shape == "Corners":
                max_c = max(2, min(cl, max(2, (x2 - x1) // 2), max(2, (y2 - y1) // 2)))
                segs = (
                    (x1, y1, x1 + max_c, y1), (x1, y1, x1, y1 + max_c),
                    (x2 - max_c, y1, x2, y1), (x2, y1, x2, y1 + max_c),
                    (x1, y2, x1 + max_c, y2), (x1, y2 - max_c, x1, y2),
                    (x2 - max_c, y2, x2, y2), (x2, y2 - max_c, x2, y2),
                )
                for a, b, c, d in segs:
                    cv.create_line(a, b, c, d, fill=color, width=tw)
            else:
                cv.create_rectangle(x1, y1, x2, y2, outline=color, width=tw, fill="")
            cv.create_text(
                w // 2, h - 6, text="ESP Preview", fill="#666666",
                font=("Segoe UI", 8), anchor="s",
            )
        except Exception:
            pass

    def _set_debug_view(self, value):
        self.debug_view_enabled = bool(value)
        self._sync_hot_params()
        if self.debug_view_enabled:
            self._open_debug_view()
            self.root.after(40, self._poll_debug_view)
        else:
            self._close_debug_view()
            with self._debug_lock:
                self._debug_frame = None
        if hasattr(self, "_redraw_debug_view_toggle"):
            try:
                self._redraw_debug_view_toggle()
            except Exception:
                pass

    def _open_debug_view(self):
        try:
            if self._debug_win is not None and self._debug_win.winfo_exists():
                self._debug_win.deiconify()
                self._debug_win.lift()
                return
        except Exception:
            self._debug_win = None
        win = tk.Toplevel(self.root)
        win.title("Detection View")
        try:
            win.update_idletasks()
            self._streamproof_widget(win)
            win.after(40, lambda w=win: self._streamproof_widget(w))
        except Exception:
            pass
        win.configure(bg="#0a0a0a")
        win.geometry("640x360")
        win.attributes("-topmost", True)
        tk.Label(
            win, text="FOV capture  |  color mask (what the bot sees)",
            bg="#0a0a0a", fg="#ffffff", font=("Segoe UI", 9),
        ).pack(anchor="w", padx=8, pady=(8, 4))
        lbl = tk.Label(win, bg="#000000")
        lbl.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        win.protocol("WM_DELETE_WINDOW", lambda: self._set_debug_view(False))
        self._debug_win = win
        self._debug_label = lbl

    def _close_debug_view(self):
        try:
            if self._debug_win is not None:
                self._debug_win.destroy()
        except Exception:
            pass
        self._debug_win = None
        self._debug_label = None
        self._debug_photo = None

    def _poll_debug_view(self):
        if not getattr(self, "debug_view_enabled", False):
            return
        try:
            with self._debug_lock:
                frame = None if self._debug_frame is None else self._debug_frame.copy()
            if frame is not None and self._debug_label is not None:
                h, w = frame.shape[:2]
                max_w = 620
                if w > max_w:
                    scale = max_w / float(w)
                    nw, nh = max_w, max(1, int(h * scale))
                    frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
                fh, fw = frame.shape[:2]
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                ppm = ("P6 %d %d 255\n" % (fw, fh)).encode("ascii") + frame.tobytes()
                photo = tk.PhotoImage(data=ppm, format="PPM")
                self._debug_photo = photo
                self._debug_label.configure(image=photo)
                try:
                    self._debug_win.geometry(f"{fw + 24}x{fh + 48}")
                except Exception:
                    pass
        except Exception:
            pass
        self.root.after(50, self._poll_debug_view)

    def _set_esp(self, value):
        self.esp_enabled = bool(value)
        self._sync_hot_params()
        if not self.esp_enabled:
            try:
                self.clear_esp_boxes()
            except Exception:
                pass
            self.root.after(20, self.clear_esp_boxes)
            self.root.after(80, self.clear_esp_boxes)
        self._ensure_overlay_visibility()
        self._apply_detection_frames()
        if hasattr(self, "_redraw_esp_toggle"):
            try:
                self._redraw_esp_toggle()
            except Exception:
                pass

    def _set_tracers(self, value):
        self.tracers_enabled = bool(value)
        self._sync_hot_params()
        if not self.tracers_enabled:
            try:
                self.clear_tracers()
            except Exception:
                pass
            self.root.after(20, self.clear_tracers)
            self.root.after(80, self.clear_tracers)
        self._ensure_overlay_visibility()
        self._apply_detection_frames()
        if hasattr(self, "_redraw_tracers_toggle"):
            try:
                self._redraw_tracers_toggle()
            except Exception:
                pass
        try:
            self._draw_esp_preview()
        except Exception:
            pass

    def on_box_thickness_change(self, value):
        self.box_thickness = max(1, min(5, int(float(value))))
        self._sync_hot_params()
        try:
            self._draw_esp_preview()
        except Exception:
            pass

    def on_tracer_thickness_change(self, value):
        self.tracer_thickness = max(1, min(5, int(float(value))))
        self._sync_hot_params()
        try:
            self._draw_esp_preview()
        except Exception:
            pass

    def on_fov_shape_change(self, event=None):
        self.fov_shape = self.fov_shape_var.get()
        self._apply_fov_shape_draw()
        self._sync_hot_params()

    def on_player_box_shape_change(self, event=None):
        self.player_box_shape = self.player_box_shape_var.get()
        self._apply_corner_length_visibility()
        self._sync_hot_params()
        try:
            self._draw_esp_preview()
        except Exception:
            pass

    def on_corner_length_change(self, value):
        self.corner_length = max(2, min(40, int(float(value))))
        self._sync_hot_params()
        try:
            self._draw_esp_preview()
        except Exception:
            pass

    def _apply_corner_length_visibility(self):
        frame = getattr(self, "corner_length_frame", None)
        if frame is None:
            return
        try:
            frame.pack_forget()
        except Exception:
            pass
        shape = self.player_box_shape_var.get() if hasattr(self, "player_box_shape_var") else "Box"
        if shape == "Corners" and getattr(self, "esp_enabled", False):
            try:
                frame.pack(fill="x")
            except Exception:
                pass

    def clear_esp_boxes(self):
        ids = list(getattr(self, "_esp_box_ids", []))
        self._esp_box_ids = []
        for item in ids:
            try:
                self.canvas.delete(item)
            except Exception:
                pass
        try:
            for item in self.canvas.find_withtag("esp_box"):
                self.canvas.delete(item)
        except Exception:
            pass

    def clear_tracers(self):
        ids = list(getattr(self, "_tracer_ids", []))
        self._tracer_ids = []
        for item in ids:
            try:
                self.canvas.delete(item)
            except Exception:
                pass
            try:
                if getattr(self, "tracer_canvas", None) is not None:
                    self.tracer_canvas.delete(item)
            except Exception:
                pass
        try:
            for item in self.canvas.find_withtag("tracer_line"):
                self.canvas.delete(item)
        except Exception:
            pass
        try:
            tc = getattr(self, "tracer_canvas", None)
            if tc is not None:
                for item in tc.find_withtag("tracer_line"):
                    tc.delete(item)
        except Exception:
            pass

    def update_esp_boxes(self, boxes, color="white", thickness=1, shape="Box", corner_len=8):
        try:
            self.clear_esp_boxes()
            tw = max(1, min(5, int(thickness)))
            cl = max(2, int(corner_len))
            for x1, y1, x2, y2 in boxes:
                if x2 <= x1:
                    x2 = x1 + 1
                if y2 <= y1:
                    y2 = y1 + 1
                if shape == "Corners":
                    max_c = max(2, min(cl, max(2, (x2 - x1) // 2), max(2, (y2 - y1) // 2)))
                    segs = (
                        (x1, y1, x1 + max_c, y1), (x1, y1, x1, y1 + max_c),
                        (x2 - max_c, y1, x2, y1), (x2, y1, x2, y1 + max_c),
                        (x1, y2, x1 + max_c, y2), (x1, y2 - max_c, x1, y2),
                        (x2 - max_c, y2, x2, y2), (x2, y2 - max_c, x2, y2),
                    )
                    for a, b, c, d in segs:
                        self._esp_box_ids.append(
                            self.canvas.create_line(
                                a, b, c, d, fill=color, width=tw, tags=("esp_box",)
                            )
                        )
                else:
                    self._esp_box_ids.append(
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2, outline=color, width=tw, fill="",
                            tags=("esp_box",),
                        )
                    )
            if hasattr(self, "circle_id"):
                self.canvas.tag_raise(self.circle_id)
            if hasattr(self, "fov_rect_id"):
                self.canvas.tag_raise(self.fov_rect_id)
        except Exception:
            pass

    def update_tracers(
        self,
        centers,
        color="white",
        thickness=1,
        origin_mode="Center",
        overlay_left=0,
        overlay_top=0,
        cursor_xy=None,
    ):
        try:
            self.clear_tracers()
            tw = max(1, min(5, int(thickness)))
            try:
                sw = ctypes.windll.user32.GetSystemMetrics(0)
                sh = ctypes.windll.user32.GetSystemMetrics(1)
            except Exception:
                sw, sh = 1920, 1080
            size = max(50, int(self.scan_size))
            pad = 3
            if origin_mode == "Cursor" and cursor_xy is not None:
                ox = float(cursor_xy[0]) - float(overlay_left)
                oy = float(cursor_xy[1]) - float(overlay_top)
            elif origin_mode == "Bottom":
                ox = size * 0.5
                oy = float(size - pad)
            else:
                ox = size * 0.5
                oy = size * 0.5
            for cx, cy in centers:
                tid = self.canvas.create_line(
                    ox, oy, cx, cy, fill=color, width=tw, tags=("tracer_line",),
                )
                self._tracer_ids.append(tid)
            if hasattr(self, "circle_id"):
                self.canvas.tag_raise(self.circle_id)
            if hasattr(self, "fov_rect_id"):
                self.canvas.tag_raise(self.fov_rect_id)
        except Exception:
            pass

    def _apply_fov_visibility(self):
        try:
            self._apply_fov_shape_draw()
            self._ensure_overlay_visibility()
        except Exception:
            pass

    def _ensure_overlay_visibility(self):
        try:
            need = bool(
                self.show_fov
                or getattr(self, "esp_enabled", False)
                or getattr(self, "tracers_enabled", False)
            )
            self._sync_xhair_overlay()
            if need:
                if self.tracking:
                    self.show_overlay()
                else:
                    self.overlay.deiconify()
                    self.overlay.attributes("-topmost", True)
            else:
                self.hide_overlay()
        except Exception:
            pass


    def _set_xhair(self, value):
        self.xhair_enabled = bool(value)
        self._apply_xhair_frames()
        self._sync_xhair_overlay()
        if hasattr(self, "_redraw_xhair_toggle"):
            try:
                self._redraw_xhair_toggle()
            except Exception:
                pass

    def _set_xhair_bars(self, value):
        self.xhair_bars = bool(value)
        self._apply_xhair_frames()
        self._redraw_xhair()
        if hasattr(self, "_redraw_xhair_bars_toggle"):
            try:
                self._redraw_xhair_bars_toggle()
            except Exception:
                pass

    def _set_xhair_dot(self, value):
        self.xhair_dot = bool(value)
        self._apply_xhair_frames()
        self._redraw_xhair()
        if hasattr(self, "_redraw_xhair_dot_toggle"):
            try:
                self._redraw_xhair_dot_toggle()
            except Exception:
                pass

    def _set_xhair_outline(self, value):
        self.xhair_outline = bool(value)
        self._apply_xhair_frames()
        self._redraw_xhair()
        if hasattr(self, "_redraw_xhair_outline_toggle"):
            try:
                self._redraw_xhair_outline_toggle()
            except Exception:
                pass

    def _on_xhair_mode(self):
        self.xhair_mode = self.xhair_mode_var.get()
        self._sync_xhair_overlay()

    def on_xhair_opacity_change(self, value):
        self.xhair_opacity = max(0.15, min(1.0, float(value)))
        self._apply_xhair_alpha()

    def on_xhair_style_change(self, value=None):
        if hasattr(self, "xhair_bar_len_var"):
            self.xhair_bar_len = float(self.xhair_bar_len_var.get())
            self.xhair_bar_width = float(self.xhair_bar_width_var.get())
            self.xhair_bar_gap = float(self.xhair_bar_gap_var.get())
            self.xhair_dot_size = float(self.xhair_dot_size_var.get())
            self.xhair_dot_shape = self.xhair_dot_shape_var.get()
            self.xhair_outline_thick = float(self.xhair_outline_thick_var.get())
        self._redraw_xhair()

    def _color_attr(self, which):
        return {
            "circle": "circle_color",
            "lock": "lock_color",
            "esp": "esp_color",
            "bar": "xhair_bar_color",
            "dot": "xhair_dot_color",
            "outline": "xhair_outline_color",
            "theme_bg": "custom_bg",
            "theme_fg": "custom_fg",
            "lock_ind_idle": "lock_ind_idle",
            "lock_ind_on": "lock_ind_on",
            "trig_ind_idle": "trig_ind_idle",
            "trig_ind_on": "trig_ind_on",
        }.get(which, "circle_color")

    def _get_pick_rgb(self, which):
        return parse_rgb(getattr(self, self._color_attr(which), (255, 255, 255)))

    def _set_pick_rgb(self, which, rgb):
        rgb = parse_rgb(rgb)
        hexv = rgb_hex(rgb)
        attr = self._color_attr(which)
        setattr(self, attr, hexv if which in ("circle", "lock", "esp") else rgb)
        if which == "circle" and hasattr(self, "circle_color_var"):
            self.circle_color_var.set(hexv)
            try:
                self.on_circle_color_change()
            except Exception:
                pass
        elif which == "lock" and hasattr(self, "lock_color_var"):
            self.lock_color_var.set(hexv)
            self.lock_color = hexv
        elif which == "esp" and hasattr(self, "esp_color_var"):
            self.esp_color_var.set(hexv)
            self.esp_color = hexv
            self._sync_hot_params()
        elif which in ("lock_ind_idle", "lock_ind_on", "trig_ind_idle", "trig_ind_on"):
            setattr(self, which, rgb)
            self._paint_indicators()
        elif which in ("theme_bg", "theme_fg"):
            setattr(self, "custom_bg" if which == "theme_bg" else "custom_fg", rgb)
            if getattr(self, "theme", "") == "Custom" or (
                hasattr(self, "theme_var") and self.theme_var.get() == "Custom"
            ):
                try:
                    self.apply_theme("Custom", rebuild=True)
                except Exception:
                    pass
        else:
            self._redraw_xhair()
        self._refresh_pick_row(which)

    def _standard_color_row(self, parent, title, which):
        return self._xhair_rgb_row(parent, title, which)

    def _xhair_rgb_row(self, parent, title, which):
        row = tk.Frame(parent, bg=C_CARD2)
        row.pack(fill="x", pady=(0, 8))
        tk.Label(row, text=title, bg=C_CARD2, fg=UI_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        inner = tk.Frame(row, bg=C_CARD2)
        inner.pack(fill="x", pady=(2, 0))
        rgb = self._get_pick_rgb(which)
        swatch = tk.Label(inner, width=3, bg=rgb_hex(rgb), relief="flat")
        swatch.pack(side="left", pady=4, ipady=6)
        ent = tk.Entry(
            inner, width=14, bg=C_CARD2, fg=UI_TEXT, insertbackground=C_TEXT,
            relief="flat", font=("Segoe UI", 9),
        )
        ent.insert(0, rgb_text(rgb))
        ent.pack(side="left", padx=8, pady=4, ipady=3)
        ent.bind("<FocusOut>", lambda e, w=which: self._commit_pick_rgb(w))
        ent.bind("<Return>", lambda e, w=which: self._commit_pick_rgb(w))
        pick = tk.Label(
            inner, text="Pick", bg=C_ACCENT, fg="#ffffff",
            font=("Segoe UI", 8, "bold"), padx=8, pady=3, cursor="hand2",
        )
        pick.pack(side="right", padx=4)
        pick.bind("<Button-1>", lambda e, w=which: self._pick_standard_color(w))
        setattr(self, "_xhair_%s_swatch" % which, swatch)
        setattr(self, "_xhair_%s_lab" % which, ent)

    def _commit_pick_rgb(self, which):
        ent = getattr(self, "_xhair_%s_lab" % which, None)
        if ent is None:
            return
        try:
            rgb = parse_rgb(ent.get())
        except Exception:
            return
        self._set_pick_rgb(which, rgb)

    def _pick_standard_color(self, which):
        c = self._ask_basic_color(self._get_pick_rgb(which))
        if not c:
            return
        self._set_pick_rgb(which, c)

    def _ask_basic_color(self, current=(255, 255, 255)):
        import colorsys
        self._color_picker_open = True
        result = {"rgb": parse_rgb(current)}
        r0, g0, b0 = result["rgb"]
        h, s, v = colorsys.rgb_to_hsv(r0 / 255.0, g0 / 255.0, b0 / 255.0)
        state = {"h": h, "s": s, "v": v, "busy": False}

        win = tk.Toplevel(self.root)
        win.withdraw()
        win.title("Color")
        win.configure(bg="#000000")
        win.attributes("-topmost", True)
        win.resizable(False, False)
        self._picker_win = win
        wrap = tk.Frame(win, bg="#000000")
        wrap.pack(padx=10, pady=10)

        left = tk.Frame(wrap, bg="#000000")
        left.pack(side="left", padx=(0, 10))
        wheel_size = 168
        bar_w, bar_h = 22, 168

        def hsv_rgb():
            rr, gg, bb = colorsys.hsv_to_rgb(state["h"], state["s"], state["v"])
            return int(rr * 255 + 0.5), int(gg * 255 + 0.5), int(bb * 255 + 0.5)

        r_var = tk.StringVar(value=str(r0))
        g_var = tk.StringVar(value=str(g0))
        b_var = tk.StringVar(value=str(b0))

        def rgb_row(parent, color, var):
            row = tk.Frame(parent, bg="#ffffff")
            row.pack(fill="x", pady=4)
            tk.Frame(row, bg=color, width=6).pack(side="left", fill="y")
            tk.Entry(
                row, textvariable=var, bd=0, relief="flat", font=("Segoe UI", 16, "bold"),
                fg=color, bg="#ffffff", width=4, justify="center",
            ).pack(side="left", padx=8, pady=6)

        rgb_row(left, "#e21b1b", r_var)
        rgb_row(left, "#21c221", g_var)
        rgb_row(left, "#2a4cff", b_var)
        hex_lab = tk.Label(
            left, text=rgb_hex((r0, g0, b0)), bg="#c94a4a", fg="#ffffff",
            font=("Segoe UI", 11, "bold"), padx=10, pady=8,
        )
        hex_lab.pack(fill="x", pady=(8, 0))

        mid = tk.Frame(wrap, bg="#000000")
        mid.pack(side="left")
        wheel_lbl = tk.Label(mid, bg="#000000", bd=0)
        wheel_lbl.pack()
        right = tk.Frame(wrap, bg="#000000")
        right.pack(side="left", padx=(10, 0))
        bar_cv = tk.Canvas(right, width=bar_w + 8, height=bar_h, bg="#000000", highlightthickness=0, bd=0)
        bar_cv.pack()

        def make_wheel_array():
            n = wheel_size
            arr = np.zeros((n, n, 3), dtype=np.uint8)
            cx = cy = (n - 1) / 2.0
            rmax = n / 2.0 - 1.0
            for yy in range(n):
                for xx in range(n):
                    dx, dy = xx - cx, yy - cy
                    rad = (dx * dx + dy * dy) ** 0.5
                    if rad > rmax:
                        continue
                    hh = (math.atan2(dy, dx) + math.pi) / (2.0 * math.pi)
                    ss = min(1.0, rad / rmax)
                    rr, gg, bb = colorsys.hsv_to_rgb(hh, ss, 1.0)
                    arr[yy, xx] = (int(rr * 255), int(gg * 255), int(bb * 255))
            return arr

        def array_to_photo(arr):
            h, w, _ = arr.shape
            header = ("P6 %d %d 255\n" % (w, h)).encode("ascii")
            return tk.PhotoImage(data=header + arr.tobytes())

        wheel_base = make_wheel_array()

        bar_img_id = bar_cv.create_image(4, 0, anchor="nw")
        handle = bar_cv.create_rectangle(2, 0, 6 + bar_w, 6, outline="#ffffff", width=2)

        def build_bar_photo():
            img = tk.PhotoImage(width=1, height=bar_h)
            for y in range(bar_h):
                vv = 1.0 - y / float(max(1, bar_h - 1))
                rr, gg, bb = colorsys.hsv_to_rgb(state["h"], state["s"], vv)
                img.put("#%02x%02x%02x" % (int(rr * 255), int(gg * 255), int(bb * 255)), to=(0, y))
            return img.zoom(bar_w, 1)

        def move_handle():
            yy = int((1.0 - state["v"]) * (bar_h - 1))
            bar_cv.coords(handle, 2, yy - 3, 6 + bar_w, yy + 3)

        def refresh_bar():
            photo = build_bar_photo()
            state["bar_photo"] = photo
            bar_cv.itemconfig(bar_img_id, image=photo)
            move_handle()

        def place_mark():
            cx = cy = wheel_size / 2.0
            rmax = wheel_size / 2.0 - 2
            ang = state["h"] * 2.0 * math.pi - math.pi
            rr = state["s"] * rmax
            px = int(round(cx + math.cos(ang) * rr))
            py = int(round(cy + math.sin(ang) * rr))
            img = wheel_base.copy()
            for rad, col in ((6, (0, 0, 0)), (5, (255, 255, 255))):
                yy, xx = np.ogrid[-rad:rad + 1, -rad:rad + 1]
                ring = np.abs(np.sqrt(xx * xx + yy * yy) - (rad - 0.6)) < 0.9
                for oy, ox in zip(*np.where(ring)):
                    y = py + oy - rad
                    x = px + ox - rad
                    if 0 <= y < wheel_size and 0 <= x < wheel_size:
                        img[y, x] = col
            photo = array_to_photo(img)
            state["wheel_photo"] = photo
            wheel_lbl.configure(image=photo)

        def paint_hex(rgb):
            hex_lab.configure(
                text=rgb_hex(rgb), bg=rgb_hex(rgb),
                fg="#000000" if (rgb[0] + rgb[1] + rgb[2]) > 400 else "#ffffff",
            )

        def sync_entries():
            rgb = result["rgb"]
            state["busy"] = True
            r_var.set(str(rgb[0]))
            g_var.set(str(rgb[1]))
            b_var.set(str(rgb[2]))
            state["busy"] = False

        def live(rebuild_bar):
            rgb = hsv_rgb()
            result["rgb"] = rgb
            paint_hex(rgb)
            sync_entries()
            place_mark()
            if rebuild_bar:
                now = time.perf_counter()
                if now - state.get("bar_t", 0) > FRAME_DT:
                    state["bar_t"] = now
                    refresh_bar()
                else:
                    move_handle()
            else:
                move_handle()

        def from_fields(*_a):
            if state["busy"]:
                return
            try:
                rgb = parse_rgb((int(r_var.get() or 0), int(g_var.get() or 0), int(b_var.get() or 0)))
            except Exception:
                return
            hh, ss, vv = colorsys.rgb_to_hsv(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
            state["h"], state["s"], state["v"] = hh, ss, vv
            result["rgb"] = rgb
            paint_hex(rgb)
            place_mark()
            refresh_bar()

        def wheel_at(ev):
            cx = cy = wheel_size / 2.0
            dx, dy = ev.x - cx, ev.y - cy
            rad = math.sqrt(dx * dx + dy * dy)
            rmax = wheel_size / 2.0 - 1
            if rad > rmax:
                rad = rmax
            state["h"] = (math.atan2(dy, dx) + math.pi) / (2.0 * math.pi)
            state["s"] = max(0.0, min(1.0, rad / rmax))
            live(True)

        def bar_at(ev):
            yy = max(0, min(bar_h - 1, ev.y))
            state["v"] = 1.0 - yy / float(max(1, bar_h - 1))
            live(False)

        wheel_lbl.bind("<Button-1>", wheel_at)
        wheel_lbl.bind("<B1-Motion>", wheel_at)
        wheel_lbl.bind("<ButtonRelease-1>", lambda e: sync_entries())
        bar_cv.bind("<Button-1>", bar_at)
        bar_cv.bind("<B1-Motion>", bar_at)
        bar_cv.bind("<ButtonRelease-1>", lambda e: sync_entries())
        for var in (r_var, g_var, b_var):
            var.trace_add("write", from_fields)

        confirmed = {"ok": False}
        ok = tk.Label(win, text="OK", bg="#e21b1b", fg="#ffffff", font=("Segoe UI", 10, "bold"), padx=16, pady=6, cursor="hand2")
        ok.pack(pady=(0, 10))
        def confirm(_e=None):
            confirmed["ok"] = True
            win.destroy()
        ok.bind("<Button-1>", confirm)
        win.bind("<Return>", confirm)
        live(True)
        sync_entries()
        win.transient(self.root)
        win.update_idletasks()
        self._streamproof_widget(win)
        win.deiconify()
        try:
            win.grab_set()
        except Exception:
            pass
        try:
            self.root.wait_window(win)
        finally:
            self._color_picker_open = False
            self._picker_win = None
        return result.get("rgb") if confirmed["ok"] else None

    def _refresh_pick_row(self, which):
        rgb = self._get_pick_rgb(which)
        sw = getattr(self, "_xhair_%s_swatch" % which, None)
        lab = getattr(self, "_xhair_%s_lab" % which, None)
        if sw is not None:
            try:
                sw.configure(bg=rgb_hex(rgb))
            except Exception:
                pass
        if lab is not None:
            try:
                if lab.winfo_class() == "Entry":
                    lab.delete(0, tk.END)
                    lab.insert(0, rgb_text(rgb))
                else:
                    lab.configure(text=rgb_text(rgb))
            except Exception:
                pass

    def _refresh_xhair_color_rows(self):
        for which in ("bar", "dot", "outline", "circle", "lock", "esp"):
            self._refresh_pick_row(which)

    def _apply_xhair_frames(self):
        settings = getattr(self, "xhair_settings", None)
        if settings is not None:
            try:
                settings.pack_forget()
            except Exception:
                pass
            if getattr(self, "xhair_enabled", False):
                try:
                    settings.pack(fill="x")
                except Exception:
                    pass
        pairs = (
            (getattr(self, "xhair_bars", False), getattr(self, "xhair_bars_frame", None), getattr(self, "xhair_bars_toggle_canvas", None)),
            (getattr(self, "xhair_dot", False), getattr(self, "xhair_dot_frame", None), getattr(self, "xhair_dot_toggle_canvas", None)),
            (getattr(self, "xhair_outline", False), getattr(self, "xhair_outline_frame", None), getattr(self, "xhair_outline_toggle_canvas", None)),
        )
        for enabled, frame, canvas in pairs:
            if frame is None:
                continue
            try:
                frame.pack_forget()
            except Exception:
                pass
            if enabled and getattr(self, "xhair_enabled", False):
                try:
                    anchor = canvas.master if canvas is not None else None
                    if anchor is not None:
                        frame.pack(fill="x", after=anchor)
                    else:
                        frame.pack(fill="x")
                except Exception:
                    try:
                        frame.pack(fill="x")
                    except Exception:
                        pass
        try:
            self._refresh_scroll()
        except Exception:
            pass

    def _ensure_xhair_overlay(self):
        if getattr(self, "xhair_overlay", None) is not None:
            return
        key = getattr(self, "_overlay_key", "#ff00ff")
        size = 160
        win = tk.Toplevel(self.root)
        win.withdraw()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        try:
            win.wm_attributes("-transparentcolor", key)
        except Exception:
            pass
        win.configure(bg=key)
        cv = tk.Canvas(win, width=size, height=size, bg=key, highlightthickness=0, bd=0)
        cv.pack(fill="both", expand=True)
        self.xhair_overlay = win
        self.xhair_canvas = cv
        self.xhair_size = size
        try:
            win.update_idletasks()
            self._streamproof_widget(win)
        except Exception:
            pass
        self._redraw_xhair()

    def _apply_xhair_alpha(self):
        try:
            self._ensure_xhair_overlay()
            win = self.xhair_overlay
            win.update_idletasks()
            wid = win.winfo_id()
            hwnd = ctypes.windll.user32.GetParent(wid) or wid
            user32 = ctypes.windll.user32
            style = user32.GetWindowLongW(int(hwnd), GWL_EXSTYLE)
            user32.SetWindowLongW(int(hwnd), GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
            alpha = int(max(0.15, min(1.0, float(getattr(self, "xhair_opacity", 1.0)))) * 255)
            user32.SetLayeredWindowAttributes(int(hwnd), getattr(self, "_overlay_key_bgr", 0x00FF00FF), alpha, LWA_COLORKEY | LWA_ALPHA)
        except Exception:
            pass


    def _make_dot_image(self, d, color, rounded, key="#ff00ff"):
        d = max(1, int(d))
        img = tk.PhotoImage(width=d, height=d)
        fill = color if str(color).startswith("#") else rgb_hex(color)
        cx = (d - 1) * 0.5
        cy = (d - 1) * 0.5
        rad = d * 0.5
        if d >= 3 and d % 2:
            rad -= 0.2
        rad2 = rad * rad
        rows = []
        for y in range(d):
            row = []
            for x in range(d):
                if not rounded:
                    row.append(fill)
                else:
                    dx = x - cx
                    dy = y - cy
                    if dx * dx + dy * dy <= rad2 + 1e-6:
                        row.append(fill)
                    else:
                        row.append(key)
            rows.append("{" + " ".join(row) + "}")
        img.put(" ".join(rows))
        return img

    def _redraw_xhair(self):
        if getattr(self, "xhair_canvas", None) is None:
            return
        cv = self.xhair_canvas
        key = getattr(self, "_overlay_key", "#ff00ff")
        cv.delete("xhair")
        if not getattr(self, "xhair_enabled", False):
            return
        size = int(getattr(self, "xhair_size", 160))
        cx = cy = size / 2.0
        gap = float(getattr(self, "xhair_bar_gap", 3))
        bars = getattr(self, "xhair_bars", False)
        dot = getattr(self, "xhair_dot", False)
        outline = getattr(self, "xhair_outline", False)
        blen = float(getattr(self, "xhair_bar_len", 10))
        bwid = max(1, int(getattr(self, "xhair_bar_width", 2)))
        bcol = rgb_hex(getattr(self, "xhair_bar_color", (255, 255, 255)))
        ot = max(1, int(getattr(self, "xhair_outline_thick", 1)))
        ocol = rgb_hex(getattr(self, "xhair_outline_color", (255, 255, 255)))
        if bars:
            segs = [
                (cx - gap - blen, cy, cx - gap, cy),
                (cx + gap, cy, cx + gap + blen, cy),
                (cx, cy - gap - blen, cx, cy - gap),
                (cx, cy + gap, cx, cy + gap + blen),
            ]
            if outline:
                for x0, y0, x1, y1 in segs:
                    cv.create_line(x0, y0, x1, y1, fill=ocol, width=bwid + ot * 2, capstyle="round", tags="xhair")
            for x0, y0, x1, y1 in segs:
                cv.create_line(x0, y0, x1, y1, fill=bcol, width=bwid, capstyle="butt", tags="xhair")
        if dot:
            d = max(1, int(round(float(getattr(self, "xhair_dot_size", 2)))))
            dcol = rgb_hex(getattr(self, "xhair_dot_color", (255, 255, 255)))
            shape = getattr(self, "xhair_dot_shape", "Rounded")
            extra = ot if outline else 0
            ix = int(round(cx))
            iy = int(round(cy))
            key = getattr(self, "_overlay_key", "#ff00ff")
            if outline and extra:
                oimg = self._make_dot_image(d + extra * 2, ocol, shape == "Rounded", key)
                self._xhair_dot_ol_img = oimg
                cv.create_image(ix, iy, image=oimg, tags="xhair")
            img = self._make_dot_image(d, dcol, shape == "Rounded", key)
            self._xhair_dot_img = img
            cv.create_image(ix, iy, image=img, tags="xhair")

    def _sync_xhair_overlay(self):
        try:
            if not getattr(self, "xhair_enabled", False) or not getattr(self, "tracking", True):
                if getattr(self, "xhair_overlay", None) is not None:
                    self.xhair_overlay.withdraw()
                return
            if getattr(self, "_tray_parked", False):
                if getattr(self, "xhair_overlay", None) is not None:
                    self.xhair_overlay.withdraw()
                return
            self._ensure_xhair_overlay()
            self._redraw_xhair()
            size = int(getattr(self, "xhair_size", 160))
            mode = self.xhair_mode_var.get() if hasattr(self, "xhair_mode_var") else getattr(self, "xhair_mode", "Follow Cursor")
            if mode == "Centered":
                x = ctypes.windll.user32.GetSystemMetrics(0) // 2
                y = ctypes.windll.user32.GetSystemMetrics(1) // 2
            else:
                x, y = get_cursor_pos()
            self.xhair_overlay.geometry("%dx%d+%d+%d" % (size, size, int(x - size // 2), int(y - size // 2)))
            self.xhair_overlay.deiconify()
            self.xhair_overlay.attributes("-topmost", True)
            self._apply_xhair_alpha()
            if getattr(self, "streamproof", False):
                try:
                    hwnd = self._hwnd_from_widget(self.xhair_overlay)
                    if hwnd:
                        ctypes.windll.user32.SetWindowDisplayAffinity(int(hwnd), WDA_EXCLUDEFROMCAPTURE)
                except Exception:
                    pass
        except Exception:
            pass

    def _set_lock_indicator(self, value):
        self.lock_indicator = bool(value)
        self._apply_indicator_frames()
        if hasattr(self, "_redraw_lock_ind"):
            try:
                self._redraw_lock_ind()
            except Exception:
                pass

    def _set_trigger_indicator(self, value):
        self.trigger_indicator = bool(value)
        self._apply_indicator_frames()
        if hasattr(self, "_redraw_trig_ind"):
            try:
                self._redraw_trig_ind()
            except Exception:
                pass

    def _on_indicator_pos(self, event=None):
        if hasattr(self, "lock_ind_pos_var"):
            self.lock_ind_pos = self.lock_ind_pos_var.get()
        if hasattr(self, "trig_ind_pos_var"):
            self.trig_ind_pos = self.trig_ind_pos_var.get()
        self._place_indicator_overlays()

    def _apply_indicator_frames(self):
        pairs = (
            (getattr(self, "lock_indicator", False), getattr(self, "lock_ind_frame", None), getattr(self, "lock_ind_toggle", None)),
            (getattr(self, "trigger_indicator", False), getattr(self, "trig_ind_frame", None), getattr(self, "trig_ind_toggle", None)),
        )
        for enabled, frame, canvas in pairs:
            if frame is None:
                continue
            try:
                frame.pack_forget()
            except Exception:
                pass
            if not enabled:
                continue
            try:
                anchor = canvas.master if canvas is not None else None
                if anchor is not None:
                    frame.pack(fill="x", pady=(0, 6), after=anchor)
                else:
                    frame.pack(fill="x", pady=(0, 6))
            except Exception:
                try:
                    frame.pack(fill="x", pady=(0, 6))
                except Exception:
                    pass
        self._ensure_indicator_overlays()

    def _ind_corner_xy(self, pos, size=18, pad=16):
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except Exception:
            sw, sh = 1920, 1080
        pos = str(pos or "Top Right")
        if pos == "Top Left":
            return pad, pad
        if pos == "Bottom Left":
            return pad, sh - size - pad
        if pos == "Bottom Right":
            return sw - size - pad, sh - size - pad
        return sw - size - pad, pad

    def _make_ind_overlay(self, key):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        chroma = "#ff00ff"
        try:
            win.wm_attributes("-transparentcolor", chroma)
        except Exception:
            pass
        win.configure(bg=chroma)
        cv = tk.Canvas(win, width=18, height=18, bg=chroma, highlightthickness=0, bd=0)
        cv.pack()
        dot = cv.create_oval(3, 3, 15, 15, outline="", fill="#ffffff")
        try:
            self._streamproof_widget(win)
        except Exception:
            pass
        setattr(self, key + "_win", win)
        setattr(self, key + "_cv", cv)
        setattr(self, key + "_dot", dot)
        return win

    def _ensure_indicator_overlays(self):
        for enabled, key in (
            (getattr(self, "lock_indicator", False), "_lock_ind"),
            (getattr(self, "trigger_indicator", False), "_trig_ind"),
        ):
            win = getattr(self, key + "_win", None)
            if enabled:
                try:
                    alive = win is not None and win.winfo_exists()
                except Exception:
                    alive = False
                if not alive:
                    self._make_ind_overlay(key)
            else:
                try:
                    if win is not None:
                        win.withdraw()
                        win.destroy()
                except Exception:
                    pass
                setattr(self, key + "_win", None)
        self._place_indicator_overlays()
        self._paint_indicators()

    def _place_indicator_overlays(self):
        for key, pos_attr, var_attr, default in (
            ("_lock_ind", "lock_ind_pos", "lock_ind_pos_var", "Top Right"),
            ("_trig_ind", "trig_ind_pos", "trig_ind_pos_var", "Top Left"),
        ):
            win = getattr(self, key + "_win", None)
            if win is None:
                continue
            pos = default
            if hasattr(self, var_attr):
                pos = getattr(self, var_attr).get() or pos
            else:
                pos = getattr(self, pos_attr, pos)
            x, y = self._ind_corner_xy(pos)
            try:
                win.geometry("18x18+%d+%d" % (int(x), int(y)))
                win.deiconify()
                win.lift()
            except Exception:
                pass

    def _set_indicator_states(self, lock_on, trig_on):
        self._ind_lock_on = bool(lock_on)
        self._ind_trig_on = bool(trig_on)
        self._paint_indicators()

    def _paint_indicators(self):
        try:
            if getattr(self, "_lock_ind_cv", None) is not None:
                col = rgb_hex(getattr(self, "lock_ind_on" if self._ind_lock_on else "lock_ind_idle", (255, 255, 255)))
                self._lock_ind_cv.itemconfig(self._lock_ind_dot, fill=col)
            if getattr(self, "_trig_ind_cv", None) is not None:
                col = rgb_hex(getattr(self, "trig_ind_on" if self._ind_trig_on else "trig_ind_idle", (255, 255, 255)))
                self._trig_ind_cv.itemconfig(self._trig_ind_dot, fill=col)
        except Exception:
            pass

    def _set_fov_color(self, color):
        try:
            shape = getattr(self, "fov_shape", "Circle")
            if hasattr(self, "fov_shape_var"):
                shape = self.fov_shape_var.get() or shape
            show = bool(getattr(self, "show_fov", True))
            if hasattr(self, "circle_id"):
                self.canvas.itemconfig(
                    self.circle_id, outline=color,
                    state="normal" if (show and shape == "Circle") else "hidden",
                )
            if hasattr(self, "fov_rect_id"):
                self.canvas.itemconfig(
                    self.fov_rect_id, outline=color,
                    state="normal" if (show and shape == "Box") else "hidden",
                )
            for i in getattr(self, "_fov_corner_ids", []):
                try:
                    self.canvas.itemconfig(
                        i, fill=color,
                        state="normal" if (show and shape == "Corners") else "hidden",
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def on_menu_scale_change(self, value):
        self.menu_scale = max(50.0, min(200.0, float(value)))
        self._apply_menu_scale(rebuild=True)

    def _apply_menu_scale(self, rebuild=False):
        try:
            base = float(getattr(self, "_tk_scale_base", 1.333) or 1.333)
            factor = max(0.5, min(2.0, float(getattr(self, "menu_scale", 100.0)) / 100.0))
            self.root.tk.call("tk", "scaling", base * factor)
        except Exception:
            pass
        if rebuild:
            try:
                self.apply_theme(getattr(self, "theme", "Default"), rebuild=True)
            except Exception:
                pass

    def on_opacity_change(self, value):
        self.menu_opacity = float(value)
        self._apply_opacity()

    def on_theme_change(self, event=None):
        self.apply_theme(self.theme_var.get(), rebuild=True)

    def _apply_custom_theme_visibility(self):
        frame = getattr(self, "custom_theme_frame", None)
        if frame is None:
            return
        on = (getattr(self, "theme_var", None) and self.theme_var.get() == "Custom") or getattr(self, "theme", "") == "Custom"
        try:
            if on:
                frame.pack(fill="x", pady=(0, 8), before=self.menu_scale_slider.master if hasattr(self, "menu_scale_slider") else None)
            else:
                frame.pack_forget()
        except Exception:
            try:
                if on:
                    frame.pack(fill="x", pady=(0, 8))
                else:
                    frame.pack_forget()
            except Exception:
                pass

    def apply_theme(self, name, rebuild=True):
        if name != "Custom" and name not in THEMES:
            name = "Ocean"
        self.theme = name
        if hasattr(self, "theme_var"):
            self.theme_var.set(name)
        if name == "Custom":
            _set_theme_globals("Custom", build_custom_theme(
                getattr(self, "custom_bg", (31, 10, 10)),
                getattr(self, "custom_fg", (255, 26, 26)),
            ))
        else:
            _set_theme_globals(name)
        if getattr(self, "dark_background", False) and name != "Custom":
            global C_CARD, C_CARD2, C_TRACK, C_BORDER
            C_CARD = "#1c1c1c"
            C_CARD2 = "#262626"
            C_TRACK = "#333333"
            C_BORDER = "#3a3a3a"
        try:
            self._setup_styles()
        except Exception:
            pass
        try:
            self.root.configure(bg=C_BG)
            if hasattr(self, "rim"):
                self.rim.configure(bg="#000000", highlightbackground="#000000")
            if hasattr(self, "outer"):
                self.outer.configure(bg="#000000")
            if hasattr(self, "sidebar"):
                self.sidebar.configure(bg="#000000")
            if hasattr(self, "side_div"):
                self.side_div.configure(bg=C_BORDER)
            if hasattr(self, "title_bar"):
                self.title_bar.configure(bg="#000000")
            if hasattr(self, "title_label"):
                self.title_label.configure(bg="#000000", fg=THEMES.get(name, {}).get("title", C_ACCENT))
            self._apply_content_background()
            if hasattr(self, "close_btn"):
                self.close_btn.configure(fg="#ff0000")
            for w in getattr(self, "tab_buttons", {}).values():
                try:
                    if w.cget("text") == self.active_tab.get():
                        w.configure(bg="#111111", fg="#ffffff")
                    else:
                        w.configure(bg="#000000", fg=C_MUTED)
                except Exception:
                    pass
            if hasattr(self, "resize_grip"):
                self.resize_grip.configure(bg=C_CARD)
                self._draw_resize_grip()
            try:
                self._style_tabs()
            except Exception:
                pass
        except Exception:
            pass

        if rebuild and hasattr(self, "content"):
            current = self.active_tab.get() if hasattr(self, "active_tab") else "Aimbot"
            for child in list(self.content.winfo_children()):
                try:
                    child.destroy()
                except Exception:
                    pass
            self.tab_frames = {}
            self._col_canvases = []
            self._sections = []
            self._build_aim_tab()
            self._build_visuals_tab()
            self._build_capture_tab()
            self._build_keybinds_tab()
            self._build_config_tab()
            try:
                self._refresh_playtime_labels()
            except Exception:
                pass
            try:
                self._rebuild_color_rows()
            except Exception:
                pass
            try:
                if hasattr(self, "_redraw_fov_toggle"):
                    self._redraw_fov_toggle()
                if hasattr(self, "_redraw_streamproof_toggle"):
                    self._redraw_streamproof_toggle()
                if hasattr(self, "_redraw_startup_toggle"):
                    self._redraw_startup_toggle()
                if hasattr(self, "_redraw_console_toggle"):
                    self._redraw_console_toggle()
                if hasattr(self, "_redraw_aot_toggle"):
                    self._redraw_aot_toggle()
                if hasattr(self, "_redraw_dark_bg_toggle"):
                    self._redraw_dark_bg_toggle()
                if hasattr(self, "_redraw_shaky_toggle"):
                    self._redraw_shaky_toggle()
                if hasattr(self, "_redraw_offset_toggle"):
                    self._redraw_offset_toggle()
                if hasattr(self, "_redraw_offset_toggle"):
                    self._redraw_offset_toggle()
                if hasattr(self, "_redraw_aimbot_toggle"):
                    self._redraw_aimbot_toggle()
                if hasattr(self, "_redraw_trigger_toggle"):
                    self._redraw_trigger_toggle()
                if hasattr(self, "_redraw_esp_toggle"):
                    self._redraw_esp_toggle()
                if hasattr(self, "_redraw_debug_view_toggle"):
                    self._redraw_debug_view_toggle()
                if hasattr(self, "_redraw_esp_preview_toggle"):
                    self._redraw_esp_preview_toggle()
                if hasattr(self, "_redraw_tracers_toggle"):
                    self._redraw_tracers_toggle()
            except Exception:
                pass
            self._show_tab(current)
            try:
                self.refresh_config_list()
            except Exception:
                pass
            try:
                self._apply_fov_visibility()
            except Exception:
                pass
    def on_circle_color_change(self, event=None):
        self.circle_color = self.circle_color_var.get()
        if hasattr(self, "canvas"):
            self.canvas.itemconfig(self.circle_id, outline=self.circle_color)
        try:
            self.update_overlay_size()
            self._make_overlay_clickthrough()
        except Exception:
            pass

    def on_fov_thickness_change(self, value):
        self.fov_thickness = int(max(1, min(5, float(value))))
        self._sync_hot_params()
        try:
            self._apply_fov_shape_draw()
        except Exception:
            pass

    def on_fov_opacity_change(self, value):
        self.fov_opacity = max(0.2, min(1.0, float(value)))
        try:
            self._make_overlay_clickthrough()
        except Exception:
            pass

    def get_key_code(self, name):
        if not name:
            return 0
        n = str(name).strip().upper()
        if n in ("NONE", "OFF", "UNBOUND", "-"):
            return 0
        aliases = {
            "ESCAPE": "ESC", "RETURN": "ENTER", "CONTROL": "CTRL",
            "MENU": "ALT", "BACK": "BACKSPACE", "SPC": "SPACE",
            "MOUSE4": "XBUTTON1", "MOUSE5": "XBUTTON2",
            "MOUSE1": "LBUTTON", "MOUSE2": "RBUTTON", "MOUSE3": "MBUTTON",
        }
        n = aliases.get(n, n)
        if n in KEY_CODE_BY_NAME:
            return int(KEY_CODE_BY_NAME[n])
        if n.startswith("VK_"):
            try:
                return int(n[3:], 16)
            except Exception:
                pass
        if len(n) == 1:
            ch = n.upper()
            if ch in KEY_CODE_BY_NAME:
                return int(KEY_CODE_BY_NAME[ch])
        return 0

    def _sync_hot_params(self):
        parsed = []
        for e in getattr(self, "color_entries", []):
            txt = e.get().strip()
            if not txt:
                continue
            try:
                parts = [int(p.strip()) for p in txt.split(",")]
                if len(parts) == 3:
                    parsed.append(tuple(parts))
            except Exception:
                pass
        if parsed:
            self.target_colors = parsed

        with self._colors_lock:
            self._hot_colors = list(self.target_colors)
            self._hot_color_ranges = precompute_color_ranges(self._hot_colors, getattr(self, "tolerance", 50))
            self._hot_tolerance = int(self.tolerance)
            self._hot_aim_hz = max(10, min(520, int(getattr(self, "aim_hz", 520))))
            self._hot_trigger_hz = max(10, min(520, int(getattr(self, "trigger_hz", 520))))
            self._hot_overlay_hz = max(10, min(520, int(getattr(self, "overlay_hz", 520))))
            self._hot_scan = int(self.scan_size)
            self._hot_scan_res = float(getattr(self, "scan_res", 1.0))
            ap = self.aim_point_var.get()
            if ap == "Edge":
                self._hot_aim_point = "edge"
            elif ap == "Head":
                self._hot_aim_point = "head"
            else:
                self._hot_aim_point = "center"
            self._hot_edge_bias = float(getattr(self, "edge_bias", 0))
            tp = self.target_priority_var.get() if hasattr(self, "target_priority_var") else "None"
            if tp == "Closest to Crosshair":
                self._hot_target_priority = "crosshair"
            elif tp == "Closest Match":
                self._hot_target_priority = "match"
            else:
                self._hot_target_priority = "none"
            self._hot_aimbot = bool(getattr(self, "aimbot_enabled", True))
            self._hot_key = self.get_key_code(self.keybind_var.get())
            self._hot_smooth = float(self.smoothness)
            self._hot_sens = float(self.sensitivity)
            self._hot_mouse_scale = float(self.mouse_scale)
            self._hot_shaky_enabled = bool(getattr(self, "shaky_enabled", False))
            self._hot_shaky_aim = float(getattr(self, "shaky_aim", 10))
            self._hot_shaky_speed = float(getattr(self, "shaky_speed", 5))
            self._hot_offset_enabled = bool(getattr(self, "offset_enabled", False))
            self._hot_offset_y = float(getattr(self, "offset_y", 0))
            self._hot_offset_x = float(getattr(self, "offset_x", 0))
            self._hot_triggerbot = bool(getattr(self, "triggerbot_enabled", False))
            self._hot_recoil = bool(getattr(self, "recoil_enabled", False))
            self._hot_recoil_strength = float(getattr(self, "recoil_strength", 2.0))
            self._hot_trigger_scan = max(1, min(100, int(getattr(self, "trigger_scan_size", 4))))
            tk_name = (
                self.trigger_keybind_var.get()
                if hasattr(self, "trigger_keybind_var")
                else getattr(self, "trigger_key_name", "XBUTTON5")
            )
            self._hot_trigger_key = self.get_key_code(tk_name)
            self._hot_trigger_reaction = float(getattr(self, "trigger_reaction_ms", 0))
            self._hot_trigger_interval = float(getattr(self, "trigger_interval_ms", 50))
            self._hot_trigger_release = float(getattr(self, "trigger_release_ms", 0))
            self._hot_trigger_key_mode = (
                self.trigger_key_mode_var.get()
                if hasattr(self, "trigger_key_mode_var")
                else getattr(self, "trigger_key_mode", "Hold")
            )
            self._hot_trigger_fire_mode = (
                self.trigger_fire_mode_var.get()
                if hasattr(self, "trigger_fire_mode_var")
                else getattr(self, "trigger_fire_mode", "Click on Color")
            )
            self._hot_aim_key_mode = self.aim_key_mode_var.get()
            self._hot_show_fov = bool(self.show_fov)
            self._hot_fov_mode = self.fov_mode_var.get() if hasattr(self, "fov_mode_var") else getattr(self, "fov_mode", "Follow Cursor")
            self._hot_esp = bool(getattr(self, "esp_enabled", False))
            self._hot_debug_view = bool(getattr(self, "debug_view_enabled", False))
            self._hot_esp_color = self.esp_color_var.get() if hasattr(self, "esp_color_var") else getattr(self, "esp_color", "white")
            self._hot_box_thickness = int(getattr(self, "box_thickness", 1))
            self._hot_player_box_shape = (
                self.player_box_shape_var.get()
                if hasattr(self, "player_box_shape_var")
                else getattr(self, "player_box_shape", "Box")
            )
            self._hot_corner_length = int(getattr(self, "corner_length", 8))
            self._hot_tracers = bool(getattr(self, "tracers_enabled", False))
            self._hot_tracer_thickness = int(getattr(self, "tracer_thickness", 1))
            self._hot_tracers_origin = (
                self.tracers_origin_var.get()
                if hasattr(self, "tracers_origin_var")
                else getattr(self, "tracers_origin", "Center")
            )

    def start(self):
        if self.tracking:
            return
        self._sync_hot_params()
        self.tracking = True
        self._worker_stop.clear()
        self._ensure_overlay_visibility()
        self._set_status("On", C_ACCENT)
        self._worker = threading.Thread(target=self._worker_loop, name="aim-worker", daemon=True)
        self._worker.start()

    def stop(self):
        self.tracking = False
        self._worker_stop.set()
        self.hide_overlay()
        self._set_fov_color(self.circle_color)
        self._set_status("Stopped", C_MUTED)

    def _worker_loop(self):
        try:
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception:
            pass

        try:
            sct = mss.MSS()
        except Exception:
            self._set_status("mss init failed", C_DANGER)
            self.tracking = False
            try:
                ctypes.windll.winmm.timeEndPeriod(1)
            except Exception:
                pass
            return

        aim_interval = 1.0 / 520.0
        idle_interval = 1.0 / 520.0
        toggle_armed = False
        prev_key_down = False
        last_lock_state = None
        vis_was_on = False
        tb_last_click = 0.0
        tb_seen_since = None
        tb_holding = False
        tb_release_at = 0.0
        tb_toggle_armed = False
        tb_prev_key = False
        tb_color_held = False
        prev_target = None
        vel_x, vel_y = 0.0, 0.0
        shake_cur_x = 0.0
        shake_cur_y = 0.0
        shake_tgt_x = 0.0
        shake_tgt_y = 0.0
        last_shake_retarget = 0.0
        last_recoil_t = 0.0
        last_blob_xy = None
        while self.tracking and not self._worker_stop.is_set():
            t0 = time.perf_counter()
            if mss is None or cv2 is None or np is None:
                time.sleep(0.05)
                continue
            if getattr(self, "_color_picker_open", False):
                time.sleep(0.02)
                continue

            with self._colors_lock:
                colors = self._hot_colors
                color_ranges = getattr(self, "_hot_color_ranges", None)
                tolerance = self._hot_tolerance
                scan = self._hot_scan
                scan_res = self._hot_scan_res
                aim_point = self._hot_aim_point
                edge_bias = float(getattr(self, "_hot_edge_bias", 0))
                target_priority = self._hot_target_priority
                aimbot_on = self._hot_aimbot
                key = self._hot_key
                smooth = self._hot_smooth
                sens = self._hot_sens
                mouse_scale = self._hot_mouse_scale
                shaky_enabled = self._hot_shaky_enabled
                shaky_aim = self._hot_shaky_aim if self._hot_shaky_enabled else 0.0
                shaky_speed = self._hot_shaky_speed
                offset_enabled = self._hot_offset_enabled
                offset_y = self._hot_offset_y
                offset_x = self._hot_offset_x
                triggerbot = self._hot_triggerbot
                trigger_key = self._hot_trigger_key
                trigger_scan = int(getattr(self, "_hot_trigger_scan", 4))
                trigger_key_mode = str(getattr(self, "_hot_trigger_key_mode", "Hold"))
                trigger_fire_mode = str(getattr(self, "_hot_trigger_fire_mode", "Click on Color"))
                trigger_reaction_ms = self._hot_trigger_reaction
                trigger_interval_ms = self._hot_trigger_interval
                trigger_release_ms = float(getattr(self, "_hot_trigger_release", 0))
                key_mode = self._hot_aim_key_mode
                lock_method = "Relative"
                show_fov = self._hot_show_fov
                fov_mode = self._hot_fov_mode
                esp_on = self._hot_esp
                debug_view = self._hot_debug_view
                esp_color = self._hot_esp_color
                box_thickness = self._hot_box_thickness
                player_box_shape = self._hot_player_box_shape
                corner_length = self._hot_corner_length
                tracers_on = self._hot_tracers
                tracer_thickness = self._hot_tracer_thickness
                tracers_origin = self._hot_tracers_origin
                recoil_on = bool(getattr(self, "_hot_recoil", False))
                recoil_str = float(getattr(self, "_hot_recoil_strength", 0.0))

            x, y = get_cursor_pos()
            if recoil_on and recoil_str > 0 and (get_key_state(0x01) & 0x8000):
                if (t0 - last_recoil_t) >= 0.01:
                    last_recoil_t = t0
                    move_mouse(0, int(round(recoil_str)))

            if fov_mode == "Centered":
                try:
                    origin_x = ctypes.windll.user32.GetSystemMetrics(0) // 2
                    origin_y = ctypes.windll.user32.GetSystemMetrics(1) // 2
                except Exception:
                    origin_x, origin_y = x, y
            else:
                origin_x, origin_y = x, y

            now = t0

            need_overlay = bool(show_fov or esp_on or tracers_on)
            xhair_on = bool(getattr(self, "xhair_enabled", False))
            if need_overlay and (now - self._last_overlay_t) >= (1.0 / max(10, int(getattr(self, "_hot_overlay_hz", 520)))):
                self._last_overlay_t = now
                ox, oy = origin_x, origin_y
                last_ov = getattr(self, "_last_ov_xy", None)
                if last_ov != (ox, oy):
                    self._last_ov_xy = (ox, oy)
                    self.root.after(0, lambda x=ox, y=oy: self.update_overlay_position(x, y))
            if xhair_on and (now - getattr(self, "_last_xhair_t", 0)) >= (1.0 / max(10, int(getattr(self, "_hot_overlay_hz", 520)))):
                self._last_xhair_t = now
                self.root.after(0, self._sync_xhair_overlay)

            if not colors:
                time.sleep(0.008)
                continue

            key_down = bool(key) and bool(get_key_state(key) & 0x8000)
            if time.perf_counter() < float(getattr(self, "_hotkey_arm_until", 0)):
                prev_key_down = True
                tb_prev_key = True
                key_down = False

            if not aimbot_on:
                aiming = False
                toggle_armed = False
                prev_key_down = key_down
            elif key_mode == "Toggle":
                if key_down and not prev_key_down:
                    toggle_armed = not toggle_armed
                aiming = toggle_armed
                prev_key_down = key_down
            else:
                aiming = key_down
                if not key_down:
                    toggle_armed = False
                prev_key_down = key_down

            if show_fov and aiming != last_lock_state:
                last_lock_state = aiming
                col = self.lock_color if aiming else self.circle_color
                self.root.after(0, lambda c=col: self._set_fov_color(c))
            elif not show_fov:
                last_lock_state = None

            need_aim = bool(aiming)
            need_vis = bool(esp_on or tracers_on)
            need_debug = bool(debug_view)
            tb_key_down = False
            if triggerbot:
                tb_key_down = bool(trigger_key) and bool(get_key_state(trigger_key) & 0x8000)
            if time.perf_counter() < float(getattr(self, "_hotkey_arm_until", 0)):
                tb_key_down = False
                tb_prev_key = True
            if not triggerbot:
                tb_toggle_armed = False
                tb_prev_key = False
                need_tb = False
            elif trigger_key_mode == "Toggle":
                if tb_key_down and not tb_prev_key:
                    tb_toggle_armed = not tb_toggle_armed
                tb_prev_key = tb_key_down
                need_tb = bool(tb_toggle_armed)
            else:
                need_tb = bool(tb_key_down)
                if not tb_key_down:
                    tb_toggle_armed = False
                tb_prev_key = tb_key_down
            need_fov_scan = need_aim or need_vis or need_debug
            try:
                self.root.after(0, lambda a=aiming, tb=need_tb: self._set_indicator_states(a, tb))
            except Exception:
                pass
            if not need_fov_scan and not need_tb:
                tb_seen_since = None
                prev_target = None
                vel_x = vel_y = 0.0
                time.sleep(0.012)
                continue

            now_tb = time.perf_counter()
            if tb_holding and now_tb >= tb_release_at:
                try:
                    mouse_left_up()
                except Exception:
                    pass
                tb_holding = False
                tb_last_click = now_tb

            hold_color = trigger_fire_mode.strip().lower().startswith("hold")
            tb_dt = 1.0 / max(10, int(getattr(self, "_hot_trigger_hz", 520)))
            if need_tb and (now_tb - getattr(self, "_last_tb_scan_t", 0)) >= tb_dt:
                self._last_tb_scan_t = now_tb
                try:
                    ts = max(1, min(100, int(trigger_scan)))
                    half_ts = ts // 2
                    tb_box = {
                        "left": int(x) - half_ts,
                        "top": int(y) - half_ts,
                        "width": ts,
                        "height": ts,
                    }
                    tb_shot = sct.grab(tb_box)
                    tb_img = np.frombuffer(tb_shot.rgb, dtype=np.uint8).reshape(
                        (tb_shot.height, tb_shot.width, 3)
                    )
                    tb_mask = build_color_mask(tb_img, colors, tolerance)
                    on_target = tb_mask is not None and bool(np.any(tb_mask))
                except Exception:
                    on_target = False
                if on_target:
                    if tb_seen_since is None:
                        tb_seen_since = now_tb
                    reaction_s = max(0.0, float(trigger_reaction_ms)) * 0.001
                    if (now_tb - tb_seen_since) >= reaction_s:
                        if hold_color:
                            if not tb_color_held:
                                try:
                                    mouse_left_down()
                                except Exception:
                                    pass
                                tb_color_held = True
                        else:
                            interval_s = max(0.0, float(trigger_interval_ms)) * 0.001
                            release_s = max(0.0, float(trigger_release_ms)) * 0.001
                            if (not tb_holding) and (now_tb - tb_last_click) >= max(interval_s, 0.001):
                                try:
                                    if release_s <= 0.0005:
                                        click_left()
                                        tb_last_click = now_tb
                                    else:
                                        mouse_left_down()
                                        tb_holding = True
                                        tb_release_at = now_tb + release_s
                                except Exception:
                                    pass
                else:
                    tb_seen_since = None
                    if tb_color_held:
                        try:
                            mouse_left_up()
                        except Exception:
                            pass
                        tb_color_held = False
            else:
                tb_seen_since = None
                if tb_holding or tb_color_held:
                    try:
                        mouse_left_up()
                    except Exception:
                        pass
                    tb_holding = False
                    tb_color_held = False
                    tb_last_click = now_tb

            if not need_fov_scan:
                elapsed = time.perf_counter() - t0
                delay = idle_interval - elapsed
                if delay > 0.0005:
                    time.sleep(delay)
                continue

            if need_debug and not need_aim and not need_vis:
                if not hasattr(self, "_last_debug_grab_t"):
                    self._last_debug_grab_t = 0.0
                if (now - self._last_debug_grab_t) < (1.0 / max(10, int(getattr(self, "_hot_overlay_hz", 520)))):
                    time.sleep(0.002)
                    continue
                self._last_debug_grab_t = now

            half = scan // 2
            left = origin_x - half
            top = origin_y - half
            bbox = {"left": left, "top": top, "width": scan, "height": scan}

            try:
                shot = sct.grab(bbox)
            except Exception:
                time.sleep(0.001)
                continue

            img = np.frombuffer(shot.rgb, dtype=np.uint8).reshape((shot.height, shot.width, 3))

            scale = max(0.25, min(1.0, float(scan_res)))
            if need_aim or need_vis:
                if scale < 0.999:
                    nw = max(1, int(img.shape[1] * scale))
                    nh = max(1, int(img.shape[0] * scale))
                    img_d = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
                    inv = 1.0 / scale
                else:
                    img_d = img
                    inv = 1.0
                mask = build_color_mask(img_d, colors, tolerance, ranges=color_ranges)
                has_mask = mask is not None and cv2.countNonZero(mask) > 0
            else:
                img_d = None
                mask = None
                has_mask = False
                inv = 1.0

            if need_debug:
                try:
                    if not hasattr(self, "_last_debug_t"):
                        self._last_debug_t = 0.0
                    if (now - self._last_debug_t) >= (1.0 / max(10, int(getattr(self, "_hot_overlay_hz", 520)))):
                        self._last_debug_t = now
                        full_mask = build_color_mask(img, colors, tolerance)
                        if full_mask is None:
                            full_mask = np.zeros(img.shape[:2], dtype=np.uint8)
                        view = img
                        green = view.copy()
                        on = full_mask > 0
                        if np.any(on):
                            green[on, 0] = (green[on, 0] * 0.35).astype(np.uint8)
                            green[on, 1] = np.maximum(green[on, 1], 220)
                            green[on, 2] = (green[on, 2] * 0.35).astype(np.uint8)
                        mask_rgb = np.stack([full_mask, full_mask, full_mask], axis=-1)
                        div = np.full((view.shape[0], 4, 3), 40, dtype=np.uint8)
                        combo = np.concatenate([view, div, green, div, mask_rgb], axis=1)
                        with self._debug_lock:
                            self._debug_frame = combo
                except Exception:
                    pass

            vis_on = need_vis
            if vis_on:
                vis_was_on = True
                if (now - self._last_esp_t) >= (1.0 / 60.0):
                    self._last_esp_t = now
                    if has_mask:
                        boxes = blob_bounding_boxes(mask, min_area=12, merge_gap=16, pad=4)
                        if inv != 1.0:
                            boxes = [
                                (int(a * inv), int(b * inv), int(c * inv), int(d * inv))
                                for a, b, c, d in boxes
                            ]
                        if esp_on:
                            self.root.after(
                                0,
                                lambda b=boxes, c=esp_color, t=box_thickness, s=player_box_shape, cl=corner_length: self.update_esp_boxes(
                                    b, c, t, s, cl
                                ),
                            )
                        else:
                            self.root.after(0, self.clear_esp_boxes)

                        if tracers_on:
                            centers = [
                                ((b[0] + b[2]) * 0.5, (b[1] + b[3]) * 0.5) for b in boxes
                            ]
                            ol, ot = left, top
                            cxy = (x, y)
                            omod = tracers_origin
                            self.root.after(
                                0,
                                lambda pts=centers, c=esp_color, t=tracer_thickness, om=omod, ol=ol, ot=ot, cxy=cxy: self.update_tracers(
                                    pts, c, t, om, ol, ot, cxy
                                ),
                            )
                        else:
                            self.root.after(0, self.clear_tracers)
                    else:
                        self.root.after(0, self.clear_esp_boxes)
                        self.root.after(0, self.clear_tracers)
            elif vis_was_on:
                vis_was_on = False
                self.root.after(0, self.clear_esp_boxes)
                self.root.after(0, self.clear_tracers)

            if not aiming:
                last_blob_xy = None
            if aiming and has_mask:
                aim_mask = select_priority_mask(
                    mask, img_d, target_priority, colors, min_area=12, last_xy=last_blob_xy
                )
                local_bbox = {
                    "left": 0,
                    "top": 0,
                    "width": aim_mask.shape[1],
                    "height": aim_mask.shape[0],
                }
                avg = target_from_mask(
                    aim_mask, local_bbox, aim_point=aim_point, edge_bias=edge_bias
                )
                if avg is not None:
                    last_blob_xy = (float(avg[0]), float(avg[1]))
                    avg = (
                        int(bbox["left"] + avg[0] * inv),
                        int(bbox["top"] + avg[1] * inv),
                    )
                else:
                    last_blob_xy = None
                if avg is not None:
                    now_t = time.perf_counter()
                    aim_x, aim_y = avg[0], avg[1]
                    prev_target = (avg[0], avg[1], now_t)

                    if offset_enabled:
                        aim_x = aim_x + float(offset_x)
                        aim_y = aim_y - float(offset_y)

                    if shaky_enabled and shaky_aim > 0:
                        spd = max(0.0, min(10.0, float(shaky_speed))) / 10.0
                        retarget_dt = 0.35 - spd * 0.31
                        max_r = (float(shaky_aim) / 50.0) * 70.0
                        if (now_t - last_shake_retarget) >= retarget_dt:
                            last_shake_retarget = now_t
                            ang = random.uniform(0.0, 6.283185307179586)
                            rad = random.uniform(0.0, max_r)
                            shake_tgt_x = rad * math.cos(ang)
                            shake_tgt_y = rad * math.sin(ang)
                        lerp = 0.04 + spd * 0.35
                        shake_cur_x += (shake_tgt_x - shake_cur_x) * lerp
                        shake_cur_y += (shake_tgt_y - shake_cur_y) * lerp
                        aim_x += shake_cur_x
                        aim_y += shake_cur_y
                    else:
                        shake_cur_x = shake_cur_y = 0.0
                        shake_tgt_x = shake_tgt_y = 0.0

                    base = 1.0 / (1.0 + smooth * 0.95)
                    factor = min(1.0, base * (sens / 5.0))
                    move_cursor_to_position(
                        aim_x, aim_y, x, y,
                        factor=factor, scale=mouse_scale, method="Relative",
                    )
            elif aiming and not has_mask:
                pass

            elapsed = time.perf_counter() - t0
            aim_interval = 1.0 / max(10, int(getattr(self, "_hot_aim_hz", 520)))
            idle_interval = aim_interval
            target = aim_interval if aiming else idle_interval
            delay = target - elapsed
            if delay > 0.0004:
                time.sleep(delay)
            elif delay > 0:
                end = t0 + target
                while time.perf_counter() < end:
                    pass

        try:
            sct.close()
        except Exception:
            pass
        try:
            ctypes.windll.winmm.timeEndPeriod(1)
        except Exception:
            pass



    def make_draggable(self):
        def is_interactive(widget):
            while widget is not None:
                cls = widget.winfo_class()
                if cls in (
                    "TScale", "Scale", "TCombobox", "Combobox",
                    "TButton", "Button", "TEntry", "Entry",
                    "Canvas",
                ):
                    return True
                if getattr(widget, "_is_slider", False):
                    return True
                try:
                    widget = widget.master
                except Exception:
                    break
            return False

        def start(e):
            if is_interactive(e.widget):
                self._dragging = False
                return
            if e.widget is getattr(self, "resize_grip", None):
                self._dragging = False
                return
            self._dragging = True
            self._dx, self._dy = e.x_root, e.y_root

        def drag(e):
            if not getattr(self, "_dragging", False):
                return
            dx = e.x_root - self._dx
            dy = e.y_root - self._dy
            self._dx, self._dy = e.x_root, e.y_root
            self.root.geometry(f"+{self.root.winfo_x() + dx}+{self.root.winfo_y() + dy}")

        def stop(e):
            self._dragging = False

        for w in (self.title_bar, self.title_label):
            w.bind("<Button-1>", start)
            w.bind("<B1-Motion>", drag)
            w.bind("<ButtonRelease-1>", stop)

def instance_already_running():
    k32 = ctypes.windll.kernel32
    k32.OpenMutexW.restype = wintypes.HANDLE
    h = k32.OpenMutexW(0x00100000, False, INSTANCE_MUTEX)
    if h:
        k32.CloseHandle(h)
        return True
    return False

if __name__ == "__main__":
    if instance_already_running():
        request_existing_instance_show()
        os._exit(0)
    if relaunch_detached():
        os._exit(0)
    _mtx, _evt, _already = _instance_handles()
    if _already:
        request_existing_instance_show()
        os._exit(0)
    try:
        if not load_show_console_pref():
            hide_console_window()
            def _keep_console_hidden():
                try:
                    if not load_show_console_pref():
                        hide_console_window()
                except Exception:
                    pass
        else:
            set_console_visible(True)
    except Exception:
        try:
            hide_console_window()
        except Exception:
            pass
    root = tk.Tk()
    try:
        root.configure(bg="#000000")
    except Exception:
        pass
    app = ColorTrackerGUI(root)
    app._show_event = _evt
    try:
        if not load_show_console_pref():
            root.after(100, hide_console_window)
            root.after(1000, hide_console_window)
    except Exception:
        pass
    root.mainloop()
