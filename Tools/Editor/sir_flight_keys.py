#!/usr/bin/env python
"""Deliver real key holds to the Unreal editor window for Sir's flight proof.

Why PostMessage: the acceptance is a *physical* key press. A scripted probe
that sets the input booleans directly would prove nothing about the bindings,
the edge detection or the release behaviour. PostMessage(WM_KEYDOWN/WM_KEYUP)
enters the same window-message path a real key takes, without stealing focus
(AppActivate / AttachThreadInput were tried and never brought the editor to
the foreground on this machine).

Usage:
    py sir_flight_keys.py <hwnd> <script>

where <script> is a comma-separated list of steps, each either
    HOLD:<key>:<seconds>      key down, wait, key up
    TAP:<key>                 key down, 60 ms, key up
    WAIT:<seconds>            pause

Keys: SPACE, LEFT_ALT, LEFT_SHIFT, LEFT_CONTROL, W, A, S, D

Example (ascend 3 s, descend 2 s, hold altitude 2 s, boost 2 s):
    py sir_flight_keys.py 0x1234 HOLD:SPACE:3,HOLD:LEFT_ALT:2,WAIT:2,HOLD:LEFT_SHIFT:2
"""
import ctypes
import sys
import time

user32 = ctypes.WinDLL('user32', use_last_error=True)
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

# Virtual key codes and keyboard scan codes.
VK = {
    'SPACE': 0x20, 'W': 0x57, 'A': 0x41, 'S': 0x53, 'D': 0x44,
    'LEFT_ALT': 0xA4, 'LEFT_SHIFT': 0xA0, 'LEFT_CONTROL': 0xA2,
}
SCAN = {
    'SPACE': 0x39, 'W': 0x11, 'A': 0x1E, 'S': 0x1F, 'D': 0x20,
    'LEFT_ALT': 0x38, 'LEFT_SHIFT': 0x2A, 'LEFT_CONTROL': 0x1D,
}


def post(hwnd, key, down):
    vk = VK[key]
    scan = SCAN[key]
    if down:
        lparam = 0x00000001 | (scan << 16)
        msg = WM_KEYDOWN
    else:
        lparam = 0xC0000001 | (scan << 16)
        msg = WM_KEYUP
    ok = user32.PostMessageW(ctypes.c_void_p(hwnd), msg, ctypes.c_size_t(vk), ctypes.c_size_t(lparam))
    print('POST %s %s hwnd=%s ok=%s err=%s' % (key, 'down' if down else 'up', hwnd, bool(ok), ctypes.get_last_error()), flush=True)
    return bool(ok)


def main():
    if len(sys.argv) < 3:
        print('usage: sir_flight_keys.py <hwnd> <script>')
        return 2
    hwnd = int(sys.argv[1], 0)
    script = sys.argv[2]

    for step in script.split(','):
        step = step.strip()
        if not step:
            continue
        parts = step.split(':')
        kind = parts[0].upper()
        if kind == 'WAIT':
            time.sleep(float(parts[1]))
            continue
        if kind == 'TAP':
            key = parts[1].upper()
            if key not in VK:
                print('unknown key %r' % key)
                return 2
            post(hwnd, key, True)
            time.sleep(0.06)
            post(hwnd, key, False)
            time.sleep(0.12)
            continue
        if kind == 'HOLD':
            key = parts[1].upper()
            seconds = float(parts[2])
            if key not in VK:
                print('unknown key %r' % key)
                return 2
            post(hwnd, key, True)
            time.sleep(seconds)
            post(hwnd, key, False)
            time.sleep(0.25)
            continue
        print('unknown step %r' % step)
        return 2

    print('SCRIPT DONE', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
